import asyncio
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.models.research import ResearchRequest
from app.models.websocket import WSMessageType, WSResearchRequest, ws_message
from app.services.research_service import run_research_streaming


router = APIRouter()


class ResearchConnection:
    def __init__(self, websocket: WebSocket):
        self.websocket = websocket
        self.cancelled = False
        self.disconnected: False
        self.task: asyncio.Task | None = None
        
    async def send(self, message_type: WSMessageType, data: dict) -> None:
        if self.disconnected:
            return
        
        await self.websocket.send_json(ws_message(message_type, data))
        
    def is_cancelled(self) -> bool:
        return self.cancelled
    

async def _run_research_for_connection(
    connection: ResearchConnection,
    request: WSResearchRequest,
) -> None:
    try:
        result = await run_research_streaming(
            request=ResearchRequest(
                session_id=request.session_id,
                query=request.query,
                mode=request.mode,
            ),
            progress=connection.send,
            is_cancelled=connection.is_cancelled,
        )
        
        await connection.send(
            WSMessageType.DONE,
            {
                "session_id": str(result.session_id),
                "cancelled": connection.cancelled,
                "response": result.response,
                "source_count": len(result.sources),
                "token_usage": result.token_usage.model_dump(),
            },
        )
        
    except Exception as exc:
        await connection.send(
            WSMessageType.EROR,
            {
                "error": str(exc),
            },
        )
        
        
@router.websocket("/ws/research")
async def websocket_research_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    connection = ResearchConnection(websocket)
    
    try:
        while True:
            payload = await websocket.receive_json()
            message_type = payload.get("type")
            
            if message_type == WSMessageType.CANCEL:
                connection.cancelled = True
                await connection.send(
                    WSMessageType.DONE,
                    {
                        "cancelled": True,
                        "response": "Cancellation requested. Partial results will be stored if available.",
                    },
                )
                continue
            
            if message_type != WSMessageType.QUERY.value:
                await connection.send(
                    WSMessageType.ERROR,
                    {
                        "error": "Unsupported websocket messsage type.",
                    },
                )
                continue
            
            if connection.task and not connection.task.done():
                await connection.send(
                    WSMessageType.ERROR,
                    {
                        "error": "A research task is already running for this connection.",
                    },
                )
                continue
            
            request = WSResearchRequest.model_validate(payload.get("data") or {})
            connection.cancelled = False
            connection.task = asyncio.create_task(
                _run_research_for_connection(connection, request)
            )
            
    except WebSocketDisconnect:
        connection.disconnected = True
        
    finally:
        connection.disconnected = True