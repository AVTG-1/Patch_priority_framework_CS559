"""
Data Model Module

Provides core data structures and utilities for the Patch Prioritization Framework.

This module implements Developer A's responsibilities:
- System and subsystem modeling
- Vulnerability and patch group management
- Player modeling
- Risk assessment and scoring
- Configuration loading and NVD integration
"""

__version__ = "1.0.0"
__api_version__ = "1.0.0"

# Core data models
from .system import SystemClass, SystemInstance
from .subsystem import Subsystem
from .vulnerability import Vulnerability
from .patch_group import (
    PatchGroup,
    collapse_by_dependencies,
    collapse_by_subsystem,
    collapse_by_severity
)
from .player import PlayerBase, PlayerRole

# Utilities
from .config_loader import ConfigLoader
from .nvd_importer import NVDImporter
from .risk_calculator import RiskCalculator

__all__ = [
    # Version info
    "__version__",
    "__api_version__",
    
    # System models
    "SystemClass",
    "SystemInstance",
    
    # Component models
    "Subsystem",
    "Vulnerability",
    "PatchGroup",
    "PlayerBase",
    "PlayerRole",
    
    # Patch grouping functions
    "collapse_by_dependencies",
    "collapse_by_subsystem",
    "collapse_by_severity",
    
    # Utilities
    "ConfigLoader",
    "NVDImporter",
    "RiskCalculator",
]
