from enum import Enum

from pydantic import BaseModel
from uuid import UUID
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