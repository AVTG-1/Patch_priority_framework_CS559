"""
Tests for RiskCalculator class
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from data_model import (
    SystemClass, SystemInstance, Subsystem, Vulnerability,
    RiskCalculator
)


class TestRiskCalculator:
    """Test suite for RiskCalculator."""
    
    def create_test_system(self):
        """Create a test system with dependencies."""
        sub1 = Subsystem(
            id="sub1",
            name="Web Server",
            connected_ids=["sub2"],
            functional_deps=["sub2"]
        )
        
        sub2 = Subsystem(
            id="sub2",
            name="Database",
            connected_ids=["sub1"],
            functional_deps=[]
        )
        
        vuln1 = Vulnerability(
            cve_id="CVE-2024-0001",
            description="SQL Injection",
            cvss_impact=8.5,
            cvss_exploitability=7.8,
            exploit_present=True,
            patch_cost=10.0,
            subsystem_id="sub2"
        )
        sub2.add_vulnerability(vuln1)
        
        system_class = SystemClass(name="WebApp")
        system = SystemInstance(
            system_class=system_class,
            subsystems=[sub1, sub2]
        )
        
        return system
    
    def test_compute_importance(self):
        """Test importance score calculation."""
        system = self.create_test_system()
        calculator = RiskCalculator()
        
        importance = calculator.compute_importance(system)
        
        # Should return dictionary
        assert isinstance(importance, dict)
        assert len(importance) == 2
        
        # All scores should be between 0 and 1
        for score in importance.values():
            assert 0.0 <= score <= 1.0
        
        # Scores should sum to approximately 1
        total = sum(importance.values())
        assert abs(total - 1.0) < 0.01
    
    def test_importance_updates_subsystems(self):
        """Test that compute_importance updates subsystem objects."""
        system = self.create_test_system()
        calculator = RiskCalculator()
        
        # Initially zero
        assert system.subsystems[0].importance_score == 0.0
        
        calculator.compute_importance(system)
        
        # Should be updated
        assert system.subsystems[0].importance_score > 0.0
        assert system.subsystems[1].importance_score > 0.0
    
    def test_dependent_subsystem_importance(self):
        """Test that dependencies affect importance scores."""
        system = self.create_test_system()
        calculator = RiskCalculator()
        
        importance = calculator.compute_importance(system)
        
        # sub2 (Database) has no dependencies and is depended upon
        # It should have higher or equal importance
        assert importance["sub2"] >= importance["sub1"]
    
    def test_score_vulnerability(self):
        """Test vulnerability scoring."""
        system = self.create_test_system()
        calculator = RiskCalculator()
        calculator.compute_importance(system)
        
        vuln = system.subsystems[1].vulnerabilities[0]
        subsystem = system.subsystems[1]
        
        score = calculator.score_vulnerability(vuln, subsystem)
        
        assert score > 0.0
        assert isinstance(score, float)
    
    def test_exploit_increases_score(self):
        """Test that exploits increase risk score."""
        system = self.create_test_system()
        calculator = RiskCalculator()
        calculator.compute_importance(system)
        
        subsystem = system.subsystems[1]
        
        # Vulnerability with exploit
        vuln_with_exploit = Vulnerability(
            cve_id="CVE-2024-0010",
            description="Test",
            cvss_impact=7.0,
            cvss_exploitability=7.0,
            exploit_present=True,
            patch_cost=10.0,
            subsystem_id="sub2"
        )
        
        # Vulnerability without exploit
        vuln_without_exploit = Vulnerability(
            cve_id="CVE-2024-0011",
            description="Test",
            cvss_impact=7.0,
            cvss_exploitability=7.0,
            exploit_present=False,
            patch_cost=10.0,
            subsystem_id="sub2"
        )
        
        score_with = calculator.score_vulnerability(vuln_with_exploit, subsystem)
        score_without = calculator.score_vulnerability(vuln_without_exploit, subsystem)
        
        assert score_with > score_without
    
    def test_score_all_vulnerabilities(self):
        """Test scoring all vulnerabilities in system."""
        system = self.create_test_system()
        calculator = RiskCalculator()
        
        scores = calculator.score_all_vulnerabilities(system)
        
        assert isinstance(scores, dict)
        assert len(scores) == 1  # One vulnerability
        assert "CVE-2024-0001" in scores
    
    def test_rank_vulnerabilities(self):
        """Test vulnerability ranking."""
        system = self.create_test_system()
        
        # Add more vulnerabilities
        sub = system.subsystems[1]
        sub.add_vulnerability(Vulnerability(
            cve_id="CVE-2024-0002",
            description="Test",
            cvss_impact=5.0,
            cvss_exploitability=5.0,
            exploit_present=False,
            patch_cost=5.0,
            subsystem_id="sub2"
        ))
        
        calculator = RiskCalculator()
        ranked = calculator.rank_vulnerabilities(system)
        
        assert isinstance(ranked, list)
        assert len(ranked) == 2
        
        # Should be tuples of (cve_id, score)
        assert all(isinstance(item, tuple) and len(item) == 2 for item in ranked)
        
        # Should be sorted descending
        scores = [score for _, score in ranked]
        assert scores == sorted(scores, reverse=True)
    
    def test_calculate_patching_priority(self):
        """Test patch priority calculation."""
        system = self.create_test_system()
        calculator = RiskCalculator()
        
        patch_groups = system.create_patch_groups()
        priorities = calculator.calculate_patching_priority(patch_groups)
        
        assert isinstance(priorities, list)
        assert all(isinstance(gid, str) for gid in priorities)
    
    def test_patching_priority_with_budget(self):
        """Test patch priority with budget constraint."""
        system = self.create_test_system()
        calculator = RiskCalculator()
        
        patch_groups = system.create_patch_groups()
        
        # Set low budget
        priorities = calculator.calculate_patching_priority(
            patch_groups,
            budget_constraint=5.0
        )
        
        # Should return fewer groups due to budget
        assert len(priorities) <= len(patch_groups)
    
    def test_assess_system_risk(self):
        """Test comprehensive risk assessment."""
        system = self.create_test_system()
        calculator = RiskCalculator()
        
        assessment = calculator.assess_system_risk(system)
        
        # Check all required keys
        assert "total_vulnerabilities" in assessment
        assert "critical_vulnerabilities" in assessment
        assert "high_vulnerabilities" in assessment
        assert "exploitable_vulnerabilities" in assessment
        assert "total_patch_cost" in assessment
        assert "average_risk_score" in assessment
        assert "max_risk_score" in assessment
        assert "most_critical_subsystem" in assessment
        assert "subsystem_importance_scores" in assessment
        assert "top_10_vulnerabilities" in assessment
        
        # Check values
        assert assessment["total_vulnerabilities"] == 1
        assert assessment["exploitable_vulnerabilities"] == 1
        assert assessment["total_patch_cost"] == 10.0
    
    def test_empty_system(self):
        """Test handling of system with no vulnerabilities."""
        sub = Subsystem(id="sub1", name="Empty")
        system = SystemInstance(
            SystemClass(name="Empty"),
            [sub]
        )
        
        calculator = RiskCalculator()
        assessment = calculator.assess_system_risk(system)
        
        assert assessment["total_vulnerabilities"] == 0
        assert assessment["total_patch_cost"] == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
