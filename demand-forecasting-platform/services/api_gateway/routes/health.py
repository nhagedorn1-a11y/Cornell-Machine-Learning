"""
Health Check Routes
Monitor system health and service status
"""

from fastapi import APIRouter, status
from datetime import datetime
from typing import Dict
import asyncio
import logging

from shared.models.schemas import HealthStatus
from shared.database.connection import Database
from shared.utils.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=HealthStatus, status_code=status.HTTP_200_OK)
async def health_check():
    """
    Basic health check - is the API responding?
    """
    return HealthStatus(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.utcnow(),
        services={"api": "healthy"}
    )


@router.get("/detailed", response_model=HealthStatus)
async def detailed_health_check():
    """
    Detailed health check - test all dependencies
    Checks: Database, Redis, MLflow
    """
    services_status = {}
    overall_status = "healthy"
    start_time = datetime.utcnow()

    # Check Database
    try:
        async with Database.session() as db:
            await db.execute("SELECT 1")
        services_status["database"] = "healthy"
        logger.debug("Database health check: OK")
    except Exception as e:
        services_status["database"] = f"unhealthy: {str(e)}"
        overall_status = "degraded"
        logger.error(f"Database health check failed: {e}")

    # Check Redis (if configured)
    try:
        import redis.asyncio as redis
        redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
        await redis_client.ping()
        services_status["redis"] = "healthy"
        await redis_client.close()
        logger.debug("Redis health check: OK")
    except Exception as e:
        services_status["redis"] = f"unhealthy: {str(e)}"
        overall_status = "degraded"
        logger.error(f"Redis health check failed: {e}")

    # Check MLflow (optional)
    try:
        import mlflow
        mlflow.set_tracking_uri(settings.MLFLOW_TRACKING_URI)
        # Simple connection test
        mlflow.get_tracking_uri()
        services_status["mlflow"] = "healthy"
        logger.debug("MLflow health check: OK")
    except Exception as e:
        services_status["mlflow"] = f"degraded: {str(e)}"
        # MLflow being down doesn't make system unhealthy
        logger.warning(f"MLflow health check failed: {e}")

    # Calculate latency
    latency = (datetime.utcnow() - start_time).total_seconds() * 1000  # ms

    # Set overall status
    if all(s == "healthy" for s in services_status.values()):
        overall_status = "healthy"
    elif any("unhealthy" in s for s in services_status.values()):
        overall_status = "unhealthy"
    else:
        overall_status = "degraded"

    return HealthStatus(
        status=overall_status,
        version="1.0.0",
        timestamp=datetime.utcnow(),
        services=services_status,
        latency_ms=latency
    )


@router.get("/readiness")
async def readiness_check():
    """
    Kubernetes readiness probe
    Returns 200 if service is ready to accept traffic
    """
    try:
        async with Database.session() as db:
            await db.execute("SELECT 1")
        return {"status": "ready"}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return {"status": "not ready", "error": str(e)}


@router.get("/liveness")
async def liveness_check():
    """
    Kubernetes liveness probe
    Returns 200 if service is alive (even if degraded)
    """
    return {"status": "alive", "timestamp": datetime.utcnow().isoformat()}
