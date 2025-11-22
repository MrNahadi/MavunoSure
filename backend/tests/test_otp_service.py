"""Unit tests for OTP service"""

import pytest
from app.services.otp_service import OTPService


class TestOTPService:
    """Test OTP generation and validation"""
    
    def test_generate_otp(self):
        """Test OTP generation"""
        service = OTPService()
        otp = service.generate_otp()
        
        assert len(otp) == 6
        assert otp.isdigit()
    
    def test_store_and_verify_otp(self, redis_client):
        """Test storing and verifying OTP"""
        service = OTPService()
        phone_number = "+254712345678"
        otp = "123456"
        
        # Store OTP
        service.store_otp(phone_number, otp)
        
        # Verify correct OTP
        assert service.verify_otp(phone_number, otp) is True
    
    def test_verify_invalid_otp(self, redis_client):
        """Test verifying invalid OTP"""
        service = OTPService()
        phone_number = "+254712345678"
        otp = "123456"
        
        # Store OTP
        service.store_otp(phone_number, otp)
        
        # Verify incorrect OTP
        assert service.verify_otp(phone_number, "654321") is False
    
    def test_verify_expired_otp(self, redis_client):
        """Test verifying non-existent OTP"""
        service = OTPService()
        phone_number = "+254712345678"
        
        # Try to verify OTP that was never stored
        assert service.verify_otp(phone_number, "123456") is False
    
    def test_otp_deleted_after_verification(self, redis_client):
        """Test that OTP is deleted after successful verification"""
        service = OTPService()
        phone_number = "+254712345678"
        otp = "123456"
        
        # Store OTP
        service.store_otp(phone_number, otp)
        
        # Verify OTP (should succeed and delete)
        assert service.verify_otp(phone_number, otp) is True
        
        # Try to verify again (should fail)
        assert service.verify_otp(phone_number, otp) is False
