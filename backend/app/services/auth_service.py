"""
认证业务逻辑
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.user import User
from app.core.security import hash_password, verify_password, create_access_token


async def register_user(
    db: AsyncSession,
    username: str,
    password: str,
    email: str = "",
) -> User:
    """
    注册新用户
    检查用户名是否已存在，不存在则创建
    """
    # 检查用户名是否已存在
    result = await db.execute(select(User).where(User.username == username))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="用户名已存在，请换一个",
        )

    # 创建用户
    user = User(
        username=username,
        email=email,
        hashed_password=hash_password(password),
        is_admin=False,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


async def login_user(
    db: AsyncSession,
    username: str,
    password: str,
) -> dict:
    """
    用户登录
    验证用户名密码，返回JWT Token
    """
    # 查找用户
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )

    # 验证密码
    if not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )

    # 生成JWT
    access_token = create_access_token(data={"sub": user.id})
    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


async def change_password(
    db: AsyncSession,
    user: User,
    old_password: str,
    new_password: str,
):
    """
    修改密码
    先验证旧密码，再更新为新密码
    """
    if not verify_password(old_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="旧密码不正确",
        )

    user.hashed_password = hash_password(new_password)
    await db.flush()
