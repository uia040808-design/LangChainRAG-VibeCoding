"""
会话管理业务逻辑
"""
from typing import List
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.session import ChatSession
from app.models.message import Message


async def create_session(
    db: AsyncSession,
    user_id: str,
    title: str = "新会话",
) -> ChatSession:
    """创建新会话"""
    session = ChatSession(user_id=user_id, title=title)
    db.add(session)
    await db.flush()
    await db.refresh(session)
    return session


async def get_user_sessions(
    db: AsyncSession,
    user_id: str,
) -> List[ChatSession]:
    """获取用户的所有会话（按更新时间倒序）"""
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.user_id == user_id)
        .order_by(desc(ChatSession.updated_at))
    )
    return list(result.scalars().all())


async def get_session(
    db: AsyncSession,
    session_id: str,
    user_id: str,
) -> ChatSession:
    """获取单个会话，同时验证权限"""
    result = await db.execute(
        select(ChatSession).where(ChatSession.id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在",
        )

    # 验证是否是自己的会话
    if session.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此会话",
        )

    return session


async def rename_session(
    db: AsyncSession,
    session_id: str,
    user_id: str,
    title: str,
) -> ChatSession:
    """重命名会话"""
    session = await get_session(db, session_id, user_id)
    session.title = title
    await db.flush()
    await db.refresh(session)
    return session


async def delete_session(
    db: AsyncSession,
    session_id: str,
    user_id: str,
):
    """删除会话（级联删除所有消息）"""
    session = await get_session(db, session_id, user_id)
    await db.delete(session)
    await db.flush()


async def get_session_messages(
    db: AsyncSession,
    session_id: str,
    user_id: str,
) -> List[Message]:
    """获取会话的所有消息（按时间正序）"""
    # 先验证会话权限
    await get_session(db, session_id, user_id)

    result = await db.execute(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at)
    )
    return list(result.scalars().all())
