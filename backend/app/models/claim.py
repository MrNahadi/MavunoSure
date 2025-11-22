"""Claim database model"""

from sqlalchemy import Column, String, DateTime, Float, ForeignKey, Text, Numeric, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.database import Base
from app.core.types import UUID


class Claim(Base):
    """Claim model representing a crop insurance claim"""
    
    __tablename__ = "claims"
    
    # Primary fields
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    agent_id = Column(UUID, ForeignKey('agents.id', ondelete='SET NULL'), nullable=True, index=True)
    farm_id = Column(UUID, ForeignKey('farms.id', ondelete='SET NULL'), nullable=True, index=True)
    status = Column(String(50), nullable=False, index=True, default='pending')
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Ground Truth fields
    image_url = Column(Text, nullable=False)
    ml_class = Column(String(50), nullable=False)
    ml_confidence = Column(Float, nullable=False)
    top_three_classes = Column(JSON, nullable=True)
    device_tilt = Column(Float, nullable=True)
    device_azimuth = Column(Float, nullable=True)
    capture_gps_lat = Column(Numeric(precision=10, scale=8), nullable=True)
    capture_gps_lng = Column(Numeric(precision=11, scale=8), nullable=True)
    
    # Space Truth fields
    ndmi_value = Column(Float, nullable=True)
    ndmi_14day_avg = Column(Float, nullable=True)
    satellite_verdict = Column(String(50), nullable=True)
    observation_date = Column(DateTime(timezone=True), nullable=True)
    cloud_cover_pct = Column(Float, nullable=True)
    
    # Final Verdict fields
    weighted_score = Column(Float, nullable=True)
    verdict_explanation = Column(Text, nullable=True)
    ground_truth_confidence = Column(Float, nullable=True)
    space_truth_confidence = Column(Float, nullable=True)
    
    # Payment fields
    payout_amount = Column(Numeric(precision=10, scale=2), nullable=True)
    payout_status = Column(String(50), nullable=True)
    payout_reference = Column(String(255), nullable=True)
    
    # Relationships
    agent = relationship("Agent", backref="claims")
    farm = relationship("Farm", backref="claims")
    
    def __repr__(self):
        return f"<Claim(id={self.id}, status={self.status}, ml_class={self.ml_class})>"
