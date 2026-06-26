import asyncio
from uuid import UUID

from app.config import settings
from app.db.repositories.memory_jobs import (
    claim_next_memory_job,
    complete_memory_job,
    create_memory_job,
    session_has_search_calls,
    update_memory_job_status,
)
from app.db.repositories.messages import count_session_messages, list_session_messages
from app.db.repositories.sessions import end_session, list_timed_out_sessions
from app.memory.long_term import store_long_term_memory
from app.memory.summarizer import summarize_session


async def session_is_worth_summarizing(session_id: UUID) -> bool:
    message_count = await count_session_messages(session_id)
    
    if message_count >= settings.min_messages_for_auto_summarize:
        return True
    
    return await session_has_search_calls(session_id)


async def queue_session_memory_job(
    session_id: UUID,
    force: bool = False,
) -> dict | None:
    if not force and not await session_is_worth_summarizing(session_id):
        return None
    
    return await create_memory_job(session_id)


async def end_session_and_maybe_queue_memory_job(
    session_id: UUID,
    summarize: bool = True,
    force: bool = False,
) -> dict:
    session = await end_session(session_id)
    
    job = None
    if summarize:
        job = await queue_session_memory_job(session_id=session_id, force=force)
        
    return {
        "session": session,
        "memory_job": job,
    }
    
    
async def queue_timed_out_sessions(timeout_minutes: int = 30) -> int:
    sessions = await list_timed_out_sessions(timeout_minutes=timeout_minutes)
    queued = 0
    
    for session in sessions:
        session_id = session["session_id"]
        await end_session(session_id)
        
        job = await queue_session_memory_job(session_id=session_id)
        if job:
            queued += 1
            
    return queued


async def process_memory_job(job: dict) -> None:
    job_id = job["job_id"]
    session_id = job["session_id"]
    
    try:
        messages = await list_session_messages(session_id)
        
        summary = await summarize_session(
            session_id=session_id,
            messages=messages,
        )
        
        await update_memory_job_status(job_id, "embedding")
        
        await store_long_term_memory(
            session_id=session_id,
            summary=summary.summary,
            key_topics=summary.key_topics,
            key_findings=summary.key_findings,
            sources_referenced=summary.sources_referenced,
            unresolved_questions=summary.unresolved_questions,
            summary_id=job_id,
        )

        await complete_memory_job(
            job_id=job_id,
            summary=summary.summary,
            key_topics=summary.key_topics,
            key_findings=summary.key_findings,
            sources_referenced=summary.sources_referenced,
            unresolved_questions=summary.unresolved_questions,
        )
        
    except Exception as exc:
        await update_memory_job_status(
            job_id=job_id,
            status="failed",
            error=str(exc),
        )
        
        
async def run_memory_worker(
    poll_interval_seconds: int = 5,
    timeout_minutes: int = 30,
) -> None:
    while True:
        await queue_timed_out_sessions(timeout_minutes=timeout_minutes)
        
        job = await claim_next_memory_job()
        if job:
            await process_memory_job(job)
            continue
        
        await asyncio.sleep(poll_interval_seconds)