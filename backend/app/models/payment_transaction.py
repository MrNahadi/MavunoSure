"""Payment transaction database model"""

from sqlalchemy import Column, String, DateTime, Numeric, Text
from sqlalchemy.sql import func
import uuid
from app.database import Base
from app.core.types import UUID


class PaymentTransactionModel(Base):
    """Payment transaction model for logging mobile money transactions"""
    
    __tablename__ = "payment_transactions"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    transaction_id = Column(String(50), unique=True, nullable=False, index=True)
    claim_id = Column(UUID, nullable=False, index=True)
    phone_number = Column(String(15), nullable=False)
    amount = Column(Numeric(precision=10, scale=2), nullable=False)
    status = Column(String(50), nullable=False)  # completed, failed, pending
    message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<PaymentTransaction(id={self.id}, transaction_id={self.transaction_id}, status={self.status})>"
