"""
Simple API Server - No Database Required
Perfect for quick testing without Docker
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn
from datetime import date, timedelta
import random

app = FastAPI(
    title="Demand Forecasting API - Standalone Mode",
    description="Lightweight API for testing without database",
    version="1.0.0"
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Demand Forecasting API",
        "version": "1.0.0",
        "status": "operational",
        "mode": "standalone (no database)",
        "docs": "http://localhost:8001/docs",
        "endpoints": {
            "health": "/health",
            "forecast": "/api/v1/forecast/demo",
            "info": "/info"
        }
    }


@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "healthy",
        "timestamp": str(date.today()),
        "database": "not required (standalone mode)",
        "services": {
            "api": "operational",
            "forecasting": "mock data"
        }
    }


@app.get("/info")
async def info():
    """System information"""
    return {
        "system": {
            "name": "Demand Forecasting Platform",
            "version": "1.0.0",
            "environment": "standalone"
        },
        "capabilities": {
            "forecasting": {
                "models": ["Prophet", "XGBoost", "Ensemble"],
                "confidence_levels": [0.90, 0.95, 0.99]
            },
            "optimization": {
                "algorithms": ["EOQ", "Safety Stock", "Rebalancing"]
            }
        },
        "note": "Running in standalone mode with mock data. For full features, use Docker setup."
    }


@app.get("/api/v1/forecast/demo")
async def demo_forecast():
    """
    Demo forecast endpoint with sample data
    """
    # Generate sample forecast for next 30 days
    today = date.today()
    predictions = []

    for i in range(30):
        forecast_date = today + timedelta(days=i)
        base_demand = 150
        seasonal_factor = 1 + 0.3 * (i % 7) / 7  # Weekly seasonality
        noise = random.uniform(0.9, 1.1)

        demand = base_demand * seasonal_factor * noise

        predictions.append({
            "date": str(forecast_date),
            "demand": round(demand, 1),
            "lower_bound": round(demand * 0.85, 1),
            "upper_bound": round(demand * 1.15, 1),
            "confidence": 0.95
        })

    return {
        "sku_id": "SKU-001",
        "location_id": "DC-ATL",
        "model": "ensemble",
        "generated_at": str(today),
        "forecast_horizon_days": 30,
        "predictions": predictions,
        "metadata": {
            "mape": 12.5,
            "accuracy": "87.5%",
            "note": "This is demo data. Real forecasts require database and trained models."
        }
    }


@app.post("/api/v1/forecast")
async def generate_forecast():
    """
    Full forecast endpoint (returns demo data in standalone mode)
    """
    return {
        "message": "In standalone mode. Use /api/v1/forecast/demo for sample data.",
        "note": "For full functionality, start with Docker: docker-compose up -d"
    }


if __name__ == "__main__":
    print("\n" + "="*70)
    print("DEMAND FORECASTING API - STANDALONE MODE")
    print("="*70)
    print("\nStarting server without database requirements...")
    print("\n✓ Server will be available at: http://localhost:8001")
    print("✓ Interactive docs at: http://localhost:8001/docs")
    print("✓ Health check at: http://localhost:8001/health")
    print("✓ Demo forecast at: http://localhost:8001/api/v1/forecast/demo")
    print("\nPress Ctrl+C to stop the server")
    print("="*70 + "\n")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )
