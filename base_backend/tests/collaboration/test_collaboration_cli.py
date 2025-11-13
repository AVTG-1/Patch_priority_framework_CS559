"""
Tests for Collaboration CLI
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

import pytest
import json
import tempfile
from collaboration_cli import CollaborationCLI
from collaboration.user import User
from collaboration.shared_vulnerability import SharedVulnerability
from data_model.system import SystemClass, SystemInstance
from data_model.subsystem import Subsystem
from data_model.vulnerability import Vulnerability


class TestCLIUserManagement:
    """Test CLI user management commands."""
    
    def setup_method(self):
        """Set up CLI instance for each test."""
        self.cli = CollaborationCLI()
    
    def test_user_create(self):
        """Test creating a user via CLI."""
        result = self.cli.user_create("user_001", "alice", "alice@example.com", "sys_001")
        assert result is True
        
        user = self.cli.user_manager.get("user_001")
        assert user is not None
        assert user.username == "alice"
    
    def test_user_create_duplicate_fails(self):
        """Test that creating duplicate user fails."""
        self.cli.user_create("user_001", "alice", "alice@example.com", "sys_001")
        result = self.cli.user_create("user_001", "bob", "bob@example.com", "sys_002")
        assert result is False
    
    def test_user_list_empty(self, capsys):
        """Test listing users when none exist."""
        self.cli.user_list()
        captured = capsys.readouterr()
        assert "No users found" in captured.out
    
    def test_user_list_with_users(self, capsys):
        """Test listing users."""
        self.cli.user_create("user_001", "alice", "alice@example.com", "sys_001")
        self.cli.user_create("user_002", "bob", "bob@example.com", "sys_002")
        
        self.cli.user_list()
        captured = capsys.readouterr()
        assert "alice" in captured.out
        assert "bob" in captured.out
    
    def test_user_list_with_pattern(self, capsys):
        """Test listing users with search pattern."""
        self.cli.user_create("user_001", "alice", "alice@example.com", "sys_001")
        self.cli.user_create("user_002", "bob", "bob@example.com", "sys_002")
        self.cli.user_create("user_003", "alice2", "alice2@example.com", "sys_003")
        
        capsys.readouterr()  # Clear previous output
        self.cli.user_list(pattern="alice")
        captured = capsys.readouterr()
        assert "alice" in captured.out
        assert "bob" not in captured.out
    
    def test_user_info_by_id(self, capsys):
        """Test getting user info by ID."""
        self.cli.user_create("user_001", "alice", "alice@example.com", "sys_001")
        
        result = self.cli.user_info("user_001")
        assert result is True
        captured = capsys.readouterr()
        assert "alice" in captured.out
        assert "sys_001" in captured.out
    
    def test_user_info_by_username(self, capsys):
        """Test getting user info by username."""
        self.cli.user_create("user_001", "alice", "alice@example.com", "sys_001")
        
        result = self.cli.user_info("alice")
        assert result is True
        captured = capsys.readouterr()
        assert "alice" in captured.out
    
    def test_user_info_by_email(self, capsys):
        """Test getting user info by email."""
        self.cli.user_create("user_001", "alice", "alice@example.com", "sys_001")
        
        result = self.cli.user_info("alice@example.com")
        assert result is True
        captured = capsys.readouterr()
        assert "alice" in captured.out
    
    def test_user_info_not_found(self):
        """Test user info when user doesn't exist."""
        result = self.cli.user_info("nonexistent")
        assert result is False
    
    def test_user_delete(self):
        """Test deleting a user."""
        self.cli.user_create("user_001", "alice", "alice@example.com", "sys_001")
        
        result = self.cli.user_delete("user_001")
        assert result is True
        assert self.cli.user_manager.get("user_001") is None
    
    def test_user_delete_not_found(self):
        """Test deleting nonexistent user."""
        result = self.cli.user_delete("nonexistent")
        assert result is False


