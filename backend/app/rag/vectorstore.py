"""
向量数据库模块 - ChromaDB 操作封装
----------------------------------
ChromaDB 是一个轻量级向量数据库，专门存储和搜索"向量"（文本的数值表示）。

工作原理：
  1. 将文档文本 → Embedding模型 → 向量（如1536个浮点数）
  2. 向量 + 原始文本 + 元数据 → 存入ChromaDB
  3. 查询时：用户问题 → Embedding → 向量 → 在ChromaDB中找最相似的K个向量

ChromaDB数据存储在本地 chroma_data/ 目录中，随项目一起。
"""
import os
from typing import List, Optional
from langchain_chroma import Chroma
from langchain_core.documents import Document
from app.core.config import settings
from app.rag.embeddings import get_embeddings_cached


# ChromaDB集合名称（相当于关系数据库中的"表"）
COLLECTION_NAME = "knowledge_base"


def get_vectorstore() -> Chroma:
    """
    获取ChromaDB向量存储实例
    返回：配置好的Chroma实例，连接到本地持久化存储

    注：使用 cosine（余弦相似度）作为距离函数，
        比默认的 l2（欧几里得距离）更适合文本语义搜索。
        余弦相似度关注方向而非绝对距离，对文本向量更有效。
    """
    embeddings = get_embeddings_cached()
    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=str(settings.chroma_dir),
        collection_metadata={"hnsw:space": "cosine"},  # 使用余弦相似度
    )


def add_documents_to_store(
    documents: List[Document],
) -> int:
    """
    将文档块添加到向量数据库
    参数：documents - 分割后的文档块列表
    返回：添加的文档块数量
    """
    vectorstore = get_vectorstore()
    # LangChain会自动调用Embedding模型将文档转为向量再存储
    ids = vectorstore.add_documents(documents)
    return len(ids)


def delete_documents_by_filter(metadata_filter: dict) -> int:
    """
    根据元数据过滤条件删除文档
    参数：metadata_filter - 过滤条件，如 {"filename": "手机参数.pdf"}
    返回：已删除的文档数量（如果支持），否则为0

    注：ChromaDB 的 get/delete 需要精确匹配 metadata
    """
    vectorstore = get_vectorstore()
    try:
        # 先获取匹配的文档ID
        results = vectorstore.get(where=metadata_filter)
        if results and results.get("ids"):
            ids_to_delete = results["ids"]
            vectorstore.delete(ids=ids_to_delete)
            return len(ids_to_delete)
    except Exception:
        pass
    return 0


def get_collection_stats() -> dict:
    """
    获取向量数据库统计信息
    返回：包含文档总数等信息的字典
    """
    try:
        vectorstore = get_vectorstore()
        collection = vectorstore._collection
        count = collection.count()
        return {"total_chunks": count}
    except Exception:
        return {"total_chunks": 0}
