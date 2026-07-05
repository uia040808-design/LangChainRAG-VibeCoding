"""
Embedding 嵌入模块
------------------
将文本转换为向量（一串数字），用于后续的相似度搜索。

使用阿里云百炼的 text-embedding-v2 模型。

⚠️ 为什么不用 LangChain 的 OpenAIEmbeddings？
   OpenAIEmbeddings 底层会用 tiktoken 将中文文本转为 token ID 再发送，
   但工作空间端点（ws-xxx.maas.aliyuncs.com）不认识 token ID 格式，
   只接受原始文本字符串。所以这里自定义一个 Embedding 类，
   用 httpx 直接发送原始文本，绕过 tiktoken 分词。

向量是什么？
  比如 "手机电池" → [0.12, -0.34, 0.56, 0.78, ...]（通常768或1536个数字）
  语义相近的文本，它们的向量在空间中距离也相近。
  所以搜索时只需找"距离最近的向量"就能找到相关内容。
"""
from typing import List
import httpx
from langchain_core.embeddings import Embeddings
from app.core.config import settings


class DashScopeEmbeddings(Embeddings):
    """
    自定义百炼 Embedding 类
    直接通过 HTTP 调用百炼兼容接口，不经过 openai 库的 tiktoken 分词
    """

    def __init__(self, model: str = "text-embedding-v2", timeout: int = 30):
        self.model = model
        self.timeout = timeout
        # 构建完整的 embeddings API 地址
        self.api_url = f"{settings.dashscope_base_url}/embeddings"
        self.api_key = settings.dashscope_api_key
        # 缓存 httpx 客户端，复用 TCP 连接（减少并发场景下的连接开销）
        self._sync_client = None
        self._async_client = None

    def _get_sync_client(self) -> httpx.Client:
        if self._sync_client is None or self._sync_client.is_closed:
            self._sync_client = httpx.Client(timeout=self.timeout)
        return self._sync_client

    def _get_async_client(self) -> httpx.AsyncClient:
        if self._async_client is None or self._async_client.is_closed:
            self._async_client = httpx.AsyncClient(timeout=self.timeout)
        return self._async_client

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        将多个文档文本转为向量（同步版本）
        """
        client = self._get_sync_client()
        vectors = []
        for text in texts:
            vector = self._call_api(client, text)
            vectors.append(vector)
        return vectors

    def embed_query(self, text: str) -> List[float]:
        """
        将单个查询文本转为向量（同步版本）
        """
        return self._call_api(self._get_sync_client(), text)

    async def aembed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        将多个文档文本转为向量（异步版本）
        """
        client = self._get_async_client()
        vectors = []
        for text in texts:
            vector = await self._acall_api(client, text)
            vectors.append(vector)
        return vectors

    async def aembed_query(self, text: str) -> List[float]:
        """
        将单个查询文本转为向量（异步版本）
        """
        return await self._acall_api(self._get_async_client(), text)

    def _call_api(self, client: httpx.Client, text: str) -> List[float]:
        """同步调用百炼 Embedding API（使用复用客户端）"""
        try:
            response = client.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "input": text,  # 直接传原始文本，不转 token ID
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["data"][0]["embedding"]
        except httpx.HTTPStatusError as e:
            raise RuntimeError(
                f"Embedding API 返回错误 (HTTP {e.response.status_code}): {e.response.text[:500]}"
            )
        except httpx.TimeoutException:
            raise RuntimeError(
                "Embedding API 请求超时，请检查网络连接或增加超时时间"
            )

    async def _acall_api(self, client: httpx.AsyncClient, text: str) -> List[float]:
        """异步调用百炼 Embedding API"""
        try:
            response = await client.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "input": text,  # 直接传原始文本，不转 token ID
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["data"][0]["embedding"]
        except httpx.HTTPStatusError as e:
            raise RuntimeError(
                f"Embedding API 返回错误 (HTTP {e.response.status_code}): {e.response.text[:500]}"
            )
        except httpx.TimeoutException:
            raise RuntimeError(
                "Embedding API 请求超时，请检查网络连接或增加超时时间"
            )


def get_embeddings() -> DashScopeEmbeddings:
    """
    获取Embedding模型实例
    返回：配置好的 DashScopeEmbeddings 对象
    """
    return DashScopeEmbeddings(
        model="text-embedding-v2",
        timeout=30,
    )


# 全局Embeddings单例，避免重复创建
_embeddings_instance = None


def get_embeddings_cached() -> DashScopeEmbeddings:
    """获取缓存的Embedding实例（单例模式）"""
    global _embeddings_instance
    if _embeddings_instance is None:
        _embeddings_instance = get_embeddings()
    return _embeddings_instance
