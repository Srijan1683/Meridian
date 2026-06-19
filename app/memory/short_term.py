from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.db.chromadb import get_short_term_collection
from app.memory.manager import retrieve_similar, store_memory


def _build_interaction_text(query: str, response: str) -> str:
    return f"User: {query}\n\nAssistant: {response}"


async def store_interaction_memory(
    session_id: UUID,
    query: str,
    response: str,
    message_id: UUID | None = None,
    topic_tags: list[str] | None = None,
) -> str:
    collection = get_short_term_collection(str(session_id))
    memory_id = str(uuid4())
    
    text = _build_interaction_text(query=query, response=response)
    
    metadata = {
        "session_id": str(session_id),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "topic_tags": ",".join(topic_tags or []),
        "memory_type": "short_term",
    }
    
    if message_id:
        metadata["message_id"] = str(message_id)
    
    await store_memory(
        collection=collection,
        memory_id=memory_id,
        text=text,
        metadata=metadata,
    )
    
    return memory_id


async def retrieve_session_memories(
    session_id: UUID,
    query: str,
    limit: int = 5,
    min_similarity: float = 0.7,
) -> list[dict]:
    collection = get_short_term_collection(str(session_id))
    
    return await retrieve_similar(
        collection=collection,
        query_text=query,
        limit=limit,
        min_similarity=min_similarity,
    )
    
    
def format_session_memory_context(memories: list[dict]):
    if not memories:
        return ""
    
    lines = ["Relevant context from this session:"]
    
    for index, memory in enumerate(memories, start=1):
        content = memory["content"]
        similarity = memory["similarity_score"]
        lines.append(f"\n[{index}] {content}\nRelevance: {similarity:.2f}")
        
    return "\n".join(lines)