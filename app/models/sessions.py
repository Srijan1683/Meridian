from enum import Enum 

from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class SessionStatus(str, Enum):
    ACTIVE = "active"
    ENDED = "ended"
    
class SessionCreate(BaseModel):
    title: str | None = None
    
class Session(BaseModel):
    session_id: UUID
    title: str | None = None
    status: SessionStatus
    created_at: datetime
    updated_at: datetime
    ended_at: datetime | None = None
    
class SessionEndRequest(BaseModel):
    summarize: bool = True
    
class ConversationRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    
class ConversationMessage(BaseModel):
    message_id: UUID
    session_id: UUID
    role: ConversationRole
    content: str
    created_at: datetime