"""
依赖注入模块
------------
FastAPI的依赖注入系统：
每个API函数需要什么资源（数据库连接、当前用户等），
就通过 Depends() 声明，FastAPI自动提供。
这样做的好处是：代码复用、便于测试、解耦。
"""
from typing import AsyncGenerator
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings
from app.core.security import decode_access_token

# ========== 数据库引擎 ==========
# 解释：create_async_engine 创建异步数据库连接引擎
# echo=False 表示不打印SQL日志（生产环境设为False，调试时可改为True）
engine = create_async_engine(
    settings.database_url,
    echo=False,
    connect_args={"check_same_thread": False},  # SQLite特殊配置，允许多线程访问
)

# 解释：async_sessionmaker 是会话工厂，每次请求创建一个新的数据库会话
async_session_factory = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


class Base(DeclarativeBase):
    """SQLAlchemy基类，所有数据库表模型都继承这个类"""
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    获取数据库会话（每个请求一个会话）
    解释：async with 确保请求结束后自动关闭数据库连接
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ========== 用户认证 ==========
# 解释：HTTPBearer 从请求头的 Authorization: Bearer <token> 中提取JWT
security_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
):
    """
    从JWT中获取当前登录用户
    解释：这个函数会在每个需要登录的API接口中自动调用，
    如果用户没有提供有效Token，直接返回401未授权错误
    """
    token = credentials.credentials
    payload = decode_access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="登录已过期，请重新登录",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的登录凭证",
        )

    # 从数据库查询用户（延迟导入避免循环依赖）
    from app.models.user import User
    from sqlalchemy import select

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
        )

    return user


async def get_current_admin_user(
    current_user=Depends(get_current_user),
):
    """
    获取当前管理员用户（权限守卫）
    解释：先验证登录，再检查是否为管理员。如果不是管理员则返回403禁止访问。
    用在知识库管理接口上。
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="仅管理员可访问此功能",
        )
    return current_user
