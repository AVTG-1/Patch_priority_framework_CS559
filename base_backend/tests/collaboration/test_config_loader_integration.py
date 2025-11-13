"""
Tests for ConfigLoader Integration with Collaboration Features
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

import pytest
import json
import tempfile
from data_model.config_loader import ConfigLoader


class TestConfigLoaderWithOwner:
    """Test config loader with owner_user_id field."""
    
    def test_load_system_with_owner(self):
        """Test loading system configuration with owner_user_id."""
        config = {
            "system_name": "Test System",
            "owner_user_id": "user_001",
            "subsystems": [
                {
                    "id": "web_001",
                    "name": "Web Server"
                }
            ]
        }
        
        loader = ConfigLoader()
        system = loader.load_from_dict(config)
        
        assert system.owner_user_id == "user_001"
    
    def test_load_system_without_owner(self):
        """Test loading system without owner_user_id (defaults to None)."""
        config = {
            "system_name": "Test System",
            "subsystems": [
                {
                    "id": "web_001",
                    "name": "Web Server"
                }
            ]
        }
        
        loader = ConfigLoader()
        system = loader.load_from_dict(config)
        
        assert system.owner_user_id is None
    
    def test_load_system_with_null_owner(self):
        """Test loading system with explicit null owner."""
        config = {
            "system_name": "Test System",
            "owner_user_id": None,
            "subsystems": [
                {
                    "id": "web_001",
                    "name": "Web Server"
                }
            ]
        }
        
        loader = ConfigLoader()
        system = loader.load_from_dict(config)
        
        assert system.owner_user_id is None


class TestConfigLoaderWithSourceField:
    """Test config loader with vulnerability source field."""
    
    def test_load_vulnerability_with_nvd_source(self):
        """Test loading vulnerability with NVD source."""
        config = {
            "system_name": "Test System",
            "subsystems": [
                {
                    "id": "web_001",
                    "name": "Web Server"
                }
            ],
            "vulnerabilities": [
                {
                    "cve_id": "CVE-2024-0001",
                    "subsystem_id": "web_001",
                    "cvss_impact": 7.5,
                    "cvss_exploitability": 8.0,
                    "patch_cost": 50.0,
                    "source": "NVD"
                }
            ]
        }
        
        loader = ConfigLoader()
        system = loader.load_from_dict(config)
        
        vuln = system.get_all_vulnerabilities()[0]
        assert vuln.source == "NVD"
        assert vuln.shared_vuln_id is None
    
    def test_load_vulnerability_with_shared_source(self):
        """Test loading vulnerability with SHARED source."""
        config = {
            "system_name": "Test System",
            "subsystems": [
                {
                    "id": "web_001",
                    "name": "Web Server"
                }
            ],
            "vulnerabilities": [
                {
                    "cve_id": "CVE-2024-0001",
                    "subsystem_id": "web_001",
                    "cvss_impact": 8.5,
                    "cvss_exploitability": 7.5,
                    "patch_cost": 75.0,
                    "source": "SHARED",
                    "shared_vuln_id": "SHARED-001"
                }
            ]
        }
        
        loader = ConfigLoader()
        system = loader.load_from_dict(config)
        
        vuln = system.get_all_vulnerabilities()[0]
        assert vuln.source == "SHARED"
        assert vuln.shared_vuln_id == "SHARED-001"
    
    def test_load_vulnerability_with_custom_source(self):
        """Test loading vulnerability with CUSTOM source."""
        config = {
            "system_name": "Test System",
            "subsystems": [
                {
                    "id": "web_001",
                    "name": "Web Server"
                }
            ],
            "vulnerabilities": [
                {
                    "cve_id": "CUSTOM-2024-0001",
                    "subsystem_id": "web_001",
                    "cvss_impact": 8.0,
                    "cvss_exploitability": 7.0,
                    "patch_cost": 60.0,
                    "source": "CUSTOM"
                }
            ]
        }
        
        loader = ConfigLoader()
        system = loader.load_from_dict(config)
        
        vuln = system.get_all_vulnerabilities()[0]
        assert vuln.source == "CUSTOM"
        assert vuln.cve_id == "CUSTOM-2024-0001"
    
    def test_load_vulnerability_without_source_defaults_nvd(self):
        """Test that vulnerability without source defaults to NVD."""
        config = {
            "system_name": "Test System",
            "subsystems": [
                {
                    "id": "web_001",
                    "name": "Web Server"
                }
            ],
            "vulnerabilities": [
                {
                    "cve_id": "CVE-2024-0001",
                    "subsystem_id": "web_001",
                    "cvss_impact": 7.5,
                    "cvss_exploitability": 8.0,
                    "patch_cost": 50.0
                }
            ]
        }
        
        loader = ConfigLoader()
        system = loader.load_from_dict(config)
        
        vuln = system.get_all_vulnerabilities()[0]
        assert vuln.source == "NVD"
    
    def test_load_multiple_vulnerabilities_mixed_sources(self):
        """Test loading multiple vulnerabilities with different sources."""
        config = {
            "system_name": "Test System",
            "subsystems": [
                {
                    "id": "web_001",
                    "name": "Web Server"
                }
            ],
            "vulnerabilities": [
                {
                    "cve_id": "CVE-2024-0001",
                    "subsystem_id": "web_001",
                    "cvss_impact": 7.5,
                    "cvss_exploitability": 8.0,
                    "patch_cost": 50.0,
                    "source": "NVD"
                },
                {
                    "cve_id": "CVE-2024-0002",
                    "subsystem_id": "web_001",
                    "cvss_impact": 8.5,
                    "cvss_exploitability": 7.5,
                    "patch_cost": 75.0,
                    "source": "SHARED",
                    "shared_vuln_id": "SHARED-001"
                },
                {
                    "cve_id": "CUSTOM-2024-0001",
                    "subsystem_id": "web_001",
                    "cvss_impact": 8.0,
                    "cvss_exploitability": 7.0,
                    "patch_cost": 60.0,
                    "source": "CUSTOM"
                }
            ]
        }
        
        loader = ConfigLoader()
        system = loader.load_from_dict(config)
        
        vulns = system.get_all_vulnerabilities()
        assert len(vulns) == 3
        
        sources = {v.source for v in vulns}
        assert sources == {"NVD", "SHARED", "CUSTOM"}


class TestConfigLoaderFromFile:
    """Test loading configuration from file with new fields."""
    
    def test_load_from_json_file_with_collaboration_fields(self):
        """Test loading from JSON file with owner and source fields."""
        config = {
            "system_name": "Collaboration Test System",
            "owner_user_id": "user_001",
            "subsystems": [
                {
                    "id": "web_001",
                    "name": "Web Server",
                    "connected_to": ["db_001"],
                    "functional_dependencies": ["db_001"]
                },
                {
                    "id": "db_001",
                    "name": "Database",
                    "connected_to": ["web_001"],
                    "functional_dependencies": []
                }
            ],
            "vulnerabilities": [
                {
                    "cve_id": "CVE-2024-0001",
                    "description": "From NVD",
                    "subsystem_id": "web_001",
                    "cvss_impact": 7.5,
                    "cvss_exploitability": 8.0,
                    "exploit_present": True,
                    "patch_cost": 50.0,
                    "dependencies": [],
                    "source": "NVD"
                },
                {
                    "cve_id": "CVE-2024-0002",
                    "description": "From community",
                    "subsystem_id": "db_001",
                    "cvss_impact": 8.5,
                    "cvss_exploitability": 7.5,
                    "exploit_present": False,
                    "patch_cost": 75.0,
                    "dependencies": [],
                    "source": "SHARED",
                    "shared_vuln_id": "SHARED-abc123"
                }
            ]
        }
        
        # Write to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config, f)
            temp_path = f.name
        
        try:
            loader = ConfigLoader()
            system = loader.load_system(temp_path)
            
            # Verify owner
            assert system.owner_user_id == "user_001"
            
            # Verify vulnerabilities
            vulns = system.get_all_vulnerabilities()
            assert len(vulns) == 2
            
            # Check NVD vulnerability
            nvd_vuln = [v for v in vulns if v.source == "NVD"][0]
            assert nvd_vuln.cve_id == "CVE-2024-0001"
            assert nvd_vuln.shared_vuln_id is None
            
            # Check SHARED vulnerability
            shared_vuln = [v for v in vulns if v.source == "SHARED"][0]
            assert shared_vuln.cve_id == "CVE-2024-0002"
            assert shared_vuln.shared_vuln_id == "SHARED-abc123"
            
        finally:
            # Clean up
            os.unlink(temp_path)
    
    def test_schema_validation_accepts_custom_cve_prefix(self):
        """Test that schema accepts CUSTOM- CVE prefix."""
        config = {
            "system_name": "Test System",
            "subsystems": [
                {
                    "id": "web_001",
                    "name": "Web Server"
                }
            ],
            "vulnerabilities": [
                {
                    "cve_id": "CUSTOM-2024-0001",
                    "subsystem_id": "web_001",
                    "cvss_impact": 8.0,
                    "cvss_exploitability": 7.0,
                    "patch_cost": 60.0,
                    "source": "CUSTOM"
                }
            ]
        }
        
        loader = ConfigLoader()
        system = loader.load_from_dict(config)
        
        vuln = system.get_all_vulnerabilities()[0]
        assert vuln.cve_id.startswith("CUSTOM-")


class TestBackwardCompatibility:
    """Test backward compatibility with old configuration files."""
    
    def test_old_config_without_collaboration_fields(self):
        """Test that old configs without new fields still work."""
        config = {
            "system_name": "Legacy System",
            "subsystems": [
                {
                    "id": "web_001",
                    "name": "Web Server"
                }
            ],
            "vulnerabilities": [
                {
                    "cve_id": "CVE-2024-0001",
                    "subsystem_id": "web_001",
                    "cvss_impact": 7.5,
                    "cvss_exploitability": 8.0,
                    "patch_cost": 50.0
                }
            ]
        }
        
        loader = ConfigLoader()
        system = loader.load_from_dict(config)
        
        # Should work with defaults
        assert system.owner_user_id is None
        
        vuln = system.get_all_vulnerabilities()[0]
        assert vuln.source == "NVD"  # Default
        assert vuln.shared_vuln_id is None
