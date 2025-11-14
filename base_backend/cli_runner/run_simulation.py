#!/usr/bin/env python3
"""
CLI Simulation Runner

Runs patch prioritization simulations from JSON configuration files.

Usage:
    python run_simulation.py config.json
    python run_simulation.py config.json --output results.json
    python run_simulation.py config.json --verbose
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any, Optional

# Add base_backend/src to path
BASE_DIR = Path(__file__).parent.parent
SRC_DIR = BASE_DIR / "src"
sys.path.insert(0, str(SRC_DIR))

from data_model import ConfigLoader, RiskCalculator, SystemInstance, PlayerBase
from game_engine import GameState, Simulator, SimulationResult


def load_config_file(config_path: str) -> Dict[str, Any]:
    """Load and validate configuration from JSON file."""
    path = Path(config_path)

    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(path, 'r') as f:
        config = json.load(f)

    return config


def create_players_from_config(config: Dict[str, Any]) -> Optional[list]:
    """Create player objects from configuration."""
    players_config = config.get('players', [])

    if not players_config:
        return None

    players = []
    for player_conf in players_config:
        role = player_conf['role'].upper()
        player_id = player_conf['player_id']
        budget = player_conf['resource_budget']

        if role == 'DEFENDER':
            player = PlayerBase.create_defender(
                player_id=player_id,
                resource_budget=budget
            )
        elif role == 'ATTACKER':
            player = PlayerBase.create_attacker(
                player_id=player_id,
                resource_budget=budget
            )
        else:
            raise ValueError(f"Unknown player role: {role}")

        players.append(player)

    return players if players else None


def run_simulation_from_config(
    config: Dict[str, Any],
    verbose: bool = False
) -> Dict[str, Any]:
    """
    Run simulation from configuration dictionary.

    Args:
        config: Configuration dictionary with system and simulation parameters
        verbose: Print detailed progress information

    Returns:
        Dictionary containing simulation results
    """
    if verbose:
        print("=" * 80)
        print("PATCH PRIORITIZATION SIMULATION")
        print("=" * 80)
        print(f"\nSystem: {config.get('system_name', 'Unknown')}")

    # Step 1: Load system from config
    if verbose:
        print("\n[1/5] Loading system configuration...")

    loader = ConfigLoader()
    system = loader.load_from_dict(config)

    if verbose:
        print(f"  ✓ Loaded {len(system.subsystems)} subsystems")
        total_vulns = sum(len(s.vulnerabilities) for s in system.subsystems)
        print(f"  ✓ Loaded {total_vulns} vulnerabilities")

    # Step 2: Calculate importance scores
    if verbose:
        print("\n[2/5] Calculating subsystem importance scores...")

    calculator = RiskCalculator()
    calculator.compute_importance(system)

    if verbose:
        for subsys in system.subsystems:
            importance = getattr(subsys, 'importance_score', 0.0)
            print(f"  • {subsys.name}: {importance:.3f}")

    # Step 3: Create players
    if verbose:
        print("\n[3/5] Initializing players...")

    players = create_players_from_config(config)

    if players:
        if verbose:
            for player in players:
                print(f"  • {player.role}: {player.player_id} (budget: {player.resource_budget})")
    else:
        if verbose:
            print("  • Using default players")

    # Step 4: Export system for game engine
    if verbose:
        print("\n[4/5] Preparing game state...")

    rounds = config.get('simulation_rounds', config.get('rounds', 10))
    patch_method = config.get('patch_grouping_method', 'dependencies')

    export_dict = system.export_for_game(
        players=players,
        patch_grouping_method=patch_method
    )

    if verbose:
        print(f"  ✓ Simulation rounds: {rounds}")
        print(f"  ✓ Patch grouping: {patch_method}")
        print(f"  ✓ Patch groups: {len(export_dict.get('patch_groups', []))}")

    # Step 5: Run simulation
    if verbose:
        print("\n[5/5] Running simulation...")

    game_state = GameState.load_from_export(export_dict)
    simulator = Simulator(game_state, simulation_length=rounds)
    simulation_results = simulator.run_simulation()

    # Format results
    result = SimulationResult.from_simulation(simulation_results)
    result_dict = result.export_to_dict()

    # Add metadata
    result_dict['system_info'] = {
        'system_name': config['system_name'],
        'subsystem_count': len(system.subsystems),
        'vulnerability_count': total_vulns,
        'patch_group_count': len(export_dict.get('patch_groups', [])),
        'simulation_rounds': rounds,
        'patch_grouping_method': patch_method
    }

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

    if verbose:
        print("\n" + "=" * 80)
        print("RESULTS")
        print("=" * 80)
        metrics = result_dict['simulation_metrics']
        print(f"\nInitial RIS:    {metrics['initial_ris']:.4f}")
        print(f"Final RIS:      {metrics['final_ris']:.4f}")
        print(f"RIS Reduction:  {metrics['ris_reduction']:.4f} ({metrics['ris_reduction_percentage']:.2f}%)")
        print(f"\nPatches Applied: {metrics['total_vulnerabilities_patched']}")
        print(f"Attacks:         {metrics['total_vulnerabilities_exploited']}")

        if result_dict.get('patch_priority_list'):
            print(f"\nPatch Priority Order:")
            for i, patch_group in enumerate(result_dict['patch_priority_list'][:10], 1):
                print(f"  {i}. {patch_group}")

    return result_dict


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Run patch prioritization simulation from JSON configuration',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Example JSON configuration:
  {
    "system_name": "Production Server",
    "subsystems": [
      {
        "id": "web",
        "name": "Web Server",
        "functional_dependencies": ["db"]
      },
      {
        "id": "db",
        "name": "Database",
        "functional_dependencies": []
      }
    ],
    "vulnerabilities": [
      {
        "cve_id": "CVE-2024-1234",
        "subsystem_id": "web",
        "cvss_impact": 7.5,
        "cvss_exploitability": 8.2,
        "patch_cost": 2.0,
        "description": "SQL injection vulnerability"
      }
    ],
    "players": [
      {
        "player_id": "defender_1",
        "role": "DEFENDER",
        "resource_budget": 100.0
      },
      {
        "player_id": "attacker_1",
        "role": "ATTACKER",
        "resource_budget": 50.0
      }
    ],
    "simulation_rounds": 10,
    "patch_grouping_method": "dependencies"
  }
        '''
    )

    parser.add_argument(
        'config_file',
        help='Path to JSON configuration file'
    )

    parser.add_argument(
        '-o', '--output',
        help='Output file for results (JSON format)',
        default=None
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Print detailed progress information'
    )

    parser.add_argument(
        '--validate-only',
        action='store_true',
        help='Only validate configuration without running simulation'
    )

    args = parser.parse_args()

    try:
        # Load configuration
        config = load_config_file(args.config_file)

        if args.validate_only:
            print(f"✓ Configuration file '{args.config_file}' is valid")
            print(f"  System: {config.get('system_name', 'Unknown')}")
            print(f"  Subsystems: {len(config.get('subsystems', []))}")
            print(f"  Vulnerabilities: {len(config.get('vulnerabilities', []))}")
            return 0

        # Run simulation
        results = run_simulation_from_config(config, verbose=args.verbose)

        # Save or print results
        if args.output:
            output_path = Path(args.output)
            with open(output_path, 'w') as f:
                json.dump(results, f, indent=2)

            if args.verbose:
                print(f"\n✓ Results saved to: {args.output}")
        else:
            if not args.verbose:
                # Print compact JSON if not verbose
                print(json.dumps(results, indent=2))

        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in configuration file: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: Configuration validation failed: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
