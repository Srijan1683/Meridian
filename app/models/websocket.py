from enum import Enum

from pydantic import BaseModel
from datetime import datetime


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

class WSMessage(BaseModel):
    type: WSMessageType
    data: dict
    timestamp: datetime