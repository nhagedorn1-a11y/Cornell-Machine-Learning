"""
Configuration Management
Loads settings from environment variables with sensible defaults
"""

from pydantic_settings import BaseSettings
from pydantic import Field, validator
from typing import List, Optional
from functools import lru_cache
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Environment
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")

    # Database
    DATABASE_URL: str = Field(..., env="DATABASE_URL")
    DB_POOL_SIZE: int = Field(default=20, env="DB_POOL_SIZE")
    DB_MAX_OVERFLOW: int = Field(default=10, env="DB_MAX_OVERFLOW")

    # Redis
    REDIS_URL: str = Field(..., env="REDIS_URL")
    CACHE_PREDICTIONS_TTL: int = Field(default=1800, env="CACHE_PREDICTIONS_TTL")

    # API Configuration
    API_HOST: str = Field(default="0.0.0.0", env="API_HOST")
    API_PORT: int = Field(default=8000, env="API_PORT")
    API_WORKERS: int = Field(default=4, env="API_WORKERS")
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000"],
        env="CORS_ORIGINS"
    )

    # External API Keys
    OPENWEATHER_API_KEY: Optional[str] = Field(None, env="OPENWEATHER_API_KEY")
    FRED_API_KEY: Optional[str] = Field(None, env="FRED_API_KEY")
    NOAA_API_KEY: Optional[str] = Field(None, env="NOAA_API_KEY")

    # MLflow
    MLFLOW_TRACKING_URI: str = Field(
        default="http://localhost:5000",
        env="MLFLOW_TRACKING_URI"
    )
    MLFLOW_EXPERIMENT_NAME: str = Field(
        default="demand-forecasting",
        env="MLFLOW_EXPERIMENT_NAME"
    )

    # Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")

    # Model Configuration
    DEFAULT_FORECAST_HORIZON: int = Field(default=90, env="DEFAULT_FORECAST_HORIZON")
    DEFAULT_CONFIDENCE_LEVEL: float = Field(
        default=0.95,
        env="DEFAULT_CONFIDENCE_LEVEL"
    )
    MODEL_RETRAIN_FREQUENCY: int = Field(
        default=7,
        env="MODEL_RETRAIN_FREQUENCY"
    )  # days

    # Performance Tuning
    MAX_CONCURRENT_FORECASTS: int = Field(
        default=10,
        env="MAX_CONCURRENT_FORECASTS"
    )
    FEATURE_STORE_CACHE_TTL: int = Field(
        default=3600,
        env="FEATURE_STORE_CACHE_TTL"
    )

    # Data Ingestion
    INGESTION_SCHEDULE: str = Field(
        default="0 */6 * * *",
        env="INGESTION_SCHEDULE"
    )
    WEATHER_UPDATE_INTERVAL: int = Field(default=3600, env="WEATHER_UPDATE_INTERVAL")
    ECONOMIC_UPDATE_INTERVAL: int = Field(
        default=86400,
        env="ECONOMIC_UPDATE_INTERVAL"
    )

    # Security
    JWT_SECRET_KEY: str = Field(
        default="dev_secret_change_in_production",
        env="JWT_SECRET_KEY"
    )
    JWT_ALGORITHM: str = Field(default="HS256", env="JWT_ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30,
        env="ACCESS_TOKEN_EXPIRE_MINUTES"
    )

    # Multi-tenancy
    ENABLE_MULTI_TENANCY: bool = Field(default=True, env="ENABLE_MULTI_TENANCY")
    DEFAULT_TENANT: str = Field(default="demo", env="DEFAULT_TENANT")

    # Feature Flags
    ENABLE_LSTM_MODEL: bool = Field(default=False, env="ENABLE_LSTM_MODEL")
    ENABLE_REAL_TIME_UPDATES: bool = Field(
        default=False,
        env="ENABLE_REAL_TIME_UPDATES"
    )
    ENABLE_AUTO_REBALANCING: bool = Field(
        default=True,
        env="ENABLE_AUTO_REBALANCING"
    )

    # Monitoring (Optional)
    SENTRY_DSN: Optional[str] = Field(None, env="SENTRY_DSN")
    DATADOG_API_KEY: Optional[str] = Field(None, env="DATADOG_API_KEY")
    PROMETHEUS_ENABLED: bool = Field(default=False, env="PROMETHEUS_ENABLED")

    @validator("CORS_ORIGINS", pre=True)
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @validator("LOG_LEVEL")
    def validate_log_level(cls, v):
        """Validate log level"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid_levels}")
        return v.upper()

    @validator("DEFAULT_CONFIDENCE_LEVEL")
    def validate_confidence_level(cls, v):
        """Validate confidence level is between 0 and 1"""
        if not 0 < v < 1:
            raise ValueError("Confidence level must be between 0 and 1")
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance
    Use lru_cache to avoid reading .env file multiple times
    """
    return Settings()


# Global settings instance
settings = get_settings()
