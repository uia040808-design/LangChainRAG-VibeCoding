"""
Locust 压力测试主脚本 — 模拟 100 人同时使用 RAG 问答系统

使用方法：
    1. 先运行 prepare.py 创建测试用户
    2. cd backend && locust -f stress_test/locustfile.py
    3. 浏览器打开 http://localhost:8089 配置并启动测试

测试流程（每个虚拟用户）：
    1. 登录 → 获取 JWT Token
    2. 创建会话 → 获取 session_id
    3. 发送问题 → 消费 SSE 流直到 done 事件
    4. 等待 3-8 秒（模拟用户思考）
    5. 重复步骤 3-4，共 3 轮对话

自定义指标：
    - first_token_time: 从发请求到收到第一个 token 的耗时（衡量检索阻塞程度）
    - login_time: 登录耗时
    - create_session_time: 创建会话耗时
"""
import time
import json
import random
from locust import HttpUser, task, between, events

from test_data import get_all_users, get_question_pool

# ============================================================
# 全局配置
# ============================================================
# 解释：这些常量控制压测的行为

ROUNDS_PER_USER = 3          # 每个用户进行几轮对话
THINK_TIME_MIN = 3           # 用户思考时间最小值（秒）
THINK_TIME_MAX = 8           # 用户思考时间最大值（秒）

# 加载测试数据
ALL_USERS = get_all_users()         # 100 个测试用户的凭据
QUESTION_POOL = get_question_pool()  # 问题池


# ============================================================
# 自定义 Locust 事件 — 记录首 Token 时间
# ============================================================
# 解释：Locust 默认只记录请求的"总耗时"。
#       但 SSE 流式请求中，我们更关心"第一个字啥时候出来"（首 Token 时间）
#       因为它直接反映了"检索阶段"（同步阻塞）对用户体验的影响。
#       通过自定义事件，在 Locust 报告中单独追踪这个指标。

@events.init.add_listener
def on_locust_init(environment, **kwargs):
    """Locust 启动时，注册一个自定义指标"首Token时间"（单位毫秒）"""

    # 解释：environment 就是 Locust 的整个运行环境
    from locust.stats import PERCENTILES_TO_REPORT
    from locust.event import Events

    # 方式：在 request 事件中额外记录 first_token_time
    # Locust 的 events.request.fire() 在 locustfile 中手动调用时
    # 可以通过自定义名称来区分指标

    print("✅ Locust 压测脚本已加载")
    print(f"   测试用户数: {len(ALL_USERS)}")
    print(f"   问题池大小: {len(QUESTION_POOL)}")
    print(f"   每用户对话轮数: {ROUNDS_PER_USER}")


