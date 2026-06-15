from typing import Any

from chromadb.api.models.Collection import Collection

from app.memory.embeddings import embed_text


def _distance_to_similarity(distance: float) -> float:
    return 1 - distance


async def store_memory(
    collection: Collection,
    memory_id: str,
    text: str,
    metadata: dict[str, Any] | None = None,
) -> None:
    embedding = await embed_text(text)

    collection.add(
        ids=[memory_id],
        documents=[text],
        embeddings=[embedding],
        metadatas=[metadata or {}],
    )


async def retrieve_similar(
    collection: Collection,
    query_text: str,
    limit: int = 5,
    min_similarity: float = 0.7,
) -> list[dict[str, Any]]:
    query_embedding = await embed_text(query_text)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=limit,
        include=["documents", "metadatas", "distances"],
    )

    memories: list[dict[str, Any]] = []

    ids = (results.get("ids") or [[]])[0]
    documents = (results.get("documents") or [[]])[0]
    metadatas = (results.get("metadatas") or [[]])[0]
    distances = (results.get("distances") or [[]])[0]

    for memory_id, document, metadata, distance in zip(
        ids,
        documents,
        metadatas,
        distances,
    ):
        similarity = _distance_to_similarity(distance)

        if similarity < min_similarity:
            continue

        memories.append(
            {
                "memory_id": memory_id,
                "content": document,
                "metadata": metadata or {},
                "similarity_score": similarity,
            }
        )

    return memories
