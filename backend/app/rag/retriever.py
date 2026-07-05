"""
检索器模块
----------
从向量数据库中检索与用户问题最相关的知识库片段。

使用两种检索策略：
1. 相似度检索：找到向量空间中距离最近的文档
2. MMR（最大边际相关性）：在相似度的基础上，增加结果多样性
   - 比如检索5条结果，如果前3条都是"电池容量"相关，
     MMR会尝试找一些其他相关但不同的内容，提高信息覆盖度
"""
from typing import List, Tuple
from langchain_core.documents import Document
from app.rag.vectorstore import get_vectorstore


def similarity_search(
    query: str,
    k: int = 5,
    score_threshold: float = -1.0,
) -> List[Tuple[Document, float]]:
    """
    相似度检索（带分数过滤）
    参数：
        query: 用户问题
        k: 返回的最相关文档数
        score_threshold: 相似度阈值，低于此值的结果被丢弃
                         -1.0 表示不过滤（保留所有结果），因为 ChromaDB
                         默认距离函数（l2）返回的距离值范围不在 [0,1]，
                         使用正值阈值会错误过滤掉相关结果
    返回：(文档, 相似度分数) 的列表，按相似度降序排列
    """
    vectorstore = get_vectorstore()
    # 多召回一些候选，供后续筛选
    results = vectorstore.similarity_search_with_relevance_scores(
        query, k=k * 3
    )

    # 按分数降序排列
    results.sort(key=lambda x: x[1], reverse=True)

    # 仅当阈值 > -1 时才过滤（默认不过滤）
    if score_threshold > -1:
        results = [
            (doc, score) for doc, score in results
            if score >= score_threshold
        ]

    return results[:k]


def mmr_search(
    query: str,
    k: int = 5,
    fetch_k: int = 10,
    lambda_mult: float = 0.7,
) -> List[Document]:
    """
    MMR（最大边际相关性）检索
    参数：
        query: 用户问题
        k: 最终返回的文档数
        fetch_k: 先获取这么多候选，然后用MMR从中选k个
        lambda_mult: 平衡参数（0~1）
            - 1 = 纯相似度排序
            - 0 = 纯多样性排序
            - 0.7 = 偏向相似度但保留一定多样性（推荐值）
    返回：经过MMR优化的文档列表
    """
    vectorstore = get_vectorstore()
    results = vectorstore.max_marginal_relevance_search(
        query,
        k=k,
        fetch_k=fetch_k,
        lambda_mult=lambda_mult,
    )
    return results


def retrieve_context(query: str, k: int = 5) -> List[Tuple[Document, float]]:
    """
    综合检索：相似度搜索 + MMR多样性补充
    这是暴露给外部的统一检索接口

    策略：
    1. 先用相似度搜索获取 top-k 结果
    2. 如果相似度搜索结果不足 k 个，用 MMR 补充（MMR不需要分数阈值）
    3. 合并去重后返回

    参数：
        query: 用户问题
        k: 检索数量
    返回：(文档, 分数) 列表
    """
    # 使用相似度检索获取初始结果
    results = similarity_search(query, k=k)

    # 如果结果不够k个，用MMR补充
    if len(results) < k:
        mmr_results = mmr_search(query, k=k - len(results))
        # 获取已有文档的ID用于去重
        existing_ids = {doc.metadata.get("chunk_id", "") for doc, _ in results}
        for doc in mmr_results:
            chunk_id = doc.metadata.get("chunk_id", "")
            if chunk_id not in existing_ids:
                results.append((doc, 0.0))  # MMR结果没有分数，给个默认值
                existing_ids.add(chunk_id)

    return results
