"""
FastAPI Web API for Patch Priority Framework
Main application entry point
"""
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Import backend bridge
from backend_bridge import run_simulation_from_config

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
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
