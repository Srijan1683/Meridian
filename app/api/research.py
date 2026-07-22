from uuid import UUID

from fastapi import APIRouter, HTTPException

from app.db.repositories.messages import get_latest_assistant_message
from app.models.research import ResearchResultResponse
from app.models.research import ResearchRequest, ResearchResponse
from app.services.research_service import run_research


router = APIRouter(prefix="/research", tags=["research"])


@router.post("", response_model=ResearchResponse)
async def research_endpoint(request: ResearchRequest):
    return await run_research(request)

@router.get("/{session_id}/latest", response_model=ResearchResultResponse)
async def latest_research_result_endpoint(session_id: UUID):
    message = await get_latest_assistant_message(session_id)
    
    if message is None:
        raise HTTPException(
            status_code=404,
            detail="No completed research result found for this session.",
        )
        
    return ResearchResultResponse(
        session_id=message["session_id"],
        message_id=message["message_id"],
        response=message["content"],
        token_count=message["token_count"],
        created_at=message["created_at"],
    )
