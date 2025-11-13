"""
Tests for SystemInstance export_for_game() method
"""

import pytest
import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from data_model import (
    SystemClass, SystemInstance, Subsystem, Vulnerability,
    PlayerBase, RiskCalculator
)


class TestSystemExport:
    """Test suite for SystemInstance.export_for_game() method."""
    
    def create_test_system(self):
        """Create a simple test system."""
        # Create subsystems
        sub1 = Subsystem(
            id="sub_001",
            name="Web Server",
            connected_ids=["sub_002"],
            functional_deps=["sub_002"]
        )
        
        sub2 = Subsystem(
            id="sub_002",
            name="Database",
            connected_ids=["sub_001"],
            functional_deps=[]
        )
        
        # Add vulnerabilities
        vuln1 = Vulnerability(
            cve_id="CVE-2024-0001",
            description="SQL Injection",
            cvss_impact=8.5,
            cvss_exploitability=7.8,
            exploit_present=True,
            patch_cost=10.0,
            subsystem_id="sub_002"
        )
        sub2.add_vulnerability(vuln1)
        
        # Create system
        system_class = SystemClass(name="WebApp")
        system = SystemInstance(
            system_class=system_class,
            subsystems=[sub1, sub2]
        )
        
        return system
    
    def test_export_basic_structure(self):
        """Test that export contains all required keys."""
        system = self.create_test_system()
        export = system.export_for_game()
        
        # Check all required keys from contract
        assert "api_version" in export
        assert "system_name" in export
        assert "subsystems" in export
        assert "functional_dependencies" in export
        assert "network_topology" in export
        assert "weights" in export
        assert "patch_groups" in export
        assert "players" in export
    
    def test_api_version(self):
        """Test that API version is correct."""
        system = self.create_test_system()
        export = system.export_for_game()
        
        assert export["api_version"] == "1.0.0"
    
    def test_subsystems_export(self):
        """Test subsystem export format."""
        system = self.create_test_system()
        export = system.export_for_game()
        
        subsystems = export["subsystems"]
        assert len(subsystems) == 2
        
        # Check subsystem structure
        for sub in subsystems:
            assert "id" in sub
            assert "name" in sub
            assert "importance_score" in sub
            assert "vulnerabilities" in sub
            assert isinstance(sub["vulnerabilities"], list)
    
    def test_vulnerability_export(self):
        """Test that vulnerabilities are properly exported."""
        system = self.create_test_system()
        export = system.export_for_game()
        
        # Find database subsystem
        db_sub = next(s for s in export["subsystems"] if s["id"] == "sub_002")
        vulns = db_sub["vulnerabilities"]
        
        assert len(vulns) == 1
        vuln = vulns[0]
        
        # Check vulnerability structure
        assert vuln["cve_id"] == "CVE-2024-0001"
        assert vuln["description"] == "SQL Injection"
        assert vuln["cvss_impact"] == 8.5
        assert vuln["cvss_exploitability"] == 7.8
        assert vuln["exploit_present"] is True
        assert vuln["patch_cost"] == 10.0
        assert vuln["dependencies"] == []
    
    def test_matrix_dimensions(self):
        """Test that dependency matrices have correct dimensions."""
        system = self.create_test_system()
        export = system.export_for_game()
        
        n = len(export["subsystems"])
        
        func_deps = export["functional_dependencies"]
        net_topo = export["network_topology"]
        
        assert len(func_deps) == n
        assert len(net_topo) == n
        
        for row in func_deps:
            assert len(row) == n
        
        for row in net_topo:
            assert len(row) == n
    
    def test_functional_dependencies(self):
        """Test functional dependency matrix construction."""
        system = self.create_test_system()
        export = system.export_for_game()
        
        # sub_001 depends on sub_002
        # sub_002 depends on nothing
        func_deps = export["functional_dependencies"]
        
        # Row 0 (sub_001), Column 1 (sub_002) should be 1
        assert func_deps[0][1] == 1
        # Row 1 (sub_002) should be all zeros
        assert all(x == 0 for x in func_deps[1])
    
    def test_network_topology(self):
        """Test network topology matrix construction."""
        system = self.create_test_system()
        export = system.export_for_game()
        
        # sub_001 and sub_002 are connected
        net_topo = export["network_topology"]
        
        # Should be symmetric
        assert net_topo[0][1] == 1
        assert net_topo[1][0] == 1
    
    def test_weights_export(self):
        """Test weight configuration export."""
        system = self.create_test_system()
        export = system.export_for_game()
        
        weights = export["weights"]
        assert "functional_weight" in weights
        assert "topological_weight" in weights
        assert isinstance(weights["functional_weight"], float)
        assert isinstance(weights["topological_weight"], float)
    
    def test_patch_groups_export(self):
        """Test patch group export."""
        system = self.create_test_system()
        export = system.export_for_game()
        
        patch_groups = export["patch_groups"]
        assert isinstance(patch_groups, list)
        assert len(patch_groups) > 0
        
        # Check patch group structure
        for pg in patch_groups:
            assert "group_id" in pg
            assert "cve_ids" in pg
            assert "total_cost" in pg
            assert "aggregate_impact" in pg
    
    def test_players_export(self):
        """Test player export."""
        system = self.create_test_system()
        
        # Create custom players
        defender = PlayerBase.create_defender("def_1", 100.0)
        attacker = PlayerBase.create_attacker("att_1", 50.0)
        
        export = system.export_for_game(players=[defender, attacker])
        
        players = export["players"]
        assert len(players) == 2
        
        # Check player structure
        for player in players:
            assert "player_id" in player
            assert "role" in player
            assert "resource_budget" in player
            assert player["role"] in ["ATTACKER", "DEFENDER"]
    
    def test_default_player_creation(self):
        """Test that default player is created if none provided."""
        system = self.create_test_system()
        export = system.export_for_game()
        
        players = export["players"]
        assert len(players) == 1
        assert players[0]["role"] == "DEFENDER"
        assert players[0]["player_id"] == "default_defender"
    
    def test_json_serializable(self):
        """Test that export is JSON-serializable."""
        system = self.create_test_system()
        export = system.export_for_game()
        
        # Should not raise exception
        json_str = json.dumps(export)
        assert isinstance(json_str, str)
        
        # Should be able to load back
        loaded = json.loads(json_str)
        assert loaded["system_name"] == export["system_name"]
    
    def test_importance_scores_calculated(self):
        """Test that importance scores are included in export."""
        system = self.create_test_system()
        
        # Calculate importance
        calculator = RiskCalculator()
        calculator.compute_importance(system)
        
        export = system.export_for_game()
        
        # Check that all subsystems have importance scores
        for sub in export["subsystems"]:
            assert sub["importance_score"] >= 0.0
            assert sub["importance_score"] <= 1.0
    
    def test_patch_grouping_methods(self):
        """Test different patch grouping methods."""
        system = self.create_test_system()
        
        # Test dependencies method
        export1 = system.export_for_game(patch_grouping_method="dependencies")
        assert "patch_groups" in export1
        
        # Test subsystem method
        export2 = system.export_for_game(patch_grouping_method="subsystem")
        assert "patch_groups" in export2
        
        # Test severity method
        export3 = system.export_for_game(patch_grouping_method="severity")
        assert "patch_groups" in export3
    
    def test_export_consistency(self):
        """Test that multiple exports produce consistent results."""
        system = self.create_test_system()
        
        export1 = system.export_for_game()
        export2 = system.export_for_game()
        
        # Compare key elements
        assert export1["system_name"] == export2["system_name"]
        assert len(export1["subsystems"]) == len(export2["subsystems"])
        assert export1["functional_dependencies"] == export2["functional_dependencies"]
        assert export1["network_topology"] == export2["network_topology"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
