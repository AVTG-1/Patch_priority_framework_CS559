"""
Tests for GameState class
"""

import pytest
import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from game_engine import GameState


class TestGameState:
    """Test suite for GameState."""
    
    @pytest.fixture
    def sample_export(self):
        """Load sample export from integration tests."""
        export_path = os.path.join(
            os.path.dirname(__file__),
            '..',
            'integration',
            'sample_export.json'
        )
        with open(export_path, 'r') as f:
            return json.load(f)
    
    def test_load_from_export(self, sample_export):
        """Test loading game state from export."""
        state = GameState.load_from_export(sample_export)
        
        assert state.system_name == "Industrial Control System"
        assert state.api_version == "1.0.0"
        assert len(state.subsystems) == 4
        assert len(state.patch_groups) == 4
        assert len(state.players) == 2
    
    def test_validate_export_missing_keys(self):
        """Test validation catches missing keys."""
        invalid_export = {
            'api_version': '1.0.0',
            'system_name': 'Test'
            # Missing other required keys
        }
        
        with pytest.raises(ValueError, match="missing required keys"):
            GameState.load_from_export(invalid_export)
    
    def test_validate_export_wrong_version(self, sample_export):
        """Test validation catches unsupported API version."""
        sample_export['api_version'] = '2.0.0'
        
        with pytest.raises(ValueError, match="Unsupported API version"):
            GameState.load_from_export(sample_export)
    
    def test_get_subsystem_count(self, sample_export):
        """Test getting subsystem count."""
        state = GameState.load_from_export(sample_export)
        assert state.get_subsystem_count() == 4
    
    def test_get_vulnerability_count(self, sample_export):
        """Test getting vulnerability count."""
        state = GameState.load_from_export(sample_export)
        assert state.get_vulnerability_count() == 5
    
    def test_get_players_by_role(self, sample_export):
        """Test filtering players by role."""
        state = GameState.load_from_export(sample_export)
        
        defenders = state.get_players_by_role("DEFENDER")
        attackers = state.get_players_by_role("ATTACKER")
        
        assert len(defenders) == 1
        assert len(attackers) == 1
        assert defenders[0]['role'] == "DEFENDER"
        assert attackers[0]['role'] == "ATTACKER"
    
    def test_get_patch_group(self, sample_export):
        """Test retrieving patch group by ID."""
        state = GameState.load_from_export(sample_export)
        
        group = state.get_patch_group("PG_0000")
        assert group is not None
        assert group['group_id'] == "PG_0000"
        
        # Non-existent group
        assert state.get_patch_group("NONEXISTENT") is None
    
    def test_get_vulnerability(self, sample_export):
        """Test retrieving vulnerability by CVE ID."""
        state = GameState.load_from_export(sample_export)
        
        vuln = state.get_vulnerability("CVE-2024-0001")
        assert vuln is not None
        assert vuln['cve_id'] == "CVE-2024-0001"
        
        # Non-existent CVE
        assert state.get_vulnerability("CVE-9999-9999") is None
    
    def test_apply_patches(self, sample_export):
        """Test applying patches."""
        state = GameState.load_from_export(sample_export)
        
        initial_count = state.get_vulnerability_count()
        state.apply_patches(["CVE-2024-0001"])
        
        assert len(state.patched_cves) == 1
        assert "CVE-2024-0001" in state.patched_cves
        assert state.get_vulnerability_count() == initial_count - 1
    
    def test_apply_patch_group(self, sample_export):
        """Test applying entire patch group."""
        state = GameState.load_from_export(sample_export)
        
        initial_count = state.get_vulnerability_count()
        
        # Apply first patch group (has 2 CVEs)
        state.apply_patch_group("PG_0000")
        
        assert len(state.patched_cves) == 2
        assert state.get_vulnerability_count() == initial_count - 2
    
    def test_exploit_vulnerabilities(self, sample_export):
        """Test marking vulnerabilities as exploited."""
        state = GameState.load_from_export(sample_export)
        
        state.exploit_vulnerabilities(["CVE-2024-0001"])
        
        assert len(state.exploited_cves) == 1
        assert "CVE-2024-0001" in state.exploited_cves
    
    def test_exploit_patched_vulnerability(self, sample_export):
        """Test that patched vulnerabilities cannot be exploited."""
        state = GameState.load_from_export(sample_export)
        
        # Patch first
        state.apply_patches(["CVE-2024-0001"])
        
        # Try to exploit (should not add to exploited set)
        state.exploit_vulnerabilities(["CVE-2024-0001"])
        
        assert "CVE-2024-0001" not in state.exploited_cves
    
    def test_calculate_remaining_impact(self, sample_export):
        """Test RIS calculation."""
        state = GameState.load_from_export(sample_export)
        
        initial_ris = state.calculate_remaining_impact()
        assert initial_ris > 0
        
        # Apply patches and check RIS decreases
        state.apply_patch_group("PG_0000")
        new_ris = state.calculate_remaining_impact()
        
        assert new_ris < initial_ris
    
    def test_is_vulnerability_patchable(self, sample_export):
        """Test checking if vulnerability is patchable."""
        state = GameState.load_from_export(sample_export)
        
        # CVE-2024-0001 has no dependencies, should be patchable
        assert state.is_vulnerability_patchable("CVE-2024-0001")
        
        # CVE-2024-0002 depends on CVE-2024-0001
        assert not state.is_vulnerability_patchable("CVE-2024-0002")
        
        # Patch dependency
        state.apply_patches(["CVE-2024-0001"])
        
        # Now CVE-2024-0002 should be patchable
        assert state.is_vulnerability_patchable("CVE-2024-0002")
    
    def test_get_patchable_vulnerabilities(self, sample_export):
        """Test getting list of patchable vulnerabilities."""
        state = GameState.load_from_export(sample_export)
        
        patchable = state.get_patchable_vulnerabilities()
        
        # Initially, only vulnerabilities without dependencies are patchable
        # CVE-2024-0002 depends on CVE-2024-0001, so should not be patchable initially
        cve_ids = [v['cve_id'] for v in patchable]
        assert "CVE-2024-0001" in cve_ids
        assert "CVE-2024-0003" in cve_ids
    
    def test_advance_round(self, sample_export):
        """Test advancing to next round."""
        state = GameState.load_from_export(sample_export)
        
        assert state.current_round == 0
        state.advance_round()
        assert state.current_round == 1
    
    def test_get_state_summary(self, sample_export):
        """Test getting state summary."""
        state = GameState.load_from_export(sample_export)
        
        summary = state.get_state_summary()
        
        assert 'round' in summary
        assert 'system_name' in summary
        assert 'remaining_vulnerabilities' in summary
        assert 'patched_vulnerabilities' in summary
        assert 'remaining_impact_score' in summary
        
        assert summary['system_name'] == "Industrial Control System"
        assert summary['remaining_vulnerabilities'] == 5
    
    def test_reset(self, sample_export):
        """Test resetting game state."""
        state = GameState.load_from_export(sample_export)
        
        # Make changes
        state.apply_patches(["CVE-2024-0001"])
        state.advance_round()
        state.exploit_vulnerabilities(["CVE-2024-0003"])
        
        assert len(state.patched_cves) > 0
        assert state.current_round > 0
        assert len(state.exploited_cves) > 0
        
        # Reset
        state.reset()
        
        assert len(state.patched_cves) == 0
        assert state.current_round == 0
        assert len(state.exploited_cves) == 0
        assert state.get_vulnerability_count() == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
