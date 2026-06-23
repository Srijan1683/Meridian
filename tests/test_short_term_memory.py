from uuid import uuid4

import pytest

from app.memory.short_term import (
    format_session_memory_context,
    retrieve_session_memories,
    store_interaction_memory,
)


@pytest.mark.asyncio
async def test_short_term_memory_retrieves_relevant_context():
    session_id = uuid4()

    await store_interaction_memory(
        session_id=session_id,
        query="What is quantum entanglement?",
        response="Quantum entanglement links particles across distance.",
        topic_tags=["physics", "quantum"],
    )

    memories = await retrieve_session_memories(
        session_id=session_id,
        query="particles connected over distance",
        limit=3,
        min_similarity=0.2,
    )

    context = format_session_memory_context(memories)

    assert memories
    assert "entanglement" in memories[0]["content"].lower()
    assert context.startswith("Relevant context from this session:")
