from enum import Enum

from pydantic import BaseModel, HttpUrl
from uuid import UUID
from datetime import datetime


class SourceType(str, Enum):
    WEB = "web"
    PAPER = "paper"
    ARTICLE = "article"
    FORUM = "forum"
    DOCUMENTATION = "documentation"
    
class Source(BaseModel):
    source_id: UUID
    session_id: UUID
    url: HttpUrl
    title: str
    snippet: str
    source_type: SourceType = SourceType.WEB
    search_query: str
    retrieved_at: datetime
    credibility_note: str | None = None
    
class SourceCitation(BaseModel):
    citation_id: UUID
    message_id: UUID
    source_id: UUID
    citation_index: int
    claim_text: str
    
class SourceListResponse(BaseModel):
    sources: list[Source]
    
class SearchResult(BaseModel):
    title: str
    url: str
    snippet: str
    source_type: SourceType = SourceType.WEB
    
class SearchResponse(BaseModel):
    answer: str
    sources: list[SearchResult]
    citations: list[str] = []