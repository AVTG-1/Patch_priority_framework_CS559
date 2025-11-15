"""
Configuration management for the FastAPI application
Loads and validates environment variables
"""
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables
    Falls back to defaults if not set
    """

    # Application Configuration
    app_name: str = Field(default="Patch Priority Framework API", alias="APP_NAME")
    app_version: str = Field(default="1.0.0", alias="APP_VERSION")
    debug: bool = Field(default=False, alias="DEBUG")

    # Server Configuration
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")

    # Security Configuration
    secret_key: str = Field(
        default="dev-secret-key-change-in-production",
        alias="SECRET_KEY"
    )
    algorithm: str = Field(default="HS256", alias="ALGORITHM")
    access_token_expire_minutes: int = Field(
        default=30,
        alias="ACCESS_TOKEN_EXPIRE_MINUTES"
    )

    # Database Configuration
    database_url: str = Field(
        default="sqlite:///./patch_priority.db",
        alias="DATABASE_URL"
    )

    # CORS Configuration
    allowed_origins: str = Field(
        default='["http://localhost:3000","http://localhost:8080"]',
        alias="ALLOWED_ORIGINS"
    )

    # NVD API Configuration
    nvd_api_key: str = Field(default="", alias="NVD_API_KEY")

    # Logging Configuration
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # Pydantic v2 configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    def get_allowed_origins_list(self) -> List[str]:
        """
        Parse allowed_origins string to list
        Returns:
            List[str]: List of allowed origin URLs
        """
        import json
        try:
            return json.loads(self.allowed_origins)
        except json.JSONDecodeError:
            # Fallback to comma-separated string
            return [origin.strip() for origin in self.allowed_origins.split(",")]


# Create global settings instance
settings = Settings()


def get_settings() -> Settings:
    """
    Dependency function to get settings instance
    Can be used with FastAPI's Depends()

    Returns:
        Settings: Application settings instance
    """
    return settings
