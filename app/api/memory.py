from time import perf_counter
from uuid import UUID

from fastapi import APIRouter

from app.memory.long_term import (
    format_long_term_memory_context,
    retrieve_long_term_memories,
)
from app.memory.short_term import (
    format_session_memory_context,
    retrieve_session_memories,
)
from app.models.memory import MemoryContext
from app.api.sessions import manually_summarize_session_endpoint


router = APIRouter(prefix="/memory", tags=["memory"])


@router.get("/{session_id}/short_term", response_model=MemoryContext)
async def get_short_term_memory_context_endpoint(
    session_id: UUID,
    query: str,
    limit: int = 5,
    min_similarity: float = 0.7,
):
    start = perf_counter()
    memories = await retrieve_session_memories(
        session_id=session_id,
        query=query,
        limit=limit,
        min_similarity=min_similarity,
    )
    
    context = format_session_memory_context(memories)
    
    return MemoryContext(
        short_term_retrieved=len(memories),
        long_term_retrieved=0,
        memories=[],
        retrieval_time_ms=int((perf_counter() - start) * 1000)
    )
    

@router.get("/long-term", response_model=MemoryContext)
async def get_long_term_memory_context_endpoint(
    query: str,
    limit: int = 5,
    min_similarity: float = 0.7,
):
    start = perf_counter()
    
    memories = await retrieve_long_term_memories(
        query=query,
        limit=limit,
        min_similarity=min_similarity,
    )
    
    context = format_long_term_memory_context(memories)
    
    return MemoryContext(
        short_term_retrieved=0,
        long_term_retrieved=len(memories),
        memories=[],
        retrieval_time_ms=int((perf_counter() - start) * 1000),
    )
    

@router.post("/{session_id}/summarise")
async def summarize_session_memory_endpoint(session_id: UUID):
    return await manually_summarize_session_endpoint(session_id)