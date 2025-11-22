"""Claim Pydantic schemas"""

from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from uuid import UUID
from decimal import Decimal
from enum import Enum
from typing import List, Tuple


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


class SatelliteVerdict(str, Enum):
    """Satellite moisture assessment verdict"""
    SEVERE_STRESS = "severe_stress"
    MODERATE_STRESS = "moderate_stress"
    NORMAL = "normal"


class GroundTruthData(BaseModel):
    """Ground Truth data collected at the farm"""
    ml_class: CropCondition = Field(..., description="ML classification result")
    ml_confidence: float = Field(..., ge=0, le=1, description="ML confidence score")
    top_three_classes: List[Tuple[CropCondition, float]] = Field(..., description="Top 3 predicted classes with confidence scores")
    device_tilt: float | None = Field(None, description="Device tilt angle in degrees")
    device_azimuth: float | None = Field(None, description="Device azimuth bearing")
    capture_gps_lat: Decimal | None = Field(None, ge=-90, le=90, description="GPS latitude at capture")
    capture_gps_lng: Decimal | None = Field(None, ge=-180, le=180, description="GPS longitude at capture")


class SpaceTruthData(BaseModel):
    """Space Truth data from satellite imagery"""
    ndmi_value: float = Field(..., description="Current NDMI value")
    ndmi_14day_avg: float = Field(..., description="14-day average NDMI")
    satellite_verdict: SatelliteVerdict = Field(..., description="Satellite assessment verdict")
    observation_date: datetime = Field(..., description="Satellite observation date")
    cloud_cover_pct: float = Field(..., ge=0, le=100, description="Cloud cover percentage")


class WeightedVerificationResult(BaseModel):
    """Weighted verification algorithm result"""
    weighted_score: float = Field(..., ge=0, le=1, description="Final weighted score")
    status: ClaimStatus = Field(..., description="Claim status decision")
    verdict_explanation: str = Field(..., description="Human-readable explanation")
    ground_truth_confidence: float = Field(..., ge=0, le=1, description="Ground Truth confidence")
    space_truth_confidence: float = Field(..., ge=0, le=1, description="Space Truth confidence")


class ClaimCreate(BaseModel):
    """Schema for creating a claim"""
    agent_id: UUID = Field(..., description="Agent who submitted the claim")
    farm_id: UUID = Field(..., description="Farm associated with the claim")
    ground_truth: GroundTruthData = Field(..., description="Ground Truth data")
    image_data: str = Field(..., description="Base64 encoded image data")
    
    @field_validator("image_data")
    @classmethod
    def validate_image_data(cls, v: str) -> str:
        """Validate image data is not empty"""
        if not v or len(v) < 100:
            raise ValueError("Image data is required and must be valid")
        return v


class ClaimUpdate(BaseModel):
    """Schema for updating a claim"""
    status: ClaimStatus | None = Field(None, description="Updated claim status")
    space_truth: SpaceTruthData | None = Field(None, description="Space Truth data")
    verification_result: WeightedVerificationResult | None = Field(None, description="Verification result")
    payout_amount: Decimal | None = Field(None, ge=0, description="Payout amount")
    payout_status: str | None = Field(None, description="Payout status")
    payout_reference: str | None = Field(None, description="Payout reference")


class ClaimInDB(BaseModel):
    """Schema for claim in database"""
    id: UUID
    agent_id: UUID | None
    farm_id: UUID | None
    status: str
    created_at: datetime
    updated_at: datetime
    
    # Ground Truth
    image_url: str
    ml_class: str
    ml_confidence: float
    top_three_classes: dict | None
    device_tilt: float | None
    device_azimuth: float | None
    capture_gps_lat: Decimal | None
    capture_gps_lng: Decimal | None
    
    # Space Truth
    ndmi_value: float | None
    ndmi_14day_avg: float | None
    satellite_verdict: str | None
    observation_date: datetime | None
    cloud_cover_pct: float | None
    
    # Final Verdict
    weighted_score: float | None
    verdict_explanation: str | None
    ground_truth_confidence: float | None
    space_truth_confidence: float | None
    
    # Payment
    payout_amount: Decimal | None
    payout_status: str | None
    payout_reference: str | None
    
    class Config:
        from_attributes = True


class ClaimResponse(BaseModel):
    """Schema for claim response"""
    id: UUID
    agent_id: UUID | None
    farm_id: UUID | None
    status: ClaimStatus
    created_at: datetime
    updated_at: datetime
    
    # Ground Truth
    image_url: str
    ground_truth: GroundTruthData
    
    # Space Truth (optional, may not be available yet)
    space_truth: SpaceTruthData | None = None
    
    # Final Verdict (optional, may not be available yet)
    verification_result: WeightedVerificationResult | None = None
    
    # Payment
    payout_amount: Decimal | None = None
    payout_status: str | None = None
    payout_reference: str | None = None
    
    class Config:
        from_attributes = True
    
    @classmethod
    def from_orm_model(cls, claim) -> "ClaimResponse":
        """Create ClaimResponse from ORM model"""
        # Build Ground Truth
        ground_truth = GroundTruthData(
            ml_class=CropCondition(claim.ml_class),
            ml_confidence=claim.ml_confidence,
            top_three_classes=claim.top_three_classes or [],
            device_tilt=claim.device_tilt,
            device_azimuth=claim.device_azimuth,
            capture_gps_lat=claim.capture_gps_lat,
            capture_gps_lng=claim.capture_gps_lng
        )
        
        # Build Space Truth if available
        space_truth = None
        if claim.ndmi_value is not None:
            space_truth = SpaceTruthData(
                ndmi_value=claim.ndmi_value,
                ndmi_14day_avg=claim.ndmi_14day_avg,
                satellite_verdict=SatelliteVerdict(claim.satellite_verdict),
                observation_date=claim.observation_date,
                cloud_cover_pct=claim.cloud_cover_pct
            )
        
        # Build Verification Result if available
        verification_result = None
        if claim.weighted_score is not None:
            verification_result = WeightedVerificationResult(
                weighted_score=claim.weighted_score,
                status=ClaimStatus(claim.status),
                verdict_explanation=claim.verdict_explanation or "",
                ground_truth_confidence=claim.ground_truth_confidence or 0.0,
                space_truth_confidence=claim.space_truth_confidence or 0.0
            )
        
        return cls(
            id=claim.id,
            agent_id=claim.agent_id,
            farm_id=claim.farm_id,
            status=ClaimStatus(claim.status),
            created_at=claim.created_at,
            updated_at=claim.updated_at,
            image_url=claim.image_url,
            ground_truth=ground_truth,
            space_truth=space_truth,
            verification_result=verification_result,
            payout_amount=claim.payout_amount,
            payout_status=claim.payout_status,
            payout_reference=claim.payout_reference
        )


class ClaimCreateResponse(BaseModel):
    """Schema for claim creation response"""
    claim_id: UUID = Field(..., description="Unique claim identifier")
    status: ClaimStatus = Field(..., description="Initial claim status")
    message: str = Field(..., description="Response message")


class ClaimListResponse(BaseModel):
    """Schema for paginated claim list response"""
    claims: List[ClaimResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
