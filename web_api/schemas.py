"""
Pydantic Schemas for Request/Response Validation

Defines data models for API endpoints.
"""

from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from typing import Optional, Dict, Any, List
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

    model_config = ConfigDict(from_attributes=True)


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

    model_config = ConfigDict(from_attributes=True)


# Simulation Schemas
class SimulationRunCreate(BaseModel):
    """Schema for creating simulation run"""
    system_id: int = Field(..., description="System configuration ID to simulate")
    system_name: str = Field(..., min_length=1, max_length=255, description="System name for simulation")
    rounds: int = Field(default=10, ge=1, le=100, description="Number of simulation rounds (1-100)")
    defender_budget: Optional[float] = Field(None, ge=0.0, description="Defender resource budget")
    attacker_budget: Optional[float] = Field(None, ge=0.0, description="Attacker resource budget")
    patch_grouping_method: str = Field(default="dependencies", description="Patch grouping strategy")

    @field_validator('patch_grouping_method')
    @classmethod
    def validate_grouping_method(cls, v):
        """Validate patch grouping method"""
        allowed = ['dependencies', 'subsystem', 'severity']
        if v not in allowed:
            raise ValueError(f'Patch grouping method must be one of: {", ".join(allowed)}')
        return v


class SimulationRunResponse(BaseModel):
    """Schema for simulation run response"""
    id: int
    system_config_id: int
    parameters_json: str
    results_json: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SimulationSummary(BaseModel):
    """Schema for simulation summary response"""
    simulation_id: int
    system_id: int
    system_name: str
    rounds: int
    initial_ris: float
    final_ris: float
    ris_reduction: float
    ris_reduction_percentage: float
    total_vulnerabilities_patched: int
    patch_priority_list: List[str]
    created_at: datetime


class SimulationDetailResponse(BaseModel):
    """Schema for detailed simulation response"""
    id: int
    system_config_id: int
    system_name: str
    parameters: Dict[str, Any]
    results: Dict[str, Any]
    created_at: datetime


# Community Vulnerability Schemas
class CommunityVulnerabilityCreate(BaseModel):
    """Schema for creating community vulnerability"""
    comm_id: Optional[str] = Field(None, max_length=100, description="Community vulnerability ID (auto-generated if not provided)")
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

    model_config = ConfigDict(from_attributes=True)


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


# Admin Schemas
class UserListResponse(BaseModel):
    """Schema for user list with additional metadata (admin view)"""
    id: int
    username: str
    email: str
    is_admin: bool
    created_at: datetime
    system_count: int
    simulation_count: int
    vulnerability_count: int


class ActivitySummary(BaseModel):
    """Schema for activity summary"""
    new_users: int
    new_systems: int
    new_simulations: int
    new_vulnerabilities: int


class TotalCounts(BaseModel):
    """Schema for total counts"""
    users: int
    systems: int
    simulations: int
    vulnerabilities: int


class UserDistribution(BaseModel):
    """Schema for user distribution"""
    admin_users: int
    regular_users: int


class VulnerabilityStatusDistribution(BaseModel):
    """Schema for vulnerability status distribution"""
    unverified: int
    verified: int
    deprecated: int


class TopUser(BaseModel):
    """Schema for top user statistics"""
    user_id: int
    username: str
    simulation_count: Optional[int] = None
    contribution_count: Optional[int] = None


class AdminStatsResponse(BaseModel):
    """Schema for admin statistics response"""
    timestamp: datetime
    total_counts: TotalCounts
    user_distribution: UserDistribution
    vulnerability_status: VulnerabilityStatusDistribution
    recent_activity_7d: ActivitySummary
    recent_activity_30d: ActivitySummary
    most_active_users: List[TopUser]
    top_contributors: List[TopUser]
