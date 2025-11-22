"""Authentication service"""

from sqlalchemy.orm import Session
from datetime import datetime
from uuid import UUID
from app.models.agent import Agent
from app.services.otp_service import otp_service
from app.services.sms_service import sms_service
from app.core.security import create_access_token, create_refresh_token, verify_token
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class AuthService:
    """Service for authentication operations"""
    
    async def send_otp(self, phone_number: str, db: Session) -> dict:
        """Generate and send OTP to phone number"""
        # Generate OTP
        otp = otp_service.generate_otp()
        
        # Store OTP in Redis
        otp_service.store_otp(phone_number, otp)
        
        # Send OTP via SMS
        sms_sent = await sms_service.send_otp(phone_number, otp)
        
        if not sms_sent:
            logger.warning(f"Failed to send SMS to {phone_number}, but OTP stored for testing")
        
        # For development/testing, log the OTP
        if settings.DEBUG:
            logger.info(f"OTP for {phone_number}: {otp}")
        
        return {
            "message": "OTP sent successfully",
            "phone_number": phone_number
        }
    
    async def verify_otp(self, phone_number: str, otp: str, db: Session) -> dict:
        """Verify OTP and return tokens"""
        # Verify OTP
        is_valid = otp_service.verify_otp(phone_number, otp)
        
        if not is_valid:
            raise ValueError("Invalid or expired OTP")
        
        # Get or create agent
        agent = db.query(Agent).filter(Agent.phone_number == phone_number).first()
        
        if not agent:
            # Create new agent
            agent = Agent(phone_number=phone_number)
            db.add(agent)
            db.commit()
            db.refresh(agent)
        
        # Update last login
        agent.last_login = datetime.utcnow()
        db.commit()
        
        # Generate tokens
        access_token = create_access_token(subject=str(agent.id))
        refresh_token = create_refresh_token(subject=str(agent.id))
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
    
    async def refresh_access_token(self, refresh_token: str, db: Session) -> dict:
        """Generate new access token from refresh token"""
        # Verify refresh token
        agent_id = verify_token(refresh_token, token_type="refresh")
        
        if not agent_id:
            raise ValueError("Invalid or expired refresh token")
        
        # Verify agent exists
        agent = db.query(Agent).filter(Agent.id == UUID(agent_id)).first()
        
        if not agent:
            raise ValueError("Agent not found")
        
        # Generate new access token
        access_token = create_access_token(subject=str(agent.id))
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
    
    def get_current_agent(self, token: str, db: Session) -> Agent:
        """Get current authenticated agent from token"""
        # Verify access token
        agent_id = verify_token(token, token_type="access")
        
        if not agent_id:
            raise ValueError("Invalid or expired token")
        
        # Get agent
        agent = db.query(Agent).filter(Agent.id == UUID(agent_id)).first()
        
        if not agent:
            raise ValueError("Agent not found")
        
        return agent


# Singleton instance
auth_service = AuthService()
