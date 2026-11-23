from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel

from app.models.memory import MemoryContext
from app.models.sources import Source


class ResearchMode(str, Enum):
    NORMAL = "normal"
    DEEP = "deep"


class TokenBudget(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ResearchRequest(BaseModel):
    session_id: UUID | None = None
    query: str
    mode: ResearchMode = ResearchMode.NORMAL


class ResearchResponse(BaseModel):
    session_id: UUID
    mode: ResearchMode
    response: str
    sources: list[Source]
    memory_context: MemoryContext
    token_usage: TokenBudget


class ResearchResultResponse(BaseModel):
    session_id: UUID
    message_id: UUID
    response: str
    token_count: int
    created_at: datetime
