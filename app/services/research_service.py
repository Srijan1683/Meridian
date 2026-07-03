from app.db.repositories.sources import create_sources_for_search
from app.db.repositories.sessions import create_session
from app.memory.long_term import (
    format_long_term_memory_context,
    retrieve_long_term_memories
)
from app.models.memory import MemoryContext
from app.models.research import ResearchMode, ResearchResponse, ResearchRequest, TokenBudget
from app.models.sources import Source, SourceType
from app.search.tavily import search_web


MAX_TAVILY_QUERY_LENGTH = 400


async def build_long_term_context(query: str) -> tuple[str, int]:
    memories = await retrieve_long_term_memories(
        query=query,
        limit=3,
        min_similarity=0.7,
    )

    return format_long_term_memory_context(memories), len(memories)


def build_search_query(
    user_query: str,
    mode: ResearchMode,
    long_term_context: str
) -> str:
    query = " ".join(user_query.split())

    if mode == ResearchMode.DEEP:
        query = f"{query} background latest developments analysis"

    if long_term_context:
        query = f"{query} related prior research context"

    if len(query) <= MAX_TAVILY_QUERY_LENGTH:
        return query

    return query[:MAX_TAVILY_QUERY_LENGTH].rsplit(" ", 1)[0]


def _source_row_to_model(row: dict) -> Source:
    return Source(
        source_id=row["source_id"],
        session_id=row["session_id"],
        url=row["url"],
        title=row["title"],
        snippet=row["snippet"],
        source_type=SourceType(row["source_type"]),
        search_query=row["search_query"],
        retrieved_at=row["retrieved_at"],
        credibility_note=row.get("credibility_note"),
    )


async def run_research(request: ResearchRequest) -> ResearchResponse:
    session = await create_session(session_id=request.session_id)
    session_id = session["session_id"]

    long_term_context, long_term_count = await build_long_term_context(request.query)
    
    search_query = build_search_query(
        user_query=request.query,
        mode=request.mode,
        long_term_context=long_term_context,
    )
    
    search_result = await search_web(
        query=search_query,
        deep=request.mode == ResearchMode.DEEP,
    )
    
    source_rows = await create_sources_for_search(
        session_id=session_id,
        sources=search_result.sources,
        search_query=search_query,
    )
    
    sources = [_source_row_to_model(row) for row in source_rows]

    response_text = search_result.answer

    return ResearchResponse(
        session_id=session_id,
        mode=request.mode,
        response=response_text,
        sources=sources,
        memory_context=MemoryContext(
            short_term_retrieved=0,
            long_term_retrieved=long_term_count,
            memories=[],
            retrieval_time_ms=0,
        ),
        token_usage=TokenBudget(),
    )
