from uuid import UUID

from app.db.postgres import get_pool


async def session_has_search_calls(session_id: UUID) -> bool:
    pool = await get_pool()

    source_count = await pool.fetchval(
        """
        SELECT COUNT(*)
        FROM sources
        WHERE session_id = $1
        """,
        session_id,
    )

    tool_count = await pool.fetchval(
        """
        SELECT COUNT(*)
        FROM tool_call_log
        WHERE session_id = $1
          AND tool_name ILIKE '%search%'
        """,
        session_id,
    )

    return bool(source_count or tool_count)


async def create_memory_job(session_id: UUID) -> dict:
    pool = await get_pool()

    existing = await pool.fetchrow(
        """
        SELECT *
        FROM memory_jobs
        WHERE session_id = $1
          AND status IN ('queued', 'summarizing', 'embedding', 'completed')
        ORDER BY created_at DESC
        LIMIT 1
        """,
        session_id,
    )

    if existing:
        return dict(existing)

    row = await pool.fetchrow(
        """
        INSERT INTO memory_jobs (session_id, status)
        VALUES ($1, 'queued')
        RETURNING *
        """,
        session_id,
    )

    return dict(row)


async def claim_next_memory_job() -> dict | None:
    pool = await get_pool()

    async with pool.acquire() as conn:
        async with conn.transaction():
            row = await conn.fetchrow(
                """
                SELECT *
                FROM memory_jobs
                WHERE status = 'queued'
                ORDER BY created_at ASC
                FOR UPDATE SKIP LOCKED
                LIMIT 1
                """
            )

            if not row:
                return None

            updated = await conn.fetchrow(
                """
                UPDATE memory_jobs
                SET status = 'summarizing'
                WHERE job_id = $1
                RETURNING *
                """,
                row["job_id"],
            )

            return dict(updated)


async def update_memory_job_status(
    job_id: UUID,
    status: str,
    error: str | None = None,
) -> None:
    pool = await get_pool()

    await pool.execute(
        """
        UPDATE memory_jobs
        SET status = $2,
            error = $3
        WHERE job_id = $1
        """,
        job_id,
        status,
        error,
    )


async def complete_memory_job(
    job_id: UUID,
    summary: str,
    key_topics: list[str],
    key_findings: list[str],
    sources_referenced: list[str],
    unresolved_questions: list[str],
) -> None:
    pool = await get_pool()

    await pool.execute(
        """
        UPDATE memory_jobs
        SET status = 'completed',
            summary = $2,
            key_topics = $3,
            key_findings = $4,
            sources_referenced = $5,
            unresolved_questions = $6,
            completed_at = NOW(),
            error = NULL
        WHERE job_id = $1
        """,
        job_id,
        summary,
        key_topics,
        key_findings,
        sources_referenced,
        unresolved_questions,
    )