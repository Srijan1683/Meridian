import json
from datetime import datetime, timezone
from uuid import UUID

from openai import AsyncOpenAI

from app.config import settings
from app.models.memory import SessionSummary


client = AsyncOpenAI(
    api_key=settings.openai_api_key,
    base_url=settings.openai_base_url,
)


def _format_messages_for_summary(messages: list[dict]) -> str:
    lines: list[str] = []
    
    for message in messages:
        role = message.get("role", "unknown")
        content = message.get("content", "")
        lines.append(f"{role.upper()}: {content}")
        
    return "\n\n".join(lines)


def _build_summary_prompt(messages: list[dict]) -> str:
    transcript = _format_messages_for_summary(messages)
    
    return f"""
Summarize this research session.

Extract:
- main summary
- key topics
- key findings
- sources referenced
- unresolved questions

Return only valid JSON with this shape:
{{
    "summary": "short summary of this session",
    "key_topics": ["topic 1", "topic 2"],
    "key_findings": ["finding 1", "finding 2"],
    "sources_referenced": ["source 1", "source 2"],
    "unresolved_questions": ["question 1", "questions 2"]
}}

Session transcript:
{transcript}
""".strip()


async def summarize_session(
    session_id: UUID,
    messages: list[dict],
) -> SessionSummary:
    prompt = _build_summary_prompt(messages)
    
    response = await client.chat.completions.create(
        model=settings.summary_model,
        messages=[
            {
                "role": "system",
                "content": "You summarize research sessions into structured memory.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.2,
    )
    
    content = response.choices[0].message.content or "{}"
    data = json.loads(content)
    
    return SessionSummary(
        session_id=session_id,
        summary=data.get("summary", ""),
        key_topics=data.get("key_topics", []),
        key_findings=data.get("key_findings", []),
        sources_referenced=data.get("sources_referenced", []),
        unresolved_questions=data.get("unresolved_questions", []),
        generated_at=datetime.now(timezone.utc),
    )