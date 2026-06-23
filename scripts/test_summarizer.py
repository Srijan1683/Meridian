import asyncio
from uuid import uuid4

from app.memory.summarizer import summarize_session


async def main() -> None:
    session_id = uuid4()
    
    messages = [
        {
            "role": "user",
            "content": "What is quantum entanglement?",
        },
        {
            "role": "assistant",
            "content": (
                "Quantum entanglement is when particles share linked states, "
                "even across distance."
            ),
        },
        {
            "role": "user",
            "content": "Why does quantum error correction matter?",
        },
        {
            "role": "assistant",
            "content": (
                "Quantum error correction matters because quantum states are "
                "fragile and can decohere."
            ),
        },
    ]
    
    summary = await summarize_session(
        session_id=session_id,
        messages=messages,
    )
    
    print(summary.model_dump_json(indent=2))
    
    if not summary.summary:
        raise RuntimeError("Expected summary text.")
    
    if not summary.key_topics:
        raise RuntimeError("Expected key topics.")
    
    if not summary.key_findings:
        raise RuntimeError("Expected key findings.")
    
    print("\nSummarizer smoke test passed.")
    

if __name__ == "__main__":
    asyncio.run(main())