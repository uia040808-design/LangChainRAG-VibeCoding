"""
RAG核心链模块单元测试
-------------------
测试范围：提示词构建、消息构建（不涉及LLM/Embedding API调用）
"""
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from app.rag.chain import (
    SYSTEM_PROMPT,
    build_context_prompt,
    build_messages,
)


class TestSystemPrompt:
    """测试系统提示词模板"""

    def test_system_prompt_is_not_empty(self):
        """测试：系统提示词不为空"""
        assert len(SYSTEM_PROMPT) > 50, "系统提示词应该足够长"

    def test_system_prompt_mentions_knowledge_base(self):
        """测试：系统提示词提到知识库相关内容"""
        assert "知识库" in SYSTEM_PROMPT, "提示词应提到知识库"

    def test_system_prompt_mentions_sources(self):
        """测试：系统提示词要求标注来源"""
        assert "来源" in SYSTEM_PROMPT, "提示词应要求标注来源"


class TestBuildContextPrompt:
    """测试知识库上下文提示词构建"""

    def test_empty_docs_returns_placeholder(self):
        """测试：空文档列表返回占位提示"""
        result = build_context_prompt([])
        assert "暂无相关内容" in result, "空文档应有提示信息"

    def test_single_doc_format(self):
        """测试：单个文档的格式化"""
        doc = Document(
            page_content="电池容量：5000mAh，支持65W快充",
            metadata={"filename": "手机参数.pdf", "page": 3}
        )
        result = build_context_prompt([(doc, 0.95)])
        assert "参考片段" in result
        assert "手机参数.pdf" in result
        assert "第3页" in result
        assert "电池容量" in result

    def test_multiple_docs_format(self):
        """测试：多个文档的格式化"""
        docs = [
            (Document(
                page_content="手机支持5G网络",
                metadata={"filename": "手机参数.pdf", "page": 1}
            ), 0.92),
            (Document(
                page_content="电池容量5000mAh",
                metadata={"filename": "电池说明.pdf"}
            ), 0.85),
        ]
        result = build_context_prompt(docs)
        assert "参考片段 1" in result
        assert "参考片段 2" in result
        assert "手机参数.pdf" in result
        assert "电池说明.pdf" in result
        # 第二个文档无页码
        assert "第1页" in result

    def test_similarity_score_format(self):
        """测试：相似度分数格式化显示"""
        doc = Document(
            page_content="测试内容",
            metadata={"filename": "test.txt"}
        )
        result = build_context_prompt([(doc, 0.87)])
        assert "%" in result, "分数应该以百分比显示"

    def test_missing_filename_shows_placeholder(self):
        """测试：缺少文件名时显示占位符"""
        doc = Document(
            page_content="测试内容",
            metadata={}
        )
        result = build_context_prompt([(doc, 0.5)])
        assert "未知文档" in result, "缺少文件名应显示'未知文档'"


class TestBuildMessages:
    """测试消息列表构建"""

    def test_build_messages_returns_list(self):
        """测试：返回列表"""
        doc = Document(
            page_content="测试知识库内容",
            metadata={"filename": "test.txt"}
        )
        messages = build_messages(
            query="测试问题",
            docs_with_scores=[(doc, 0.9)],
            chat_history=[],
        )
        assert isinstance(messages, list), "应返回列表"

    def test_build_messages_starts_with_system(self):
        """测试：消息列表第一项是SystemMessage"""
        doc = Document(
            page_content="测试内容",
            metadata={"filename": "test.txt"}
        )
        messages = build_messages(
            query="测试问题",
            docs_with_scores=[(doc, 0.8)],
            chat_history=[],
        )
        assert isinstance(messages[0], SystemMessage), "第一条应为系统消息"

    def test_build_messages_ends_with_user_query(self):
        """测试：消息列表最后一项是用户问题"""
        doc = Document(
            page_content="测试内容",
            metadata={"filename": "test.txt"}
        )
        messages = build_messages(
            query="这是我的问题",
            docs_with_scores=[(doc, 0.8)],
            chat_history=[],
        )
        last_msg = messages[-1]
        assert isinstance(last_msg, HumanMessage)
        assert last_msg.content == "这是我的问题"

    def test_build_messages_includes_knowledge_in_system(self):
        """测试：系统消息中包含了知识库内容"""
        doc = Document(
            page_content="特殊标记的知识库内容_ABC123",
            metadata={"filename": "special.txt"}
        )
        messages = build_messages(
            query="问题",
            docs_with_scores=[(doc, 0.99)],
            chat_history=[],
        )
        system_content = messages[0].content
        assert "特殊标记的知识库内容_ABC123" in system_content

    def test_build_messages_includes_chat_history(self):
        """测试：包含对话历史"""
        doc = Document(
            page_content="知识内容",
            metadata={"filename": "test.txt"}
        )
        history = [
            {"role": "user", "content": "你好"},
            {"role": "assistant", "content": "你好！有什么可以帮你的？"},
            {"role": "user", "content": "介绍下手机"},
            {"role": "assistant", "content": "这款手机支持5G..."},
        ]
        messages = build_messages(
            query="它的电池呢？",
            docs_with_scores=[(doc, 0.8)],
            chat_history=history,
        )
        # 应该有：SystemMessage + 4条历史 + 当前问题
        assert len(messages) == 6, f"应该有6条消息(system+4历史+1当前)"

    def test_build_messages_empty_knowledge(self):
        """测试：知识库为空时也能正常工作"""
        messages = build_messages(
            query="问题",
            docs_with_scores=[],
            chat_history=[],
        )
        assert len(messages) >= 2  # system + user
        assert "暂无相关内容" in messages[0].content

    def test_build_messages_history_truncated(self):
        """测试：长对话历史被截断（只保留最近10条）"""
        doc = Document(
            page_content="知识",
            metadata={"filename": "t.txt"}
        )
        # 创建20条历史消息（超过10条限制）
        history = []
        for i in range(20):
            history.append({"role": "user", "content": f"问题{i}"})
            history.append({"role": "assistant", "content": f"回答{i}"})

        messages = build_messages(
            query="最新问题",
            docs_with_scores=[(doc, 0.8)],
            chat_history=history,
        )
        # 只保留最后10条 = 5轮对话
        # system(1) + 历史(10) + 当前(1) = 12
        assert len(messages) == 12, f"应有12条消息, 实际有{len(messages)}"
