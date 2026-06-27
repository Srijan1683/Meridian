from uuid import UUID

from fastapi import APIRouter, HTTPException

from app.models.sessions import SessionEndRequest
from app.workers.memory_worker import end_session_and_maybe_queue_memory_job


router = APIRouter(prefix="/sessions", tags=["sessions"])

@router.post("/{session_id}/end")
async def end_session_endpoint(
    session_id: UUID,
    request: SessionEndRequest
):
    result = await end_session_and_maybe_queue_memory_job(
        session_id=session_id,
        summarize=request.summarize,
        force=False,
    )
    
    if result["session"] is None:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return result

@router.post("/{session_id}/summarize")
async def manually_summarize_session_endpoint(session_id: UUID):
    result = await end_session_and_maybe_queue_memory_job(
        session_id=session_id,
        summarize=True,
        force=True,
    )
    
    if result["session"] is None:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return result