"""
直接测试百炼 API 连通性
用于诊断：是 Embedding API 不通，还是 Chat API 不通
"""
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("DASHSCOPE_API_KEY")
BASE_URL = os.getenv("DASHSCOPE_BASE_URL")

print(f"API Key 前缀: {API_KEY[:20]}...")
print(f"Base URL: {BASE_URL}")
print()

# 测试1：直接 HTTP 请求 Embedding API
async def test_embedding():
    """测试 Embedding API 是否能正常调用"""
    import httpx

    url = f"{BASE_URL}/embeddings"
    print(f"[测试1] Embedding API")
    print(f"  请求地址: {url}")
    print(f"  模型: text-embedding-v2")
    print(f"  正在请求...")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "text-embedding-v2",
                    "input": "测试文本",
                },
            )
            print(f"  HTTP状态码: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                emb_len = len(data.get("data", [{}])[0].get("embedding", []))
                print(f"  ✅ Embedding API 正常！向量维度: {emb_len}")
                return True
            else:
                print(f"  ❌ Embedding API 返回错误:")
                print(f"  {response.text[:500]}")
                return False
    except httpx.TimeoutException:
        print(f"  ❌ Embedding API 请求超时（30秒）")
        return False
    except Exception as e:
        print(f"  ❌ Embedding API 异常: {type(e).__name__}: {e}")
        return False


# 测试2：直接 HTTP 请求 Chat API
async def test_chat():
    """测试 Chat API 是否能正常调用（非流式）"""
    import httpx

    url = f"{BASE_URL}/chat/completions"
    print(f"\n[测试2] Chat API")
    print(f"  请求地址: {url}")
    print(f"  模型: qwen-plus")
    print(f"  正在请求...")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "qwen-plus",
                    "messages": [
                        {"role": "user", "content": "你好，请简单介绍一下你自己"}
                    ],
                    "max_tokens": 100,
                },
            )
            print(f"  HTTP状态码: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                print(f"  ✅ Chat API 正常！")
                print(f"  回复内容: {content[:200]}")
                return True
            else:
                print(f"  ❌ Chat API 返回错误:")
                print(f"  {response.text[:500]}")
                return False
    except httpx.TimeoutException:
        print(f"  ❌ Chat API 请求超时（30秒）")
        return False
    except Exception as e:
        print(f"  ❌ Chat API 异常: {type(e).__name__}: {e}")
        return False


async def main():
    print("=" * 60)
    print("百炼 API 连通性诊断")
    print("=" * 60)

    emb_ok = await test_embedding()
    chat_ok = await test_chat()

    print("\n" + "=" * 60)
    print("诊断结果汇总:")
    print(f"  Embedding API: {'✅ 正常' if emb_ok else '❌ 异常'}")
    print(f"  Chat API:      {'✅ 正常' if chat_ok else '❌ 异常'}")

    if not emb_ok and not chat_ok:
        print("\n⚠️  两个 API 都不通，可能原因：")
        print("  1. 工作空间 URL 不支持 /compatible-mode/v1 路径")
        print("  2. 需要用 DashScope 原生 SDK 而非 OpenAI 兼容模式")
        print("  3. API Key 权限不足")
    elif not emb_ok:
        print("\n⚠️  Embedding 不通但 Chat 通，可能是模型名不对")
        print("  尝试把 text-embedding-v2 换成 text-embedding-v1 或其他名称")
    elif not chat_ok:
        print("\n⚠️  Chat 不通但 Embedding 通，可能是模型名不对")

    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
