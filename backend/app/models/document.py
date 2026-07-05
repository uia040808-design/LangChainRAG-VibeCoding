"""
知识库文档表模型
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.deps import Base


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    # 原始文件名
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    # 文档标题（展示用）
    title: Mapped[str] = mapped_column(String(200), default="")
    # 文件类型：pdf/txt/csv/docx/md
    file_type: Mapped[str] = mapped_column(String(20), nullable=False)
    # 文件大小（字节）
    file_size: Mapped[int] = mapped_column(Integer, default=0)
    # 文件存储路径
    file_path: Mapped[str] = mapped_column(String(500), default="")
    # 分块数量
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    # 处理状态：processing/ready/error
    status: Mapped[str] = mapped_column(String(20), default="processing")
    # 错误信息
    error_message: Mapped[str] = mapped_column(Text, default="")
    # 上传者ID
    created_by: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    # 上传时间
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    # 关联：谁上传的
    uploader = relationship("User", back_populates="documents")

    def __repr__(self):
        return f"<KnowledgeDocument(filename={self.filename}, status={self.status})>"
