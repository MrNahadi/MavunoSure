"""Unit tests for farm service"""

import pytest
from decimal import Decimal
from app.services.farm_service import farm_service
from app.schemas.farm import FarmCreate, GPSCoordinates, CropType


class TestFarmService:
    """Test farm service business logic"""
    
    def test_validate_gps_accuracy_ideal(self):
        """Test GPS validation with ideal accuracy (< 10m)"""
        warning = farm_service.validate_gps_accuracy(5.0)
        assert warning is None
    
    def test_validate_gps_accuracy_acceptable(self):
        """Test GPS validation with acceptable accuracy (10-20m)"""
        warning = farm_service.validate_gps_accuracy(15.0)
        assert warning is None
    
    def test_validate_gps_accuracy_poor(self):
        """Test GPS validation with poor accuracy (> 20m)"""
        warning = farm_service.validate_gps_accuracy(25.0)
        assert warning is not None
        assert warning.accuracy == 25.0
        assert warning.threshold == 20.0
        assert "poor" in warning.warning.lower()
    
    def test_validate_gps_accuracy_none(self):
        """Test GPS validation with no accuracy data"""
        warning = farm_service.validate_gps_accuracy(None)
        assert warning is None
    
    def test_validate_gps_accuracy_at_threshold(self):
        """Test GPS validation exactly at warning threshold"""
        warning = farm_service.validate_gps_accuracy(20.0)
        assert warning is None
    
    def test_validate_gps_accuracy_just_above_threshold(self):
        """Test GPS validation just above warning threshold"""
        warning = farm_service.validate_gps_accuracy(20.1)
        assert warning is not None
        assert warning.accuracy == 20.1
    
    def test_create_farm_with_good_gps(self, db_session):
        """Test creating farm with good GPS accuracy"""
        farm_data = FarmCreate(
            farmer_name="John Doe",
            farmer_id="12345678",
            phone_number="+254712345678",
            crop_type=CropType.MAIZE,
            gps_coordinates=GPSCoordinates(
                lat=Decimal("-1.286389"),
                lng=Decimal("36.817223"),
                accuracy=8.5
            )
        )
        
        result = farm_service.create_farm(farm_data, db_session)
        
        assert result.id is not None
        assert result.farmer_name == "John Doe"
        assert result.farmer_id == "12345678"
        assert result.gps_coordinates.accuracy == 8.5
        assert result.gps_warning is None
    
    def test_create_farm_with_poor_gps(self, db_session):
        """Test creating farm with poor GPS accuracy returns warning"""
        farm_data = FarmCreate(
            farmer_name="Jane Smith",
            farmer_id="87654321",
            phone_number="+254723456789",
            crop_type=CropType.MAIZE,
            gps_coordinates=GPSCoordinates(
                lat=Decimal("-1.286389"),
                lng=Decimal("36.817223"),
                accuracy=35.0
            )
        )
        
        result = farm_service.create_farm(farm_data, db_session)
        
        assert result.id is not None
        assert result.gps_warning is not None
        assert result.gps_warning.accuracy == 35.0
    
    def test_get_farm_by_id_exists(self, db_session):
        """Test retrieving existing farm by ID"""
        # Create a farm first
        farm_data = FarmCreate(
            farmer_name="Test Farmer",
            farmer_id="11111111",
            phone_number="+254734567890",
            crop_type=CropType.MAIZE,
            gps_coordinates=GPSCoordinates(
                lat=Decimal("-1.286389"),
                lng=Decimal("36.817223"),
                accuracy=10.0
            )
        )
        created_farm = farm_service.create_farm(farm_data, db_session)
        
        # Retrieve the farm
        retrieved_farm = farm_service.get_farm_by_id(created_farm.id, db_session)
        
        assert retrieved_farm is not None
        assert retrieved_farm.id == created_farm.id
        assert retrieved_farm.farmer_name == "Test Farmer"
    
    def test_get_farm_by_id_not_exists(self, db_session):
        """Test retrieving non-existent farm returns None"""
        from uuid import uuid4
        
        result = farm_service.get_farm_by_id(uuid4(), db_session)
        assert result is None
    
    def test_search_farms_by_farmer_id_single(self, db_session):
        """Test searching farms by farmer ID with single result"""
        farm_data = FarmCreate(
            farmer_name="Search Test",
            farmer_id="99999999",
            phone_number="+254745678901",
            crop_type=CropType.MAIZE,
            gps_coordinates=GPSCoordinates(
                lat=Decimal("-1.286389"),
                lng=Decimal("36.817223"),
                accuracy=10.0
            )
        )
        farm_service.create_farm(farm_data, db_session)
        
        results = farm_service.search_farms_by_farmer_id("99999999", db_session)
        
        assert len(results) == 1
        assert results[0].farmer_id == "99999999"
    
    def test_search_farms_by_farmer_id_multiple(self, db_session):
        """Test searching farms by farmer ID with multiple results"""
        farmer_id = "88888888"
        
        # Create multiple farms for same farmer
        for i in range(3):
            farm_data = FarmCreate(
                farmer_name=f"Multi Farm {i}",
                farmer_id=farmer_id,
                phone_number=f"+25475678901{i}",
                crop_type=CropType.MAIZE,
                gps_coordinates=GPSCoordinates(
                    lat=Decimal("-1.286389") + Decimal(i * 0.001),
                    lng=Decimal("36.817223") + Decimal(i * 0.001),
                    accuracy=10.0
                )
            )
            farm_service.create_farm(farm_data, db_session)
        
        results = farm_service.search_farms_by_farmer_id(farmer_id, db_session)
        
        assert len(results) == 3
        assert all(farm.farmer_id == farmer_id for farm in results)
    
    def test_search_farms_by_farmer_id_not_found(self, db_session):
        """Test searching for non-existent farmer ID returns empty list"""
        results = farm_service.search_farms_by_farmer_id("00000000", db_session)
        assert len(results) == 0
