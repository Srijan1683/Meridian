import asyncio
from uuid import uuid4

from app.db.chromadb import get_short_term_collection
from app.memory.manager import retrieve_similar, store_memory


async def main() -> None:
    session_id = f"test_{uuid4().hex}"
    collection = get_short_term_collection(session_id)

    memories = [
        {
            "text": "Quantum entanglement links particles across distance.",
            "metadata": {"topic": "physics"},
        },
        {
            "text": "Pasta recipes often use tomatoes, basil, garlic, and olive oil.",
            "metadata": {"topic": "cooking"},
        },
        {
            "text": "Neural networks learn patterns from data using layered representations.",
            "metadata": {"topic": "machine_learning"},
        },
    ]

    for memory in memories:
        await store_memory(
            collection=collection,
            memory_id=str(uuid4()),
            text=memory["text"],
            metadata=memory["metadata"],
        )

    results = await retrieve_similar(
        collection=collection,
        query_text="spooky action at a distance",
        limit=3,
        min_similarity=0.0,
    )

    print("\nTop results:\n")

    for index, result in enumerate(results, start=1):
        print(f"{index}. {result['content']}")
        print(f"   topic: {result['metadata'].get('topic')}")
        print(f"   similarity: {result['similarity_score']:.3f}")

    if results and results[0]["metadata"].get("topic") == "physics":
        print("\nSmoke test passed.")
    else:
        raise RuntimeError("Smoke test failed: expected physics result first.")


if __name__ == "__main__":
    asyncio.run(main())