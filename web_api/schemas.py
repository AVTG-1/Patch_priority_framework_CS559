"""
Pydantic Schemas for Request/Response Validation

Defines data models for API endpoints.
"""

from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime


# User Schemas
class UserCreate(BaseModel):
    """Schema for user registration"""
    username: str = Field(..., min_length=3, max_length=50, description="Username (3-50 characters)")
    email: EmailStr = Field(..., description="Valid email address")
    password: str = Field(..., min_length=6, description="Password (minimum 6 characters)")

    @field_validator('username')
    @classmethod
    def username_alphanumeric(cls, v):
        """Validate username is alphanumeric with underscores/hyphens"""
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username must be alphanumeric (can include _ and -)')
        return v


class UserLogin(BaseModel):
    """Schema for user login"""
    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password")


class UserResponse(BaseModel):
    """Schema for user data in responses"""
    id: int
    username: str
    email: str
    created_at: datetime
    is_admin: bool

    class Config:
        from_attributes = True


class Token(BaseModel):
    """Schema for token response"""
    access_token: str
    token_type: str
    expires_in: int
    user: UserResponse


class TokenData(BaseModel):
    """Schema for token payload data"""
    username: Optional[str] = None


# System Configuration Schemas
class SystemConfigCreate(BaseModel):
    """Schema for creating system configuration"""
    name: str = Field(..., min_length=1, max_length=255)
    config_json: str = Field(..., description="JSON configuration string")


class SystemConfigResponse(BaseModel):
    """Schema for system configuration response"""
    id: int
    user_id: int
    name: str
    config_json: str
    created_at: datetime

    class Config:
        from_attributes = True


# Simulation Schemas
class SimulationRunCreate(BaseModel):
    """Schema for creating simulation run"""
    system_config_id: int
    parameters_json: str = Field(..., description="Simulation parameters as JSON")


class SimulationRunResponse(BaseModel):
    """Schema for simulation run response"""
    id: int
    system_config_id: int
    parameters_json: str
    results_json: str
    created_at: datetime

    class Config:
        from_attributes = True


# Community Vulnerability Schemas
class CommunityVulnerabilityCreate(BaseModel):
    """Schema for creating community vulnerability"""
    comm_id: str = Field(..., max_length=100, description="Community vulnerability ID")
    description: str = Field(..., min_length=10, description="Vulnerability description")
    cvss_impact: float = Field(..., ge=0.0, le=10.0, description="CVSS impact score (0-10)")
    cvss_exploitability: float = Field(..., ge=0.0, le=10.0, description="CVSS exploitability score (0-10)")
    affected_subsystem_type: Optional[str] = Field(None, max_length=100)
    exploit_present: bool = Field(default=False)
    patch_cost_estimate: Optional[float] = Field(None, ge=0.0)


class CommunityVulnerabilityResponse(BaseModel):
    """Schema for community vulnerability response"""
    id: int
    comm_id: str
    reporter_id: int
    reporter_username: Optional[str]
    description: str
    cvss_impact: float
    cvss_exploitability: float
    status: str
    created_at: datetime
    affected_subsystem_type: Optional[str]
    exploit_present: bool
    patch_cost_estimate: Optional[float]
    upvotes: int
    downvotes: int
    vote_score: int

    class Config:
        from_attributes = True


# Error Schemas
class ErrorResponse(BaseModel):
    """Schema for error responses"""
    detail: str
    status_code: int


# Success Schemas
class MessageResponse(BaseModel):
    """Schema for simple message responses"""
    message: str
    status: str = "success"
