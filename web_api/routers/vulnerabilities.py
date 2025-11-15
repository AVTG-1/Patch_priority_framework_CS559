"""
Vulnerabilities Router

Handles vulnerability data from NVD and community vulnerabilities.
"""

import sys
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

# Add base_backend to path for imports
base_backend_path = Path(__file__).parent.parent.parent / "base_backend" / "src"
sys.path.insert(0, str(base_backend_path))

from data_model.nvd_importer import NVDImporter

from database import get_db
from models import User, CommunityVulnerability, VulnerabilityStatus
from auth import get_current_user, get_current_admin_user
from schemas import CommunityVulnerabilityResponse, CommunityVulnerabilityCreate

router = APIRouter(
    prefix="/api/vulnerabilities",
    tags=["vulnerabilities"]
)

# Simple in-memory cache for NVD results (24-hour TTL)
# Structure: {cve_id: {"data": {...}, "timestamp": datetime}}
nvd_cache: Dict[str, Dict[str, Any]] = {}
CACHE_TTL_HOURS = 24

# Initialize NVD Importer (without API key for now)
nvd_importer = NVDImporter()


def get_cached_nvd_data(cve_id: str) -> Optional[Dict[str, Any]]:
    """
    Get NVD data from cache if available and not expired.

    Args:
        cve_id: CVE identifier

    Returns:
        Cached data if available and fresh, None otherwise
    """
    if cve_id not in nvd_cache:
        return None

    cache_entry = nvd_cache[cve_id]
    cache_time = cache_entry["timestamp"]

    # Check if cache is expired (older than 24 hours)
    if datetime.utcnow() - cache_time > timedelta(hours=CACHE_TTL_HOURS):
        # Remove expired entry
        del nvd_cache[cve_id]
        return None

    return cache_entry["data"]


def set_cached_nvd_data(cve_id: str, data: Dict[str, Any]) -> None:
    """
    Store NVD data in cache with current timestamp.

    Args:
        cve_id: CVE identifier
        data: Data to cache
    """
    nvd_cache[cve_id] = {
        "data": data,
        "timestamp": datetime.utcnow()
    }


def vulnerability_to_dict(vuln) -> Dict[str, Any]:
    """
    Convert Vulnerability object to dictionary for API response.

    Args:
        vuln: Vulnerability object from nvd_importer

    Returns:
        Dictionary representation
    """
    return {
        "cve_id": vuln.cve_id,
        "description": vuln.description,
        "cvss_impact": vuln.cvss_impact,
        "cvss_exploitability": vuln.cvss_exploitability,
        "exploit_present": vuln.exploit_present,
        "patch_cost": vuln.patch_cost,
        "subsystem_id": vuln.subsystem_id,
        "dependencies": vuln.dependencies,
        "custom_extras": vuln.custom_extras
    }


def generate_comm_id(db: Session) -> str:
    """
    Generate a unique community vulnerability ID in format COMM-YYYY-NNNN.

    Args:
        db: Database session

    Returns:
        str: Generated community ID (e.g., COMM-2025-0001)
    """
    current_year = datetime.utcnow().year

    # Find the highest number for this year
    prefix = f"COMM-{current_year}-"
    existing = db.query(CommunityVulnerability).filter(
        CommunityVulnerability.comm_id.like(f"{prefix}%")
    ).order_by(CommunityVulnerability.comm_id.desc()).first()

    if existing:
        # Extract the number from the last ID
        last_number = int(existing.comm_id.split("-")[-1])
        new_number = last_number + 1
    else:
        # First vulnerability for this year
        new_number = 1

    # Format as COMM-YYYY-NNNN (4 digits with leading zeros)
    return f"{prefix}{new_number:04d}"


@router.get("/nvd")
async def query_nvd(
    cve_id: str = Query(..., description="CVE identifier (e.g., CVE-2021-44228)", pattern="^CVE-\\d{4}-\\d{4,}$")
):
    """
    Query NVD for CVE details.

    Fetches vulnerability data from the National Vulnerability Database (NVD).
    Results are cached for 24 hours to reduce API calls.

    Args:
        cve_id: CVE identifier (e.g., CVE-2021-44228)

    Returns:
        dict: CVE details including:
            - cve_id: CVE identifier
            - description: Vulnerability description
            - cvss_impact: CVSS impact score
            - cvss_exploitability: CVSS exploitability score
            - exploit_present: Whether known exploits exist
            - patch_cost: Default patch cost
            - subsystem_id: Subsystem identifier
            - custom_extras: Additional metadata (published date, CWE, etc.)
            - cached: Whether this result came from cache
            - cache_timestamp: When this was cached (if cached)

    Raises:
        HTTPException 404: If CVE not found in NVD
        HTTPException 503: If NVD API is unavailable
    """
    # Check cache first
    cached_data = get_cached_nvd_data(cve_id)
    if cached_data:
        return {
            **cached_data,
            "cached": True,
            "cache_timestamp": nvd_cache[cve_id]["timestamp"].isoformat()
        }

    # Fetch from NVD
    try:
        vulnerability = nvd_importer.fetch_cve(cve_id)

        if not vulnerability:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"CVE {cve_id} not found in NVD database"
            )

        # Convert to dictionary
        vuln_dict = vulnerability_to_dict(vulnerability)

        # Cache the result
        set_cached_nvd_data(cve_id, vuln_dict)

        return {
            **vuln_dict,
            "cached": False,
            "cache_timestamp": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to fetch CVE from NVD: {str(e)}"
        )


