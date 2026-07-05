"""
知识库管理相关的请求/响应数据模型
"""
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field, field_validator


def _coerce_datetime(v: Any) -> str:
    if isinstance(v, datetime):
        return v.isoformat()
    return str(v) if v else ""


# ========== 响应模型 ==========

class DocumentResponse(BaseModel):
    """文档列表项响应"""
    id: str
    filename: str
    title: str
    file_type: str
    file_size: int
    chunk_count: int
    status: str
    error_message: str = ""
    created_at: str

    model_config = {"from_attributes": True}

    @field_validator('created_at', mode='before')
    @classmethod
    def coerce_dt(cls, v: Any) -> str:
        return _coerce_datetime(v)


class DocumentListResponse(BaseModel):
    """文档列表响应"""
    documents: list[DocumentResponse]
    total: int


class ChunkResponse(BaseModel):
    """文档分块响应"""
    chunk_id: str
    content: str
    metadata: dict = {}

    model_config = {"from_attributes": True}


class UploadResponse(BaseModel):
    """上传文档响应"""
    id: str
    filename: str
    status: str
    message: str = "文档已上传，正在后台处理中"


class StatsResponse(BaseModel):
    """仪表盘统计数据"""
    total_users: int = 0
    total_documents: int = 0
    total_sessions: int = 0
    total_messages: int = 0
    documents_by_status: dict = {}
