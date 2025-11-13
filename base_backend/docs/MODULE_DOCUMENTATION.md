# Module Documentation - Developer A

## Overview

This document provides detailed API documentation for all classes, methods, and utilities in the Data Model module.

## API Version: 1.0.0

---

## Core Classes

### SystemClass

Template for a system type (e.g., SCADA, Web Application).

**Attributes:**
- `name: str` - System type name
- `description: str` - Description of system characteristics
- `default_subsystems: List[str]` - Suggested subsystem types
- `weight_config: Dict[str, float]` - Default weight configuration

**Example:**
```python
system_class = SystemClass(
    name="SCADA System",
    description="Industrial control system",
    weight_config={"functional_weight": 0.7, "topological_weight": 0.3}
)
```

---

### SystemInstance

Instance of a system with specific subsystems and vulnerabilities.

**Constructor:**
```python
SystemInstance(
    system_class: SystemClass,
    subsystems: List[Subsystem],
    weights: Optional[Dict[str, float]] = None
)
```

**Key Methods:**

#### `export_for_game(players, patch_grouping_method) -> Dict[str, Any]`
**CRITICAL INTEGRATION METHOD**

Exports system as dictionary for game engine integration.

**Parameters:**
- `players: Optional[List[PlayerBase]]` - List of players (creates default if None)
- `patch_grouping_method: str` - Method for grouping patches ("dependencies", "subsystem", "severity")

**Returns:**
Dictionary with keys:
- `api_version: str` - API version (currently "1.0.0")
- `system_name: str` - System name
- `subsystems: List[dict]` - List of subsystem dictionaries
- `functional_dependencies: List[List[int]]` - N×N dependency matrix
- `network_topology: List[List[int]]` - N×N topology matrix
- `weights: dict` - Weight configuration
- `patch_groups: List[dict]` - List of patch group dictionaries
- `players: List[dict]` - List of player dictionaries

**Example:**
```python
system = SystemInstance(system_class, subsystems)
export_dict = system.export_for_game()

# Pass to Developer B
from game_engine import GameState
game_state = GameState.load_from_export(export_dict)
```

#### `get_all_vulnerabilities() -> List[Vulnerability]`
Get all vulnerabilities across all subsystems.

#### `create_patch_groups(method) -> List[PatchGroup]`
Create patch groups from vulnerabilities.

**Parameters:**
- `method: str` - Grouping method ("dependencies", "subsystem", "severity")

#### `add_subsystem(subsystem: Subsystem)`
Add a subsystem to the system.

#### `remove_subsystem(subsystem_id: str) -> bool`
Remove a subsystem by ID.

---

### Subsystem

Represents a subsystem component within a system.

**Constructor:**
```python
Subsystem(
    id: str,
    name: str,
    importance_score: float = 0.0,
    vulnerabilities: List[Vulnerability] = [],
    connected_ids: List[str] = [],
    functional_deps: List[str] = []
)
```

**Key Methods:**

#### `add_vulnerability(vulnerability: Vulnerability)`
Add a vulnerability to this subsystem.

#### `remove_vulnerability(cve_id: str) -> bool`
Remove a vulnerability by CVE ID.

#### `get_vulnerability(cve_id: str) -> Optional[Vulnerability]`
Get vulnerability by CVE ID.

#### `get_total_patch_cost() -> float`
Calculate total cost to patch all vulnerabilities.

#### `get_critical_vulnerabilities(threshold: float = 7.0) -> List[Vulnerability]`
Get vulnerabilities with high impact scores.

#### `to_dict() -> Dict[str, Any]`
Export subsystem as dictionary.

**Export Format:**
```python
{
    "id": str,
    "name": str,
    "importance_score": float,
    "vulnerabilities": List[dict]
}
```

---

### Vulnerability

Represents a CVE vulnerability with CVSS metrics.

**Constructor:**
```python
Vulnerability(
    cve_id: str,                    # Must start with "CVE-"
    description: str,
    cvss_impact: float,             # 0.0-10.0
    cvss_exploitability: float,     # 0.0-10.0
    exploit_present: bool,
    patch_cost: float,              # >= 0
    subsystem_id: str,
    dependencies: List[str] = [],
    custom_extras: Dict[str, Any] = {}
)
```

**Validation Rules:**
- `cve_id` must start with "CVE-"
- CVSS scores must be in range [0.0, 10.0]
- `patch_cost` must be non-negative
- Cannot have self-dependency

**Key Methods:**

#### `to_dict() -> Dict[str, Any]`
Export vulnerability for integration.

**Export Format:**
```python
{
    "cve_id": str,
    "description": str,
    "cvss_impact": float,
    "cvss_exploitability": float,
    "exploit_present": bool,
    "patch_cost": float,
    "dependencies": List[str]
}
```

