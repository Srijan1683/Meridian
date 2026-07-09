from openai import AsyncOpenAI
from app.config import settings
from app.agents.prompts import (
    get_research_prompt, 
    get_search_count,
    get_synthesis_instruction,
)
from app.db.repositories.sources import create_sources_for_search, create_source_citations
from app.db.repositories.sessions import create_session
from app.db.repositories.messages import create_message
from app.models.sessions import ConversationRole
from app.services.citation_service import (
    append_source_list,
    extract_citations,
    validate_citations,
)
from app.memory.long_term import (
    format_long_term_memory_context,
    retrieve_long_term_memories
)
from app.models.memory import MemoryContext
from app.models.research import ResearchMode, ResearchResponse, ResearchRequest, TokenBudget
from app.models.sources import Source, SourceType
from app.search.tavily import search_web


MAX_TAVILY_QUERY_LENGTH = 400

client = AsyncOpenAI(
    api_key=settings.openai_api_key,
    base_url=settings.openai_base_url,
)


async def build_long_term_context(query: str) -> tuple[str, int]:
    memories = await retrieve_long_term_memories(
        query=query,
        limit=3,
        min_similarity=0.7,
    )

    return format_long_term_memory_context(memories), len(memories)


def _trim_query(query: str) -> str:
    query = " ".join(query.split())
    
    if len(query) <= MAX_TAVILY_QUERY_LENGTH:
        return query
    
    return query[:MAX_TAVILY_QUERY_LENGTH].rsplit(" ", 1)[0]


def build_search_queries(
    user_query: str,
    mode: ResearchMode,
    long_term_context: str
) -> list[str]:
    base_query = " ".join(user_query.split())
    
    if mode == ResearchMode.NORMAL:
        queries = [
            base_query,
            f"{base_query} latest reliable sources",
        ]
        
    else:
        queries = [
            base_query,
            f"{base_query} key background context",
            f"{base_query} latest developments",
            f"{base_query} expert analysis",
            f"{base_query} challenges limitations contradictions",
            f"{base_query} future outlook",
        ]
        
    if long_term_context:
        queries.append(f"{base_query} related prior research context")
        
    max_queries = get_search_count(mode)
    return [_trim_query(query) for query in queries[:max_queries]]


def _source_row_to_model(row: dict) -> Source:
    return Source(
        source_id=row["source_id"],
        session_id=row["session_id"],
        url=row["url"],
        title=row["title"],
        snippet=row["snippet"],
        source_type=SourceType(row["source_type"]),
        search_query=row["search_query"],
        retrieved_at=row["retrieved_at"],
        credibility_note=row.get("credibility_note"),
    )


async def synthesize_response(
    user_query: str,
    mode: ResearchMode,
    search_answers: list[str],
    sources: list[Source],
    long_term_context: str,
) -> tuple[str, TokenBudget]:
    source_lines = []
    
    for index, source in enumerate(sources, start=1):
        source_lines.append(
            f"[{index}] {source.title}\n"
            f"URL: {source.url}\n"
            f"Snippet: {source.snippet}"
        )

    finding_lines = []

    for index, answer in enumerate(search_answers, start=1):
        if answer:
            finding_lines.append(f"Search {index} answer:\n{answer}")

    prompt = f"""
System behavior:
{get_research_prompt(mode)}

Synthesis instruction:
{get_synthesis_instruction(mode)}

User question:
{user_query}

Previous-session context:
{long_term_context or "None"}

Search findings:
{chr(10).join(finding_lines) or "No search answers returned."}

Sources:
{chr(10).join(source_lines) or "No sources returned."}

Write the final answer now.
""".strip()

    response = await client.chat.completions.create(
        model=settings.research_model,
        messages=[
            {
                "role": "system",
                "content": get_research_prompt(mode),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.2,
    )

    content = response.choices[0].message.content or ""

    usage = response.usage
    token_usage = TokenBudget(
        prompt_tokens=getattr(usage, "prompt_tokens", 0) if usage else 0,
        completion_tokens=getattr(usage, "completion_tokens", 0) if usage else 0,
        total_tokens=getattr(usage, "total_tokens", 0) if usage else 0,
    )

    return content, token_usage


async def run_research(request: ResearchRequest) -> ResearchResponse:
    session = await create_session(session_id=request.session_id)
    session_id = session["session_id"]

    long_term_context, long_term_count = await build_long_term_context(request.query)
    
    search_queries = build_search_queries(
        user_query=request.query,
        mode=request.mode,
        long_term_context=long_term_context,
    )
    
    all_source_rows: list[dict] = []
    search_answers: list[str] = []
    
    for search_query in search_queries:
        search_result = await search_web(
            query=search_query,
            deep=request.mode == ResearchMode.DEEP,
        )
        
        search_answers.append(search_result.answer)
    
        source_rows = await create_sources_for_search(
            session_id=session_id,
            sources=search_result.sources,
            search_query=search_query,
        )
    
        all_source_rows.extend(source_rows)
    
    sources = [_source_row_to_model(row) for row in all_source_rows]
    
    response_text, token_usage = await synthesize_response(
        user_query=request.query,
        mode=request.mode,
        search_answers=search_answers,
        sources=sources,
        long_term_context=long_term_context,
    )
    
    invalid_citations = validate_citations(
        response_text=response_text,
        sources=sources,
    )
    
    if invalid_citations:
        response_text += (
            "\n\nCitation warning: Some citation markers did not map to returned sources: "
            + ", ".join(f"[{index}]" for index in sorted(set(invalid_citations)))
        )
        
    response_with_sources = append_source_list(
        response_text=response_text,
        sources=sources,
    )
    
    assistant_message = await create_message(
        session_id=session_id,
        role=ConversationRole.ASSISTANT,
        content=response_with_sources,
        token_count=token_usage.total_tokens,
    )
    
    citations = extract_citations(
        response_text=response_text,
        sources=sources,
    )
    
    await create_source_citations(
        message_id=assistant_message["message_id"],
        citations=citations,
    )
    

    return ResearchResponse(
        session_id=session_id,
        mode=request.mode,
        response=response_with_sources,
        sources=sources,
        memory_context=MemoryContext(
            short_term_retrieved=0,
            long_term_retrieved=long_term_count,
            memories=[],
            retrieval_time_ms=0,
        ),
        token_usage=token_usage,
    )
