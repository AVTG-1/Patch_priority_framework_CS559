"""
System Model

Represents system templates and instances with dependency matrices
and the critical export_for_game() method for integration.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import numpy as np
from .subsystem import Subsystem
from .vulnerability import Vulnerability
from .patch_group import PatchGroup, collapse_by_dependencies
from .player import PlayerBase


@dataclass
class SystemClass:
    """
    Template for a system type (e.g., SCADA, Web Application).
    
    Attributes:
        name: System type name
        description: Description of system characteristics
        default_subsystems: Suggested subsystem types
        weight_config: Default weight configuration
    """
    name: str
    description: str = ""
    default_subsystems: List[str] = field(default_factory=list)
    weight_config: Dict[str, float] = field(default_factory=lambda: {
        "functional_weight": 0.6,
        "topological_weight": 0.4
    })
    
    def __post_init__(self):
        """Validate system class data."""
        if not self.name or not self.name.strip():
            raise ValueError("System name cannot be empty")
        
        # Validate weights
        if "functional_weight" not in self.weight_config:
            self.weight_config["functional_weight"] = 0.6
        if "topological_weight" not in self.weight_config:
            self.weight_config["topological_weight"] = 0.4


class SystemInstance:
    """
    Instance of a system with specific subsystems and vulnerabilities.
    
    Attributes:
        system_class: Template this instance follows
        subsystems: List of subsystem instances
        weights: Weight configuration for importance calculation
        w_adj: Functional dependency matrix (numpy array)
        n_topology: Network topology matrix (numpy array)
    """
    
    def __init__(self,
                 system_class: SystemClass,
                 subsystems: List[Subsystem],
                 weights: Optional[Dict[str, float]] = None,
                 owner_user_id: Optional[str] = None):
        """
        Initialize system instance.
        
        Args:
            system_class: System template
            subsystems: List of subsystems
            weights: Optional custom weights
            owner_user_id: ID of user who owns this system (for collaboration)
        """
        self.system_class = system_class
        self.subsystems = subsystems
        self.weights = weights or system_class.weight_config.copy()
        self.owner_user_id = owner_user_id
        
        # Build dependency matrices
        self.w_adj = self._build_functional_matrix()
        self.n_topology = self._build_topology_matrix()
        
        self._validate()
    
    def _validate(self):
        """Validate system instance."""
        if not self.subsystems:
            raise ValueError("System must have at least one subsystem")
        
        # Check for duplicate subsystem IDs
        subsystem_ids = [s.id for s in self.subsystems]
        if len(subsystem_ids) != len(set(subsystem_ids)):
            raise ValueError("Duplicate subsystem IDs found")
        
        # Validate matrix dimensions
        n = len(self.subsystems)
        if self.w_adj.shape != (n, n):
            raise ValueError(f"Functional matrix must be {n}x{n}, got {self.w_adj.shape}")
        if self.n_topology.shape != (n, n):
            raise ValueError(f"Topology matrix must be {n}x{n}, got {self.n_topology.shape}")
        
        # Validate weights
        if "functional_weight" not in self.weights or "topological_weight" not in self.weights:
            raise ValueError("Weights must contain 'functional_weight' and 'topological_weight'")
    
    def _build_functional_matrix(self) -> np.ndarray:
        """
        Build functional dependency matrix from subsystems.
        
        Returns:
            N x N matrix where entry [i,j] = 1 if subsystem i depends on j
        """
        n = len(self.subsystems)
        matrix = np.zeros((n, n), dtype=int)
        
        # Create ID to index mapping
        id_to_idx = {s.id: i for i, s in enumerate(self.subsystems)}
        
        # Fill matrix
        for i, subsystem in enumerate(self.subsystems):
            for dep_id in subsystem.functional_deps:
                if dep_id in id_to_idx:
                    j = id_to_idx[dep_id]
                    matrix[i, j] = 1
        
        return matrix
    
    def _build_topology_matrix(self) -> np.ndarray:
        """
        Build network topology matrix from subsystems.
        
        Returns:
            N x N matrix where entry [i,j] = 1 if subsystems i and j are connected
        """
        n = len(self.subsystems)
        matrix = np.zeros((n, n), dtype=int)
        
        # Create ID to index mapping
        id_to_idx = {s.id: i for i, s in enumerate(self.subsystems)}
        
        # Fill matrix (symmetric for undirected connections)
        for i, subsystem in enumerate(self.subsystems):
            for conn_id in subsystem.connected_ids:
                if conn_id in id_to_idx:
                    j = id_to_idx[conn_id]
                    matrix[i, j] = 1
                    matrix[j, i] = 1  # Symmetric
        
        return matrix
    
    def get_subsystem(self, subsystem_id: str) -> Optional[Subsystem]:
        """
        Get subsystem by ID.
        
        Args:
            subsystem_id: Subsystem identifier
        
        Returns:
            Subsystem if found, None otherwise
        """
        for subsystem in self.subsystems:
            if subsystem.id == subsystem_id:
                return subsystem
        return None
    
    def get_all_vulnerabilities(self) -> List[Vulnerability]:
        """
        Get all vulnerabilities across all subsystems.
        
        Returns:
            Flattened list of all vulnerabilities
        """
        all_vulns = []
        for subsystem in self.subsystems:
            all_vulns.extend(subsystem.vulnerabilities)
        return all_vulns
    
    def get_total_vulnerability_count(self) -> int:
        """Get total number of vulnerabilities in system."""
        return sum(s.get_vulnerability_count() for s in self.subsystems)
    
    def get_critical_subsystems(self, threshold: float = 0.7) -> List[Subsystem]:
        """
        Get subsystems with high importance scores.
        
        Args:
            threshold: Minimum importance score
        
        Returns:
            List of critical subsystems
        """
        return [s for s in self.subsystems if s.importance_score >= threshold]
    
    def create_patch_groups(self, method: str = "dependencies") -> List[PatchGroup]:
        """
        Create patch groups from vulnerabilities.
        
        Args:
            method: Grouping method ("dependencies", "subsystem", "severity")
        
        Returns:
            List of PatchGroup objects
        """
        from .patch_group import collapse_by_subsystem, collapse_by_severity
        
        all_vulns = self.get_all_vulnerabilities()
        
        if method == "dependencies":
            return collapse_by_dependencies(all_vulns)
        elif method == "subsystem":
            return collapse_by_subsystem(all_vulns)
        elif method == "severity":
            return collapse_by_severity(all_vulns)
        else:
            raise ValueError(f"Unknown grouping method: {method}")
    
    def export_for_game(self, players: Optional[List[PlayerBase]] = None,
                       patch_grouping_method: str = "dependencies") -> Dict[str, Any]:
        """
        Export system as dictionary for game engine integration.
        
        This is the critical integration point with Developer B.
        
        Args:
            players: List of players (if None, creates default defender)
            patch_grouping_method: Method for grouping patches
        
        Returns:
            Dictionary conforming to integration contract
        """
        # Create default player if none provided
        if players is None:
            players = [PlayerBase.create_defender("default_defender", 100.0)]
        
        # Create patch groups
        patch_groups = self.create_patch_groups(method=patch_grouping_method)
        
        # Build export dictionary
        export_dict = {
            "api_version": "1.0.0",
            "system_name": self.system_class.name,
            "subsystems": [s.to_dict() for s in self.subsystems],
            "functional_dependencies": self.w_adj.tolist(),
            "network_topology": self.n_topology.tolist(),
            "weights": {
                "functional_weight": float(self.weights["functional_weight"]),
                "topological_weight": float(self.weights["topological_weight"])
            },
            "patch_groups": [pg.to_dict() for pg in patch_groups],
            "players": [p.to_dict() for p in players]
        }
        
        return export_dict
    
    def add_subsystem(self, subsystem: Subsystem):
        """
        Add a subsystem to the system.
        
        Args:
            subsystem: Subsystem to add
        """
        # Check for duplicate
        if any(s.id == subsystem.id for s in self.subsystems):
            raise ValueError(f"Subsystem with ID '{subsystem.id}' already exists")
        
        self.subsystems.append(subsystem)
        
        # Rebuild matrices
        self.w_adj = self._build_functional_matrix()
        self.n_topology = self._build_topology_matrix()
    
    def remove_subsystem(self, subsystem_id: str) -> bool:
        """
        Remove a subsystem by ID.
        
        Args:
            subsystem_id: ID of subsystem to remove
        
        Returns:
            True if removed, False if not found
        """
        for i, subsystem in enumerate(self.subsystems):
            if subsystem.id == subsystem_id:
                self.subsystems.pop(i)
                
                # Rebuild matrices
                self.w_adj = self._build_functional_matrix()
                self.n_topology = self._build_topology_matrix()
                return True
        return False
    
    def import_shared_vulnerability(self, shared_vuln, target_subsystem_id: str) -> Vulnerability:
        """
        Import a shared vulnerability into this system.
        
        Args:
            shared_vuln: SharedVulnerability object from repository
            target_subsystem_id: ID of subsystem to add vulnerability to
        
        Returns:
            The created Vulnerability object
        
        Raises:
            ValueError: If subsystem not found
        """
        # Find target subsystem
        target_subsystem = self.get_subsystem(target_subsystem_id)
        if not target_subsystem:
            raise ValueError(f"Subsystem '{target_subsystem_id}' not found")
        
        # Convert SharedVulnerability to Vulnerability
        vuln = Vulnerability(
            cve_id=shared_vuln.cve_id,
            description=shared_vuln.description,
            cvss_impact=shared_vuln.cvss_impact,
            cvss_exploitability=shared_vuln.cvss_exploitability,
            exploit_present=False,  # Conservative default
            patch_cost=shared_vuln.patch_cost,
            subsystem_id=target_subsystem_id,
            dependencies=[],  # Must be set manually if needed
            source="SHARED",
            shared_vuln_id=shared_vuln.shared_vuln_id
        )
        
        # Add to subsystem
        target_subsystem.add_vulnerability(vuln)
        
        return vuln
    
    def __repr__(self) -> str:
        return (f"SystemInstance(class='{self.system_class.name}', "
                f"subsystems={len(self.subsystems)}, "
                f"vulnerabilities={self.get_total_vulnerability_count()})")
