import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class Order(Base):
    __tablename__ = "orders"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_id = Column(String, ForeignKey("customers.id"), nullable=False)
    status = Column(String, nullable=False)  # pending, processing, shipped, delivered, cancelled, refunded
    amount = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    customer = relationship("Customer", back_populates="orders")

    def __repr__(self):
        return f"<Order {self.id} (${self.amount}, {self.status})>"
