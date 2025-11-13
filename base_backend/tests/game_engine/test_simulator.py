"""
Tests for Simulator
"""

import pytest
import sys
import os
import json
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from game_engine import GameState, Simulator, SimulationResult


class TestSimulator:
    """Test suite for Simulator."""
    
    @pytest.fixture
    def game_state(self):
        """Create game state from sample export."""
        export_path = os.path.join(
            os.path.dirname(__file__),
            '..',
            'integration',
            'sample_export.json'
        )
        with open(export_path, 'r') as f:
            export_dict = json.load(f)
        
        return GameState.load_from_export(export_dict)
    
    def test_create_simulator(self, game_state):
        """Test creating simulator."""
        simulator = Simulator(game_state, simulation_length=5)
        
        assert simulator.simulation_length == 5
        assert simulator.discount_factor == 0.9
        assert simulator.game_state == game_state
    
    def test_invalid_simulation_length(self, game_state):
        """Test that simulation length must be positive."""
        with pytest.raises(ValueError, match="must be positive"):
            Simulator(game_state, simulation_length=0)
    
    def test_invalid_discount_factor(self, game_state):
        """Test that discount factor must be in [0, 1]."""
        with pytest.raises(ValueError, match="must be in"):
            Simulator(game_state, discount_factor=1.5)
    
    def test_run_round(self, game_state):
        """Test running single round."""
        simulator = Simulator(game_state, simulation_length=5)
        
        result = simulator.run_round()
        
        assert 'round' in result
        assert 'initial_ris' in result
        assert 'final_ris' in result
        assert 'patches_applied' in result
        assert 'vulnerabilities_exploited' in result
        assert isinstance(result['patches_applied'], list)
    
    def test_run_simulation(self, game_state):
        """Test running complete simulation."""
        simulator = Simulator(game_state, simulation_length=3)
        
        results = simulator.run_simulation()
        
        assert 'total_rounds' in results
        assert 'initial_ris' in results
        assert 'final_ris' in results
        assert 'ris_trajectory' in results
        assert 'patch_schedule' in results
        assert 'round_details' in results
        
        # Check trajectory length
        assert len(results['ris_trajectory']) == results['total_rounds'] + 1
    
    def test_ris_decreases(self, game_state):
        """Test that RIS generally decreases over simulation."""
        simulator = Simulator(game_state, simulation_length=5)
        
        results = simulator.run_simulation()
        
        initial_ris = results['initial_ris']
        final_ris = results['final_ris']
        
        # RIS should decrease or stay same (if no patches applied)
        assert final_ris <= initial_ris
    
    def test_simulation_terminates_early(self, game_state):
        """Test simulation terminates if no vulnerabilities remain."""
        # Short simulation on small system
        simulator = Simulator(game_state, simulation_length=100)
        
        results = simulator.run_simulation()
        
        # Should terminate before 100 rounds
        assert results['total_rounds'] <= 100
    
    def test_get_patch_priority_list(self, game_state):
        """Test extracting patch priority list."""
        simulator = Simulator(game_state, simulation_length=3)
        simulator.run_simulation()
        
        priority_list = simulator.get_patch_priority_list()
        
        assert isinstance(priority_list, list)
        # Check no duplicates
        assert len(priority_list) == len(set(priority_list))
    
    def test_reset_simulator(self, game_state):
        """Test resetting simulator state."""
        simulator = Simulator(game_state, simulation_length=3)
        simulator.run_simulation()
        
        assert len(simulator.round_history) > 0
        assert len(simulator.ris_trajectory) > 0
        
        simulator.reset()
        
        assert len(simulator.round_history) == 0
        assert len(simulator.ris_trajectory) == 0


class TestSimulationResult:
    """Test suite for SimulationResult."""
    
    @pytest.fixture
    def simulation_results(self):
        """Create sample simulation results."""
        return {
            'total_rounds': 3,
            'initial_ris': 100.0,
            'final_ris': 50.0,
            'ris_trajectory': [100.0, 80.0, 60.0, 50.0],
            'patch_schedule': [['PG1'], ['PG2'], ['PG3']],
            'round_details': [
                {
                    'round': 0,
                    'patches_applied': ['PG1'],
                    'vulnerabilities_exploited': ['CVE-1'],
                    'final_ris': 80.0,
                    'defender_payoff': -5.0,
                    'attacker_payoff': 3.0,
                    'equilibrium_type': 'pure'
                },
                {
                    'round': 1,
                    'patches_applied': ['PG2'],
                    'vulnerabilities_exploited': [],
                    'final_ris': 60.0,
                    'defender_payoff': -3.0,
                    'attacker_payoff': 1.0,
                    'equilibrium_type': 'mixed'
                },
                {
                    'round': 2,
                    'patches_applied': ['PG3'],
                    'vulnerabilities_exploited': [],
                    'final_ris': 50.0,
                    'defender_payoff': -2.0,
                    'attacker_payoff': 0.5,
                    'equilibrium_type': 'pure'
                }
            ]
        }
    
    def test_create_from_simulation(self, simulation_results):
        """Test creating SimulationResult from simulation output."""
        result = SimulationResult.from_simulation(simulation_results)
        
        assert result.patch_priority_list == ['PG1', 'PG2', 'PG3']
        assert result.ris_summary == [100.0, 80.0, 60.0, 50.0]
        assert len(result.per_round_details) == 3
    
    def test_export_to_dict(self, simulation_results):
        """Test exporting result to dictionary."""
        result = SimulationResult.from_simulation(simulation_results)
        export = result.export_to_dict()
        
        assert 'patch_priority_list' in export
        assert 'ris_summary' in export
        assert 'equilibrium_report' in export
        assert 'per_round_details' in export
    
    def test_get_ris_reduction_percentage(self, simulation_results):
        """Test calculating RIS reduction percentage."""
        result = SimulationResult.from_simulation(simulation_results)
        
        percentage = result.get_ris_reduction_percentage()
        
        # 100 -> 50 is 50% reduction
        assert np.isclose(percentage, 50.0)
    
    def test_get_patch_effectiveness(self, simulation_results):
        """Test analyzing patch effectiveness."""
        result = SimulationResult.from_simulation(simulation_results)
        
        effectiveness = result.get_patch_effectiveness()
        
        assert 'average_reduction_per_round' in effectiveness
        assert 'max_reduction_round' in effectiveness
        assert 'total_reduction' in effectiveness
    
    def test_get_summary(self, simulation_results):
        """Test generating summary string."""
        result = SimulationResult.from_simulation(simulation_results)
        
        summary = result.get_summary()
        
        assert isinstance(summary, str)
        assert 'Total Rounds' in summary
        assert 'RIS' in summary


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