@router.get("/community", response_model=List[CommunityVulnerabilityResponse])
async def list_community_vulnerabilities(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    status_filter: Optional[str] = Query(None, description="Filter by status (pending, verified, rejected)")
):
    """
    List all community-submitted vulnerabilities.

    Returns a paginated list of vulnerabilities submitted by the community.
    Users can optionally filter by status.

    Args:
        db: Database session
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return (pagination, max 1000)
        status_filter: Optional status filter (pending, verified, rejected)

    Returns:
        List[CommunityVulnerabilityResponse]: List of community vulnerabilities

    Raises:
        HTTPException 400: If invalid status filter provided
    """
    # Validate status filter
    if status_filter and status_filter not in ["pending", "verified", "rejected"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid status filter. Must be one of: pending, verified, rejected"
        )

    # Build query
    query = db.query(CommunityVulnerability)

    # Apply status filter if provided
    if status_filter:
        query = query.filter(CommunityVulnerability.status == status_filter)

    # Order by vote score (upvotes - downvotes), then by creation date (newest first)
    query = query.order_by(
        (CommunityVulnerability.upvotes - CommunityVulnerability.downvotes).desc(),
        CommunityVulnerability.created_at.desc()
    )

    # Apply pagination
    vulnerabilities = query.offset(skip).limit(limit).all()

    # Add reporter username and calculate vote_score for each vulnerability
    for vuln in vulnerabilities:
        if vuln.reporter:
            vuln.reporter_username = vuln.reporter.username
        else:
            vuln.reporter_username = None
        # Add computed vote_score field
        vuln.vote_score = vuln.upvotes - vuln.downvotes

    return vulnerabilities


@router.get("/community/{comm_id}", response_model=CommunityVulnerabilityResponse)
async def get_community_vulnerability(
    comm_id: str,
    db: Session = Depends(get_db)
):
    """
    Get a specific community vulnerability by community ID.

    Args:
        comm_id: Community vulnerability identifier
        db: Database session

    Returns:
        CommunityVulnerabilityResponse: Community vulnerability details

    Raises:
        HTTPException 404: If vulnerability not found
    """
    vulnerability = db.query(CommunityVulnerability).filter(
        CommunityVulnerability.comm_id == comm_id
    ).first()

    if not vulnerability:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Community vulnerability {comm_id} not found"
        )

    # Add reporter username and calculate vote_score
    if vulnerability.reporter:
        vulnerability.reporter_username = vulnerability.reporter.username
    else:
        vulnerability.reporter_username = None
    # Add computed vote_score field
    vulnerability.vote_score = vulnerability.upvotes - vulnerability.downvotes

    return vulnerability


