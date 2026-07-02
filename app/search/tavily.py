import httpx

from app.config import settings
from app.models.sources import SearchResponse, SearchResult, SourceType


class TavilySearchError(RuntimeError):
    pass


def _extract_sources(data: dict) -> list[SearchResult]:
    results = data.get("results") or []
    sources: list[SearchResult] = []
    
    for result in results:
        url = result.get("url")
        if not url:
            continue
        
        
        sources.append(
            SearchResult(
                title=result.get("title") or url,
                url=url,
                snippet=result.get("content") or "",
                source_type=SourceType.WEB,
            )
        )
        
    return sources


async def search_web(
    query: str,
    *,
    deep: bool = False,
    max_results: int = 5,
) -> SearchResponse:
    payload = {
        "query": query,
        "search_depth": "advanced" if deep else "basic",
        "include_answer": "advanced" if deep else "basic",
        "include_raw_content": False,
        "max_results": max_results,
        "include_usage": True,
    }
    
    headers = {
        "Authorisation": f"Bearer {settings.tavily_api_key}",
        "Content_Type": "applications/json",
    }
    
    url = f"{settings.tavily_base_url.rstrip('/')}/search"
    
    async with httpx.AsyncClient(timeout=45) as client:
        response = await client.post(url, json=payload, headers=headers)
        
    if response.status_code >= 400:
        raise TavilySearchError(
            f"Tavily search failed with {response.status_code}: {response.text}"
        )
        
    data = response.json()
    
    return SearchResponse(
        answer=data.get("answer") or "",
        sources=_extract_sources(data),
        citations=[source.url for source in _extract_sources(data)],
    )