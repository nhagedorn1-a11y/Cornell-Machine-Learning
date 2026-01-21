"""
Optimization API Routes
Inventory rebalancing and procurement optimization
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from shared.models.schemas import RebalanceRequest, RebalanceResponse, TransferRecommendation, Priority
from shared.database.connection import get_db
from decimal import Decimal

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/rebalance", response_model=RebalanceResponse)
async def optimize_inventory_rebalance(
    request: RebalanceRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Generate inventory transfer recommendations to optimize stock placement

    **Algorithm:**
    1. Compare current inventory vs forecast demand
    2. Identify surplus (excess stock) and deficit (understocked) locations
    3. Calculate optimal transfers considering:
       - Transportation costs
       - Expected ROI (revenue from prevented stockouts)
       - Capacity constraints
       - Budget limits

    **Returns:**
    - Transfer recommendations (from → to, quantity, cost, ROI)
    - Optional procurement recommendations (if rebalancing insufficient)
    - Total cost and expected ROI
    """

    try:
        logger.info(f"Rebalancing request: {len(request.current_inventory.__root__)} locations")

        # Mock implementation for MVP
        # In production, this would use optimization algorithms (linear programming)

        transfer_recs = []

        # Simple logic: Find overstock and understock locations
        inventory_data = request.current_inventory.__root__

        # Example transfer from Chicago to Atlanta
        transfer_recs.append(
            TransferRecommendation(
                **{
                    "from": "DC-CHI",
                    "to": "DC-ATL",
                    "sku_id": "SKU-001",
                    "quantity": 300,
                    "cost": Decimal("1200.00"),
                    "expected_roi": Decimal("4500.00"),
                    "priority": Priority.HIGH,
                    "rationale": "Atlanta forecast shows 450 unit demand vs 200 current stock. "
                               "Chicago has 800 units (250 over target). Transfer prevents "
                               "stockout and reduces excess carrying cost."
                }
            )
        )

        total_cost = sum(t.cost for t in transfer_recs)
        expected_roi = sum(t.expected_roi for t in transfer_recs)

        response = RebalanceResponse(
            transfer_recommendations=transfer_recs,
            procurement_recommendations=None,
            total_cost=total_cost,
            expected_roi=expected_roi,
            summary={
                "total_transfers": len(transfer_recs),
                "roi_percentage": float((expected_roi / total_cost * 100) if total_cost > 0 else 0),
                "estimated_stockout_prevention": "$4,500",
                "carrying_cost_reduction": "$800"
            }
        )

        logger.info(f"Rebalancing complete: {len(transfer_recs)} transfers, ROI: {expected_roi}")

        return response

    except Exception as e:
        logger.error(f"Rebalancing failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate rebalancing recommendations"
        )


@router.post("/procurement")
async def optimize_procurement(
    sku_ids: list[str],
    planning_horizon: int = 90,
    db: AsyncSession = Depends(get_db)
):
    """
    Generate procurement recommendations based on forecasted demand

    **Returns:**
    - When to order
    - How much to order (EOQ optimization)
    - Expected cost
    - Supplier recommendations
    """

    try:
        # Mock procurement recommendation
        recommendations = [
            {
                "sku_id": sku_id,
                "order_date": "2026-02-15",
                "quantity": 5000,
                "estimated_cost": 25000.00,
                "supplier": "Supplier-A",
                "rationale": "Forecast shows peak demand in March. Order by Feb 15 for 14-day lead time."
            }
            for sku_id in sku_ids
        ]

        return {
            "procurement_recommendations": recommendations,
            "total_cost": sum(r["estimated_cost"] for r in recommendations),
            "planning_horizon_days": planning_horizon
        }

    except Exception as e:
        logger.error(f"Procurement optimization failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate procurement recommendations"
        )
