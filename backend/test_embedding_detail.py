"""
深入诊断：LangChain OpenAIEmbeddings 到底发了什么 HTTP 请求
"""
import asyncio
import os
import logging

# 开启 httpx 的调试日志，看看 LangChain 实际发出的请求内容
logging.basicConfig(level=logging.DEBUG)
httpx_logger = logging.getLogger("httpx")
httpx_logger.setLevel(logging.DEBUG)

from dotenv import load_dotenv
load_dotenv()

API_KEY = os.getenv("DASHSCOPE_API_KEY")
BASE_URL = os.getenv("DASHSCOPE_BASE_URL")


async def test_openai_lib_direct():
    """测试用 openai Python 库直接调用 Embedding API"""
    from openai import AsyncOpenAI

    print("\n[测试1] openai 库直接调用 Embedding")
    print(f"  Base URL: {BASE_URL}")

    client = AsyncOpenAI(
        api_key=API_KEY,
        base_url=BASE_URL,
        timeout=30.0,
    )

    # 测试 A：传字符串
    print("\n  --- 测试A：input 为字符串 ---")
    try:
        resp = await client.embeddings.create(
            model="text-embedding-v2",
            input="测试文本",
        )
        print(f"  ✅ 成功！维度: {len(resp.data[0].embedding)}")
    except Exception as e:
        print(f"  ❌ 失败: {e}")

    # 测试 B：传字符串列表
    print("\n  --- 测试B：input 为字符串列表 ---")
    try:
        resp = await client.embeddings.create(
            model="text-embedding-v2",
            input=["测试文本"],
        )
        print(f"  ✅ 成功！维度: {len(resp.data[0].embedding)}")
    except Exception as e:
        print(f"  ❌ 失败: {e}")

    # 测试 C：传字符串 + dimensions 参数
    print("\n  --- 测试C：input 为字符串 + dimensions=1536 ---")
    try:
        resp = await client.embeddings.create(
            model="text-embedding-v2",
            input="测试文本",
            dimensions=1536,
        )
        print(f"  ✅ 成功！维度: {len(resp.data[0].embedding)}")
    except Exception as e:
        print(f"  ❌ 失败: {e}")

    # 测试 D：传字符串列表 + dimensions 参数
    print("\n  --- 测试D：input 为字符串列表 + dimensions=1536 ---")
    try:
        resp = await client.embeddings.create(
            model="text-embedding-v2",
            input=["测试文本"],
            dimensions=1536,
        )
        print(f"  ✅ 成功！维度: {len(resp.data[0].embedding)}")
    except Exception as e:
        print(f"  ❌ 失败: {e}")


async def test_langchain_embedding_variants():
    """测试 LangChain OpenAIEmbeddings 不同配置"""
    from langchain_openai import OpenAIEmbeddings

    print("\n\n[测试2] LangChain OpenAIEmbeddings 不同配置")

    # 变体A：不带 dimensions
    print("\n  --- 变体A：不带 dimensions 参数 ---")
    try:
        embeddings = OpenAIEmbeddings(
            model="text-embedding-v2",
            openai_api_base=BASE_URL,
            openai_api_key=API_KEY,
            request_timeout=30,
        )
        vector = await embeddings.aembed_query("测试文本")
        print(f"  ✅ 成功！维度: {len(vector)}")
    except Exception as e:
        print(f"  ❌ 失败: {e}")

    # 变体B：带 dimensions=1536
    print("\n  --- 变体B：带 dimensions=1536 ---")
    try:
        embeddings = OpenAIEmbeddings(
            model="text-embedding-v2",
            openai_api_base=BASE_URL,
            openai_api_key=API_KEY,
            dimensions=1536,
            request_timeout=30,
        )
        vector = await embeddings.aembed_query("测试文本")
        print(f"  ✅ 成功！维度: {len(vector)}")
    except Exception as e:
        print(f"  ❌ 失败: {e}")

    # 变体C：不带 dimensions + 用 embed_documents（传列表）
    print("\n  --- 变体C：不带 dimensions + embed_documents([...]) ---")
    try:
        embeddings = OpenAIEmbeddings(
            model="text-embedding-v2",
            openai_api_base=BASE_URL,
            openai_api_key=API_KEY,
            request_timeout=30,
        )
        vectors = await embeddings.aembed_documents(["测试文本"])
        print(f"  ✅ 成功！维度: {len(vectors[0])}, 数量: {len(vectors)}")
    except Exception as e:
        print(f"  ❌ 失败: {e}")

    # 变体D：带 dimensions + embed_documents
    print("\n  --- 变体D：带 dimensions=1536 + embed_documents([...]) ---")
    try:
        embeddings = OpenAIEmbeddings(
            model="text-embedding-v2",
            openai_api_base=BASE_URL,
            openai_api_key=API_KEY,
            dimensions=1536,
            request_timeout=30,
        )
        vectors = await embeddings.aembed_documents(["测试文本"])
        print(f"  ✅ 成功！维度: {len(vectors[0])}, 数量: {len(vectors)}")
    except Exception as e:
        print(f"  ❌ 失败: {e}")


async def main():
    print("=" * 60)
    print("Embedding API 深入诊断")
    print("=" * 60)

    await test_openai_lib_direct()
    await test_langchain_embedding_variants()

    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
