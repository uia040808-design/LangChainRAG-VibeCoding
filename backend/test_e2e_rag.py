# -*- coding: utf-8 -*-
"""
端到端 RAG 流程测试
逐步骤执行，定位到底卡在哪一步
"""
import asyncio
import sys
import os
import time

sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()


async def step1_embed_query():
    """步骤1：测试 Embedding 查询"""
    from app.rag.embeddings import get_embeddings

    print("[步骤1] Embedding 查询...", end=" ", flush=True)
    start = time.time()

    try:
        embeddings = get_embeddings()
        vector = await embeddings.aembed_query("你好，请问你是什么模型？")
        elapsed = time.time() - start
        print("[OK] 成功 (%.1fs)，向量维度: %d" % (elapsed, len(vector)))
        return True
    except Exception as e:
        print("[FAIL] 失败: %s" % e)
        return False


async def step2_chromadb_search():
    """步骤2：测试 ChromaDB 向量检索"""
    from langchain_chroma import Chroma
    from app.rag.embeddings import get_embeddings

    print("[步骤2] ChromaDB 检索...", end=" ", flush=True)
    start = time.time()

    try:
        embeddings = get_embeddings()
        chroma_dir = os.path.abspath("./chroma_data")

        vectorstore = Chroma(
            collection_name="knowledge_base",
            embedding_function=embeddings,
            persist_directory=chroma_dir,
        )

        count = vectorstore._collection.count()
        print("(文档数: %d)" % count, end=" ", flush=True)

        results = vectorstore.similarity_search_with_relevance_scores(
            "你好，请问你是什么模型？", k=3
        )
        elapsed = time.time() - start
        print("[OK] 成功 (%.1fs)，找到 %d 条结果" % (elapsed, len(results)))
        return results
    except Exception as e:
        print("[FAIL] 失败: %s" % e)
        import traceback
        traceback.print_exc()
        return None


async def step3_llm_nonstream():
    """步骤3：测试 LLM 非流式调用"""
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage, SystemMessage
    from app.core.config import settings

    print("[步骤3] LLM 非流式调用...", end=" ", flush=True)
    start = time.time()

    try:
        llm = ChatOpenAI(
            model="qwen-plus",
            openai_api_base=settings.dashscope_base_url,
            openai_api_key=settings.dashscope_api_key,
            temperature=0.3,
            streaming=False,
            max_tokens=100,
            request_timeout=30,
        )
        messages = [
            SystemMessage(content="你是一个有帮助的助手。"),
            HumanMessage(content="你好，请问你是什么模型？"),
        ]
        response = await llm.ainvoke(messages)
        elapsed = time.time() - start
        print("[OK] 成功 (%.1fs)" % elapsed)
        print("   回复: %s" % response.content[:150])
        return True
    except Exception as e:
        print("[FAIL] 失败: %s" % e)
        import traceback
        traceback.print_exc()
        return False


async def step4_llm_stream():
    """步骤4：测试 LLM 流式调用"""
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage, SystemMessage
    from app.core.config import settings

    print("[步骤4] LLM 流式调用...", end=" ", flush=True)
    start = time.time()

    try:
        llm = ChatOpenAI(
            model="qwen-plus",
            openai_api_base=settings.dashscope_base_url,
            openai_api_key=settings.dashscope_api_key,
            temperature=0.3,
            streaming=True,
            max_tokens=200,
            request_timeout=30,
        )
        messages = [
            SystemMessage(content="你是一个有帮助的助手，回答要简短。"),
            HumanMessage(content="用一句话介绍你自己"),
        ]

        full = ""
        chunk_count = 0
        print()
        print("   流式内容: ", end="", flush=True)

        async for chunk in llm.astream(messages):
            if chunk.content:
                full += chunk.content
                chunk_count += 1
                print(chunk.content, end="", flush=True)

        elapsed = time.time() - start
        print()
        print("   [OK] 成功 (%.1fs)，%d 个chunk，共 %d 字" % (elapsed, chunk_count, len(full)))
        return True
    except Exception as e:
        print()
        print("   [FAIL] 失败: %s" % e)
        import traceback
        traceback.print_exc()
        return False


async def step5_full_rag_pipeline():
    """步骤5：完整 RAG 流程（generate_answer）"""
    from app.rag.chain import generate_answer

    print("[步骤5] 完整 RAG 流程...")
    start = time.time()

    try:
        print("   等待第一个chunk...", end=" ", flush=True)
        first = True

        async for chunk in generate_answer(
            query="你好，请问你是什么模型？",
            chat_history=[],
        ):
            if first:
                print("(首个chunk耗时 %.1fs)" % (time.time() - start))
                first = False

            if chunk["type"] == "sources":
                print("   [来源] %d 条" % len(chunk["data"]))
            elif chunk["type"] == "token":
                print(chunk["content"], end="", flush=True)
            elif chunk["type"] == "done":
                print()
                print("   [OK] 完成！总耗时 %.1fs" % (time.time() - start))
                print("   完整回答长度: %d 字" % len(chunk["content"]))
            elif chunk["type"] == "error":
                print()
                print("   [FAIL] 错误: %s" % chunk["message"])
                return False

        return True
    except Exception as e:
        print()
        print("   [FAIL] 异常: %s" % e)
        import traceback
        traceback.print_exc()
        return False


async def main():
    print("=" * 60)
    print("RAG 端到端诊断 - 逐步骤执行")
    print("=" * 60)
    print()

    results = {}

    # 步骤1
    results["Embedding"] = await step1_embed_query()
    if not results["Embedding"]:
        print()
        print("[STOP] Embedding 失败，后续无法继续。")
        return
    print()

    # 步骤2
    results["ChromaDB"] = await step2_chromadb_search()
    if results["ChromaDB"] is None:
        print()
        print("[STOP] ChromaDB 检索失败。")
        return
    print()

    # 步骤3
    results["LLM非流式"] = await step3_llm_nonstream()
    print()

    # 步骤4
    results["LLM流式"] = await step4_llm_stream()
    print()

    # 步骤5
    results["完整RAG"] = await step5_full_rag_pipeline()
    print()

    # 汇总
    print("=" * 60)
    print("诊断结果汇总:")
    for name, ok in results.items():
        status = "OK" if ok else "FAIL"
        print("  %s: [%s]" % (name, status))
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
