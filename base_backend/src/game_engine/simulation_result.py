"""
Simulation Result Module

Exports simulation results back to Developer A for display/analysis.
"""

from typing import Dict, Any, List, Optional
import json


class SimulationResult:
    """
    Encapsulates simulation results for export.
    
    This is the reverse integration point - Developer B exports results
    that Developer A can consume for visualization and reporting.
    """
    
    def __init__(self,
                 patch_priority_list: List[str],
                 ris_summary: List[float],
                 equilibrium_report: Dict[str, Any],
                 per_round_details: List[Dict[str, Any]]):
        """
        Initialize simulation result.
        
        Args:
            patch_priority_list: Ordered list of patch group IDs (priority order)
            ris_summary: RIS value per round
            equilibrium_report: Nash equilibrium statistics
            per_round_details: Detailed results for each round
        """
        self.patch_priority_list = patch_priority_list
        self.ris_summary = ris_summary
        self.equilibrium_report = equilibrium_report
        self.per_round_details = per_round_details
    
    @classmethod
    def from_simulation(cls, simulation_results: Dict[str, Any]) -> 'SimulationResult':
        """
        Create SimulationResult from Simulator output.
        
        Args:
            simulation_results: Dictionary from Simulator.run_simulation()
        
        Returns:
            SimulationResult instance
        """
        # Extract patch priority from schedule
        patch_priority = []
        for round_patches in simulation_results['patch_schedule']:
            for patch_group in round_patches:
                if patch_group not in patch_priority:
                    patch_priority.append(patch_group)
        
        # Extract RIS trajectory
        ris_summary = simulation_results['ris_trajectory']
        
        # Build equilibrium report
        equilibrium_report = cls._build_equilibrium_report(simulation_results)
        
        # Format per-round details
        per_round_details = cls._format_round_details(simulation_results['round_details'])
        
        return cls(
            patch_priority_list=patch_priority,
            ris_summary=ris_summary,
            equilibrium_report=equilibrium_report,
            per_round_details=per_round_details
        )
    
    @staticmethod
    def _build_equilibrium_report(results: Dict[str, Any]) -> Dict[str, Any]:
        """Build equilibrium summary from simulation results."""
        round_details = results['round_details']
        
        # Aggregate equilibrium statistics
        total_defender_payoff = sum(r.get('defender_payoff', 0.0) for r in round_details)
        total_attacker_payoff = sum(r.get('attacker_payoff', 0.0) for r in round_details)
        
        equilibrium_types = [r.get('equilibrium_type', 'none') for r in round_details]
        pure_count = sum(1 for t in equilibrium_types if t == 'pure')
        mixed_count = sum(1 for t in equilibrium_types if t == 'mixed')
        
        # Calculate total_ris_reduction if not present
        total_ris_reduction = results.get('total_ris_reduction')
        if total_ris_reduction is None:
            initial = results.get('initial_ris', 0.0)
            final = results.get('final_ris', 0.0)
            total_ris_reduction = initial - final
        
        return {
            'total_defender_payoff': total_defender_payoff,
            'total_attacker_payoff': total_attacker_payoff,
            'average_defender_payoff': total_defender_payoff / len(round_details) if round_details else 0.0,
            'average_attacker_payoff': total_attacker_payoff / len(round_details) if round_details else 0.0,
            'pure_equilibria_count': pure_count,
            'mixed_equilibria_count': mixed_count,
            'expected_impact': total_ris_reduction,
            'expected_profit': total_attacker_payoff
        }
    
    @staticmethod
    def _format_round_details(round_details: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format round details for export."""
        formatted = []
        
        for detail in round_details:
            formatted.append({
                'round': detail['round'],
                'patched_groups': detail.get('patches_applied', []),
                'attacked_vulnerabilities': detail.get('vulnerabilities_exploited', []),
                'remaining_ris': detail.get('final_ris', 0.0)
            })
        
        return formatted
    
    def export_to_dict(self) -> Dict[str, Any]:
        """
        Export simulation result as dictionary.
        
        This conforms to the integration contract for Developer A.
        
        Returns:
            Dictionary with all simulation results
        """
        return {
            'patch_priority_list': self.patch_priority_list,
            'ris_summary': self.ris_summary,
            'equilibrium_report': self.equilibrium_report,
            'per_round_details': self.per_round_details
        }
    
    def export_to_json(self, filepath: str):
        """
        Export results to JSON file.
        
        Args:
            filepath: Path to output file
        """
        with open(filepath, 'w') as f:
            json.dump(self.export_to_dict(), f, indent=2)
    
    def get_summary(self) -> str:
        """
        Get human-readable summary of results.
        
        Returns:
            Summary string
        """
        summary = "=" * 70 + "\n"
        summary += "Simulation Results Summary\n"
        summary += "=" * 70 + "\n\n"
        
        summary += f"Total Rounds: {len(self.per_round_details)}\n"
        summary += f"Initial RIS: {self.ris_summary[0]:.2f}\n"
        summary += f"Final RIS: {self.ris_summary[-1]:.2f}\n"
        summary += f"Total RIS Reduction: {self.ris_summary[0] - self.ris_summary[-1]:.2f}\n\n"
        
        summary += "Equilibrium Statistics:\n"
        eq_report = self.equilibrium_report
        summary += f"  Defender Average Payoff: {eq_report['average_defender_payoff']:.4f}\n"
        summary += f"  Attacker Average Payoff: {eq_report['average_attacker_payoff']:.4f}\n"
        summary += f"  Pure Equilibria: {eq_report['pure_equilibria_count']}\n"
        summary += f"  Mixed Equilibria: {eq_report['mixed_equilibria_count']}\n\n"
        
        summary += f"Patch Priority (Top 10):\n"
        for i, patch_group in enumerate(self.patch_priority_list[:10], 1):
            summary += f"  {i}. {patch_group}\n"
        
        summary += "\n" + "=" * 70 + "\n"
        
        return summary
    
    def get_ris_reduction_percentage(self) -> float:
        """
        Calculate percentage reduction in RIS.
        
        Returns:
            Percentage reduction (0-100)
        """
        if not self.ris_summary or self.ris_summary[0] == 0:
            return 0.0
        
        initial = self.ris_summary[0]
        final = self.ris_summary[-1]
        
        return ((initial - final) / initial) * 100.0
    
    def get_patch_effectiveness(self) -> Dict[str, float]:
        """
        Analyze effectiveness of patches per round.
        
        Returns:
            Dictionary with effectiveness metrics
        """
        if len(self.ris_summary) < 2:
            return {}
        
        round_reductions = []
        for i in range(len(self.ris_summary) - 1):
            reduction = self.ris_summary[i] - self.ris_summary[i + 1]
            round_reductions.append(reduction)
        
        return {
            'average_reduction_per_round': sum(round_reductions) / len(round_reductions),
            'max_reduction_round': max(round_reductions) if round_reductions else 0.0,
            'min_reduction_round': min(round_reductions) if round_reductions else 0.0,
            'total_reduction': sum(round_reductions)
        }
    
    def __repr__(self) -> str:
        return (f"SimulationResult(rounds={len(self.per_round_details)}, "
                f"patches={len(self.patch_priority_list)}, "
                f"ris_reduction={self.get_ris_reduction_percentage():.1f}%)")
