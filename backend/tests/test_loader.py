"""
文档加载器模块单元测试
--------------------
测试范围：各类型文档的加载、不支持类型异常
使用临时文件进行测试，不影响真实数据
"""
import sys
import os
import pytest
import tempfile
import shutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.rag.loader import load_document, load_txt, load_markdown


class TestLoadDocumentDispatch:
    """测试 load_document 根据文件类型分发"""

    def test_load_txt_file(self):
        """测试：加载.txt文件"""
        with tempfile.NamedTemporaryFile(suffix=".txt", mode="w", encoding="utf-8", delete=False) as f:
            f.write("这是一段测试文本内容。\n第二行内容。")
            tmp_path = f.name

        try:
            docs = load_document(tmp_path)
            assert len(docs) > 0, "应该返回至少一个Document"
            assert "测试文本内容" in docs[0].page_content
            assert docs[0].metadata["file_type"] == "txt"
            assert docs[0].metadata["filename"] == os.path.basename(tmp_path)
        finally:
            os.unlink(tmp_path)

    def test_load_md_file(self):
        """测试：加载.md文件（使用TextLoader）"""
        with tempfile.NamedTemporaryFile(suffix=".md", mode="w", encoding="utf-8", delete=False) as f:
            f.write("# 标题\n\n这是Markdown内容。\n\n## 二级标题\n\n更多内容。")
            tmp_path = f.name

        try:
            docs = load_document(tmp_path)
            assert len(docs) > 0, "应该返回至少一个Document"
            assert docs[0].metadata["file_type"] == "md"
            assert "Markdown内容" in docs[0].page_content
        finally:
            os.unlink(tmp_path)

    def test_unsupported_file_type(self):
        """测试：不支持的文件类型抛出异常"""
        with tempfile.NamedTemporaryFile(suffix=".xyz", mode="w", encoding="utf-8", delete=False) as f:
            f.write("test")
            tmp_path = f.name

        try:
            with pytest.raises(ValueError, match="不支持的文件类型"):
                load_document(tmp_path)
        finally:
            os.unlink(tmp_path)

    def test_file_type_case_insensitive(self):
        """测试：文件后缀名大小写不敏感"""
        with tempfile.NamedTemporaryFile(suffix=".TXT", mode="w", encoding="utf-8", delete=False) as f:
            f.write("测试内容")
            tmp_path = f.name

        try:
            docs = load_document(tmp_path)
            assert len(docs) > 0
            assert docs[0].metadata["file_type"] == "txt"
        finally:
            os.unlink(tmp_path)


class TestLoadTxt:
    """测试纯文本文件加载"""

    def test_basic_text_loading(self):
        """测试：基本文本加载"""
        with tempfile.NamedTemporaryFile(suffix=".txt", mode="w", encoding="utf-8", delete=False) as f:
            f.write("Hello World\n你好世界")
            tmp_path = f.name

        try:
            docs = load_txt(tmp_path)
            assert len(docs) >= 1
            content = docs[0].page_content
            assert "Hello World" in content or "你好世界" in content
        finally:
            os.unlink(tmp_path)

    def test_metadata_added(self):
        """测试：加载后添加了元数据"""
        with tempfile.NamedTemporaryFile(suffix=".txt", mode="w", encoding="utf-8", delete=False) as f:
            f.write("测试")
            tmp_path = f.name

        try:
            docs = load_txt(tmp_path)
            for doc in docs:
                assert "filename" in doc.metadata
                assert "file_type" in doc.metadata
                assert doc.metadata["file_type"] == "txt"
        finally:
            os.unlink(tmp_path)

    def test_empty_txt_file(self):
        """测试：空文本文件"""
        with tempfile.NamedTemporaryFile(suffix=".txt", mode="w", encoding="utf-8", delete=False) as f:
            f.write("")
            tmp_path = f.name

        try:
            docs = load_txt(tmp_path)
            # 空文件可能返回空列表或含空内容的列表
            assert isinstance(docs, list)
        finally:
            os.unlink(tmp_path)


class TestLoadMarkdown:
    """测试Markdown文件加载（使用TextLoader）"""

    def test_markdown_basic(self):
        """测试：基本Markdown加载"""
        with tempfile.NamedTemporaryFile(suffix=".md", mode="w", encoding="utf-8", delete=False) as f:
            f.write("# 产品介绍\n\n这是产品详情。\n\n## 规格参数\n\n- 电池: 5000mAh\n- 屏幕: 6.7英寸")
            tmp_path = f.name

        try:
            docs = load_markdown(tmp_path)
            assert len(docs) >= 1
            content = docs[0].page_content
            assert "产品介绍" in content
            assert "5000mAh" in content
        finally:
            os.unlink(tmp_path)

    def test_markdown_metadata(self):
        """测试：Markdown文档的元数据"""
        with tempfile.NamedTemporaryFile(suffix=".md", mode="w", encoding="utf-8", delete=False) as f:
            f.write("# 测试")
            tmp_path = f.name

        try:
            docs = load_markdown(tmp_path)
            for doc in docs:
                assert doc.metadata["file_type"] == "md"
                assert "filename" in doc.metadata
        finally:
            os.unlink(tmp_path)
