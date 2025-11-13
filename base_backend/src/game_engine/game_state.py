"""
Game State Module

Manages the game state by loading export from Developer A and maintaining
current system configuration, vulnerabilities, and player information.
"""

from typing import Dict, Any, List, Optional
import numpy as np


class GameState:
    """
    Represents the current state of the game.
    
    Loads and manages data exported from Developer A's SystemInstance,
    tracking the current vulnerabilities, patches applied, and game progress.
    """
    
    def __init__(self):
        """Initialize empty game state."""
        self.api_version: Optional[str] = None
        self.system_name: Optional[str] = None
        self.subsystems: List[Dict[str, Any]] = []
        self.functional_dependencies: np.ndarray = None
        self.network_topology: np.ndarray = None
        self.weights: Dict[str, float] = {}
        self.patch_groups: List[Dict[str, Any]] = []
        self.players: List[Dict[str, Any]] = []
        
        # Game progress tracking
        self.current_round: int = 0
        self.patched_cves: set = set()
        self.exploited_cves: set = set()
        self.remaining_vulnerabilities: List[Dict[str, Any]] = []
    
    @classmethod
    def load_from_export(cls, export_dict: Dict[str, Any]) -> 'GameState':
        """
        Load game state from Developer A's export dictionary.
        
        Args:
            export_dict: Dictionary from SystemInstance.export_for_game()
        
        Returns:
            GameState instance initialized with export data
        
        Raises:
            ValueError: If export format is invalid
        """
        state = cls()
        state._validate_export(export_dict)
        state._load_export(export_dict)
        return state
    
    def _validate_export(self, export_dict: Dict[str, Any]):
        """
        Validate export dictionary has required keys.
        
        Args:
            export_dict: Export dictionary to validate
        
        Raises:
            ValueError: If required keys are missing
        """
        required_keys = [
            'api_version', 'system_name', 'subsystems',
            'functional_dependencies', 'network_topology',
            'weights', 'patch_groups', 'players'
        ]
        
        missing_keys = [key for key in required_keys if key not in export_dict]
        if missing_keys:
            raise ValueError(f"Export missing required keys: {missing_keys}")
        
        # Validate API version
        if export_dict['api_version'] != '1.0.0':
            raise ValueError(f"Unsupported API version: {export_dict['api_version']}")
    
    def _load_export(self, export_dict: Dict[str, Any]):
        """Load data from validated export dictionary."""
        self.api_version = export_dict['api_version']
        self.system_name = export_dict['system_name']
        self.subsystems = export_dict['subsystems']
        
        # Convert matrices to numpy arrays
        self.functional_dependencies = np.array(export_dict['functional_dependencies'])
        self.network_topology = np.array(export_dict['network_topology'])
        
        self.weights = export_dict['weights']
        self.patch_groups = export_dict['patch_groups']
        self.players = export_dict['players']
        
        # Initialize remaining vulnerabilities
        self._initialize_vulnerabilities()
    
    def _initialize_vulnerabilities(self):
        """Extract all vulnerabilities from subsystems."""
        self.remaining_vulnerabilities = []
        for subsystem in self.subsystems:
            for vuln in subsystem['vulnerabilities']:
                vuln_copy = vuln.copy()
                vuln_copy['subsystem_id'] = subsystem['id']
                vuln_copy['subsystem_name'] = subsystem['name']
                vuln_copy['importance_score'] = subsystem['importance_score']
                self.remaining_vulnerabilities.append(vuln_copy)
    
    def get_subsystem_count(self) -> int:
        """Get number of subsystems."""
        return len(self.subsystems)
    
    def get_vulnerability_count(self) -> int:
        """Get number of remaining vulnerabilities."""
        return len(self.remaining_vulnerabilities)
    
    def get_patch_group_count(self) -> int:
        """Get number of patch groups."""
        return len(self.patch_groups)
    
    def get_players_by_role(self, role: str) -> List[Dict[str, Any]]:
        """
        Get players by role.
        
        Args:
            role: "ATTACKER" or "DEFENDER"
        
        Returns:
            List of player dictionaries
        """
        return [p for p in self.players if p['role'] == role]
    
    def get_defenders(self) -> List[Dict[str, Any]]:
        """Get all defender players."""
        return self.get_players_by_role("DEFENDER")
    
    def get_attackers(self) -> List[Dict[str, Any]]:
        """Get all attacker players."""
        return self.get_players_by_role("ATTACKER")
    
    def get_patch_group(self, group_id: str) -> Optional[Dict[str, Any]]:
        """
        Get patch group by ID.
        
        Args:
            group_id: Patch group identifier
        
        Returns:
            Patch group dictionary or None
        """
        for group in self.patch_groups:
            if group['group_id'] == group_id:
                return group
        return None
    
    def get_vulnerability(self, cve_id: str) -> Optional[Dict[str, Any]]:
        """
        Get vulnerability by CVE ID.
        
        Args:
            cve_id: CVE identifier
        
        Returns:
            Vulnerability dictionary or None
        """
        for vuln in self.remaining_vulnerabilities:
            if vuln['cve_id'] == cve_id:
                return vuln
        return None
    
    def apply_patches(self, cve_ids: List[str]):
        """
        Apply patches to vulnerabilities.
        
        Args:
            cve_ids: List of CVE IDs to patch
        """
        for cve_id in cve_ids:
            self.patched_cves.add(cve_id)
            # Remove from remaining vulnerabilities
            self.remaining_vulnerabilities = [
                v for v in self.remaining_vulnerabilities 
                if v['cve_id'] != cve_id
            ]
    
    def apply_patch_group(self, group_id: str):
        """
        Apply all patches in a group.
        
        Args:
            group_id: Patch group ID
        """
        group = self.get_patch_group(group_id)
        if group:
            self.apply_patches(group['cve_ids'])
    
    def exploit_vulnerabilities(self, cve_ids: List[str]):
        """
        Mark vulnerabilities as exploited.
        
        Args:
            cve_ids: List of CVE IDs exploited
        """
        for cve_id in cve_ids:
            if cve_id not in self.patched_cves:
                self.exploited_cves.add(cve_id)
    
    def calculate_remaining_impact(self) -> float:
        """
        Calculate Remaining Impact Score (RIS).
        
        Returns:
            Sum of impact scores for remaining vulnerabilities
        """
        total_impact = 0.0
        for vuln in self.remaining_vulnerabilities:
            # Weight by subsystem importance and CVSS impact
            impact = vuln['cvss_impact'] * vuln['importance_score']
            
            # Apply exploit multiplier
            if vuln.get('exploit_present', False):
                impact *= 1.5
            
            total_impact += impact
        
        return total_impact
    
    def get_subsystem_vulnerability_count(self, subsystem_id: str) -> int:
        """
        Get number of remaining vulnerabilities in a subsystem.
        
        Args:
            subsystem_id: Subsystem identifier
        
        Returns:
            Count of vulnerabilities
        """
        return sum(
            1 for v in self.remaining_vulnerabilities 
            if v.get('subsystem_id') == subsystem_id
        )
    
    def is_vulnerability_patchable(self, cve_id: str) -> bool:
        """
        Check if vulnerability can be patched (dependencies satisfied).
        
        Args:
            cve_id: CVE identifier
        
        Returns:
            True if all dependencies are patched
        """
        vuln = self.get_vulnerability(cve_id)
        if not vuln:
            return False
        
        dependencies = vuln.get('dependencies', [])
        return all(dep in self.patched_cves for dep in dependencies)
    
    def get_patchable_vulnerabilities(self) -> List[Dict[str, Any]]:
        """
        Get vulnerabilities that can currently be patched.
        
        Returns:
            List of patchable vulnerabilities
        """
        return [
            v for v in self.remaining_vulnerabilities
            if self.is_vulnerability_patchable(v['cve_id'])
        ]
    
    def advance_round(self):
        """Advance to next round."""
        self.current_round += 1
    
    def get_state_summary(self) -> Dict[str, Any]:
        """
        Get summary of current game state.
        
        Returns:
            Dictionary with state statistics
        """
        return {
            'round': self.current_round,
            'system_name': self.system_name,
            'total_subsystems': self.get_subsystem_count(),
            'remaining_vulnerabilities': self.get_vulnerability_count(),
            'patched_vulnerabilities': len(self.patched_cves),
            'exploited_vulnerabilities': len(self.exploited_cves),
            'remaining_impact_score': self.calculate_remaining_impact(),
            'patch_groups_available': self.get_patch_group_count(),
            'defenders': len(self.get_defenders()),
            'attackers': len(self.get_attackers())
        }
    
    def reset(self):
        """Reset game state to initial conditions."""
        self.current_round = 0
        self.patched_cves.clear()
        self.exploited_cves.clear()
        self._initialize_vulnerabilities()
    
    def __repr__(self) -> str:
        return (f"GameState(system='{self.system_name}', round={self.current_round}, "
                f"vulnerabilities={self.get_vulnerability_count()}, "
                f"patched={len(self.patched_cves)})")
