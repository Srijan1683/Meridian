from fastapi import APIRouter

from app.models.research import ResearchRequest, ResearchResponse
from app.services.research_service import run_research


router = APIRouter(prefix="/research", tags=["research"])


@router.post("", response_model=ResearchResponse)
async def research_endpoint(request: ResearchRequest):
    return await run_research(request)