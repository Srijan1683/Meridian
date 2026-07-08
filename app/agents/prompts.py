from app.models.research import ResearchMode


NORMAL_RESEARCH_PROMPT = """
You are a research assistant. Answer the user's question using your web search tool.
Be concise. One or two searches should be enough. Cite your sources.
""".strip()


DEEP_RESEARCH_PROMPT = """
You are a thorough research agent. When given a question: first identify the key
angles to investigate. Search for each angle. Evaluate what you find -- look for
gaps, contradictions, and follow-up questions. Run additional searches to fill gaps.
When you have enough, synthesize a comprehensive answer. Every factual claim must
include a citation. If sources contradict each other, note it explicitly.
""".strip()


def get_research_prompt(mode: ResearchMode) -> str:
    if mode == ResearchMode.DEEP:
        return DEEP_RESEARCH_PROMPT
    
    return NORMAL_RESEARCH_PROMPT

def get_search_count(mode: ResearchMode) -> int:
    if mode == ResearchMode.DEEP:
        return 6
    
    return 2

def get_synthesis_instruction(mode: ResearchMode) -> str:
    if mode == ResearchMode.DEEP:
        return """
Write a comprehensive research answer.

Requirements:
- Every factual claim should include a citation like [1], [2], or [3].
- Use only citation numbers from the provided Sources list.
- If a factual claim cannot be cited, write "(unverified)" after it.
- Cover the key angles investigated.
- Mention gaps, uncertainty, or contradictions when present.
- If sources contradict each other, note it explicitly with citations.
- Use only the provided sources.
- Do not invent sources.
- Do not include a source list; it will be appended automatically.
    """.strip()
    
    return """
Write a concise research answer.

Requirements:
- Answer directly.
- Every factual claim must include a citation like [1] or [2].
- Use only citation numbers from the provided Sources list.
- If a factual claim cannot be cited, write "(unverified)" after it.
- Use only the provided sources.
- Do not invent sources.
- Do not include a source list; it will be appended automatically.
""".strip()
