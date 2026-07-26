from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.sessions import router as sessions_router
from app.api.research import router as research_router
from app.api.websocket import router as websocket_router
from app.api.memory import router as memory_router
from app.api.sources import router as sources_router

app = FastAPI(
    title="Meridian",
    description="Research assistant API with session memory support.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://localhost:5173",
        "http://localhost:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sessions_router)
app.include_router(research_router)
app.include_router(websocket_router)
app.include_router(memory_router)
app.include_router(sources_router)

@app.get("/health")
async def health_check():
    return {"status": "ok"}
