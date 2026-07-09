import re
from uuid import UUID

from app.models.sources import Source


CITATION_PATTERN = re.compile(r"\[(\d+)]")


def append_source_list(response_text: str, sources: list[Source]) -> str:
    if not sources:
        return response_text
    
    lines = [response_text.rstrip(), "", "Sources:"]
    
    for index, source in enumerate(sources, start=1):
        lines.append(f"[{index}] {source.title} - {source.url}")
        
    return "\n".join(lines)


def _sentence_for_position(text: str, position: int) -> str:
    start = max(
        text.rfind(".", 0, position),
        text.rfind("!", 0, position),
        text.rfind("?", 0, position),
        text.rfind("\n", 0, position),
    )
    
    end_candidates = [
        text.find(".", position),
        text.find("!", position),
        text.find("?", position),
        text.find("\n", position),
    ]
    end_candidates = [candidate for candidate in end_candidates if candidate != -1]
    
    end = min(end_candidates) if end_candidates else len(text)
    
    return text[start + 1:end + 1].strip()

def extract_citations(
    response_text: str,
    sources: list[Source],
) -> list[dict]:
    citations: list[dict] = []
    seen: set[tuple[int, UUID, str]] = set()
    
    for match in CITATION_PATTERN.finditer(response_text):
        citation_index = int(match.group(1))
        
        if citation_index < 1 or citation_index > len(sources):
            continue
        
        source = sources[citation_index - 1]
        claim_text = _sentence_for_position(response_text, match.start())
        
        key = (citation_index, source.source_id, claim_text)
        if key in seen:
            continue
        
        seen.add(key)
        
        citations.append(
            {
                "citation_index": citation_index,
                "source_id": source.source_id,
                "claim_text": claim_text,
            }
        )
        
    return citations


def validate_citations(
    response_text: str,
    sources: list[Source],
) -> list[int]:
    invalid_indexes: list[int] = []
    
    for match in CITATION_PATTERN.finditer(response_text):
        citation_index = int(match.group(1))
        
        if citation_index < 1 or citation_index > len(sources):
            invalid_indexes.append(citation_index)
            
    return invalid_indexes