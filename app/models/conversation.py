import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False, default="New Conversation")
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")
    execution_logs = relationship("ExecutionLog", back_populates="conversation", cascade="all, delete-orphan", order_by="ExecutionLog.created_at")
    approval_requests = relationship("ApprovalRequest", back_populates="conversation", cascade="all, delete-orphan", order_by="ApprovalRequest.created_at")

    def __repr__(self):
        return f"<Conversation {self.id}: {self.title}>"
