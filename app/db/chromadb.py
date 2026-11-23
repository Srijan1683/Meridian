from functools import lru_cache
from pathlib import Path

import chromadb

from app.config import settings


@lru_cache
def get_chroma_client():
    if settings.chroma_api_key and settings.chroma_tenant and settings.chroma_database:
        return chromadb.CloudClient(
            tenant=settings.chroma_tenant,
            database=settings.chroma_database,
            api_key=settings.chroma_api_key,
        )

    return chromadb.PersistentClient(path=str(Path(settings.chroma_path)))


def get_short_term_collection(session_id: str):
    return get_chroma_client().get_or_create_collection(
        name=f"short_term_{session_id}",
        metadata={"hnsw:space": "cosine"},
    )


def get_long_term_collection():
    return get_chroma_client().get_or_create_collection(
        name="long_term_memory",
        metadata={"hnsw:space": "cosine"},
    )
