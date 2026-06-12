from typing import Enum, Literal

from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class MemoryType(str, Enum):
    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"
    
class MemoryEntry(BaseModel):
    memory_id: UUID
    memory_type: MemoryType
    session_id: UUID
    content: str
    metadata: dict
    similarity_score: float | None = None
    created_at: datetime
    
class MemoryContext(BaseModel):
    short_term_retrieved: int
    long_term_retrieved: int
    memories: list[MemoryEntry]
    retrieval_time_ms: int
    
class SessionSummary(BaseModel):
    session_id: UUID
    summary: str
    key_topics: list[str]
    key_findings: list[str]
    sources_referenced: list[str]
    generated_at: datetime
    
class MemoryJobStatus(BaseModel):
    session_id: UUID
    job_id: UUID
    status: Literal["queued", "summarizing", "embedding", "completed", "failed"]
    created_at: datetime
    completed_at: datetime | None = None