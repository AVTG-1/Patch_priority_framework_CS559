"""
Database Models

Defines SQLAlchemy ORM models for the Patch Priority Framework.
"""

from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from database import Base


class VulnerabilityStatus(str, enum.Enum):
    """Enum for community vulnerability verification status"""
    UNVERIFIED = "UNVERIFIED"
    VERIFIED = "VERIFIED"
    DEPRECATED = "DEPRECATED"


class User(Base):
    """
    User model for authentication and authorization.

    Stores user credentials and metadata.
    Each user can have multiple system configurations and simulation runs.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)

    # Relationships
    system_configs = relationship("SystemConfig", back_populates="user", cascade="all, delete-orphan")
    reported_vulnerabilities = relationship("CommunityVulnerability", back_populates="reporter", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}', is_admin={self.is_admin})>"

    def to_dict(self):
        """Convert user to dictionary (excluding password)"""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "is_admin": self.is_admin
        }


class SystemConfig(Base):
    """
    System Configuration model.

    Stores user's system configurations as JSON.
    Each configuration can have multiple simulation runs.
    """
    __tablename__ = "system_configs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    config_json = Column(Text, nullable=False)  # JSON stored as text
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="system_configs")
    simulation_runs = relationship("SimulationRun", back_populates="system_config", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<SystemConfig(id={self.id}, name='{self.name}', user_id={self.user_id})>"

    def to_dict(self):
        """Convert system config to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "config_json": self.config_json,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class SimulationRun(Base):
    """
    Simulation Run model.

    Stores simulation parameters and results.
    Each run is associated with a system configuration.
    """
    __tablename__ = "simulation_runs"

    id = Column(Integer, primary_key=True, index=True)
    system_config_id = Column(Integer, ForeignKey("system_configs.id"), nullable=False, index=True)
    parameters_json = Column(Text, nullable=False)  # JSON stored as text
    results_json = Column(Text, nullable=False)  # JSON stored as text
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    system_config = relationship("SystemConfig", back_populates="simulation_runs")

    def __repr__(self):
        return f"<SimulationRun(id={self.id}, system_config_id={self.system_config_id})>"

    def to_dict(self):
        """Convert simulation run to dictionary"""
        return {
            "id": self.id,
            "system_config_id": self.system_config_id,
            "parameters_json": self.parameters_json,
            "results_json": self.results_json,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class CommunityVulnerability(Base):
    """
    Community Vulnerability model.

    Stores vulnerabilities shared by the community.
    Users can report vulnerabilities and others can verify them.
    """
    __tablename__ = "community_vulnerabilities"

    id = Column(Integer, primary_key=True, index=True)
    comm_id = Column(String(100), unique=True, nullable=False, index=True)  # Community-assigned ID (e.g., COMM-CVE-2024-001)
    reporter_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    description = Column(Text, nullable=False)
    cvss_impact = Column(Float, nullable=False)  # CVSS impact score (0.0 - 10.0)
    cvss_exploitability = Column(Float, nullable=False)  # CVSS exploitability score (0.0 - 10.0)
    status = Column(Enum(VulnerabilityStatus), default=VulnerabilityStatus.UNVERIFIED, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Additional metadata fields
    affected_subsystem_type = Column(String(100), nullable=True)  # Type of subsystem affected
    exploit_present = Column(Boolean, default=False, nullable=False)
    patch_cost_estimate = Column(Float, nullable=True)  # Estimated cost to patch
    upvotes = Column(Integer, default=0, nullable=False)  # Community voting
    downvotes = Column(Integer, default=0, nullable=False)  # Community voting

    # Relationships
    reporter = relationship("User", back_populates="reported_vulnerabilities")

    def __repr__(self):
        return f"<CommunityVulnerability(id={self.id}, comm_id='{self.comm_id}', status='{self.status}')>"

    def to_dict(self):
        """Convert community vulnerability to dictionary"""
        return {
            "id": self.id,
            "comm_id": self.comm_id,
            "reporter_id": self.reporter_id,
            "reporter_username": self.reporter.username if self.reporter else None,
            "description": self.description,
            "cvss_impact": self.cvss_impact,
            "cvss_exploitability": self.cvss_exploitability,
            "status": self.status.value if isinstance(self.status, VulnerabilityStatus) else self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "affected_subsystem_type": self.affected_subsystem_type,
            "exploit_present": self.exploit_present,
            "patch_cost_estimate": self.patch_cost_estimate,
            "upvotes": self.upvotes,
            "downvotes": self.downvotes,
            "vote_score": self.upvotes - self.downvotes
        }

    def get_vote_score(self) -> int:
        """Calculate net vote score"""
        return self.upvotes - self.downvotes
