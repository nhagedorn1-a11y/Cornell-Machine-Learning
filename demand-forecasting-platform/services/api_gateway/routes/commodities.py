"""
Commodities API Routes
Commodity price forecasting and procurement planning
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from datetime import date, timedelta
from decimal import Decimal

from shared.models.schemas import (
    CommodityForecastRequest,
    CommodityForecastResponse,
    CommodityPricePrediction,
    ProcurementScheduleItem
)
from shared.database.connection import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/forecast", response_model=CommodityForecastResponse)
async def forecast_commodity_prices(
    request: CommodityForecastRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Forecast commodity prices and generate procurement schedule

    **Commodities Supported:**
    - Petrochemicals (oil, natural gas, plastics)
    - Metals (steel, aluminum, copper)
    - Agricultural (fertilizer components, wood pulp)
    - Freight (diesel, shipping rates)

    **Returns:**
    - Daily price forecasts with confidence intervals
    - Optimal procurement schedule (when/how much to buy)
    - Hedging recommendations
    - Total estimated cost
    """

    try:
        logger.info(
            f"Commodity forecast request: {len(request.material_types)} materials, "
            f"{request.planning_horizon} days"
        )

        price_forecasts = {}
        procurement_schedule = []
        total_cost = Decimal("0.00")

        # Generate forecast for each commodity
        for material in request.material_types:
            forecasts = _generate_commodity_forecast(
                material,
                request.planning_horizon
            )
            price_forecasts[material] = forecasts

            # Generate procurement recommendation
            procurement_item = _generate_procurement_recommendation(
                material,
                forecasts
            )
            procurement_schedule.append(procurement_item)
            total_cost += procurement_item.estimated_price

        # Generate hedging recommendations
        hedging_recs = _generate_hedging_recommendations(
            request.material_types,
            price_forecasts
        )

        response = CommodityForecastResponse(
            price_forecasts=price_forecasts,
            procurement_schedule=procurement_schedule,
            total_estimated_cost=total_cost,
            hedging_recommendations=hedging_recs
        )

        logger.info(
            f"Commodity forecast generated: {len(request.material_types)} materials, "
            f"total cost: ${total_cost}"
        )

        return response

    except Exception as e:
        logger.error(f"Commodity forecast failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate commodity forecast"
        )


def _generate_commodity_forecast(
    material: str,
    planning_horizon: int
) -> list[CommodityPricePrediction]:
    """Generate price forecast for a commodity (mock implementation)"""

    # Base prices (mock data)
    base_prices = {
        "oil": 75.0,
        "steel": 850.0,
        "plastic": 1200.0,
        "aluminum": 2400.0,
        "fertilizer": 580.0,
        "diesel": 3.50,
        "natural_gas": 3.20
    }

    base_price = base_prices.get(material.lower(), 100.0)
    forecasts = []

    start_date = date.today()

    for i in range(planning_horizon):
        current_date = start_date + timedelta(days=i)

        # Add trend and seasonality (mock)
        trend = i * 0.1  # Slight upward trend
        seasonality = 5.0 * (i % 30) / 30  # Monthly cycle

        price = base_price + trend + seasonality
        lower_bound = price * 0.95
        upper_bound = price * 1.05

        forecast = CommodityPricePrediction(
            date=current_date,
            price=Decimal(str(round(price, 2))),
            lower_bound=Decimal(str(round(lower_bound, 2))),
            upper_bound=Decimal(str(round(upper_bound, 2))),
            confidence=Decimal("0.90")
        )

        forecasts.append(forecast)

    return forecasts


