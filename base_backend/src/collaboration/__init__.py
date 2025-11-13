"""
Collaboration Module

Enables multi-user collaboration through shared vulnerability repositories.
Users can publish custom vulnerabilities and import discoveries from others.
"""

from .user import User
from .shared_vulnerability import SharedVulnerability
from .vulnerability_repository import VulnerabilityRepository
from .user_manager import UserManager

__all__ = ['User', 'SharedVulnerability', 'VulnerabilityRepository', 'UserManager']
