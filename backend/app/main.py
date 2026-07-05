"""
FastAPI 应用主入口
=================
启动命令：uvicorn app.main:app --reload --port 8000
API文档：http://localhost:8000/docs（Swagger自动生成）
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.deps import engine, Base
from app.models import User

# 导入所有API路由
from app.api import auth, chat, session, knowledge


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    启动时：创建数据库表，初始化管理员账号
    关闭时：释放数据库连接
    """
    # ===== 启动时执行 =====
    # 1. 创建所有数据库表（如果不存在）
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 2. 初始化管理员账号 admin/123456
    from sqlalchemy import select as _select
    from app.core.deps import async_session_factory
    from app.core.security import hash_password

    async with async_session_factory() as db:
        result = await db.execute(_select(User).where(User.username == "admin"))
        admin = result.scalar_one_or_none()

        if not admin:
            admin = User(
                username="admin",
                email="admin@example.com",
                hashed_password=hash_password("123456"),
                is_admin=True,
            )
            db.add(admin)
            await db.commit()
            print("[初始化] 管理员账号已创建: admin / 123456")
        else:
            print("[初始化] 管理员账号已存在")

    print(f"[启动] {settings.app_name} v{settings.app_version}")
    print(f"[启动] API文档: http://localhost:{settings.backend_port}/docs")
    print(f"[启动] 服务地址: http://localhost:{settings.backend_port}")

    yield  # 应用运行期间

    # ===== 关闭时执行 =====
    await engine.dispose()
    print("[关闭] 数据库连接已释放")


# 创建FastAPI应用实例
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="LangChain RAG 企业级知识库问答系统 - 毕业设计",
    lifespan=lifespan,
)

# ===== CORS中间件配置 =====
# 解释：CORS（跨域资源共享）允许前端（localhost:5173）调用后端（localhost:8000）
# 因为前后端是不同的端口，浏览器默认禁止跨域请求，需要后端明确允许
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        f"http://localhost:{settings.frontend_port}",
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],   # 允许所有HTTP方法
    allow_headers=["*"],   # 允许所有请求头
)

# ===== 注册路由 =====
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(session.router)
app.include_router(knowledge.router)


# ===== 根路径 =====
@app.get("/")
async def root():
    """健康检查接口"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs",
    }
