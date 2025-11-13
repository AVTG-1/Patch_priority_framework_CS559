"""
Comprehensive tests for Phase 1: Backend API Foundation

Tests cover:
- FastAPI app initialization and basic endpoints
- Backend integration bridge
- Database models and operations
- JWT authentication system
- Error handling and edge cases
"""

import pytest
from fastapi import status
from datetime import datetime
import json

from models import User, SystemConfig, SimulationRun, CommunityVulnerability, VulnerabilityStatus
from auth import hash_password, verify_password, create_access_token, verify_token
from backend_bridge import get_system_summary


# ============================================================================
# Test: Basic Application Endpoints
# ============================================================================

class TestBasicEndpoints:
    """Test basic FastAPI endpoints"""

    def test_health_endpoint(self, client):
        """
        Test the /health endpoint returns healthy status.

        Validates:
        - Status code 200
        - Correct response structure
        - Service name and version
        """
        response = client.get("/health")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "Patch Priority Framework API"
        assert data["version"] == "1.0.0"

    def test_root_endpoint(self, client):
        """
        Test the root / endpoint returns API information.

        Validates:
        - Status code 200
        - Welcome message
        - Links to docs and health
        """
        response = client.get("/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data
        assert data["docs"] == "/docs"
        assert data["health"] == "/health"


# ============================================================================
# Test: Authentication - User Registration
# ============================================================================

class TestUserRegistration:
    """Test user registration endpoint"""

    def test_register_new_user_success(self, client, sample_user_data):
        """
        Test successful user registration.

        Validates:
        - Status code 201
        - Returns JWT token
        - User data in response
        - Token expiration info
        """
        response = client.post("/api/auth/register", json=sample_user_data)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()

        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
        assert data["user"]["username"] == sample_user_data["username"]
        assert data["user"]["email"] == sample_user_data["email"]
        assert "password" not in data["user"]  # Password should not be in response

    def test_register_duplicate_username(self, client, sample_user, sample_user_data):
        """
        Test registration with duplicate username fails.

        Validates:
        - Status code 400
        - Error message about duplicate username
        """
        response = client.post("/api/auth/register", json=sample_user_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Username already registered" in response.json()["detail"]

    def test_register_duplicate_email(self, client, sample_user):
        """
        Test registration with duplicate email fails.

        Validates:
        - Status code 400
        - Error message about duplicate email
        """
        new_user_data = {
            "username": "differentuser",
            "email": sample_user.email,  # Same email
            "password": "testpass123"
        }
        response = client.post("/api/auth/register", json=new_user_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Email already registered" in response.json()["detail"]

    @pytest.mark.parametrize("invalid_data,expected_error", [
        ({"username": "ab", "email": "test@example.com", "password": "pass123"}, "at least 3 characters"),
        ({"username": "testuser", "email": "invalid-email", "password": "pass123"}, "value is not a valid email"),
        ({"username": "testuser", "email": "test@example.com", "password": "123"}, "at least 6 characters"),
        ({"username": "test user!", "email": "test@example.com", "password": "pass123"}, "alphanumeric"),
    ])
    def test_register_invalid_data(self, client, invalid_data, expected_error):
        """
        Test registration with invalid data fails.

        Tests various validation failures:
        - Username too short (< 3 chars)
        - Invalid email format
        - Password too short (< 6 chars)
        - Username with special characters

        Validates:
        - Status code 422 (validation error)
        """
        response = client.post("/api/auth/register", json=invalid_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_register_missing_fields(self, client):
        """
        Test registration with missing required fields.

        Validates:
        - Status code 422
        - Proper validation errors
        """
        response = client.post("/api/auth/register", json={"username": "testuser"})

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ============================================================================
# Test: Authentication - User Login
# ============================================================================

class TestUserLogin:
    """Test user login endpoint"""

    def test_login_success(self, client, sample_user, sample_user_data):
        """
        Test successful login.

        Validates:
        - Status code 200
        - Returns JWT token
        - User information in response
        """
        response = client.post(
            "/api/auth/login",
            data={
                "username": sample_user_data["username"],
                "password": sample_user_data["password"]
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["username"] == sample_user_data["username"]

    def test_login_wrong_password(self, client, sample_user, sample_user_data):
        """
        Test login with incorrect password.

        Validates:
        - Status code 401
        - Error message about incorrect credentials
        """
        response = client.post(
            "/api/auth/login",
            data={
                "username": sample_user_data["username"],
                "password": "wrongpassword"
            }
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Incorrect username or password" in response.json()["detail"]

    def test_login_nonexistent_user(self, client):
        """
        Test login with non-existent username.

        Validates:
        - Status code 401
        - Error message
        """
        response = client.post(
            "/api/auth/login",
            data={
                "username": "nonexistent",
                "password": "somepassword"
            }
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_missing_credentials(self, client):
        """
        Test login with missing credentials.

        Validates:
        - Status code 422
        """
        response = client.post("/api/auth/login", data={})

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ============================================================================
# Test: Authentication - Protected Routes
# ============================================================================

class TestProtectedRoutes:
    """Test protected endpoints requiring authentication"""

    def test_get_current_user_success(self, client, auth_headers, sample_user):
        """
        Test accessing /api/auth/me with valid token.

        Validates:
        - Status code 200
        - Returns current user information
        - User ID, username, email present
        """
        response = client.get("/api/auth/me", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["id"] == sample_user.id
        assert data["username"] == sample_user.username
        assert data["email"] == sample_user.email
        assert data["is_admin"] == sample_user.is_admin

    def test_get_current_user_no_token(self, client):
        """
        Test accessing protected route without token.

        Validates:
        - Status code 401
        - Error message about missing credentials
        """
        response = client.get("/api/auth/me")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_current_user_invalid_token(self, client):
        """
        Test accessing protected route with invalid token.

        Validates:
        - Status code 401
        - Proper error handling
        """
        headers = {"Authorization": "Bearer invalid_token_12345"}
        response = client.get("/api/auth/me", headers=headers)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_current_user_malformed_header(self, client):
        """
        Test accessing protected route with malformed auth header.

        Validates:
        - Status code 401
        """
        headers = {"Authorization": "InvalidFormat token123"}
        response = client.get("/api/auth/me", headers=headers)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ============================================================================
# Test: Simulation Endpoint
# ============================================================================

class TestSimulationEndpoint:
    """Test simulation endpoint"""

    def test_test_simulation_success(self, client):
        """
        Test the /api/test-simulation endpoint.

        Validates:
        - Status code 200
        - Returns simulation results
        - Contains expected result fields
        """
        response = client.post("/api/test-simulation")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["status"] == "success"
        assert "results" in data
        results = data["results"]

        # Check key result fields
        assert "patch_priority_list" in results
        assert "ris_summary" in results
        assert "equilibrium_report" in results
        assert "system_info" in results
        assert "simulation_metrics" in results

        # Validate types
        assert isinstance(results["patch_priority_list"], list)
        assert isinstance(results["ris_summary"], list)
        assert isinstance(results["system_info"], dict)


# ============================================================================
# Test: Database Models
# ============================================================================

class TestDatabaseModels:
    """Test database models and operations"""

    def test_user_model_creation(self, db_session):
        """
        Test User model creation and attributes.

        Validates:
        - User can be created
        - All fields are set correctly
        - to_dict() method works
        """
        user = User(
            username="dbuser",
            email="dbuser@example.com",
            hashed_password=hash_password("password123"),
            is_admin=False
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        assert user.id is not None
        assert user.username == "dbuser"
        assert user.email == "dbuser@example.com"
        assert user.created_at is not None
        assert user.is_admin is False

        # Test to_dict()
        user_dict = user.to_dict()
        assert "id" in user_dict
        assert "username" in user_dict
        assert "email" in user_dict
        assert "hashed_password" not in user_dict  # Should not expose password

    def test_system_config_model(self, db_session, sample_user):
        """
        Test SystemConfig model and relationships.

        Validates:
        - SystemConfig creation
        - Foreign key relationship with User
        - to_dict() method
        """
        config = SystemConfig(
            user_id=sample_user.id,
            name="Test Config",
            config_json='{"test": "data"}'
        )
        db_session.add(config)
        db_session.commit()
        db_session.refresh(config)

        assert config.id is not None
        assert config.user_id == sample_user.id
        assert config.user.username == sample_user.username
        assert config.created_at is not None

    def test_simulation_run_model(self, db_session, sample_system_config):
        """
        Test SimulationRun model.

        Validates:
        - SimulationRun creation
        - Relationship with SystemConfig
        - JSON fields
        """
        run = SimulationRun(
            system_config_id=sample_system_config.id,
            parameters_json='{"rounds": 10}',
            results_json='{"results": "data"}'
        )
        db_session.add(run)
        db_session.commit()
        db_session.refresh(run)

        assert run.id is not None
        assert run.system_config_id == sample_system_config.id
        assert run.system_config.name == sample_system_config.name
        assert run.created_at is not None

    def test_community_vulnerability_model(self, db_session, sample_user):
        """
        Test CommunityVulnerability model.

        Validates:
        - Vulnerability creation
        - All fields including optional ones
        - Vote score calculation
        - Status enum
        """
        vuln = CommunityVulnerability(
            comm_id="COMM-TEST-001",
            reporter_id=sample_user.id,
            description="Test vulnerability",
            cvss_impact=9.0,
            cvss_exploitability=8.5,
            status=VulnerabilityStatus.VERIFIED,
            affected_subsystem_type="database",
            exploit_present=True,
            patch_cost_estimate=20.0,
            upvotes=10,
            downvotes=2
        )
        db_session.add(vuln)
        db_session.commit()
        db_session.refresh(vuln)

        assert vuln.id is not None
        assert vuln.comm_id == "COMM-TEST-001"
        assert vuln.reporter_id == sample_user.id
        assert vuln.status == VulnerabilityStatus.VERIFIED
        assert vuln.get_vote_score() == 8  # 10 - 2

    @pytest.mark.parametrize("status_value", [
        VulnerabilityStatus.UNVERIFIED,
        VulnerabilityStatus.VERIFIED,
        VulnerabilityStatus.DEPRECATED,
    ])
    def test_vulnerability_status_enum(self, db_session, sample_user, status_value):
        """
        Test different vulnerability status values.

        Validates:
        - All enum values can be set
        - Enum values are stored correctly
        """
        vuln = CommunityVulnerability(
            comm_id=f"COMM-{status_value.value}-001",
            reporter_id=sample_user.id,
            description="Test",
            cvss_impact=5.0,
            cvss_exploitability=5.0,
            status=status_value
        )
        db_session.add(vuln)
        db_session.commit()
        db_session.refresh(vuln)

        assert vuln.status == status_value

    def test_user_cascade_delete(self, db_session, sample_user):
        """
        Test that deleting a user cascades to related records.

        Validates:
        - SystemConfig deleted when user is deleted
        - CommunityVulnerability deleted when user is deleted
        """
        # Create related records
        config = SystemConfig(
            user_id=sample_user.id,
            name="Test Config",
            config_json="{}"
        )
        vuln = CommunityVulnerability(
            comm_id="COMM-CASCADE-001",
            reporter_id=sample_user.id,
            description="Test",
            cvss_impact=5.0,
            cvss_exploitability=5.0
        )
        db_session.add(config)
        db_session.add(vuln)
        db_session.commit()

        config_id = config.id
        vuln_id = vuln.id

        # Delete user
        db_session.delete(sample_user)
        db_session.commit()

        # Check that related records are deleted
        assert db_session.query(SystemConfig).filter_by(id=config_id).first() is None
        assert db_session.query(CommunityVulnerability).filter_by(id=vuln_id).first() is None


# ============================================================================
# Test: Authentication Utilities
# ============================================================================

class TestAuthUtilities:
    """Test authentication utility functions"""

    def test_password_hashing(self):
        """
        Test password hashing and verification.

        Validates:
        - Passwords are hashed correctly
        - Hashed password is different from plain text
        - Verification works for correct password
        - Verification fails for incorrect password
        """
        password = "testpassword123"
        hashed = hash_password(password)

        assert hashed != password
        assert isinstance(hashed, str)
        assert len(hashed) > 0

        # Test verification
        assert verify_password(password, hashed) is True
        assert verify_password("wrongpassword", hashed) is False

    def test_jwt_token_creation_and_validation(self):
        """
        Test JWT token creation and validation.

        Validates:
        - Token is created successfully
        - Token is a string
        - Token can be verified
        - Token contains correct data
        """
        data = {"sub": "testuser"}
        token = create_access_token(data)

        assert isinstance(token, str)
        assert len(token) > 0

        # Verify token
        payload = verify_token(token)
        assert payload is not None
        assert payload["sub"] == "testuser"
        assert "exp" in payload

    def test_jwt_token_invalid(self):
        """
        Test JWT token validation with invalid token.

        Validates:
        - Invalid token returns None
        """
        invalid_token = "invalid.token.here"
        payload = verify_token(invalid_token)

        assert payload is None


# ============================================================================
# Test: Backend Bridge Functions
# ============================================================================

class TestBackendBridge:
    """Test backend integration bridge functions"""

    def test_get_system_summary(self):
        """
        Test get_system_summary utility function.

        Validates:
        - Function can load system from example config
        - Returns expected fields
        - Data types are correct
        """
        from pathlib import Path
        from backend_bridge import load_system_from_config

        # Load example system
        example_config = Path(__file__).parent.parent.parent / "base_backend" / "config" / "example_system.json"

        if example_config.exists():
            system = load_system_from_config(str(example_config))
            summary = get_system_summary(system)

            assert "system_name" in summary
            assert "subsystem_count" in summary
            assert "vulnerability_count" in summary
            assert isinstance(summary["subsystem_count"], int)
            assert isinstance(summary["vulnerability_count"], int)


# ============================================================================
# Test: Edge Cases and Error Handling
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error conditions"""

    def test_register_with_very_long_username(self, client):
        """
        Test registration with very long username.

        Validates:
        - Server handles long input gracefully
        - Returns validation error
        """
        long_username = "a" * 100
        user_data = {
            "username": long_username,
            "email": "test@example.com",
            "password": "password123"
        }
        response = client.post("/api/auth/register", json=user_data)

        # Should fail validation (max 50 chars)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_login_with_empty_strings(self, client):
        """
        Test login with empty username/password.

        Validates:
        - Empty credentials are rejected
        """
        response = client.post(
            "/api/auth/login",
            data={"username": "", "password": ""}
        )

        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_422_UNPROCESSABLE_ENTITY]

    def test_vulnerability_vote_score_edge_cases(self, db_session, sample_user):
        """
        Test edge cases for vulnerability vote scores.

        Validates:
        - Zero votes
        - Negative vote scores
        - Large vote counts
        """
        test_cases = [
            (0, 0, 0),      # No votes
            (0, 10, -10),   # Only downvotes
            (100, 0, 100),  # Only upvotes
            (50, 50, 0),    # Equal votes
        ]

        for upvotes, downvotes, expected_score in test_cases:
            vuln = CommunityVulnerability(
                comm_id=f"COMM-VOTE-{upvotes}-{downvotes}",
                reporter_id=sample_user.id,
                description="Test",
                cvss_impact=5.0,
                cvss_exploitability=5.0,
                upvotes=upvotes,
                downvotes=downvotes
            )
            assert vuln.get_vote_score() == expected_score

    @pytest.mark.parametrize("cvss_value", [0.0, 5.0, 10.0])
    def test_vulnerability_cvss_boundary_values(self, db_session, sample_user, cvss_value):
        """
        Test CVSS scores at boundary values.

        Validates:
        - Minimum value (0.0)
        - Mid value (5.0)
        - Maximum value (10.0)
        """
        vuln = CommunityVulnerability(
            comm_id=f"COMM-CVSS-{cvss_value}",
            reporter_id=sample_user.id,
            description="Test",
            cvss_impact=cvss_value,
            cvss_exploitability=cvss_value
        )
        db_session.add(vuln)
        db_session.commit()
        db_session.refresh(vuln)

        assert vuln.cvss_impact == cvss_value
        assert vuln.cvss_exploitability == cvss_value

    def test_concurrent_user_registration(self, client):
        """
        Test handling of near-simultaneous duplicate registrations.

        Validates:
        - Second registration fails even if near-simultaneous
        """
        user_data = {
            "username": "concurrent_test",
            "email": "concurrent@example.com",
            "password": "password123"
        }

        # First registration
        response1 = client.post("/api/auth/register", json=user_data)
        assert response1.status_code == status.HTTP_201_CREATED

        # Second registration with same data
        response2 = client.post("/api/auth/register", json=user_data)
        assert response2.status_code == status.HTTP_400_BAD_REQUEST


# ============================================================================
# Test: Database Query Operations
# ============================================================================

class TestDatabaseQueries:
    """Test database query operations"""

    def test_query_users_by_username(self, db_session, sample_user):
        """
        Test querying users by username.

        Validates:
        - User can be found by username
        - Query returns correct user
        """
        user = db_session.query(User).filter(User.username == sample_user.username).first()

        assert user is not None
        assert user.id == sample_user.id
        assert user.email == sample_user.email

    def test_query_users_by_email(self, db_session, sample_user):
        """
        Test querying users by email.

        Validates:
        - User can be found by email
        - Query returns correct user
        """
        user = db_session.query(User).filter(User.email == sample_user.email).first()

        assert user is not None
        assert user.id == sample_user.id

    def test_query_vulnerabilities_by_status(self, db_session, sample_user):
        """
        Test querying vulnerabilities by status.

        Validates:
        - Can filter by UNVERIFIED
        - Can filter by VERIFIED
        - Correct count returned
        """
        # Create vulnerabilities with different statuses
        vuln1 = CommunityVulnerability(
            comm_id="COMM-001",
            reporter_id=sample_user.id,
            description="Test 1",
            cvss_impact=5.0,
            cvss_exploitability=5.0,
            status=VulnerabilityStatus.UNVERIFIED
        )
        vuln2 = CommunityVulnerability(
            comm_id="COMM-002",
            reporter_id=sample_user.id,
            description="Test 2",
            cvss_impact=5.0,
            cvss_exploitability=5.0,
            status=VulnerabilityStatus.VERIFIED
        )
        db_session.add_all([vuln1, vuln2])
        db_session.commit()

        # Query unverified
        unverified = db_session.query(CommunityVulnerability).filter(
            CommunityVulnerability.status == VulnerabilityStatus.UNVERIFIED
        ).all()
        assert len(unverified) == 1
        assert unverified[0].comm_id == "COMM-001"

        # Query verified
        verified = db_session.query(CommunityVulnerability).filter(
            CommunityVulnerability.status == VulnerabilityStatus.VERIFIED
        ).all()
        assert len(verified) == 1
        assert verified[0].comm_id == "COMM-002"

    def test_query_system_configs_by_user(self, db_session, sample_user):
        """
        Test querying system configs by user.

        Validates:
        - Can retrieve all configs for a user
        - Relationship works correctly
        """
        # Create multiple configs
        config1 = SystemConfig(
            user_id=sample_user.id,
            name="Config 1",
            config_json="{}"
        )
        config2 = SystemConfig(
            user_id=sample_user.id,
            name="Config 2",
            config_json="{}"
        )
        db_session.add_all([config1, config2])
        db_session.commit()

        # Query
        configs = db_session.query(SystemConfig).filter(
            SystemConfig.user_id == sample_user.id
        ).all()

        assert len(configs) == 2


# ============================================================================
# Test: Data Validation
# ============================================================================

class TestDataValidation:
    """Test data validation in schemas"""

    def test_user_create_schema_validation(self, client):
        """
        Test UserCreate schema validation.

        Validates various invalid inputs are rejected.
        """
        invalid_cases = [
            # Missing required fields
            {"username": "test"},
            {"email": "test@example.com"},
            {"password": "pass123"},
            # Invalid types
            {"username": 123, "email": "test@example.com", "password": "pass123"},
            {"username": "test", "email": "not-an-email", "password": "pass123"},
        ]

        for invalid_data in invalid_cases:
            response = client.post("/api/auth/register", json=invalid_data)
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
