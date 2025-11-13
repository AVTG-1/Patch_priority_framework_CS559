"""
Tests for UserManager
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

import pytest
from collaboration.user import User
from collaboration.user_manager import UserManager


class TestUserManagerBasic:
    """Test basic CRUD operations."""
    
    def test_create_empty_manager(self):
        """Test creating an empty manager."""
        manager = UserManager()
        assert manager.count() == 0
        assert manager.list_all() == []
    
    def test_create_user(self):
        """Test creating a user."""
        manager = UserManager()
        user = User(
            user_id="user_001",
            username="alice",
            email="alice@example.com",
            system_id="sys_001"
        )
        
        result = manager.create_user(user)
        assert result == user
        assert manager.count() == 1
    
    def test_create_duplicate_user_id_raises_error(self):
        """Test that duplicate user_id raises ValueError."""
        manager = UserManager()
        user1 = User("user_001", "alice", "alice@example.com", "sys_001")
        user2 = User("user_001", "bob", "bob@example.com", "sys_002")
        
        manager.create_user(user1)
        with pytest.raises(ValueError, match="already exists"):
            manager.create_user(user2)
    
    def test_create_duplicate_username_raises_error(self):
        """Test that duplicate username raises ValueError."""
        manager = UserManager()
        user1 = User("user_001", "alice", "alice@example.com", "sys_001")
        user2 = User("user_002", "alice", "alice2@example.com", "sys_002")
        
        manager.create_user(user1)
        with pytest.raises(ValueError, match="already taken"):
            manager.create_user(user2)
    
    def test_create_duplicate_email_raises_error(self):
        """Test that duplicate email raises ValueError."""
        manager = UserManager()
        user1 = User("user_001", "alice", "alice@example.com", "sys_001")
        user2 = User("user_002", "bob", "alice@example.com", "sys_002")
        
        manager.create_user(user1)
        with pytest.raises(ValueError, match="already registered"):
            manager.create_user(user2)
    
    def test_create_duplicate_system_raises_error(self):
        """Test that duplicate system_id raises ValueError (one-to-one constraint)."""
        manager = UserManager()
        user1 = User("user_001", "alice", "alice@example.com", "sys_001")
        user2 = User("user_002", "bob", "bob@example.com", "sys_001")
        
        manager.create_user(user1)
        with pytest.raises(ValueError, match="already owned"):
            manager.create_user(user2)
    
    def test_get_user(self):
        """Test getting a user by ID."""
        manager = UserManager()
        user = User("user_001", "alice", "alice@example.com", "sys_001")
        manager.create_user(user)
        
        result = manager.get("user_001")
        assert result == user
    
    def test_get_nonexistent_returns_none(self):
        """Test that getting nonexistent user returns None."""
        manager = UserManager()
        assert manager.get("user_999") is None
    
    def test_get_by_username(self):
        """Test getting user by username."""
        manager = UserManager()
        user = User("user_001", "alice", "alice@example.com", "sys_001")
        manager.create_user(user)
        
        result = manager.get_by_username("alice")
        assert result == user
    
    def test_get_by_username_nonexistent_returns_none(self):
        """Test that getting by nonexistent username returns None."""
        manager = UserManager()
        assert manager.get_by_username("nonexistent") is None
    
    def test_get_by_email(self):
        """Test getting user by email."""
        manager = UserManager()
        user = User("user_001", "alice", "alice@example.com", "sys_001")
        manager.create_user(user)
        
        result = manager.get_by_email("alice@example.com")
        assert result == user
    
    def test_get_by_email_nonexistent_returns_none(self):
        """Test that getting by nonexistent email returns None."""
        manager = UserManager()
        assert manager.get_by_email("nonexistent@example.com") is None
    
    def test_get_by_system(self):
        """Test getting user by system ID."""
        manager = UserManager()
        user = User("user_001", "alice", "alice@example.com", "sys_001")
        manager.create_user(user)
        
        result = manager.get_by_system("sys_001")
        assert result == user
    
    def test_get_by_system_nonexistent_returns_none(self):
        """Test that getting by nonexistent system returns None."""
        manager = UserManager()
        assert manager.get_by_system("sys_999") is None
    
    def test_delete_user(self):
        """Test deleting a user."""
        manager = UserManager()
        user = User("user_001", "alice", "alice@example.com", "sys_001")
        manager.create_user(user)
        
        result = manager.delete("user_001")
        assert result is True
        assert manager.count() == 0
        assert manager.get("user_001") is None
        assert manager.get_by_username("alice") is None
        assert manager.get_by_email("alice@example.com") is None
        assert manager.get_by_system("sys_001") is None
    
    def test_delete_nonexistent_returns_false(self):
        """Test that deleting nonexistent user returns False."""
        manager = UserManager()
        result = manager.delete("user_999")
        assert result is False
    
    def test_list_all(self):
        """Test listing all users."""
        manager = UserManager()
        user1 = User("user_001", "alice", "alice@example.com", "sys_001")
        user2 = User("user_002", "bob", "bob@example.com", "sys_002")
        
        manager.create_user(user1)
        manager.create_user(user2)
        
        all_users = manager.list_all()
        assert len(all_users) == 2
        assert user1 in all_users
        assert user2 in all_users
    
    def test_clear(self):
        """Test clearing all users."""
        manager = UserManager()
        user = User("user_001", "alice", "alice@example.com", "sys_001")
        manager.create_user(user)
        
        manager.clear()
        assert manager.count() == 0


class TestUserManagerUpdate:
    """Test update functionality."""
    
    def test_update_user(self):
        """Test updating a user."""
        manager = UserManager()
        user = User("user_001", "alice", "alice@example.com", "sys_001")
        manager.create_user(user)
        
        # Modify user
        user.username = "alice_new"
        user.email = "alice_new@example.com"
        user.system_id = "sys_002"
        
        result = manager.update(user)
        assert result == user
        assert manager.get_by_username("alice_new") == user
        assert manager.get_by_email("alice_new@example.com") == user
        assert manager.get_by_system("sys_002") == user
        
        # Old values should not work
        assert manager.get_by_username("alice") is None
        assert manager.get_by_email("alice@example.com") is None
        assert manager.get_by_system("sys_001") is None
    
    def test_update_nonexistent_raises_error(self):
        """Test that updating nonexistent user raises ValueError."""
        manager = UserManager()
        user = User("user_999", "bob", "bob@example.com", "sys_999")
        
        with pytest.raises(ValueError, match="not found"):
            manager.update(user)
    
    def test_update_username_conflict_raises_error(self):
        """Test that updating to existing username raises ValueError."""
        manager = UserManager()
        user1 = User("user_001", "alice", "alice@example.com", "sys_001")
        user2 = User("user_002", "bob", "bob@example.com", "sys_002")
        
        manager.create_user(user1)
        manager.create_user(user2)
        
        user1.username = "bob"  # Try to take bob's username
        with pytest.raises(ValueError, match="already taken"):
            manager.update(user1)
    
    def test_update_email_conflict_raises_error(self):
        """Test that updating to existing email raises ValueError."""
        manager = UserManager()
        user1 = User("user_001", "alice", "alice@example.com", "sys_001")
        user2 = User("user_002", "bob", "bob@example.com", "sys_002")
        
        manager.create_user(user1)
        manager.create_user(user2)
        
        user1.email = "bob@example.com"  # Try to take bob's email
        with pytest.raises(ValueError, match="already registered"):
            manager.update(user1)
    
    def test_update_system_conflict_raises_error(self):
        """Test that updating to existing system raises ValueError."""
        manager = UserManager()
        user1 = User("user_001", "alice", "alice@example.com", "sys_001")
        user2 = User("user_002", "bob", "bob@example.com", "sys_002")
        
        manager.create_user(user1)
        manager.create_user(user2)
        
        user1.system_id = "sys_002"  # Try to take bob's system
        with pytest.raises(ValueError, match="already owned"):
            manager.update(user1)
    
    def test_update_same_username_allowed(self):
        """Test that updating with same username is allowed."""
        manager = UserManager()
        user = User("user_001", "alice", "alice@example.com", "sys_001")
        manager.create_user(user)
        
        # Update email but keep username
        user.email = "alice_new@example.com"
        result = manager.update(user)
        assert result.username == "alice"
        assert result.email == "alice_new@example.com"


class TestUserManagerChecks:
    """Test existence check methods."""
    
    def test_username_exists(self):
        """Test checking if username exists."""
        manager = UserManager()
        user = User("user_001", "alice", "alice@example.com", "sys_001")
        manager.create_user(user)
        
        assert manager.username_exists("alice") is True
        assert manager.username_exists("bob") is False
    
    def test_email_exists(self):
        """Test checking if email exists."""
        manager = UserManager()
        user = User("user_001", "alice", "alice@example.com", "sys_001")
        manager.create_user(user)
        
        assert manager.email_exists("alice@example.com") is True
        assert manager.email_exists("bob@example.com") is False
    
    def test_system_has_owner(self):
        """Test checking if system has owner."""
        manager = UserManager()
        user = User("user_001", "alice", "alice@example.com", "sys_001")
        manager.create_user(user)
        
        assert manager.system_has_owner("sys_001") is True
        assert manager.system_has_owner("sys_002") is False


class TestUserManagerSearch:
    """Test search functionality."""
    
    def setup_method(self):
        """Set up manager with sample users."""
        self.manager = UserManager()
        
        self.manager.create_user(User(
            "user_001", "alice_smith", "alice@example.com", "sys_001"
        ))
        self.manager.create_user(User(
            "user_002", "bob_jones", "bob@example.com", "sys_002"
        ))
        self.manager.create_user(User(
            "user_003", "alice_brown", "alice2@example.com", "sys_003"
        ))
        self.manager.create_user(User(
            "user_004", "charlie", "charlie@example.com", "sys_004"
        ))
    
    def test_search_users_by_pattern(self):
        """Test searching users by username pattern."""
        results = self.manager.search_users(username_pattern="alice")
        assert len(results) == 2
        assert all("alice" in u.username.lower() for u in results)
    
    def test_search_users_case_insensitive(self):
        """Test that search is case-insensitive."""
        results = self.manager.search_users(username_pattern="ALICE")
        assert len(results) == 2
    
    def test_search_users_no_pattern_returns_all(self):
        """Test that search without pattern returns all users."""
        results = self.manager.search_users()
        assert len(results) == 4
    
    def test_search_users_no_match(self):
        """Test search with no matching pattern."""
        results = self.manager.search_users(username_pattern="xyz")
        assert len(results) == 0


class TestUserManagerIntegration:
    """Test integration scenarios."""
    
    def test_user_lifecycle(self):
        """Test complete user lifecycle: create, read, update, delete."""
        manager = UserManager()
        
        # Create
        user = User("user_001", "alice", "alice@example.com", "sys_001")
        manager.create_user(user)
        assert manager.count() == 1
        
        # Read
        retrieved = manager.get("user_001")
        assert retrieved.username == "alice"
        
        # Update
        user.email = "alice_new@example.com"
        manager.update(user)
        updated = manager.get("user_001")
        assert updated.email == "alice_new@example.com"
        
        # Delete
        manager.delete("user_001")
        assert manager.count() == 0
    
    def test_one_to_one_system_constraint(self):
        """Test that one-to-one constraint is enforced throughout."""
        manager = UserManager()
        
        # Create first user with system
        user1 = User("user_001", "alice", "alice@example.com", "sys_001")
        manager.create_user(user1)
        
        # Cannot create another user with same system
        user2 = User("user_002", "bob", "bob@example.com", "sys_001")
        with pytest.raises(ValueError, match="already owned"):
            manager.create_user(user2)
        
        # Create user2 with different system
        user2 = User("user_002", "bob", "bob@example.com", "sys_002")
        manager.create_user(user2)
        
        # Cannot update user2 to use user1's system
        user2.system_id = "sys_001"
        with pytest.raises(ValueError, match="already owned"):
            manager.update(user2)
        
        # After deleting user1, system becomes available
        manager.delete("user_001")
        user2.system_id = "sys_001"
        manager.update(user2)
        assert manager.get_by_system("sys_001") == user2
    
    def test_multiple_users_different_systems(self):
        """Test managing multiple users with different systems."""
        manager = UserManager()
        
        users = [
            User(f"user_{i:03d}", f"user{i}", f"user{i}@example.com", f"sys_{i:03d}")
            for i in range(10)
        ]
        
        for user in users:
            manager.create_user(user)
        
        assert manager.count() == 10
        
        # Verify all systems are properly mapped
        for i in range(10):
            owner = manager.get_by_system(f"sys_{i:03d}")
            assert owner.user_id == f"user_{i:03d}"
