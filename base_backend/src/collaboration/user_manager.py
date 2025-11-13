"""
User Manager

Manages user accounts and their system associations.
Ensures one-to-one relationship between users and systems.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from typing import List, Optional, Dict, Set
from user import User


class UserManager:
    """
    Manager for user accounts and system associations.
    
    Attributes:
        _users: Dictionary mapping user_id to User
        _username_index: Dictionary mapping username to user_id (for uniqueness)
        _email_index: Dictionary mapping email to user_id (for uniqueness)
        _system_index: Dictionary mapping system_id to user_id (for one-to-one)
    """
    
    def __init__(self):
        """Initialize empty user manager."""
        self._users: Dict[str, User] = {}
        self._username_index: Dict[str, str] = {}
        self._email_index: Dict[str, str] = {}
        self._system_index: Dict[str, str] = {}
    
    def create_user(self, user: User) -> User:
        """
        Create a new user.
        
        Args:
            user: User to create
        
        Returns:
            The created user
        
        Raises:
            ValueError: If user_id, username, email, or system_id already exists
        """
        # Check for duplicate user_id
        if user.user_id in self._users:
            raise ValueError(f"User with ID {user.user_id} already exists")
        
        # Check for duplicate username
        if user.username in self._username_index:
            raise ValueError(f"Username '{user.username}' already taken")
        
        # Check for duplicate email
        if user.email in self._email_index:
            raise ValueError(f"Email '{user.email}' already registered")
        
        # Check for duplicate system_id (one-to-one constraint)
        if user.system_id in self._system_index:
            raise ValueError(f"System {user.system_id} already owned by another user")
        
        # Add to storage and indices
        self._users[user.user_id] = user
        self._username_index[user.username] = user.user_id
        self._email_index[user.email] = user.user_id
        self._system_index[user.system_id] = user.user_id
        
        return user
    
    def get(self, user_id: str) -> Optional[User]:
        """
        Get a user by ID.
        
        Args:
            user_id: ID of the user
        
        Returns:
            User if found, None otherwise
        """
        return self._users.get(user_id)
    
    def get_by_username(self, username: str) -> Optional[User]:
        """
        Get a user by username.
        
        Args:
            username: Username to look up
        
        Returns:
            User if found, None otherwise
        """
        user_id = self._username_index.get(username)
        if user_id:
            return self._users.get(user_id)
        return None
    
    def get_by_email(self, email: str) -> Optional[User]:
        """
        Get a user by email.
        
        Args:
            email: Email to look up
        
        Returns:
            User if found, None otherwise
        """
        user_id = self._email_index.get(email)
        if user_id:
            return self._users.get(user_id)
        return None
    
    def get_by_system(self, system_id: str) -> Optional[User]:
        """
        Get the user who owns a specific system.
        
        Args:
            system_id: ID of the system
        
        Returns:
            User who owns this system, None if system not owned
        """
        user_id = self._system_index.get(system_id)
        if user_id:
            return self._users.get(user_id)
        return None
    
    def update(self, user: User) -> User:
        """
        Update an existing user.
        
        Args:
            user: Updated user (must have existing user_id)
        
        Returns:
            The updated user
        
        Raises:
            ValueError: If user doesn't exist or update violates constraints
        """
        if user.user_id not in self._users:
            raise ValueError(f"User {user.user_id} not found")
        
        # Get old user data from indices (not from _users which might be same object)
        old_username = None
        old_email = None
        old_system = None
        
        for username, uid in self._username_index.items():
            if uid == user.user_id:
                old_username = username
                break
        
        for email, uid in self._email_index.items():
            if uid == user.user_id:
                old_email = email
                break
        
        for system, uid in self._system_index.items():
            if uid == user.user_id:
                old_system = system
                break
        
        # Check if username changed and if new username is taken
        if user.username != old_username:
            if user.username in self._username_index:
                raise ValueError(f"Username '{user.username}' already taken")
            # Update username index
            if old_username:
                del self._username_index[old_username]
            self._username_index[user.username] = user.user_id
        
        # Check if email changed and if new email is taken
        if user.email != old_email:
            if user.email in self._email_index:
                raise ValueError(f"Email '{user.email}' already registered")
            # Update email index
            if old_email:
                del self._email_index[old_email]
            self._email_index[user.email] = user.user_id
        
        # Check if system_id changed and if new system is already owned
        if user.system_id != old_system:
            if user.system_id in self._system_index:
                raise ValueError(f"System {user.system_id} already owned by another user")
            # Update system index
            if old_system:
                del self._system_index[old_system]
            self._system_index[user.system_id] = user.user_id
        
        # Update user
        self._users[user.user_id] = user
        return user
    
    def delete(self, user_id: str) -> bool:
        """
        Delete a user.
        
        Args:
            user_id: ID of user to delete
        
        Returns:
            True if deleted, False if not found
        """
        if user_id not in self._users:
            return False
        
        user = self._users[user_id]
        
        # Remove from all indices
        del self._users[user_id]
        del self._username_index[user.username]
        del self._email_index[user.email]
        del self._system_index[user.system_id]
        
        return True
    
    def list_all(self) -> List[User]:
        """
        Get all users.
        
        Returns:
            List of all users
        """
        return list(self._users.values())
    
    def count(self) -> int:
        """
        Get total count of users.
        
        Returns:
            Number of users
        """
        return len(self._users)
    
    def clear(self):
        """Clear all users."""
        self._users.clear()
        self._username_index.clear()
        self._email_index.clear()
        self._system_index.clear()
    
    def username_exists(self, username: str) -> bool:
        """
        Check if username is taken.
        
        Args:
            username: Username to check
        
        Returns:
            True if username exists
        """
        return username in self._username_index
    
    def email_exists(self, email: str) -> bool:
        """
        Check if email is registered.
        
        Args:
            email: Email to check
        
        Returns:
            True if email exists
        """
        return email in self._email_index
    
    def system_has_owner(self, system_id: str) -> bool:
        """
        Check if a system has an owner.
        
        Args:
            system_id: System ID to check
        
        Returns:
            True if system is owned by a user
        """
        return system_id in self._system_index
    
    def search_users(self, username_pattern: Optional[str] = None) -> List[User]:
        """
        Search users by username pattern.
        
        Args:
            username_pattern: Substring to match in username (case-insensitive)
        
        Returns:
            List of matching users
        """
        if username_pattern is None:
            return self.list_all()
        
        pattern_lower = username_pattern.lower()
        return [
            user for user in self._users.values()
            if pattern_lower in user.username.lower()
        ]
