"""
API Gateway - Main FastAPI Application
Handles all RESTful endpoints for the Demand Forecasting Platform
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging
import time
from contextlib import asynccontextmanager

from services.api_gateway.routes import forecasting, optimization, metrics, commodities, health
from services.api_gateway.middleware import auth, logging as log_middleware
from shared.database.connection import Database
from shared.utils.config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan events (startup/shutdown)
    """
    # Startup
    logger.info("Starting Demand Forecasting API Gateway...")

    # Initialize database connection
    await Database.connect()
    logger.info(f"Connected to database: {settings.DATABASE_URL.split('@')[1]}")

    # Warm up ML models (load into memory)
    # await load_ml_models()

    logger.info("API Gateway ready to accept requests")

    yield

    # Shutdown
    logger.info("Shutting down API Gateway...")
    await Database.disconnect()
    logger.info("Database connections closed")


# Create FastAPI application
app = FastAPI(
    title="Demand Forecasting & Inventory Optimization API",
    description="""
    Production-grade SaaS platform for predictive demand forecasting and inventory optimization.

    ## Features
    * **Forecasting**: SKU-level demand predictions with 95% confidence intervals
    * **Optimization**: Inventory rebalancing and procurement recommendations
    * **Weather Intelligence**: 14-day weather-driven demand signals
    * **Economic Indicators**: Macro trends influencing consumer demand
    * **ML Pipeline**: Ensemble models (Prophet + XGBoost + LSTM)
    * **Real-time Alerts**: Stockout risks and overstock warnings

    ## Authentication
    All endpoints require API key authentication via `X-API-Key` header.
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# ============================================================================
# Middleware Configuration
# ============================================================================

# CORS - Allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GZip compression for responses
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Custom logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests with timing"""
    start_time = time.time()

    # Log request
    logger.info(f"Request: {request.method} {request.url.path}")

    # Process request
    response = await call_next(request)

    # Calculate processing time
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)

    # Log response
    logger.info(
        f"Response: {request.method} {request.url.path} "
        f"Status={response.status_code} Time={process_time:.3f}s"
    )

    return response

# API Key authentication middleware (applied to specific routes)
# app.add_middleware(auth.APIKeyMiddleware)

# ============================================================================
# Exception Handlers
# ============================================================================

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with detailed messages"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "detail": exc.errors(),
            "body": exc.body
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred. Please try again later."
        }
    )

# ============================================================================
# Route Registration
# ============================================================================

# Health check endpoints
app.include_router(
    health.router,
    prefix="/health",
    tags=["Health"]
)

# API v1 routes
API_V1_PREFIX = "/api/v1"

app.include_router(
    forecasting.router,
    prefix=f"{API_V1_PREFIX}/forecast",
    tags=["Forecasting"]
)

app.include_router(
    optimization.router,
    prefix=f"{API_V1_PREFIX}/optimize",
    tags=["Optimization"]
)

app.include_router(
    metrics.router,
    prefix=f"{API_V1_PREFIX}/metrics",
    tags=["Metrics"]
)

app.include_router(
    commodities.router,
    prefix=f"{API_V1_PREFIX}/commodities",
    tags=["Commodities"]
)

# ============================================================================
# Root Endpoints
# ============================================================================

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint - API information"""
    return {
        "name": "Demand Forecasting & Inventory Optimization API",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/info", tags=["Root"])
async def info():
    """System information and capabilities"""
    return {
        "system": {
            "name": "Demand Forecasting Platform",
            "version": "1.0.0",
            "environment": settings.ENVIRONMENT
        },
        "capabilities": {
            "forecasting": {
                "models": ["Prophet", "XGBoost", "LSTM", "Ensemble"],
                "max_forecast_horizon_days": settings.DEFAULT_FORECAST_HORIZON,
                "confidence_levels": [0.90, 0.95, 0.99]
            },
            "optimization": {
                "algorithms": ["EOQ", "Safety Stock", "Rebalancing"],
                "multi_echelon": True
            },
            "data_sources": {
                "weather": ["NOAA", "OpenWeather"],
                "economic": ["FRED", "BLS"],
                "custom": True
            }
        },
        "performance_targets": {
            "forecast_mape": "< 15%",
            "api_latency_p95": "< 200ms",
            "uptime": "99.9%"
        }
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True if settings.ENVIRONMENT == "development" else False,
        workers=settings.API_WORKERS if settings.ENVIRONMENT == "production" else 1
    )
