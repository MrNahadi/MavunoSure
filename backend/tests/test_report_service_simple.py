"""Simple unit tests for PDF report generation service without Redis dependency"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from decimal import Decimal
from io import BytesIO
from PIL import Image

from app.services.report_service import report_service
from app.models.claim import Claim
from app.models.farm import Farm


class TestReportServiceSimple:
    """Simple unit tests for PDF generation without full integration"""
    
    def test_generate_pdf_content(self):
        """Test PDF content generation with mock data"""
        # Create mock claim
        claim = Mock(spec=Claim)
        claim.id = "test-claim-id"
        claim.status = "auto_approved"
        claim.created_at = datetime.now()
        claim.image_url = "/uploads/claims/test.jpg"
        claim.ml_class = "drought_stress"
        claim.ml_confidence = 0.85
        claim.top_three_classes = [
            ["drought_stress", 0.85],
            ["healthy", 0.10],
            ["northern_leaf_blight", 0.05]
        ]
        claim.device_tilt = 65.0
        claim.device_azimuth = 180.0
        claim.capture_gps_lat = Decimal("-1.286389")
        claim.capture_gps_lng = Decimal("36.817223")
        claim.ndmi_value = -0.25
        claim.ndmi_14day_avg = -0.15
        claim.satellite_verdict = "severe_stress"
        claim.observation_date = datetime.now()
        claim.cloud_cover_pct = 15.0
        claim.weighted_score = 0.92
        claim.verdict_explanation = "Double confirmation: Visual drought stress matches severe satellite moisture deficit"
        claim.ground_truth_confidence = 0.85
        claim.space_truth_confidence = 0.9
        claim.payout_amount = Decimal("5000.00")
        claim.payout_status = "completed"
        claim.payout_reference = "PAY-12345"
        
        # Create mock farm
        farm = Mock(spec=Farm)
        farm.farmer_name = "John Doe"
        farm.farmer_id = "12345678"
        farm.phone_number = "+254712345678"
        farm.crop_type = "maize"
        farm.gps_lat = Decimal("-1.286389")
        farm.gps_lng = Decimal("36.817223")
        farm.registered_at = datetime.now()
        
        # Mock image loading to avoid file I/O
        with patch.object(report_service, '_add_claim_image') as mock_image:
            from reportlab.platypus import Paragraph
            from reportlab.lib.styles import getSampleStyleSheet
            styles = getSampleStyleSheet()
            mock_image.return_value = Paragraph("[Test Image]", styles['Normal'])
            
            # Generate PDF
            pdf_bytes = report_service._generate_pdf_content(claim, farm)
            
            # Verify PDF was generated
            assert pdf_bytes is not None
            assert isinstance(pdf_bytes, bytes)
            assert len(pdf_bytes) > 1000  # PDF should be reasonably sized
            
            # Verify PDF header
            assert pdf_bytes.startswith(b'%PDF')
    
    def test_generate_pdf_with_minimal_data(self):
        """Test PDF generation with minimal claim data (no Space Truth)"""
        # Create mock claim with minimal data
        claim = Mock(spec=Claim)
        claim.id = "test-claim-id-2"
        claim.status = "pending"
        claim.created_at = datetime.now()
        claim.image_url = "/uploads/claims/test2.jpg"
        claim.ml_class = "healthy"
        claim.ml_confidence = 0.75
        claim.top_three_classes = [
            ["healthy", 0.75],
            ["drought_stress", 0.15],
            ["northern_leaf_blight", 0.10]
        ]
        claim.device_tilt = 55.0
        claim.device_azimuth = 90.0
        claim.capture_gps_lat = Decimal("-1.286389")
        claim.capture_gps_lng = Decimal("36.817223")
        # No Space Truth data
        claim.ndmi_value = None
        claim.ndmi_14day_avg = None
        claim.satellite_verdict = None
        claim.observation_date = None
        claim.cloud_cover_pct = None
        # No Verification Result
        claim.weighted_score = None
        claim.verdict_explanation = None
        claim.ground_truth_confidence = None
        claim.space_truth_confidence = None
        # No Payment
        claim.payout_amount = None
        claim.payout_status = None
        claim.payout_reference = None
        
        # Create mock farm
        farm = Mock(spec=Farm)
        farm.farmer_name = "Jane Smith"
        farm.farmer_id = "87654321"
        farm.phone_number = "+254723456789"
        farm.crop_type = "wheat"
        farm.gps_lat = Decimal("-1.286389")
        farm.gps_lng = Decimal("36.817223")
        farm.registered_at = datetime.now()
        
        # Mock image loading
        with patch.object(report_service, '_add_claim_image') as mock_image:
            from reportlab.platypus import Paragraph
            from reportlab.lib.styles import getSampleStyleSheet
            styles = getSampleStyleSheet()
            mock_image.return_value = Paragraph("[Test Image]", styles['Normal'])
            
            # Generate PDF
            pdf_bytes = report_service._generate_pdf_content(claim, farm)
            
            # Verify PDF was generated
            assert pdf_bytes is not None
            assert isinstance(pdf_bytes, bytes)
            assert len(pdf_bytes) > 500
            assert pdf_bytes.startswith(b'%PDF')
    
    def test_ndmi_chart_creation(self):
        """Test NDMI chart generation"""
        current_ndmi = -0.25
        avg_ndmi = -0.15
        
        drawing = report_service._create_ndmi_chart(current_ndmi, avg_ndmi)
        
        # Verify drawing was created
        assert drawing is not None
        assert drawing.width == 400
        assert drawing.height == 200
    
    def test_upload_locally(self):
        """Test local PDF storage"""
        from pathlib import Path
        
        # Create test PDF bytes
        test_pdf = b'%PDF-1.4\ntest content'
        filename = "reports/test-claim/test.pdf"
        
        # Upload locally
        url = report_service._upload_locally(test_pdf, filename)
        
        # Verify URL format
        assert url.startswith("/uploads/")
        assert url.endswith(".pdf")
        
        # Verify file was created
        file_path = Path("uploads") / filename
        assert file_path.exists()
        
        # Clean up
        file_path.unlink()
        file_path.parent.rmdir()
        file_path.parent.parent.rmdir()
