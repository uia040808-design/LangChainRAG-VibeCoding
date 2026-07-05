"""
测试 LangChain 封装的 API 调用
用于诊断：LangChain 的 ChatOpenAI / OpenAIEmbeddings 是否正常工作
"""
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("DASHSCOPE_API_KEY")
BASE_URL = os.getenv("DASHSCOPE_BASE_URL")

print(f"Base URL: {BASE_URL}")
print()


async def test_langchain_embedding():
    """测试 LangChain 的 OpenAIEmbeddings"""
    from langchain_openai import OpenAIEmbeddings

    print("[测试1] LangChain OpenAIEmbeddings")
    print(f"  模型: text-embedding-v2")
    print(f"  正在请求...")

    try:
        embeddings = OpenAIEmbeddings(
            model="text-embedding-v2",
            openai_api_base=BASE_URL,
            openai_api_key=API_KEY,
            dimensions=1536,
            request_timeout=30,
        )
        # 用 aembed_query 异步方法
        vector = await embeddings.aembed_query("测试文本")
        print(f"  ✅ LangChain Embedding 正常！向量维度: {len(vector)}")
        return True
    except Exception as e:
        print(f"  ❌ LangChain Embedding 异常: {type(e).__name__}: {e}")
        return False


async def test_langchain_chat():
    """测试 LangChain 的 ChatOpenAI（非流式）"""
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage

    print("\n[测试2] LangChain ChatOpenAI（非流式）")
    print(f"  模型: qwen-plus")
    print(f"  正在请求...")

    try:
        llm = ChatOpenAI(
            model="qwen-plus",
            openai_api_base=BASE_URL,
            openai_api_key=API_KEY,
            temperature=0.3,
            streaming=False,
            max_tokens=100,
            request_timeout=30,
        )
        response = await llm.ainvoke([HumanMessage(content="你好，说一句话")])
        print(f"  ✅ LangChain ChatOpenAI 正常！")
        print(f"  回复: {response.content[:200]}")
        return True
    except Exception as e:
        print(f"  ❌ LangChain ChatOpenAI 异常: {type(e).__name__}: {e}")
        return False


async def test_chromadb():
    """测试 ChromaDB 连接和检索"""
    from langchain_chroma import Chroma
    from langchain_openai import OpenAIEmbeddings

    print("\n[测试3] ChromaDB 向量检索")
    print(f"  正在连接 ChromaDB...")

    try:
        embeddings = OpenAIEmbeddings(
            model="text-embedding-v2",
            openai_api_base=BASE_URL,
            openai_api_key=API_KEY,
            dimensions=1536,
            request_timeout=30,
        )

        import os as _os
        chroma_dir = _os.path.abspath("./chroma_data")
        print(f"  ChromaDB 目录: {chroma_dir}")

        vectorstore = Chroma(
            collection_name="knowledge_base",
            embedding_function=embeddings,
            persist_directory=chroma_dir,
        )

        # 获取集合统计
        try:
            count = vectorstore._collection.count()
            print(f"  集合中的文档块数量: {count}")
        except Exception as e:
            print(f"  无法获取文档数量: {e}")
            count = 0

        if count == 0:
            print(f"  ⚠️  向量数据库为空（没有上传过知识文档）")
            print(f"  ✅ ChromaDB 连接正常（空库也会正常返回）")
            return True

        # 尝试检索
        print(f"  正在检索: '测试问题'...")
        results = vectorstore.similarity_search_with_relevance_scores(
            "测试问题", k=3
        )
        print(f"  ✅ ChromaDB 检索正常！找到 {len(results)} 条结果")
        if results:
            doc, score = results[0]
            print(f"  第一条: 分数={score:.4f}, 内容={doc.page_content[:100]}...")
        return True

    except Exception as e:
        print(f"  ❌ ChromaDB 异常: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    print("=" * 60)
    print("LangChain 封装层诊断")
    print("=" * 60)

    emb_ok = await test_langchain_embedding()
    chat_ok = await test_langchain_chat()
    chroma_ok = await test_chromadb()

    print("\n" + "=" * 60)
    print("诊断结果汇总:")
    print(f"  LangChain Embedding: {'✅ 正常' if emb_ok else '❌ 异常'}")
    print(f"  LangChain ChatOpenAI: {'✅ 正常' if chat_ok else '❌ 异常'}")
    print(f"  ChromaDB 检索:       {'✅ 正常' if chroma_ok else '❌ 异常'}")

    if emb_ok and chat_ok and chroma_ok:
        print("\n✅ 三部分都正常！问题可能在前端 SSE 连接或后端 API 层")
        print("   建议检查：后端 /api/chat 接口的 SSE 事件流是否正常发送")
    else:
        print("\n⚠️  有环节异常，请根据上述报错定位问题")

    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
