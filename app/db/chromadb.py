from pathlib import Path

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import settings

if settings.chroma_api_key and settings.chroma_tenant and settings.chroma_database:
    chroma_client = chromadb.CloudClient(
        tenant=settings.chroma_tenant,
        database=settings.chroma_database,
        api_key=settings.chroma_api_key,
    )
else:
    CHROMA_PATH = Path(settings.chroma_path)
    chroma_client = chromadb.PersistentClient(path=str(CHROMA_PATH))


def get_short_term_collection(session_id: str):
    return chroma_client.get_or_create_collection(
        name=f"short_term_{session_id}",
        metadata={"hnsw:space": "cosine"},
    )
   
def get_long_term_collection():
    return chroma_client.get_or_create_collection(
        name="long_term_memory",
        metadata={"hnsw:space": "cosine"},
    )