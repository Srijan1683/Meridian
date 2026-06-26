from uuid import UUID

from app.db.postgres import get_pool


async def list_session_messages(session_id: UUID) -> list[dict]:
    pool = await get_pool()
    
    rows = await pool.fetch(
        """
        SELECT message_id, session_id, role, content, token_count, created_at
        FROM conversation_history
        WHERE session_id = $1
        ORDER BY created_at ASC
        """,
        session_id,
    )
    
    return [dict(row) for row in rows]


async def count_session_messages(session_id: UUID) -> int:
    pool = await get_pool()
    
    return await pool.fetchval(
        """
        SELECT COUNT(*)
        FROM conversation_history
        WHERE session_id = $1
        """,
        session_id,
    )