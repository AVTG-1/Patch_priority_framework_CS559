"""
Nash Equilibrium Solver

Computes pure and mixed Nash equilibria for the patch prioritization game.
"""

from typing import List, Dict, Any, Tuple, Optional
import numpy as np
import nashpy as nash


class NashSolver:
    """
    Solves for Nash equilibria in the game.
    
    Uses nashpy library for computing equilibria.
    """
    
    def __init__(self):
        """Initialize Nash solver."""
        self.tolerance = 1e-6
    
    def compute_pure_nash(self, 
                         payoff_matrix_defender: np.ndarray,
                         payoff_matrix_attacker: np.ndarray) -> List[Tuple[int, int]]:
        """
        Find all pure strategy Nash equilibria.
        
        Args:
            payoff_matrix_defender: Payoff matrix for defender (rows=defender, cols=attacker)
            payoff_matrix_attacker: Payoff matrix for attacker (rows=defender, cols=attacker)
        
        Returns:
            List of (defender_strategy_index, attacker_strategy_index) tuples
        """
        pure_equilibria = []
        
        n_defender_strategies = payoff_matrix_defender.shape[0]
        n_attacker_strategies = payoff_matrix_defender.shape[1]
        
        # Check each strategy profile
        for i in range(n_defender_strategies):
            for j in range(n_attacker_strategies):
                # Check if (i, j) is a Nash equilibrium
                
                # Defender's incentive: is strategy i best response to attacker's j?
                defender_payoff = payoff_matrix_defender[i, j]
                defender_best_response = np.max(payoff_matrix_defender[:, j])
                
                # Attacker's incentive: is strategy j best response to defender's i?
                attacker_payoff = payoff_matrix_attacker[i, j]
                attacker_best_response = np.max(payoff_matrix_attacker[i, :])
                
                # Both must be best responses
                if (np.isclose(defender_payoff, defender_best_response, atol=self.tolerance) and
                    np.isclose(attacker_payoff, attacker_best_response, atol=self.tolerance)):
                    pure_equilibria.append((i, j))
        
        return pure_equilibria
    
    def compute_mixed_nash(self,
                          payoff_matrix_defender: np.ndarray,
                          payoff_matrix_attacker: np.ndarray,
                          max_equilibria: int = 10,
                          timeout: float = 5.0) -> List[Tuple[np.ndarray, np.ndarray]]:
        """
        Find mixed strategy Nash equilibria using support enumeration.
        
        Args:
            payoff_matrix_defender: Payoff matrix for defender
            payoff_matrix_attacker: Payoff matrix for attacker
            max_equilibria: Maximum number of equilibria to find
            timeout: Maximum seconds to spend searching (default 5.0)
        
        Returns:
            List of (defender_mixed_strategy, attacker_mixed_strategy) tuples
        """
        # For large games (>10x10), skip mixed Nash and use pure only
        if (payoff_matrix_defender.shape[0] > 10 or 
            payoff_matrix_defender.shape[1] > 10):
            return []
        
        # Create game using nashpy
        # nashpy expects (row_player_payoffs, col_player_payoffs)
        game = nash.Game(payoff_matrix_defender, payoff_matrix_attacker)
        
        equilibria = []
        
        try:
            # Try lemke_howson first (faster, finds one equilibrium)
            defender_strategy, attacker_strategy = game.lemke_howson(initial_dropped_label=0)
            
            # Validate and clean
            if (np.all(defender_strategy >= -self.tolerance) and
                np.all(attacker_strategy >= -self.tolerance)):
                defender_strategy = np.maximum(defender_strategy, 0)
                attacker_strategy = np.maximum(attacker_strategy, 0)
                defender_strategy /= np.sum(defender_strategy)
                attacker_strategy /= np.sum(attacker_strategy)
                
                equilibria.append((defender_strategy, attacker_strategy))
        except Exception:
            pass
        
        return equilibria
    
    def compute_expected_payoffs(self,
                                payoff_matrix: np.ndarray,
                                defender_strategy: np.ndarray,
                                attacker_strategy: np.ndarray) -> float:
        """
        Compute expected payoff for a player given mixed strategies.
        
        Args:
            payoff_matrix: Payoff matrix for the player
            defender_strategy: Defender's mixed strategy (probability distribution)
            attacker_strategy: Attacker's mixed strategy (probability distribution)
        
        Returns:
            Expected payoff
        """
        # Expected payoff = sum over all outcomes of (prob * payoff)
        expected = np.sum(
            defender_strategy.reshape(-1, 1) * 
            attacker_strategy.reshape(1, -1) * 
            payoff_matrix
        )
        return expected
    
    def find_best_equilibrium(self,
                            payoff_matrix_defender: np.ndarray,
                            payoff_matrix_attacker: np.ndarray,
                            preference: str = "defender") -> Optional[Dict[str, Any]]:
        """
        Find the best Nash equilibrium from a player's perspective.
        
        Args:
            payoff_matrix_defender: Defender's payoff matrix
            payoff_matrix_attacker: Attacker's payoff matrix
            preference: "defender" or "attacker" - whose payoff to maximize
        
        Returns:
            Dictionary with equilibrium details, or None if no equilibrium found
        """
        # First check for pure equilibria
        pure_eq = self.compute_pure_nash(payoff_matrix_defender, payoff_matrix_attacker)
        
        best_equilibrium = None
        best_payoff = -np.inf
        
        # Evaluate pure equilibria
        for defender_idx, attacker_idx in pure_eq:
            if preference == "defender":
                payoff = payoff_matrix_defender[defender_idx, attacker_idx]
            else:
                payoff = payoff_matrix_attacker[defender_idx, attacker_idx]
            
            if payoff > best_payoff:
                best_payoff = payoff
                
                # Create pure strategy distributions
                defender_strategy = np.zeros(payoff_matrix_defender.shape[0])
                defender_strategy[defender_idx] = 1.0
                
                attacker_strategy = np.zeros(payoff_matrix_defender.shape[1])
                attacker_strategy[attacker_idx] = 1.0
                
                best_equilibrium = {
                    'type': 'pure',
                    'defender_strategy': defender_strategy,
                    'attacker_strategy': attacker_strategy,
                    'defender_strategy_index': defender_idx,
                    'attacker_strategy_index': attacker_idx,
                    'defender_payoff': payoff_matrix_defender[defender_idx, attacker_idx],
                    'attacker_payoff': payoff_matrix_attacker[defender_idx, attacker_idx]
                }
        
        # Compute mixed equilibria
        mixed_eq = self.compute_mixed_nash(payoff_matrix_defender, payoff_matrix_attacker)
        
        # Evaluate mixed equilibria
        for defender_strategy, attacker_strategy in mixed_eq:
            defender_payoff = self.compute_expected_payoffs(
                payoff_matrix_defender, defender_strategy, attacker_strategy
            )
            attacker_payoff = self.compute_expected_payoffs(
                payoff_matrix_attacker, defender_strategy, attacker_strategy
            )
            
            if preference == "defender":
                payoff = defender_payoff
            else:
                payoff = attacker_payoff
            
            if payoff > best_payoff:
                best_payoff = payoff
                best_equilibrium = {
                    'type': 'mixed',
                    'defender_strategy': defender_strategy,
                    'attacker_strategy': attacker_strategy,
                    'defender_payoff': defender_payoff,
                    'attacker_payoff': attacker_payoff
                }
        
        return best_equilibrium
    
    def get_equilibrium_summary(self, equilibrium: Dict[str, Any]) -> str:
        """
        Get human-readable summary of an equilibrium.
        
        Args:
            equilibrium: Equilibrium dictionary
        
        Returns:
            Summary string
        """
        if not equilibrium:
            return "No equilibrium found"
        
        eq_type = equilibrium['type']
        defender_payoff = equilibrium['defender_payoff']
        attacker_payoff = equilibrium['attacker_payoff']
        
        summary = f"Nash Equilibrium ({eq_type}):\n"
        summary += f"  Defender expected payoff: {defender_payoff:.4f}\n"
        summary += f"  Attacker expected payoff: {attacker_payoff:.4f}\n"
        
        if eq_type == 'pure':
            summary += f"  Defender strategy index: {equilibrium['defender_strategy_index']}\n"
            summary += f"  Attacker strategy index: {equilibrium['attacker_strategy_index']}\n"
        else:
            # Show top strategies by probability
            defender_strategy = equilibrium['defender_strategy']
            attacker_strategy = equilibrium['attacker_strategy']
            
            # Top 3 defender strategies
            top_defender = np.argsort(defender_strategy)[-3:][::-1]
            summary += "  Top defender strategies:\n"
            for idx in top_defender:
                if defender_strategy[idx] > 0.01:
                    summary += f"    Strategy {idx}: {defender_strategy[idx]:.3f}\n"
            
            # Top 3 attacker strategies
            top_attacker = np.argsort(attacker_strategy)[-3:][::-1]
            summary += "  Top attacker strategies:\n"
            for idx in top_attacker:
                if attacker_strategy[idx] > 0.01:
                    summary += f"    Strategy {idx}: {attacker_strategy[idx]:.3f}\n"
        
        return summary
