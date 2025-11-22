"""Pydantic schemas package"""

from app.schemas.agent import (
    AgentBase,
    AgentCreate,
    AgentUpdate,
    AgentInDB,
    AgentResponse
)
from app.schemas.auth import (
    SendOTPRequest,
    SendOTPResponse,
    VerifyOTPRequest,
    TokenResponse,
    RefreshTokenRequest,
    TokenPayload
)
from app.schemas.farm import (
    CropType,
    FarmBase,
    FarmCreate,
    FarmUpdate,
    FarmInDB,
    FarmResponse,
    FarmCreateResponse,
    GPSCoordinates,
    GPSValidationWarning
)
from app.schemas.claim import (
    CropCondition,
    ClaimStatus,
    SatelliteVerdict,
    GroundTruthData,
    SpaceTruthData,
    WeightedVerificationResult,
    ClaimCreate,
    ClaimUpdate,
    ClaimInDB,
    ClaimResponse,
    ClaimCreateResponse,
    ClaimListResponse
)

__all__ = [
    "AgentBase",
    "AgentCreate",
    "AgentUpdate",
    "AgentInDB",
    "AgentResponse",
    "SendOTPRequest",
    "SendOTPResponse",
    "VerifyOTPRequest",
    "TokenResponse",
    "RefreshTokenRequest",
    "TokenPayload",
    "CropType",
    "FarmBase",
    "FarmCreate",
    "FarmUpdate",
    "FarmInDB",
    "FarmResponse",
    "FarmCreateResponse",
    "GPSCoordinates",
    "GPSValidationWarning",
    "CropCondition",
    "ClaimStatus",
    "SatelliteVerdict",
    "GroundTruthData",
    "SpaceTruthData",
    "WeightedVerificationResult",
    "ClaimCreate",
    "ClaimUpdate",
    "ClaimInDB",
    "ClaimResponse",
    "ClaimCreateResponse",
    "ClaimListResponse"
]
