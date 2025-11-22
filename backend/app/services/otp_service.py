"""OTP generation and validation service"""

import random
import string
from datetime import datetime, timedelta
from typing import Dict
import redis
from app.config import settings


class OTPService:
    """Service for managing OTP generation and validation"""
    
    def __init__(self):
        """Initialize OTP service with Redis connection"""
        self.redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
        self.otp_expiry_minutes = 5
        self.otp_length = 6
    
    def generate_otp(self) -> str:
        """Generate a random 6-digit OTP"""
        return ''.join(random.choices(string.digits, k=self.otp_length))
    
    def store_otp(self, phone_number: str, otp: str) -> None:
        """Store OTP in Redis with expiration"""
        key = f"otp:{phone_number}"
        # Store OTP with 5-minute expiration
        self.redis_client.setex(key, timedelta(minutes=self.otp_expiry_minutes), otp)
    
    def verify_otp(self, phone_number: str, otp: str) -> bool:
        """Verify OTP against stored value"""
        key = f"otp:{phone_number}"
        stored_otp = self.redis_client.get(key)
        
        if stored_otp is None:
            return False
        
        if stored_otp == otp:
            # Delete OTP after successful verification
            self.redis_client.delete(key)
            return True
        
        return False
    
    def delete_otp(self, phone_number: str) -> None:
        """Delete OTP from Redis"""
        key = f"otp:{phone_number}"
        self.redis_client.delete(key)


# Singleton instance
otp_service = OTPService()
