"""Farm Pydantic schemas"""

from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from uuid import UUID
from decimal import Decimal
from enum import Enum


class CropType(str, Enum):
    """Supported crop types"""
    MAIZE = "maize"
    # Future crops can be added here


class FarmBase(BaseModel):
    """Base farm schema"""
    farmer_name: str = Field(..., min_length=1, max_length=255, description="Farmer's full name")
    farmer_id: str = Field(..., min_length=1, max_length=50, description="Farmer's national ID or identification number")
    phone_number: str = Field(..., description="Farmer's phone number in E.164 format")
    crop_type: CropType = Field(..., description="Type of crop grown on the farm")
    
    @field_validator("farmer_name")
    @classmethod
    def validate_farmer_name(cls, v: str) -> str:
        """Validate farmer name is not empty after stripping"""
        if not v.strip():
            raise ValueError("Farmer name cannot be empty")
        return v.strip()
    
    @field_validator("farmer_id")
    @classmethod
    def validate_farmer_id(cls, v: str) -> str:
        """Validate farmer ID is not empty after stripping"""
        if not v.strip():
            raise ValueError("Farmer ID cannot be empty")
        return v.strip()


class GPSCoordinates(BaseModel):
    """GPS coordinates with accuracy"""
    lat: Decimal = Field(..., ge=-90, le=90, description="Latitude in decimal degrees")
    lng: Decimal = Field(..., ge=-180, le=180, description="Longitude in decimal degrees")
    accuracy: float | None = Field(None, gt=0, description="GPS accuracy in meters")
    
    @field_validator("accuracy")
    @classmethod
    def validate_accuracy(cls, v: float | None) -> float | None:
        """Validate GPS accuracy is positive"""
        if v is not None and v <= 0:
            raise ValueError("GPS accuracy must be positive")
        return v


class FarmCreate(FarmBase):
    """Schema for creating a farm"""
    gps_coordinates: GPSCoordinates = Field(..., description="Farm GPS coordinates")
    registered_by: UUID | None = Field(None, description="Agent ID who registered the farm")


class FarmUpdate(BaseModel):
    """Schema for updating a farm"""
    farmer_name: str | None = Field(None, min_length=1, max_length=255)
    phone_number: str | None = Field(None)
    crop_type: CropType | None = Field(None)
    gps_coordinates: GPSCoordinates | None = Field(None)


class FarmInDB(FarmBase):
    """Schema for farm in database"""
    id: UUID
    gps_lat: Decimal
    gps_lng: Decimal
    gps_accuracy: float | None
    registered_at: datetime
    registered_by: UUID | None
    
    class Config:
        from_attributes = True


class FarmResponse(BaseModel):
    """Schema for farm response"""
    id: UUID
    farmer_name: str
    farmer_id: str
    phone_number: str
    crop_type: CropType
    gps_coordinates: GPSCoordinates
    registered_at: datetime
    registered_by: UUID | None
    
    class Config:
        from_attributes = True
    
    @classmethod
    def from_orm_model(cls, farm: "Farm") -> "FarmResponse":
        """Create FarmResponse from ORM model"""
        return cls(
            id=farm.id,
            farmer_name=farm.farmer_name,
            farmer_id=farm.farmer_id,
            phone_number=farm.phone_number,
            crop_type=farm.crop_type,
            gps_coordinates=GPSCoordinates(
                lat=farm.gps_lat,
                lng=farm.gps_lng,
                accuracy=farm.gps_accuracy
            ),
            registered_at=farm.registered_at,
            registered_by=farm.registered_by
        )


class GPSValidationWarning(BaseModel):
    """GPS validation warning"""
    warning: str
    accuracy: float
    threshold: float


class FarmCreateResponse(FarmResponse):
    """Schema for farm creation response with optional GPS warning"""
    gps_warning: GPSValidationWarning | None = Field(None, description="Warning if GPS accuracy is suboptimal")