class RAGUser(HttpUser):
    """
    RAG 系统虚拟用户类

    每个虚拟用户 = 一个独立的测试用户账号，
    模拟完整的"登录 → 建会话 → 多轮问答"流程。
    """

    # 解释：wait_time = between(3, 8) 表示每轮对话之间等待 3-8 秒
    #       模拟真实用户思考时间，避免请求过于密集
    wait_time = between(THINK_TIME_MIN, THINK_TIME_MAX)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.token: str = ""          # JWT Token
        self.username: str = ""       # 当前用户名
        self.round_count: int = 0     # 当前已完成的对话轮数

    def on_start(self):
        """
        每个虚拟用户启动时执行一次：登录 + 创建会话

        Locust 会在创建虚拟用户时自动调用这个方法，
        相当于用户打开浏览器→登录→点击"新建会话"的过程
        """
        # ---- 步骤 1：登录 ----
        user = random.choice(ALL_USERS)
        self.username = user["username"]

        login_start = time.time()
        with self.client.post(
            "/api/auth/login",
            json={"username": user["username"], "password": user["password"]},
            name="POST /api/auth/login",      # name= 让 Locust 按这个名称分组统计
            catch_response=True,
        ) as response:
            login_time_ms = (time.time() - login_start) * 1000

            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token", "")
                response.success()
            else:
                response.failure(f"登录失败: {response.status_code} {response.text[:100]}")

        # ---- 步骤 2：创建会话 ----
        session_start = time.time()
        with self.client.post(
            "/api/sessions",
            headers={"Authorization": f"Bearer {self.token}"},
            name="POST /api/sessions",
            catch_response=True,
        ) as response:
            session_time_ms = (time.time() - session_start) * 1000

            if response.status_code == 200:
                data = response.json()
                self.session_id = data.get("id", "")
                response.success()
            else:
                self.session_id = ""
                response.failure(f"创建会话失败: {response.status_code} {response.text[:100]}")

    @task
    def chat_round(self):
        """
        核心任务：发送一个问题并消费 SSE 流式回答

        每个虚拟用户会反复执行这个任务（每轮之间 wait_time 秒间隔），
        直到完成 ROUNDS_PER_USER 轮对话后停止。

        SSE 流式处理逻辑：
        1. 发送 POST 请求，设置 stream=True
        2. 逐行读取响应体（SSE 格式：event: xxx\ndata: {...}\n\n）
        3. 记录第一个 "token" 事件的时间 → first_token_time
        4. 收到 "done" 事件后结束本轮
        """
        # 达到对话轮数上限后不再发请求
        # 解释：Locust 的 task 装饰器会让这个方法反复被调用，
        #       通过 round_count 计数器来控制每个用户只做固定轮数
        if self.round_count >= ROUNDS_PER_USER:
            return

        # 如果登录或创建会话失败，跳过
        if not self.token or not getattr(self, "session_id", ""):
            return

        # 随机选一个问题
        question = random.choice(QUESTION_POOL)

        # 发送 SSE 请求
        request_start = time.time()
        first_token_time = None  # 首 token 到达时间

        with self.client.post(
            f"/api/chat/{self.session_id}",
            json={"message": question},
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
            },
            name="POST /api/chat/{session_id}",
            catch_response=True,
            stream=True,  # 关键：启用流式读取
        ) as response:
            if response.status_code != 200:
                response.failure(f"聊天请求失败: {response.status_code} {response.text[:100]}")
                return

            # 逐行解析 SSE 事件流
            # SSE 格式示例：
            #   event: token
            #   data: {"content": "你好"}
            #
            #   event: done
            #   data: {"message_id": "xxx", "content": "完整答案"}
            current_event = None
            token_count = 0
            done_received = False

            try:
                for line in response.iter_lines(decode_unicode=True):
                    if not line:
                        # 空行 = 一个事件的结束
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

                        # 记录首 token 时间
                        if current_event == "token" and first_token_time is None:
                            first_token_time = time.time()
                            # 解释：用 Locust 的自定义事件上报首 Token 时间
                            #       response_time 单位是毫秒
                            ft_ms = (first_token_time - request_start) * 1000
                            events.request.fire(
                                request_type="SSE",
                                name="首Token时间 (检索+生成首个字)",
                                response_time=ft_ms,
                                response_length=1,
                            )

                        if current_event == "token":
                            token_count += 1

                        if current_event == "done":
                            done_received = True

                        if current_event == "error":
                            response.failure(f"服务端SSE错误: {data.get('message', '')}")
                            return

            except Exception as e:
                response.failure(f"SSE流读取异常: {str(e)[:100]}")
                return

            if done_received:
                total_time_ms = (time.time() - request_start) * 1000
                response.success()
            else:
                response.failure("SSE流未收到done事件")

        self.round_count += 1

    # ------------------------------------------------------------------
    # 以下两个 task 用于收集结束后自动输出汇总报告
    # ------------------------------------------------------------------
    # 解释：Locust 的 @task 装饰器可以设置权重（数字越大执行频率越高）。
    #       chat_round 是主要任务，权重默认 1。
    #       下面的 on_stop 会在压测结束时输出一份中文总结。

    def on_stop(self):
        """
        虚拟用户停止时调用（压测结束或用户数缩减时触发），
        输出该用户的简要统计。
        """
        print(f"[{self.username}] 完成 {self.round_count} 轮对话")


