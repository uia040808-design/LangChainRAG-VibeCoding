"""
SSE 深度剖析脚本 — 测量单次 RAG 请求各阶段的耗时

用途：
    与 Locust 压测配合使用，对单次请求做"微观"分析。
    Locust 给的是宏观指标（RPS、p95），这个脚本给的是
    "一次问答到底慢在哪个环节"——检索？LLM生成？数据库写入？

用法：
    cd backend
    python stress_test/sse_verify.py

输出示例：
    ========================================
      SSE 请求阶段耗时分析
    ========================================
      登录耗时:           234 ms
      创建会话耗时:       45 ms
      --- 聊天各阶段 ---
      HTTP 等待:          312 ms  (从发请求到收到第一个字节)
      首 Token 到达:      1850 ms (检索+生成首个字)
      完整回答生成:       8200 ms (从首Token到done事件)
      总聊天耗时:         10062 ms
      收到 Token 数量:    156 个
      ========================================
"""
import httpx
import time
import json

# 配置
BASE_URL = "http://localhost:8000"
USERNAME = "testuser001"   # 需要先运行 prepare.py 创建
PASSWORD = "test123456"
QUESTION = "iPhone 15 有什么新功能？"


def analyze_sse_request():
    """发送一次 SSE 请求并分析各阶段耗时"""
    print("=" * 50)
    print("  SSE 请求阶段耗时分析")
    print("=" * 50)
    print(f"  目标: {BASE_URL}")
    print(f"  用户: {USERNAME}")
    print(f"  问题: {QUESTION}")
    print("=" * 50)
    print()

    # ---- 阶段 1：登录 ----
    t0 = time.time()
    try:
        resp = httpx.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": USERNAME, "password": PASSWORD},
            timeout=30.0,
        )
        login_time_ms = (time.time() - t0) * 1000
        if resp.status_code != 200:
            print(f"❌ 登录失败: {resp.status_code} {resp.text}")
            print("   请先运行 prepare.py 创建测试用户")
            return
        token = resp.json()["access_token"]
        print(f"  登录耗时:           {login_time_ms:>8.0f} ms")
    except httpx.ConnectError:
        print("❌ 无法连接后端，请确认服务已启动（端口 8000）")
        return

    # ---- 阶段 2：创建会话 ----
    t0 = time.time()
    resp = httpx.post(
        f"{BASE_URL}/api/sessions",
        headers={"Authorization": f"Bearer {token}"},
        timeout=30.0,
    )
    session_time_ms = (time.time() - t0) * 1000
    if resp.status_code != 200:
        print(f"❌ 创建会话失败: {resp.status_code} {resp.text}")
        return
    session_id = resp.json()["id"]
    print(f"  创建会话耗时:       {session_time_ms:>8.0f} ms")

    # ---- 阶段 3：发送聊天请求（SSE 流式）----
    print(f"  会话ID: {session_id[:20]}...")
    print()

    request_start = time.time()
    first_byte_time = None      # 收到第一个 HTTP 字节的时间
    first_token_time = None     # 收到第一个文字 token 的时间
    done_time = None            # 收到 done 事件的时间
    token_count = 0
    full_answer_parts = []

    try:
        with httpx.stream(
            "POST",
            f"{BASE_URL}/api/chat/{session_id}",
            json={"message": QUESTION},
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            timeout=120.0,  # SSE 可能很长时间，给足超时
        ) as response:
            if response.status_code != 200:
                print(f"❌ 聊天请求失败: {response.status_code}")
                return

            current_event = None
            for line in response.iter_lines():
                if first_byte_time is None:
                    first_byte_time = time.time()

                if not line:
                    current_event = None
                    continue

                if line.startswith("event: "):
                    current_event = line[7:].strip()
                elif line.startswith("data: "):
                    data_str = line[6:]
                    try:
                        data = json.loads(data_str)
                    except json.JSONDecodeError:
                        continue

                    if current_event == "token":
                        if first_token_time is None:
                            first_token_time = time.time()
                        token_count += 1
                        full_answer_parts.append(data.get("content", ""))

                    elif current_event == "done":
                        done_time = time.time()

                    elif current_event == "error":
                        print(f"  ❌ SSE 错误: {data.get('message', '未知')}")
                        return

    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return

    # ---- 计算各阶段耗时 ----
    if first_byte_time is None:
        print("❌ 未收到任何响应数据")
        return

    http_wait_ms = (first_byte_time - request_start) * 1000

    if first_token_time is not None:
        first_token_ms = (first_token_time - request_start) * 1000
    else:
        first_token_ms = None

    if done_time is not None and first_token_time is not None:
        generation_ms = (done_time - first_token_time) * 1000
    else:
        generation_ms = None

    total_ms = (time.time() - request_start) * 1000

    # ---- 输出分析结果 ----
    print("  --- 聊天各阶段耗时 ---")
    print(f"  HTTP 等待（首字节）:   {http_wait_ms:>8.0f} ms")
    if first_token_ms is not None:
        print(f"  首 Token 到达:          {first_token_ms:>8.0f} ms  ← 检索 + 生成首个字")
    if generation_ms is not None:
        print(f"  流式生成（Token→Done）: {generation_ms:>8.0f} ms  ← LLM 生成全部回答")
    print(f"  总聊天耗时:             {total_ms:>8.0f} ms")
    print(f"  收到 Token 数:          {token_count:>8} 个")

    print()
    print("  --- 分析 ---")
    if first_token_ms is not None:
        # 首 Token 时间主要反映：检索（Embedding API + 向量搜索）+ LLM 生成第一个字
        if first_token_ms > 3000:
            print("  ⚠️  首 Token 时间 > 3 秒，检索阶段存在明显阻塞")
        elif first_token_ms > 1500:
            print("  ⚡ 首 Token 时间 > 1.5 秒，检索阶段有一定延迟")
        else:
            print("  ✅ 首 Token 时间正常")

        if generation_ms is not None and token_count > 0:
            avg_token_ms = generation_ms / token_count
            print(f"  平均每个 Token 生成耗时: {avg_token_ms:.0f} ms")

    print()
    print("=" * 50)
    full_answer = "".join(full_answer_parts)
    if full_answer:
        print(f"  完整回答预览（前200字）：")
        print(f"  {full_answer[:200]}...")
    print("=" * 50)


if __name__ == "__main__":
    analyze_sse_request()
