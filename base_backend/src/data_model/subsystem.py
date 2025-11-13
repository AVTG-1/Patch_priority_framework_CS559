"""
Subsystem Model

Represents a subsystem within a larger system, containing vulnerabilities
and dependency relationships.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from .vulnerability import Vulnerability


@dataclass
class Subsystem:
    """
    Represents a subsystem component within a system.
    
    Attributes:
        id: Unique identifier for this subsystem
        name: Human-readable name
        importance_score: Calculated importance score (0.0-1.0)
        vulnerabilities: List of vulnerabilities affecting this subsystem
        connected_ids: IDs of subsystems this one is connected to (network)
        functional_deps: IDs of subsystems this one functionally depends on
    """
    id: str
    name: str
    importance_score: float = 0.0
    vulnerabilities: List[Vulnerability] = field(default_factory=list)
    connected_ids: List[str] = field(default_factory=list)
    functional_deps: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate subsystem data after initialization."""
        self._validate()
    
    def _validate(self):
        """
        Validate subsystem attributes.
        
        Raises:
            ValueError: If any attribute is invalid
        """
        if not self.id or not self.id.strip():
            raise ValueError("Subsystem id cannot be empty")
        
        if not self.name or not self.name.strip():
            raise ValueError("Subsystem name cannot be empty")
        
        if not 0.0 <= self.importance_score <= 1.0:
            raise ValueError(f"importance_score must be between 0.0 and 1.0: {self.importance_score}")
        
        if not isinstance(self.vulnerabilities, list):
            raise ValueError("vulnerabilities must be a list")
        
        if not isinstance(self.connected_ids, list):
            raise ValueError("connected_ids must be a list")
        
        if not isinstance(self.functional_deps, list):
            raise ValueError("functional_deps must be a list")
        
        # Check for self-dependency
        if self.id in self.functional_deps:
            raise ValueError(f"Subsystem {self.id} cannot depend on itself")
        
        if self.id in self.connected_ids:
            raise ValueError(f"Subsystem {self.id} cannot be connected to itself")
        
        # Validate all vulnerabilities belong to this subsystem
        for vuln in self.vulnerabilities:
            if vuln.subsystem_id != self.id:
                raise ValueError(
                    f"Vulnerability {vuln.cve_id} subsystem_id '{vuln.subsystem_id}' "
                    f"does not match subsystem id '{self.id}'"
                )
    
    def add_vulnerability(self, vulnerability: Vulnerability):
        """
        Add a vulnerability to this subsystem.
        
        Args:
            vulnerability: Vulnerability to add
        
        Raises:
            ValueError: If vulnerability belongs to different subsystem
        """
        if vulnerability.subsystem_id != self.id:
            raise ValueError(
                f"Cannot add vulnerability {vulnerability.cve_id} with subsystem_id "
                f"'{vulnerability.subsystem_id}' to subsystem '{self.id}'"
            )
        
        # Check for duplicates
        if vulnerability in self.vulnerabilities:
            raise ValueError(f"Vulnerability {vulnerability.cve_id} already exists in subsystem {self.id}")
        
        self.vulnerabilities.append(vulnerability)
    
    def remove_vulnerability(self, cve_id: str) -> bool:
        """
        Remove a vulnerability by CVE ID.
        
        Args:
            cve_id: CVE identifier to remove
        
        Returns:
            True if removed, False if not found
        """
        for i, vuln in enumerate(self.vulnerabilities):
            if vuln.cve_id == cve_id:
                self.vulnerabilities.pop(i)
                return True
        return False
    
    def get_vulnerability(self, cve_id: str) -> Optional[Vulnerability]:
        """
        Get vulnerability by CVE ID.
        
        Args:
            cve_id: CVE identifier to find
        
        Returns:
            Vulnerability if found, None otherwise
        """
        for vuln in self.vulnerabilities:
            if vuln.cve_id == cve_id:
                return vuln
        return None
    
    def get_total_patch_cost(self) -> float:
        """
        Calculate total cost to patch all vulnerabilities.
        
        Returns:
            Sum of all patch costs
        """
        return sum(vuln.patch_cost for vuln in self.vulnerabilities)
    
    def get_vulnerability_count(self) -> int:
        """Get number of vulnerabilities in this subsystem."""
        return len(self.vulnerabilities)
    
    def get_critical_vulnerabilities(self, threshold: float = 7.0) -> List[Vulnerability]:
        """
        Get vulnerabilities with high impact scores.
        
        Args:
            threshold: Minimum CVSS impact score
        
        Returns:
            List of critical vulnerabilities
        """
        return [v for v in self.vulnerabilities if v.cvss_impact >= threshold]
    
    def has_exploitable_vulnerabilities(self) -> bool:
        """Check if any vulnerability has known exploits."""
        return any(v.exploit_present for v in self.vulnerabilities)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Export subsystem as dictionary for integration.
        
        Returns:
            Dictionary with subsystem data and all vulnerabilities
        """
        return {
            "id": self.id,
            "name": self.name,
            "importance_score": float(self.importance_score),
            "vulnerabilities": [v.to_dict() for v in self.vulnerabilities]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Subsystem':
        """
        Create Subsystem from dictionary.
        
        Args:
            data: Dictionary with subsystem data
        
        Returns:
            Subsystem instance
        """
        subsystem_id = data["id"]
        
        # Create vulnerabilities
        vulnerabilities = []
        for vuln_data in data.get("vulnerabilities", []):
            vuln = Vulnerability.from_dict(vuln_data, subsystem_id)
            vulnerabilities.append(vuln)
        
        return cls(
            id=subsystem_id,
            name=data["name"],
            importance_score=float(data.get("importance_score", 0.0)),
            vulnerabilities=vulnerabilities,
            connected_ids=data.get("connected_to", []),
            functional_deps=data.get("functional_dependencies", [])
        )
    
    def __repr__(self) -> str:
        return (f"Subsystem(id='{self.id}', name='{self.name}', "
                f"importance={self.importance_score:.3f}, "
                f"vulnerabilities={len(self.vulnerabilities)})")
    
    def __hash__(self) -> int:
        """Allow use in sets and as dict keys."""
        return hash(self.id)
    
    def __eq__(self, other) -> bool:
        """Compare subsystems by ID."""
        if not isinstance(other, Subsystem):
            return False
        return self.id == other.id
