"""Authentication Pydantic schemas"""

from pydantic import BaseModel, Field, field_validator
import re


class SendOTPRequest(BaseModel):
    """Schema for sending OTP"""
    phone_number: str = Field(..., description="Phone number in E.164 format")
    
    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, v: str) -> str:
        """Validate phone number format"""
        cleaned = re.sub(r'[^\d+]', '', v)
        if not re.match(r'^\+?[1-9]\d{9,14}$', cleaned):
            raise ValueError("Invalid phone number format")
        if not cleaned.startswith('+'):
            cleaned = '+' + cleaned
        return cleaned


class SendOTPResponse(BaseModel):
    """Schema for OTP send response"""
    message: str
    phone_number: str


class VerifyOTPRequest(BaseModel):
    """Schema for verifying OTP"""
    phone_number: str = Field(..., description="Phone number in E.164 format")
    otp: str = Field(..., min_length=4, max_length=6, description="OTP code")
    
    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, v: str) -> str:
        """Validate phone number format"""
        cleaned = re.sub(r'[^\d+]', '', v)
        if not re.match(r'^\+?[1-9]\d{9,14}$', cleaned):
            raise ValueError("Invalid phone number format")
        if not cleaned.startswith('+'):
            cleaned = '+' + cleaned
        return cleaned


class TokenResponse(BaseModel):
    """Schema for token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request"""
    refresh_token: str = Field(..., description="Refresh token")


class TokenPayload(BaseModel):
    """Schema for JWT token payload"""
    sub: str  # subject (agent_id)
    exp: int  # expiration time
    type: str  # token type (access or refresh)
