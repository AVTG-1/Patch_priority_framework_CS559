"""
Simulation Engine

Runs multi-round simulations of the patch prioritization game,
tracking RIS (Remaining Impact Score) and patch schedules.
"""

from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from .game_state import GameState
from .strategy import StrategySet, create_strategy_set
from .nash_solver import NashSolver


class Simulator:
    """
    Simulates the patch prioritization game over multiple rounds.
    
    Attributes:
        game_state: Current game state
        simulation_length: Number of rounds to simulate
        discount_factor: Discount factor for future payoffs
        nash_solver: Nash equilibrium solver
    """
    
    def __init__(self,
                 game_state: GameState,
                 simulation_length: int = 10,
                 discount_factor: float = 0.9):
        """
        Initialize simulator.
        
        Args:
            game_state: Initial game state
            simulation_length: Number of rounds
            discount_factor: Discount factor (0-1)
        """
        self.game_state = game_state
        self.simulation_length = simulation_length
        self.discount_factor = discount_factor
        self.nash_solver = NashSolver()
        
        # Tracking
        self.round_history: List[Dict[str, Any]] = []
        self.ris_trajectory: List[float] = []
        self.patch_schedule: List[List[str]] = []
        
        self._validate()
    
    def _validate(self):
        """Validate simulation parameters."""
        if self.simulation_length <= 0:
            raise ValueError("Simulation length must be positive")
        
        if not 0 <= self.discount_factor <= 1:
            raise ValueError("Discount factor must be in [0, 1]")
    
    def build_payoff_matrices(self,
                             defender_strategies: StrategySet,
                             attacker_strategies: StrategySet) -> Tuple[np.ndarray, np.ndarray]:
        """
        Build payoff matrices for current game state.
        
        Args:
            defender_strategies: Defender strategy set
            attacker_strategies: Attacker strategy set
        
        Returns:
            Tuple of (defender_payoff_matrix, attacker_payoff_matrix)
        """
        n_defender = defender_strategies.get_strategy_count()
        n_attacker = attacker_strategies.get_strategy_count()
        
        defender_payoffs = np.zeros((n_defender, n_attacker))
        attacker_payoffs = np.zeros((n_defender, n_attacker))
        
        # For each strategy combination, compute payoffs
        for i in range(n_defender):
            defender_strategy = defender_strategies.get_strategy(i)
            
            for j in range(n_attacker):
                attacker_strategy = attacker_strategies.get_strategy(j)
                
                # Simulate this strategy combination
                d_payoff, a_payoff = self._compute_payoffs(
                    defender_strategy,
                    attacker_strategy
                )
                
                defender_payoffs[i, j] = d_payoff
                attacker_payoffs[i, j] = a_payoff
        
        return defender_payoffs, attacker_payoffs
    
    def _compute_payoffs(self,
                        defender_actions: List[str],
                        attacker_actions: List[str]) -> Tuple[float, float]:
        """
        Compute payoffs for a strategy combination.
        
        Args:
            defender_actions: Patch groups to apply
            attacker_actions: Vulnerabilities to exploit
        
        Returns:
            Tuple of (defender_payoff, attacker_payoff)
        """
        # Create temporary state copy
        initial_ris = self.game_state.calculate_remaining_impact()
        
        # Apply defender patches
        patched_cves = set()
        for group_id in defender_actions:
            group = self.game_state.get_patch_group(group_id)
            if group:
                patched_cves.update(group['cve_ids'])
        
        # Calculate impact of successful attacks
        attack_impact = 0.0
        for cve_id in attacker_actions:
            if cve_id not in patched_cves:
                vuln = self.game_state.get_vulnerability(cve_id)
                if vuln:
                    # Impact weighted by importance
                    impact = vuln['cvss_impact'] * vuln['importance_score']
                    if vuln.get('exploit_present', False):
                        impact *= 1.5
                    attack_impact += impact
        
        # Defender wants to minimize impact (negative payoff from attacks)
        # Also pays cost for patching
        patch_cost = sum(
            self.game_state.get_patch_group(gid)['total_cost']
            for gid in defender_actions
            if self.game_state.get_patch_group(gid)
        )
        
        defender_payoff = -attack_impact - 0.1 * patch_cost  # Weight patch cost less
        
        # Attacker wants to maximize impact, pays cost for exploiting
        exploit_cost = sum(
            10.0 - self.game_state.get_vulnerability(cve_id)['cvss_exploitability']
            for cve_id in attacker_actions
            if self.game_state.get_vulnerability(cve_id)
        )
        
        attacker_payoff = attack_impact - 0.1 * exploit_cost
        
        return defender_payoff, attacker_payoff
    
    def run_round(self) -> Dict[str, Any]:
        """
        Execute one round of the simulation.
        
        Returns:
            Dictionary with round results
        """
        # Record initial RIS
        initial_ris = self.game_state.calculate_remaining_impact()
        
        # Get current players
        defenders = self.game_state.get_defenders()
        attackers = self.game_state.get_attackers()
        
        if not defenders or not attackers:
            # No players, skip round
            return {
                'round': self.game_state.current_round,
                'initial_ris': initial_ris,
                'final_ris': initial_ris,
                'ris_reduction': 0.0,
                'patches_applied': [],
                'vulnerabilities_exploited': [],
                'defender_payoff': 0.0,
                'attacker_payoff': 0.0,
                'equilibrium_type': 'none',
                'remaining_vulnerabilities': self.game_state.get_vulnerability_count()
            }
        
        # Use first defender and attacker (can extend to multiple)
        defender = defenders[0]
        attacker = attackers[0]
        
        # Enumerate strategies (limit for Nash computation tractability)
        defender_strategies = create_strategy_set(
            defender,
            self.game_state.patch_groups,
            self.game_state.remaining_vulnerabilities,
            max_strategies=10  # Reduced for fast Nash computation
        )
        
        attacker_strategies = create_strategy_set(
            attacker,
            self.game_state.patch_groups,
            self.game_state.remaining_vulnerabilities,
            max_strategies=10  # Reduced for fast Nash computation
        )
        
        # Build payoff matrices
        defender_payoffs, attacker_payoffs = self.build_payoff_matrices(
            defender_strategies,
            attacker_strategies
        )
        
        # Solve for Nash equilibrium
        equilibrium = self.nash_solver.find_best_equilibrium(
            defender_payoffs,
            attacker_payoffs,
            preference="defender"
        )
        
        if not equilibrium:
            # No equilibrium found, use random strategies
            defender_action_idx = 0
            attacker_action_idx = 0
        elif equilibrium['type'] == 'pure':
            defender_action_idx = equilibrium['defender_strategy_index']
            attacker_action_idx = equilibrium['attacker_strategy_index']
        else:
            # Sample from mixed strategy
            defender_action_idx = np.random.choice(
                len(defender_strategies.strategies),
                p=equilibrium['defender_strategy']
            )
            attacker_action_idx = np.random.choice(
                len(attacker_strategies.strategies),
                p=equilibrium['attacker_strategy']
            )
        
        # Execute actions
        defender_actions = defender_strategies.get_strategy(defender_action_idx)
        attacker_actions = attacker_strategies.get_strategy(attacker_action_idx)
        
        # Apply patches
        patched_cves = []
        for group_id in defender_actions:
            group = self.game_state.get_patch_group(group_id)
            if group:
                self.game_state.apply_patch_group(group_id)
                patched_cves.extend(group['cve_ids'])
        
        # Apply exploits
        exploited_cves = []
        for cve_id in attacker_actions:
            if cve_id not in self.game_state.patched_cves:
                self.game_state.exploit_vulnerabilities([cve_id])
                exploited_cves.append(cve_id)
        
        # Calculate final RIS
        final_ris = self.game_state.calculate_remaining_impact()
        
        # Record round results
        round_result = {
            'round': self.game_state.current_round,
            'initial_ris': initial_ris,
            'final_ris': final_ris,
            'ris_reduction': initial_ris - final_ris,
            'patches_applied': patched_cves,
            'vulnerabilities_exploited': exploited_cves,
            'defender_payoff': equilibrium['defender_payoff'] if equilibrium else 0.0,
            'attacker_payoff': equilibrium['attacker_payoff'] if equilibrium else 0.0,
            'equilibrium_type': equilibrium['type'] if equilibrium else 'none',
            'remaining_vulnerabilities': self.game_state.get_vulnerability_count()
        }
        
        # Advance round
        self.game_state.advance_round()
        
        return round_result
    
    def run_simulation(self) -> Dict[str, Any]:
        """
        Run full simulation.
        
        Returns:
            Dictionary with complete simulation results
        """
        # Reset tracking
        self.round_history = []
        self.ris_trajectory = [self.game_state.calculate_remaining_impact()]
        self.patch_schedule = []
        
        # Run rounds
        for _ in range(self.simulation_length):
            round_result = self.run_round()
            
            self.round_history.append(round_result)
            self.ris_trajectory.append(round_result['final_ris'])
            self.patch_schedule.append(round_result['patches_applied'])
            
            # Stop if no more vulnerabilities
            if self.game_state.get_vulnerability_count() == 0:
                break
        
        # Compile results
        total_patched = len(self.game_state.patched_cves)
        total_exploited = len(self.game_state.exploited_cves)
        
        results = {
            'total_rounds': len(self.round_history),
            'initial_ris': self.ris_trajectory[0],
            'final_ris': self.ris_trajectory[-1],
            'total_ris_reduction': self.ris_trajectory[0] - self.ris_trajectory[-1],
            'ris_trajectory': self.ris_trajectory,
            'total_vulnerabilities_patched': total_patched,
            'total_vulnerabilities_exploited': total_exploited,
            'patch_schedule': self.patch_schedule,
            'round_details': self.round_history,
            'final_state': self.game_state.get_state_summary()
        }
        
        return results
    
    def get_patch_priority_list(self) -> List[str]:
        """
        Get prioritized list of patches from first round.
        
        Returns:
            List of patch group IDs in priority order
        """
        if not self.patch_schedule:
            return []
        
        # Priority is based on order of patching across rounds
        priority_list = []
        for patches in self.patch_schedule:
            for patch in patches:
                if patch not in priority_list:
                    priority_list.append(patch)
        
        return priority_list
    
    def reset(self):
        """Reset simulation state."""
        self.game_state.reset()
        self.round_history = []
        self.ris_trajectory = []
        self.patch_schedule = []
