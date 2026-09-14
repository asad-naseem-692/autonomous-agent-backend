import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class ExecutionLog(Base):
    __tablename__ = "execution_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False)
    tool_name = Column(String, nullable=False)
    tool_input = Column(JSON, nullable=False)
    tool_output = Column(JSON, nullable=True)
    status = Column(String, nullable=False)  # "executed" | "pending_approval" | "rejected" | "failed"
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    conversation = relationship("Conversation", back_populates="execution_logs")

    def __repr__(self):
        return f"<ExecutionLog {self.tool_name} ({self.status})>"
