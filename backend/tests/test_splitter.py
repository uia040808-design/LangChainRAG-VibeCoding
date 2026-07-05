"""
文本分块模块单元测试
-------------------
测试范围：文本分割器的创建和文档分块功能
"""
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from langchain_core.documents import Document

from app.rag.splitter import (
    get_text_splitter,
    split_documents,
    CHINESE_SEPARATORS,
)


class TestTextSplitter:
    """测试 RecursiveCharacterTextSplitter 的创建"""

    def test_get_splitter_returns_object(self):
        """测试：get_text_splitter 返回有效对象"""
        splitter = get_text_splitter()
        assert splitter is not None, "应返回分割器实例"

    def test_get_splitter_default_chunk_size(self):
        """测试：默认chunk_size=500"""
        splitter = get_text_splitter()
        assert splitter._chunk_size == 500

    def test_get_splitter_default_chunk_overlap(self):
        """测试：默认chunk_overlap=50"""
        splitter = get_text_splitter()
        assert splitter._chunk_overlap == 50

    def test_get_splitter_custom_params(self):
        """测试：自定义chunk_size和chunk_overlap"""
        splitter = get_text_splitter(chunk_size=1000, chunk_overlap=200)
        assert splitter._chunk_size == 1000
        assert splitter._chunk_overlap == 200


class TestSplitDocuments:
    """测试文档分块功能"""

    def test_split_single_short_document(self):
        """测试：短文档不会分块（少于chunk_size）"""
        doc = Document(
            page_content="这是一段很短的文本。只有一句话。",
            metadata={"filename": "test.txt"}
        )
        chunks = split_documents([doc], chunk_size=500, chunk_overlap=50)
        assert len(chunks) == 1, "短文档不应被分割"
        assert chunks[0].page_content == "这是一段很短的文本。只有一句话。"

    def test_split_long_document(self):
        """测试：长文档会被分割成多个块"""
        # 生成一个超过500字的长文本
        long_text = "这是一段测试文本。" * 200  # 约1400字
        doc = Document(
            page_content=long_text,
            metadata={"filename": "long.txt"}
        )
        chunks = split_documents([doc], chunk_size=200, chunk_overlap=20)
        assert len(chunks) > 1, f"长文档应被分割，实际得到{len(chunks)}个块"

    def test_split_preserves_metadata(self):
        """测试：分块后保留原始元数据"""
        doc = Document(
            page_content=("这是测试文本。" * 50),
            metadata={"filename": "test.pdf", "page": 1, "file_type": "pdf"}
        )
        chunks = split_documents([doc], chunk_size=100, chunk_overlap=10)
        for chunk in chunks:
            assert chunk.metadata.get("filename") == "test.pdf"
            assert chunk.metadata.get("page") == 1

    def test_split_adds_chunk_id(self):
        """测试：每个分块都有唯一的chunk_id"""
        doc = Document(
            page_content=("这是测试文本。" * 50),
            metadata={"filename": "test.txt"}
        )
        chunks = split_documents([doc], chunk_size=100, chunk_overlap=10)
        chunk_ids = set()
        for chunk in chunks:
            assert "chunk_id" in chunk.metadata, "每个块应有chunk_id"
            chunk_ids.add(chunk.metadata["chunk_id"])
        assert len(chunk_ids) == len(chunks), "所有chunk_id应唯一"

    def test_split_empty_document_list(self):
        """测试：空文档列表返回空列表"""
        chunks = split_documents([], chunk_size=500, chunk_overlap=50)
        assert chunks == [], "空列表应返回空列表"

    def test_split_empty_content_document(self):
        """测试：空内容文档"""
        doc = Document(
            page_content="",
            metadata={"filename": "empty.txt"}
        )
        chunks = split_documents([doc], chunk_size=500, chunk_overlap=50)
        assert len(chunks) == 0, "空内容文档应返回空列表"

    def test_multiple_documents_split(self):
        """测试：多个文档同时分块"""
        docs = [
            Document(
                page_content=("文档A的内容。" * 30),
                metadata={"filename": "A.txt"}
            ),
            Document(
                page_content=("文档B的内容。" * 30),
                metadata={"filename": "B.txt"}
            ),
        ]
        chunks = split_documents(docs, chunk_size=100, chunk_overlap=10)
        assert len(chunks) > 0
        # 应该有来自两个文档的块
        filenames = set(c.metadata.get("filename") for c in chunks)
        assert "A.txt" in filenames
        assert "B.txt" in filenames


class TestChineseSeparators:
    """测试中文分隔符配置"""

    def test_separators_include_chinese_punctuation(self):
        """测试：分隔符包含中文标点"""
        assert "。" in CHINESE_SEPARATORS, "应包含中文句号"
        assert "！" in CHINESE_SEPARATORS, "应包含中文感叹号"
        assert "？" in CHINESE_SEPARATORS, "应包含中文问号"
        assert "；" in CHINESE_SEPARATORS, "应包含中文分号"
        assert "，" in CHINESE_SEPARATORS, "应包含中文逗号"

    def test_separators_include_paragraph(self):
        """测试：分隔符包含段落分隔"""
        assert "\n\n" in CHINESE_SEPARATORS, "应包含双换行（段落分隔）"
        assert "\n" in CHINESE_SEPARATORS, "应包含单换行"

    def test_separators_empty_string_is_last(self):
        """测试：空字符串是最后一个分隔符（兜底按字符分割）"""
        assert CHINESE_SEPARATORS[-1] == "", "最后一个分隔符应为空字符串"
