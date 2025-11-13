"""
Player Model

Represents attacker and defender players in the game-theoretic framework.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class PlayerRole(Enum):
    """Enumeration of player roles."""
    ATTACKER = "ATTACKER"
    DEFENDER = "DEFENDER"


@dataclass
class PlayerBase:
    """
    Represents a player (attacker or defender) in the game.
    
    Attributes:
        player_id: Unique identifier for this player
        role: Player role (ATTACKER or DEFENDER)
        resource_budget: Available resources for actions
        team_id: Optional team identifier for multi-team scenarios
        strategy: Optional strategy identifier
    """
    player_id: str
    role: str
    resource_budget: float
    team_id: Optional[str] = None
    strategy: Optional[str] = None
    
    def __post_init__(self):
        """Validate player data after initialization."""
        self._validate()
    
    def _validate(self):
        """
        Validate player attributes.
        
        Raises:
            ValueError: If any attribute is invalid
        """
        if not self.player_id or not self.player_id.strip():
            raise ValueError("player_id cannot be empty")
        
        # Normalize and validate role
        if isinstance(self.role, PlayerRole):
            self.role = self.role.value
        
        valid_roles = [r.value for r in PlayerRole]
        if self.role not in valid_roles:
            raise ValueError(
                f"role must be one of {valid_roles}, got: {self.role}"
            )
        
        if self.resource_budget < 0:
            raise ValueError(f"resource_budget must be non-negative: {self.resource_budget}")
        
        if self.resource_budget == 0:
            import warnings
            warnings.warn(f"Player {self.player_id} has zero resource budget")
    
    def is_attacker(self) -> bool:
        """Check if this player is an attacker."""
        return self.role == PlayerRole.ATTACKER.value
    
    def is_defender(self) -> bool:
        """Check if this player is a defender."""
        return self.role == PlayerRole.DEFENDER.value
    
    def has_resources(self, required: float) -> bool:
        """
        Check if player has sufficient resources.
        
        Args:
            required: Required resource amount
        
        Returns:
            True if budget >= required
        """
        return self.resource_budget >= required
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Export player as dictionary for integration.
        
        Returns:
            Dictionary with player data, JSON-serializable
        """
        player_dict = {
            "player_id": self.player_id,
            "role": self.role,
            "resource_budget": float(self.resource_budget)
        }
        
        if self.team_id is not None:
            player_dict["team_id"] = self.team_id
        
        if self.strategy is not None:
            player_dict["strategy"] = self.strategy
        
        return player_dict
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PlayerBase':
        """
        Create PlayerBase from dictionary.
        
        Args:
            data: Dictionary with player data
        
        Returns:
            PlayerBase instance
        """
        return cls(
            player_id=data["player_id"],
            role=data["role"],
            resource_budget=float(data["resource_budget"]),
            team_id=data.get("team_id"),
            strategy=data.get("strategy")
        )
    
    @classmethod
    def create_defender(cls, player_id: str, resource_budget: float, 
                       team_id: Optional[str] = None) -> 'PlayerBase':
        """
        Factory method to create a defender player.
        
        Args:
            player_id: Unique player identifier
            resource_budget: Available resources
            team_id: Optional team identifier
        
        Returns:
            PlayerBase instance with DEFENDER role
        """
        return cls(
            player_id=player_id,
            role=PlayerRole.DEFENDER.value,
            resource_budget=resource_budget,
            team_id=team_id
        )
    
    @classmethod
    def create_attacker(cls, player_id: str, resource_budget: float,
                       team_id: Optional[str] = None) -> 'PlayerBase':
        """
        Factory method to create an attacker player.
        
        Args:
            player_id: Unique player identifier
            resource_budget: Available resources
            team_id: Optional team identifier
        
        Returns:
            PlayerBase instance with ATTACKER role
        """
        return cls(
            player_id=player_id,
            role=PlayerRole.ATTACKER.value,
            resource_budget=resource_budget,
            team_id=team_id
        )
    
    def __repr__(self) -> str:
        team_str = f", team='{self.team_id}'" if self.team_id else ""
        return (f"PlayerBase(id='{self.player_id}', role={self.role}, "
                f"budget={self.resource_budget}{team_str})")
    
    def __hash__(self) -> int:
        """Allow use in sets and as dict keys."""
        return hash(self.player_id)
    
    def __eq__(self, other) -> bool:
        """Compare players by ID."""
        if not isinstance(other, PlayerBase):
            return False
        return self.player_id == other.player_id