class TestCLISystemManagement:
    """Test CLI system management commands."""
    
    def setup_method(self):
        """Set up CLI and test config file."""
        self.cli = CollaborationCLI()
        
        # Create a test configuration file
        config = {
            "system_name": "Test System",
            "subsystems": [
                {
                    "id": "web_001",
                    "name": "Web Server"
                }
            ],
            "vulnerabilities": [
                {
                    "cve_id": "CVE-2024-0001",
                    "subsystem_id": "web_001",
                    "cvss_impact": 7.5,
                    "cvss_exploitability": 8.0,
                    "patch_cost": 50.0
                }
            ]
        }
        
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        json.dump(config, self.temp_file)
        self.temp_file.close()
    
    def teardown_method(self):
        """Clean up temp file."""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
    
    def test_system_load(self, capsys):
        """Test loading a system from config file."""
        result = self.cli.system_load(self.temp_file.name)
        assert result is True
        captured = capsys.readouterr()
        assert "Test System" in captured.out
    
    def test_system_load_with_user(self, capsys):
        """Test loading system with user override."""
        result = self.cli.system_load(self.temp_file.name, user_id="user_001")
        assert result is True
        
        # System should be stored with user_001 as key
        system = self.cli.systems.get("user_001")
        assert system is not None
        assert system.owner_user_id == "user_001"
    
    def test_system_load_invalid_file(self):
        """Test loading from nonexistent file."""
        result = self.cli.system_load("/nonexistent/file.json")
        assert result is False
    
    def test_system_list_empty(self, capsys):
        """Test listing systems when none loaded."""
        self.cli.system_list()
        captured = capsys.readouterr()
        assert "No systems loaded" in captured.out
    
    def test_system_list_with_systems(self, capsys):
        """Test listing loaded systems."""
        self.cli.system_load(self.temp_file.name)
        
        self.cli.system_list()
        captured = capsys.readouterr()
        assert "Test System" in captured.out
    
    def test_system_info(self, capsys):
        """Test showing system info."""
        self.cli.system_load(self.temp_file.name, user_id="sys_001")
        
        result = self.cli.system_info("sys_001")
        assert result is True
        captured = capsys.readouterr()
        assert "Test System" in captured.out
        assert "Web Server" in captured.out
    
    def test_system_info_not_found(self):
        """Test system info when system doesn't exist."""
        result = self.cli.system_info("nonexistent")
        assert result is False


