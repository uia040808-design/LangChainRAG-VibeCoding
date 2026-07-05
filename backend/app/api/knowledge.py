"""
知识库管理接口（仅管理员可访问）
"""
import asyncio
from fastapi import APIRouter, Depends, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_admin_user
from app.schemas.knowledge import (
    DocumentResponse, DocumentListResponse,
    UploadResponse, ChunkResponse, StatsResponse,
)
from app.services import knowledge_service

router = APIRouter(prefix="/api/knowledge", tags=["知识库管理"])


@router.get("/documents", response_model=DocumentListResponse)
async def list_documents(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin_user),
):
    """获取文档列表（分页）"""
    documents, total = await knowledge_service.get_documents(db, page, page_size)
    return DocumentListResponse(
        documents=documents,
        total=total,
    )


@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin_user),
):
    """
    上传知识库文档
    文件上传后立即返回"处理中"状态，
    后台异步进行文档解析和向量化处理。
    """
    doc = await knowledge_service.upload_document(db, file, admin.id)

    # 使用 asyncio.create_task 启动后台异步任务
    # 比 BackgroundTasks 更可靠：直接在事件循环中调度，不依赖中间件
    asyncio.create_task(knowledge_service.process_document_async(doc.id))

    return UploadResponse(
        id=doc.id,
        filename=doc.filename,
        status="processing",
        message="文档已上传，正在后台处理中",
    )


@router.get("/documents/{doc_id}", response_model=DocumentResponse)
async def get_document(
    doc_id: str,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin_user),
):
    """获取文档详情"""
    doc = await knowledge_service.get_document(db, doc_id)
    return doc


@router.delete("/documents/{doc_id}")
async def delete_document(
    doc_id: str,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin_user),
):
    """删除文档（同时删除向量数据和物理文件）"""
    await knowledge_service.delete_document(db, doc_id)
    return {"message": "文档已删除"}


@router.get("/documents/{doc_id}/chunks")
async def get_document_chunks(
    doc_id: str,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin_user),
):
    """查看文档的分块列表"""
    # 先确认文档存在
    await knowledge_service.get_document(db, doc_id)
    chunks = await knowledge_service.get_document_chunks(doc_id)
    return {"chunks": chunks, "total": len(chunks)}


@router.get("/stats", response_model=StatsResponse)
async def get_stats(
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin_user),
):
    """获取系统统计数据（管理员仪表盘）"""
    stats = await knowledge_service.get_stats(db)
    return stats
