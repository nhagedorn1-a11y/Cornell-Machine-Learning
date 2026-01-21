"""
Metrics API Routes
Dashboard metrics and KPIs
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from decimal import Decimal

from shared.models.schemas import (
    DashboardMetrics,
    ForecastAccuracyMetrics,
    InventoryHealthMetrics,
    ServiceLevelMetrics
)
from shared.database.connection import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/dashboard", response_model=DashboardMetrics)
async def get_dashboard_metrics(
    db: AsyncSession = Depends(get_db)
):
    """
    Get comprehensive dashboard metrics

    **Returns:**
    - Forecast accuracy (MAPE, RMSE, bias)
    - Inventory health (value, turnover, stockout rate)
    - Service levels (fill rate, on-time delivery)
    """

    try:
        # Mock metrics for MVP
        # In production, these would be calculated from database

        forecast_accuracy = ForecastAccuracyMetrics(
            mape=Decimal("14.2"),
            rmse=Decimal("45.8"),
            bias=Decimal("-2.3"),
            samples=1250
        )

        inventory_health = InventoryHealthMetrics(
            total_value=Decimal("12800000.00"),
            turnover_ratio=Decimal("4.2"),
            stockout_rate=Decimal("0.018"),
            excess_inventory_pct=Decimal("8.5"),
            days_of_supply=Decimal("32.5")
        )

        service_levels = ServiceLevelMetrics(
            fill_rate=Decimal("0.942"),
            on_time_delivery=Decimal("0.956"),
            perfect_order_rate=Decimal("0.912")
        )

        metrics = DashboardMetrics(
            forecast_accuracy=forecast_accuracy,
            inventory_health=inventory_health,
            service_levels=service_levels
        )

        logger.info("Dashboard metrics retrieved")

        return metrics

    except Exception as e:
        logger.error(f"Failed to retrieve dashboard metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve metrics"
        )


@router.get("/forecast-accuracy")
async def get_forecast_accuracy_breakdown(
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed forecast accuracy breakdown by SKU, location, time period
    """

    try:
        # Mock detailed accuracy metrics
        return {
            "overall": {
                "mape": 14.2,
                "rmse": 45.8
            },
            "by_category": [
                {"category": "Lawn Care", "mape": 12.5, "samples": 450},
                {"category": "Garden Tools", "mape": 16.8, "samples": 380},
                {"category": "Pest Control", "mape": 13.2, "samples": 420}
            ],
            "by_location": [
                {"location": "DC-ATL", "mape": 15.1, "samples": 320},
                {"location": "DC-CHI", "mape": 13.8, "samples": 295},
                {"location": "DC-NYC", "mape": 14.5, "samples": 310}
            ],
            "trend": [
                {"week": "2026-W01", "mape": 15.2},
                {"week": "2026-W02", "mape": 14.8},
                {"week": "2026-W03", "mape": 14.2}
            ]
        }

    except Exception as e:
        logger.error(f"Failed to get accuracy breakdown: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve accuracy breakdown"
        )


@router.get("/inventory-health")
async def get_inventory_health_details(
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed inventory health metrics by location and category
    """

    try:
        return {
            "by_location": [
                {
                    "location": "DC-ATL",
                    "total_value": 2800000,
                    "days_of_supply": 28,
                    "stockout_risk": "low",
                    "excess_inventory_pct": 5.2
                },
                {
                    "location": "DC-CHI",
                    "total_value": 3200000,
                    "days_of_supply": 35,
                    "stockout_risk": "low",
                    "excess_inventory_pct": 12.8
                },
                {
                    "location": "DC-NYC",
                    "total_value": 2900000,
                    "days_of_supply": 22,
                    "stockout_risk": "medium",
                    "excess_inventory_pct": 3.1
                }
            ],
            "alerts": [
                {
                    "type": "excess_inventory",
                    "location": "DC-CHI",
                    "value": 409600,
                    "recommendation": "Transfer 300 units to DC-NYC"
                },
                {
                    "type": "stockout_risk",
                    "location": "DC-NYC",
                    "sku": "SKU-045",
                    "recommendation": "Emergency procurement: 500 units"
                }
            ]
        }

    except Exception as e:
        logger.error(f"Failed to get inventory health: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve inventory health"
        )


@router.get("/service-levels")
async def get_service_level_details(
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed service level metrics and trends
    """

    try:
        return {
            "current": {
                "fill_rate": 0.942,
                "on_time_delivery": 0.956,
                "perfect_order_rate": 0.912
            },
            "trend_30_days": [
                {"date": "2026-01-01", "fill_rate": 0.938},
                {"date": "2026-01-08", "fill_rate": 0.941},
                {"date": "2026-01-15", "fill_rate": 0.942},
                {"date": "2026-01-22", "fill_rate": 0.945}
            ],
            "target": {
                "fill_rate": 0.98,
                "on_time_delivery": 0.95,
                "perfect_order_rate": 0.92
            },
            "gap_analysis": {
                "fill_rate_gap": 0.038,
                "actions_to_close_gap": [
                    "Reduce forecast error by 3%",
                    "Increase safety stock by 10%",
                    "Improve supplier on-time delivery"
                ]
            }
        }

    except Exception as e:
        logger.error(f"Failed to get service levels: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve service levels"
        )