def _generate_procurement_recommendation(
    material: str,
    forecasts: list[CommodityPricePrediction]
) -> ProcurementScheduleItem:
    """Generate procurement recommendation based on price forecast"""

    # Find optimal buy date (lowest price in forecast)
    optimal_date = min(forecasts, key=lambda f: f.price).date
    optimal_price = min(f.price for f in forecasts)

    # Typical order quantities (mock)
    quantities = {
        "oil": 10000,  # barrels
        "steel": 50,   # tons
        "plastic": 100, # tons
        "aluminum": 25, # tons
        "fertilizer": 200, # tons
        "diesel": 5000,  # gallons
        "natural_gas": 10000  # MMBtu
    }

    quantity = Decimal(str(quantities.get(material.lower(), 100)))
    estimated_price = optimal_price * quantity

    rationale = (
        f"Forecast shows price trough on {optimal_date.strftime('%B %d')}. "
        f"Recommended order date locks in {optimal_price:.2f}/unit vs current "
        f"{forecasts[0].price:.2f}/unit. Estimated savings: "
        f"${(forecasts[0].price - optimal_price) * quantity:.2f}"
    )

    return ProcurementScheduleItem(
        commodity=material,
        quantity=quantity,
        order_date=optimal_date,
        estimated_price=estimated_price,
        rationale=rationale
    )


def _generate_hedging_recommendations(
    materials: list[str],
    price_forecasts: dict
) -> list[str]:
    """Generate hedging recommendations based on price volatility"""

    recommendations = []

    for material in materials:
        forecasts = price_forecasts[material]

        # Calculate price volatility
        prices = [float(f.price) for f in forecasts]
        volatility = (max(prices) - min(prices)) / min(prices) * 100

        if volatility > 10:
            recommendations.append(
                f"{material.title()}: High volatility ({volatility:.1f}%). "
                f"Consider fixed-price contract or futures hedge."
            )
        elif volatility > 5:
            recommendations.append(
                f"{material.title()}: Moderate volatility ({volatility:.1f}%). "
                f"Monitor for hedging opportunities."
            )

    return recommendations if recommendations else [
        "Current market shows low volatility. Spot purchasing recommended."
    ]


@router.get("/prices/current")
async def get_current_commodity_prices(
    materials: list[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get current commodity spot prices

    **Returns:**
    - Latest spot prices
    - 24-hour change
    - Source and timestamp
    """

    try:
        # Mock current prices
        prices = [
            {
                "material": "oil",
                "price": 75.50,
                "unit": "per barrel",
                "change_24h": 1.2,
                "change_pct": 1.6,
                "source": "NYMEX",
                "timestamp": "2026-01-21T12:00:00Z"
            },
            {
                "material": "steel",
                "price": 850.00,
                "unit": "per ton",
                "change_24h": -5.50,
                "change_pct": -0.6,
                "source": "LME",
                "timestamp": "2026-01-21T12:00:00Z"
            },
            {
                "material": "plastic",
                "price": 1200.00,
                "unit": "per ton",
                "change_24h": 8.00,
                "change_pct": 0.7,
                "source": "ICIS",
                "timestamp": "2026-01-21T12:00:00Z"
            }
        ]

        # Filter by requested materials if specified
        if materials:
            prices = [p for p in prices if p["material"] in materials]

        return {
            "prices": prices,
            "count": len(prices)
        }

    except Exception as e:
        logger.error(f"Failed to get current prices: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve current prices"
        )


@router.get("/prices/historical")
async def get_historical_commodity_prices(
    material: str,
    days: int = 90,
    db: AsyncSession = Depends(get_db)
):
    """
    Get historical commodity price data

    **Query Parameters:**
    - `material`: Commodity type
    - `days`: Number of days of history (default: 90)

    **Returns:**
    - Daily historical prices
    - Moving averages
    - Volatility metrics
    """

    try:
        # Mock historical data
        start_date = date.today() - timedelta(days=days)
        historical_prices = []

        for i in range(days):
            price_date = start_date + timedelta(days=i)
            price = 75.0 + i * 0.1 + (i % 10) * 2  # Mock trend + seasonality

            historical_prices.append({
                "date": price_date.isoformat(),
                "price": round(price, 2)
            })

        return {
            "material": material,
            "period_days": days,
            "data_points": len(historical_prices),
            "prices": historical_prices,
            "statistics": {
                "avg_price": 77.50,
                "min_price": 72.10,
                "max_price": 82.90,
                "volatility": 6.2
            }
        }

    except Exception as e:
        logger.error(f"Failed to get historical prices: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve historical prices"
        )