#### `get_base_score() -> float`
Calculate base risk score from CVSS metrics.

#### `has_dependencies() -> bool`
Check if vulnerability has patch dependencies.

#### `get_exploit_multiplier() -> float`
Returns 1.5 if exploit exists, 1.0 otherwise.

---

### PatchGroup

Aggregates vulnerabilities into patchable groups.

**Constructor:**
```python
PatchGroup(
    group_id: str,
    cve_ids: List[str] = [],
    vulnerabilities: List[Vulnerability] = [],
    total_cost: float = 0.0,
    aggregate_impact: float = 0.0
)
```

**Key Methods:**

#### `add_vulnerability(vulnerability: Vulnerability)`
Add a vulnerability to this group.

#### `get_size() -> int`
Get number of vulnerabilities in group.

#### `contains_cve(cve_id: str) -> bool`
Check if group contains a specific CVE.

#### `to_dict() -> Dict[str, Any]`
Export patch group for integration.

**Export Format:**
```python
{
    "group_id": str,
    "cve_ids": List[str],
    "total_cost": float,
    "aggregate_impact": float
}
```

#### `from_vulnerabilities(group_id, vulnerabilities) -> PatchGroup` (classmethod)
Create a PatchGroup from a list of vulnerabilities.

**Patch Grouping Functions:**

#### `collapse_by_dependencies(vulnerabilities) -> List[PatchGroup]`
Group vulnerabilities with mutual dependencies together.

#### `collapse_by_subsystem(vulnerabilities) -> List[PatchGroup]`
Group all vulnerabilities by their subsystem.

#### `collapse_by_severity(vulnerabilities, thresholds) -> List[PatchGroup]`
Group vulnerabilities by severity levels (CRITICAL, HIGH, MEDIUM, LOW).

---

### PlayerBase

Represents attacker and defender players.

**Constructor:**
```python
PlayerBase(
    player_id: str,
    role: str,                      # "ATTACKER" or "DEFENDER"
    resource_budget: float,         # >= 0
    team_id: Optional[str] = None,
    strategy: Optional[str] = None
)
```

**Factory Methods:**

#### `create_defender(player_id, resource_budget, team_id) -> PlayerBase`
Create a defender player.

#### `create_attacker(player_id, resource_budget, team_id) -> PlayerBase`
Create an attacker player.

**Key Methods:**

#### `is_attacker() -> bool`
Check if player is an attacker.

#### `is_defender() -> bool`
Check if player is a defender.

#### `has_resources(required: float) -> bool`
Check if player has sufficient resources.

#### `to_dict() -> Dict[str, Any]`
Export player for integration.

**Export Format:**
```python
{
    "player_id": str,
    "role": str,
    "resource_budget": float,
    "team_id": Optional[str]
}
```

---

## Utility Classes

### ConfigLoader

Validates and parses system configurations from JSON/YAML files.

**Methods:**

#### `load_system(filepath: str) -> SystemInstance`
Load system from configuration file.

**Supported formats:** JSON, YAML (requires PyYAML)

#### `load_from_dict(config: Dict[str, Any]) -> SystemInstance`
Load system from configuration dictionary.

#### `validate_inputs(config: Dict[str, Any]) -> tuple[bool, Optional[str]]`
Validate configuration without loading.

**Returns:** `(is_valid, error_message)`

#### `save_system(system, filepath, include_players) -> None`
Save system configuration to file.

**Configuration Schema:**

```json
{
  "system_name": "string (required)",
  "system_class": "string",
  "subsystems": [
    {
      "id": "string (required)",
      "name": "string (required)",
      "connected_to": ["subsystem_ids"],
      "functional_dependencies": ["subsystem_ids"]
    }
  ],
  "vulnerabilities": [
    {
      "cve_id": "CVE-YYYY-NNNN (required)",
      "subsystem_id": "string (required)",
      "cvss_impact": 0.0-10.0,
      "cvss_exploitability": 0.0-10.0,
      "exploit_present": boolean,
      "patch_cost": number >= 0,
      "dependencies": ["cve_ids"]
    }
  ],
  "players": [
    {
      "player_id": "string",
      "role": "ATTACKER|DEFENDER",
      "resource_budget": number >= 0
    }
  ],
  "weights": {
    "functional_weight": 0.0-1.0,
    "topological_weight": 0.0-1.0
  }
}
```

---

### NVDImporter

Integrates with the NVD API to fetch CVE data.

**Constructor:**
```python
NVDImporter(
    api_key: Optional[str] = None,
    rate_limit_delay: float = 6.0
)
```

**Methods:**

#### `import_from_nvd(cve_ids, subsystem_id, default_patch_cost) -> List[Vulnerability]`
Import multiple CVEs from NVD.

**Parameters:**
- `cve_ids: List[str]` - CVE identifiers to fetch
- `subsystem_id: str` - Default subsystem ID
- `default_patch_cost: float` - Default patch cost

