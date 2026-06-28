from uuid import UUID, uuid4

from app.memory.long_term import (
    format_long_term_memory_context,
    retrieve_long_term_memories
)
from app.models.research import ResearchMode, ResearchRequest, ResearchResponse, TokenBudget
from app.models.memory import MemoryContext
from app.models.sources import Source


async def build_long_term_context(query: str) -> tuple[str, int]:
    memories = await retrieve_long_term_memories(
        query=query,
        limit=3,
        min_similarity=0.7,
    )

    return format_long_term_memory_context(memories), len(memories)


async def build_research_prompt_with_memory(query: str) -> tuple[str, int]:
    long_term_context, long_term_count = await build_long_term_context(query)

    if long_term_context:
        prompt = f"""
{long_term_context}

Current user query:
{query}
""".strip()
    else:
        prompt = query

    return prompt, long_term_count


async def run_research(request: ResearchRequest) -> ResearchResponse:
    session_id = request.session_id or uuid4()

    prompt, long_term_count = await build_research_prompt_with_memory(request.query)

    response_text = (
        "Research service is ready. Long-term memory context has been loaded "
        "and will be included before the query is sent to the agent."
    )

    if prompt != request.query:
        response_text += "\n\nRelevant previous-session context was found."

    return ResearchResponse(
        session_id=session_id,
        mode=request.mode,
        response=response_text,
        sources=[],
        memory_context=MemoryContext(
            short_term_retrieved=0,
            long_term_retrieved=long_term_count,
            memories=[],
            retrieval_time_ms=0,
        ),
        token_usage=TokenBudget(),
    )