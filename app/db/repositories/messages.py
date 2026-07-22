from uuid import UUID

from app.db.postgres import get_pool
from app.models.sessions import ConversationRole


async def create_message(
    session_id: UUID,
    role: ConversationRole,
    content: str,
    token_count: int = 0,
) -> dict:
    pool = await get_pool()
    
    row = await pool.fetchrow(
        """
        INSERT INTO conversation_history (
            session_id,
            role,
            content,
            token_count
        )
        VALUES ($1, $2, $3, $4)
        RETURNING *
        """,
        session_id,
        role.value,
        content,
        token_count,
    )
    
    return dict(row)


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


async def get_latest_assistant_message(session_id: UUID) -> dict | None:
    pool = await get_pool()
    
    row = await pool.fetchrow(
        """
        SELECT message_id, session_id, role, content, token_count, created_at
        FROM conversation_history
        WHERE session_id = $1
            AND role = 'assistant'
        ORDER BY created_at DESC
        LIMIT 1
        """,
        session_id,
    )
    
    return dict(row) if row else None
