import pytest
from fastapi.testclient import TestClient

import app.services.research_service as research_service
from app.main import app
from app.models.research import ResearchMode, ResearchRequest
from app.models.websocket import WSMessageType


@pytest.mark.asyncio
async def test_deep_research_streams_memory_search_sources_and_content(patch_research):
    events = []

    async def progress(message_type, data):
        events.append({"type": message_type.value, "data": data})

    result = await research_service.run_research_streaming(
        request=ResearchRequest(
            query="Deep research reusable rockets",
            mode=ResearchMode.DEEP,
        ),
        progress=progress,
        is_cancelled=lambda: False,
    )

    event_types = [event["type"] for event in events]

    assert event_types[0] == WSMessageType.MEMORY.value
    assert event_types.count(WSMessageType.SEARCHING.value) == 6
    assert event_types.count(WSMessageType.SOURCE.value) == 6
    assert event_types[-1] == WSMessageType.CONTENT.value

    assert len(patch_research["search_queries"]) == 6
    assert all(search["deep"] is True for search in patch_research["search_queries"])

    streamed_text = "".join(
        event["data"]["chunk"]
        for event in events
        if event["type"] == WSMessageType.CONTENT.value
    )

    assert streamed_text == result.response
    assert "Sources:" in streamed_text
    assert patch_research["citations"]


def test_websocket_deep_research_events_are_correct(patch_research):
    with TestClient(app) as client:
        with client.websocket_connect("/ws/research") as websocket:
            websocket.send_json(
                {
                    "type": "query",
                    "data": {
                        "query": "Deep research battery supply chains",
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

    assert messages[0]["type"] == "memory"
    assert any(message["type"] == "searching" for message in messages)
    assert any(message["type"] == "source" for message in messages)
    assert any(message["type"] == "content" for message in messages)

    done = messages[-1]
    assert done["type"] == "done"
    assert done["data"]["cancelled"] is False
    assert done["data"]["source_count"] == 6
    assert "Sources:" in done["data"]["response"]