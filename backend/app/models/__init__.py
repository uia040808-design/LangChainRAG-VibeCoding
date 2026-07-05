from app.core.deps import Base

# 所有模型在此导入，确保 Alembic/建表时能发现
from app.models.user import User
from app.models.session import ChatSession
from app.models.message import Message
from app.models.document import KnowledgeDocument

__all__ = ["Base", "User", "ChatSession", "Message", "KnowledgeDocument"]
