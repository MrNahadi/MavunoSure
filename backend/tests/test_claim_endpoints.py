"""Integration tests for claim management endpoints"""

import pytest
import base64
from decimal import Decimal
from unittest.mock import patch, AsyncMock, MagicMock
from app.services.otp_service import otp_service
from app.models.agent import Agent
from app.models.farm import Farm


class TestClaimEndpoints:
    """Test claim API endpoints"""
    
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
    
    @pytest.fixture
    def test_farm(self, client, auth_headers):
        """Create a test farm for claim testing"""
        farm_data = {
            "farmer_name": "Test Farmer",
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
        
        return response.json()
    
    @pytest.fixture
    def sample_image_data(self):
        """Generate sample base64 encoded image data"""
        # Create a minimal valid image (1x1 pixel PNG)
        import io
        from PIL import Image
        
        img = Image.new('RGB', (100, 100), color='red')
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        return base64.b64encode(buffer.read()).decode('utf-8')
    
    def test_create_claim_success(self, client, auth_headers, test_farm, sample_image_data, db_session):
        """Test creating a claim successfully"""
        # Get agent_id from auth
        from app.models.agent import Agent
        agent = db_session.query(Agent).first()
        
        claim_data = {
            "agent_id": str(agent.id),
            "farm_id": test_farm["id"],
            "ground_truth": {
                "ml_class": "drought_stress",
                "ml_confidence": 0.85,
                "top_three_classes": [
                    ["drought_stress", 0.85],
                    ["healthy", 0.10],
                    ["northern_leaf_blight", 0.05]
                ],
                "device_tilt": 65.0,
                "device_azimuth": 180.0,
                "capture_gps_lat": -1.286389,
                "capture_gps_lng": 36.817223
            },
            "image_data": sample_image_data
        }
        
        with patch('app.services.storage_service.storage_service.upload_claim_image') as mock_upload:
            mock_upload.return_value = "https://storage.example.com/claims/test-image.jpg"
            
            response = client.post(
                "/api/v1/claims",
                json=claim_data,
                headers=auth_headers
            )
        
        assert response.status_code == 201
        data = response.json()
        assert "claim_id" in data
        assert data["status"] == "pending"
        assert "message" in data
    
    def test_create_claim_invalid_agent(self, client, auth_headers, test_farm, sample_image_data):
        """Test creating claim with invalid agent ID fails"""
        from uuid import uuid4
        
        claim_data = {
            "agent_id": str(uuid4()),
            "farm_id": test_farm["id"],
            "ground_truth": {
                "ml_class": "drought_stress",
                "ml_confidence": 0.85,
                "top_three_classes": [
                    ["drought_stress", 0.85],
                    ["healthy", 0.10],
                    ["northern_leaf_blight", 0.05]
                ],
                "device_tilt": 65.0,
                "device_azimuth": 180.0,
                "capture_gps_lat": -1.286389,
                "capture_gps_lng": 36.817223
            },
            "image_data": sample_image_data
        }
        
        response = client.post(
            "/api/v1/claims",
            json=claim_data,
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert "not found" in response.json()["detail"].lower()
    
    def test_create_claim_invalid_farm(self, client, auth_headers, sample_image_data, db_session):
        """Test creating claim with invalid farm ID fails"""
        from uuid import uuid4
        from app.models.agent import Agent
        
        agent = db_session.query(Agent).first()
        
        claim_data = {
            "agent_id": str(agent.id),
            "farm_id": str(uuid4()),
            "ground_truth": {
                "ml_class": "drought_stress",
                "ml_confidence": 0.85,
                "top_three_classes": [
                    ["drought_stress", 0.85],
                    ["healthy", 0.10],
                    ["northern_leaf_blight", 0.05]
                ],
                "device_tilt": 65.0,
                "device_azimuth": 180.0,
                "capture_gps_lat": -1.286389,
                "capture_gps_lng": 36.817223
            },
            "image_data": sample_image_data
        }
        
        response = client.post(
            "/api/v1/claims",
            json=claim_data,
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert "not found" in response.json()["detail"].lower()
    
    def test_create_claim_unauthorized(self, client, test_farm, sample_image_data):
        """Test creating claim without authentication fails"""
        from uuid import uuid4
        
        claim_data = {
            "agent_id": str(uuid4()),
            "farm_id": test_farm["id"],
            "ground_truth": {
                "ml_class": "drought_stress",
                "ml_confidence": 0.85,
                "top_three_classes": [
                    ["drought_stress", 0.85],
                    ["healthy", 0.10],
                    ["northern_leaf_blight", 0.05]
                ],
                "device_tilt": 65.0,
                "device_azimuth": 180.0,
                "capture_gps_lat": -1.286389,
                "capture_gps_lng": 36.817223
            },
            "image_data": sample_image_data
        }
        
        response = client.post("/api/v1/claims", json=claim_data)
        assert response.status_code == 403
    
    def test_get_claim_by_id_success(self, client, auth_headers, test_farm, sample_image_data, db_session):
        """Test retrieving claim by ID"""
        from app.models.agent import Agent
        
        agent = db_session.query(Agent).first()
        
        # Create a claim first
        claim_data = {
            "agent_id": str(agent.id),
            "farm_id": test_farm["id"],
            "ground_truth": {
                "ml_class": "drought_stress",
                "ml_confidence": 0.85,
                "top_three_classes": [
                    ["drought_stress", 0.85],
                    ["healthy", 0.10],
                    ["northern_leaf_blight", 0.05]
                ],
                "device_tilt": 65.0,
                "device_azimuth": 180.0,
                "capture_gps_lat": -1.286389,
                "capture_gps_lng": 36.817223
            },
            "image_data": sample_image_data
        }
        
        with patch('app.services.storage_service.storage_service.upload_claim_image') as mock_upload:
            mock_upload.return_value = "https://storage.example.com/claims/test-image.jpg"
            
            create_response = client.post(
                "/api/v1/claims",
                json=claim_data,
                headers=auth_headers
            )
        
        created_claim = create_response.json()
        claim_id = created_claim["claim_id"]
        
        # Retrieve the claim
        get_response = client.get(
            f"/api/v1/claims/{claim_id}",
            headers=auth_headers
        )
        
        assert get_response.status_code == 200
        data = get_response.json()
        assert data["id"] == claim_id
        assert data["status"] == "pending"
        assert data["ground_truth"]["ml_class"] == "drought_stress"
        assert data["ground_truth"]["ml_confidence"] == 0.85
        assert data["space_truth"] is None  # Not processed yet
        assert data["verification_result"] is None  # Not processed yet
    
    def test_get_claim_by_id_not_found(self, client, auth_headers):
        """Test retrieving non-existent claim returns 404"""
        from uuid import uuid4
        
        response = client.get(
            f"/api/v1/claims/{uuid4()}",
            headers=auth_headers
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_get_claim_unauthorized(self, client):
        """Test retrieving claim without authentication fails"""
        from uuid import uuid4
        
        response = client.get(f"/api/v1/claims/{uuid4()}")
        assert response.status_code == 403
    
    def test_list_claims_success(self, client, auth_headers, test_farm, sample_image_data, db_session):
        """Test listing claims with pagination"""
        from app.models.agent import Agent
        
        agent = db_session.query(Agent).first()
        
        # Create multiple claims
        for i in range(3):
            claim_data = {
                "agent_id": str(agent.id),
                "farm_id": test_farm["id"],
                "ground_truth": {
                    "ml_class": "drought_stress",
                    "ml_confidence": 0.85,
                    "top_three_classes": [
                        ["drought_stress", 0.85],
                        ["healthy", 0.10],
                        ["northern_leaf_blight", 0.05]
                    ],
                    "device_tilt": 65.0,
                    "device_azimuth": 180.0,
                    "capture_gps_lat": -1.286389,
                    "capture_gps_lng": 36.817223
                },
                "image_data": sample_image_data
            }
            
            with patch('app.services.storage_service.storage_service.upload_claim_image') as mock_upload:
                mock_upload.return_value = f"https://storage.example.com/claims/test-image-{i}.jpg"
                
                client.post(
                    "/api/v1/claims",
                    json=claim_data,
                    headers=auth_headers
                )
        
        # List claims
        response = client.get(
            "/api/v1/claims",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "claims" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "total_pages" in data
        assert data["total"] == 3
        assert len(data["claims"]) == 3
    
    def test_list_claims_filter_by_agent(self, client, auth_headers, test_farm, sample_image_data, db_session):
        """Test filtering claims by agent ID"""
        from app.models.agent import Agent
        
        agent = db_session.query(Agent).first()
        
        # Create claims
        claim_data = {
            "agent_id": str(agent.id),
            "farm_id": test_farm["id"],
            "ground_truth": {
                "ml_class": "drought_stress",
                "ml_confidence": 0.85,
                "top_three_classes": [
                    ["drought_stress", 0.85],
                    ["healthy", 0.10],
                    ["northern_leaf_blight", 0.05]
                ],
                "device_tilt": 65.0,
                "device_azimuth": 180.0,
                "capture_gps_lat": -1.286389,
                "capture_gps_lng": 36.817223
            },
            "image_data": sample_image_data
        }
        
        with patch('app.services.storage_service.storage_service.upload_claim_image') as mock_upload:
            mock_upload.return_value = "https://storage.example.com/claims/test-image.jpg"
            
            client.post(
                "/api/v1/claims",
                json=claim_data,
                headers=auth_headers
            )
        
        # Filter by agent
        response = client.get(
            f"/api/v1/claims?agentId={agent.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert all(claim["agent_id"] == str(agent.id) for claim in data["claims"])
    
    def test_list_claims_filter_by_status(self, client, auth_headers, test_farm, sample_image_data, db_session):
        """Test filtering claims by status"""
        from app.models.agent import Agent
        
        agent = db_session.query(Agent).first()
        
        # Create claim
        claim_data = {
            "agent_id": str(agent.id),
            "farm_id": test_farm["id"],
            "ground_truth": {
                "ml_class": "drought_stress",
                "ml_confidence": 0.85,
                "top_three_classes": [
                    ["drought_stress", 0.85],
                    ["healthy", 0.10],
                    ["northern_leaf_blight", 0.05]
                ],
                "device_tilt": 65.0,
                "device_azimuth": 180.0,
                "capture_gps_lat": -1.286389,
                "capture_gps_lng": 36.817223
            },
            "image_data": sample_image_data
        }
        
        with patch('app.services.storage_service.storage_service.upload_claim_image') as mock_upload:
            mock_upload.return_value = "https://storage.example.com/claims/test-image.jpg"
            
            client.post(
                "/api/v1/claims",
                json=claim_data,
                headers=auth_headers
            )
        
        # Filter by status
        response = client.get(
            "/api/v1/claims?status=pending",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert all(claim["status"] == "pending" for claim in data["claims"])
    
    def test_list_claims_invalid_status(self, client, auth_headers):
        """Test filtering with invalid status returns error"""
        response = client.get(
            "/api/v1/claims?status=invalid_status",
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert "invalid status" in response.json()["detail"].lower()
    
    def test_list_claims_pagination(self, client, auth_headers, test_farm, sample_image_data, db_session):
        """Test claims list pagination"""
        from app.models.agent import Agent
        
        agent = db_session.query(Agent).first()
        
        # Create 5 claims
        for i in range(5):
            claim_data = {
                "agent_id": str(agent.id),
                "farm_id": test_farm["id"],
                "ground_truth": {
                    "ml_class": "drought_stress",
                    "ml_confidence": 0.85,
                    "top_three_classes": [
                        ["drought_stress", 0.85],
                        ["healthy", 0.10],
                        ["northern_leaf_blight", 0.05]
                    ],
                    "device_tilt": 65.0,
                    "device_azimuth": 180.0,
                    "capture_gps_lat": -1.286389,
                    "capture_gps_lng": 36.817223
                },
                "image_data": sample_image_data
            }
            
            with patch('app.services.storage_service.storage_service.upload_claim_image') as mock_upload:
                mock_upload.return_value = f"https://storage.example.com/claims/test-image-{i}.jpg"
                
                client.post(
                    "/api/v1/claims",
                    json=claim_data,
                    headers=auth_headers
                )
        
        # Get first page with 2 items
        response = client.get(
            "/api/v1/claims?page=1&page_size=2",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["claims"]) == 2
        assert data["page"] == 1
        assert data["page_size"] == 2
        assert data["total_pages"] == 3
        
        # Get second page
        response2 = client.get(
            "/api/v1/claims?page=2&page_size=2",
            headers=auth_headers
        )
        
        assert response2.status_code == 200
        data2 = response2.json()
        assert len(data2["claims"]) == 2
        assert data2["page"] == 2
    
    def test_list_claims_unauthorized(self, client):
        """Test listing claims without authentication fails"""
        response = client.get("/api/v1/claims")
        assert response.status_code == 403