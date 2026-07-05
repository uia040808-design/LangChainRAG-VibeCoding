# -*- coding: utf-8 -*-
"""
HTTP 级别 SSE 流测试
直接调用后端 REST API，测试完整的 HTTP SSE 流是否正常
需要后端正在运行 (uvicorn app.main:app --port 8000)
"""
import httpx
import json
import asyncio

BACKEND = "http://localhost:8000"


async def test_http_sse():
    print("=" * 60)
    print("HTTP SSE 流测试")
    print("后端地址: %s" % BACKEND)
    print("=" * 60)

    async with httpx.AsyncClient(timeout=60.0) as client:
        # 步骤1：登录获取 token
        print("\n[1] 登录获取Token...")
        try:
            resp = await client.post(
                "%s/api/auth/login" % BACKEND,
                json={"username": "admin", "password": "123456"},
            )
            print("   状态码: %d" % resp.status_code)
            if resp.status_code != 200:
                print("   响应: %s" % resp.text[:300])
                print("[FAIL] 请确认后端已启动 (uvicorn app.main:app --port 8000)")
                return
            data = resp.json()
            token = data.get("access_token") or data.get("token")
            if not token:
                print("   响应: %s" % json.dumps(data, ensure_ascii=False)[:300])
                print("[FAIL] 未找到 token 字段")
                return
            print("   [OK] Token获取成功: %s..." % token[:50])
        except httpx.ConnectError:
            print("[FAIL] 无法连接后端，请先启动: uvicorn app.main:app --port 8000")
            return

        # 步骤2：创建会话
        print("\n[2] 创建会话...")
        resp = await client.post(
            "%s/api/sessions" % BACKEND,
            headers={"Authorization": "Bearer %s" % token},
        )
        session = resp.json()
        session_id = session["id"]
        print("   [OK] 会话ID: %s" % session_id)

        # 步骤3：发送消息并读取SSE流
        print("\n[3] 发送消息并读取SSE流...")
        print("   请求: POST /api/chat/%s" % session_id)

        try:
            async with client.stream(
                "POST",
                "%s/api/chat/%s" % (BACKEND, session_id),
                json={"message": "你好，请问你是什么模型？"},
                headers={
                    "Authorization": "Bearer %s" % token,
                    "Content-Type": "application/json",
                },
            ) as response:
                print("   HTTP状态码: %d" % response.status_code)
                print("   Content-Type: %s" % response.headers.get("content-type", "未知"))
                print()

                if response.status_code != 200:
                    print("   [FAIL] HTTP错误:")
                    body = await response.aread()
                    print("   %s" % body.decode()[:500])
                    return

                # 逐行读取SSE
                print("   --- SSE 事件流 ---")
                event_count = 0
                full_answer = ""
                line_count = 0

                async for line in response.aiter_lines():
                    line_count += 1
                    if not line:
                        continue

                    if line.startswith("event: "):
                        event_type = line[7:]
                        print("   [事件] %s" % event_type)
                        event_count += 1

                    elif line.startswith("data: "):
                        data_str = line[6:]
                        try:
                            data = json.loads(data_str)
                        except json.JSONDecodeError:
                            print("   [数据-解析失败] %s" % data_str[:100])
                            continue

                        # token 事件 - 打印内容
                        if "content" in data and len(str(data)) < 500:
                            print("   [内容] %s" % data["content"])
                            full_answer += data["content"]

                        # sources 事件
                        elif isinstance(data, list):
                            print("   [来源] %d 条" % len(data))

                        # error 事件
                        elif "message" in data and len(str(data)) > 50:
                            print("   [错误] %s" % data["message"][:200])

                        # done 事件
                        elif "message_id" in data:
                            print("   [完成] message_id=%s, 内容长度=%d" % (
                                data.get("message_id", "")[:20],
                                len(data.get("content", ""))
                            ))

                print()
                print("   --- 结束 ---")
                print("   总行数: %d" % line_count)
                print("   事件数: %d" % event_count)
                print("   回答长度: %d 字" % len(full_answer))

                if full_answer:
                    print()
                    print("   [OK] SSE 流测试成功!")
                else:
                    print()
                    print("   [FAIL] 没有收到任何回答内容")

        except httpx.TimeoutException:
            print("   [FAIL] 请求超时")
        except Exception as e:
            print("   [FAIL] 异常: %s" % e)
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_http_sse())
