from typing import Literal
from enum import Enum

from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from app.models.memory import MemoryContext


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
    
class Source(BaseModel):
    source_id: UUID
    url: str
    title: str
    snippet: str
    source_type: Literal["web", "paper", "article", "forum", "documentation"]
    retrieved_at: datetime
    search_query: str
    credibility_note: str | None = None
    
class ResearchResponse(BaseModel):
    session_id: UUID
    mode: ResearchMode
    response: str
    sources: list[Source]
    memory_context: MemoryContext
    token_usage: TokenBudget