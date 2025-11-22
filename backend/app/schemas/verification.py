"""Verification schemas for weighted algorithm"""

from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime
from typing import List, Tuple, Optional


class CropCondition(str, Enum):
    """Crop condition classifications"""
    HEALTHY = "healthy"
    DROUGHT = "drought_stress"
    DISEASE_BLIGHT = "northern_leaf_blight"
    DISEASE_RUST = "common_rust"
    PEST_ARMYWORM = "fall_armyworm"
    OTHER = "other"


class ClaimStatus(str, Enum):
    """Claim processing status"""
    PENDING = "pending"
    AUTO_APPROVED = "auto_approved"
    FLAGGED_FOR_REVIEW = "flagged_for_review"
    REJECTED = "rejected"
    PAID = "paid"


class GroundTruth(BaseModel):
    """Ground Truth data from mobile app"""
    image_url: str
    ml_class: CropCondition
    ml_confidence: float = Field(..., ge=0.0, le=1.0)
    top_three_classes: List[Tuple[CropCondition, float]]
    device_tilt: float
    device_azimuth: float
    capture_gps_lat: float
    capture_gps_lng: float
    capture_timestamp: datetime


class WeightedVerificationResult(BaseModel):
    """Result of weighted verification algorithm"""
    score: float = Field(..., ge=0.0, le=1.0)
    status: ClaimStatus
    explanation: str
    ground_truth_confidence: float = Field(..., ge=0.0, le=1.0)
    space_truth_confidence: float = Field(..., ge=0.0, le=1.0)
    rule_applied: Optional[str] = None