# ============================================================
# 压测结束后的自动汇总报告
# ============================================================
# 解释：Locust 的 quitting 事件在压测停止时触发，
#       这里输出一份中文总结报告，方便直接用于毕业设计论文。

@events.quitting.add_listener
def on_quitting(environment, **kwargs):
    """
    压测结束时自动输出的中文汇总报告
    包含：请求统计、首Token延迟、失败率、性能拐点判断
    """
    print()
    print("=" * 65)
    print("   📊 压力测试汇总报告")
    print("=" * 65)

    if not environment.stats.total.num_requests:
        print("   ⚠️  没有收集到任何请求数据，请检查测试配置")
        return

    stats = environment.stats.total

    # 1. 基本统计
    print(f"   总请求数:      {stats.num_requests}")
    print(f"   总失败数:      {stats.num_failures}")
    print(f"   失败率:        {stats.fail_ratio * 100:.2f}%")
    print(f"   平均 RPS:      {stats.total_rps:.1f} 请求/秒")
    print()

    # 2. 响应时间分布
    print("   --- 响应时间分布（毫秒）---")
    print(f"   最小值:        {stats.min_response_time:.0f} ms")
    print(f"   平均值:        {stats.avg_response_time:.0f} ms")
    print(f"   中位数 p50:    {stats.get_response_time_percentile(0.50):.0f} ms")
    print(f"   p95:           {stats.get_response_time_percentile(0.95):.0f} ms")
    print(f"   p99:           {stats.get_response_time_percentile(0.99):.0f} ms")
    print(f"   最大值:        {stats.max_response_time:.0f} ms")
    print()

    # 3. 按接口分组统计
    print("   --- 各接口耗时（毫秒）---")
    print(f"   {'接口':<40} {'请求数':>6} {'平均':>8} {'p95':>8} {'失败率':>8}")
    print(f"   {'-'*40} {'-'*6} {'-'*8} {'-'*8} {'-'*8}")

    for entry in environment.stats.entries.values():
        if entry.num_requests == 0:
            continue
        name = entry.name[:40]
        fail_pct = entry.fail_ratio * 100
        avg = entry.avg_response_time
        p95 = entry.get_response_time_percentile(0.95) if entry.num_requests > 0 else 0
        print(f"   {name:<40} {entry.num_requests:>6} {avg:>7.0f}ms {p95:>7.0f}ms {fail_pct:>7.1f}%")

    print()

    # 4. 性能拐点分析
    #    解释：根据失败率和 p95 延迟，判断系统是否达到了性能上限
    if stats.fail_ratio > 0.1:
        print("   ⚠️  失败率超过 10%，系统可能已达到并发上限")
    elif stats.fail_ratio > 0.05:
        print("   ⚡ 失败率在 5%-10% 之间，系统接近性能拐点")
    else:
        print("   ✅ 失败率低于 5%，系统在此并发量下运行稳定")

    # 检查 p95 延迟
    p95 = stats.get_response_time_percentile(0.95)
    if p95 > 30000:
        print("   ⚠️  p95 延迟超过 30 秒，用户体验严重受影响")
    elif p95 > 10000:
        print("   ⚡ p95 延迟超过 10 秒，用户体验较差")
    else:
        print("   ✅ p95 延迟在可接受范围内")

    print()
    print("   --- 毕业设计论文可用结论 ---")
    print(f"   1. 系统在 {environment.runner.target_user_count if environment.runner else '?'} 并发用户下的失败率为 {stats.fail_ratio * 100:.2f}%")
    user_count = getattr(environment.runner, 'target_user_count', '?') if environment.runner else '?'

    if stats.num_failures > 0:
        # 尝试识别主要错误类型
        print(f"   2. 主要瓶颈：需查看后端日志确认具体错误类型")
    print(f"   3. 平均响应时间：{stats.avg_response_time:.0f}ms，p95：{p95:.0f}ms")
    print(f"   4. 最大 RPS：{stats.total_rps:.1f}")

    print()
    print("=" * 65)
    print("   提示：以上数据也可在 Locust Web UI 中查看图表和导出 CSV")
    print("=" * 65)
    print()
