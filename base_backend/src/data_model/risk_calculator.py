"""
Risk Calculator

Provides algorithms for calculating subsystem importance scores
and vulnerability risk metrics.
"""

from typing import List, Dict, Any
import numpy as np
from .system import SystemInstance
from .subsystem import Subsystem
from .vulnerability import Vulnerability
from .patch_group import PatchGroup, collapse_by_dependencies


class RiskCalculator:
    """
    Calculates risk scores and importance metrics for system components.
    """
    
    def __init__(self):
        """Initialize risk calculator."""
        self.importance_cache = {}
    
    def compute_importance(self, system: SystemInstance, 
                          max_iterations: int = 100,
                          convergence_threshold: float = 1e-6) -> Dict[str, float]:
        """
        Compute importance scores for all subsystems using iterative algorithm.
        
        Uses a combination of functional dependencies and network topology
        to calculate centrality-based importance scores.
        
        Args:
            system: System instance to analyze
            max_iterations: Maximum iterations for convergence
            convergence_threshold: Convergence threshold for stopping
        
        Returns:
            Dictionary mapping subsystem IDs to importance scores
        """
        n = len(system.subsystems)
        if n == 0:
            return {}
        
        # Get weights
        w_func = system.weights.get("functional_weight", 0.6)
        w_topo = system.weights.get("topological_weight", 0.4)
        
        # Initialize importance scores uniformly
        importance = np.ones(n) / n
        
        # Get dependency matrices
        W = system.w_adj.astype(float)
        N = system.n_topology.astype(float)
        
        # Normalize matrices by row sums (avoid division by zero)
        W_row_sums = W.sum(axis=1, keepdims=True)
        W_row_sums[W_row_sums == 0] = 1
        W_norm = W / W_row_sums
        
        N_row_sums = N.sum(axis=1, keepdims=True)
        N_row_sums[N_row_sums == 0] = 1
        N_norm = N / N_row_sums
        
        # Iterative importance calculation (similar to PageRank)
        for iteration in range(max_iterations):
            # Combine functional and topological influences
            new_importance = w_func * (W_norm.T @ importance) + w_topo * (N_norm.T @ importance)
            
            # Normalize to sum to 1
            # new_importance = new_importance / new_importance.sum() --> Changed
            importance_sum = new_importance.sum()
            if importance_sum > 0:
                new_importance = new_importance / importance_sum
            else:
                new_importance = np.zeros_like(new_importance)
            
            
            # Check convergence
            diff = np.abs(new_importance - importance).sum()
            importance = new_importance
            
            if diff < convergence_threshold:
                break
        
        # Update subsystem objects and create result dictionary
        result = {}
        for i, subsystem in enumerate(system.subsystems):
            score = float(importance[i])
            subsystem.importance_score = score
            result[subsystem.id] = score
        
        # Cache results
        self.importance_cache[id(system)] = result
        
        return result
    
    def score_vulnerability(self, vulnerability: Vulnerability, 
                           subsystem: Subsystem,
                           importance_weight: float = 0.3) -> float:
        """
        Calculate a comprehensive risk score for a vulnerability.
        
        Combines CVSS metrics, exploit availability, and subsystem importance.
        
        Args:
            vulnerability: Vulnerability to score
            subsystem: Subsystem containing the vulnerability
            importance_weight: Weight for subsystem importance (0.0-1.0)
        
        Returns:
            Risk score (higher = more risky)
        """
        # CVSS base score (average of impact and exploitability)
        cvss_score = (vulnerability.cvss_impact + vulnerability.cvss_exploitability) / 2.0
        
        # Exploit multiplier
        exploit_mult = vulnerability.get_exploit_multiplier()
        
        # Subsystem importance
        subsystem_importance = subsystem.importance_score
        
        # Dependency penalty (vulnerabilities with dependencies are slightly riskier)
        dep_penalty = 1.1 if vulnerability.has_dependencies() else 1.0
        
        # Combined risk score
        risk_score = (
            cvss_score * (1 - importance_weight) +
            subsystem_importance * 10.0 * importance_weight
        ) * exploit_mult * dep_penalty
        
        return risk_score
    
    def score_all_vulnerabilities(self, system: SystemInstance,
                                  importance_weight: float = 0.3) -> Dict[str, float]:
        """
        Calculate risk scores for all vulnerabilities in the system.
        
        Args:
            system: System instance to analyze
            importance_weight: Weight for subsystem importance
        
        Returns:
            Dictionary mapping CVE IDs to risk scores
        """
        # Ensure importance scores are calculated
        if not all(s.importance_score > 0 for s in system.subsystems):
            self.compute_importance(system)
        
        scores = {}
        for subsystem in system.subsystems:
            for vulnerability in subsystem.vulnerabilities:
                score = self.score_vulnerability(vulnerability, subsystem, importance_weight)
                scores[vulnerability.cve_id] = score
        
        return scores
    
    def rank_vulnerabilities(self, system: SystemInstance,
                           importance_weight: float = 0.3) -> List[tuple]:
        """
        Rank all vulnerabilities by risk score.
        
        Args:
            system: System instance to analyze
            importance_weight: Weight for subsystem importance
        
        Returns:
            List of (cve_id, score) tuples, sorted by score (descending)
        """
        scores = self.score_all_vulnerabilities(system, importance_weight)
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return ranked
    
    def collapse_patch_dependencies(self, vulnerabilities: List[Vulnerability]) -> List[PatchGroup]:
        """
        Collapse vulnerabilities into patch groups based on dependencies.
        
        This is a convenience wrapper around the patch_group module's function.
        
        Args:
            vulnerabilities: List of vulnerabilities to group
        
        Returns:
            List of PatchGroup objects
        """
        return collapse_by_dependencies(vulnerabilities)
    
    def calculate_patching_priority(self, patch_groups: List[PatchGroup],
                                   budget_constraint: float = None) -> List[str]:
        """
        Calculate optimal patching order for patch groups.
        
        Uses a simple cost-benefit ratio approach.
        
        Args:
            patch_groups: List of patch groups to prioritize
            budget_constraint: Optional budget limit
        
        Returns:
            List of group IDs in priority order
        """
        if not patch_groups:
            return []
        
        # Calculate cost-benefit ratio for each group
        priorities = []
        for group in patch_groups:
            if group.total_cost > 0:
                # Benefit = impact, Cost = patching cost
                # Higher impact per unit cost is better
                ratio = group.aggregate_impact / group.total_cost
            else:
                # Free patches get highest priority
                ratio = float('inf')
            
            priorities.append((group.group_id, ratio, group.total_cost))
        
        # Sort by ratio (descending)
        priorities.sort(key=lambda x: x[1], reverse=True)
        
        # Apply budget constraint if specified
        if budget_constraint is not None:
            selected = []
            total_cost = 0.0
            for group_id, ratio, cost in priorities:
                if total_cost + cost <= budget_constraint:
                    selected.append(group_id)
                    total_cost += cost
            return selected
        
        return [group_id for group_id, _, _ in priorities]
    
    def assess_system_risk(self, system: SystemInstance) -> Dict[str, Any]:
        """
        Perform comprehensive risk assessment of the system.
        
        Args:
            system: System instance to assess
        
        Returns:
            Dictionary with various risk metrics
        """
        # Calculate importance scores
        importance_scores = self.compute_importance(system)
        
        # Get all vulnerabilities
        all_vulns = system.get_all_vulnerabilities()
        
        # Score vulnerabilities
        vuln_scores = self.score_all_vulnerabilities(system)
        
        # Statistics
        total_vulns = len(all_vulns)
        critical_vulns = sum(1 for v in all_vulns if v.cvss_impact >= 9.0)
        high_vulns = sum(1 for v in all_vulns if 7.0 <= v.cvss_impact < 9.0)
        exploitable_vulns = sum(1 for v in all_vulns if v.exploit_present)
        
        # Total patch cost
        total_patch_cost = sum(v.patch_cost for v in all_vulns)
        
        # Average risk score
        avg_risk_score = sum(vuln_scores.values()) / len(vuln_scores) if vuln_scores else 0.0
        max_risk_score = max(vuln_scores.values()) if vuln_scores else 0.0
        
        # Most critical subsystem
        most_critical_subsystem = max(system.subsystems, key=lambda s: s.importance_score)
        
        return {
            "total_vulnerabilities": total_vulns,
            "critical_vulnerabilities": critical_vulns,
            "high_vulnerabilities": high_vulns,
            "exploitable_vulnerabilities": exploitable_vulns,
            "total_patch_cost": total_patch_cost,
            "average_risk_score": avg_risk_score,
            "max_risk_score": max_risk_score,
            "most_critical_subsystem": {
                "id": most_critical_subsystem.id,
                "name": most_critical_subsystem.name,
                "importance": most_critical_subsystem.importance_score
            },
            "subsystem_importance_scores": importance_scores,
            "top_10_vulnerabilities": [
                {"cve_id": cve_id, "risk_score": score}
                for cve_id, score in self.rank_vulnerabilities(system)[:10]
            ]
        }
