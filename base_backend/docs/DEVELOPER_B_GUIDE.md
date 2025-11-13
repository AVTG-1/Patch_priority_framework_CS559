# Developer B Implementation Guide

## Overview

Developer B's module (`game_engine`) implements the game-theoretic simulation engine that:
1. Loads exports from Developer A
2. Enumerates strategies for attackers and defenders
3. Computes Nash equilibria
4. Simulates multi-round patch prioritization games
5. Exports results back to Developer A

## Architecture

```
Developer A Export (dict)
    ↓
GameState.load_from_export()
    ↓
Strategy Enumeration
    ↓
Payoff Matrix Construction
    ↓
Nash Equilibrium Computation
    ↓
Multi-Round Simulation
    ↓
SimulationResult.export_to_dict()
    ↓
Developer A (display/analysis)
```

## Core Components

### 1. GameState (`game_state.py`)
**Purpose:** Manages current game state and tracks progress

**Key Methods:**
- `load_from_export(export_dict)` - Load from Developer A's export
- `apply_patches(cve_ids)` - Apply defender patches
- `exploit_vulnerabilities(cve_ids)` - Mark attacker exploits
- `calculate_remaining_impact()` - Compute RIS (Remaining Impact Score)
- `get_patchable_vulnerabilities()` - Get vulnerabilities ready to patch

**Usage:**
```python
from game_engine import GameState

# Load from Developer A
game_state = GameState.load_from_export(export_dict)

# Apply actions
game_state.apply_patch_group("PG_0001")
game_state.exploit_vulnerabilities(["CVE-2024-0001"])

# Check state
ris = game_state.calculate_remaining_impact()
```

### 2. Strategy (`strategy.py`)
**Purpose:** Enumerate and manage strategies for players

**Key Functions:**
- `enumerate_defender_strategies()` - Generate all feasible patch combinations
- `enumerate_attacker_strategies()` - Generate all feasible exploit combinations
- `create_strategy_set()` - Create StrategySet for a player
- `filter_dominated_strategies()` - Remove strictly dominated strategies

**Usage:**
```python
from game_engine import create_strategy_set

# Create defender strategy set
defender_strategies = create_strategy_set(
    player=defender,
    patch_groups=game_state.patch_groups,
    vulnerabilities=game_state.remaining_vulnerabilities
)

# Access strategies
for i in range(defender_strategies.get_strategy_count()):
    strategy = defender_strategies.get_strategy(i)
    print(f"Strategy {i}: {strategy}")
```

### 3. NashSolver (`nash_solver.py`)
**Purpose:** Compute pure and mixed Nash equilibria

**Dependencies:** `nashpy` library

**Key Methods:**
- `compute_pure_nash()` - Find all pure strategy Nash equilibria
- `compute_mixed_nash()` - Find mixed strategy Nash equilibria
- `find_best_equilibrium()` - Find best equilibrium for a player
- `compute_expected_payoffs()` - Calculate expected payoffs

**Usage:**
```python
from game_engine import NashSolver
import numpy as np

solver = NashSolver()

# Find pure equilibria
pure_eq = solver.compute_pure_nash(
    defender_payoffs,
    attacker_payoffs
)

# Find mixed equilibria
mixed_eq = solver.compute_mixed_nash(
    defender_payoffs,
    attacker_payoffs
)

# Get best equilibrium
best_eq = solver.find_best_equilibrium(
    defender_payoffs,
    attacker_payoffs,
    preference="defender"
)
```

### 4. Simulator (`simulator.py`)
**Purpose:** Run multi-round simulations

**Key Methods:**
- `build_payoff_matrices()` - Construct payoff matrices from strategies
- `run_round()` - Execute one simulation round
- `run_simulation()` - Execute complete simulation
- `get_patch_priority_list()` - Extract patch priorities

**Usage:**
```python
from game_engine import Simulator

simulator = Simulator(
    game_state,
    simulation_length=10,
    discount_factor=0.9
)

# Run simulation
results = simulator.run_simulation()

# Access results
print(f"Initial RIS: {results['initial_ris']}")
print(f"Final RIS: {results['final_ris']}")
print(f"Patches applied: {results['total_vulnerabilities_patched']}")
```

### 5. SimulationResult (`simulation_result.py`)
**Purpose:** Package results for export to Developer A

**Key Methods:**
- `from_simulation()` - Create from Simulator output
- `export_to_dict()` - Export as dictionary (integration contract)
- `export_to_json()` - Save to JSON file
- `get_summary()` - Human-readable summary

**Usage:**
```python
from game_engine import SimulationResult

result = SimulationResult.from_simulation(simulation_results)

# Export for Developer A
export_dict = result.export_to_dict()

# Save to file
result.export_to_json("results.json")

# Print summary
print(result.get_summary())
```

## Integration Points

### Input (from Developer A)
**Contract:** Dictionary from `SystemInstance.export_for_game()`

