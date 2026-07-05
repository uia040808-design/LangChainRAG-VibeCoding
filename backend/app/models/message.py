"""
消息表模型
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.deps import Base


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    # 外键：属于哪个会话
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    # 角色：user(用户提问) 或 assistant(AI回答)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    # 消息内容
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    # 引用的知识库来源（JSON字符串）
    sources: Mapped[str] = mapped_column(Text, default="[]")
    # 用户反馈：like / dislike / null
    feedback: Mapped[str] = mapped_column(String(10), nullable=True)
    # 创建时间
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    # 关联：属于哪个会话
    session = relationship("ChatSession", back_populates="messages")

    def __repr__(self):
        return f"<Message(role={self.role}, session_id={self.session_id})>"
