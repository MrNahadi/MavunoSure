"""Farm management API endpoints"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

from app.database import get_db
from app.core.dependencies import get_current_agent
from app.models.agent import Agent
from app.schemas.farm import (
    FarmCreate,
    FarmCreateResponse,
    FarmResponse,
    GPSCoordinates
)
from app.services.farm_service import farm_service

router = APIRouter()


@router.post(
    "",
    response_model=FarmCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new farm",
    description="Create a new farm registration with GPS coordinates and farmer information"
)
async def create_farm(
    farm_data: FarmCreate,
    db: Session = Depends(get_db),
    current_agent: Agent = Depends(get_current_agent)
):
    """
    Register a new farm with the following information:
    
    - **farmer_name**: Full name of the farmer
    - **farmer_id**: National ID or identification number
    - **phone_number**: Farmer's phone number
    - **crop_type**: Type of crop (currently only 'maize' supported)
    - **gps_coordinates**: Farm location with lat, lng, and optional accuracy
    
    Returns the created farm with a GPS warning if accuracy > 20m
    """
    # Set the registered_by field to current agent if not provided
    if farm_data.registered_by is None:
        farm_data.registered_by = current_agent.id
    
    try:
        farm = farm_service.create_farm(farm_data, db)
        return farm
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create farm: {str(e)}"
        )


@router.get(
    "/{farm_id}",
    response_model=FarmResponse,
    summary="Get farm by ID",
    description="Retrieve a specific farm by its UUID"
)
async def get_farm(
    farm_id: UUID,
    db: Session = Depends(get_db),
    current_agent: Agent = Depends(get_current_agent)
):
    """
    Get detailed information about a specific farm by ID.
    
    - **farm_id**: UUID of the farm to retrieve
    """
    farm = farm_service.get_farm_by_id(farm_id, db)
    
    if not farm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Farm with id {farm_id} not found"
        )
    
    return FarmResponse(
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


@router.get(
    "/search",
    response_model=List[FarmResponse],
    summary="Search farms by farmer ID",
    description="Search for all farms registered under a specific farmer ID"
)
async def search_farms(
    farmerId: str = Query(..., description="Farmer's identification number to search for"),
    db: Session = Depends(get_db),
    current_agent: Agent = Depends(get_current_agent)
):
    """
    Search for farms by farmer identification number.
    
    - **farmerId**: Farmer's national ID or identification number (query parameter)
    
    Returns a list of all farms registered under this farmer ID.
    """
    farms = farm_service.search_farms_by_farmer_id(farmerId, db)
    
    return [
        FarmResponse(
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
        for farm in farms
    ]
