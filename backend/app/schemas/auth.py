"""
认证相关的请求/响应数据模型
"""
from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field, field_validator


# ========== 请求模型 ==========

class RegisterRequest(BaseModel):
    """注册请求"""
    username: str = Field(..., min_length=2, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, max_length=100, description="密码")
    email: str = Field(default="", max_length=100, description="邮箱")


class LoginRequest(BaseModel):
    """登录请求"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class ChangePasswordRequest(BaseModel):
    """修改密码请求"""
    old_password: str = Field(..., description="旧密码")
    new_password: str = Field(..., min_length=6, max_length=100, description="新密码")


# ========== 响应模型 ==========

class TokenResponse(BaseModel):
    """登录成功后返回的Token"""
    access_token: str = Field(..., description="JWT访问令牌")
    token_type: str = Field(default="bearer", description="令牌类型")


class UserResponse(BaseModel):
    """用户信息响应"""
    id: str
    username: str
    email: str
    is_admin: bool
    created_at: str

    model_config = {"from_attributes": True}

    @field_validator('created_at', mode='before')
    @classmethod
    def coerce_datetime(cls, v: Any) -> str:
        if isinstance(v, datetime):
            return v.isoformat()
        return str(v) if v else ""