**Required Keys:**
- `api_version` - Must be "1.0.0"
- `system_name` - System identifier
- `subsystems` - List with vulnerabilities
- `functional_dependencies` - N×N matrix
- `network_topology` - N×N matrix
- `weights` - Functional/topological weights
- `patch_groups` - Aggregated patches
- `players` - Attacker/defender configs

**Validation:** `GameState._validate_export()` checks format

### Output (to Developer A)
**Contract:** Dictionary from `SimulationResult.export_to_dict()`

**Required Keys:**
- `patch_priority_list` - Ordered patch group IDs
- `ris_summary` - RIS value per round
- `equilibrium_report` - Nash equilibrium statistics
- `per_round_details` - Round-by-round results

## Algorithms

### Strategy Enumeration
Enumerates all feasible strategy combinations within resource budget using combinatorial generation with cost constraints.

### Payoff Calculation
```
Defender Payoff = -(Attack Impact) - α*(Patch Cost)
Attacker Payoff = (Attack Impact) - β*(Exploit Cost)

Attack Impact = Σ(CVSS_impact × Importance × Exploit_Multiplier)
```

### Nash Equilibrium
Uses `nashpy` library:
- Pure: Brute force checking of best responses
- Mixed: Support enumeration or Lemke-Howson algorithm

### RIS Calculation
```
RIS = Σ(CVSS_impact × Subsystem_Importance × Exploit_Multiplier)
```
For all remaining unpatched vulnerabilities.

## Testing

### Unit Tests
- `test_game_state.py` - 20+ tests for GameState
- `test_strategy.py` - 15+ tests for strategy enumeration
- `test_nash_solver.py` - 10+ tests for equilibrium computation
- `test_simulator.py` - 15+ tests for simulation

### Integration Tests
- `test_full_pipeline.py` - End-to-end workflow tests

**Run Tests:**
```bash
# All Developer B tests
pytest tests/game_engine/ -v

# Specific module
pytest tests/game_engine/test_game_state.py -v

# Integration tests
pytest tests/integration/ -v
```

## Performance Considerations

### Strategy Enumeration
- Limited to 100-1000 strategies per player for tractability
- Exponential in number of patch groups/vulnerabilities
- Use `max_strategies` parameter to control

### Nash Computation
- Pure NE: O(n×m) where n,m are strategy counts
- Mixed NE: Exponential in worst case (support enumeration)
- Falls back to Lemke-Howson for large games

### Simulation
- Each round: O(n×m) for payoff matrix construction
- Total: O(rounds × n × m)
- Typically 10-20 rounds sufficient

## Common Usage Patterns

### Pattern 1: Quick Simulation
```python
from game_engine import GameState, Simulator, SimulationResult

# Load, simulate, export
game_state = GameState.load_from_export(export_dict)
simulator = Simulator(game_state, simulation_length=5)
results = simulator.run_simulation()
result = SimulationResult.from_simulation(results)
print(result.get_summary())
```

### Pattern 2: Custom Strategy Analysis
```python
from game_engine import create_strategy_set, NashSolver

# Create custom strategies
defender_strategies = create_strategy_set(...)
attacker_strategies = create_strategy_set(...)

# Analyze equilibria
solver = NashSolver()
equilibrium = solver.find_best_equilibrium(
    defender_payoffs,
    attacker_payoffs
)
```

### Pattern 3: Multi-Scenario Analysis
```python
results_list = []
for discount_factor in [0.7, 0.8, 0.9]:
    game_state = GameState.load_from_export(export_dict)
    simulator = Simulator(game_state, discount_factor=discount_factor)
    results = simulator.run_simulation()
    results_list.append(results)
```

## Troubleshooting

### Issue: Nash equilibrium not found
**Solution:** Game may be too large. Reduce max_strategies or use random sampling.

### Issue: Simulation runs slowly
**Solution:** Reduce simulation_length or max_strategies parameter.

### Issue: Import fails from Developer A
**Solution:** Check API version compatibility and validate export format.

### Issue: RIS not decreasing
**Solution:** Check that patches are being applied correctly and budget is sufficient.

## Extensions

### Adding New Strategy Types
1. Add enumeration function in `strategy.py`
2. Update `create_strategy_set()` to support new type
3. Add tests

### Custom Payoff Functions
1. Override `Simulator._compute_payoffs()`
2. Implement custom logic
3. Maintain interface compatibility

### Additional Equilibrium Concepts
1. Add new solver methods in `NashSolver`
2. Update `find_best_equilibrium()` if needed
3. Document in equilibrium report

## API Version History

**1.0.0** (Current)
- Initial implementation
- Basic game-theoretic framework
- Pure and mixed Nash equilibria
- Multi-round simulation

## References

- nashpy documentation: https://nashpy.readthedocs.io/
- Game Theory textbooks for equilibrium concepts
- CVSS specification for impact scoring
