"""
Configuration Loader

Validates and parses system configurations from JSON/YAML files.
"""

import json
import os
from typing import Dict, Any, List, Optional
from jsonschema import validate, ValidationError
from .system import SystemClass, SystemInstance
from .subsystem import Subsystem
from .vulnerability import Vulnerability
from .player import PlayerBase


class ConfigLoader:
    """
    Loads and validates system configurations from files.
    """
    
    # JSON Schema for system configuration
    SYSTEM_SCHEMA = {
        "type": "object",
        "required": ["system_name", "subsystems"],
        "properties": {
            "system_name": {"type": "string", "minLength": 1},
            "system_class": {"type": "string"},
            "owner_user_id": {"type": ["string", "null"]},
            "subsystems": {
                "type": "array",
                "minItems": 1,
                "items": {
                    "type": "object",
                    "required": ["id", "name"],
                    "properties": {
                        "id": {"type": "string", "minLength": 1},
                        "name": {"type": "string", "minLength": 1},
                        "connected_to": {"type": "array", "items": {"type": "string"}},
                        "functional_dependencies": {"type": "array", "items": {"type": "string"}}
                    }
                }
            },
            "vulnerabilities": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["cve_id", "subsystem_id", "cvss_impact", 
                               "cvss_exploitability", "patch_cost"],
                    "properties": {
                        "cve_id": {"type": "string", "pattern": "^(CVE-|CUSTOM-)"},
                        "description": {"type": "string"},
                        "subsystem_id": {"type": "string"},
                        "cvss_impact": {"type": "number", "minimum": 0, "maximum": 10},
                        "cvss_exploitability": {"type": "number", "minimum": 0, "maximum": 10},
                        "exploit_present": {"type": "boolean"},
                        "patch_cost": {"type": "number", "minimum": 0},
                        "dependencies": {"type": "array", "items": {"type": "string"}},
                        "source": {"type": "string", "enum": ["NVD", "SHARED", "CUSTOM"]},
                        "shared_vuln_id": {"type": ["string", "null"]}
                    }
                }
            },
            "players": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["player_id", "role", "resource_budget"],
                    "properties": {
                        "player_id": {"type": "string"},
                        "role": {"type": "string", "enum": ["ATTACKER", "DEFENDER"]},
                        "resource_budget": {"type": "number", "minimum": 0},
                        "team_id": {"type": ["string", "null"]}
                    }
                }
            },
            "weights": {
                "type": "object",
                "properties": {
                    "functional_weight": {"type": "number", "minimum": 0, "maximum": 1},
                    "topological_weight": {"type": "number", "minimum": 0, "maximum": 1}
                }
            }
        }
    }
    
    def __init__(self):
        """Initialize configuration loader."""
        self.yaml_available = False
        try:
            import yaml
            self.yaml = yaml
            self.yaml_available = True
        except ImportError:
            pass
    
    def load_system(self, filepath: str) -> SystemInstance:
        """
        Load system from configuration file.
        
        Supports JSON and YAML formats (if PyYAML installed).
        
        Args:
            filepath: Path to configuration file
        
        Returns:
            SystemInstance object
        
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If configuration is invalid
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Configuration file not found: {filepath}")
        
        # Determine file type and load
        _, ext = os.path.splitext(filepath)
        
        with open(filepath, 'r') as f:
            if ext.lower() in ['.yaml', '.yml']:
                if not self.yaml_available:
                    raise ImportError("PyYAML not installed. Install with: pip install PyYAML")
                config = self.yaml.safe_load(f)
            else:  # Assume JSON
                config = json.load(f)
        
        return self.load_from_dict(config)
    
    def load_from_dict(self, config: Dict[str, Any]) -> SystemInstance:
        """
        Load system from configuration dictionary.
        
        Args:
            config: Configuration dictionary
        
        Returns:
            SystemInstance object
        
        Raises:
            ValueError: If configuration is invalid
        """
        # Validate schema
        try:
            validate(instance=config, schema=self.SYSTEM_SCHEMA)
        except ValidationError as e:
            raise ValueError(f"Configuration validation failed: {e.message}")
        
        # Extract components
        system_name = config["system_name"]
        system_class_name = config.get("system_class", system_name)
        
        # Create system class
        system_class = SystemClass(
            name=system_class_name,
            description=config.get("description", ""),
            weight_config=config.get("weights", {})
        )
        
        # Create subsystems
        subsystems = self._load_subsystems(config["subsystems"])
        
        # Add vulnerabilities to subsystems
        if "vulnerabilities" in config:
            self._load_vulnerabilities(config["vulnerabilities"], subsystems)
        
        # Create system instance
        weights = config.get("weights")
        owner_user_id = config.get("owner_user_id")
        system = SystemInstance(
            system_class=system_class,
            subsystems=subsystems,
            weights=weights,
            owner_user_id=owner_user_id
        )
        
        return system
    
    def _load_subsystems(self, subsystem_configs: List[Dict[str, Any]]) -> List[Subsystem]:
        """
        Load subsystems from configuration.
        
        Args:
            subsystem_configs: List of subsystem configuration dicts
        
        Returns:
            List of Subsystem objects
        """
        subsystems = []
        
        for config in subsystem_configs:
            subsystem = Subsystem(
                id=config["id"],
                name=config["name"],
                importance_score=config.get("importance_score", 0.0),
                vulnerabilities=[],
                connected_ids=config.get("connected_to", []),
                functional_deps=config.get("functional_dependencies", [])
            )
            subsystems.append(subsystem)
        
        return subsystems
    
    def _load_vulnerabilities(self, vuln_configs: List[Dict[str, Any]], 
                            subsystems: List[Subsystem]):
        """
        Load vulnerabilities and add to subsystems.
        
        Args:
            vuln_configs: List of vulnerability configuration dicts
            subsystems: List of subsystem objects to add vulnerabilities to
        """
        # Create subsystem lookup
        subsystem_map = {s.id: s for s in subsystems}
        
        for config in vuln_configs:
            subsystem_id = config["subsystem_id"]
            
            if subsystem_id not in subsystem_map:
                raise ValueError(f"Vulnerability references unknown subsystem: {subsystem_id}")
            
            vulnerability = Vulnerability(
                cve_id=config["cve_id"],
                description=config.get("description", ""),
                cvss_impact=config["cvss_impact"],
                cvss_exploitability=config["cvss_exploitability"],
                exploit_present=config.get("exploit_present", False),
                patch_cost=config["patch_cost"],
                subsystem_id=subsystem_id,
                dependencies=config.get("dependencies", []),
                custom_extras=config.get("custom_extras", {}),
                source=config.get("source", "NVD"),
                shared_vuln_id=config.get("shared_vuln_id")
            )
            
            subsystem_map[subsystem_id].add_vulnerability(vulnerability)
    
    def load_players(self, config: Dict[str, Any]) -> List[PlayerBase]:
        """
        Load players from configuration.
        
        Args:
            config: Full configuration dictionary
        
        Returns:
            List of PlayerBase objects
        """
        if "players" not in config:
            return []
        
        players = []
        for player_config in config["players"]:
            player = PlayerBase.from_dict(player_config)
            players.append(player)
        
        return players
    
    def validate_inputs(self, config: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate configuration without loading.
        
        Args:
            config: Configuration dictionary to validate
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            validate(instance=config, schema=self.SYSTEM_SCHEMA)
            
            # Additional semantic validation
            subsystem_ids = {s["id"] for s in config["subsystems"]}
            
            # Check vulnerability references
            if "vulnerabilities" in config:
                for vuln in config["vulnerabilities"]:
                    if vuln["subsystem_id"] not in subsystem_ids:
                        return False, f"Vulnerability {vuln['cve_id']} references unknown subsystem"
            
            # Check dependency references
            for subsystem in config["subsystems"]:
                for dep in subsystem.get("functional_dependencies", []):
                    if dep not in subsystem_ids:
                        return False, f"Subsystem {subsystem['id']} has invalid dependency: {dep}"
                
                for conn in subsystem.get("connected_to", []):
                    if conn not in subsystem_ids:
                        return False, f"Subsystem {subsystem['id']} has invalid connection: {conn}"
            
            return True, None
            
        except ValidationError as e:
            return False, str(e.message)
        except Exception as e:
            return False, str(e)
    
    def save_system(self, system: SystemInstance, filepath: str, 
                   include_players: bool = True):
        """
        Save system configuration to file.
        
        Args:
            system: System instance to save
            filepath: Output file path
            include_players: Whether to include player definitions
        """
        # Build configuration dictionary
        config = {
            "system_name": system.system_class.name,
            "system_class": system.system_class.name,
            "description": system.system_class.description,
            "subsystems": [],
            "vulnerabilities": [],
            "weights": system.weights
        }
        
        # Add subsystems
        for subsystem in system.subsystems:
            subsys_config = {
                "id": subsystem.id,
                "name": subsystem.name,
                "connected_to": subsystem.connected_ids,
                "functional_dependencies": subsystem.functional_deps
            }
            config["subsystems"].append(subsys_config)
            
            # Add vulnerabilities
            for vuln in subsystem.vulnerabilities:
                vuln_config = {
                    "cve_id": vuln.cve_id,
                    "description": vuln.description,
                    "subsystem_id": vuln.subsystem_id,
                    "cvss_impact": vuln.cvss_impact,
                    "cvss_exploitability": vuln.cvss_exploitability,
                    "exploit_present": vuln.exploit_present,
                    "patch_cost": vuln.patch_cost,
                    "dependencies": vuln.dependencies
                }
                config["vulnerabilities"].append(vuln_config)
        
        # Determine format and save
        _, ext = os.path.splitext(filepath)
        
        with open(filepath, 'w') as f:
            if ext.lower() in ['.yaml', '.yml']:
                if not self.yaml_available:
                    raise ImportError("PyYAML not installed. Install with: pip install PyYAML")
                self.yaml.dump(config, f, default_flow_style=False)
            else:  # JSON
                json.dump(config, f, indent=2)
