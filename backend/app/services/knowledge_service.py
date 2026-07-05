"""
知识库管理业务逻辑
"""
import os
import uuid
from typing import List
from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status, UploadFile

from app.core.config import settings
from app.models.document import KnowledgeDocument
from app.rag.loader import load_document
from app.rag.splitter import split_documents
from app.rag.vectorstore import add_documents_to_store, delete_documents_by_filter


async def upload_document(
    db: AsyncSession,
    file: UploadFile,
    user_id: str,
) -> KnowledgeDocument:
    """
    上传文档：保存文件 → 创建数据库记录 → 返回记录
    实际处理（解析+向量化）由后台任务完成
    """
    # 验证文件类型
    filename = file.filename or "unknown"
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in settings.allowed_file_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的文件类型 .{ext}，支持的类型：{', '.join(settings.allowed_file_types)}",
        )

    # 保存文件
    file_id = str(uuid.uuid4())
    saved_name = f"{file_id}.{ext}"
    file_path = settings.upload_dir / saved_name

    content = await file.read()
    if len(content) > settings.max_upload_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"文件过大，最大支持 {settings.max_upload_size // 1024 // 1024}MB",
        )

    with open(file_path, "wb") as f:
        f.write(content)

    # 创建数据库记录
    doc = KnowledgeDocument(
        filename=filename,
        title=filename.rsplit(".", 1)[0],  # 默认标题=文件名去后缀
        file_type=ext,
        file_size=len(content),
        file_path=str(file_path),
        status="processing",  # 初始状态：处理中
        created_by=user_id,
    )
    db.add(doc)
    await db.flush()
    await db.refresh(doc)

    return doc


async def process_document_async(doc_id: str):
    """
    异步处理文档：加载 → 分块 → 向量化 → 更新状态

    设计要点：
    - 文档加载、分块、向量化都是同步阻塞操作（文件IO、HTTP请求），
      通过 asyncio.to_thread() 放到线程池执行，不阻塞事件循环
    - 数据库操作使用异步 SQLAlchemy，直接在事件循环中执行
    - 通过 asyncio.create_task() 在后台运行，不等待结果

    使用方式（在 FastAPI 接口中）：
        import asyncio
        asyncio.create_task(process_document_async(doc_id))
    """
    import asyncio
    from app.core.deps import async_session_factory

    async with async_session_factory() as db:
        result = await db.execute(
            select(KnowledgeDocument).where(KnowledgeDocument.id == doc_id)
        )
        doc = result.scalar_one_or_none()

        if not doc:
            print(f"[文档处理] 错误：文档不存在 {doc_id}")
            return

        print(f"[文档处理] 开始处理: {doc.filename} ({doc_id})")

        try:
            # 1. 加载文档（同步文件IO → 线程池）
            documents = await asyncio.to_thread(load_document, doc.file_path)

            if not documents:
                raise ValueError("文档无法解析或内容为空")

            # 2. 分块（同步内存操作 → 线程池）
            chunks = await asyncio.to_thread(split_documents, documents)
            print(f"[文档处理] {doc.filename} 分块完成: {len(chunks)} 块")

            # 3. 为每个chunk添加文档级别的元数据
            for chunk in chunks:
                chunk.metadata["doc_id"] = doc.id
                chunk.metadata["filename"] = doc.filename

            # 4. 存入向量数据库（同步HTTP Embedding API调用 → 线程池）
            chunk_count = await asyncio.to_thread(add_documents_to_store, chunks)
            print(f"[文档处理] {doc.filename} 向量化完成: {chunk_count} 条")

            # 5. 更新数据库记录
            doc.chunk_count = chunk_count
            doc.status = "ready"
            doc.error_message = ""
            print(f"[文档处理] {doc.filename} 处理完成 ✓")

        except Exception as e:
            print(f"[文档处理] {doc.filename} 处理失败: {e}")
            doc.status = "error"
            doc.error_message = str(e)

        await db.commit()


def process_document(doc_id: str):
    """
    同步包装器，供手动测试或外部脚本调用。
    通过 asyncio.run() 在独立事件循环中运行异步处理。

    注意：在 FastAPI 请求处理中不应调用此函数，
    应使用 asyncio.create_task(process_document_async(doc_id))。
    """
    import asyncio
    print(f"[文档处理] 通过同步包装器处理: {doc_id}")
    asyncio.run(process_document_async(doc_id))


async def get_documents(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
) -> tuple[List[KnowledgeDocument], int]:
    """获取文档列表（分页）"""
    # 查询总数
    count_result = await db.execute(
        select(func.count()).select_from(KnowledgeDocument)
    )
    total = count_result.scalar() or 0

    # 分页查询
    result = await db.execute(
        select(KnowledgeDocument)
        .order_by(desc(KnowledgeDocument.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    documents = list(result.scalars().all())

    return documents, total


async def get_document(
    db: AsyncSession,
    doc_id: str,
) -> KnowledgeDocument:
    """获取单个文档详情"""
    result = await db.execute(
        select(KnowledgeDocument).where(KnowledgeDocument.id == doc_id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    return doc


async def delete_document(
    db: AsyncSession,
    doc_id: str,
):
    """删除文档（同时删除文件和向量数据）"""
    doc = await get_document(db, doc_id)

    # 1. 删除向量数据
    delete_documents_by_filter({"doc_id": doc.id})

    # 2. 删除物理文件
    if doc.file_path and os.path.exists(doc.file_path):
        os.remove(doc.file_path)

    # 3. 删除数据库记录
    await db.delete(doc)
    await db.commit()


async def get_document_chunks(doc_id: str) -> list:
    """获取文档的分块列表（从ChromaDB查询）"""
    from app.rag.vectorstore import get_vectorstore
    vectorstore = get_vectorstore()
    try:
        results = vectorstore.get(where={"doc_id": doc_id})
        chunks = []
        if results and results.get("documents"):
            for i, content in enumerate(results["documents"]):
                chunks.append({
                    "chunk_id": results.get("ids", [f"chunk_{i}"])[i] if results.get("ids") else f"chunk_{i}",
                    "content": content,
                    "metadata": results.get("metadatas", [{}])[i] if results.get("metadatas") else {},
                })
        return chunks
    except Exception:
        return []


async def get_stats(db: AsyncSession) -> dict:
    """获取系统统计数据（管理员仪表盘）"""
    from app.models.user import User
    from app.models.session import ChatSession
    from app.models.message import Message

    total_users = (await db.execute(select(func.count()).select_from(User))).scalar() or 0
    total_docs = (await db.execute(select(func.count()).select_from(KnowledgeDocument))).scalar() or 0
    total_sessions = (await db.execute(select(func.count()).select_from(ChatSession))).scalar() or 0
    total_messages = (await db.execute(select(func.count()).select_from(Message))).scalar() or 0

    # 按状态统计文档
    ready_count = (await db.execute(
        select(func.count()).select_from(KnowledgeDocument).where(KnowledgeDocument.status == "ready")
    )).scalar() or 0
    processing_count = (await db.execute(
        select(func.count()).select_from(KnowledgeDocument).where(KnowledgeDocument.status == "processing")
    )).scalar() or 0
    error_count = (await db.execute(
        select(func.count()).select_from(KnowledgeDocument).where(KnowledgeDocument.status == "error")
    )).scalar() or 0

    return {
        "total_users": total_users,
        "total_documents": total_docs,
        "total_sessions": total_sessions,
        "total_messages": total_messages,
        "documents_by_status": {
            "ready": ready_count,
            "processing": processing_count,
            "error": error_count,
        },
    }
