"""
FastAPI Web API for Patch Priority Framework
Main application entry point
"""
from pathlib import Path
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import uvicorn

# Import backend bridge
from backend_bridge import run_simulation_from_config

# Import database and models
from database import get_db, init_db
from models import User

# Import authentication
from auth import (
    hash_password,
    authenticate_user,
    create_token_response,
    get_current_user,
    get_current_active_user
)

# Import schemas
from schemas import (
    UserCreate,
    UserResponse,
    Token,
    MessageResponse,
    ErrorResponse
)

# Create FastAPI application instance
app = FastAPI(
    title="Patch Priority Framework API",
    description="Game-theoretic patch prioritization system for cybersecurity vulnerability management",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Startup event to initialize database
@app.on_event("startup")
async def startup_event():
    """Initialize database on application startup"""
    init_db()
    print("Database initialized")


@app.get("/health")
async def health_check():
    """
    Health check endpoint to verify API is running
    Returns:
        dict: Status information
    """
    return {
        "status": "healthy",
        "service": "Patch Priority Framework API",
        "version": "1.0.0"
    }


@app.get("/")
async def root():
    """
    Root endpoint with API information
    Returns:
        dict: Welcome message and API details
    """
    return {
        "message": "Welcome to Patch Priority Framework API",
        "docs": "/docs",
        "health": "/health"
    }


# ============================================================================
# Authentication Endpoints
# ============================================================================

@app.post("/api/auth/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user.

    Creates a new user account with hashed password.

    Args:
        user_data: User registration data (username, email, password)
        db: Database session

    Returns:
        Token: JWT access token and user information

    Raises:
        HTTPException 400: If username or email already exists
        HTTPException 422: If validation fails
    """
    # Check if username already exists
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    # Check if email already exists
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create new user with hashed password
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        is_admin=False
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Return token response
    return create_token_response(new_user)


@app.post("/api/auth/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Login and receive JWT access token.

    Authenticates user with username and password using OAuth2 password flow.

    Args:
        form_data: OAuth2 form data (username, password)
        db: Database session

    Returns:
        Token: JWT access token and user information

    Raises:
        HTTPException 401: If credentials are invalid
    """
    user = authenticate_user(db, form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return create_token_response(user)


@app.get("/api/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """
    Get current authenticated user information.

    Protected route that requires valid JWT token.

    Args:
        current_user: Current authenticated user (from token)

    Returns:
        UserResponse: Current user information

    Raises:
        HTTPException 401: If token is invalid or missing
    """
    return current_user


# ============================================================================
# Simulation Endpoints
# ============================================================================

@app.post("/api/test-simulation")
async def test_simulation():
    """
    Test endpoint that runs a simulation on the example system.

    Loads the example_system.json config and runs a 5-round simulation
    to verify the backend integration is working correctly.

    Returns:
        dict: Simulation results including:
            - patch_priority_list: Ordered patches by priority
            - ris_summary: RIS trajectory over rounds
            - equilibrium_report: Game theory equilibrium statistics
            - per_round_details: Detailed round-by-round results
            - system_info: System metadata
            - simulation_metrics: Performance metrics

    Raises:
        HTTPException: If example config not found or simulation fails
    """
    try:
        # Path to example configuration
        example_config_path = Path(__file__).parent.parent / "base_backend" / "config" / "example_system.json"

        if not example_config_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Example configuration not found at {example_config_path}"
            )

        # Run simulation with 5 rounds
        results = run_simulation_from_config(
            config_path=str(example_config_path),
            rounds=5,
            patch_grouping_method="dependencies"
        )

        return {
            "status": "success",
            "message": "Test simulation completed successfully",
            "results": results
        }

    except FileNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail=f"Configuration file not found: {str(e)}"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid configuration or simulation parameters: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Simulation failed: {str(e)}"
        )


if __name__ == "__main__":
    # Run the application
    # Use app object instead of string when running directly
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
