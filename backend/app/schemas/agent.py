"""Agent Pydantic schemas"""

from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from uuid import UUID
import re


class AgentBase(BaseModel):
    """Base agent schema"""
    phone_number: str = Field(..., description="Agent phone number in E.164 format")
    
    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, v: str) -> str:
        """Validate phone number format"""
        # Remove spaces and special characters
        cleaned = re.sub(r'[^\d+]', '', v)
        
        # Check if it's a valid format (starts with + and has 10-15 digits)
        if not re.match(r'^\+?[1-9]\d{9,14}$', cleaned):
            raise ValueError("Invalid phone number format. Must be in E.164 format (e.g., +254712345678)")
        
        # Ensure it starts with +
        if not cleaned.startswith('+'):
            cleaned = '+' + cleaned
            
        return cleaned


class AgentCreate(AgentBase):
    """Schema for creating an agent"""
    name: str | None = Field(None, description="Agent name")


class AgentUpdate(BaseModel):
    """Schema for updating an agent"""
    name: str | None = Field(None, description="Agent name")
    phone_number: str | None = Field(None, description="Agent phone number")


class AgentInDB(AgentBase):
    """Schema for agent in database"""
    id: UUID
    name: str | None
    created_at: datetime
    last_login: datetime | None
    
    class Config:
        from_attributes = True


class AgentResponse(AgentInDB):
    """Schema for agent response"""
    pass
