import pytest
from fastapi.testclient import TestClient

import app.api.websocket as websocket_api
import app.services.research_service as research_service
from app.main import app
from app.models.research import ResearchMode, ResearchRequest
from app.models.sources import SearchResponse, SearchResult, SourceType
from app.models.websocket import WSMessageType


@pytest.mark.asyncio
async def test_very_long_session_builds_bounded_deep_search_plan(patch_research):
    long_query = " ".join(f"message-{index}" for index in range(25))

    result = await research_service.run_research(
        ResearchRequest(
            query=long_query,
            mode=ResearchMode.DEEP,
        )
    )

    assert len(patch_research["search_queries"]) == 6
    assert all(
        len(search["query"]) <= research_service.MAX_TAVILY_QUERY_LENGTH
        for search in patch_research["search_queries"]
    )
    assert result.sources


def test_rate_limit_mid_research_streams_error_event(monkeypatch, patch_research):
    calls = 0

    async def rate_limited_search(query, *, deep=False):
        nonlocal calls
        calls += 1

        if calls == 2:
            raise RuntimeError("Perplexity rate limit: retry later")

        return SearchResponse(
            answer="First result",
            sources=[
                SearchResult(
                    title="First source",
                    url="https://example.com/rate-limit-first",
                    snippet="Available before the limit",
                    source_type=SourceType.WEB,
                )
            ],
        )

    monkeypatch.setattr(research_service, "search_web", rate_limited_search)

    with TestClient(app) as client:
        with client.websocket_connect("/ws/research") as websocket:
            websocket.send_json(
                {
                    "type": "query",
                    "data": {
                        "query": "rate limit resilience",
                        "mode": "deep",
                    },
                }
            )

            messages = []
            while True:
                message = websocket.receive_json()
                messages.append(message)

                if message["type"] in {"done", "error"}:
                    break

    assert messages[-1]["type"] == "error"
    assert "rate limit" in messages[-1]["data"]["error"].lower()


@pytest.mark.asyncio
async def test_websocket_disconnection_does_not_send_after_disconnect():
    send_count = 0

    class FakeWebSocket:
        async def send_json(self, payload):
            nonlocal send_count
            send_count += 1

    connection = websocket_api.ResearchConnection(FakeWebSocket())
    connection.disconnected = True

    await connection.send(WSMessageType.CONTENT, {"chunk": "ignored"})

    assert send_count == 0


@pytest.mark.asyncio
async def test_contradicting_sources_are_synthesized_with_valid_citations(patch_research):
    result = await research_service.run_research(
        ResearchRequest(
            query="Contradict estimates for commercial fusion",
            mode=ResearchMode.NORMAL,
        )
    )

    assert "Sources disagree" in result.response
    assert "Evidence comes from [1]" in result.response

    assert patch_research["citations"]

    source_ids = {source.source_id for source in result.sources}

    assert all(
        citation["source_id"] in source_ids
        for citation in patch_research["citations"]
    )