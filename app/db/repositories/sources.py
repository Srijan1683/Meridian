from uuid import UUID

from app.db.postgres import get_pool
from app.models.sources import SearchResult, SourceType


async def create_source(
    session_id: UUID,
    source: SearchResult,
    search_query: str,
) -> dict:
    pool = await get_pool()
    
    row = await pool.fetchrow(
        """
        INSERT INTO sources (
            session_id,
            url,
            title,
            snippet,
            source_type,
            search_query
        )
        VALUES ($1, $2, $3, $4, $5, $6)
        RETURNING *
        """,
        session_id,
        source.url,
        source.title,
        source.snippet,
        source.source_type.value,
        search_query,
    )
    
    return dict(row)


async def create_sources_for_search(
    session_id: UUID,
    sources: list[SearchResult],
    search_query: str,
) -> list[dict]:
    created_sources: list[dict] = []
    for source in sources:
        created = await create_source(
            session_id=session_id,
            source=source,
            search_query=search_query,
        )
        created_sources.append(created)
        
    return created_sources


async def list_session_sources(session_id: UUID) -> list[dict]:
    pool = await get_pool()
    
    rows = await pool.fetch(
        """
        SELECT * FROM sources
        WHERE session_id = $1
        ORDER BY retrieved_at ASC
        """,
        session_id,
    )
    
    return [dict(row) for row in rows]