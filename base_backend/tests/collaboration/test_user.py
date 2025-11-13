"""
Tests for User Model
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from collaboration.user import User


class TestUserCreation:
    """Test user instantiation and validation."""
    
    def test_valid_user_creation(self):
        """Test creating a valid user."""
        user = User(
            user_id="user_001",
            username="alice_dev",
            email="alice@example.com",
            system_id="sys_001"
        )
        assert user.user_id == "user_001"
        assert user.username == "alice_dev"
        assert user.email == "alice@example.com"
        assert user.system_id == "sys_001"
    
    def test_user_with_created_at(self):
        """Test user creation with timestamp."""
        user = User(
            user_id="user_002",
            username="bob",
            email="bob@test.com",
            system_id="sys_002",
            created_at="2024-01-15T10:30:00Z"
        )
        assert user.created_at == "2024-01-15T10:30:00Z"
    
    def test_empty_user_id_raises_error(self):
        """Test that empty user_id raises ValueError."""
        with pytest.raises(ValueError, match="user_id cannot be empty"):
            User(
                user_id="",
                username="alice",
                email="alice@example.com",
                system_id="sys_001"
            )
    
    def test_empty_username_raises_error(self):
        """Test that empty username raises ValueError."""
        with pytest.raises(ValueError, match="username cannot be empty"):
            User(
                user_id="user_001",
                username="",
                email="alice@example.com",
                system_id="sys_001"
            )
    
    def test_short_username_raises_error(self):
        """Test that username < 3 chars raises ValueError."""
        with pytest.raises(ValueError, match="username must be at least 3 characters"):
            User(
                user_id="user_001",
                username="ab",
                email="alice@example.com",
                system_id="sys_001"
            )
    
    def test_invalid_username_characters_raises_error(self):
        """Test that invalid username characters raise ValueError."""
        with pytest.raises(ValueError, match="username can only contain"):
            User(
                user_id="user_001",
                username="alice@dev",
                email="alice@example.com",
                system_id="sys_001"
            )
    
    def test_empty_email_raises_error(self):
        """Test that empty email raises ValueError."""
        with pytest.raises(ValueError, match="email cannot be empty"):
            User(
                user_id="user_001",
                username="alice",
                email="",
                system_id="sys_001"
            )
    
    def test_invalid_email_format_raises_error(self):
        """Test that invalid email format raises ValueError."""
        with pytest.raises(ValueError, match="invalid email format"):
            User(
                user_id="user_001",
                username="alice",
                email="not-an-email",
                system_id="sys_001"
            )
    
    def test_empty_system_id_raises_error(self):
        """Test that empty system_id raises ValueError."""
        with pytest.raises(ValueError, match="system_id cannot be empty"):
            User(
                user_id="user_001",
                username="alice",
                email="alice@example.com",
                system_id=""
            )


class TestUserMethods:
    """Test user methods."""
    
    def test_to_dict(self):
        """Test converting user to dictionary."""
        user = User(
            user_id="user_001",
            username="alice",
            email="alice@example.com",
            system_id="sys_001",
            created_at="2024-01-15T10:30:00Z"
        )
        data = user.to_dict()
        assert data["user_id"] == "user_001"
        assert data["username"] == "alice"
        assert data["email"] == "alice@example.com"
        assert data["system_id"] == "sys_001"
        assert data["created_at"] == "2024-01-15T10:30:00Z"
    
    def test_from_dict(self):
        """Test creating user from dictionary."""
        data = {
            "user_id": "user_002",
            "username": "bob",
            "email": "bob@test.com",
            "system_id": "sys_002",
            "created_at": "2024-01-16T12:00:00Z"
        }
        user = User.from_dict(data)
        assert user.user_id == "user_002"
        assert user.username == "bob"
        assert user.email == "bob@test.com"
        assert user.system_id == "sys_002"
        assert user.created_at == "2024-01-16T12:00:00Z"
    
    def test_from_dict_without_created_at(self):
        """Test creating user from dict without created_at."""
        data = {
            "user_id": "user_003",
            "username": "charlie",
            "email": "charlie@test.com",
            "system_id": "sys_003"
        }
        user = User.from_dict(data)
        assert user.user_id == "user_003"
        assert user.created_at is None


class TestUserComparison:
    """Test user comparison and hashing."""
    
    def test_user_equality(self):
        """Test that users with same user_id are equal."""
        user1 = User("user_001", "alice", "alice@example.com", "sys_001")
        user2 = User("user_001", "alice_different", "different@example.com", "sys_002")
        assert user1 == user2
    
    def test_user_inequality(self):
        """Test that users with different user_id are not equal."""
        user1 = User("user_001", "alice", "alice@example.com", "sys_001")
        user2 = User("user_002", "alice", "alice@example.com", "sys_001")
        assert user1 != user2
    
    def test_user_hash(self):
        """Test that users can be hashed and used in sets."""
        user1 = User("user_001", "alice", "alice@example.com", "sys_001")
        user2 = User("user_001", "alice", "alice@example.com", "sys_001")
        user3 = User("user_002", "bob", "bob@example.com", "sys_002")
        
        user_set = {user1, user2, user3}
        assert len(user_set) == 2  # user1 and user2 are same
    
    def test_user_repr(self):
        """Test user string representation."""
        user = User("user_001", "alice", "alice@example.com", "sys_001")
        repr_str = repr(user)
        assert "user_001" in repr_str
        assert "alice" in repr_str
        assert "sys_001" in repr_str
