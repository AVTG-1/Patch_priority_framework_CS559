"""
Strategy Module

Handles strategy enumeration, validation, and management for attackers and defenders.
"""

from typing import List, Dict, Any, Optional, Tuple
from itertools import combinations
import numpy as np


class StrategySet:
    """
    Represents a set of possible strategies for a player.
    
    Attributes:
        player_id: ID of the player
        player_role: "ATTACKER" or "DEFENDER"
        strategies: List of strategies (each is a list of actions)
        probabilities: Probability distribution over strategies (for mixed)
        is_mixed: Whether this represents a mixed strategy
    """
    
    def __init__(self, 
                 player_id: str,
                 player_role: str,
                 strategies: List[List[str]],
                 probabilities: Optional[List[float]] = None):
        """
        Initialize strategy set.
        
        Args:
            player_id: Player identifier
            player_role: "ATTACKER" or "DEFENDER"
            strategies: List of strategy profiles
            probabilities: Optional probabilities for mixed strategies
        """
        self.player_id = player_id
        self.player_role = player_role
        self.strategies = strategies
        
        if probabilities is not None:
            self.probabilities = probabilities
            self.is_mixed = True
        else:
            self.probabilities = [1.0 / len(strategies)] * len(strategies)
            self.is_mixed = False
        
        self._validate()
    
    def _validate(self):
        """Validate strategy set."""
        if not self.strategies:
            raise ValueError("Strategy set cannot be empty")
        
        if len(self.probabilities) != len(self.strategies):
            raise ValueError("Probabilities must match number of strategies")
        
        if not np.isclose(sum(self.probabilities), 1.0):
            raise ValueError(f"Probabilities must sum to 1.0, got {sum(self.probabilities)}")
        
        if any(p < 0 for p in self.probabilities):
            raise ValueError("Probabilities cannot be negative")
    
    def get_strategy_count(self) -> int:
        """Get number of strategies."""
        return len(self.strategies)
    
    def get_strategy(self, index: int) -> List[str]:
        """Get strategy by index."""
        return self.strategies[index]
    
    def get_probability(self, index: int) -> float:
        """Get probability of strategy at index."""
        return self.probabilities[index]
    
    def set_probabilities(self, probabilities: List[float]):
        """
        Set probability distribution for mixed strategy.
        
        Args:
            probabilities: New probability distribution
        """
        if len(probabilities) != len(self.strategies):
            raise ValueError("Probabilities must match number of strategies")
        
        if not np.isclose(sum(probabilities), 1.0):
            raise ValueError("Probabilities must sum to 1.0")
        
        self.probabilities = probabilities
        self.is_mixed = not all(p == 0 or p == 1 for p in probabilities)
    
    def sample_strategy(self) -> Tuple[int, List[str]]:
        """
        Sample a strategy according to probability distribution.
        
        Returns:
            Tuple of (strategy_index, strategy_actions)
        """
        index = np.random.choice(len(self.strategies), p=self.probabilities)
        return index, self.strategies[index]
    
    def to_dict(self) -> Dict[str, Any]:
        """Export strategy set as dictionary."""
        return {
            'player_id': self.player_id,
            'player_role': self.player_role,
            'strategy_count': len(self.strategies),
            'strategies': self.strategies,
            'probabilities': self.probabilities,
            'is_mixed': self.is_mixed
        }
    
    def __repr__(self) -> str:
        return (f"StrategySet(player='{self.player_id}', role={self.player_role}, "
                f"strategies={len(self.strategies)}, mixed={self.is_mixed})")


def enumerate_defender_strategies(patch_groups: List[Dict[str, Any]], 
                                  resource_budget: float,
                                  max_strategies: int = 1000) -> List[List[str]]:
    """
    Enumerate all feasible defender strategies (patch group combinations).
    
    Args:
        patch_groups: List of patch group dictionaries
        resource_budget: Available resource budget
        max_strategies: Maximum number of strategies to enumerate
    
    Returns:
        List of strategies (each strategy is a list of patch group IDs)
    """
    strategies = [[]]  # Include "do nothing" strategy
    
    # Sort by cost for efficiency
    sorted_groups = sorted(patch_groups, key=lambda g: g['total_cost'])
    
    # Enumerate all feasible combinations
    for size in range(1, len(patch_groups) + 1):
        for combo in combinations(sorted_groups, size):
            total_cost = sum(g['total_cost'] for g in combo)
            
            if total_cost <= resource_budget:
                strategy = [g['group_id'] for g in combo]
                strategies.append(strategy)
                
                if len(strategies) >= max_strategies:
                    return strategies
    
    return strategies


