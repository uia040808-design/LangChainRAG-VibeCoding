"""
问答/会话相关的请求/响应数据模型
"""
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field, field_validator


# Validator helper
def _coerce_datetime(v: Any) -> str:
    if isinstance(v, datetime):
        return v.isoformat()
    return str(v) if v else ""


# ========== 请求模型 ==========

class ChatRequest(BaseModel):
    """发送消息请求"""
    message: str = Field(..., min_length=1, description="用户消息内容")


class FeedbackRequest(BaseModel):
    """消息反馈请求"""
    feedback: str = Field(..., description="like / dislike")


class RenameSessionRequest(BaseModel):
    """重命名会话请求"""
    title: str = Field(..., min_length=1, max_length=200, description="新标题")


# ========== 响应模型 ==========

class SourceInfo(BaseModel):
    """知识库引用来源信息"""
    document_title: str = Field(..., description="文档标题")
    chunk_id: str = Field(default="", description="文本块ID")
    content: str = Field(..., description="引用的文本片段内容")
    similarity_score: float = Field(default=0.0, description="相似度分数")


class MessageResponse(BaseModel):
    """消息响应"""
    id: str
    session_id: str
    role: str
    content: str
    sources: Optional[list[SourceInfo]] = Field(default=None, description="引用来源列表")
    feedback: Optional[str] = None
    created_at: str

    model_config = {"from_attributes": True}

    @field_validator('created_at', mode='before')
    @classmethod
    def coerce_dt(cls, v: Any) -> str:
        return _coerce_datetime(v)


class SessionResponse(BaseModel):
    """会话响应"""
    id: str
    title: str
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}

    @field_validator('created_at', 'updated_at', mode='before')
    @classmethod
    def coerce_dt(cls, v: Any) -> str:
        return _coerce_datetime(v)


class SessionListResponse(BaseModel):
    """会话列表响应"""
    sessions: list[SessionResponse]
    total: int
