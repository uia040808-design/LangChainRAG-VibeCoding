"""
文档加载器模块
--------------
支持多种文档格式的加载：PDF、TXT、CSV、DOCX、Markdown。
每种格式使用对应的 LangChain 加载器，统一返回 Document 对象列表。

Document 对象是 LangChain 中的标准数据单元，包含：
  - page_content: 文档的文本内容
  - metadata: 文档的元数据（文件名、页码等）
"""
import os
from pathlib import Path
from typing import List
from langchain_core.documents import Document


def load_document(file_path: str) -> List[Document]:
    """
    根据文件类型加载文档
    参数：file_path - 文件的绝对路径
    返回：Document 对象列表
    """
    file_path = Path(file_path)
    suffix = file_path.suffix.lower()

    if suffix == ".pdf":
        return load_pdf(str(file_path))
    elif suffix == ".txt":
        return load_txt(str(file_path))
    elif suffix == ".csv":
        return load_csv(str(file_path))
    elif suffix == ".docx":
        return load_docx(str(file_path))
    elif suffix == ".md":
        return load_markdown(str(file_path))
    else:
        raise ValueError(f"不支持的文件类型: {suffix}")


def load_pdf(file_path: str) -> List[Document]:
    """
    加载PDF文档
    解释：pypdf 是纯Python的PDF解析库，不需要安装额外软件
    """
    from langchain_community.document_loaders import PyPDFLoader
    loader = PyPDFLoader(file_path)
    documents = loader.load()
    # 为每个页面的Document添加文件名元数据
    filename = os.path.basename(file_path)
    for doc in documents:
        doc.metadata["filename"] = filename
        doc.metadata["file_type"] = "pdf"
    return documents


def load_txt(file_path: str) -> List[Document]:
    """
    加载TXT文档
    解释：TextLoader 按行读取文本文件
    """
    from langchain_community.document_loaders import TextLoader
    filename = os.path.basename(file_path)
    loader = TextLoader(file_path, encoding="utf-8")
    documents = loader.load()
    for doc in documents:
        doc.metadata["filename"] = filename
        doc.metadata["file_type"] = "txt"
    return documents


def load_csv(file_path: str) -> List[Document]:
    """
    加载CSV文档
    解释：CSVLoader 将CSV的每一行转为一条记录
    """
    from langchain_community.document_loaders import CSVLoader
    filename = os.path.basename(file_path)
    loader = CSVLoader(file_path, encoding="utf-8")
    documents = loader.load()
    for doc in documents:
        doc.metadata["filename"] = filename
        doc.metadata["file_type"] = "csv"
    return documents


def load_docx(file_path: str) -> List[Document]:
    """
    加载Word文档 (.docx)
    解释：Docx2txtLoader 提取Word中的纯文本内容
    """
    from langchain_community.document_loaders import Docx2txtLoader
    filename = os.path.basename(file_path)
    loader = Docx2txtLoader(file_path)
    documents = loader.load()
    for doc in documents:
        doc.metadata["filename"] = filename
        doc.metadata["file_type"] = "docx"
    return documents


def load_markdown(file_path: str) -> List[Document]:
    """
    加载Markdown文档
    解释：Markdown本质是纯文本文件，用TextLoader即可读取
         注：不推荐用UnstructuredMarkdownLoader，因为unstructured库太重（500MB+）
    """
    from langchain_community.document_loaders import TextLoader
    filename = os.path.basename(file_path)
    loader = TextLoader(file_path, encoding="utf-8")
    documents = loader.load()
    for doc in documents:
        doc.metadata["filename"] = filename
        doc.metadata["file_type"] = "md"
    return documents
