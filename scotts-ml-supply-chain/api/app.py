"""
FastAPI application for Scotts ML Supply Chain Optimizer
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supply_chain_optimizer import SupplyChainOptimizer

# Initialize FastAPI app
app = FastAPI(
    title="Scotts ML Supply Chain Optimizer API",
    description="AI-powered supply chain optimization for commodity ordering and inventory management",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global optimizer instance
optimizer = None


# ========== Request/Response Models ==========

class ForecastRequest(BaseModel):
    horizon_days: int = 90
    include_weather: bool = True


class InventoryOptimizationRequest(BaseModel):
    products: Optional[List[str]] = None
    service_level: float = 0.95


class CommodityPlanRequest(BaseModel):
    planning_horizon_days: int = 90


class StatusResponse(BaseModel):
    status: str
    message: str
    timestamp: str


# ========== Endpoints ==========

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "name": "Scotts ML Supply Chain Optimizer API",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": [
            "/health",
            "/initialize",
            "/forecast",
            "/inventory/optimize",
            "/inventory/project",
            "/commodities/plan",
            "/summary"
        ]
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "optimizer_initialized": optimizer is not None
    }


@app.post("/initialize", response_model=StatusResponse)
async def initialize_optimizer(generate_sample: bool = True):
    """
    Initialize the optimizer with data

    Args:
        generate_sample: If True, generate sample data for demo
    """
    global optimizer

    try:
        optimizer = SupplyChainOptimizer()

        if generate_sample:
            optimizer.generate_sample_data(
                num_stores=10,
                num_products=20,
                days_history=365
            )

        return StatusResponse(
            status="success",
            message="Optimizer initialized successfully",
            timestamp=datetime.now().isoformat()
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/forecast")
async def generate_forecast(request: ForecastRequest):
    """
    Generate demand forecasts

    Args:
        horizon_days: Number of days to forecast (default: 90)
        include_weather: Include weather data in forecast (default: True)
    """
    global optimizer

    if optimizer is None:
        raise HTTPException(
            status_code=400,
            detail="Optimizer not initialized. Call /initialize first."
        )

    try:
        forecast = optimizer.forecast_demand(
            horizon_days=request.horizon_days,
            include_weather=request.include_weather
        )

        # Convert to dict for JSON response
        forecast_dict = forecast.to_dict('records')

        return {
            "status": "success",
            "forecast_points": len(forecast),
            "horizon_days": request.horizon_days,
            "total_forecasted_demand": float(forecast['predicted_quantity'].sum()),
            "forecasts": forecast_dict[:100],  # Limit response size
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/inventory/optimize")
async def optimize_inventory(request: InventoryOptimizationRequest):
    """
    Optimize inventory policies

    Args:
        products: Optional list of product SKUs to optimize
        service_level: Target service level (0-1)
    """
    global optimizer

    if optimizer is None:
        raise HTTPException(
            status_code=400,
            detail="Optimizer not initialized. Call /initialize first."
        )

    try:
        policies = optimizer.optimize_inventory(
            products=request.products,
            service_level=request.service_level
        )

        return {
            "status": "success",
            "products_optimized": len(policies),
            "service_level": request.service_level,
            "policies": policies.to_dict('records'),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/inventory/project")
async def project_inventory(horizon_days: int = 60):
    """
    Project future inventory levels

    Args:
        horizon_days: Number of days to project
    """
    global optimizer

    if optimizer is None:
        raise HTTPException(
            status_code=400,
            detail="Optimizer not initialized. Call /initialize first."
        )

    try:
        projections = optimizer.project_inventory_levels(
            horizon_days=horizon_days
        )

        return {
            "status": "success",
            "projection_points": len(projections),
            "horizon_days": horizon_days,
            "projections": projections.to_dict('records')[:200],  # Limit size
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/commodities/plan")
async def plan_commodities(request: CommodityPlanRequest):
    """
    Generate commodity procurement plan

    Args:
        planning_horizon_days: Planning horizon in days
    """
    global optimizer

    if optimizer is None:
        raise HTTPException(
            status_code=400,
            detail="Optimizer not initialized. Call /initialize first."
        )

    try:
        orders = optimizer.plan_commodity_orders(
            planning_horizon_days=request.planning_horizon_days
        )

        if orders:
            total_cost = sum(order['estimated_cost'] for order in orders)
            urgent_orders = [o for o in orders if o['urgency_score'] >= 0.7]
        else:
            total_cost = 0
            urgent_orders = []

        return {
            "status": "success",
            "total_orders": len(orders),
            "total_cost": total_cost,
            "urgent_orders_count": len(urgent_orders),
            "orders": orders,
            "urgent_orders": urgent_orders,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/summary")
async def get_summary():
    """Get executive summary of all analyses"""
    global optimizer

    if optimizer is None:
        raise HTTPException(
            status_code=400,
            detail="Optimizer not initialized. Call /initialize first."
        )

    try:
        summary = optimizer.generate_executive_summary()
        return summary

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/export")
async def export_results(output_dir: str = "./output"):
    """Export all results to CSV files"""
    global optimizer

    if optimizer is None:
        raise HTTPException(
            status_code=400,
            detail="Optimizer not initialized. Call /initialize first."
        )

    try:
        optimizer.export_results(output_dir=output_dir)

        return {
            "status": "success",
            "message": f"Results exported to {output_dir}",
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== Run Server ==========

if __name__ == "__main__":
    import uvicorn

    print("Starting Scotts ML Supply Chain Optimizer API...")
    print("API Documentation: http://localhost:8000/docs")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
