"""
认证接口：注册、登录、修改密码
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_user
from app.schemas.auth import (
    RegisterRequest, LoginRequest, ChangePasswordRequest,
    TokenResponse, UserResponse,
)
from app.services import auth_service

router = APIRouter(prefix="/api/auth", tags=["认证"])


@router.post("/register", response_model=UserResponse)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    用户注册
    - username: 用户名（2-50字符）
    - password: 密码（至少6位）
    - email: 邮箱（可选）
    """
    user = await auth_service.register_user(
        db=db,
        username=request.username,
        password=request.password,
        email=request.email,
    )
    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    用户登录
    返回JWT Token，之后所有需要认证的请求都要在Header中携带：
    Authorization: Bearer <token>
    """
    return await auth_service.login_user(
        db=db,
        username=request.username,
        password=request.password,
    )


@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    修改密码（需登录）
    """
    await auth_service.change_password(
        db=db,
        user=current_user,
        old_password=request.old_password,
        new_password=request.new_password,
    )
    return {"message": "密码修改成功"}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user=Depends(get_current_user)):
    """
    获取当前登录用户信息（需登录）
    前端用这个接口来验证Token是否有效
    """
    return current_user
