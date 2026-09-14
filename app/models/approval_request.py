import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class ApprovalRequest(Base):
    __tablename__ = "approval_requests"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False)
    tool_name = Column(String, nullable=False)
    tool_input = Column(JSON, nullable=False)
    status = Column(String, nullable=False, default="pending")  # "pending" | "approved" | "rejected"
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(String, ForeignKey("users.id"), nullable=True)

    conversation = relationship("Conversation", back_populates="approval_requests")

    def __repr__(self):
        return f"<ApprovalRequest {self.tool_name} ({self.status})>"
