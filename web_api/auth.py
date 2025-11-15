"""
Authentication Module

Provides JWT token generation/validation and password hashing utilities.
Implements OAuth2 with Password (and hashing), Bearer with JWT tokens.
"""

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from config import settings
from database import get_db
from models import User

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


# Password hashing utilities
def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        str: Hashed password
    """
    # Encode password to bytes
    password_bytes = password.encode('utf-8')
    # Generate salt and hash
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    # Return as string
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to verify against

    Returns:
        bool: True if password matches, False otherwise
    """
    # Encode to bytes
    password_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    # Verify
    return bcrypt.checkpw(password_bytes, hashed_bytes)


# JWT token utilities
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: Dictionary of data to encode in the token (e.g., {"sub": username})
        expires_delta: Optional custom expiration time

    Returns:
        str: Encoded JWT token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)

    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """
    Verify and decode a JWT token.

    Args:
        token: JWT token to verify

    Returns:
        Optional[dict]: Decoded token payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except JWTError:
        return None


# User authentication
def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """
    Authenticate a user by username and password.

    Args:
        db: Database session
        username: Username to authenticate
        password: Plain text password

    Returns:
        Optional[User]: User object if authenticated, None otherwise
    """
    user = db.query(User).filter(User.username == username).first()

    if not user:
        return None

    if not verify_password(password, user.hashed_password):
        return None

    return user


# Dependencies for protected routes
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get the current authenticated user from JWT token.

    Args:
        token: JWT token from Authorization header
        db: Database session

    Returns:
        User: Current authenticated user

    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = verify_token(token)

    if payload is None:
        raise credentials_exception

    username: str = payload.get("sub")

    if username is None:
        raise credentials_exception

    user = db.query(User).filter(User.username == username).first()

    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to get the current active user.

    Can be extended to check if user is active/disabled.

    Args:
        current_user: User from get_current_user dependency

    Returns:
        User: Current active user

    Raises:
        HTTPException: If user is inactive (not implemented yet)
    """
    # Future: Add user.is_active check here if needed
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to require admin privileges.

    Args:
        current_user: User from get_current_user dependency

    Returns:
        User: Current admin user

    Raises:
        HTTPException: If user is not an admin
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Admin access required."
        )

    return current_user


# Token response model helper
def create_token_response(user: User) -> dict:
    """
    Create a standardized token response.

    Args:
        user: User object to create token for

    Returns:
        dict: Token response with access_token and token_type
    """
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60,  # seconds
        "user": user.to_dict()
    }
