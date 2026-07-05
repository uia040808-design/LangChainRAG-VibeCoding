"""
问答接口：发送消息、获取回答（SSE流式输出）、反馈
"""
import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_user
from app.schemas.chat import ChatRequest, FeedbackRequest, MessageResponse, SourceInfo
from app.schemas.auth import UserResponse
from app.services import chat_service

router = APIRouter(prefix="/api", tags=["问答"])


@router.post("/chat/{session_id}")
async def chat(
    session_id: str,
    request: ChatRequest,
    current_user=Depends(get_current_user),
):
    """
    发送消息并获取AI回答（SSE流式输出）

    SSE (Server-Sent Events) 是服务端推送技术，
    前端通过 EventSource 或 fetch 读取流式数据。

    返回的SSE事件类型：
    - sources: 引用来源列表（JSON）
    - token: 逐字的回答内容
    - done: 回答完成，包含完整答案和消息ID
    """

    async def event_generator():
        """SSE事件生成器"""
        try:
            async for chunk in chat_service.chat_stream(
                session_id=session_id,
                user_id=current_user.id,
                query=request.message,
            ):
                if chunk["type"] == "sources":
                    # 发送引用来源
                    yield f"event: sources\ndata: {json.dumps(chunk['data'], ensure_ascii=False)}\n\n"
                elif chunk["type"] == "token":
                    # 发送文字片段
                    yield f"event: token\ndata: {json.dumps({'content': chunk['content']}, ensure_ascii=False)}\n\n"
                elif chunk["type"] == "error":
                    # 发送错误信息
                    yield f"event: error\ndata: {json.dumps({'message': chunk['message']}, ensure_ascii=False)}\n\n"
                elif chunk["type"] == "done":
                    # 发送完成信号
                    yield f"event: done\ndata: {json.dumps({'message_id': chunk.get('message_id', ''), 'content': chunk['content']}, ensure_ascii=False)}\n\n"
        except Exception as e:
            # 兜底：即使 chat_stream 内部崩溃，也要发一个 error 事件给前端
            import traceback
            traceback.print_exc()
            yield f"event: error\ndata: {json.dumps({'message': f'服务内部错误：{str(e)}'}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # 禁用Nginx缓冲
        },
    )


@router.post("/messages/{message_id}/feedback")
async def feedback_message(
    message_id: str,
    request: FeedbackRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    对AI回答进行反馈（点赞/点踩）
    """
    await chat_service.save_feedback(
        db=db,
        message_id=message_id,
        feedback=request.feedback,
    )
    return {"message": "反馈已提交"}
