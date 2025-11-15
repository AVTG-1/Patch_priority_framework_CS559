"""
Pytest configuration and fixtures for web API tests
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base, get_db
from main import app
from models import User, SystemConfig, SimulationRun, CommunityVulnerability, VulnerabilityStatus
from auth import hash_password


# Test database engine (in-memory SQLite)
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """
    Create a fresh database session for each test.

    Yields:
        Session: SQLAlchemy database session
    """
    # Create tables
    Base.metadata.create_all(bind=engine)

    # Create session
    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        # Drop all tables after test
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """
    Create a test client with dependency override for database.

    Args:
        db_session: Database session fixture

    Yields:
        TestClient: FastAPI test client
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def sample_user_data():
    """
    Sample user data for testing.

    Returns:
        dict: User registration data
    """
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass123"
    }


@pytest.fixture
def sample_user(db_session, sample_user_data):
    """
    Create a sample user in the database.

    Args:
        db_session: Database session
        sample_user_data: Sample user data

    Returns:
        User: Created user object
    """
    user = User(
        username=sample_user_data["username"],
        email=sample_user_data["email"],
        hashed_password=hash_password(sample_user_data["password"]),
        is_admin=False
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_user(db_session):
    """
    Create an admin user in the database.

    Args:
        db_session: Database session

    Returns:
        User: Created admin user
    """
    user = User(
        username="admin",
        email="admin@example.com",
        hashed_password=hash_password("adminpass123"),
        is_admin=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_token(client, sample_user, sample_user_data):
    """
    Get authentication token for sample user.

    Args:
        client: Test client
        sample_user: Sample user
        sample_user_data: Sample user data (for password)

    Returns:
        str: JWT access token
    """
    response = client.post(
        "/api/auth/login",
        data={
            "username": sample_user_data["username"],
            "password": sample_user_data["password"]
        }
    )
    return response.json()["access_token"]


@pytest.fixture
def auth_headers(auth_token):
    """
    Get authentication headers with bearer token.

    Args:
        auth_token: JWT access token

    Returns:
        dict: Headers with authorization
    """
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def sample_system_config(db_session, sample_user):
    """
    Create a sample system configuration.

    Args:
        db_session: Database session
        sample_user: User who owns the config

    Returns:
        SystemConfig: Created system configuration
    """
    config = SystemConfig(
        user_id=sample_user.id,
        name="Test SCADA System",
        config_json='{"system_name": "Test System", "subsystems": []}'
    )
    db_session.add(config)
    db_session.commit()
    db_session.refresh(config)
    return config


@pytest.fixture
def sample_simulation_run(db_session, sample_system_config):
    """
    Create a sample simulation run.

    Args:
        db_session: Database session
        sample_system_config: System configuration

    Returns:
        SimulationRun: Created simulation run
    """
    run = SimulationRun(
        system_config_id=sample_system_config.id,
        parameters_json='{"rounds": 5, "patch_grouping_method": "dependencies"}',
        results_json='{"patch_priority_list": ["CVE-2024-0001"], "ris_summary": [10.0, 5.0]}'
    )
    db_session.add(run)
    db_session.commit()
    db_session.refresh(run)
    return run


@pytest.fixture
def sample_community_vulnerability(db_session, sample_user):
    """
    Create a sample community vulnerability.

    Args:
        db_session: Database session
        sample_user: User who reported the vulnerability

    Returns:
        CommunityVulnerability: Created vulnerability
    """
    vuln = CommunityVulnerability(
        comm_id="COMM-CVE-2024-001",
        reporter_id=sample_user.id,
        description="Test SQL injection vulnerability",
        cvss_impact=8.5,
        cvss_exploitability=7.8,
        status=VulnerabilityStatus.UNVERIFIED,
        affected_subsystem_type="web_server",
        exploit_present=True,
        patch_cost_estimate=15.0,
        upvotes=5,
        downvotes=1
    )
    db_session.add(vuln)
    db_session.commit()
    db_session.refresh(vuln)
    return vuln
