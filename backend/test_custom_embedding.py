"""
测试新的 DashScopeEmbeddings 自定义类
"""
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

# 把 backend 目录加入 Python 路径
import sys
sys.path.insert(0, os.path.dirname(__file__))


async def test_custom_embedding():
    """测试自定义 DashScopeEmbeddings"""
    from app.rag.embeddings import DashScopeEmbeddings

    print("[测试1] DashScopeEmbeddings - embed_query（同步）")
    embeddings = DashScopeEmbeddings(model="text-embedding-v2", timeout=30)
    print(f"  API URL: {embeddings.api_url}")
    print(f"  正在请求...")

    try:
        vector = embeddings.embed_query("测试文本")
        print(f"  ✅ 成功！向量维度: {len(vector)}")
        print(f"  前5个值: {vector[:5]}")
    except Exception as e:
        print(f"  ❌ 失败: {e}")
        return False

    print("\n[测试2] DashScopeEmbeddings - aembed_query（异步）")
    try:
        vector = await embeddings.aembed_query("异步测试文本")
        print(f"  ✅ 成功！向量维度: {len(vector)}")
    except Exception as e:
        print(f"  ❌ 失败: {e}")
        return False

    print("\n[测试3] DashScopeEmbeddings - embed_documents（批量同步）")
    try:
        vectors = embeddings.embed_documents(["文本1", "文本2", "文本3"])
        print(f"  ✅ 成功！返回 {len(vectors)} 个向量，维度: {len(vectors[0])}")
    except Exception as e:
        print(f"  ❌ 失败: {e}")
        return False

    print("\n[测试4] DashScopeEmbeddings - aembed_documents（批量异步）")
    try:
        vectors = await embeddings.aembed_documents(["异步文本1", "异步文本2"])
        print(f"  ✅ 成功！返回 {len(vectors)} 个向量，维度: {len(vectors[0])}")
    except Exception as e:
        print(f"  ❌ 失败: {e}")
        return False

    return True


async def test_chromadb_integration():
    """测试 ChromaDB 与 DashScopeEmbeddings 集成"""
    from langchain_chroma import Chroma
    from app.rag.embeddings import get_embeddings

    print("\n[测试5] ChromaDB + DashScopeEmbeddings 集成")
    embeddings = get_embeddings()

    import os as _os
    chroma_dir = _os.path.abspath("./chroma_data")
    print(f"  ChromaDB 目录: {chroma_dir}")

    try:
        vectorstore = Chroma(
            collection_name="knowledge_base",
            embedding_function=embeddings,
            persist_directory=chroma_dir,
        )

        count = vectorstore._collection.count()
        print(f"  文档数量: {count}")

        # 即使为空也应该能正常返回
        results = vectorstore.similarity_search_with_relevance_scores(
            "测试问题", k=3
        )
        print(f"  ✅ ChromaDB + DashScopeEmbeddings 集成正常！")
        print(f"  检索到 {len(results)} 条结果")
        return True
    except Exception as e:
        print(f"  ❌ 失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    print("=" * 60)
    print("自定义 DashScopeEmbeddings 测试")
    print("=" * 60)

    emb_ok = await test_custom_embedding()
    chroma_ok = await test_chromadb_integration()

    print("\n" + "=" * 60)
    print("结果:")
    print(f"  DashScopeEmbeddings: {'✅ 正常' if emb_ok else '❌ 异常'}")
    print(f"  ChromaDB 集成:       {'✅ 正常' if chroma_ok else '❌ 异常'}")

    if emb_ok and chroma_ok:
        print("\n✅ 自定义 Embedding 类工作正常，可以重启后端测试问答了！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
