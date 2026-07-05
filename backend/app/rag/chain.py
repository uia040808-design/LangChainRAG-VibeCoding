"""
RAG 核心链模块
--------------
这是整个RAG系统的大脑，负责编排整个问答流程：
  检索 → 构建提示词 → 调用LLM → 返回结果

提示词模板说明：
  system_prompt：设定AI的角色和行为规则
  知识库内容：检索到的相关文档片段
  对话历史：当前会话中的历史消息（用于多轮对话理解上下文）
  用户问题：当前用户的问题
"""
import json
from typing import AsyncIterator, List, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.documents import Document

from app.core.config import settings
from app.rag.retriever import retrieve_context


# ========== 提示词模板 ==========

SYSTEM_PROMPT = """你是一个专业的电商客服助手，专门回答关于商品的问题。
请根据下面提供的"知识库参考内容"来回答用户的问题。

回答规则：
1. 优先基于"知识库参考内容"中的信息回答问题，确保回答准确
2. 如果知识库中有相关信息，请引用具体内容，并标注 [来源: 文档名]
3. 如果知识库中没有相关信息，请诚实地说"抱歉，知识库中暂时没有关于这个问题的相关信息"
4. 回答要简洁清晰，使用中文，友好专业
5. 如果用户的问题不明确，可以追问澄清
6. 不要编造知识库中没有的商品信息"""


def build_context_prompt(docs_with_scores: List[tuple]) -> str:
    """
    构建知识库上下文提示词
    将检索到的文档片段格式化为LLM可理解的格式
    """
    if not docs_with_scores:
        return "（知识库中暂无相关内容）"

    parts = []
    for i, (doc, score) in enumerate(docs_with_scores, 1):
        filename = doc.metadata.get("filename", "未知文档")
        page = doc.metadata.get("page", "")
        page_info = f"，第{page}页" if page else ""

        parts.append(
            f"【参考片段 {i}】（来源：{filename}{page_info}，相关度：{score:.0%}）\n"
            f"{doc.page_content}"
        )

    return "\n\n".join(parts)


def build_messages(
    query: str,
    docs_with_scores: List[tuple],
    chat_history: List[Dict[str, str]],
) -> list:
    """
    构建发送给LLM的完整消息列表
    参数：
        query: 用户当前问题
        docs_with_scores: 检索到的(文档, 分数)列表
        chat_history: 历史对话 [{"role": "user/assistant", "content": "..."}]
    返回：消息列表，可直接传给LLM
    """
    # 构建知识库上下文
    context = build_context_prompt(docs_with_scores)

    # 完整的系统提示词 = 角色设定 + 知识库内容
    full_system_prompt = (
        SYSTEM_PROMPT +
        "\n\n--- 以下是知识库参考内容 ---\n" +
        context +
        "\n--- 知识库参考内容结束 ---\n\n"
        "请根据以上知识库内容回答用户的问题。"
    )

    messages = [SystemMessage(content=full_system_prompt)]

    # 添加历史对话（最近5轮，避免上下文过长）
    recent_history = chat_history[-10:]  # 5轮对话 = 10条消息
    for msg in recent_history:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            messages.append(AIMessage(content=msg["content"]))

    # 添加当前问题
    messages.append(HumanMessage(content=query))

    return messages


def get_llm(streaming: bool = True) -> ChatOpenAI:
    """
    获取LLM实例（通义千问）
    参数：streaming - 是否启用流式输出
    """
    return ChatOpenAI(
        model="qwen-plus",  # 推荐：性价比最高；也可用 qwen-turbo / qwen-max
        openai_api_base=settings.dashscope_base_url,
        openai_api_key=settings.dashscope_api_key,
        temperature=0.3,  # 温度较低，回答更确定、更准确（适合知识库问答）
        streaming=streaming,
        max_tokens=2000,
        request_timeout=60,  # 请求超时60秒，避免前端无限等待
    )


async def generate_answer(
    query: str,
    chat_history: List[Dict[str, str]],
) -> AsyncIterator[Dict[str, Any]]:
    """
    生成RAG回答（流式输出）
    这是对外暴露的核心方法，业务层直接调用这个函数

    参数：
        query: 用户问题
        chat_history: 历史对话列表
    Yields：
        字典 {"type": "token", "content": "..."} - 流式文字
        字典 {"type": "sources", "data": [...]} - 引用来源（在文字前发送）
        字典 {"type": "error", "message": "..."} - 错误信息
        字典 {"type": "done", "content": "完整回答"} - 完成标记
    """
    try:
        # 步骤1：检索相关知识库内容
        docs_with_scores = retrieve_context(query, k=5)

        # 步骤2：提取引用来源信息（先发送给前端）
        sources = []
        for doc, score in docs_with_scores:
            sources.append({
                "document_title": doc.metadata.get("filename", "未知文档"),
                "chunk_id": doc.metadata.get("chunk_id", ""),
                "content": doc.page_content[:200],  # 预览前200字
                "similarity_score": round(score, 4),
            })
        yield {"type": "sources", "data": sources}

        # 步骤3：构建消息
        messages = build_messages(query, docs_with_scores, chat_history)

        # 步骤4：调用LLM流式生成
        llm = get_llm(streaming=True)
        full_answer = ""

        async for chunk in llm.astream(messages):
            if chunk.content:
                full_answer += chunk.content
                yield {"type": "token", "content": chunk.content}

        # 步骤5：发送完成标记
        yield {"type": "done", "content": full_answer}

    except Exception as e:
        # 捕获所有异常，通过SSE发送给前端，避免前端永远卡在"回答中"
        error_msg = str(e)
        # 识别常见错误，给出更友好的提示
        if "401" in error_msg or "Unauthorized" in error_msg or "invalid" in error_msg.lower():
            error_msg = "API Key 无效或已过期，请检查 .env 文件中的 DASHSCOPE_API_KEY"
        elif "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
            error_msg = "连接阿里云百炼超时，请检查网络连接"
        elif "connection" in error_msg.lower() or "connect" in error_msg.lower():
            error_msg = "无法连接到阿里云百炼服务，请检查网络"
        yield {"type": "error", "message": f"回答生成失败：{error_msg}"}


async def generate_answer_simple(query: str) -> str:
    """
    简单问答（非流式，用于测试或内部调用）
    参数：query - 用户问题
    返回：完整回答字符串
    """
    docs_with_scores = retrieve_context(query, k=5)
    messages = build_messages(query, docs_with_scores, [])
    llm = get_llm(streaming=False)
    response = await llm.ainvoke(messages)
    return response.content
