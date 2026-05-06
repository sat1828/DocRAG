"""
Authentication schemas for request/response validation.
"""
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime
import uuid


class UserCreate(BaseModel):
    """Schema for user registration."""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    
    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123!"
            }
        }
    )


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str


class Token(BaseModel):
    """JWT token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Decoded token data."""
    email: Optional[str] = None


class UserResponse(BaseModel):
    """User information response."""
    id: uuid.UUID
    email: str
    role: str
    is_active: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
