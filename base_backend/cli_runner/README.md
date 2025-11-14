# CLI Simulation Runner

Run patch prioritization simulations directly from the command line using JSON configuration files.

## Quick Start

```bash
# Run simulation with verbose output
python run_simulation.py example_config.json --verbose

# Save results to file
python run_simulation.py example_config.json --output results.json

# Validate configuration without running
python run_simulation.py example_config.json --validate-only
```

## Configuration File Format

The JSON configuration must include:

### Required Fields

- **`system_name`** (string): Name of the system
- **`subsystems`** (array): List of subsystem definitions
- **`vulnerabilities`** (array): List of vulnerabilities

### Subsystem Structure

```json
{
  "id": "unique_id",
  "name": "Display Name",
  "functional_dependencies": ["other_subsystem_id"],
  "connected_to": ["topology_connected_subsystem"]
}
```

### Vulnerability Structure

```json
{
  "cve_id": "CVE-2024-1234",
  "subsystem_id": "subsystem_id",
  "cvss_impact": 7.5,
  "cvss_exploitability": 8.6,
  "patch_cost": 2.0,
  "description": "Vulnerability description",
  "exploit_present": true,
  "dependencies": ["other_cve_id"],
  "source": "NVD"
}
```

**Required vulnerability fields:**
- `cve_id`: Must match pattern `^(CVE-|CUSTOM-)`
- `subsystem_id`: Must match a subsystem `id`
- `cvss_impact`: Float 0-10
- `cvss_exploitability`: Float 0-10
- `patch_cost`: Float >= 0

### Optional Fields

**Players Configuration:**
```json
"players": [
  {
    "player_id": "defender_1",
    "role": "DEFENDER",
    "resource_budget": 200.0
  },
  {
    "player_id": "attacker_1",
    "role": "ATTACKER",
    "resource_budget": 100.0
  }
]
```

**Simulation Parameters:**
```json
"simulation_rounds": 10,
"patch_grouping_method": "dependencies",
"weights": {
  "functional_dependency_weight": 0.7,
  "topological_dependency_weight": 0.3
}
```

**Patch Grouping Methods:**
- `dependencies`: Group patches by vulnerability dependencies
- `subsystem`: Group patches by affected subsystem
- `severity`: Group patches by CVSS score

## Examples

### Example 1: Simple System

```json
{
  "system_name": "Simple Web Server",
  "subsystems": [
    {
      "id": "main",
      "name": "Web Server",
      "functional_dependencies": []
    }
  ],
  "vulnerabilities": [
    {
      "cve_id": "CVE-2024-1234",
      "subsystem_id": "main",
      "cvss_impact": 7.5,
      "cvss_exploitability": 8.6,
      "patch_cost": 1.0,
      "description": "SQL injection",
      "exploit_present": true,
      "dependencies": [],
      "source": "NVD"
    }
  ],
  "simulation_rounds": 5
}
```

### Example 2: Multi-tier System with Dependencies

```json
{
  "system_name": "E-commerce Platform",
  "subsystems": [
    {
      "id": "frontend",
      "name": "Frontend",
      "functional_dependencies": ["backend", "cdn"]
    },
    {
      "id": "backend",
      "name": "Backend API",
      "functional_dependencies": ["database"]
    },
    {
      "id": "database",
      "name": "Database",
      "functional_dependencies": []
    },
    {
      "id": "cdn",
      "name": "CDN",
      "functional_dependencies": []
    }
  ],
  "vulnerabilities": [
    {
      "cve_id": "CVE-2024-1111",
      "subsystem_id": "frontend",
      "cvss_impact": 6.5,
      "cvss_exploitability": 9.0,
      "patch_cost": 1.0,
      "description": "XSS vulnerability"
    },
    {
      "cve_id": "CVE-2024-2222",
      "subsystem_id": "backend",
      "cvss_impact": 8.5,
      "cvss_exploitability": 7.2,
      "patch_cost": 3.0,
      "description": "Authentication bypass"
    },
    {
      "cve_id": "CVE-2024-3333",
      "subsystem_id": "database",
      "cvss_impact": 9.5,
      "cvss_exploitability": 6.0,
      "patch_cost": 5.0,
      "description": "SQL injection in ORM"
    }
  ],
  "players": [
    {
      "player_id": "security_team",
      "role": "DEFENDER",
      "resource_budget": 150.0
    },
    {
      "player_id": "threat_actor",
      "role": "ATTACKER",
      "resource_budget": 75.0
    }
  ],
  "simulation_rounds": 12,
  "patch_grouping_method": "dependencies"
}
```

## Output Format

The simulation produces JSON output with:

```json
{
  "patch_priority_list": ["group_1", "group_2", ...],
  "ris_summary": [10.5, 8.3, 6.1, ...],
  "equilibrium_report": {
    "total_defender_payoff": 100.0,
    "total_attacker_payoff": 50.0,
    ...
  },
  "per_round_details": [...],
  "system_info": {
    "system_name": "...",
    "subsystem_count": 4,
    "vulnerability_count": 10,
    ...
  },
  "simulation_metrics": {
    "initial_ris": 10.5,
    "final_ris": 2.3,
    "ris_reduction": 8.2,
    "ris_reduction_percentage": 78.1,
    ...
  }
}
```

## Usage Tips

1. **Start with validation**: Use `--validate-only` to check your configuration before running
2. **Use verbose mode**: Add `--verbose` to see detailed progress and results
3. **Adjust budgets**: Higher defender budgets allow more patches per round
4. **Tune dependencies**: Functional dependencies affect importance calculations
5. **Experiment with grouping**: Try different `patch_grouping_method` values

## Troubleshooting

**"Configuration validation failed"**: Check that all required fields are present and CVE IDs match the pattern.

**"RIS values are 0"**: Ensure vulnerabilities have non-zero CVSS scores and are properly assigned to subsystems.

**"No patch groups created"**: Check that `patch_grouping_method` is valid and vulnerabilities have appropriate dependencies.

## Advanced: Scripting

```bash
#!/bin/bash
# Run multiple simulations with different parameters

for budget in 50 100 150 200; do
  # Modify config with new budget
  jq ".players[0].resource_budget = $budget" base_config.json > config_$budget.json

  # Run simulation
  python run_simulation.py config_$budget.json --output results_$budget.json
done

# Compare results
echo "Budget,Initial RIS,Final RIS,Reduction %"
for budget in 50 100 150 200; do
  jq -r ". | [.system_info.simulation_rounds, .simulation_metrics.initial_ris, .simulation_metrics.final_ris, .simulation_metrics.ris_reduction_percentage] | @csv" results_$budget.json
done
```
