from pathlib import Path

import chromadb


CHROMA_PATH = Path("chroma_data")

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