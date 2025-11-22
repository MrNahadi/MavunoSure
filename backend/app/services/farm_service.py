"""Farm service for business logic"""

from sqlalchemy.orm import Session
from sqlalchemy import or_
from uuid import UUID
from typing import List, Optional
from app.models.farm import Farm
from app.schemas.farm import (
    FarmCreate,
    FarmResponse,
    FarmCreateResponse,
    GPSValidationWarning,
    GPSCoordinates
)


class FarmService:
    """Service for farm-related operations"""
    
    # GPS accuracy thresholds in meters
    GPS_IDEAL_ACCURACY = 10.0
    GPS_WARNING_ACCURACY = 20.0
    
    def validate_gps_accuracy(self, accuracy: Optional[float]) -> Optional[GPSValidationWarning]:
        """
        Validate GPS accuracy and return warning if needed
        
        Args:
            accuracy: GPS accuracy in meters
            
        Returns:
            GPSValidationWarning if accuracy is suboptimal, None otherwise
        """
        if accuracy is None:
            return None
            
        if accuracy > self.GPS_WARNING_ACCURACY:
            return GPSValidationWarning(
                warning="GPS accuracy is poor. Please move to open ground for better signal.",
                accuracy=accuracy,
                threshold=self.GPS_WARNING_ACCURACY
            )
        
        return None
    
    def create_farm(self, farm_data: FarmCreate, db: Session) -> FarmCreateResponse:
        """
        Create a new farm registration
        
        Args:
            farm_data: Farm creation data
            db: Database session
            
        Returns:
            FarmCreateResponse with GPS warning if applicable
        """
        # Validate GPS accuracy
        gps_warning = self.validate_gps_accuracy(farm_data.gps_coordinates.accuracy)
        
        # Create farm model
        farm = Farm(
            farmer_name=farm_data.farmer_name,
            farmer_id=farm_data.farmer_id,
            phone_number=farm_data.phone_number,
            crop_type=farm_data.crop_type.value,
            gps_lat=farm_data.gps_coordinates.lat,
            gps_lng=farm_data.gps_coordinates.lng,
            gps_accuracy=farm_data.gps_coordinates.accuracy,
            registered_by=farm_data.registered_by
        )
        
        db.add(farm)
        db.commit()
        db.refresh(farm)
        
        # Create response
        response = FarmCreateResponse(
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
            registered_by=farm.registered_by,
            gps_warning=gps_warning
        )
        
        return response
    
    def get_farm_by_id(self, farm_id: UUID, db: Session) -> Optional[Farm]:
        """
        Get farm by ID
        
        Args:
            farm_id: Farm UUID
            db: Database session
            
        Returns:
            Farm model or None if not found
        """
        return db.query(Farm).filter(Farm.id == farm_id).first()
    
    def search_farms_by_farmer_id(self, farmer_id: str, db: Session) -> List[Farm]:
        """
        Search farms by farmer ID
        
        Args:
            farmer_id: Farmer's identification number
            db: Database session
            
        Returns:
            List of Farm models
        """
        return db.query(Farm).filter(Farm.farmer_id == farmer_id).all()


# Singleton instance
farm_service = FarmService()
