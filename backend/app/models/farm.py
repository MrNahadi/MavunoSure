"""Farm database model"""

from sqlalchemy import Column, String, DateTime, Float, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.database import Base
from app.core.types import UUID


class Farm(Base):
    """Farm model representing a registered farm"""
    
    __tablename__ = "farms"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    farmer_name = Column(String(255), nullable=False)
    farmer_id = Column(String(50), nullable=False, index=True)
    phone_number = Column(String(15), nullable=False)
    crop_type = Column(String(50), nullable=False)
    gps_lat = Column(Numeric(precision=10, scale=8), nullable=False)
    gps_lng = Column(Numeric(precision=11, scale=8), nullable=False)
    gps_accuracy = Column(Float, nullable=True)
    registered_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    registered_by = Column(UUID, ForeignKey('agents.id', ondelete='SET NULL'), nullable=True, index=True)
    
    # Relationship to agent
    agent = relationship("Agent", backref="farms")
    
    def __repr__(self):
        return f"<Farm(id={self.id}, farmer_name={self.farmer_name}, crop_type={self.crop_type})>"
