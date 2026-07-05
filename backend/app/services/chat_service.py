"""
聊天问答业务逻辑
"""
import json
import traceback
from typing import AsyncIterator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message import Message
from app.models.session import ChatSession
from app.rag.chain import generate_answer
from app.core.deps import async_session_factory


async def get_chat_history(db: AsyncSession, session_id: str, limit: int = 20) -> list:
    """
    获取会话的对话历史
    返回格式：[{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
    """
    result = await db.execute(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at.desc())
        .limit(limit)
    )
    messages = list(result.scalars().all())
    messages.reverse()  # 转为时间正序

    return [
        {"role": msg.role, "content": msg.content}
        for msg in messages
    ]


async def chat_stream(
    session_id: str,
    user_id: str,
    query: str,
) -> AsyncIterator[dict]:
    """
    流式聊天：检索 + LLM生成 + 保存消息

    注意：不使用 FastAPI 依赖注入的 db session，
    因为 StreamingResponse 返回后依赖可能提前关闭 session。
    这里自己管理数据库会话的生命周期。
    """
    # 自己创建数据库会话，不依赖 FastAPI Depends
    async with async_session_factory() as db:
        try:
            # 验证会话权限
            result = await db.execute(
                select(ChatSession).where(ChatSession.id == session_id)
            )
            session = result.scalar_one_or_none()

            if not session:
                yield {"type": "error", "message": "会话不存在"}
                return
            if session.user_id != user_id:
                yield {"type": "error", "message": "无权访问此会话"}
                return

            # 获取聊天历史
            chat_history = await get_chat_history(db, session_id)

            # 保存用户消息
            user_msg = Message(
                session_id=session_id,
                role="user",
                content=query,
            )
            db.add(user_msg)
            await db.flush()

            # 如果会话标题是"新会话"，自动用第一条消息更新标题
            if session.title == "新会话":
                session.title = query[:50] + ("..." if len(query) > 50 else "")

            # RAG生成回答（流式）
            sources_data = []
            full_answer = ""

            async for chunk in generate_answer(query, chat_history):
                if chunk["type"] == "sources":
                    sources_data = chunk["data"]
                    yield {"type": "sources", "data": sources_data}
                elif chunk["type"] == "token":
                    full_answer += chunk["content"]
                    yield {"type": "token", "content": chunk["content"]}
                elif chunk["type"] == "error":
                    yield {"type": "error", "message": chunk["message"]}
                    await db.commit()
                    return
                elif chunk["type"] == "done":
                    full_answer = chunk["content"]

            # 如果full_answer为空
            if not full_answer:
                yield {"type": "error", "message": "模型未返回任何内容，请检查API Key和网络连接"}
                await db.commit()
                return

            # 保存AI回答
            assistant_msg = Message(
                session_id=session_id,
                role="assistant",
                content=full_answer,
                sources=json.dumps(sources_data, ensure_ascii=False),
            )
            db.add(assistant_msg)
            await db.commit()
            await db.refresh(assistant_msg)

            # 发送完成信号
            yield {"type": "done", "message_id": assistant_msg.id, "content": full_answer}

        except Exception as e:
            traceback.print_exc()
            yield {"type": "error", "message": f"服务内部错误：{str(e)}"}


async def save_feedback(
    db: AsyncSession,
    message_id: str,
    feedback: str,
):
    """保存用户对回答的反馈（点赞/点踩）"""
    result = await db.execute(
        select(Message).where(Message.id == message_id)
    )
    message = result.scalar_one_or_none()

    if not message:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="消息不存在")

    if feedback not in ("like", "dislike"):
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="反馈类型只能为 like 或 dislike")

    message.feedback = feedback
    await db.commit()
