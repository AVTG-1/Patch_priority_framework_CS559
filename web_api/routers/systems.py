"""
Systems Router

Handles CRUD operations for system configurations.
Users can manage their own system configurations.
Admins can access all systems.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import json

from database import get_db
from models import User, SystemConfig
from auth import get_current_user, get_current_admin_user
from schemas import SystemConfigCreate, SystemConfigResponse

router = APIRouter(
    prefix="/api/systems",
    tags=["systems"]
)


# Helper function to check system ownership or admin
def check_system_access(system: SystemConfig, current_user: User, require_owner: bool = False):
    """
    Check if user has access to a system.

    Args:
        system: SystemConfig to check access for
        current_user: Current authenticated user
        require_owner: If True, only owner can access (for write operations)

    Raises:
        HTTPException 403: If user doesn't have access
        HTTPException 404: If system not found (to hide existence from non-owners)
    """
    # Admin users have access to everything (unless require_owner is True for delete)
    if current_user.is_admin and not require_owner:
        return

    # Check ownership
    if system.user_id != current_user.id:
        # Return 404 instead of 403 to hide existence of systems user doesn't own
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="System configuration not found"
        )


@router.post("", response_model=SystemConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_system(
    system_data: SystemConfigCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new system configuration.

    Requires authentication. System is linked to the authenticated user.

    Args:
        system_data: System configuration data
        current_user: Authenticated user
        db: Database session

    Returns:
        SystemConfigResponse: Created system configuration with ID

    Raises:
        HTTPException 400: If config_json is invalid JSON
        HTTPException 401: If not authenticated
    """
    # Validate that config_json is valid JSON
    try:
        json.loads(system_data.config_json)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="config_json must be valid JSON"
        )

    # Create new system configuration
    new_system = SystemConfig(
        user_id=current_user.id,
        name=system_data.name,
        config_json=system_data.config_json
    )

    db.add(new_system)
    db.commit()
    db.refresh(new_system)

    return new_system


@router.get("", response_model=List[SystemConfigResponse])
async def list_systems(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """
    List all system configurations for the current user.

    Admin users see all systems. Regular users see only their own.

    Args:
        current_user: Authenticated user
        db: Database session
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return (pagination)

    Returns:
        List[SystemConfigResponse]: List of system configurations

    Raises:
        HTTPException 401: If not authenticated
    """
    # Admin users can see all systems
    if current_user.is_admin:
        systems = db.query(SystemConfig).offset(skip).limit(limit).all()
    else:
        # Regular users see only their own systems
        systems = db.query(SystemConfig).filter(
            SystemConfig.user_id == current_user.id
        ).offset(skip).limit(limit).all()

    return systems


@router.get("/{system_id}", response_model=SystemConfigResponse)
async def get_system(
    system_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific system configuration by ID.

    Users can only access their own systems unless they're admin.

    Args:
        system_id: System configuration ID
        current_user: Authenticated user
        db: Database session

    Returns:
        SystemConfigResponse: System configuration

    Raises:
        HTTPException 401: If not authenticated
        HTTPException 404: If system not found or user doesn't have access
    """
    system = db.query(SystemConfig).filter(SystemConfig.id == system_id).first()

    if not system:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="System configuration not found"
        )

    # Check access permissions
    check_system_access(system, current_user)

    return system


@router.put("/{system_id}", response_model=SystemConfigResponse)
async def update_system(
    system_id: int,
    system_data: SystemConfigCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a system configuration.

    Users can only update their own systems unless they're admin.

    Args:
        system_id: System configuration ID
        system_data: Updated system configuration data
        current_user: Authenticated user
        db: Database session

    Returns:
        SystemConfigResponse: Updated system configuration

    Raises:
        HTTPException 400: If config_json is invalid JSON
        HTTPException 401: If not authenticated
        HTTPException 404: If system not found or user doesn't have access
    """
    system = db.query(SystemConfig).filter(SystemConfig.id == system_id).first()

    if not system:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="System configuration not found"
        )

    # Check access permissions
    check_system_access(system, current_user)

    # Validate that config_json is valid JSON
    try:
        json.loads(system_data.config_json)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="config_json must be valid JSON"
        )

    # Update system configuration
    system.name = system_data.name
    system.config_json = system_data.config_json

    db.commit()
    db.refresh(system)

    return system


@router.delete("/{system_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_system(
    system_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a system configuration.

    Only the owner can delete their system. Admin privilege doesn't override ownership.

    Args:
        system_id: System configuration ID
        current_user: Authenticated user
        db: Database session

    Returns:
        None (204 No Content)

    Raises:
        HTTPException 401: If not authenticated
        HTTPException 404: If system not found or user doesn't own it
    """
    system = db.query(SystemConfig).filter(SystemConfig.id == system_id).first()

    if not system:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="System configuration not found"
        )

    # For delete, require ownership (even admins can't delete others' systems)
    check_system_access(system, current_user, require_owner=True)

    # Delete the system
    db.delete(system)
    db.commit()

    return None
