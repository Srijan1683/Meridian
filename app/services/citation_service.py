import re
from uuid import UUID

from app.models.sources import Source


CITATION_PATTERN = re.compile(r"\[(\d+)]")
WORD_PATTERN = re.compile(r"[a-z0-9]+")


def append_source_list(response_text: str, sources: list[Source]) -> str:
    if not sources:
        return response_text
    
    lines = [response_text.rstrip(), "", "Sources:"]
    
    for index, source in enumerate(sources, start=1):
        lines.append(f"[{index}] {source.title} - {source.url}")
        
    return "\n".join(lines)


def _source_relevance_score(paragraph: str, source: Source) -> float:
    paragraph_words = set(WORD_PATTERN.findall(paragraph.lower()))
    source_text = f"{source.title} {source.snippet}".lower()
    source_words = set(WORD_PATTERN.findall(source_text))
    overlap = len(paragraph_words & source_words)
    information_weight = min(len(source.snippet), 500) / 500

    return (overlap * 10) + information_weight


def limit_citations_per_paragraph(
    response_text: str,
    sources: list[Source],
    max_citations: int = 3,
) -> str:
    if max_citations < 1 or not sources:
        return response_text

    paragraphs = re.split(r"(\n\s*\n)", response_text)
    limited_parts: list[str] = []

    for paragraph in paragraphs:
        citation_indexes = [
            int(match.group(1))
            for match in CITATION_PATTERN.finditer(paragraph)
            if 1 <= int(match.group(1)) <= len(sources)
        ]
        unique_indexes = list(dict.fromkeys(citation_indexes))

        if len(unique_indexes) <= max_citations:
            limited_parts.append(paragraph)
            continue

        ranked_indexes = sorted(
            unique_indexes,
            key=lambda index: (
                _source_relevance_score(paragraph, sources[index - 1]),
                -index,
            ),
            reverse=True,
        )
        kept_indexes = set(ranked_indexes[:max_citations])

        limited_parts.append(
            CITATION_PATTERN.sub(
                lambda match: match.group(0)
                if int(match.group(1)) in kept_indexes
                else "",
                paragraph,
            )
        )

    return "".join(limited_parts)


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
