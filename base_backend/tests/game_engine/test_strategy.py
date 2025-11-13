"""
Tests for Strategy module
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from game_engine import (
    StrategySet,
    enumerate_defender_strategies,
    enumerate_attacker_strategies,
    create_strategy_set,
    get_strategy_cost
)


class TestStrategySet:
    """Test suite for StrategySet."""
    
    def test_create_strategy_set(self):
        """Test creating a strategy set."""
        strategies = [['A'], ['B'], ['A', 'B']]
        strategy_set = StrategySet('player1', 'DEFENDER', strategies)
        
        assert strategy_set.player_id == 'player1'
        assert strategy_set.player_role == 'DEFENDER'
        assert strategy_set.get_strategy_count() == 3
        assert not strategy_set.is_mixed
    
    def test_create_mixed_strategy(self):
        """Test creating mixed strategy set."""
        strategies = [['A'], ['B']]
        probabilities = [0.7, 0.3]
        strategy_set = StrategySet('player1', 'DEFENDER', strategies, probabilities)
        
        assert strategy_set.is_mixed
        assert strategy_set.get_probability(0) == 0.7
        assert strategy_set.get_probability(1) == 0.3
    
    def test_invalid_probabilities_length(self):
        """Test that probability length must match strategies."""
        strategies = [['A'], ['B'], ['C']]
        probabilities = [0.5, 0.5]  # Wrong length
        
        with pytest.raises(ValueError, match="must match number of strategies"):
            StrategySet('player1', 'DEFENDER', strategies, probabilities)
    
    def test_invalid_probability_sum(self):
        """Test that probabilities must sum to 1."""
        strategies = [['A'], ['B']]
        probabilities = [0.6, 0.6]  # Sum > 1
        
        with pytest.raises(ValueError, match="must sum to 1.0"):
            StrategySet('player1', 'DEFENDER', strategies, probabilities)
    
    def test_negative_probabilities(self):
        """Test that negative probabilities are invalid."""
        strategies = [['A'], ['B']]
        probabilities = [1.2, -0.2]
        
        with pytest.raises(ValueError, match="cannot be negative"):
            StrategySet('player1', 'DEFENDER', strategies, probabilities)
    
    def test_get_strategy(self):
        """Test retrieving strategy by index."""
        strategies = [['A'], ['B'], ['A', 'B']]
        strategy_set = StrategySet('player1', 'DEFENDER', strategies)
        
        assert strategy_set.get_strategy(0) == ['A']
        assert strategy_set.get_strategy(2) == ['A', 'B']
    
    def test_set_probabilities(self):
        """Test updating probability distribution."""
        strategies = [['A'], ['B'], ['C']]
        strategy_set = StrategySet('player1', 'DEFENDER', strategies)
        
        new_probs = [0.5, 0.3, 0.2]
        strategy_set.set_probabilities(new_probs)
        
        assert strategy_set.probabilities == new_probs
        assert strategy_set.is_mixed
    
    def test_sample_strategy(self):
        """Test sampling from strategy distribution."""
        strategies = [['A'], ['B']]
        probabilities = [1.0, 0.0]  # Deterministic
        strategy_set = StrategySet('player1', 'DEFENDER', strategies, probabilities)
        
        # Sample multiple times, should always get strategy 0
        for _ in range(10):
            idx, strategy = strategy_set.sample_strategy()
            assert idx == 0
            assert strategy == ['A']
    
    def test_to_dict(self):
        """Test exporting strategy set to dictionary."""
        strategies = [['A'], ['B']]
        strategy_set = StrategySet('player1', 'DEFENDER', strategies)
        
        result = strategy_set.to_dict()
        
        assert result['player_id'] == 'player1'
        assert result['player_role'] == 'DEFENDER'
        assert result['strategy_count'] == 2
        assert result['strategies'] == strategies


class TestStrategyEnumeration:
    """Test strategy enumeration functions."""
    
    def test_enumerate_defender_strategies_basic(self):
        """Test basic defender strategy enumeration."""
        patch_groups = [
            {'group_id': 'PG1', 'total_cost': 5.0},
            {'group_id': 'PG2', 'total_cost': 3.0}
        ]
        
        strategies = enumerate_defender_strategies(patch_groups, resource_budget=10.0)
        
        # Should include: [], [PG2], [PG1], [PG2, PG1]
        assert len(strategies) >= 3
        assert [] in strategies
        assert ['PG2'] in strategies or ['PG1'] in strategies
    
    def test_enumerate_defender_strategies_budget_limit(self):
        """Test that budget limits strategies."""
        patch_groups = [
            {'group_id': 'PG1', 'total_cost': 5.0},
            {'group_id': 'PG2', 'total_cost': 8.0}
        ]
        
        strategies = enumerate_defender_strategies(patch_groups, resource_budget=6.0)
        
        # Should not include both PG1 and PG2 together
        assert ['PG1', 'PG2'] not in strategies
        assert ['PG2', 'PG1'] not in strategies
    
    def test_enumerate_attacker_strategies_basic(self):
        """Test basic attacker strategy enumeration."""
        vulnerabilities = [
            {'cve_id': 'CVE-1', 'cvss_exploitability': 8.0},
            {'cve_id': 'CVE-2', 'cvss_exploitability': 6.0}
        ]
        
        strategies = enumerate_attacker_strategies(vulnerabilities, resource_budget=10.0)
        
        # Should include empty strategy and individual attacks
        assert [] in strategies
        assert len(strategies) >= 3
    
    def test_enumerate_strategies_max_limit(self):
        """Test max strategies limit."""
        patch_groups = [
            {'group_id': f'PG{i}', 'total_cost': 1.0}
            for i in range(20)
        ]
        
        strategies = enumerate_defender_strategies(
            patch_groups,
            resource_budget=100.0,
            max_strategies=50
        )
        
        assert len(strategies) <= 50
    
    def test_create_strategy_set_defender(self):
        """Test creating strategy set for defender."""
        player = {
            'player_id': 'def1',
            'role': 'DEFENDER',
            'resource_budget': 50.0
        }
        patch_groups = [
            {'group_id': 'PG1', 'total_cost': 10.0},
            {'group_id': 'PG2', 'total_cost': 15.0}
        ]
        vulnerabilities = []
        
        strategy_set = create_strategy_set(player, patch_groups, vulnerabilities)
        
        assert strategy_set.player_id == 'def1'
        assert strategy_set.player_role == 'DEFENDER'
        assert strategy_set.get_strategy_count() > 0
    
    def test_create_strategy_set_attacker(self):
        """Test creating strategy set for attacker."""
        player = {
            'player_id': 'att1',
            'role': 'ATTACKER',
            'resource_budget': 30.0
        }
        patch_groups = []
        vulnerabilities = [
            {'cve_id': 'CVE-1', 'cvss_exploitability': 7.0},
            {'cve_id': 'CVE-2', 'cvss_exploitability': 5.0}
        ]
        
        strategy_set = create_strategy_set(player, patch_groups, vulnerabilities)
        
        assert strategy_set.player_id == 'att1'
        assert strategy_set.player_role == 'ATTACKER'
        assert strategy_set.get_strategy_count() > 0
    
    def test_get_strategy_cost_defender(self):
        """Test calculating defender strategy cost."""
        strategy = ['PG1', 'PG2']
        patch_groups = [
            {'group_id': 'PG1', 'total_cost': 10.0},
            {'group_id': 'PG2', 'total_cost': 15.0},
            {'group_id': 'PG3', 'total_cost': 5.0}
        ]
        
        cost = get_strategy_cost(strategy, patch_groups, [], 'DEFENDER')
        assert cost == 25.0
    
    def test_get_strategy_cost_attacker(self):
        """Test calculating attacker strategy cost."""
        strategy = ['CVE-1', 'CVE-2']
        vulnerabilities = [
            {'cve_id': 'CVE-1', 'cvss_exploitability': 8.0},  # Cost = 2.0
            {'cve_id': 'CVE-2', 'cvss_exploitability': 6.0}   # Cost = 4.0
        ]
        
        cost = get_strategy_cost(strategy, [], vulnerabilities, 'ATTACKER')
        assert cost == 6.0  # 2.0 + 4.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
