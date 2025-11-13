"""
Admin Router

Admin-only endpoints for user management and platform statistics.
"""

from typing import List, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import get_db
from models import User, SystemConfig, SimulationRun, CommunityVulnerability
from auth import get_current_admin_user
from schemas import UserResponse, AdminStatsResponse, UserListResponse

router = APIRouter(
    prefix="/api/admin",
    tags=["admin"]
)


@router.get("/users", response_model=List[UserListResponse])
async def list_all_users(
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return")
):
    """
    List all users in the system (admin only).

    Returns a paginated list of all users with their details including
    system count, simulation count, and vulnerability contribution count.

    Args:
        current_admin: Current authenticated admin user
        db: Database session
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return (pagination, max 1000)

    Returns:
        List[UserListResponse]: List of users with metadata

    Raises:
        HTTPException 401: If not authenticated
        HTTPException 403: If user is not admin
    """
    # Query users with additional counts
    query = db.query(User).order_by(User.created_at.desc())

    # Apply pagination
    users = query.offset(skip).limit(limit).all()

    # Enrich user data with counts
    user_list = []
    for user in users:
        # Count user's systems
        system_count = db.query(SystemConfig).filter(
            SystemConfig.user_id == user.id
        ).count()

        # Count user's simulations (via their systems)
        simulation_count = db.query(SimulationRun).join(SystemConfig).filter(
            SystemConfig.user_id == user.id
        ).count()

        # Count user's community vulnerability submissions
        vulnerability_count = db.query(CommunityVulnerability).filter(
            CommunityVulnerability.reporter_id == user.id
        ).count()

        user_list.append({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_admin": user.is_admin,
            "created_at": user.created_at,
            "system_count": system_count,
            "simulation_count": simulation_count,
            "vulnerability_count": vulnerability_count
        })

    return user_list


@router.put("/users/{user_id}/admin", response_model=UserResponse)
async def toggle_admin_status(
    user_id: int,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Toggle admin status for a user (admin only).

    Promotes a regular user to admin or demotes an admin to regular user.
    Admins cannot demote themselves to prevent accidental lockout.

    Args:
        user_id: ID of user to modify
        current_admin: Current authenticated admin user
        db: Database session

    Returns:
        UserResponse: Updated user with new admin status

    Raises:
        HTTPException 401: If not authenticated
        HTTPException 403: If user is not admin or trying to demote themselves
        HTTPException 404: If user not found
    """
    # Get target user
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )

    # Prevent self-demotion
    if user.id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot modify your own admin status"
        )

    # Toggle admin status
    user.is_admin = not user.is_admin

    db.commit()
    db.refresh(user)

    return user


@router.get("/stats", response_model=AdminStatsResponse)
async def get_platform_statistics(
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get platform-wide statistics (admin only).

    Returns comprehensive statistics about the platform including:
    - Total counts for users, systems, simulations, and vulnerabilities
    - Recent activity summary (last 7 days and last 30 days)
    - User distribution (admin vs regular)
    - Vulnerability status distribution

    Args:
        current_admin: Current authenticated admin user
        db: Database session

    Returns:
        AdminStatsResponse: Platform statistics

    Raises:
        HTTPException 401: If not authenticated
        HTTPException 403: If user is not admin
    """
    # Calculate date thresholds
    now = datetime.utcnow()
    last_7_days = now - timedelta(days=7)
    last_30_days = now - timedelta(days=30)

    # Total counts
    total_users = db.query(User).count()
    total_systems = db.query(SystemConfig).count()
    total_simulations = db.query(SimulationRun).count()
    total_vulnerabilities = db.query(CommunityVulnerability).count()

    # User statistics
    admin_users = db.query(User).filter(User.is_admin == True).count()
    regular_users = total_users - admin_users

    # Recent activity - users
    new_users_7d = db.query(User).filter(User.created_at >= last_7_days).count()
    new_users_30d = db.query(User).filter(User.created_at >= last_30_days).count()

    # Recent activity - systems
    new_systems_7d = db.query(SystemConfig).filter(
        SystemConfig.created_at >= last_7_days
    ).count()
    new_systems_30d = db.query(SystemConfig).filter(
        SystemConfig.created_at >= last_30_days
    ).count()

    # Recent activity - simulations
    new_simulations_7d = db.query(SimulationRun).filter(
        SimulationRun.created_at >= last_7_days
    ).count()
    new_simulations_30d = db.query(SimulationRun).filter(
        SimulationRun.created_at >= last_30_days
    ).count()

    # Recent activity - vulnerabilities
    new_vulnerabilities_7d = db.query(CommunityVulnerability).filter(
        CommunityVulnerability.created_at >= last_7_days
    ).count()
    new_vulnerabilities_30d = db.query(CommunityVulnerability).filter(
        CommunityVulnerability.created_at >= last_30_days
    ).count()

    # Vulnerability status distribution
    from models import VulnerabilityStatus

    unverified_vulns = db.query(CommunityVulnerability).filter(
        CommunityVulnerability.status == VulnerabilityStatus.UNVERIFIED
    ).count()

    verified_vulns = db.query(CommunityVulnerability).filter(
        CommunityVulnerability.status == VulnerabilityStatus.VERIFIED
    ).count()

    deprecated_vulns = db.query(CommunityVulnerability).filter(
        CommunityVulnerability.status == VulnerabilityStatus.DEPRECATED
    ).count()

    # Most active users (by simulation count)
    most_active_users = db.query(
        User.id,
        User.username,
        func.count(SimulationRun.id).label('simulation_count')
    ).join(
        SystemConfig, User.id == SystemConfig.user_id
    ).join(
        SimulationRun, SystemConfig.id == SimulationRun.system_config_id
    ).group_by(
        User.id, User.username
    ).order_by(
        func.count(SimulationRun.id).desc()
    ).limit(5).all()

    # Top vulnerability contributors
    top_contributors = db.query(
        User.id,
        User.username,
        func.count(CommunityVulnerability.id).label('contribution_count')
    ).join(
        CommunityVulnerability, User.id == CommunityVulnerability.reporter_id
    ).group_by(
        User.id, User.username
    ).order_by(
        func.count(CommunityVulnerability.id).desc()
    ).limit(5).all()

    return {
        "timestamp": now,
        "total_counts": {
            "users": total_users,
            "systems": total_systems,
            "simulations": total_simulations,
            "vulnerabilities": total_vulnerabilities
        },
        "user_distribution": {
            "admin_users": admin_users,
            "regular_users": regular_users
        },
        "vulnerability_status": {
            "unverified": unverified_vulns,
            "verified": verified_vulns,
            "deprecated": deprecated_vulns
        },
        "recent_activity_7d": {
            "new_users": new_users_7d,
            "new_systems": new_systems_7d,
            "new_simulations": new_simulations_7d,
            "new_vulnerabilities": new_vulnerabilities_7d
        },
        "recent_activity_30d": {
            "new_users": new_users_30d,
            "new_systems": new_systems_30d,
            "new_simulations": new_simulations_30d,
            "new_vulnerabilities": new_vulnerabilities_30d
        },
        "most_active_users": [
            {"user_id": user.id, "username": user.username, "simulation_count": user.simulation_count}
            for user in most_active_users
        ],
        "top_contributors": [
            {"user_id": user.id, "username": user.username, "contribution_count": user.contribution_count}
            for user in top_contributors
        ]
    }
