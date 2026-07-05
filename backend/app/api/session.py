"""
会话管理接口
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_user
from app.schemas.chat import (
    RenameSessionRequest,
    SessionResponse, SessionListResponse,
)
from app.services import session_service

router = APIRouter(prefix="/api/sessions", tags=["会话"])


@router.get("", response_model=SessionListResponse)
async def list_sessions(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """获取当前用户的所有会话列表"""
    sessions = await session_service.get_user_sessions(db, current_user.id)
    return SessionListResponse(
        sessions=sessions,
        total=len(sessions),
    )


@router.post("", response_model=SessionResponse)
async def create_session(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """创建新会话"""
    session = await session_service.create_session(db, current_user.id)
    return session


@router.get("/{session_id}/messages")
async def get_messages(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """获取会话的历史消息"""
    import json
    messages = await session_service.get_session_messages(
        db, session_id, current_user.id
    )
    result = []
    for msg in messages:
        sources = None
        if msg.sources and msg.sources != "[]":
            try:
                sources = json.loads(msg.sources)
            except json.JSONDecodeError:
                sources = []

        result.append({
            "id": msg.id,
            "session_id": msg.session_id,
            "role": msg.role,
            "content": msg.content,
            "sources": sources,
            "feedback": msg.feedback,
            "created_at": msg.created_at.isoformat() if msg.created_at else "",
        })
    return result


@router.put("/{session_id}", response_model=SessionResponse)
async def rename_session(
    session_id: str,
    request: RenameSessionRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """重命名会话"""
    session = await session_service.rename_session(
        db, session_id, current_user.id, request.title
    )
    return session


@router.delete("/{session_id}")
async def delete_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """删除会话"""
    await session_service.delete_session(db, session_id, current_user.id)
    return {"message": "会话已删除"}
