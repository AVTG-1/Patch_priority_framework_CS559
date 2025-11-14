"""
Simulations Router

Handles running and managing game-theoretic patch prioritization simulations.
"""

import sys
import json
import tempfile
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session

# Add base_backend to path for imports
base_backend_path = Path(__file__).parent.parent.parent / "base_backend" / "src"
sys.path.insert(0, str(base_backend_path))

from data_model import PlayerBase

from database import get_db
from models import User, SystemConfig, SimulationRun
from auth import get_current_user
from schemas import (
    SimulationRunCreate,
    SimulationRunResponse,
    SimulationSummary,
    SimulationDetailResponse
)
from backend_bridge import load_system_from_config, run_simulation

router = APIRouter(
    prefix="/api/simulations",
    tags=["simulations"]
)


def run_simulation_task(
    simulation_id: int,
    config_path: str,
    rounds: int,
    defender_budget: Optional[float],
    attacker_budget: Optional[float],
    patch_grouping_method: str,
    db_connection_string: str
):
    """
    Background task to run simulation and store results.

    This runs asynchronously to avoid blocking the API response.

    Args:
        simulation_id: ID of the simulation run in database
        config_path: Path to temporary config file
        rounds: Number of simulation rounds
        defender_budget: Defender resource budget (optional)
        attacker_budget: Attacker resource budget (optional)
        patch_grouping_method: Patch grouping strategy
        db_connection_string: Database connection string
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    # Create new database session for background task
    engine = create_engine(db_connection_string)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        # Load system from config
        system = load_system_from_config(config_path)

        # Create player objects if budgets provided
        players = None
        if defender_budget is not None or attacker_budget is not None:
            players = []
            if defender_budget is not None:
                defender = PlayerBase.create_defender(
                    player_id="defender_1",
                    resource_budget=defender_budget
                )
                players.append(defender)

            if attacker_budget is not None:
                attacker = PlayerBase.create_attacker(
                    player_id="attacker_1",
                    resource_budget=attacker_budget
                )
                players.append(attacker)

        # Run simulation
        results = run_simulation(
            system_instance=system,
            rounds=rounds,
            players=players,
            patch_grouping_method=patch_grouping_method
        )

        # Update simulation run with results
        simulation = db.query(SimulationRun).filter(SimulationRun.id == simulation_id).first()
        if simulation:
            simulation.results_json = json.dumps(results)
            db.commit()

    except Exception as e:
        # Store error in results
        simulation = db.query(SimulationRun).filter(SimulationRun.id == simulation_id).first()
        if simulation:
            error_results = {
                "error": True,
                "error_message": str(e),
                "error_type": type(e).__name__
            }
            simulation.results_json = json.dumps(error_results)
            db.commit()
    finally:
        db.close()
        # Clean up temporary file
        try:
            Path(config_path).unlink()
        except:
            pass


@router.post("", response_model=SimulationSummary, status_code=status.HTTP_201_CREATED)
async def run_new_simulation(
    simulation_data: SimulationRunCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Run a new simulation on a system configuration.

    Creates a simulation run and executes it in the background. The simulation
    uses game-theoretic analysis to determine optimal patch prioritization.

    Args:
        simulation_data: Simulation parameters including:
            - system_id: System configuration to simulate
            - rounds: Number of simulation rounds (default: 10)
            - defender_budget: Optional defender resource budget
            - attacker_budget: Optional attacker resource budget
            - patch_grouping_method: Patch grouping strategy (default: "dependencies")
        background_tasks: FastAPI background tasks
        current_user: Authenticated user (from JWT)
        db: Database session

    Returns:
        SimulationSummary: Simulation ID and initial summary (full results available after completion)

    Raises:
        HTTPException 401: If not authenticated
        HTTPException 403: If user doesn't own the system
        HTTPException 404: If system not found
        HTTPException 422: If validation fails
    """
    # Get system configuration
    system_config = db.query(SystemConfig).filter(
        SystemConfig.id == simulation_data.system_id
    ).first()

    if not system_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"System configuration {simulation_data.system_id} not found"
        )

    # Check permissions (user must own system or be admin)
    if system_config.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to simulate this system"
        )

    # Parse system configuration JSON
    try:
        config_dict = json.loads(system_config.config_json)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid system configuration JSON"
        )

    # Create parameters dictionary
    parameters = {
        "rounds": simulation_data.rounds,
        "defender_budget": simulation_data.defender_budget,
        "attacker_budget": simulation_data.attacker_budget,
        "patch_grouping_method": simulation_data.patch_grouping_method
    }

    # Create simulation run record with pending results
    pending_results = {
        "status": "pending",
        "message": "Simulation is running in background"
    }

    new_simulation = SimulationRun(
        system_config_id=system_config.id,
        parameters_json=json.dumps(parameters),
        results_json=json.dumps(pending_results)
    )

    db.add(new_simulation)
    db.commit()
    db.refresh(new_simulation)

    # Transform config_dict to match ConfigLoader schema
    config_dict['system_name'] = simulation_data.system_name

    # Handle subsystems - ensure proper structure
    subsystems_list = config_dict.get('subsystems', [])
    dependencies_dict = config_dict.get('dependencies', {})

    # If no subsystems defined, create default
    if not subsystems_list:
        subsystems_list = [
            {
                'id': 'main',
                'name': simulation_data.system_name,
            }
        ]
        default_subsystem_id = 'main'
    else:
        # Transform subsystems to include id field and dependencies
        transformed_subsystems = []
        for subsystem in subsystems_list:
            subsys_name = subsystem.get('name', 'subsystem')
            subsys_id = subsystem.get('id', subsys_name.lower().replace(' ', '_'))

            # Get functional dependencies for this subsystem
            subsys_deps = dependencies_dict.get(subsys_name, [])

            transformed_subsystems.append({
                'id': subsys_id,
                'name': subsys_name,
                'functional_dependencies': subsys_deps
            })

        subsystems_list = transformed_subsystems
        default_subsystem_id = subsystems_list[0]['id'] if subsystems_list else 'main'

    config_dict['subsystems'] = subsystems_list

    # Transform vulnerabilities to ConfigLoader format
    vulnerabilities_list = config_dict.get('vulnerabilities', [])
    transformed_vulns = []

    for i, vuln in enumerate(vulnerabilities_list):
        # Convert frontend vuln_id to backend cve_id
        cve_id = vuln.get('vuln_id', vuln.get('cve_id', f'CUSTOM-{i}'))

        # Ensure cve_id matches required pattern: ^(CVE-|CUSTOM-)
        if not cve_id.startswith('CVE-') and not cve_id.startswith('CUSTOM-'):
            cve_id = f'CUSTOM-{cve_id}'

        # Get or calculate CVSS scores
        cvss_score = vuln.get('cvss_score', 5.0)
        cvss_impact = vuln.get('cvss_impact', cvss_score * 0.6)
        cvss_exploitability = vuln.get('cvss_exploitability', cvss_score * 0.4)

        # Determine which subsystem this vulnerability belongs to
        affected_component = vuln.get('affected_component', '')
        subsystem_id = default_subsystem_id

        # Try to match vulnerability to subsystem by component name
        for subsys in subsystems_list:
            if subsys['name'].lower() in affected_component.lower():
                subsystem_id = subsys['id']
                break

        transformed_vulns.append({
            'cve_id': cve_id,
            'subsystem_id': subsystem_id,
            'cvss_impact': float(cvss_impact),
            'cvss_exploitability': float(cvss_exploitability),
            'patch_cost': vuln.get('patch_cost', 1.0),
            'description': vuln.get('description', ''),
            'exploit_present': vuln.get('exploit_present', False),
            'dependencies': vuln.get('dependencies', []),
            'source': 'CUSTOM'
        })

    config_dict['vulnerabilities'] = transformed_vulns

    # Write config to temporary file for background task
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_dict, f)
        temp_config_path = f.name

    # Get database connection string from database URL
    from database import SQLALCHEMY_DATABASE_URL

    # Add background task to run simulation
    background_tasks.add_task(
        run_simulation_task,
        simulation_id=new_simulation.id,
        config_path=temp_config_path,
        rounds=simulation_data.rounds,
        defender_budget=simulation_data.defender_budget,
        attacker_budget=simulation_data.attacker_budget,
        patch_grouping_method=simulation_data.patch_grouping_method,
        db_connection_string=SQLALCHEMY_DATABASE_URL
    )

    # Return simulation summary (results will be populated by background task)
    return SimulationSummary(
        simulation_id=new_simulation.id,
        system_id=system_config.id,
        system_name=simulation_data.system_name,
        rounds=simulation_data.rounds,
        initial_ris=0.0,  # Will be updated by background task
        final_ris=0.0,  # Will be updated by background task
        ris_reduction=0.0,  # Will be updated by background task
        ris_reduction_percentage=0.0,  # Will be updated by background task
        total_vulnerabilities_patched=0,  # Will be updated by background task
        patch_priority_list=[],  # Will be updated by background task
        created_at=new_simulation.created_at
    )


