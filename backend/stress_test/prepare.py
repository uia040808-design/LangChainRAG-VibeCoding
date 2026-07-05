"""
压力测试准备脚本：批量创建 100 个测试用户

使用方法：
    cd backend
    python stress_test/prepare.py

工作原理：
    1. 调用 POST /api/auth/register 接口注册用户
    2. 用户名格式：testuser001 ~ testuser100
    3. 密码统一：test123456
    4. 已存在的用户会跳过（不会重复注册）

前置条件：
    后端服务已启动（uvicorn，端口 8000）
    系统已存在 admin 用户（启动时自动创建）

注意事项：
    压测完成后，这些测试用户不会自动删除。
    如果需要清理，可以删除 app.db 中的 users 表记录或在管理后台操作。
"""
import httpx
import asyncio
import time

# 配置
BASE_URL = "http://localhost:8000"
TOTAL_USERS = 100
USER_PASSWORD = "test123456"
CONCURRENT_REGISTRATIONS = 10  # 同时注册的用户数（别太快，避免对服务造成压力）


async def register_user(client: httpx.AsyncClient, index: int) -> dict:
    """
    注册单个测试用户

    参数:
        client: httpx 异步客户端
        index: 用户编号（1-100）

    返回:
        {"index": 1, "username": "testuser001", "status": "created"/"skipped"/"failed", "message": "..."}
    """
    username = f"testuser{index:03d}"
    try:
        response = await client.post(
            f"{BASE_URL}/api/auth/register",
            json={
                "username": username,
                "password": USER_PASSWORD,
                "email": f"{username}@test.local",
            },
            timeout=30.0,
        )
        if response.status_code == 200:
            return {"index": index, "username": username, "status": "created"}
        elif response.status_code == 400:
            # 用户名已存在，跳过
            detail = response.json().get("detail", "")
            return {"index": index, "username": username, "status": "skipped",
                    "message": detail}
        else:
            return {"index": index, "username": username, "status": "failed",
                    "message": f"HTTP {response.status_code}: {response.text[:100]}"}
    except Exception as e:
        return {"index": index, "username": username, "status": "failed",
                "message": str(e)[:100]}


async def main():
    """主流程：批量创建 100 个测试用户"""
    print("=" * 60)
    print("  压力测试准备：批量创建 100 个测试用户")
    print("=" * 60)
    print(f"  目标地址: {BASE_URL}")
    print(f"  用户数量: {TOTAL_USERS}")
    print(f"  并发数:   {CONCURRENT_REGISTRATIONS}")
    print("=" * 60)
    print()

    # 先检查后端是否可达
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{BASE_URL}/api/auth/me", timeout=10.0)
            # 预期返回 401（未登录），说明服务正常
            if resp.status_code in (401, 403, 200):
                print("✅ 后端服务连接正常")
            else:
                print(f"⚠️  后端返回异常状态码: {resp.status_code}")
    except httpx.ConnectError:
        print("❌ 无法连接后端服务，请确认 uvicorn 已启动（端口 8000）")
        return
    except Exception as e:
        print(f"❌ 连接后端时发生错误: {e}")
        return

    print()
    start_time = time.time()

    # 分批并发注册
    # 解释：信号量（Semaphore）控制同时进行的任务数，
    #       避免一次性发送 100 个注册请求压垮服务
    semaphore = asyncio.Semaphore(CONCURRENT_REGISTRATIONS)

    async def register_with_limit(index: int) -> dict:
        """带并发限制的注册函数"""
        async with semaphore:
            async with httpx.AsyncClient() as client:
                return await register_user(client, index)

    # 创建 100 个注册任务，分批执行
    tasks = [register_with_limit(i) for i in range(1, TOTAL_USERS + 1)]
    results = await asyncio.gather(*tasks)

    # 统计结果
    created = [r for r in results if r["status"] == "created"]
    skipped = [r for r in results if r["status"] == "skipped"]
    failed = [r for r in results if r["status"] == "failed"]

    elapsed = time.time() - start_time

    # 打印汇总
    print()
    print("=" * 60)
    print("  注册结果汇总")
    print("=" * 60)
    print(f"  ✅ 新建成功: {len(created)} 个")
    print(f"  ⏭️  已存在跳过: {len(skipped)} 个")
    print(f"  ❌ 失败: {len(failed)} 个")
    print(f"  ⏱️  总耗时: {elapsed:.1f} 秒")
    print("=" * 60)

    if failed:
        print()
        print("  失败详情：")
        for f in failed:
            print(f"    - {f['username']}: {f.get('message', '未知错误')}")

    if created:
        usernames = [u["username"] for u in created[:5]]
        print(f"\n  新创建的测试用户示例: {', '.join(usernames)}{'...' if len(created) > 5 else ''}")
        print(f"  密码统一为: {USER_PASSWORD}")

    print()
    print("  准备完成！现在可以运行压力测试：")
    print("    cd backend && locust -f stress_test/locustfile.py")
    print()


if __name__ == "__main__":
    asyncio.run(main())
