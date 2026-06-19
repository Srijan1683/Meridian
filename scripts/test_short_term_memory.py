import asyncio
from uuid import uuid4

from app.memory.short_term import (
    format_session_memory_context,
    retrieve_session_memories,
    store_interaction_memory,
)

async def main() -> None:
    session_id = uuid4()
    
    await store_interaction_memory(
        session_id=session_id,
        query="What is quantum entanglement?",
        response="Quantum entanglement links particles so their states are connected across distance.",
        topic_tags=["physics", "quantum"],
    )
    
    await store_interaction_memory(
        session_id=session_id,
        query="How do i make tomato pasta?",
        response="Use tomatoes, basil, garlic, olive oil, and pasta.",
        topic_tags=["cooking"],
    )
    
    await store_interaction_memory(
        session_id=session_id,
        query="What are neural networks?",
        response="Neural networks learn patterns from data using layered representations.",
        topic_tags=["machine-learning"],
    )
    
    memories = await retrieve_session_memories(
        session_id=session_id,
        query="What did we say about particles affecting each other?",
        limit=3,
        min_similarity=0.2,
    )
    
    context = format_session_memory_context(memories)
    
    print(context)
    
    if not memories:
        raise RuntimeError("Expected at least one memory.")
    
    if "entanglement" not in memories[0]["content"].lower():
        raise RuntimeError("Expected quantum memory to be most relevant.")
    
    if not context.startswith("Relevant context from this session:"):
        raise RuntimeError("Memory context formatting failed.")
    
    print("\nShort-term memory smoke test passed.")
    

if __name__ == "__main__":
    asyncio.run(main())