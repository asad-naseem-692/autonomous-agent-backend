import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime
from sqlalchemy.orm import relationship
from app.core.database import Base

class Customer(Base):
    __tablename__ = "customers"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    balance = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    orders = relationship("Order", back_populates="customer", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Customer {self.name} ({self.email})>"