#### `fetch_cve(cve_id, subsystem_id, default_patch_cost) -> Optional[Vulnerability]`
Fetch a single CVE from NVD.

#### `search_by_keyword(keyword, max_results) -> List[str]`
Search for CVEs by keyword.

**Rate Limits:**
- Without API key: 6 seconds between requests
- With API key: 0.6 seconds between requests

---

### RiskCalculator

Calculates risk scores and importance metrics.

**Methods:**

#### `compute_importance(system, max_iterations, convergence_threshold) -> Dict[str, float]`
Compute importance scores for all subsystems using iterative algorithm.

**Algorithm:** PageRank-like iterative calculation combining functional dependencies and network topology.

**Returns:** Dictionary mapping subsystem IDs to importance scores [0.0, 1.0]

#### `score_vulnerability(vulnerability, subsystem, importance_weight) -> float`
Calculate comprehensive risk score for a vulnerability.

**Formula:**
```
risk_score = (cvss_score * (1 - w) + importance * 10 * w) 
             * exploit_multiplier * dependency_penalty
```

#### `score_all_vulnerabilities(system, importance_weight) -> Dict[str, float]`
Calculate risk scores for all vulnerabilities.

#### `rank_vulnerabilities(system, importance_weight) -> List[tuple]`
Rank vulnerabilities by risk score.

**Returns:** List of `(cve_id, score)` tuples, sorted descending.

#### `collapse_patch_dependencies(vulnerabilities) -> List[PatchGroup]`
Collapse vulnerabilities into patch groups based on dependencies.

#### `calculate_patching_priority(patch_groups, budget_constraint) -> List[str]`
Calculate optimal patching order using cost-benefit ratio.

#### `assess_system_risk(system) -> Dict[str, Any]`
Perform comprehensive risk assessment.

**Returns:**
```python
{
    "total_vulnerabilities": int,
    "critical_vulnerabilities": int,
    "high_vulnerabilities": int,
    "exploitable_vulnerabilities": int,
    "total_patch_cost": float,
    "average_risk_score": float,
    "max_risk_score": float,
    "most_critical_subsystem": dict,
    "subsystem_importance_scores": dict,
    "top_10_vulnerabilities": list
}
```

---

## Usage Patterns

### Pattern 1: Load from Configuration
```python
from data_model import ConfigLoader, RiskCalculator

loader = ConfigLoader()
system = loader.load_system("config/system.json")

calculator = RiskCalculator()
calculator.compute_importance(system)

export = system.export_for_game()
```

### Pattern 2: Build Programmatically
```python
from data_model import (
    SystemClass, SystemInstance, Subsystem,
    Vulnerability, PlayerBase
)

# Create components
system_class = SystemClass(name="MySystem")
subsystems = [
    Subsystem(id="sub1", name="Component 1"),
    Subsystem(id="sub2", name="Component 2")
]
vulnerabilities = [
    Vulnerability(
        cve_id="CVE-2024-0001",
        description="Test vuln",
        cvss_impact=8.0,
        cvss_exploitability=7.5,
        exploit_present=True,
        patch_cost=10.0,
        subsystem_id="sub1"
    )
]
subsystems[0].add_vulnerability(vulnerabilities[0])

# Create system
system = SystemInstance(system_class, subsystems)

# Export
export = system.export_for_game()
```

### Pattern 3: Enrich with NVD Data
```python
from data_model import NVDImporter

importer = NVDImporter(api_key="your_key")
cve_ids = ["CVE-2024-0001", "CVE-2024-0002"]
vulnerabilities = importer.import_from_nvd(
    cve_ids,
    subsystem_id="web_server",
    default_patch_cost=15.0
)

# Add to subsystem
for vuln in vulnerabilities:
    subsystem.add_vulnerability(vuln)
```

---

## Error Handling

All classes raise `ValueError` for validation errors:

```python
try:
    vuln = Vulnerability(
        cve_id="INVALID-2024-0001",  # Invalid format
        ...
    )
except ValueError as e:
    print(f"Validation error: {e}")
```

---

## Type Hints

All functions and methods include type hints for better IDE support:

```python
def export_for_game(
    self,
    players: Optional[List[PlayerBase]] = None,
    patch_grouping_method: str = "dependencies"
) -> Dict[str, Any]:
    ...
```

---

## Testing

Run tests with:
```bash
pytest tests/data_model/
```

Individual test files:
```bash
pytest tests/data_model/test_vulnerability.py -v
pytest tests/data_model/test_system.py -v
```

---

## Version History

### 1.0.0 (Current)
- Initial release
- Core data models (System, Subsystem, Vulnerability, PatchGroup, Player)
- Risk calculation algorithms
- NVD integration
- Configuration loading
- Integration export interface