@router.get("/{simulation_id}", response_model=SimulationDetailResponse)
async def get_simulation_results(
    simulation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed results for a specific simulation.

    Returns complete simulation results including patch priorities, RIS trajectory,
    Nash equilibrium analysis, and per-round details.

    Args:
        simulation_id: Simulation run ID
        current_user: Authenticated user (from JWT)
        db: Database session

    Returns:
        SimulationDetailResponse: Complete simulation results

    Raises:
        HTTPException 401: If not authenticated
        HTTPException 403: If user doesn't own the system
        HTTPException 404: If simulation not found
    """
    # Get simulation run
    simulation = db.query(SimulationRun).filter(
        SimulationRun.id == simulation_id
    ).first()

    if not simulation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Simulation {simulation_id} not found"
        )

    # Check permissions (user must own system or be admin)
    if simulation.system_config.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view this simulation"
        )

    # Parse JSON fields
    try:
        parameters = json.loads(simulation.parameters_json)
        results = json.loads(simulation.results_json)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to parse simulation data"
        )

    # Get system name from config
    try:
        config_dict = json.loads(simulation.system_config.config_json)
        system_name = config_dict.get("system_name", "Unknown")
    except:
        system_name = "Unknown"

    return SimulationDetailResponse(
        id=simulation.id,
        system_config_id=simulation.system_config_id,
        system_name=system_name,
        parameters=parameters,
        results=results,
        created_at=simulation.created_at
    )


@router.get("", response_model=List[SimulationRunResponse])
async def list_simulations(
    system_id: Optional[int] = Query(None, description="Filter by system configuration ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return")
):
    """
    List simulations for the current user.

    Optionally filter by system configuration ID. Results are ordered by
    creation date (newest first).

    Args:
        system_id: Optional system configuration ID to filter by
        current_user: Authenticated user (from JWT)
        db: Database session
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return (pagination, max 1000)

    Returns:
        List[SimulationRunResponse]: List of simulations

    Raises:
        HTTPException 401: If not authenticated
        HTTPException 403: If user doesn't own the specified system
        HTTPException 404: If specified system not found
    """
    # Build query
    query = db.query(SimulationRun).join(SystemConfig)

    # Filter by system_id if provided
    if system_id is not None:
        # Verify system exists and user has permission
        system_config = db.query(SystemConfig).filter(
            SystemConfig.id == system_id
        ).first()

        if not system_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"System configuration {system_id} not found"
            )

        if system_config.user_id != current_user.id and not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to view simulations for this system"
            )

        query = query.filter(SimulationRun.system_config_id == system_id)
    else:
        # Show only user's simulations (unless admin)
        if not current_user.is_admin:
            query = query.filter(SystemConfig.user_id == current_user.id)

    # Order by creation date (newest first)
    query = query.order_by(SimulationRun.created_at.desc())

    # Apply pagination
    simulations = query.offset(skip).limit(limit).all()

    return simulations
