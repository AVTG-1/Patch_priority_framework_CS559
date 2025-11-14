"""
Backend Bridge Module

Utility functions to bridge FastAPI web API with the existing Python backend.
Provides clean interface to load systems and run simulations.
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional, List

# Add base_backend/src to Python path
backend_src_path = Path(__file__).parent.parent / "base_backend" / "src"
sys.path.insert(0, str(backend_src_path))

# Import backend modules
from data_model import ConfigLoader, RiskCalculator, SystemInstance
from game_engine import GameState, Simulator, SimulationResult


def load_system_from_config(config_path: str) -> SystemInstance:
    """
    Load and initialize a system from a configuration file.

    This function:
    1. Loads the system configuration from JSON/YAML
    2. Calculates importance scores for all subsystems
    3. Returns a ready-to-simulate SystemInstance

    Args:
        config_path: Path to system configuration file (JSON or YAML)

    Returns:
        SystemInstance: Initialized system with calculated risk scores

    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If config file is invalid
    """
    # Step 1: Load configuration
    loader = ConfigLoader()
    system = loader.load_system(config_path)

    # Step 2: Calculate importance scores
    calculator = RiskCalculator()
    calculator.compute_importance(system)

    return system


def run_simulation(
    system_instance: SystemInstance,
    rounds: int = 10,
    players: Optional[List] = None,
    patch_grouping_method: str = "dependencies"
) -> Dict[str, Any]:
    """
    Run a game-theoretic simulation on a system instance.

    This function:
    1. Exports the system for the game engine
    2. Loads the game state
    3. Runs the simulation for specified rounds
    4. Returns comprehensive results including patch priorities

    Args:
        system_instance: SystemInstance to simulate
        rounds: Number of simulation rounds (default: 10)
        players: Optional list of player objects (will use default if None)
        patch_grouping_method: How to group patches - "dependencies", "subsystem", or "severity"

    Returns:
        Dict containing:
            - patch_priority_list: Ordered list of patch group IDs
            - ris_summary: RIS (Remaining Impact Score) per round
            - equilibrium_report: Nash equilibrium statistics
            - per_round_details: Detailed results for each round
            - system_info: Basic system information

    Raises:
        ValueError: If simulation parameters are invalid
    """
    # Step 1: Export system for game engine
    export_dict = system_instance.export_for_game(
        players=players,
        patch_grouping_method=patch_grouping_method
    )

    # Step 2: Initialize game state
    game_state = GameState.load_from_export(export_dict)

    # Step 3: Run simulation
    simulator = Simulator(game_state, simulation_length=rounds)
    simulation_results = simulator.run_simulation()

    # Step 4: Format results
    result = SimulationResult.from_simulation(simulation_results)

    # Step 5: Add additional metadata
    result_dict = result.export_to_dict()

    # Debug logging
    print(f"[DEBUG] Simulation completed:")
    print(f"[DEBUG] - Total rounds requested: {rounds}")
    print(f"[DEBUG] - Total rounds in simulation_results: {simulation_results.get('total_rounds', 'N/A')}")
    print(f"[DEBUG] - Length of round_details: {len(simulation_results.get('round_details', []))}")
    print(f"[DEBUG] - Length of per_round_details in result_dict: {len(result_dict.get('per_round_details', []))}")
    print(f"[DEBUG] - Round numbers in per_round_details: {[r.get('round') for r in result_dict.get('per_round_details', [])]}")

    result_dict['system_info'] = {
        'system_name': export_dict['system_name'],
        'subsystem_count': len(export_dict['subsystems']),
        'vulnerability_count': sum(
            len(subsystem['vulnerabilities'])
            for subsystem in export_dict['subsystems']
        ),
        'patch_group_count': len(export_dict['patch_groups']),
        'simulation_rounds': rounds,
        'patch_grouping_method': patch_grouping_method
    }

    # Add raw simulation metrics
    result_dict['simulation_metrics'] = {
        'total_rounds': simulation_results.get('total_rounds', rounds),
        'total_vulnerabilities_patched': simulation_results.get('total_vulnerabilities_patched', 0),
        'total_vulnerabilities_exploited': simulation_results.get('total_vulnerabilities_exploited', 0),
        'initial_ris': simulation_results.get('initial_ris', 0.0),
        'final_ris': simulation_results.get('final_ris', 0.0),
        'ris_reduction': simulation_results.get('initial_ris', 0.0) - simulation_results.get('final_ris', 0.0),
        'ris_reduction_percentage': (
            ((simulation_results.get('initial_ris', 0.0) - simulation_results.get('final_ris', 0.0)) /
             simulation_results.get('initial_ris', 1.0) * 100)
            if simulation_results.get('initial_ris', 0.0) > 0 else 0.0
        )
    }

    return result_dict


def run_simulation_from_config(
    config_path: str,
    rounds: int = 10,
    patch_grouping_method: str = "dependencies"
) -> Dict[str, Any]:
    """
    Load a system from config and run simulation in one call.

    Convenience function that combines load_system_from_config and run_simulation.

    Args:
        config_path: Path to system configuration file
        rounds: Number of simulation rounds (default: 10)
        patch_grouping_method: How to group patches

    Returns:
        Dict: Simulation results (same format as run_simulation)

    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If config or simulation parameters are invalid
    """
    # Load system
    system = load_system_from_config(config_path)

    # Load players from config (if present)
    import json
    with open(config_path, 'r') as f:
        config_dict = json.load(f)

    players = None
    if 'players' in config_dict:
        loader = ConfigLoader()
        players = loader.load_players(config_dict)

    # Run simulation
    return run_simulation(
        system,
        rounds=rounds,
        players=players,
        patch_grouping_method=patch_grouping_method
    )


def get_system_summary(system_instance: SystemInstance) -> Dict[str, Any]:
    """
    Get a summary of system information without running simulation.

    Useful for previewing a system before simulation.

    Args:
        system_instance: SystemInstance to summarize

    Returns:
        Dict containing:
            - system_name: Name of the system
            - system_class: System classification
            - subsystem_count: Number of subsystems
            - vulnerability_count: Total vulnerabilities
            - subsystems: List of subsystem summaries
    """
    return {
        'system_name': system_instance.system_class.name,
        'system_class': system_instance.system_class.name,
        'subsystem_count': len(system_instance.subsystems),
        'vulnerability_count': system_instance.get_total_vulnerability_count(),
        'subsystems': [
            {
                'id': subsystem.id,
                'name': subsystem.name,
                'vulnerability_count': len(subsystem.vulnerabilities),
                'importance_score': getattr(subsystem, 'importance_score', 0.0),
                'total_patch_cost': subsystem.get_total_patch_cost()
            }
            for subsystem in system_instance.subsystems
        ]
    }
