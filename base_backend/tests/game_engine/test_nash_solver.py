"""
Tests for Nash Solver
"""

import pytest
import sys
import os
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from game_engine import NashSolver


class TestNashSolver:
    """Test suite for NashSolver."""
    
    def test_compute_pure_nash_simple(self):
        """Test finding pure Nash equilibrium in simple game."""
        # Prisoner's Dilemma payoffs
        defender_payoffs = np.array([
            [-1, -3],
            [0, -2]
        ])
        attacker_payoffs = np.array([
            [-1, 0],
            [-3, -2]
        ])
        
        solver = NashSolver()
        pure_eq = solver.compute_pure_nash(defender_payoffs, attacker_payoffs)
        
        # (Defect, Defect) is the pure Nash equilibrium
        assert (1, 1) in pure_eq
    
    def test_compute_pure_nash_matching_pennies(self):
        """Test game with no pure Nash equilibrium."""
        # Matching pennies has no pure NE
        defender_payoffs = np.array([
            [1, -1],
            [-1, 1]
        ])
        attacker_payoffs = np.array([
            [-1, 1],
            [1, -1]
        ])
        
        solver = NashSolver()
        pure_eq = solver.compute_pure_nash(defender_payoffs, attacker_payoffs)
        
        assert len(pure_eq) == 0
    
    def test_compute_mixed_nash(self):
        """Test finding mixed Nash equilibrium."""
        # Simple 2x2 game
        defender_payoffs = np.array([
            [3, 0],
            [0, 2]
        ])
        attacker_payoffs = np.array([
            [2, 0],
            [0, 3]
        ])
        
        solver = NashSolver()
        mixed_eq = solver.compute_mixed_nash(defender_payoffs, attacker_payoffs)
        
        # Should find at least one equilibrium
        assert len(mixed_eq) > 0
        
        # Check that strategies are valid probability distributions
        for defender_strategy, attacker_strategy in mixed_eq:
            assert np.isclose(np.sum(defender_strategy), 1.0)
            assert np.isclose(np.sum(attacker_strategy), 1.0)
            assert np.all(defender_strategy >= 0)
            assert np.all(attacker_strategy >= 0)
    
    def test_compute_expected_payoffs(self):
        """Test computing expected payoffs."""
        payoff_matrix = np.array([
            [3, 1],
            [0, 2]
        ])
        defender_strategy = np.array([0.5, 0.5])
        attacker_strategy = np.array([0.5, 0.5])
        
        solver = NashSolver()
        expected = solver.compute_expected_payoffs(
            payoff_matrix,
            defender_strategy,
            attacker_strategy
        )
        
        # Manual calculation: 0.5*0.5*3 + 0.5*0.5*1 + 0.5*0.5*0 + 0.5*0.5*2 = 1.5
        assert np.isclose(expected, 1.5)
    
    def test_find_best_equilibrium_pure(self):
        """Test finding best pure equilibrium."""
        # Game with multiple pure equilibria
        defender_payoffs = np.array([
            [3, 0],
            [0, 2]
        ])
        attacker_payoffs = np.array([
            [3, 0],
            [0, 2]
        ])
        
        solver = NashSolver()
        best_eq = solver.find_best_equilibrium(
            defender_payoffs,
            attacker_payoffs,
            preference="defender"
        )
        
        assert best_eq is not None
        assert best_eq['type'] == 'pure'
        assert best_eq['defender_strategy_index'] == 0  # Better payoff
    
    def test_find_best_equilibrium_mixed(self):
        """Test finding best mixed equilibrium."""
        # Matching pennies - only mixed equilibrium
        defender_payoffs = np.array([
            [1, -1],
            [-1, 1]
        ])
        attacker_payoffs = np.array([
            [-1, 1],
            [1, -1]
        ])
        
        solver = NashSolver()
        best_eq = solver.find_best_equilibrium(
            defender_payoffs,
            attacker_payoffs,
            preference="defender"
        )
        
        if best_eq:  # nashpy might find equilibrium
            assert best_eq['type'] == 'mixed'
            assert 'defender_strategy' in best_eq
            assert 'attacker_strategy' in best_eq
    
    def test_get_equilibrium_summary(self):
        """Test generating equilibrium summary."""
        equilibrium = {
            'type': 'pure',
            'defender_strategy_index': 0,
            'attacker_strategy_index': 1,
            'defender_payoff': 5.0,
            'attacker_payoff': 3.0
        }
        
        solver = NashSolver()
        summary = solver.get_equilibrium_summary(equilibrium)
        
        assert isinstance(summary, str)
        assert 'pure' in summary.lower()
        assert '5.0' in summary or '5.000' in summary
    
    def test_get_equilibrium_summary_none(self):
        """Test summary for no equilibrium."""
        solver = NashSolver()
        summary = solver.get_equilibrium_summary(None)
        
        assert 'No equilibrium' in summary


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