def enumerate_attacker_strategies(vulnerabilities: List[Dict[str, Any]],
                                  resource_budget: float,
                                  max_strategies: int = 1000) -> List[List[str]]:
    """
    Enumerate all feasible attacker strategies (vulnerability exploits).
    
    Args:
        vulnerabilities: List of vulnerability dictionaries
        resource_budget: Available resource budget (for exploit cost)
        max_strategies: Maximum number of strategies to enumerate
    
    Returns:
        List of strategies (each strategy is a list of CVE IDs)
    """
    strategies = [[]]  # Include "do nothing" strategy
    
    # For attackers, assume exploit cost is related to exploitability
    # Lower exploitability = higher cost
    vulns_with_cost = []
    for vuln in vulnerabilities:
        exploit_cost = 10.0 - vuln['cvss_exploitability']  # Inverse relationship
        vulns_with_cost.append((vuln['cve_id'], exploit_cost))
    
    # Sort by cost
    vulns_with_cost.sort(key=lambda x: x[1])
    
    # Enumerate combinations
    for size in range(1, len(vulns_with_cost) + 1):
        for combo in combinations(vulns_with_cost, size):
            total_cost = sum(cost for _, cost in combo)
            
            if total_cost <= resource_budget:
                strategy = [cve_id for cve_id, _ in combo]
                strategies.append(strategy)
                
                if len(strategies) >= max_strategies:
                    return strategies
    
    return strategies


def filter_dominated_strategies(strategies: List[List[str]],
                                payoff_matrix: np.ndarray,
                                player_index: int) -> List[int]:
    """
    Filter out strictly dominated strategies.
    
    Args:
        strategies: List of strategies
        payoff_matrix: Payoff matrix (rows=player1, cols=player2)
        player_index: 0 for row player, 1 for column player
    
    Returns:
        List of indices of non-dominated strategies
    """
    if len(strategies) == 0:
        return []
    
    non_dominated = []
    
    for i in range(len(strategies)):
        is_dominated = False
        
        for j in range(len(strategies)):
            if i == j:
                continue
            
            # Check if strategy j dominates strategy i
            if player_index == 0:  # Row player
                payoffs_i = payoff_matrix[i, :]
                payoffs_j = payoff_matrix[j, :]
            else:  # Column player
                payoffs_i = payoff_matrix[:, i]
                payoffs_j = payoff_matrix[:, j]
            
            # j dominates i if all payoffs are >= and at least one is >
            if np.all(payoffs_j >= payoffs_i) and np.any(payoffs_j > payoffs_i):
                is_dominated = True
                break
        
        if not is_dominated:
            non_dominated.append(i)
    
    return non_dominated


def create_strategy_set(player: Dict[str, Any],
                       patch_groups: List[Dict[str, Any]],
                       vulnerabilities: List[Dict[str, Any]],
                       max_strategies: int = 1000) -> StrategySet:
    """
    Create strategy set for a player.
    
    Args:
        player: Player dictionary
        patch_groups: Available patch groups
        vulnerabilities: Available vulnerabilities
        max_strategies: Maximum strategies to enumerate
    
    Returns:
        StrategySet for the player
    """
    player_id = player['player_id']
    role = player['role']
    budget = player['resource_budget']
    
    if role == "DEFENDER":
        strategies = enumerate_defender_strategies(
            patch_groups, budget, max_strategies
        )
    elif role == "ATTACKER":
        strategies = enumerate_attacker_strategies(
            vulnerabilities, budget, max_strategies
        )
    else:
        raise ValueError(f"Unknown player role: {role}")
    
    return StrategySet(player_id, role, strategies)


def get_strategy_cost(strategy: List[str],
                     patch_groups: List[Dict[str, Any]],
                     vulnerabilities: List[Dict[str, Any]],
                     role: str) -> float:
    """
    Calculate cost of executing a strategy.
    
    Args:
        strategy: List of action IDs
        patch_groups: Available patch groups
        vulnerabilities: Available vulnerabilities
        role: "ATTACKER" or "DEFENDER"
    
    Returns:
        Total cost of strategy
    """
    total_cost = 0.0
    
    if role == "DEFENDER":
        group_map = {g['group_id']: g for g in patch_groups}
        for group_id in strategy:
            if group_id in group_map:
                total_cost += group_map[group_id]['total_cost']
    
    elif role == "ATTACKER":
        vuln_map = {v['cve_id']: v for v in vulnerabilities}
        for cve_id in strategy:
            if cve_id in vuln_map:
                # Exploit cost inverse to exploitability
                exploit_cost = 10.0 - vuln_map[cve_id]['cvss_exploitability']
                total_cost += exploit_cost
    
    return total_cost


def get_strategy_description(strategy: List[str], role: str) -> str:
    """
    Get human-readable description of a strategy.
    
    Args:
        strategy: List of action IDs
        role: "ATTACKER" or "DEFENDER"
    
    Returns:
        Description string
    """
    if not strategy:
        return f"{role}: Do nothing"
    
    if role == "DEFENDER":
        return f"Patch groups: {', '.join(strategy)}"
    else:
        return f"Exploit: {', '.join(strategy)}"
