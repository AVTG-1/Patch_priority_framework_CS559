# Integration Guide - Developer A to Developer B

## Overview

This guide specifies how Developer A's data model module integrates with Developer B's game engine module through the `export_for_game()` interface.

## Integration Contract

**API Version:** 1.0.0

**Integration Direction:** A exports → B consumes

## Export Interface

### Primary Method

```python
SystemInstance.export_for_game(players: List[PlayerBase] = None) -> dict
```

### Export Dictionary Schema

```python
{
    "api_version": "1.0.0",
    "system_name": str,
    "subsystems": List[dict],
    "functional_dependencies": List[List[int]],
    "network_topology": List[List[int]],
    "weights": dict,
    "patch_groups": List[dict],
    "players": List[dict]
}
```

## Detailed Specifications

### 1. Subsystem Export Format

```python
{
    "id": str,
    "name": str,
    "importance_score": float,
    "vulnerabilities": List[dict]
}
```

**Constraints:**
- `id` must be unique across all subsystems
- `importance_score` range: [0.0, 1.0]
- Order in list determines matrix indices

### 2. Vulnerability Export Format

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

**Constraints:**
- `cvss_impact`, `cvss_exploitability`: [0.0, 10.0]
- `patch_cost`: positive float
- `dependencies`: list of cve_ids (can be empty)

### 3. Dependency Matrices

**Functional Dependencies:**
- Square matrix: N×N where N = number of subsystems
- `functional_dependencies[i][j] = 1` if subsystem i depends on j
- Diagonal typically 0 (subsystem doesn't depend on itself)

**Network Topology:**
- Square matrix: N×N
- `network_topology[i][j] = 1` if subsystems i and j are connected
- Typically symmetric for network connections

**Example:**
```python
# For 3 subsystems: [Web, App, DB]
functional_dependencies = [
    [0, 1, 1],  # Web depends on App and DB
    [0, 0, 1],  # App depends on DB
    [0, 0, 0]   # DB depends on nothing
]

network_topology = [
    [0, 1, 0],  # Web connected to App
    [1, 0, 1],  # App connected to Web and DB
    [0, 1, 0]   # DB connected to App
]
```

### 4. Weights Format

```python
{
    "functional_weight": float,  # Typically 0.0-1.0
    "topological_weight": float  # Typically 0.0-1.0
}
```

**Constraints:**
- Both weights should sum to approximately 1.0 for balanced importance calculation
- Adjust based on system characteristics

### 5. Patch Group Format

```python
{
    "group_id": str,
    "cve_ids": List[str],
    "total_cost": float,
    "aggregate_impact": float
}
```

**Constraints:**
- `group_id` must be unique
- `cve_ids`: non-empty list of vulnerability IDs in this group
- `total_cost`: sum or adjusted cost for patching all CVEs in group
- `aggregate_impact`: combined impact metric

### 6. Player Format

```python
{
    "player_id": str,
    "role": str,  # "ATTACKER" or "DEFENDER"
    "resource_budget": float,
    "team_id": Optional[str]
}
```

**Constraints:**
- `role` must be exactly "ATTACKER" or "DEFENDER"
- `resource_budget`: positive float
- `team_id`: optional, for multi-team scenarios

## Usage Example

### Developer A (Exporting)

```python
from data_model import SystemInstance, ConfigLoader

# Load or create system
system = ConfigLoader().load_system("config/system.json")

# Export for Developer B
export_dict = system.export_for_game()

# Verify export
assert "api_version" in export_dict
assert export_dict["api_version"] == "1.0.0"
assert len(export_dict["subsystems"]) > 0
```

### Developer B (Consuming)

```python
from game_engine import GameState

# Receive export from Developer A
export_dict = system.export_for_game()

# Load into game state
game_state = GameState.load_from_export(export_dict)

# Run simulation
# ... (Developer B's code)
```

## Validation Rules

Developer A guarantees:
1. All dictionary keys match specification exactly
2. Matrix dimensions are square and match subsystem count
3. All values are JSON-serializable (no numpy arrays in final export)
4. No null/None values except where explicitly Optional
5. All referenced IDs (subsystem_id, cve_id) exist in the export

## Testing Integration

### Sample Export Location

```
tests/integration/sample_export.json
```

Developer B can use this file for development and testing without requiring Developer A's module.

### Generate Sample Export

```python
from data_model import ConfigLoader

loader = ConfigLoader()
system = loader.load_system("config/example_system.json")
export = system.export_for_game()

import json
with open("tests/integration/sample_export.json", "w") as f:
    json.dump(export, f, indent=2)
```

## Error Handling

If Developer B encounters issues:
1. Verify `api_version` matches expected version
2. Validate all required keys are present
3. Check matrix dimensions match subsystem count
4. Ensure all ID references are valid

## Version Compatibility

- **1.0.0**: Initial release
- Future versions will be backward-compatible or provide migration path
- Breaking changes will increment major version

## Contact Points

**Data Format Issues:** Contact Developer A  
**Simulation Logic Issues:** Contact Developer B  
**Integration Issues:** Coordinate between both developers

## Migration Guide

When API changes occur:
1. Update `api_version` in export
2. Document changes in this guide
3. Provide sample exports for new version
4. Update integration tests

## Sample Full Export

See `tests/integration/sample_export.json` for complete example with all fields populated.
