from app.models.research import ResearchMode
from app.search.tavily import search_web


async def web_search_tool(
    query: str,
    mode: ResearchMode = ResearchMode.NORMAL,
) -> dict:
    result = await search_web(
        query=query,
        deep=mode == ResearchMode.DEEP,
    )
    
    return {
        "answer": result.answer,
        "sources": [source.model_dump() for source in result.sources],
        "citations": result.citations,
    }