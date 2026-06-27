from fastapi import FastAPI

from app.api.sessions import router as sessions_router


app = FastAPI(
    title="Meridian",
    version="0.1.0",
)

app.include_router(sessions_router)

@app.get("/health")
async def health_check():
    return {"status": "ok"}