class TestCLIVulnerabilitySharing:
    """Test CLI vulnerability sharing commands."""
    
    def setup_method(self):
        """Set up CLI with test data."""
        self.cli = CollaborationCLI()
        
        # Create user
        self.cli.user_create("user_001", "alice", "alice@example.com", "sys_001")
        
        # Create system manually
        sys_class = SystemClass(name="Alice's System")
        subsystem = Subsystem(
            id="web_001",
            name="Web Server",
            importance_score=0.8,
            vulnerabilities=[]
        )
        vuln = Vulnerability(
            cve_id="CVE-2024-0001",
            description="Test vulnerability",
            cvss_impact=8.5,
            cvss_exploitability=7.5,
            exploit_present=False,
            patch_cost=75.0,
            subsystem_id="web_001",
            source="CUSTOM"
        )
        subsystem.add_vulnerability(vuln)
        
        system = SystemInstance(
            system_class=sys_class,
            subsystems=[subsystem],
            owner_user_id="user_001"
        )
        self.cli.systems["sys_001"] = system
    
    def test_publish_vulnerability(self, capsys):
        """Test publishing a vulnerability."""
        result = self.cli.publish("sys_001", "CVE-2024-0001", "web_server")
        assert result is True
        
        # Verify it's in repository
        results = self.cli.repo.search(cve_prefix="CVE-2024")
        assert len(results) == 1
        captured = capsys.readouterr()
        assert "Published" in captured.out
    
    def test_publish_with_metrics(self, capsys):
        """Test publishing with game theory metrics."""
        metrics_json = '{"nash": 0.75, "ris_reduction": 35.5}'
        result = self.cli.publish("sys_001", "CVE-2024-0001", "web_server", metrics=metrics_json)
        assert result is True
        
        # Verify metrics stored
        results = self.cli.repo.search(cve_prefix="CVE-2024")
        assert len(results) == 1
        assert results[0].game_theory_metrics["nash"] == 0.75
    
    def test_publish_system_not_found(self):
        """Test publishing when system doesn't exist."""
        result = self.cli.publish("nonexistent", "CVE-2024-0001", "web_server")
        assert result is False
    
    def test_publish_vulnerability_not_found(self):
        """Test publishing when vulnerability doesn't exist in system."""
        result = self.cli.publish("sys_001", "CVE-9999-9999", "web_server")
        assert result is False
    
    def test_publish_system_no_owner(self):
        """Test publishing when system has no owner."""
        # Create system without owner
        sys_class = SystemClass(name="No Owner System")
        subsystem = Subsystem(id="web_001", name="Web", importance_score=0.8, vulnerabilities=[])
        system = SystemInstance(sys_class, [subsystem])
        self.cli.systems["no_owner"] = system
        
        result = self.cli.publish("no_owner", "CVE-2024-0001", "web_server")
        assert result is False
    
    def test_search_empty(self, capsys):
        """Test searching when repository is empty."""
        self.cli.search()
        captured = capsys.readouterr()
        assert "No vulnerabilities found" in captured.out
    
    def test_search_all(self, capsys):
        """Test searching all vulnerabilities."""
        # Publish first
        self.cli.publish("sys_001", "CVE-2024-0001", "web_server")
        
        self.cli.search()
        captured = capsys.readouterr()
        assert "CVE-2024-0001" in captured.out
        assert "user_001" in captured.out
    
    def test_search_by_author(self, capsys):
        """Test searching by author."""
        self.cli.publish("sys_001", "CVE-2024-0001", "web_server")
        
        self.cli.search(author="user_001")
        captured = capsys.readouterr()
        assert "CVE-2024-0001" in captured.out
    
    def test_search_by_subsystem_type(self, capsys):
        """Test searching by subsystem type."""
        self.cli.publish("sys_001", "CVE-2024-0001", "web_server")
        
        self.cli.search(subsystem_type="web_server")
        captured = capsys.readouterr()
        assert "CVE-2024-0001" in captured.out
    
    def test_import_vulnerability(self, capsys):
        """Test importing a vulnerability."""
        # Publish first
        self.cli.publish("sys_001", "CVE-2024-0001", "web_server")
        
        # Get shared ID
        results = self.cli.repo.list_all()
        shared_id = results[0].shared_vuln_id
        
        # Create another system
        sys_class = SystemClass(name="Bob's System")
        subsystem = Subsystem(id="web_002", name="Web App", importance_score=0.8, vulnerabilities=[])
        system = SystemInstance(sys_class, [subsystem], owner_user_id="user_002")
        self.cli.systems["sys_002"] = system
        
        # Import
        result = self.cli.import_vuln("sys_002", shared_id, "web_002")
        assert result is True
        
        # Verify imported
        imported_vulns = system.get_all_vulnerabilities()
        assert len(imported_vulns) == 1
        assert imported_vulns[0].source == "SHARED"
        captured = capsys.readouterr()
        assert "Imported" in captured.out
    
    def test_import_system_not_found(self):
        """Test importing when system doesn't exist."""
        result = self.cli.import_vuln("nonexistent", "SHARED-001", "web_001")
        assert result is False
    
    def test_import_vulnerability_not_found(self):
        """Test importing when vulnerability doesn't exist."""
        result = self.cli.import_vuln("sys_001", "SHARED-999", "web_001")
        assert result is False
    
    def test_vote_up(self, capsys):
        """Test upvoting a vulnerability."""
        # Publish first
        self.cli.publish("sys_001", "CVE-2024-0001", "web_server")
        
        results = self.cli.repo.list_all()
        shared_id = results[0].shared_vuln_id
        
        result = self.cli.vote(shared_id, "up")
        assert result is True
        
        # Verify vote count
        vuln = self.cli.repo.get(shared_id)
        assert vuln.votes == 1
        captured = capsys.readouterr()
        assert "Voted up" in captured.out
    
    def test_vote_down(self, capsys):
        """Test downvoting a vulnerability."""
        self.cli.publish("sys_001", "CVE-2024-0001", "web_server")
        
        results = self.cli.repo.list_all()
        shared_id = results[0].shared_vuln_id
        
        result = self.cli.vote(shared_id, "down")
        assert result is True
        
        vuln = self.cli.repo.get(shared_id)
        assert vuln.votes == -1
    
    def test_vote_invalid_direction(self):
        """Test voting with invalid direction."""
        result = self.cli.vote("SHARED-001", "invalid")
        assert result is False
    
    def test_vote_not_found(self):
        """Test voting on nonexistent vulnerability."""
        result = self.cli.vote("SHARED-999", "up")
        assert result is False


