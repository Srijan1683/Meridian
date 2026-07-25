from uuid import UUID

from fastapi import APIRouter

from app.db.repositories.sources import list_session_sources
from app.models.sources import Source, SourceListResponse, SourceType


router = APIRouter(prefix="/sources", tags=["sources"])


def _source_row_to_model(row: dict) -> Source:
    return Source(
        source_id=row["source_id"],
        session_id=row["session_id"],
        url=row["url"],
        title=row["title"],
        snippet=row["snippet"],
        source_type=SourceType(row["source_type"]),
        search_query=row["source_query"],
        retrieved_at=row["retrieved_at"],
        credibility_note=row.get("credibility_note"),
    )
    

@router.get("/{session_id}", response_model=SourceListResponse)
async def list_sources_for_session_endpoint(session_id: UUID):
    rows = await list_session_sources(session_id)
    
    return SourceListResponse(
        sources=[_source_row_to_model(row) for row in rows]
    )