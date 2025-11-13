"""
Full Pipeline Integration Test

Tests complete flow from Developer A to Developer B and back.
"""

import pytest
import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from data_model import ConfigLoader, RiskCalculator
from game_engine import GameState, Simulator, SimulationResult


class TestFullPipeline:
    """Test complete integration of both modules."""
    
    @pytest.fixture
    def config_path(self):
        """Path to example configuration."""
        return os.path.join(
            os.path.dirname(__file__),
            '..',
            '..',
            'config',
            'example_system.json'
        )
    
    def test_complete_pipeline(self, config_path):
        """Test full pipeline from config to results."""
        # Step 1: Load system (Developer A)
        loader = ConfigLoader()
        system = loader.load_system(config_path)
        
        assert system is not None
        assert len(system.subsystems) > 0
        
        # Step 2: Calculate importance (Developer A)
        calculator = RiskCalculator()
        calculator.compute_importance(system)
        
        # Verify importance scores calculated
        for subsystem in system.subsystems:
            assert subsystem.importance_score > 0
        
        # Step 3: Export for game (Developer A → Developer B)
        export_dict = system.export_for_game()
        
        # Verify export format
        assert export_dict['api_version'] == '1.0.0'
        assert 'system_name' in export_dict
        assert len(export_dict['subsystems']) > 0
        assert len(export_dict['patch_groups']) > 0
        assert len(export_dict['players']) > 0
        
        # Step 4: Load into game state (Developer B)
        game_state = GameState.load_from_export(export_dict)
        
        assert game_state.system_name == export_dict['system_name']
        assert game_state.get_subsystem_count() == len(export_dict['subsystems'])
        
        # Step 5: Run simulation (Developer B)
        simulator = Simulator(game_state, simulation_length=5)
        simulation_results = simulator.run_simulation()
        
        assert 'total_rounds' in simulation_results
        assert simulation_results['total_rounds'] > 0
        assert simulation_results['final_ris'] <= simulation_results['initial_ris']
        
        # Step 6: Generate results (Developer B → Developer A)
        result = SimulationResult.from_simulation(simulation_results)
        
        # Verify result format matches contract
        result_dict = result.export_to_dict()
        assert 'patch_priority_list' in result_dict
        assert 'ris_summary' in result_dict
        assert 'equilibrium_report' in result_dict
        assert 'per_round_details' in result_dict
        
        # Verify equilibrium report structure
        eq_report = result_dict['equilibrium_report']
        assert 'expected_impact' in eq_report
        assert 'expected_profit' in eq_report
        
        # Verify per-round details structure
        for round_detail in result_dict['per_round_details']:
            assert 'round' in round_detail
            assert 'patched_groups' in round_detail
            assert 'attacked_vulnerabilities' in round_detail
            assert 'remaining_ris' in round_detail
    
    def test_sample_export_loadable(self):
        """Test that sample export can be loaded."""
        export_path = os.path.join(
            os.path.dirname(__file__),
            '..',
            'integration',
            'sample_export.json'
        )
        
        with open(export_path, 'r') as f:
            export_dict = json.load(f)
        
        # Should load without errors
        game_state = GameState.load_from_export(export_dict)
        
        assert game_state is not None
        assert game_state.get_vulnerability_count() > 0
    
    def test_pipeline_with_sample_export(self):
        """Test pipeline starting from sample export."""
        export_path = os.path.join(
            os.path.dirname(__file__),
            '..',
            'integration',
            'sample_export.json'
        )
        
        with open(export_path, 'r') as f:
            export_dict = json.load(f)
        
        # Load and simulate
        game_state = GameState.load_from_export(export_dict)
        simulator = Simulator(game_state, simulation_length=3)
        simulation_results = simulator.run_simulation()
        
        # Generate results
        result = SimulationResult.from_simulation(simulation_results)
        
        # Should complete without errors
        assert result.patch_priority_list is not None
        assert len(result.ris_summary) > 0
    
    def test_export_import_consistency(self, config_path):
        """Test that export → import preserves data."""
        # Export from Developer A
        loader = ConfigLoader()
        system = loader.load_system(config_path)
        calculator = RiskCalculator()
        calculator.compute_importance(system)
        export_dict = system.export_for_game()
        
        # Import in Developer B
        game_state = GameState.load_from_export(export_dict)
        
        # Verify data consistency
        assert game_state.system_name == system.system_class.name
        assert game_state.get_subsystem_count() == len(system.subsystems)
        assert game_state.get_patch_group_count() == len(export_dict['patch_groups'])
        
        # Verify vulnerability count
        total_vulns_export = sum(
            len(s['vulnerabilities']) for s in export_dict['subsystems']
        )
        assert game_state.get_vulnerability_count() == total_vulns_export
    
    def test_multiple_simulations_same_state(self, config_path):
        """Test running multiple simulations on same system."""
        # Setup
        loader = ConfigLoader()
        system = loader.load_system(config_path)
        calculator = RiskCalculator()
        calculator.compute_importance(system)
        export_dict = system.export_for_game()
        
        # Run two simulations
        game_state1 = GameState.load_from_export(export_dict)
        simulator1 = Simulator(game_state1, simulation_length=3)
        results1 = simulator1.run_simulation()
        
        game_state2 = GameState.load_from_export(export_dict)
        simulator2 = Simulator(game_state2, simulation_length=3)
        results2 = simulator2.run_simulation()
        
        # Both should complete successfully
        assert results1['total_rounds'] > 0
        assert results2['total_rounds'] > 0
        
        # Initial RIS should be the same
        assert results1['initial_ris'] == results2['initial_ris']
    
    def test_result_export_to_json(self, config_path, tmp_path):
        """Test exporting results to JSON file."""
        # Run pipeline
        loader = ConfigLoader()
        system = loader.load_system(config_path)
        calculator = RiskCalculator()
        calculator.compute_importance(system)
        export_dict = system.export_for_game()
        
        game_state = GameState.load_from_export(export_dict)
        simulator = Simulator(game_state, simulation_length=3)
        simulation_results = simulator.run_simulation()
        
        result = SimulationResult.from_simulation(simulation_results)
        
        # Export to file
        output_file = tmp_path / "results.json"
        result.export_to_json(str(output_file))
        
        # Verify file created and loadable
        assert output_file.exists()
        
        with open(output_file, 'r') as f:
            loaded_results = json.load(f)
        
        assert 'patch_priority_list' in loaded_results
        assert 'ris_summary' in loaded_results


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
