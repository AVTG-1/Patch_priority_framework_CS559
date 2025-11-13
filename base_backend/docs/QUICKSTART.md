# Quick Start Guide

## Installation

```bash
# Clone repository
git clone <repository-url>
cd patch_prioritization_framework

# Setup virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Basic Usage

### 1. Define a System from Scratch

```python
from data_model import SystemClass, SystemInstance, Subsystem, Vulnerability, PlayerBase
import numpy as np

# Create subsystems
subsystem1 = Subsystem(
    id="sub_001",
    name="Web Server",
    importance_score=0.0,  # Will be calculated
    vulnerabilities=[],
    connected_ids=["sub_002"],
    functional_deps=["sub_002"]
)

subsystem2 = Subsystem(
    id="sub_002",
    name="Database",
    importance_score=0.0,
    vulnerabilities=[],
    connected_ids=["sub_001"],
    functional_deps=[]
)

# Add vulnerabilities
vuln1 = Vulnerability(
    cve_id="CVE-2024-0001",
    description="SQL Injection vulnerability",
    cvss_impact=7.5,
    cvss_exploitability=8.2,
    exploit_present=True,
    patch_cost=5.0,
    subsystem_id="sub_002",
    dependencies=[]
)
subsystem2.vulnerabilities.append(vuln1)

# Create system instance
system = SystemInstance(
    system_class=SystemClass(name="WebApp", description="Web application system"),
    subsystems=[subsystem1, subsystem2],
    weights={"functional_weight": 0.6, "topological_weight": 0.4}
)

# Add players
defender = PlayerBase(
    player_id="defender_1",
    role="DEFENDER",
    resource_budget=100.0,
    team_id=None
)

attacker = PlayerBase(
    player_id="attacker_1",
    role="ATTACKER",
    resource_budget=50.0,
    team_id=None
)

# Export for game engine
export_dict = system.export_for_game([defender, attacker])
```

### 2. Load from Configuration File

```python
from data_model import ConfigLoader

# Load system from JSON
loader = ConfigLoader()
system = loader.load_system("config/example_system.json")

# Export for simulation
export_dict = system.export_for_game()
print(f"System: {export_dict['system_name']}")
print(f"Total vulnerabilities: {sum(len(s['vulnerabilities']) for s in export_dict['subsystems'])}")
```

### 3. Import CVE Data from NVD

```python
from data_model import NVDImporter

# Initialize importer
importer = NVDImporter(api_key="your_nvd_api_key")  # API key optional

# Import specific CVEs
cve_list = ["CVE-2024-0001", "CVE-2024-0002"]
vulnerabilities = importer.import_from_nvd(cve_list)

# Add to subsystem
subsystem.vulnerabilities.extend(vulnerabilities)
```

### 4. Calculate Risk Scores

```python
from data_model import RiskCalculator

calculator = RiskCalculator()

# Calculate subsystem importance
calculator.compute_importance(system)

# Score vulnerabilities
for subsystem in system.subsystems:
    for vuln in subsystem.vulnerabilities:
        score = calculator.score_vulnerability(vuln, subsystem)
        print(f"{vuln.cve_id}: Risk Score = {score}")

# Create patch groups
patch_groups = calculator.collapse_patch_dependencies(system.get_all_vulnerabilities())
```

### 5. Export for Integration

```python
# Generate complete export for Developer B
export_dict = system.export_for_game()

# Save to JSON for testing
import json
with open("tests/integration/sample_export.json", "w") as f:
    json.dump(export_dict, f, indent=2)

# Pass to game engine (Developer B's code)
# from game_engine import GameState
# game_state = GameState.load_from_export(export_dict)
```

## Common Workflows

### Workflow 1: Manual System Definition
1. Create subsystems with dependencies
2. Add vulnerabilities to subsystems
3. Define players (attackers/defenders)
4. Calculate importance scores
5. Export for simulation

### Workflow 2: Configuration-Based
1. Create JSON configuration file
2. Use ConfigLoader to parse and validate
3. System automatically calculates dependencies
4. Export for simulation

### Workflow 3: NVD-Enhanced
1. Define basic system structure
2. Use NVDImporter to fetch real CVE data
3. Enrich vulnerabilities with CVSS metrics
4. Calculate risk scores
5. Export for simulation

## Configuration File Example

```json
{
  "system_name": "SCADA System",
  "system_class": "Industrial Control System",
  "subsystems": [
    {
      "id": "hmi_001",
      "name": "HMI Controller",
      "connected_to": ["plc_001"],
      "functional_dependencies": ["plc_001"]
    }
  ],
  "vulnerabilities": [
    {
      "cve_id": "CVE-2024-1234",
      "subsystem_id": "hmi_001",
      "cvss_impact": 8.5,
      "cvss_exploitability": 7.2,
      "patch_cost": 10.0
    }
  ],
  "players": [
    {
      "player_id": "def_1",
      "role": "DEFENDER",
      "resource_budget": 150.0
    }
  ],
  "weights": {
    "functional_weight": 0.7,
    "topological_weight": 0.3
  }
}
```

## Next Steps

- See [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md) for integration with Developer B
- See [MODULE_DOCUMENTATION.md](MODULE_DOCUMENTATION.md) for detailed API reference
- Run tests: `pytest tests/`
