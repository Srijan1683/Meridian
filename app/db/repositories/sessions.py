from uuid import UUID

from app.db.postgres import get_pool


async def create_session(
    session_id: UUID | None = None,
    title: str | None = None,
) -> dict:
    pool = await get_pool()
    
    if session_id:
        row = await pool.fetchrow(
            """
            INSERT INTO sessions (session_id, title)
            VALUES ($1, $2)
            ON CONFLICT (session_id) DO UPDATE
            SET updated_at = NOW()
            RETURNING *
            """,
            session_id,
            title,
        )
    else:
        row = await pool.fetchrow(
            """
            INSERT INTO sessions (title)
            VALUES ($1)
            RETURNING *
            """,
            title,
        )
    
    return dict(row)


async def end_session(session_id: UUID) -> dict | None:
    pool = await get_pool()
    
    row = await pool.fetchrow(
        """
        UPDATE sessions
        SET status = 'ended',
            ended_at = COALESCE(ended_at, NOW()),
            updated_at = NOW()
        WHERE session_id = $1
        RETURNING *
        """,
        session_id,
    )
    
    return dict(row) if row else None


async def list_timed_out_sessions(timeout_minutes: int = 30) -> list[dict]:
    pool = await get_pool()
    
    rows = await pool.fetch(
        """
        SELECT *
        FROM sessions
        WHERE status = 'active'
            AND updated_at <= NOW() - ($1 * INTERVAL '1 minute')
        """,
        timeout_minutes,
    )
    
    return [dict(row) for row in rows]
