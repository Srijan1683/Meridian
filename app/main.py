from fastapi import FastAPI

from app.api.sessions import router as sessions_router
from app.api.research import router as research_router

app = FastAPI(
    title="Meridian",
    description="Research assistant API with session memory support.",
    version="0.1.0",
)

app.include_router(sessions_router)
app.include_router(research_router)

@app.get("/health")
async def health_check():
    return {"status": "ok"}
