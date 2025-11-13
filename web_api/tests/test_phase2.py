"""
Comprehensive pytest tests for Phase 2 - Core API Endpoints

Tests cover:
- System management CRUD endpoints
- NVD vulnerability query endpoints with caching
- Community vulnerability submission and verification
- Simulation execution endpoints with async support
- Admin-only endpoints (user management, platform statistics)
"""

import pytest
import json
import time
from datetime import datetime, timedelta

from models import User, SystemConfig, SimulationRun, CommunityVulnerability, VulnerabilityStatus


# ============================================================================
# SYSTEM MANAGEMENT TESTS (Task 2.1)
# ============================================================================

class TestSystemManagement:
    """Tests for system management CRUD endpoints"""

    def test_create_system_success(self, client, auth_headers):
        """Test creating a new system configuration"""
        system_data = {
            "name": "Test Industrial System",
            "config_json": json.dumps({
                "system_name": "Test System",
                "system_class": "Industrial Control System",
                "subsystems": [
                    {
                        "id": "sub1",
                        "name": "Subsystem 1",
                        "connected_to": [],
                        "functional_dependencies": []
                    }
                ],
                "vulnerabilities": []
            })
        }

        response = client.post("/api/systems", json=system_data, headers=auth_headers)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Industrial System"
        assert "id" in data
        assert "created_at" in data

    def test_create_system_unauthenticated(self, client):
        """Test creating system without authentication fails"""
        system_data = {
            "name": "Test System",
            "config_json": json.dumps({"system_name": "Test"})
        }

        response = client.post("/api/systems", json=system_data)

        assert response.status_code == 401

    @pytest.mark.parametrize("invalid_field,value", [
        ("name", ""),  # Empty name
        ("config_json", "not valid json"),  # Invalid JSON
        ("config_json", ""),  # Empty config
    ])
    def test_create_system_invalid_data(self, client, auth_headers, invalid_field, value):
        """Test creating system with invalid data"""
        system_data = {
            "name": "Test System",
            "config_json": json.dumps({"system_name": "Test"})
        }
        system_data[invalid_field] = value

        response = client.post("/api/systems", json=system_data, headers=auth_headers)

        assert response.status_code in [400, 422]

    def test_list_systems_for_user(self, client, auth_headers, db_session, sample_user, sample_system_config):
        """Test listing systems for authenticated user"""
        response = client.get("/api/systems", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["id"] == sample_system_config.id

    def test_list_systems_empty(self, client, auth_headers):
        """Test listing systems when user has none"""
        response = client.get("/api/systems", headers=auth_headers)

        assert response.status_code == 200
        assert response.json() == []

    def test_get_system_by_id_success(self, client, auth_headers, sample_system_config):
        """Test retrieving specific system by ID"""
        response = client.get(f"/api/systems/{sample_system_config.id}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_system_config.id
        assert data["name"] == sample_system_config.name

    def test_get_system_not_found(self, client, auth_headers):
        """Test retrieving non-existent system returns 404"""
        response = client.get("/api/systems/999999", headers=auth_headers)

        assert response.status_code == 404

    def test_get_system_unauthorized_access(self, client, db_session, sample_system_config):
        """Test accessing another user's system fails"""
        # Create another user
        other_user = User(
            username="otheruser",
            email="other@example.com",
            hashed_password="hashed",
            is_admin=False
        )
        db_session.add(other_user)
        db_session.commit()

        # Login as other user
        response = client.post("/api/auth/register", json={
            "username": "otheruser2",
            "email": "other2@example.com",
            "password": "pass123"
        })
        other_token = response.json()["access_token"]
        other_headers = {"Authorization": f"Bearer {other_token}"}

        # Try to access original user's system
        response = client.get(f"/api/systems/{sample_system_config.id}", headers=other_headers)

        # Expect 404 (not 403) to hide existence of systems from unauthorized users
        # This is a security feature to prevent information leakage
        assert response.status_code == 404

    def test_update_system_success(self, client, auth_headers, sample_system_config):
        """Test updating system configuration"""
        update_data = {
            "name": "Updated System Name",
            "config_json": json.dumps({"system_name": "Updated"})
        }

        response = client.put(
            f"/api/systems/{sample_system_config.id}",
            json=update_data,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated System Name"

    def test_update_system_not_found(self, client, auth_headers):
        """Test updating non-existent system returns 404"""
        update_data = {
            "name": "Updated",
            "config_json": json.dumps({"system_name": "Updated"})
        }

        response = client.put("/api/systems/999999", json=update_data, headers=auth_headers)

        assert response.status_code == 404

    def test_delete_system_success(self, client, auth_headers, sample_system_config, db_session):
        """Test deleting system configuration

        Note: DELETE returns 204 No Content (standard REST convention for successful
        deletion with no response body).
        """
        system_id = sample_system_config.id

        response = client.delete(f"/api/systems/{system_id}", headers=auth_headers)

        # Expect 204 No Content (standard for DELETE operations)
        assert response.status_code == 204

        # Verify deletion from database
        deleted_system = db_session.query(SystemConfig).filter(
            SystemConfig.id == system_id
        ).first()
        assert deleted_system is None

    def test_delete_system_not_found(self, client, auth_headers):
        """Test deleting non-existent system returns 404"""
        response = client.delete("/api/systems/999999", headers=auth_headers)

        assert response.status_code == 404


# ============================================================================
# VULNERABILITY QUERY TESTS (Task 2.2)
# ============================================================================

class TestVulnerabilityQueries:
    """Tests for NVD and community vulnerability query endpoints"""

    def test_query_nvd_valid_cve(self, client, mocker):
        """Test querying NVD for valid CVE (mocked)"""
        # Mock the NVD importer
        mock_fetch = mocker.patch('routers.vulnerabilities.nvd_importer.fetch_cve')
        mock_vulnerability = mocker.MagicMock()
        mock_vulnerability.cve_id = "CVE-2021-44228"
        mock_vulnerability.description = "Log4Shell vulnerability"
        mock_vulnerability.cvss_impact = 10.0
        mock_vulnerability.cvss_exploitability = 9.8
        mock_vulnerability.exploit_present = True
        mock_vulnerability.patch_cost = 20.0
        mock_vulnerability.subsystem_id = None
        mock_vulnerability.dependencies = []
        mock_vulnerability.custom_extras = {}
        mock_fetch.return_value = mock_vulnerability

        response = client.get("/api/vulnerabilities/nvd?cve_id=CVE-2021-44228")

        assert response.status_code == 200
        data = response.json()
        assert data["cve_id"] == "CVE-2021-44228"
        assert "cvss_impact" in data
        assert "cached" in data

    def test_query_nvd_invalid_format(self, client):
        """Test querying NVD with invalid CVE format"""
        response = client.get("/api/vulnerabilities/nvd?cve_id=INVALID-FORMAT")

        assert response.status_code == 422

    def test_query_nvd_not_found(self, client, mocker):
        """Test querying NVD for non-existent CVE"""
        mock_fetch = mocker.patch('routers.vulnerabilities.nvd_importer.fetch_cve')
        mock_fetch.return_value = None

        response = client.get("/api/vulnerabilities/nvd?cve_id=CVE-9999-99999")

        assert response.status_code == 404

    def test_list_community_vulnerabilities(self, client, sample_community_vulnerability):
        """Test listing community vulnerabilities"""
        response = client.get("/api/vulnerabilities/community")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["comm_id"] == sample_community_vulnerability.comm_id

    def test_list_community_vulnerabilities_pagination(self, client, db_session, sample_user):
        """Test pagination of community vulnerabilities"""
        # Create multiple vulnerabilities
        for i in range(5):
            vuln = CommunityVulnerability(
                comm_id=f"COMM-2024-000{i}",
                reporter_id=sample_user.id,
                description=f"Test vulnerability {i}",
                cvss_impact=7.0,
                cvss_exploitability=6.0,
                status=VulnerabilityStatus.UNVERIFIED
            )
            db_session.add(vuln)
        db_session.commit()

        # Test pagination
        response = client.get("/api/vulnerabilities/community?skip=0&limit=2")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_get_community_vulnerability_by_id(self, client, sample_community_vulnerability):
        """Test retrieving specific community vulnerability"""
        comm_id = sample_community_vulnerability.comm_id
        response = client.get(f"/api/vulnerabilities/community/{comm_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["comm_id"] == comm_id
        assert "reporter_username" in data
        assert "vote_score" in data

    def test_get_community_vulnerability_not_found(self, client):
        """Test retrieving non-existent community vulnerability"""
        response = client.get("/api/vulnerabilities/community/NONEXISTENT")

        assert response.status_code == 404


# ============================================================================
# COMMUNITY VULNERABILITY SUBMISSION TESTS (Task 2.3)
# ============================================================================

class TestCommunityVulnerabilitySubmission:
    """Tests for community vulnerability submission and management"""

    def test_submit_vulnerability_success(self, client, auth_headers, db_session):
        """Test submitting new community vulnerability"""
        vuln_data = {
            "description": "Critical buffer overflow in authentication module",
            "cvss_impact": 9.5,
            "cvss_exploitability": 8.7,
            "affected_subsystem_type": "authentication",
            "exploit_present": True,
            "patch_cost_estimate": 15.5
        }

        response = client.post(
            "/api/vulnerabilities/community",
            json=vuln_data,
            headers=auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert "comm_id" in data
        assert data["comm_id"].startswith("COMM-")
        assert data["status"] == "UNVERIFIED"
        assert data["description"] == vuln_data["description"]

    def test_submit_vulnerability_custom_id(self, client, auth_headers):
        """Test submitting vulnerability with custom ID"""
        vuln_data = {
            "comm_id": "COMM-TEST-9999",
            "description": "SQL injection vulnerability in user profile",
            "cvss_impact": 7.5,
            "cvss_exploitability": 6.8
        }

        response = client.post(
            "/api/vulnerabilities/community",
            json=vuln_data,
            headers=auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["comm_id"] == "COMM-TEST-9999"

    def test_submit_vulnerability_duplicate_id(self, client, auth_headers, sample_community_vulnerability):
        """Test submitting vulnerability with duplicate ID fails"""
        vuln_data = {
            "comm_id": sample_community_vulnerability.comm_id,
            "description": "Duplicate vulnerability",
            "cvss_impact": 7.0,
            "cvss_exploitability": 6.0
        }

        response = client.post(
            "/api/vulnerabilities/community",
            json=vuln_data,
            headers=auth_headers
        )

        assert response.status_code == 400

    @pytest.mark.parametrize("cvss_value", [-1.0, 11.0, 15.5])
    def test_submit_vulnerability_invalid_cvss(self, client, auth_headers, cvss_value):
        """Test submitting vulnerability with invalid CVSS scores"""
        vuln_data = {
            "description": "Test vulnerability with invalid CVSS",
            "cvss_impact": cvss_value,
            "cvss_exploitability": 7.0
        }

        response = client.post(
            "/api/vulnerabilities/community",
            json=vuln_data,
            headers=auth_headers
        )

        assert response.status_code == 422

    def test_submit_vulnerability_unauthenticated(self, client):
        """Test submitting vulnerability without authentication fails"""
        vuln_data = {
            "description": "Test vulnerability",
            "cvss_impact": 7.0,
            "cvss_exploitability": 6.0
        }

        response = client.post("/api/vulnerabilities/community", json=vuln_data)

        assert response.status_code == 401

    def test_verify_vulnerability_as_admin(self, client, db_session, admin_user, sample_community_vulnerability):
        """Test verifying vulnerability as admin"""
        # Login as admin
        admin_response = client.post(
            "/api/auth/login",
            data={"username": "admin", "password": "adminpass123"}
        )
        admin_token = admin_response.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        comm_id = sample_community_vulnerability.comm_id
        response = client.put(
            f"/api/vulnerabilities/community/{comm_id}/verify",
            headers=admin_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "VERIFIED"

    def test_verify_vulnerability_as_regular_user_fails(self, client, auth_headers, sample_community_vulnerability):
        """Test verifying vulnerability as regular user fails"""
        comm_id = sample_community_vulnerability.comm_id
        response = client.put(
            f"/api/vulnerabilities/community/{comm_id}/verify",
            headers=auth_headers
        )

        assert response.status_code == 403

    def test_verify_vulnerability_not_found(self, client, db_session, admin_user):
        """Test verifying non-existent vulnerability"""
        # Login as admin
        admin_response = client.post(
            "/api/auth/login",
            data={"username": "admin", "password": "adminpass123"}
        )
        admin_token = admin_response.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        response = client.put(
            "/api/vulnerabilities/community/NONEXISTENT/verify",
            headers=admin_headers
        )

        assert response.status_code == 404

    def test_deprecate_own_vulnerability(self, client, auth_headers, sample_community_vulnerability):
        """Test deprecating own vulnerability as reporter"""
        comm_id = sample_community_vulnerability.comm_id
        response = client.delete(
            f"/api/vulnerabilities/community/{comm_id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "DEPRECATED"

    def test_deprecate_other_user_vulnerability_fails(self, client, db_session, sample_community_vulnerability):
        """Test deprecating another user's vulnerability fails"""
        # Create another user
        other_response = client.post("/api/auth/register", json={
            "username": "otheruser",
            "email": "other@example.com",
            "password": "pass123"
        })
        other_token = other_response.json()["access_token"]
        other_headers = {"Authorization": f"Bearer {other_token}"}

        comm_id = sample_community_vulnerability.comm_id
        response = client.delete(
            f"/api/vulnerabilities/community/{comm_id}",
            headers=other_headers
        )

        assert response.status_code == 403

    def test_deprecate_vulnerability_as_admin(self, client, db_session, admin_user, sample_community_vulnerability):
        """Test deprecating vulnerability as admin"""
        # Login as admin
        admin_response = client.post(
            "/api/auth/login",
            data={"username": "admin", "password": "adminpass123"}
        )
        admin_token = admin_response.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        comm_id = sample_community_vulnerability.comm_id
        response = client.delete(
            f"/api/vulnerabilities/community/{comm_id}",
            headers=admin_headers
        )

        assert response.status_code == 200


# ============================================================================
# SIMULATION EXECUTION TESTS (Task 2.4)
# ============================================================================

class TestSimulationExecution:
    """Tests for simulation execution endpoints with async support"""

    @pytest.fixture
    def valid_system_config(self, client, auth_headers):
        """Create a valid system configuration for simulation"""
        system_data = {
            "name": "Test Simulation System",
            "config_json": json.dumps({
                "system_name": "Test System",
                "system_class": "Industrial Control System",
                "subsystems": [
                    {
                        "id": "sub1",
                        "name": "Subsystem 1",
                        "connected_to": [],
                        "functional_dependencies": []
                    }
                ],
                "vulnerabilities": [
                    {
                        "cve_id": "CVE-2024-0001",
                        "description": "Test vulnerability",
                        "subsystem_id": "sub1",
                        "cvss_impact": 7.0,
                        "cvss_exploitability": 6.0,
                        "exploit_present": False,
                        "patch_cost": 10.0,
                        "dependencies": []
                    }
                ]
            })
        }
        response = client.post("/api/systems", json=system_data, headers=auth_headers)
        return response.json()

    def test_run_simulation_success(self, client, auth_headers, valid_system_config):
        """Test running simulation with default parameters"""
        sim_data = {
            "system_id": valid_system_config["id"],
            "rounds": 5
        }

        response = client.post("/api/simulations", json=sim_data, headers=auth_headers)

        assert response.status_code == 201
        data = response.json()
        assert "simulation_id" in data
        assert data["system_id"] == valid_system_config["id"]
        assert data["rounds"] == 5

    def test_run_simulation_with_custom_budgets(self, client, auth_headers, valid_system_config):
        """Test running simulation with custom budgets"""
        sim_data = {
            "system_id": valid_system_config["id"],
            "rounds": 10,
            "defender_budget": 100.0,
            "attacker_budget": 50.0,
            "patch_grouping_method": "subsystem"
        }

        response = client.post("/api/simulations", json=sim_data, headers=auth_headers)

        assert response.status_code == 201
        data = response.json()
        assert data["rounds"] == 10

    @pytest.mark.parametrize("invalid_rounds", [0, -5, 150])
    def test_run_simulation_invalid_rounds(self, client, auth_headers, valid_system_config, invalid_rounds):
        """Test running simulation with invalid rounds parameter"""
        sim_data = {
            "system_id": valid_system_config["id"],
            "rounds": invalid_rounds
        }

        response = client.post("/api/simulations", json=sim_data, headers=auth_headers)

        assert response.status_code == 422

    def test_run_simulation_invalid_grouping_method(self, client, auth_headers, valid_system_config):
        """Test running simulation with invalid patch grouping method"""
        sim_data = {
            "system_id": valid_system_config["id"],
            "rounds": 5,
            "patch_grouping_method": "invalid_method"
        }

        response = client.post("/api/simulations", json=sim_data, headers=auth_headers)

        assert response.status_code == 422

    def test_run_simulation_system_not_found(self, client, auth_headers):
        """Test running simulation on non-existent system"""
        sim_data = {
            "system_id": 999999,
            "rounds": 5
        }

        response = client.post("/api/simulations", json=sim_data, headers=auth_headers)

        assert response.status_code == 404

    def test_run_simulation_unauthorized_system(self, client, db_session, valid_system_config):
        """Test running simulation on another user's system"""
        # Create another user
        other_response = client.post("/api/auth/register", json={
            "username": "otheruser",
            "email": "other@example.com",
            "password": "pass123"
        })
        other_token = other_response.json()["access_token"]
        other_headers = {"Authorization": f"Bearer {other_token}"}

        sim_data = {
            "system_id": valid_system_config["id"],
            "rounds": 5
        }

        response = client.post("/api/simulations", json=sim_data, headers=other_headers)

        assert response.status_code == 403

    def test_get_simulation_results(self, client, auth_headers, sample_simulation_run):
        """Test retrieving simulation results"""
        sim_id = sample_simulation_run.id
        response = client.get(f"/api/simulations/{sim_id}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sim_id
        assert "parameters" in data
        assert "results" in data

    def test_get_simulation_not_found(self, client, auth_headers):
        """Test retrieving non-existent simulation"""
        response = client.get("/api/simulations/999999", headers=auth_headers)

        assert response.status_code == 404

    def test_list_simulations_for_user(self, client, auth_headers, sample_simulation_run):
        """Test listing simulations for authenticated user"""
        response = client.get("/api/simulations", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_list_simulations_by_system(self, client, auth_headers, sample_system_config, sample_simulation_run):
        """Test listing simulations filtered by system ID"""
        system_id = sample_system_config.id
        response = client.get(f"/api/simulations?system_id={system_id}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        for sim in data:
            assert sim["system_config_id"] == system_id

    def test_list_simulations_pagination(self, client, auth_headers):
        """Test simulation list pagination"""
        response = client.get("/api/simulations?skip=0&limit=10", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 10


# ============================================================================
# ADMIN ENDPOINTS TESTS (Task 2.5)
# ============================================================================

class TestAdminEndpoints:
    """Tests for admin-only endpoints"""

    def test_list_users_as_admin(self, client, db_session, admin_user, sample_user):
        """Test listing all users as admin"""
        # Login as admin
        admin_response = client.post(
            "/api/auth/login",
            data={"username": "admin", "password": "adminpass123"}
        )
        admin_token = admin_response.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        response = client.get("/api/admin/users", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2  # At least admin and sample_user

        # Check that user metadata is included
        assert "system_count" in data[0]
        assert "simulation_count" in data[0]
        assert "vulnerability_count" in data[0]

    def test_list_users_as_regular_user_fails(self, client, auth_headers):
        """Test listing users as regular user fails"""
        response = client.get("/api/admin/users", headers=auth_headers)

        assert response.status_code == 403

    def test_list_users_unauthenticated_fails(self, client):
        """Test listing users without authentication fails"""
        response = client.get("/api/admin/users")

        assert response.status_code == 401

    def test_list_users_pagination(self, client, db_session, admin_user):
        """Test user list pagination"""
        # Login as admin
        admin_response = client.post(
            "/api/auth/login",
            data={"username": "admin", "password": "adminpass123"}
        )
        admin_token = admin_response.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        response = client.get("/api/admin/users?skip=0&limit=5", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 5

    def test_toggle_admin_status_success(self, client, db_session, admin_user, sample_user):
        """Test toggling admin status for a user"""
        # Login as admin
        admin_response = client.post(
            "/api/auth/login",
            data={"username": "admin", "password": "adminpass123"}
        )
        admin_token = admin_response.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        user_id = sample_user.id
        original_status = sample_user.is_admin

        response = client.put(f"/api/admin/users/{user_id}/admin", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["is_admin"] != original_status

    def test_toggle_own_admin_status_fails(self, client, db_session, admin_user):
        """Test that admin cannot toggle their own status"""
        # Login as admin
        admin_response = client.post(
            "/api/auth/login",
            data={"username": "admin", "password": "adminpass123"}
        )
        admin_token = admin_response.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        admin_id = admin_user.id

        response = client.put(f"/api/admin/users/{admin_id}/admin", headers=admin_headers)

        assert response.status_code == 403
        assert "Cannot modify your own" in response.json()["detail"]

    def test_toggle_admin_status_user_not_found(self, client, db_session, admin_user):
        """Test toggling admin status for non-existent user"""
        # Login as admin
        admin_response = client.post(
            "/api/auth/login",
            data={"username": "admin", "password": "adminpass123"}
        )
        admin_token = admin_response.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        response = client.put("/api/admin/users/999999/admin", headers=admin_headers)

        assert response.status_code == 404

    def test_toggle_admin_status_as_regular_user_fails(self, client, auth_headers, sample_user):
        """Test toggling admin status as regular user fails"""
        response = client.put(f"/api/admin/users/{sample_user.id}/admin", headers=auth_headers)

        assert response.status_code == 403

    def test_get_platform_statistics_as_admin(self, client, db_session, admin_user, sample_user,
                                             sample_system_config, sample_simulation_run,
                                             sample_community_vulnerability):
        """Test retrieving platform statistics as admin"""
        # Login as admin
        admin_response = client.post(
            "/api/auth/login",
            data={"username": "admin", "password": "adminpass123"}
        )
        admin_token = admin_response.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        response = client.get("/api/admin/stats", headers=admin_headers)

        assert response.status_code == 200
        data = response.json()

        # Check required fields
        assert "timestamp" in data
        assert "total_counts" in data
        assert "user_distribution" in data
        assert "vulnerability_status" in data
        assert "recent_activity_7d" in data
        assert "recent_activity_30d" in data
        assert "most_active_users" in data
        assert "top_contributors" in data

        # Check total counts
        assert data["total_counts"]["users"] >= 2
        assert data["total_counts"]["systems"] >= 1
        assert data["total_counts"]["simulations"] >= 1
        assert data["total_counts"]["vulnerabilities"] >= 1

        # Check user distribution
        assert data["user_distribution"]["admin_users"] >= 1
        assert data["user_distribution"]["regular_users"] >= 1

        # Check vulnerability status
        assert "unverified" in data["vulnerability_status"]
        assert "verified" in data["vulnerability_status"]
        assert "deprecated" in data["vulnerability_status"]

    def test_get_platform_statistics_as_regular_user_fails(self, client, auth_headers):
        """Test retrieving statistics as regular user fails"""
        response = client.get("/api/admin/stats", headers=auth_headers)

        assert response.status_code == 403

    def test_get_platform_statistics_unauthenticated_fails(self, client):
        """Test retrieving statistics without authentication fails"""
        response = client.get("/api/admin/stats")

        assert response.status_code == 401


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestPhase2Integration:
    """Integration tests combining multiple Phase 2 features"""

    def test_full_workflow_system_to_simulation(self, client, auth_headers):
        """Test complete workflow: create system -> run simulation -> get results"""
        # Step 1: Create system
        system_data = {
            "name": "Integration Test System",
            "config_json": json.dumps({
                "system_name": "Integration Test",
                "system_class": "Test Class",
                "subsystems": [
                    {
                        "id": "sub1",
                        "name": "Subsystem 1",
                        "connected_to": [],
                        "functional_dependencies": []
                    }
                ],
                "vulnerabilities": [
                    {
                        "cve_id": "CVE-2024-INT",
                        "description": "Integration test vulnerability",
                        "subsystem_id": "sub1",
                        "cvss_impact": 8.0,
                        "cvss_exploitability": 7.0,
                        "exploit_present": True,
                        "patch_cost": 12.0,
                        "dependencies": []
                    }
                ]
            })
        }
        system_response = client.post("/api/systems", json=system_data, headers=auth_headers)
        assert system_response.status_code == 201
        system_id = system_response.json()["id"]

        # Step 2: Run simulation
        sim_data = {
            "system_id": system_id,
            "rounds": 5,
            "defender_budget": 50.0
        }
        sim_response = client.post("/api/simulations", json=sim_data, headers=auth_headers)
        assert sim_response.status_code == 201
        simulation_id = sim_response.json()["simulation_id"]

        # Step 3: Wait briefly for background task
        time.sleep(2)

        # Step 4: Get simulation results
        results_response = client.get(f"/api/simulations/{simulation_id}", headers=auth_headers)
        assert results_response.status_code == 200

    def test_vulnerability_submission_and_verification_workflow(self, client, db_session, admin_user, auth_headers):
        """Test workflow: submit vulnerability -> verify as admin"""
        # Step 1: Submit vulnerability
        vuln_data = {
            "description": "Integration test vulnerability submission",
            "cvss_impact": 8.5,
            "cvss_exploitability": 7.5,
            "affected_subsystem_type": "web_server"
        }
        submit_response = client.post(
            "/api/vulnerabilities/community",
            json=vuln_data,
            headers=auth_headers
        )
        assert submit_response.status_code == 201
        comm_id = submit_response.json()["comm_id"]
        assert submit_response.json()["status"] == "UNVERIFIED"

        # Step 2: Login as admin
        admin_response = client.post(
            "/api/auth/login",
            data={"username": "admin", "password": "adminpass123"}
        )
        admin_token = admin_response.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        # Step 3: Verify vulnerability
        verify_response = client.put(
            f"/api/vulnerabilities/community/{comm_id}/verify",
            headers=admin_headers
        )
        assert verify_response.status_code == 200
        assert verify_response.json()["status"] == "VERIFIED"

        # Step 4: Check stats updated
        stats_response = client.get("/api/admin/stats", headers=admin_headers)
        assert stats_response.status_code == 200
        stats = stats_response.json()
        assert stats["vulnerability_status"]["verified"] >= 1
