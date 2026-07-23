import pytest

import app.services.research_service as research_service
from app.models.research import ResearchMode, ResearchRequest


@pytest.mark.asyncio
async def test_normal_mode_tracks_sources_citations_and_response(patch_research):
    state = patch_research

    result = await research_service.run_research(
        ResearchRequest(
            query="What changed in reusable rockets?",
            mode=ResearchMode.NORMAL,
        )
    )

    assert result.session_id in state["sessions"]
    assert len(state["search_queries"]) == 2
    assert all(search["deep"] is False for search in state["search_queries"])
    assert result.sources
    assert state["sources"]
    assert "Sources:" in result.response
    assert "[1] Source 1 - https://example.com/source-1" in result.response
    assert state["messages"]
    assert state["messages"][0]["content"] == result.response
    assert state["citations"]
    assert state["citations"][0]["citation_index"] == 1
    assert state["citations"][0]["source_id"] == result.sources[0].source_id


@pytest.mark.asyncio
@pytest.mark.xfail(
    reason=(
        "run_research does not currently call "
        "app.memory.short_term.store_interaction_memory."
    )
)
async def test_normal_mode_updates_short_term_memory(patch_research):
    state = patch_research

    await research_service.run_research(
        ResearchRequest(
            query="What changed in reusable rockets?",
            mode=ResearchMode.NORMAL,
        )
    )

    assert state["short_term_memories"]