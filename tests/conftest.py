from datetime import datetime, timezone
from uuid import uuid4

import pytest

import app.services.research_service as research_service
from app.models.research import TokenBudget
from app.models.sources import SearchResponse, SearchResult, SourceType


@pytest.fixture
def research_state():
    return {
        "sessions": {},
        "messages": [],
        "sources": [],
        "citations": [],
        "search_queries": [],
        "short_term_memories": [],
        "long_term_memories": [],
        "memory_jobs": [],
        "completed_jobs": [],
    }


@pytest.fixture
def patch_research(monkeypatch, research_state):
    async def fake_create_session(session_id=None, title=None):
        sid = session_id or uuid4()
        row = {
            "session_id": sid,
            "title": title,
            "status": "active",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "ended_at": None,
        }
        research_state["sessions"][sid] = row
        return row

    async def fake_create_message(session_id, role, content, token_count=0):
        row = {
            "message_id": uuid4(),
            "session_id": session_id,
            "role": role.value if hasattr(role, "value") else role,
            "content": content,
            "token_count": token_count,
            "created_at": datetime.now(timezone.utc),
        }
        research_state["messages"].append(row)
        return row

    async def fake_create_sources_for_search(session_id, sources, search_query):
        rows = []
        for source in sources:
            row = {
                "source_id": uuid4(),
                "session_id": session_id,
                "url": source.url,
                "title": source.title,
                "snippet": source.snippet,
                "source_type": source.source_type.value,
                "search_query": search_query,
                "retrieved_at": datetime.now(timezone.utc),
                "credibility_note": None,
            }
            rows.append(row)
            research_state["sources"].append(row)
        return rows

    async def fake_create_source_citations(message_id, citations):
        rows = []
        for citation in citations:
            row = {
                "citation_id": uuid4(),
                "message_id": message_id,
                **citation,
            }
            rows.append(row)
            research_state["citations"].append(row)
        return rows

    async def fake_search_web(query, *, deep=False):
        research_state["search_queries"].append({"query": query, "deep": deep})

        if "rate limit" in query.lower():
            raise RuntimeError("Perplexity rate limit: retry later")

        index = len(research_state["search_queries"])
        return SearchResponse(
            answer=f"Finding {index} for {query}.",
            sources=[
                SearchResult(
                    title=f"Source {index}",
                    url=f"https://example.com/source-{index}",
                    snippet=f"Snippet {index} about {query}",
                    source_type=SourceType.WEB,
                )
            ],
            citations=[f"https://example.com/source-{index}"],
        )

    async def fake_synthesize_response(
        user_query,
        mode,
        search_answers,
        sources,
        long_term_context,
    ):
        prior = ""
        if long_term_context:
            prior = " Prior research says quantum computing needs error correction."

        conflict = ""
        if "contradict" in user_query.lower():
            conflict = (
                " Sources disagree on timing; one expects near-term progress "
                "while another is cautious."
            )

        text = f"Answer to {user_query}.{prior}{conflict} Evidence comes from [1]."
        if len(sources) > 1:
            text += " Additional context is available in [2]."

        return text, TokenBudget(
            prompt_tokens=10,
            completion_tokens=20,
            total_tokens=30,
        )

    async def fake_build_long_term_context(query):
        matches = [
            memory
            for memory in research_state["long_term_memories"]
            if "quantum" in query.lower()
        ]

        if not matches:
            return "", 0

        context = "Relevant context from previous sessions:\n" + "\n".join(
            memory["summary"] for memory in matches
        )
        return context, len(matches)

    monkeypatch.setattr(research_service, "create_session", fake_create_session)
    monkeypatch.setattr(research_service, "create_message", fake_create_message)
    monkeypatch.setattr(
        research_service,
        "create_sources_for_search",
        fake_create_sources_for_search,
    )
    monkeypatch.setattr(
        research_service,
        "create_source_citations",
        fake_create_source_citations,
    )
    monkeypatch.setattr(research_service, "search_web", fake_search_web)
    monkeypatch.setattr(research_service, "synthesize_response", fake_synthesize_response)
    monkeypatch.setattr(
        research_service,
        "build_long_term_context",
        fake_build_long_term_context,
    )

    return research_state