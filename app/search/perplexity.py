import httpx

from app.config import settings
from app.models.sources import SearchResponse, SearchResult, SourceType


class PerplexitySearchError(RuntimeError):
    pass


def _extract_answer(data: dict) -> str:
    choices = data.get("choices") or []
    
    if not choices:
        return ""
    
    message = choices[0].get("message") or {}
    return message.get("content") or ""


def _extract_sources(data: dict) -> list[SearchResult]:
    search_results = data.get("search_results") or []
    sources: list[SearchResult] = []
    
    for result in search_results:
        url = result.get("url")
        if not url:
            continue
        
        sources.append(
            SearchResult(
                title=result.get("title") or url,
                url=url,
                snippet=result.get("snippet") or "",
                source_type=SourceType.WEB,
            )
        )
        
    return sources


async def search_web(
    query: str,
    *,
    deep: bool = False,
    max_tokens: int = 1200,
) -> SearchResponse:
    system_prompt = (
        "You are a web research assistant. Search the open web and answer with "
        "concise, factual information grounded in the cited sources."
    )
    
    if deep:
        system_prompt += (
            " Investigate from multiple angles, identify gaps, and prefer "
            "specific follow-up searches over broad restatements."
        )
        
    payload = {
        "model": settings.perplexity_model,
        "messages": [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": query,
            },
        ],
        "max_tokens": max_tokens,
        "temperature": 0.2,
        "web_search_options": {
            "search_mode": "web",
            "return_related_questions": True,
        },
    }
    
    headers = {
        "Authorization": f"Bearer {settings.perplexity_api_key}",
        "Content-Type": "application/json",
    }
    
    url = f"{settings.perplexity_base_url.rstrip('/')}/v1/sonar"
    
    async with httpx.AsyncClient(timeout=45) as client:
        response = await client.post(url, json=payload, headers=headers)
        
    if response.status_code >= 400:
        raise PerplexitySearchError(
            f"Perplexity search failed with {response.status_code}: {response.text}"
        )
        
    data = response.json()
    
    return SearchResponse(
        answer=_extract_answer(data),
        sources=_extract_sources(data),
        citations=data.get("citations") or []
    )