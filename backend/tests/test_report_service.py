"""Integration tests for PDF report generation service"""

import pytest
import base64
from unittest.mock import patch, MagicMock, Mock
from io import BytesIO
from PIL import Image
from PyPDF2 import PdfReader

from app.services.otp_service import otp_service
from app.models.agent import Agent
from app.models.farm import Farm
from app.models.claim import Claim
from app.schemas.claim import ClaimStatus


class TestReportService:
    """Test PDF report generation service"""
    
    @pytest.fixture
    def auth_headers(self, client, db_session):
        """Create authenticated agent and return auth headers"""
        phone_number = "+254712345678"
        otp = "123456"
        
        # Mock Redis client
        mock_redis = Mock()
        mock_redis.setex = Mock()
        mock_redis.get = Mock(return_value=otp)
        mock_redis.delete = Mock()
        
        from unittest.mock import AsyncMock
        with patch('app.services.otp_service.otp_service.redis_client', mock_redis), \
             patch('app.services.sms_service.sms_service.send_otp', new_callable=AsyncMock):
            
            # Store OTP
            otp_service.store_otp(phone_number, otp)
            
            # Verify OTP to get token
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
        """Create a test farm"""
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
        
        return response.json()
    
    @pytest.fixture
    def sample_image_data(self):
        """Generate sample base64 encoded image data"""
        img = Image.new('RGB', (100, 100), color='green')
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        return base64.b64encode(buffer.read()).decode('utf-8')
    
    @pytest.fixture
    def complete_claim(self, client, auth_headers, test_farm, sample_image_data, db_session):
        """Create a complete claim with all data populated"""
        from app.models.agent import Agent
        from datetime import datetime
        from pathlib import Path
        
        # Create uploads directory for test images
        upload_dir = Path("uploads/claims")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
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
            mock_upload.return_value = "/uploads/claims/test-image.jpg"
            
            create_response = client.post(
                "/api/v1/claims",
                json=claim_data,
                headers=auth_headers
            )
        
        created_claim = create_response.json()
        claim_id = created_claim["claim_id"]
        
        # Update claim with Space Truth and Verification Result
        claim = db_session.query(Claim).filter(Claim.id == claim_id).first()
        claim.ndmi_value = -0.25
        claim.ndmi_14day_avg = -0.15
        claim.satellite_verdict = "severe_stress"
        claim.observation_date = datetime.now()
        claim.cloud_cover_pct = 15.0
        claim.weighted_score = 0.92
        claim.status = ClaimStatus.AUTO_APPROVED.value
        claim.verdict_explanation = "Double confirmation: Visual drought stress matches severe satellite moisture deficit"
        claim.ground_truth_confidence = 0.85
        claim.space_truth_confidence = 0.9
        claim.payout_amount = 5000.00
        claim.payout_status = "completed"
        claim.payout_reference = "PAY-12345"
        
        db_session.commit()
        
        return claim_id
    
    def test_generate_pdf_report_success(self, client, auth_headers, complete_claim):
        """Test generating PDF report for a complete claim"""
        response = client.get(
            f"/api/v1/reports/{complete_claim}/pdf",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "claim_id" in data
        assert "pdf_url" in data
        assert "message" in data
        assert "expires_in_days" in data
        assert data["claim_id"] == str(complete_claim)
        assert data["expires_in_days"] == 7
        assert "PDF report generated successfully" in data["message"]
        
        # Verify PDF URL is valid
        assert data["pdf_url"].startswith("/uploads/reports/")
        assert data["pdf_url"].endswith(".pdf")
    
    def test_generate_pdf_report_claim_not_found(self, client, auth_headers):
        """Test generating PDF for non-existent claim returns 404"""
        from uuid import uuid4
        
        response = client.get(
            f"/api/v1/reports/{uuid4()}/pdf",
            headers=auth_headers
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_generate_pdf_report_unauthorized(self, client, complete_claim):
        """Test generating PDF without authentication fails"""
        response = client.get(f"/api/v1/reports/{complete_claim}/pdf")
        assert response.status_code == 403
    
    def test_pdf_contains_required_sections(self, client, auth_headers, complete_claim, db_session):
        """Test that generated PDF contains all required sections"""
        # Generate PDF
        response = client.get(
            f"/api/v1/reports/{complete_claim}/pdf",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        pdf_url = data["pdf_url"]
        
        # Read the generated PDF file
        pdf_path = pdf_url.replace("/uploads/", "uploads/")
        
        try:
            with open(pdf_path, 'rb') as f:
                pdf_reader = PdfReader(f)
                
                # Extract text from all pages
                pdf_text = ""
                for page in pdf_reader.pages:
                    pdf_text += page.extract_text()
                
                # Verify required sections are present
                assert "MavunoSure Claim Verification Report" in pdf_text
                assert "Farmer Information" in pdf_text
                assert "Ground Truth Assessment" in pdf_text
                assert "Space Truth Assessment" in pdf_text
                assert "Final Verification Result" in pdf_text
                assert "Payment Information" in pdf_text
                
                # Verify farmer details
                assert "John Doe" in pdf_text
                assert "12345678" in pdf_text
                
                # Verify Ground Truth data
                assert "Drought Stress" in pdf_text or "drought" in pdf_text.lower()
                assert "85" in pdf_text  # Confidence score
                
                # Verify Space Truth data
                assert "NDMI" in pdf_text
                assert "severe" in pdf_text.lower()
                
                # Verify Final Verdict
                assert "0.92" in pdf_text  # Weighted score
                assert "AUTO APPROVED" in pdf_text or "auto_approved" in pdf_text.lower()
                
                # Verify Payment info
                assert "5000" in pdf_text or "5,000" in pdf_text
                assert "PAY-12345" in pdf_text
                
        except FileNotFoundError:
            pytest.fail(f"PDF file not found at {pdf_path}")
    
    def test_pdf_with_minimal_claim_data(self, client, auth_headers, test_farm, sample_image_data, db_session):
        """Test PDF generation with minimal claim data (no Space Truth or Verification Result)"""
        from app.models.agent import Agent
        
        agent = db_session.query(Agent).first()
        
        # Create minimal claim
        claim_data = {
            "agent_id": str(agent.id),
            "farm_id": test_farm["id"],
            "ground_truth": {
                "ml_class": "healthy",
                "ml_confidence": 0.75,
                "top_three_classes": [
                    ["healthy", 0.75],
                    ["drought_stress", 0.15],
                    ["northern_leaf_blight", 0.10]
                ],
                "device_tilt": 55.0,
                "device_azimuth": 90.0,
                "capture_gps_lat": -1.286389,
                "capture_gps_lng": 36.817223
            },
            "image_data": sample_image_data
        }
        
        with patch('app.services.storage_service.storage_service.upload_claim_image') as mock_upload:
            mock_upload.return_value = "/uploads/claims/test-image-minimal.jpg"
            
            create_response = client.post(
                "/api/v1/claims",
                json=claim_data,
                headers=auth_headers
            )
        
        created_claim = create_response.json()
        claim_id = created_claim["claim_id"]
        
        # Generate PDF
        response = client.get(
            f"/api/v1/reports/{claim_id}/pdf",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "pdf_url" in data
        
        # Verify PDF was created
        pdf_path = data["pdf_url"].replace("/uploads/", "uploads/")
        
        try:
            with open(pdf_path, 'rb') as f:
                pdf_reader = PdfReader(f)
                pdf_text = ""
                for page in pdf_reader.pages:
                    pdf_text += page.extract_text()
                
                # Should have basic sections
                assert "Farmer Information" in pdf_text
                assert "Ground Truth Assessment" in pdf_text
                
                # Should NOT have Space Truth or Final Verdict sections
                # (or they should be minimal/empty)
                assert "Healthy" in pdf_text or "healthy" in pdf_text.lower()
                
        except FileNotFoundError:
            pytest.fail(f"PDF file not found at {pdf_path}")
