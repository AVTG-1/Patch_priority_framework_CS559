"""
User Model

Represents a user in the collaboration system. Each user owns exactly one system.
"""

from typing import Optional
from dataclasses import dataclass
import re


@dataclass
class User:
    """
    Represents a user who owns a system and can collaborate.
    
    Attributes:
        user_id: Unique identifier for the user
        username: Unique username for login/display
        email: User's email address
        system_id: ID of the system owned by this user (one-to-one)
        created_at: Timestamp of user creation (optional)
    """
    user_id: str
    username: str
    email: str
    system_id: str
    created_at: Optional[str] = None
    
    def __post_init__(self):
        """Validate user data after initialization."""
        self._validate()
    
    def _validate(self):
        """
        Validate user attributes.
        
        Raises:
            ValueError: If any attribute is invalid
        """
        if not self.user_id or not self.user_id.strip():
            raise ValueError("user_id cannot be empty")
        
        if not self.username or not self.username.strip():
            raise ValueError("username cannot be empty")
        
        if len(self.username) < 3:
            raise ValueError("username must be at least 3 characters")
        
        if not re.match(r'^[a-zA-Z0-9_-]+$', self.username):
            raise ValueError("username can only contain alphanumeric characters, hyphens, and underscores")
        
        if not self.email or not self.email.strip():
            raise ValueError("email cannot be empty")
        
        # Basic email validation
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', self.email):
            raise ValueError(f"invalid email format: {self.email}")
        
        if not self.system_id or not self.system_id.strip():
            raise ValueError("system_id cannot be empty")
    
    def to_dict(self):
        """
        Export user as dictionary.
        
        Returns:
            Dictionary with all user data
        """
        return {
            "user_id": self.user_id,
            "username": self.username,
            "email": self.email,
            "system_id": self.system_id,
            "created_at": self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'User':
        """
        Create User from dictionary.
        
        Args:
            data: Dictionary with user data
        
        Returns:
            User instance
        """
        return cls(
            user_id=data["user_id"],
            username=data["username"],
            email=data["email"],
            system_id=data["system_id"],
            created_at=data.get("created_at")
        )
    
    def __repr__(self) -> str:
        return f"User(user_id='{self.user_id}', username='{self.username}', system_id='{self.system_id}')"
    
    def __hash__(self) -> int:
        """Allow use in sets and as dict keys."""
        return hash(self.user_id)
    
    def __eq__(self, other) -> bool:
        """Compare users by user_id."""
        if not isinstance(other, User):
            return False
        return self.user_id == other.user_id
