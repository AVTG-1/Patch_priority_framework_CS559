"""
Generate Sample Export

Creates a sample export JSON file for Developer B to use in testing
and development without requiring Developer A's module.
"""

import json
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from data_model import ConfigLoader, RiskCalculator


def generate_sample_export():
    """Generate sample export from example configuration."""
    
    # Load example system
    config_path = os.path.join(
        os.path.dirname(__file__),
        '..',
        'config',
        'example_system.json'
    )
    
    loader = ConfigLoader()
    system = loader.load_system(config_path)
    
    # Calculate importance scores
    calculator = RiskCalculator()
    calculator.compute_importance(system)
    
    # Load players from config
    with open(config_path, 'r') as f:
        config = json.load(f)
    players = loader.load_players(config)
    
    # Export for game engine
    export_dict = system.export_for_game(players=players)
    
    # Save to integration test directory
    output_path = os.path.join(
        os.path.dirname(__file__),
        '..',
        'tests',
        'integration',
        'sample_export.json'
    )
    
    # Create directory if needed
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(export_dict, f, indent=2)
    
    print(f"Sample export generated: {output_path}")
    print(f"System: {export_dict['system_name']}")
    print(f"Subsystems: {len(export_dict['subsystems'])}")
    print(f"Total vulnerabilities: {sum(len(s['vulnerabilities']) for s in export_dict['subsystems'])}")
    print(f"Patch groups: {len(export_dict['patch_groups'])}")
    print(f"Players: {len(export_dict['players'])}")
    
    return export_dict


if __name__ == "__main__":
    generate_sample_export()
