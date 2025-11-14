#!/usr/bin/env python3
"""Debug script to check matrix construction"""

import sys
import os
import json

# Add base_backend/src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from data_model import ConfigLoader, RiskCalculator

def main():
    # Load simple_test.json
    config_path = os.path.join(os.path.dirname(__file__), 'simple_test.json')
    with open(config_path, 'r') as f:
        config = json.load(f)

    # Load system
    loader = ConfigLoader()
    system = loader.load_from_dict(config)

    print("System loaded successfully!")
    print(f"Subsystems: {len(system.subsystems)}")
    for i, subsys in enumerate(system.subsystems):
        print(f"  [{i}] {subsys.name} (id: {subsys.id})")
        print(f"      functional_deps: {subsys.functional_deps}")
        print(f"      connected_ids: {subsys.connected_ids}")

    print(f"\nFunctional dependency matrix (w_adj):")
    print(system.w_adj)

    print(f"\nTopology matrix (n_topology):")
    print(system.n_topology)

    print(f"\nWeights:")
    print(f"  functional_weight: {system.weights.get('functional_weight', 'N/A')}")
    print(f"  topological_weight: {system.weights.get('topological_weight', 'N/A')}")

    # Calculate importance with debug
    import numpy as np

    n = len(system.subsystems)
    w_func = system.weights.get("functional_weight", 0.6)
    w_topo = system.weights.get("topological_weight", 0.4)

    # Initialize importance scores uniformly
    importance_vec = np.ones(n) / n
    print(f"\nInitial importance: {importance_vec}")

    # Get dependency matrices
    W = system.w_adj.astype(float)
    N = system.n_topology.astype(float)

    print(f"\nW matrix:\n{W}")
    print(f"N matrix:\n{N}")

    # Normalize matrices by row sums (avoid division by zero)
    W_row_sums = W.sum(axis=1, keepdims=True)
    print(f"\nW_row_sums before fix: {W_row_sums.T}")
    W_row_sums[W_row_sums == 0] = 1
    print(f"W_row_sums after fix: {W_row_sums.T}")
    W_norm = W / W_row_sums
    print(f"W_norm:\n{W_norm}")

    N_row_sums = N.sum(axis=1, keepdims=True)
    N_row_sums[N_row_sums == 0] = 1
    N_norm = N / N_row_sums
    print(f"N_norm:\n{N_norm}")

    # Do one iteration manually
    print(f"\nManual iteration:")
    print(f"W_norm.T:\n{W_norm.T}")
    print(f"W_norm.T @ importance_vec: {W_norm.T @ importance_vec}")
    print(f"N_norm.T @ importance_vec: {N_norm.T @ importance_vec}")

    new_importance = w_func * (W_norm.T @ importance_vec) + w_topo * (N_norm.T @ importance_vec)
    print(f"new_importance before normalization: {new_importance}")
    print(f"sum: {new_importance.sum()}")

    if new_importance.sum() > 0:
        new_importance = new_importance / new_importance.sum()
    else:
        new_importance = np.zeros_like(new_importance)
    print(f"new_importance after normalization: {new_importance}")

    # Now run the actual calculator with debug
    print(f"\n" + "="*80)
    print(f"Running RiskCalculator.compute_importance() with debug=True:")
    print(f"="*80)
    calculator = RiskCalculator()
    importance = calculator.compute_importance(system, debug=True)

    print(f"\nFinal importance scores from RiskCalculator:")
    for subsys_id, score in importance.items():
        print(f"  {subsys_id}: {score}")

if __name__ == "__main__":
    main()