class TestCLIStatistics:
    """Test CLI statistics commands."""
    
    def setup_method(self):
        """Set up CLI with test data."""
        self.cli = CollaborationCLI()
        
        # Create user and system
        self.cli.user_create("user_001", "alice", "alice@example.com", "sys_001")
        
        sys_class = SystemClass(name="Test System")
        subsystem = Subsystem(id="web_001", name="Web", importance_score=0.8, vulnerabilities=[])
        
        for i in range(3):
            vuln = Vulnerability(
                cve_id=f"CVE-2024-000{i+1}",
                description=f"Vuln {i+1}",
                cvss_impact=7.5 + i,
                cvss_exploitability=8.0,
                exploit_present=False,
                patch_cost=50.0,
                subsystem_id="web_001",
                source="CUSTOM"
            )
            subsystem.add_vulnerability(vuln)
        
        system = SystemInstance(sys_class, [subsystem], owner_user_id="user_001")
        self.cli.systems["sys_001"] = system
        
        # Publish all
        for i in range(3):
            self.cli.publish("sys_001", f"CVE-2024-000{i+1}", "web_server")
    
    def test_stats_repo(self, capsys):
        """Test repository statistics."""
        self.cli.stats_repo()
        captured = capsys.readouterr()
        assert "Total vulnerabilities: 3" in captured.out
        assert "CVE-*" in captured.out
    
    def test_stats_repo_empty(self, capsys):
        """Test repository stats when empty."""
        cli = CollaborationCLI()
        cli.stats_repo()
        captured = capsys.readouterr()
        assert "Total vulnerabilities: 0" in captured.out
    
    def test_stats_user(self, capsys):
        """Test user statistics."""
        result = self.cli.stats_user("user_001")
        assert result is True
        captured = capsys.readouterr()
        assert "alice" in captured.out
        assert "Published vulnerabilities: 3" in captured.out
    
    def test_stats_user_not_found(self):
        """Test user stats when user doesn't exist."""
        result = self.cli.stats_user("nonexistent")
        assert result is False


class TestCLIIntegration:
    """Test complete CLI workflows."""
    
    def test_complete_workflow(self, capsys):
        """Test complete workflow: create users, load systems, publish, search, import."""
        cli = CollaborationCLI()
        
        # Create two users
        cli.user_create("user_001", "alice", "alice@example.com", "sys_001")
        cli.user_create("user_002", "bob", "bob@example.com", "sys_002")
        
        # Create systems manually
        for user_id, sys_id in [("user_001", "sys_001"), ("user_002", "sys_002")]:
            sys_class = SystemClass(name=f"{user_id}'s System")
            subsystem = Subsystem(id="web_001", name="Web", importance_score=0.8, vulnerabilities=[])
            
            if user_id == "user_001":
                vuln = Vulnerability(
                    cve_id="CUSTOM-2024-0001",
                    description="Alice's discovery",
                    cvss_impact=8.5,
                    cvss_exploitability=7.5,
                    exploit_present=False,
                    patch_cost=75.0,
                    subsystem_id="web_001",
                    source="CUSTOM"
                )
                subsystem.add_vulnerability(vuln)
            
            system = SystemInstance(sys_class, [subsystem], owner_user_id=user_id)
            cli.systems[sys_id] = system
        
        # Alice publishes
        result = cli.publish("sys_001", "CUSTOM-2024-0001", "web_server",
                           metrics='{"nash": 0.75}')
        assert result is True
        
        # Bob searches
        cli.search(subsystem_type="web_server")
        captured = capsys.readouterr()
        assert "CUSTOM-2024-0001" in captured.out
        
        # Bob votes
        shared_id = cli.repo.list_all()[0].shared_vuln_id
        cli.vote(shared_id, "up")
        
        # Bob imports
        result = cli.import_vuln("sys_002", shared_id, "web_001")
        assert result is True
        
        # Check stats
        cli.stats_user("user_001")
        captured = capsys.readouterr()
        assert "Published vulnerabilities: 1" in captured.out
        assert "Total votes received: 1" in captured.out
