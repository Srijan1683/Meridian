import pytest

import app.services.research_service as research_service
from app.models.research import ResearchMode, ResearchRequest, TokenBudget


@pytest.mark.asyncio
async def test_sources_are_tracked_with_session_and_search_query(patch_research):
    state = patch_research

    result = await research_service.run_research(
        ResearchRequest(
            query="How are reusable rockets changing launch economics?",
            mode=ResearchMode.NORMAL,
        )
    )

    assert result.sources
    assert len(state["sources"]) == 2

    for source in state["sources"]:
        assert source["session_id"] == result.session_id
        assert source["source_id"]
        assert str(source["url"]).startswith("https://example.com/source-")
        assert source["title"].startswith("Source")
        assert source["snippet"]
        assert source["source_type"] == "web"
        assert source["search_query"]

    tracked_queries = {source["search_query"] for source in state["sources"]}

    assert tracked_queries == {
        "How are reusable rockets changing launch economics?",
        "How are reusable rockets changing launch economics? latest reliable sources",
    }


@pytest.mark.asyncio
async def test_response_source_list_matches_returned_sources(patch_research):
    result = await research_service.run_research(
        ResearchRequest(
            query="What changed in reusable rockets?",
            mode=ResearchMode.NORMAL,
        )
    )

    for index, source in enumerate(result.sources, start=1):
        expected_line = f"[{index}] {source.title} - {str(source.url)}"
        assert expected_line in result.response

    assert result.response.count("Sources:") == 1


@pytest.mark.asyncio
async def test_citations_are_persisted_against_valid_sources(patch_research):
    state = patch_research

    result = await research_service.run_research(
        ResearchRequest(
            query="What changed in reusable rockets?",
            mode=ResearchMode.NORMAL,
        )
    )

    source_ids = {source.source_id for source in result.sources}
    message_ids = {message["message_id"] for message in state["messages"]}

    assert state["citations"]

    for citation in state["citations"]:
        assert citation["message_id"] in message_ids
        assert citation["source_id"] in source_ids
        assert citation["citation_index"] in {1, 2}
        assert citation["claim_text"]


@pytest.mark.asyncio
async def test_invalid_citation_marker_adds_warning(monkeypatch, patch_research):
    async def synthesize_with_invalid_citation(
        user_query,
        mode,
        search_answers,
        sources,
        long_term_context,
    ):
        return (
            "This answer cites a missing source [99].",
            TokenBudget(prompt_tokens=1, completion_tokens=1, total_tokens=2),
        )

    monkeypatch.setattr(
        research_service,
        "synthesize_response",
        synthesize_with_invalid_citation,
    )

    result = await research_service.run_research(
        ResearchRequest(
            query="What changed in reusable rockets?",
            mode=ResearchMode.NORMAL,
        )
    )

    assert "Citation warning" in result.response
    assert "[99]" in result.response
    assert not patch_research["citations"]


@pytest.mark.asyncio
async def test_deep_mode_tracks_sources_from_each_iterative_search(patch_research):
    state = patch_research

    result = await research_service.run_research(
        ResearchRequest(
            query="Deep research reusable rockets",
            mode=ResearchMode.DEEP,
        )
    )

    assert len(state["search_queries"]) == 6
    assert len(state["sources"]) == 6
    assert len(result.sources) == 6

    source_queries = [source["search_query"] for source in state["sources"]]
    search_queries = [search["query"] for search in state["search_queries"]]

    assert source_queries == search_queries
    assert all(search["deep"] is True for search in state["search_queries"])
