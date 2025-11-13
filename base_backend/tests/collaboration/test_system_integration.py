"""
Tests for System Integration with Collaboration Features
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

import pytest
from data_model.system import SystemClass, SystemInstance
from data_model.subsystem import Subsystem
from data_model.vulnerability import Vulnerability
from collaboration.shared_vulnerability import SharedVulnerability
from collaboration.user import User
from collaboration.user_manager import UserManager
from collaboration.vulnerability_repository import VulnerabilityRepository


class TestSystemOwnership:
    """Test system ownership functionality."""
    
    def test_create_system_with_owner(self):
        """Test creating system with owner_user_id."""
        sys_class = SystemClass(name="Test System")
        subsystem = Subsystem(
            id="sub_001",
            name="Web Server",
            importance_score=0.8,
            vulnerabilities=[]
        )
        
        system = SystemInstance(
            system_class=sys_class,
            subsystems=[subsystem],
            owner_user_id="user_001"
        )
        
        assert system.owner_user_id == "user_001"
    
    def test_create_system_without_owner(self):
        """Test creating system without owner (None)."""
        sys_class = SystemClass(name="Test System")
        subsystem = Subsystem(
            id="sub_001",
            name="Web Server",
            importance_score=0.8,
            vulnerabilities=[]
        )
        
        system = SystemInstance(
            system_class=sys_class,
            subsystems=[subsystem]
        )
        
        assert system.owner_user_id is None


class TestImportSharedVulnerability:
    """Test importing shared vulnerabilities into systems."""
    
    def setup_method(self):
        """Set up test system and shared vulnerability."""
        self.sys_class = SystemClass(name="Test System")
        self.subsystem = Subsystem(
            id="web_001",
            name="Web Server",
            importance_score=0.8,
            vulnerabilities=[]
        )
        self.system = SystemInstance(
            system_class=self.sys_class,
            subsystems=[self.subsystem],
            owner_user_id="user_001"
        )
        
        self.shared_vuln = SharedVulnerability(
            shared_vuln_id="SHARED-001",
            author_user_id="user_002",
            cve_id="CVE-2024-0001",
            description="Critical RCE vulnerability",
            subsystem_type="web_server",
            cvss_impact=9.0,
            cvss_exploitability=8.5,
            patch_cost=100.0,
            game_theory_metrics={"nash": 0.85, "ris_reduction": 45.2},
            votes=15
        )
    
    def test_import_shared_vulnerability_basic(self):
        """Test basic import of shared vulnerability."""
        vuln = self.system.import_shared_vulnerability(
            self.shared_vuln,
            "web_001"
        )
        
        assert vuln.cve_id == "CVE-2024-0001"
        assert vuln.description == "Critical RCE vulnerability"
        assert vuln.cvss_impact == 9.0
        assert vuln.cvss_exploitability == 8.5
        assert vuln.patch_cost == 100.0
        assert vuln.subsystem_id == "web_001"
        assert vuln.source == "SHARED"
        assert vuln.shared_vuln_id == "SHARED-001"
    
    def test_import_adds_to_subsystem(self):
        """Test that import actually adds vulnerability to subsystem."""
        initial_count = self.subsystem.get_vulnerability_count()
        
        self.system.import_shared_vulnerability(
            self.shared_vuln,
            "web_001"
        )
        
        assert self.subsystem.get_vulnerability_count() == initial_count + 1
        assert self.system.get_total_vulnerability_count() == initial_count + 1
    
    def test_import_to_nonexistent_subsystem_raises_error(self):
        """Test that importing to nonexistent subsystem raises ValueError."""
        with pytest.raises(ValueError, match="not found"):
            self.system.import_shared_vulnerability(
                self.shared_vuln,
                "nonexistent_subsystem"
            )
    
    def test_import_multiple_shared_vulnerabilities(self):
        """Test importing multiple shared vulnerabilities."""
        shared_vuln2 = SharedVulnerability(
            shared_vuln_id="SHARED-002",
            author_user_id="user_003",
            cve_id="CVE-2024-0002",
            description="SQL injection",
            subsystem_type="web_server",
            cvss_impact=7.5,
            cvss_exploitability=6.0,
            patch_cost=50.0
        )
        
        vuln1 = self.system.import_shared_vulnerability(self.shared_vuln, "web_001")
        vuln2 = self.system.import_shared_vulnerability(shared_vuln2, "web_001")
        
        assert self.subsystem.get_vulnerability_count() == 2
        assert vuln1.shared_vuln_id == "SHARED-001"
        assert vuln2.shared_vuln_id == "SHARED-002"
    
    def test_import_custom_cve(self):
        """Test importing vulnerability with CUSTOM- CVE ID."""
        custom_vuln = SharedVulnerability(
            shared_vuln_id="SHARED-003",
            author_user_id="user_004",
            cve_id="CUSTOM-2024-0001",
            description="Custom discovered vulnerability",
            subsystem_type="web_server",
            cvss_impact=8.0,
            cvss_exploitability=7.5,
            patch_cost=75.0
        )
        
        vuln = self.system.import_shared_vulnerability(custom_vuln, "web_001")
        
        assert vuln.cve_id == "CUSTOM-2024-0001"
        assert vuln.source == "SHARED"


class TestCollaborationWorkflow:
    """Test complete collaboration workflow."""
    
    def setup_method(self):
        """Set up users, systems, and repository."""
        # Create user manager and users
        self.user_manager = UserManager()
        self.user1 = User("user_001", "alice", "alice@example.com", "sys_001")
        self.user2 = User("user_002", "bob", "bob@example.com", "sys_002")
        self.user_manager.create_user(self.user1)
        self.user_manager.create_user(self.user2)
        
        # Create repository
        self.repo = VulnerabilityRepository()
        
        # Create alice's system with a vulnerability
        sys_class1 = SystemClass(name="Alice's System")
        subsystem1 = Subsystem(
            id="web_001",
            name="Web Server",
            importance_score=0.9,
            vulnerabilities=[]
        )
        vuln1 = Vulnerability(
            cve_id="CUSTOM-2024-0001",
            description="Alice discovered this",
            cvss_impact=8.5,
            cvss_exploitability=7.5,
            exploit_present=False,
            patch_cost=75.0,
            subsystem_id="web_001",
            source="CUSTOM"
        )
        subsystem1.add_vulnerability(vuln1)
        
        self.alice_system = SystemInstance(
            system_class=sys_class1,
            subsystems=[subsystem1],
            owner_user_id="user_001"
        )
        
        # Create bob's system (empty initially)
        sys_class2 = SystemClass(name="Bob's System")
        subsystem2 = Subsystem(
            id="web_001",
            name="Web Application",
            importance_score=0.8,
            vulnerabilities=[]
        )
        self.bob_system = SystemInstance(
            system_class=sys_class2,
            subsystems=[subsystem2],
            owner_user_id="user_002"
        )
    
    def test_publish_discover_import_workflow(self):
        """Test complete workflow: publish -> discover -> import."""
        # Alice publishes her custom vulnerability
        alice_vuln = self.alice_system.get_all_vulnerabilities()[0]
        shared_data = alice_vuln.to_shared(
            author_user_id="user_001",
            subsystem_type="web_server",
            game_theory_metrics={"nash": 0.75, "ris_reduction": 30.0}
        )
        shared_vuln = SharedVulnerability.from_dict(shared_data)
        self.repo.add(shared_vuln)
        
        # Bob discovers it by searching
        results = self.repo.search(subsystem_type="web_server")
        assert len(results) == 1
        discovered_vuln = results[0]
        assert discovered_vuln.author_user_id == "user_001"
        assert discovered_vuln.cve_id == "CUSTOM-2024-0001"
        
        # Bob imports it into his system
        initial_count = self.bob_system.get_total_vulnerability_count()
        imported_vuln = self.bob_system.import_shared_vulnerability(
            discovered_vuln,
            "web_001"
        )
        
        assert self.bob_system.get_total_vulnerability_count() == initial_count + 1
        assert imported_vuln.source == "SHARED"
        assert imported_vuln.shared_vuln_id == discovered_vuln.shared_vuln_id
        assert imported_vuln.cve_id == "CUSTOM-2024-0001"
    
    def test_voting_on_shared_vulnerabilities(self):
        """Test voting mechanism on shared vulnerabilities."""
        # Alice publishes
        alice_vuln = self.alice_system.get_all_vulnerabilities()[0]
        shared_data = alice_vuln.to_shared(
            author_user_id="user_001",
            subsystem_type="web_server"
        )
        shared_vuln = SharedVulnerability.from_dict(shared_data)
        self.repo.add(shared_vuln)
        
        # Bob finds and upvotes it
        found_vuln = self.repo.get(shared_vuln.shared_vuln_id)
        assert found_vuln.votes == 0
        
        self.repo.upvote(shared_vuln.shared_vuln_id)
        assert found_vuln.votes == 1
        
        # After upvoting, Bob imports it
        imported_vuln = self.bob_system.import_shared_vulnerability(
            found_vuln,
            "web_001"
        )
        assert imported_vuln is not None
    
    def test_multiple_users_same_vulnerability(self):
        """Test multiple users publishing same CVE with different analyses."""
        # Alice publishes her analysis
        alice_vuln = self.alice_system.get_all_vulnerabilities()[0]
        shared_data1 = alice_vuln.to_shared(
            author_user_id="user_001",
            subsystem_type="web_server",
            game_theory_metrics={"nash": 0.75}
        )
        shared_vuln1 = SharedVulnerability.from_dict(shared_data1)
        self.repo.add(shared_vuln1)
        
        # Bob also discovers same CVE and publishes his analysis
        bob_vuln = Vulnerability(
            cve_id="CUSTOM-2024-0001",  # Same CVE
            description="Bob's analysis",
            cvss_impact=8.0,  # Different scores
            cvss_exploitability=8.0,
            exploit_present=True,
            patch_cost=50.0,  # Different cost
            subsystem_id="web_001",
            source="CUSTOM"
        )
        shared_data2 = bob_vuln.to_shared(
            author_user_id="user_002",
            subsystem_type="web_application",
            game_theory_metrics={"nash": 0.80}
        )
        shared_vuln2 = SharedVulnerability.from_dict(shared_data2)
        self.repo.add(shared_vuln2)
        
        # Search should find both versions
        results = self.repo.get_by_cve_id("CUSTOM-2024-0001")
        assert len(results) == 2
        authors = {r.author_user_id for r in results}
        assert authors == {"user_001", "user_002"}


class TestSystemWithMixedVulnerabilitySources:
    """Test systems containing vulnerabilities from multiple sources."""
    
    def test_system_with_nvd_and_shared_vulnerabilities(self):
        """Test system containing both NVD and SHARED vulnerabilities."""
        sys_class = SystemClass(name="Mixed System")
        subsystem = Subsystem(
            id="web_001",
            name="Web Server",
            importance_score=0.8,
            vulnerabilities=[]
        )
        
        # Add NVD vulnerability
        nvd_vuln = Vulnerability(
            cve_id="CVE-2024-0001",
            description="From NVD",
            cvss_impact=7.5,
            cvss_exploitability=8.0,
            exploit_present=True,
            patch_cost=50.0,
            subsystem_id="web_001",
            source="NVD"
        )
        subsystem.add_vulnerability(nvd_vuln)
        
        system = SystemInstance(
            system_class=sys_class,
            subsystems=[subsystem],
            owner_user_id="user_001"
        )
        
        # Import shared vulnerability
        shared_vuln = SharedVulnerability(
            shared_vuln_id="SHARED-001",
            author_user_id="user_002",
            cve_id="CVE-2024-0002",
            description="From collaboration",
            subsystem_type="web_server",
            cvss_impact=8.5,
            cvss_exploitability=7.5,
            patch_cost=75.0
        )
        system.import_shared_vulnerability(shared_vuln, "web_001")
        
        # Check both are present
        all_vulns = system.get_all_vulnerabilities()
        assert len(all_vulns) == 2
        
        sources = {v.source for v in all_vulns}
        assert sources == {"NVD", "SHARED"}
    
    def test_export_preserves_source_information(self):
        """Test that export_for_game preserves source field."""
        sys_class = SystemClass(name="Test System")
        subsystem = Subsystem(
            id="web_001",
            name="Web Server",
            importance_score=0.8,
            vulnerabilities=[]
        )
        
        shared_vuln = SharedVulnerability(
            shared_vuln_id="SHARED-001",
            author_user_id="user_001",
            cve_id="CVE-2024-0001",
            description="Shared vulnerability",
            subsystem_type="web_server",
            cvss_impact=8.0,
            cvss_exploitability=7.5,
            patch_cost=60.0
        )
        
        system = SystemInstance(
            system_class=sys_class,
            subsystems=[subsystem],
            owner_user_id="user_001"
        )
        
        system.import_shared_vulnerability(shared_vuln, "web_001")
        
        # Export and check
        export_data = system.export_for_game()
        subsystem_data = export_data["subsystems"][0]
        vuln_data = subsystem_data["vulnerabilities"][0]
        
        assert vuln_data["source"] == "SHARED"
        assert vuln_data["shared_vuln_id"] == "SHARED-001"
