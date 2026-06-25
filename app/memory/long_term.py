from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.db.chromadb import get_long_term_collection
from app.memory.manager import retrieve_similar, store_memory


def _build_summary_text(
    summary: str,
    key_topics: list[str],
    key_findings: list[str],
    sources_referenced: list[str] | None = None,
    unresolved_questions: list[str] | None = None,
) -> str:
    lines = [
        "In a previous session, you researched:",
        summary,
        "",
        "Main topics:",
        ", ".join(key_topics),
        "",
        "Key findings:",
        "\n".join(f"- {finding}" for finding in key_findings),
    ]
    
    if sources_referenced:
        lines.extend(
            [
                "",
                "Sources referenced:",
                "\n".join(f"- {source}" for source in sources_referenced),
            ]
        )
        
    if unresolved_questions:
        lines.extend(
            [
                "",
                "Unresolved questions:",
                "\n".join(f"- {question}" for question in unresolved_questions),
            ]
        )
        
    return "\n".join(lines)


async def store_long_term_memory(
    session_id: UUID,
    summary: str,
    key_topics: list[str],
    key_findings: list[str],
    sources_referenced: list[str] | None = None,
    unresolved_questions: list[str] | None = None,
    summary_id: UUID | None = None,
) -> str:
    collection = get_long_term_collection()
    memory_id = str(uuid4())
    
    text = _build_summary_text(
        summary=summary,
        key_findings=key_findings,
        key_topics=key_topics,
        sources_referenced=sources_referenced,
        unresolved_questions=unresolved_questions,
    )
    
    metadata = {
        "session_id": str(session_id),
        "summary_id": str(summary_id or uuid4()),
        "key_topics": ",".join(key_topics),
        "key_findings": ",".join(key_findings),
        "sources_referenced": ",".join(sources_referenced or []),
        "unresolved_questions": ",".join(unresolved_questions or []),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "memory_type": "long_term",
    }
    
    await store_memory(
        collection=collection,
        memory_id=memory_id,
        text=text,
        metadata=metadata,
    )
    
    return memory_id


async def retrieve_long_term_memories(
    query: str,
    limit: int = 5,
    min_similarity: float = 0.7,
) -> list[dict]:
    collection = get_long_term_collection()
    
    return await retrieve_similar(
        collection=collection,
        query_text=query,
        limit=limit,
        min_similarity=min_similarity,
    )
    
    
def format_long_term_memory_context(memories: list[dict]) -> str:
    if not memories:
        return ""
    
    lines = ["Relevant context from previous sessions:"]
    
    for index, memory in enumerate(memories, start=1):
        content = memory["content"]
        similarity = memory["similarity_score"]
        lines.append(f"\n[{index}] {content}\nRelevance: {similarity:.2f}")
        
    return "\n".join(lines)