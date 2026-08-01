from pathlib import Path

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import settings

if settings.chroma_cloud_api_key and settings.chroma_cloud_server_url:
    chroma_client = chromadb.Client(
        ChromaSettings(
            chroma_api_impl="rest",
            chroma_server_host=settings.chroma_cloud_server_url,
            chroma_server_http_port=443,
            chroma_ssl_enabled=True,
            chroma_api_key=settings.chroma_cloud_api_key,
        )
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