"""Integration tests for authentication endpoints"""

import pytest
from unittest.mock import patch, AsyncMock
from app.services.otp_service import otp_service


class TestAuthEndpoints:
    """Test authentication API endpoints"""
    
    @pytest.mark.asyncio
    async def test_send_otp_success(self, client, redis_client):
        """Test sending OTP successfully"""
        phone_number = "+254712345678"
        
        with patch('app.services.sms_service.sms_service.send_otp', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = True
            
            response = client.post(
                "/api/v1/auth/send-otp",
                json={"phone_number": phone_number}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "OTP sent successfully"
            assert data["phone_number"] == phone_number
            
            # Verify OTP was stored in Redis
            stored_otp = redis_client.get(f"otp:{phone_number}")
            assert stored_otp is not None
            assert len(stored_otp) == 6
    
    def test_send_otp_invalid_phone(self, client):
        """Test sending OTP with invalid phone number"""
        response = client.post(
            "/api/v1/auth/send-otp",
            json={"phone_number": "invalid"}
        )
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_verify_otp_success(self, client, db_session, redis_client):
        """Test verifying OTP successfully"""
        phone_number = "+254712345678"
        otp = "123456"
        
        # Store OTP
        otp_service.store_otp(phone_number, otp)
        
        with patch('app.services.sms_service.sms_service.send_otp', new_callable=AsyncMock):
            response = client.post(
                "/api/v1/auth/verify-otp",
                json={
                    "phone_number": phone_number,
                    "otp": otp
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert "refresh_token" in data
            assert data["token_type"] == "bearer"
            assert "expires_in" in data
    
    def test_verify_otp_invalid(self, client, redis_client):
        """Test verifying invalid OTP"""
        phone_number = "+254712345678"
        
        response = client.post(
            "/api/v1/auth/verify-otp",
            json={
                "phone_number": phone_number,
                "otp": "999999"
            }
        )
        
        assert response.status_code == 401
        assert "Invalid or expired OTP" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_verify_otp_creates_agent(self, client, db_session, redis_client):
        """Test that verifying OTP creates a new agent"""
        phone_number = "+254712345678"
        otp = "123456"
        
        # Store OTP
        otp_service.store_otp(phone_number, otp)
        
        with patch('app.services.sms_service.sms_service.send_otp', new_callable=AsyncMock):
            response = client.post(
                "/api/v1/auth/verify-otp",
                json={
                    "phone_number": phone_number,
                    "otp": otp
                }
            )
            
            assert response.status_code == 200
            
            # Verify agent was created in database
            from app.models.agent import Agent
            agent = db_session.query(Agent).filter(Agent.phone_number == phone_number).first()
            assert agent is not None
            assert agent.phone_number == phone_number
            assert agent.last_login is not None
    
    @pytest.mark.asyncio
    async def test_refresh_token_success(self, client, db_session, redis_client):
        """Test refreshing access token"""
        phone_number = "+254712345678"
        otp = "123456"
        
        # Store OTP and verify to get tokens
        otp_service.store_otp(phone_number, otp)
        
        with patch('app.services.sms_service.sms_service.send_otp', new_callable=AsyncMock):
            verify_response = client.post(
                "/api/v1/auth/verify-otp",
                json={
                    "phone_number": phone_number,
                    "otp": otp
                }
            )
            
            tokens = verify_response.json()
            refresh_token = tokens["refresh_token"]
            
            # Use refresh token to get new access token
            refresh_response = client.post(
                "/api/v1/auth/refresh-token",
                json={"refresh_token": refresh_token}
            )
            
            assert refresh_response.status_code == 200
            data = refresh_response.json()
            assert "access_token" in data
            assert data["token_type"] == "bearer"
    
    def test_refresh_token_invalid(self, client):
        """Test refreshing with invalid token"""
        response = client.post(
            "/api/v1/auth/refresh-token",
            json={"refresh_token": "invalid_token"}
        )
        
        assert response.status_code == 401
