from enum import Enum

from pydantic import BaseModel
from datetime import datetime, timezone
from uuid import UUID

from app.models.research import ResearchMode
from app.models.sources import Source


class WSMessageType(str, Enum):
    # Client to Server
    QUERY = "query"
    CANCEL = "cancel"
    # Server to Client
    SEARCHING = "searching"
    CONTENT = "content"
    SOURCE = "source"
    MEMORY = "memory"
    DONE = "done"
    ERROR = "error"


class WSResearchRequest(BaseModel):
    query: str
    mode: ResearchMode = ResearchMode.NORMAL
    session_id: UUID | None = None


class WSMessage(BaseModel):
    type: WSMessageType
    data: dict
    timestamp: datetime
    

def ws_message(message_type: WSMessageType, data: dict) -> dict:
    return {
        "type": message_type.value,
        "data": data,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


class WSResearchState(BaseModel):
    session_id: UUID
    cancelled: bool = False
    partial_response: str = ""
    sources: list[Source] = []