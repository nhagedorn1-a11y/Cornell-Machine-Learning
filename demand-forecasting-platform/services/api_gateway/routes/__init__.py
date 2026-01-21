"""
API Gateway Routes
All API endpoint route modules
"""

from services.api_gateway.routes import (
    health,
    forecasting,
    optimization,
    metrics,
    commodities
)

__all__ = [
    "health",
    "forecasting",
    "optimization",
    "metrics",
    "commodities"
]
