"""
文本分块模块
------------
将长文档切分成小块，原因：
1. 大模型有输入长度限制（上下文窗口），不能一次塞太多内容
2. 小块文本更容易被精确检索到相关内容
3. 小块文本的向量表示更准确（不会被其他内容稀释）

分块策略：RecursiveCharacterTextSplitter（递归字符分割器）
- chunk_size=500：每个块约500个字符
- chunk_overlap=50：相邻块之间有50个字符的重叠
  重叠的好处：避免关键信息正好被切在边界上而丢失上下文
"""
from typing import List
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document


# 中文文本分割的默认分隔符
# 解释：分割器会按优先级依次尝试这些分隔符，先按段落分，再按句子分，最后按字符分
CHINESE_SEPARATORS = [
    "\n\n",    # 空行（段落分隔）
    "\n",      # 换行
    "。",      # 中文句号
    "！",      # 中文感叹号
    "？",      # 中文问号
    "；",      # 中文分号
    "，",      # 中文逗号
    ".",       # 英文句号
    "!",       # 英文感叹号
    "?",       # 英文问号
    ";",       # 英文分号
    " ",       # 空格
    "",        # 最后兜底：按字符分割
]


def get_text_splitter(
    chunk_size: int = 500,
    chunk_overlap: int = 50
) -> RecursiveCharacterTextSplitter:
    """
    获取文本分割器实例
    参数：
        chunk_size: 每个文本块的最大字符数
        chunk_overlap: 相邻块重叠的字符数
    返回：配置好的分割器
    """
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=CHINESE_SEPARATORS,
        # 解释：length_function=len 表示用字符数来计算长度
        length_function=len,
        # 解释：is_separator_regex=False 表示分隔符是普通字符串而非正则表达式
        is_separator_regex=False,
    )


def split_documents(
    documents: List[Document],
    chunk_size: int = 500,
    chunk_overlap: int = 50
) -> List[Document]:
    """
    将文档列表分割成小块
    参数：
        documents: 原始文档列表
        chunk_size: 每块最大字符数
        chunk_overlap: 重叠字符数
    返回：分割后的文档块列表，每个块保留了原始文档的元数据
    """
    splitter = get_text_splitter(chunk_size, chunk_overlap)
    chunks = splitter.split_documents(documents)

    # 为每个块添加唯一的chunk_id，方便后续追踪引用来源
    for i, chunk in enumerate(chunks):
        chunk.metadata["chunk_id"] = f"chunk_{i:05d}"

    return chunks
