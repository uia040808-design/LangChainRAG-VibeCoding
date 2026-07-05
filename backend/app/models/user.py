"""
用户表模型
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.deps import Base


class User(Base):
    __tablename__ = "users"

    # 主键，UUID格式
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    # 用户名，唯一，不可重复
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    # 邮箱
    email: Mapped[str] = mapped_column(String(100), default="")
    # bcrypt加密后的密码
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    # 是否管理员
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    # 注册时间
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    # 更新时间
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # 关联：一个用户有多个会话
    sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")
    # 关联：一个用户上传了多个文档
    documents = relationship("KnowledgeDocument", back_populates="uploader", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(username={self.username}, is_admin={self.is_admin})>"
