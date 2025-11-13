"""
Patch Group Model

Aggregates vulnerabilities into patchable groups based on dependencies
and provides combined metrics.
"""

from typing import List, Dict, Any, Set
from dataclasses import dataclass, field
from .vulnerability import Vulnerability


@dataclass
class PatchGroup:
    """
    Represents a group of vulnerabilities that should be patched together.
    
    Attributes:
        group_id: Unique identifier for this patch group
        cve_ids: List of CVE IDs in this group
        vulnerabilities: List of Vulnerability objects
        total_cost: Combined cost to patch all vulnerabilities
        aggregate_impact: Combined impact metric
    """
    group_id: str
    cve_ids: List[str] = field(default_factory=list)
    vulnerabilities: List[Vulnerability] = field(default_factory=list)
    total_cost: float = 0.0
    aggregate_impact: float = 0.0
    
    def __post_init__(self):
        """Validate patch group data after initialization."""
        self._validate()
        if self.vulnerabilities and not self.cve_ids:
            self.cve_ids = [v.cve_id for v in self.vulnerabilities]
        if self.vulnerabilities:
            self._calculate_metrics()
    
    def _validate(self):
        """
        Validate patch group attributes.
        
        Raises:
            ValueError: If any attribute is invalid
        """
        if not self.group_id or not self.group_id.strip():
            raise ValueError("group_id cannot be empty")
        
        if not isinstance(self.cve_ids, list):
            raise ValueError("cve_ids must be a list")
        
        if not isinstance(self.vulnerabilities, list):
            raise ValueError("vulnerabilities must be a list")
        
        if len(self.cve_ids) != len(set(self.cve_ids)):
            raise ValueError(f"Duplicate CVE IDs found in group {self.group_id}")
        
        if self.total_cost < 0:
            raise ValueError(f"total_cost cannot be negative: {self.total_cost}")
        
        if self.aggregate_impact < 0:
            raise ValueError(f"aggregate_impact cannot be negative: {self.aggregate_impact}")
    
    def add_vulnerability(self, vulnerability: Vulnerability):
        """
        Add a vulnerability to this group.
        
        Args:
            vulnerability: Vulnerability to add
        """
        if vulnerability.cve_id in self.cve_ids:
            raise ValueError(f"Vulnerability {vulnerability.cve_id} already in group {self.group_id}")
        
        self.vulnerabilities.append(vulnerability)
        self.cve_ids.append(vulnerability.cve_id)
        self._calculate_metrics()
    
    def _calculate_metrics(self):
        """Calculate aggregate metrics from vulnerabilities."""
        if not self.vulnerabilities:
            self.total_cost = 0.0
            self.aggregate_impact = 0.0
            return
        
        # Sum of all patch costs
        self.total_cost = sum(v.patch_cost for v in self.vulnerabilities)
        
        # Maximum impact (worst vulnerability determines group impact)
        max_impact = max(v.cvss_impact for v in self.vulnerabilities)
        
        # Average exploitability
        avg_exploitability = sum(v.cvss_exploitability for v in self.vulnerabilities) / len(self.vulnerabilities)
        
        # Check if any has exploit
        has_exploit = any(v.exploit_present for v in self.vulnerabilities)
        exploit_multiplier = 1.5 if has_exploit else 1.0
        
        # Aggregate impact: combine metrics
        self.aggregate_impact = (max_impact + avg_exploitability) / 2.0 * exploit_multiplier
    
    def get_size(self) -> int:
        """Get number of vulnerabilities in this group."""
        return len(self.vulnerabilities)
    
    def contains_cve(self, cve_id: str) -> bool:
        """Check if group contains a specific CVE."""
        return cve_id in self.cve_ids
    
    def get_subsystems(self) -> Set[str]:
        """Get set of all subsystem IDs affected by this group."""
        return {v.subsystem_id for v in self.vulnerabilities}
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Export patch group as dictionary for integration.
        
        Returns:
            Dictionary with patch group data, JSON-serializable
        """
        return {
            "group_id": self.group_id,
            "cve_ids": list(self.cve_ids),
            "total_cost": float(self.total_cost),
            "aggregate_impact": float(self.aggregate_impact)
        }
    
    @classmethod
    def from_vulnerabilities(cls, group_id: str, vulnerabilities: List[Vulnerability]) -> 'PatchGroup':
        """
        Create a PatchGroup from a list of vulnerabilities.
        
        Args:
            group_id: Unique identifier for the group
            vulnerabilities: List of vulnerabilities to group
        
        Returns:
            PatchGroup instance
        """
        return cls(
            group_id=group_id,
            vulnerabilities=vulnerabilities,
            cve_ids=[v.cve_id for v in vulnerabilities]
        )
    
    def __repr__(self) -> str:
        return (f"PatchGroup(id='{self.group_id}', size={self.get_size()}, "
                f"cost={self.total_cost:.2f}, impact={self.aggregate_impact:.2f})")
    
    def __hash__(self) -> int:
        """Allow use in sets and as dict keys."""
        return hash(self.group_id)
    
    def __eq__(self, other) -> bool:
        """Compare patch groups by ID."""
        if not isinstance(other, PatchGroup):
            return False
        return self.group_id == other.group_id


def collapse_by_dependencies(vulnerabilities: List[Vulnerability]) -> List[PatchGroup]:
    """
    Collapse vulnerabilities into patch groups based on dependencies.
    
    Vulnerabilities with mutual dependencies are grouped together.
    Independent vulnerabilities get their own groups.
    
    Args:
        vulnerabilities: List of all vulnerabilities to group
    
    Returns:
        List of PatchGroup objects
    """
    if not vulnerabilities:
        return []
    
    # Build dependency graph
    vuln_map = {v.cve_id: v for v in vulnerabilities}
    visited = set()
    groups = []
    
    def get_dependency_closure(cve_id: str, closure: Set[str]):
        """Recursively find all dependencies."""
        if cve_id in closure or cve_id not in vuln_map:
            return
        
        closure.add(cve_id)
        vuln = vuln_map[cve_id]
        
        for dep_id in vuln.dependencies:
            get_dependency_closure(dep_id, closure)
        
        # Also find vulnerabilities that depend on this one
        for other_id, other_vuln in vuln_map.items():
            if cve_id in other_vuln.dependencies:
                get_dependency_closure(other_id, closure)
    
    # Create groups
    group_counter = 0
    for vuln in vulnerabilities:
        if vuln.cve_id in visited:
            continue
        
        # Get all related vulnerabilities
        closure = set()
        get_dependency_closure(vuln.cve_id, closure)
        
        # Mark as visited
        visited.update(closure)
        
        # Create group
        group_vulns = [vuln_map[cve_id] for cve_id in closure if cve_id in vuln_map]
        group_id = f"PG_{group_counter:04d}"
        group = PatchGroup.from_vulnerabilities(group_id, group_vulns)
        groups.append(group)
        
        group_counter += 1
    
    return groups


def collapse_by_subsystem(vulnerabilities: List[Vulnerability]) -> List[PatchGroup]:
    """
    Collapse vulnerabilities into patch groups by subsystem.
    
    All vulnerabilities in the same subsystem are grouped together.
    
    Args:
        vulnerabilities: List of all vulnerabilities to group
    
    Returns:
        List of PatchGroup objects
    """
    if not vulnerabilities:
        return []
    
    # Group by subsystem
    subsystem_groups = {}
    for vuln in vulnerabilities:
        if vuln.subsystem_id not in subsystem_groups:
            subsystem_groups[vuln.subsystem_id] = []
        subsystem_groups[vuln.subsystem_id].append(vuln)
    
    # Create patch groups
    groups = []
    for idx, (subsystem_id, vulns) in enumerate(subsystem_groups.items()):
        group_id = f"PG_{subsystem_id}_{idx:04d}"
        group = PatchGroup.from_vulnerabilities(group_id, vulns)
        groups.append(group)
    
    return groups


def collapse_by_severity(vulnerabilities: List[Vulnerability], 
                         thresholds: List[float] = None) -> List[PatchGroup]:
    """
    Collapse vulnerabilities into patch groups by severity levels.
    
    Args:
        vulnerabilities: List of all vulnerabilities to group
        thresholds: CVSS impact thresholds for grouping (default: [9.0, 7.0, 4.0])
    
    Returns:
        List of PatchGroup objects (Critical, High, Medium, Low)
    """
    if not vulnerabilities:
        return []
    
    if thresholds is None:
        thresholds = [9.0, 7.0, 4.0]
    
    # Group by severity
    severity_groups = {
        "CRITICAL": [],
        "HIGH": [],
        "MEDIUM": [],
        "LOW": []
    }
    
    for vuln in vulnerabilities:
        if vuln.cvss_impact >= thresholds[0]:
            severity_groups["CRITICAL"].append(vuln)
        elif vuln.cvss_impact >= thresholds[1]:
            severity_groups["HIGH"].append(vuln)
        elif vuln.cvss_impact >= thresholds[2]:
            severity_groups["MEDIUM"].append(vuln)
        else:
            severity_groups["LOW"].append(vuln)
    
    # Create patch groups
    groups = []
    for severity, vulns in severity_groups.items():
        if vulns:  # Only create group if non-empty
            group_id = f"PG_{severity}"
            group = PatchGroup.from_vulnerabilities(group_id, vulns)
            groups.append(group)
    
    return groups
