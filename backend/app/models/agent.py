"""Agent database model"""

from sqlalchemy import Column, String, DateTime
from sqlalchemy.sql import func
import uuid
from app.database import Base
from app.core.types import UUID


class Agent(Base):
    """Agent (Village Agent) model"""
    
    __tablename__ = "agents"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    phone_number = Column(String(15), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<Agent(id={self.id}, phone_number={self.phone_number})>"
