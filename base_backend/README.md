# Patch Prioritization Framework - Developer A Module

## Overview

This module implements the **Data Models & Assessment Logic** for a game-theoretic patch prioritization framework. It provides the foundational data structures and risk assessment algorithms that model cybersecurity systems, vulnerabilities, and patches, then exports them in a standardized format for game simulation.

## Project Structure

```
patch_prioritization_framework/
├── src/
│   └── data_model/
│       ├── __init__.py              # Module exports
│       ├── system.py                # SystemClass, SystemInstance
│       ├── subsystem.py             # Subsystem model
│       ├── vulnerability.py         # Vulnerability model
│       ├── patch_group.py           # PatchGroup logic
│       ├── player.py                # PlayerBase model
│       ├── config_loader.py         # Input parsers/validation
│       ├── nvd_importer.py          # NVD/CVE integration
│       └── risk_calculator.py       # Scoring logic
├── tests/
│   ├── data_model/
│   │   ├── test_system.py
│   │   ├── test_subsystem.py
│   │   ├── test_vulnerability.py
│   │   ├── test_patch_group.py
│   │   ├── test_player.py
│   │   ├── test_config_loader.py
│   │   └── test_risk_calculator.py
│   └── integration/
│       └── sample_export.json       # Sample data for Developer B
├── config/
│   └── example_system.json          # Example system configuration
├── docs/
│   ├── QUICKSTART.md                # Getting started guide
│   ├── INTEGRATION_GUIDE.md         # Integration specifications
│   └── MODULE_DOCUMENTATION.md      # Detailed module docs
├── requirements.txt                 # Python dependencies
└── README.md                        # This file
```

## Module Responsibilities

### Core Data Models
- **system.py**: Defines system templates and instances with dependency matrices
- **subsystem.py**: Models individual subsystems with importance scores
- **vulnerability.py**: Represents CVEs with CVSS metrics and dependencies
- **patch_group.py**: Aggregates vulnerabilities into patchable groups
- **player.py**: Models attacker/defender entities with resource budgets

### Utilities
- **config_loader.py**: Validates and parses system configurations from JSON/YAML
- **nvd_importer.py**: Integrates with NVD API for CVE data enrichment
- **risk_calculator.py**: Computes importance scores and risk metrics

## Key Features

- **Type-safe data models** with comprehensive validation
- **Export interface** (`export_for_game()`) for seamless integration with game engine
- **Flexible configuration** support for various system architectures
- **NVD integration** for automated vulnerability data import
- **Risk assessment** algorithms for subsystem importance and vulnerability scoring

## Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Quick Start

See [QUICKSTART.md](docs/QUICKSTART.md) for detailed usage examples.

```python
from data_model import SystemInstance, ConfigLoader

# Load system configuration
loader = ConfigLoader()
system = loader.load_system("config/example_system.json")

# Export for game simulation
export_dict = system.export_for_game()
print(f"Exported system: {export_dict['system_name']}")
print(f"Subsystems: {len(export_dict['subsystems'])}")
print(f"Patch groups: {len(export_dict['patch_groups'])}")
```

## Integration with Developer B

This module exports data via the `export_for_game()` method, which returns a dictionary conforming to the integration contract. Developer B consumes this dictionary to initialize game simulations.

See [INTEGRATION_GUIDE.md](docs/INTEGRATION_GUIDE.md) for detailed integration specifications.

## Testing

```bash
# Run all tests
python -m pytest tests/

# Run specific module tests
python -m pytest tests/data_model/test_system.py

# Run with coverage
python -m pytest --cov=src/data_model tests/
```

## Dependencies

- Python 3.8+
- numpy: Matrix operations for dependencies
- pandas: Data manipulation (optional, for batch processing)
- requests: NVD API integration
- jsonschema: Configuration validation
- pytest: Testing framework

## API Version

Current API version: **1.0.0**

All exports include `api_version` field for compatibility tracking.

## License

[Add your license here]

## Contributors

- Developer A: Data Models & Assessment Logic
- Developer B: Game Engine & Simulation (separate module)
