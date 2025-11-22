"""Integration tests for farm management endpoints"""

import pytest
from decimal import Decimal
from unittest.mock import patch, AsyncMock
from app.services.otp_service import otp_service


class TestFarmEndpoints:
    """Test farm API endpoints"""
    
    @pytest.fixture
    def auth_headers(self, client, redis_client):
        """Create authenticated agent and return auth headers"""
        phone_number = "+254712345678"
        otp = "123456"
        
        # Store OTP and verify to get token
        otp_service.store_otp(phone_number, otp)
        
        with patch('app.services.sms_service.sms_service.send_otp', new_callable=AsyncMock):
            response = client.post(
                "/api/v1/auth/verify-otp",
                json={
                    "phone_number": phone_number,
                    "otp": otp
                }
            )
            
            tokens = response.json()
            return {"Authorization": f"Bearer {tokens['access_token']}"}
    
    def test_create_farm_success(self, client, auth_headers):
        """Test creating a farm successfully"""
        farm_data = {
            "farmer_name": "John Doe",
            "farmer_id": "12345678",
            "phone_number": "+254712345678",
            "crop_type": "maize",
            "gps_coordinates": {
                "lat": -1.286389,
                "lng": 36.817223,
                "accuracy": 8.5
            }
        }
        
        response = client.post(
            "/api/v1/farms",
            json=farm_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["farmer_name"] == "John Doe"
        assert data["farmer_id"] == "12345678"
        assert data["crop_type"] == "maize"
        assert data["gps_coordinates"]["accuracy"] == 8.5
        assert data["gps_warning"] is None
        assert "id" in data
        assert "registered_at" in data
    
    def test_create_farm_with_gps_warning(self, client, auth_headers):
        """Test creating farm with poor GPS accuracy returns warning"""
        farm_data = {
            "farmer_name": "Jane Smith",
            "farmer_id": "87654321",
            "phone_number": "+254723456789",
            "crop_type": "maize",
            "gps_coordinates": {
                "lat": -1.286389,
                "lng": 36.817223,
                "accuracy": 35.0
            }
        }
        
        response = client.post(
            "/api/v1/farms",
            json=farm_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["gps_warning"] is not None
        assert data["gps_warning"]["accuracy"] == 35.0
        assert data["gps_warning"]["threshold"] == 20.0
        assert "poor" in data["gps_warning"]["warning"].lower()
    
    def test_create_farm_unauthorized(self, client):
        """Test creating farm without authentication fails"""
        farm_data = {
            "farmer_name": "Test Farmer",
            "farmer_id": "11111111",
            "phone_number": "+254734567890",
            "crop_type": "maize",
            "gps_coordinates": {
                "lat": -1.286389,
                "lng": 36.817223,
                "accuracy": 10.0
            }
        }
        
        response = client.post("/api/v1/farms", json=farm_data)
        assert response.status_code == 403
    
    def test_create_farm_invalid_gps_lat(self, client, auth_headers):
        """Test creating farm with invalid latitude"""
        farm_data = {
            "farmer_name": "Test Farmer",
            "farmer_id": "11111111",
            "phone_number": "+254734567890",
            "crop_type": "maize",
            "gps_coordinates": {
                "lat": 95.0,  # Invalid: > 90
                "lng": 36.817223,
                "accuracy": 10.0
            }
        }
        
        response = client.post(
            "/api/v1/farms",
            json=farm_data,
            headers=auth_headers
        )
        assert response.status_code == 422
    
    def test_create_farm_invalid_gps_lng(self, client, auth_headers):
        """Test creating farm with invalid longitude"""
        farm_data = {
            "farmer_name": "Test Farmer",
            "farmer_id": "11111111",
            "phone_number": "+254734567890",
            "crop_type": "maize",
            "gps_coordinates": {
                "lat": -1.286389,
                "lng": 185.0,  # Invalid: > 180
                "accuracy": 10.0
            }
        }
        
        response = client.post(
            "/api/v1/farms",
            json=farm_data,
            headers=auth_headers
        )
        assert response.status_code == 422
    
    def test_get_farm_by_id_success(self, client, auth_headers):
        """Test retrieving farm by ID"""
        # Create a farm first
        farm_data = {
            "farmer_name": "Get Test",
            "farmer_id": "22222222",
            "phone_number": "+254745678901",
            "crop_type": "maize",
            "gps_coordinates": {
                "lat": -1.286389,
                "lng": 36.817223,
                "accuracy": 10.0
            }
        }
        
        create_response = client.post(
            "/api/v1/farms",
            json=farm_data,
            headers=auth_headers
        )
        created_farm = create_response.json()
        farm_id = created_farm["id"]
        
        # Retrieve the farm
        get_response = client.get(
            f"/api/v1/farms/{farm_id}",
            headers=auth_headers
        )
        
        assert get_response.status_code == 200
        data = get_response.json()
        assert data["id"] == farm_id
        assert data["farmer_name"] == "Get Test"
        assert data["farmer_id"] == "22222222"
    
    def test_get_farm_by_id_not_found(self, client, auth_headers):
        """Test retrieving non-existent farm returns 404"""
        from uuid import uuid4
        
        response = client.get(
            f"/api/v1/farms/{uuid4()}",
            headers=auth_headers
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_get_farm_unauthorized(self, client):
        """Test retrieving farm without authentication fails"""
        from uuid import uuid4
        
        response = client.get(f"/api/v1/farms/{uuid4()}")
        assert response.status_code == 403
    
    def test_search_farms_by_farmer_id_success(self, client, auth_headers):
        """Test searching farms by farmer ID"""
        farmer_id = "33333333"
        
        # Create multiple farms for same farmer
        for i in range(2):
            farm_data = {
                "farmer_name": f"Search Test {i}",
                "farmer_id": farmer_id,
                "phone_number": f"+25475678901{i}",
                "crop_type": "maize",
                "gps_coordinates": {
                    "lat": -1.286389 + (i * 0.001),
                    "lng": 36.817223 + (i * 0.001),
                    "accuracy": 10.0
                }
            }
            client.post(
                "/api/v1/farms",
                json=farm_data,
                headers=auth_headers
            )
        
        # Search for farms
        response = client.get(
            f"/api/v1/farms/search?farmerId={farmer_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all(farm["farmer_id"] == farmer_id for farm in data)
    
    def test_search_farms_not_found(self, client, auth_headers):
        """Test searching for non-existent farmer ID returns empty list"""
        response = client.get(
            "/api/v1/farms/search?farmerId=00000000",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0
    
    def test_search_farms_unauthorized(self, client):
        """Test searching farms without authentication fails"""
        response = client.get("/api/v1/farms/search?farmerId=12345678")
        assert response.status_code == 403
    
    def test_search_farms_missing_query_param(self, client, auth_headers):
        """Test searching farms without farmerId parameter fails"""
        response = client.get(
            "/api/v1/farms/search",
            headers=auth_headers
        )
        assert response.status_code == 422
