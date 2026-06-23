import asyncio
from uuid import uuid4

from app.memory.long_term import (
    store_long_term_memory,
    format_long_term_memory_context,
    retrieve_long_term_memories,
)

async def main() -> None:
    session_id = uuid4()
    summary_id = uuid4()

    empty_memories = await retrieve_long_term_memories(
        query="Nothing has been stored yet.",
        limit=3,
        min_similarity=0.2,
    )

    empty_context = format_long_term_memory_context(empty_memories)

    if empty_memories:
        raise RuntimeError("Bootstrap test failed: expected no memories.")

    if empty_context != "":
        raise RuntimeError("Bootstrap test failed: expected empty context.")

    await store_long_term_memory(
        session_id=session_id,
        summary=(
            "The session explored quantum computing basics, especially quantum entanglement, qubits, superposition, and why error correction matters."
            ),
        key_topics=[
            "quantum computing",
            "quantum entanglement",
            "qubits",
            "quantum error correction",
        ],
        key_findings=[
            "Qubits can represent superpositions of states.",
            "Entanglement links quantum states across particles.",
            "Quantum error correction is needed because quantum states are fragile.",
        ],
        sources_referenced=[
            "https://example.com/quantum-computing-intro",
            "https://example.com/quantum-error-correction",
        ],
        summary_id= summary_id,
        
    )
    
    memories = await retrieve_long_term_memories(
        query="What did i previously learn about entangled particles?",
        limit=3,
        min_similarity=0.2,
    )
    
    context = format_long_term_memory_context(memories)
    
    print(context)
    

    if not memories:
        raise RuntimeError("Expected at least one long-term memory.")

    if "entanglement" not in memories[0]["content"].lower():
        raise RuntimeError("Expected quantum long-term memory to be most relevant.")

    if not context.startswith("Relevant context from previous sessions:"):
        raise RuntimeError("Long-term memory context formatting failed.")

    print("\nLong-term memory smoke test passed.")


if __name__ == "__main__":
    asyncio.run(main())
