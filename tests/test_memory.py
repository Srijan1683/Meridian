from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

import app.services.research_service as research_service
import app.workers.memory_worker as memory_worker
from app.models.research import ResearchMode, ResearchRequest


@pytest.mark.asyncio
async def test_long_term_memory_surfaces_in_next_session(monkeypatch, patch_research):
    state = patch_research

    session1 = uuid4()

    await research_service.run_research(
        ResearchRequest(
            session_id=session1,
            query="Research quantum computing",
            mode=ResearchMode.NORMAL,
        )
    )

    job_id = uuid4()

    async def fake_end_session(session_id):
        session = state["sessions"][session_id]
        session["status"] = "ended"
        session["ended_at"] = datetime.now(timezone.utc)
        return session

    async def fake_create_memory_job(session_id):
        job = {
            "job_id": job_id,
            "session_id": session_id,
            "status": "queued",
        }
        state["memory_jobs"].append(job)
        return job

    async def fake_list_session_messages(session_id):
        return [
            message
            for message in state["messages"]
            if message["session_id"] == session_id
        ]

    async def fake_summarize_session(session_id, messages):
        return SimpleNamespace(
            summary=(
                "Session 1 researched quantum computing, qubits, and why "
                "quantum error correction matters."
            ),
            key_topics=["quantum computing", "quantum error correction"],
            key_findings=[
                "Quantum states are fragile and require error correction."
            ],
            sources_referenced=["https://example.com/source-1"],
            unresolved_questions=[],
        )

    async def fake_update_memory_job_status(job_id, status, error=None):
        state["memory_jobs"][0]["status"] = status
        state["memory_jobs"][0]["error"] = error

    async def fake_store_long_term_memory(
        session_id,
        summary,
        key_topics,
        key_findings,
        sources_referenced,
        unresolved_questions,
        summary_id,
    ):
        state["long_term_memories"].append(
            {
                "session_id": session_id,
                "summary_id": summary_id,
                "summary": summary,
                "key_topics": key_topics,
                "key_findings": key_findings,
                "sources_referenced": sources_referenced,
                "unresolved_questions": unresolved_questions,
            }
        )

    async def fake_complete_memory_job(
        job_id,
        summary,
        key_topics,
        key_findings,
        sources_referenced,
        unresolved_questions,
    ):
        state["completed_jobs"].append(
            {
                "job_id": job_id,
                "summary": summary,
                "key_topics": key_topics,
                "key_findings": key_findings,
                "sources_referenced": sources_referenced,
                "unresolved_questions": unresolved_questions,
            }
        )
        state["memory_jobs"][0]["status"] = "completed"

    monkeypatch.setattr(memory_worker, "end_session", fake_end_session)
    monkeypatch.setattr(memory_worker, "create_memory_job", fake_create_memory_job)
    monkeypatch.setattr(
        memory_worker,
        "list_session_messages",
        fake_list_session_messages,
    )
    monkeypatch.setattr(memory_worker, "summarize_session", fake_summarize_session)
    monkeypatch.setattr(
        memory_worker,
        "update_memory_job_status",
        fake_update_memory_job_status,
    )
    monkeypatch.setattr(
        memory_worker,
        "store_long_term_memory",
        fake_store_long_term_memory,
    )
    monkeypatch.setattr(
        memory_worker,
        "complete_memory_job",
        fake_complete_memory_job,
    )
    async def fake_session_is_worth_summarizing(session_id):
        return True

    monkeypatch.setattr(
        memory_worker,
        "session_is_worth_summarizing",
        fake_session_is_worth_summarizing,
    )

    end_result = await memory_worker.end_session_and_maybe_queue_memory_job(
        session1,
        summarize=True,
    )

    assert end_result["session"]["status"] == "ended"
    assert end_result["memory_job"]["status"] == "queued"

    await memory_worker.process_memory_job(end_result["memory_job"])

    assert state["memory_jobs"][0]["status"] == "completed"
    assert state["long_term_memories"]

    session2 = uuid4()

    result2 = await research_service.run_research(
        ResearchRequest(
            session_id=session2,
            query="How does quantum error correction relate?",
            mode=ResearchMode.NORMAL,
        )
    )

    assert result2.memory_context.long_term_retrieved == 1
    assert "Prior research says quantum computing needs error correction" in result2.response