@router.post("/community", response_model=CommunityVulnerabilityResponse, status_code=status.HTTP_201_CREATED)
async def submit_community_vulnerability(
    vuln_data: CommunityVulnerabilityCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submit a new community vulnerability.

    Requires authentication. Automatically generates a unique COMM-YYYY-NNNN ID
    and sets status to UNVERIFIED.

    Args:
        vuln_data: Vulnerability data (description, CVSS scores, etc.)
        current_user: Authenticated user (from JWT token)
        db: Database session

    Returns:
        CommunityVulnerabilityResponse: Created vulnerability with generated ID

    Raises:
        HTTPException 400: If comm_id already exists
        HTTPException 401: If not authenticated
        HTTPException 422: If validation fails
    """
    # Check if comm_id already exists (if provided in vuln_data)
    existing = db.query(CommunityVulnerability).filter(
        CommunityVulnerability.comm_id == vuln_data.comm_id
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Community vulnerability {vuln_data.comm_id} already exists"
        )

    # Generate unique COMM-YYYY-NNNN ID if not provided
    comm_id = vuln_data.comm_id if vuln_data.comm_id else generate_comm_id(db)

    # Create new community vulnerability
    new_vulnerability = CommunityVulnerability(
        comm_id=comm_id,
        reporter_id=current_user.id,
        description=vuln_data.description,
        cvss_impact=vuln_data.cvss_impact,
        cvss_exploitability=vuln_data.cvss_exploitability,
        status=VulnerabilityStatus.UNVERIFIED,
        affected_subsystem_type=vuln_data.affected_subsystem_type,
        exploit_present=vuln_data.exploit_present,
        patch_cost_estimate=vuln_data.patch_cost_estimate,
        upvotes=0,
        downvotes=0
    )

    db.add(new_vulnerability)
    db.commit()
    db.refresh(new_vulnerability)

    # Add reporter username and vote_score
    new_vulnerability.reporter_username = current_user.username
    new_vulnerability.vote_score = 0

    return new_vulnerability


@router.put("/community/{comm_id}/verify", response_model=CommunityVulnerabilityResponse)
async def verify_community_vulnerability(
    comm_id: str,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Verify a community vulnerability (admin only).

    Changes the status from UNVERIFIED to VERIFIED. Only admin users can verify
    vulnerabilities.

    Args:
        comm_id: Community vulnerability identifier
        current_user: Authenticated admin user
        db: Database session

    Returns:
        CommunityVulnerabilityResponse: Updated vulnerability with VERIFIED status

    Raises:
        HTTPException 401: If not authenticated
        HTTPException 403: If user is not admin
        HTTPException 404: If vulnerability not found
    """
    vulnerability = db.query(CommunityVulnerability).filter(
        CommunityVulnerability.comm_id == comm_id
    ).first()

    if not vulnerability:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Community vulnerability {comm_id} not found"
        )

    # Update status to VERIFIED
    vulnerability.status = VulnerabilityStatus.VERIFIED

    db.commit()
    db.refresh(vulnerability)

    # Add reporter username and vote_score
    if vulnerability.reporter:
        vulnerability.reporter_username = vulnerability.reporter.username
    else:
        vulnerability.reporter_username = None
    vulnerability.vote_score = vulnerability.upvotes - vulnerability.downvotes

    return vulnerability


@router.delete("/community/{comm_id}", status_code=status.HTTP_200_OK)
async def deprecate_community_vulnerability(
    comm_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Mark a community vulnerability as DEPRECATED.

    Admin users can deprecate any vulnerability. Regular users can only deprecate
    their own vulnerabilities. The vulnerability is not deleted, just marked as
    DEPRECATED.

    Args:
        comm_id: Community vulnerability identifier
        current_user: Authenticated user
        db: Database session

    Returns:
        dict: Success message

    Raises:
        HTTPException 401: If not authenticated
        HTTPException 403: If user is not admin and not the reporter
        HTTPException 404: If vulnerability not found
    """
    vulnerability = db.query(CommunityVulnerability).filter(
        CommunityVulnerability.comm_id == comm_id
    ).first()

    if not vulnerability:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Community vulnerability {comm_id} not found"
        )

    # Check permissions: admin or reporter
    if not current_user.is_admin and vulnerability.reporter_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins or the reporter can deprecate this vulnerability"
        )

    # Update status to DEPRECATED
    vulnerability.status = VulnerabilityStatus.DEPRECATED

    db.commit()

    return {
        "message": f"Community vulnerability {comm_id} marked as DEPRECATED",
        "comm_id": comm_id,
        "status": "DEPRECATED"
    }


@router.get("/cache/stats")
async def get_cache_stats():
    """
    Get NVD cache statistics (for debugging/monitoring).

    Returns:
        dict: Cache statistics including:
            - total_entries: Total number of cached entries
            - entries: List of cached CVE IDs with timestamps
            - ttl_hours: Cache TTL in hours
    """
    return {
        "total_entries": len(nvd_cache),
        "entries": [
            {
                "cve_id": cve_id,
                "cached_at": entry["timestamp"].isoformat(),
                "age_hours": (datetime.utcnow() - entry["timestamp"]).total_seconds() / 3600
            }
            for cve_id, entry in nvd_cache.items()
        ],
        "ttl_hours": CACHE_TTL_HOURS
    }


@router.delete("/cache")
async def clear_cache(current_user: User = Depends(get_current_user)):
    """
    Clear the NVD cache (requires authentication).

    Clears all cached NVD results. Useful for testing or forcing fresh data.

    Args:
        current_user: Authenticated user

    Returns:
        dict: Success message with number of entries cleared
    """
    entries_cleared = len(nvd_cache)
    nvd_cache.clear()

    return {
        "message": "NVD cache cleared successfully",
        "entries_cleared": entries_cleared
    }
