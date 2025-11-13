#!/usr/bin/env python3
"""
Patch Prioritization Framework - Main Entry Point

Integrates Developer A (Data Models) and Developer B (Game Engine)
to provide a complete patch prioritization solution.
"""

import sys
import argparse
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from data_model import ConfigLoader, RiskCalculator, SystemInstance
from game_engine import GameState, Simulator, SimulationResult


def run_from_config(config_path: str, 
                   output_path: str = None,
                   simulation_rounds: int = 10,
                   verbose: bool = True) -> SimulationResult:
    """
    Run complete pipeline from configuration file.
    
    Args:
        config_path: Path to system configuration JSON
        output_path: Optional path to save results
        simulation_rounds: Number of simulation rounds
        verbose: Print progress information
    
    Returns:
        SimulationResult object
    """
    if verbose:
        print("=" * 70)
        print("Patch Prioritization Framework")
        print("=" * 70)
        print()
    
    # Step 1: Load system (Developer A)
    if verbose:
        print("Step 1: Loading system configuration...")
    
    loader = ConfigLoader()
    system = loader.load_system(config_path)
    
    if verbose:
        print(f"  ✓ Loaded system: {system.system_class.name}")
        print(f"  ✓ Subsystems: {len(system.subsystems)}")
        print(f"  ✓ Vulnerabilities: {system.get_total_vulnerability_count()}")
        print()
    
    # Step 2: Calculate risk scores (Developer A)
    if verbose:
        print("Step 2: Calculating risk scores...")
    
    calculator = RiskCalculator()
    calculator.compute_importance(system)
    
    if verbose:
        print(f"  ✓ Importance scores calculated")
        print()
    
    # Step 2.5: Load players from config
    # Load config again to get players
    with open(config_path, 'r') as f:
        import json
        config_dict = json.load(f)
    
    players = loader.load_players(config_dict) if 'players' in config_dict else None
    
    # Step 3: Export for game engine (Developer A → Developer B)
    if verbose:
        print("Step 3: Exporting to game engine...")
    
    export_dict = system.export_for_game(players=players)
    
    if verbose:
        print(f"  ✓ Export complete (API v{export_dict['api_version']})")
        print(f"  ✓ Patch groups: {len(export_dict['patch_groups'])}")
        print(f"  ✓ Players: {len(export_dict['players'])}")
        print()
    
    # Step 4: Load into game state (Developer B)
    if verbose:
        print("Step 4: Initializing game state...")
    
    game_state = GameState.load_from_export(export_dict)
    
    if verbose:
        print(f"  ✓ Game state loaded")
        print(f"  ✓ Defenders: {len(game_state.get_defenders())}")
        print(f"  ✓ Attackers: {len(game_state.get_attackers())}")
        print()
    
    # Step 5: Run simulation (Developer B)
    if verbose:
        print(f"Step 5: Running {simulation_rounds}-round simulation...")
    
    simulator = Simulator(game_state, simulation_length=simulation_rounds)
    simulation_results = simulator.run_simulation()
    
    if verbose:
        print(f"  ✓ Simulation complete")
        print(f"  ✓ Rounds executed: {simulation_results['total_rounds']}")
        print(f"  ✓ Vulnerabilities patched: {simulation_results['total_vulnerabilities_patched']}")
        print(f"  ✓ Vulnerabilities exploited: {simulation_results['total_vulnerabilities_exploited']}")
        print()
    
    # Step 6: Export results (Developer B → Developer A)
    if verbose:
        print("Step 6: Generating results...")
    
    result = SimulationResult.from_simulation(simulation_results)
    
    if verbose:
        print(f"  ✓ RIS reduction: {result.get_ris_reduction_percentage():.1f}%")
        print(f"  ✓ Initial RIS: {result.ris_summary[0]:.2f}")
        print(f"  ✓ Final RIS: {result.ris_summary[-1]:.2f}")
        print()
    
    # Step 7: Save results if requested
    if output_path:
        result.export_to_json(output_path)
        if verbose:
            print(f"Step 7: Results saved to {output_path}")
            print()
    
    # Print summary
    if verbose:
        print(result.get_summary())
    
    return result


def run_from_export(export_path: str,
                   output_path: str = None,
                   simulation_rounds: int = 10,
                   verbose: bool = True) -> SimulationResult:
    """
    Run simulation from pre-exported game state.
    
    Args:
        export_path: Path to export JSON from Developer A
        output_path: Optional path to save results
        simulation_rounds: Number of simulation rounds
        verbose: Print progress information
    
    Returns:
        SimulationResult object
    """
    if verbose:
        print("=" * 70)
        print("Patch Prioritization Framework (From Export)")
        print("=" * 70)
        print()
    
    # Load export
    if verbose:
        print("Loading export...")
    
    with open(export_path, 'r') as f:
        export_dict = json.load(f)
    
    if verbose:
        print(f"  ✓ Export loaded: {export_dict['system_name']}")
        print()
    
    # Initialize game state
    game_state = GameState.load_from_export(export_dict)
    
    # Run simulation
    if verbose:
        print(f"Running {simulation_rounds}-round simulation...")
    
    simulator = Simulator(game_state, simulation_length=simulation_rounds)
    simulation_results = simulator.run_simulation()
    
    if verbose:
        print(f"  ✓ Simulation complete")
        print()
    
    # Generate results
    result = SimulationResult.from_simulation(simulation_results)
    
    # Save if requested
    if output_path:
        result.export_to_json(output_path)
        if verbose:
            print(f"Results saved to {output_path}")
            print()
    
    # Print summary
    if verbose:
        print(result.get_summary())
    
    return result


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Patch Prioritization Framework - Game-Theoretic Vulnerability Management"
    )
    
    parser.add_argument(
        'input',
        help='Path to system configuration (JSON) or export file'
    )
    
    parser.add_argument(
        '-o', '--output',
        help='Path to save results (JSON)',
        default=None
    )
    
    parser.add_argument(
        '-r', '--rounds',
        type=int,
        default=10,
        help='Number of simulation rounds (default: 10)'
    )
    
    parser.add_argument(
        '-e', '--from-export',
        action='store_true',
        help='Input is an export file (skip Developer A processing)'
    )
    
    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='Quiet mode (minimal output)'
    )
    
    args = parser.parse_args()
    
    try:
        if args.from_export:
            result = run_from_export(
                args.input,
                args.output,
                args.rounds,
                verbose=not args.quiet
            )
        else:
            result = run_from_config(
                args.input,
                args.output,
                args.rounds,
                verbose=not args.quiet
            )
        
        return 0
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if not args.quiet:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
