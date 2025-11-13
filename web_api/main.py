"""
FastAPI Web API for Patch Priority Framework
Main application entry point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

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


if __name__ == "__main__":
    # Run the application
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
