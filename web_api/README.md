# Patch Priority Framework - FastAPI Web API

This is the FastAPI-based REST API for the Patch Priority Framework, providing HTTP endpoints for the game-theoretic patch prioritization system.

## Setup

### 1. Install Dependencies

```bash
cd web_api
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy the example environment file and update with your values:

```bash
cp .env.example .env
```

Edit `.env` and set:
- `SECRET_KEY`: Generate using `openssl rand -hex 32`
- `DATABASE_URL`: Your database connection string
- `NVD_API_KEY`: (Optional) Your NVD API key for vulnerability data

### 3. Run the Application

#### Development Mode (with auto-reload):

```bash
python main.py
```

Or using uvicorn directly:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

#### Production Mode:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API Endpoints

### Health Check

- **GET** `/health`
  - Returns API health status
  - Response: `{"status": "healthy", "service": "Patch Priority Framework API", "version": "1.0.0"}`

### Root

- **GET** `/`
  - Returns API information and available endpoints
  - Response: `{"message": "Welcome to Patch Priority Framework API", "docs": "/docs", "health": "/health"}`

### API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Configuration

Configuration is managed through environment variables loaded via `config.py`:

- `APP_NAME`: Application name
- `APP_VERSION`: API version
- `DEBUG`: Enable debug mode (default: False)
- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 8000)
- `SECRET_KEY`: JWT secret key for authentication
- `DATABASE_URL`: Database connection string
- `ALLOWED_ORIGINS`: CORS allowed origins (JSON array)
- `NVD_API_KEY`: National Vulnerability Database API key

## Testing the API

### Using curl:

```bash
# Health check
curl http://localhost:8000/health

# Root endpoint
curl http://localhost:8000/
```

### Using httpie:

```bash
# Health check
http GET http://localhost:8000/health

# Root endpoint
http GET http://localhost:8000/
```

## Project Structure

```
web_api/
├── main.py              # FastAPI application entry point
├── config.py            # Configuration management
├── requirements.txt     # Python dependencies
├── .env.example         # Example environment variables
├── .env                 # Your environment variables (not in git)
└── README.md           # This file
```

## Next Steps

This is the foundation for the FastAPI backend. Future development will add:
- Authentication and authorization endpoints
- System configuration endpoints
- Vulnerability management endpoints
- Game simulation endpoints
- Collaboration features
- Database integration
- Frontend integration

## Development

The API runs in development mode with auto-reload enabled. Any changes to Python files will automatically restart the server.

To access the interactive API documentation:
1. Start the server
2. Visit http://localhost:8000/docs for Swagger UI
3. Visit http://localhost:8000/redoc for ReDoc documentation

## License

Part of the Patch Priority Framework CS559 project.
