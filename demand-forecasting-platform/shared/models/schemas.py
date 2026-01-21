"""
Shared Pydantic Models (DTOs)
Data Transfer Objects for API requests/responses
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import date, datetime
from decimal import Decimal
from enum import Enum


# ============================================================================
# Enums
# ============================================================================

class ModelType(str, Enum):
    """Forecast model types"""
    PROPHET = "prophet"
    XGBOOST = "xgboost"
    LSTM = "lstm"
    ENSEMBLE = "ensemble"


class AlertSeverity(str, Enum):
    """Alert severity levels"""
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class InventoryStatus(str, Enum):
    """Inventory status"""
    NORMAL = "normal"
    LOW = "low"
    CRITICAL = "critical"
    EXCESS = "excess"


class TransferStatus(str, Enum):
    """Transfer status"""
    PENDING = "pending"
    IN_TRANSIT = "in_transit"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Priority(str, Enum):
    """Priority levels"""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


# ============================================================================
# Base Models
# ============================================================================

class DateRange(BaseModel):
    """Date range for forecasting"""
    start: date = Field(..., description="Start date (inclusive)")
    end: date = Field(..., description="End date (inclusive)")

    @validator("end")
    def end_after_start(cls, v, values):
        if "start" in values and v < values["start"]:
            raise ValueError("end date must be after start date")
        return v

    @validator("end")
    def max_range_validation(cls, v, values):
        if "start" in values:
            delta = (v - values["start"]).days
            if delta > 365:
                raise ValueError("Date range cannot exceed 365 days")
        return v


class Constraints(BaseModel):
    """Constraints for optimization"""
    budget: Optional[Decimal] = Field(None, description="Budget limit in dollars")
    max_transfers: Optional[int] = Field(None, description="Maximum number of transfers")
    capacity: Optional[Dict[str, int]] = Field(
        None,
        description="Capacity limits per location"
    )


# ============================================================================
# Forecasting Models
# ============================================================================

class ForecastRequest(BaseModel):
    """Request model for demand forecasting"""
    date_range: DateRange
    sku_ids: List[str] = Field(..., min_items=1, description="SKU IDs to forecast")
    location_ids: Optional[List[str]] = Field(
        None,
        description="Location IDs (null = all locations)"
    )
    confidence_level: float = Field(
        default=0.95,
        ge=0.8,
        le=0.99,
        description="Confidence level for prediction intervals"
    )
    model_type: Optional[ModelType] = Field(
        None,
        description="Specific model to use (null = ensemble)"
    )
    include_features: bool = Field(
        default=False,
        description="Include feature importance in response"
    )

    class Config:
        schema_extra = {
            "example": {
                "date_range": {
                    "start": "2026-02-01",
                    "end": "2026-03-31"
                },
                "sku_ids": ["SKU-001", "SKU-002"],
                "location_ids": ["DC-ATL", "DC-CHI"],
                "confidence_level": 0.95
            }
        }


class DemandPrediction(BaseModel):
    """Single demand prediction"""
    date: date
    demand: Decimal = Field(..., description="Predicted demand quantity")
    lower_bound: Decimal = Field(..., description="Lower confidence bound")
    upper_bound: Decimal = Field(..., description="Upper confidence bound")
    recommended_stock: int = Field(
        ...,
        description="Recommended stock level (includes safety stock)"
    )


class SKUForecast(BaseModel):
    """Forecast for a single SKU at a location"""
    sku_id: str
    location_id: str
    predictions: List[DemandPrediction]
    features_used: Optional[Dict[str, float]] = Field(
        None,
        description="Feature importance (if requested)"
    )


class ForecastResponse(BaseModel):
    """Response model for demand forecasting"""
    forecasts: List[SKUForecast]
    metadata: Dict[str, Any] = Field(
        ...,
        description="Model metadata (version, accuracy, etc.)"
    )

    class Config:
        schema_extra = {
            "example": {
                "forecasts": [
                    {
                        "sku_id": "SKU-001",
                        "location_id": "DC-ATL",
                        "predictions": [
                            {
                                "date": "2026-02-01",
                                "demand": 450,
                                "lower_bound": 380,
                                "upper_bound": 520,
                                "recommended_stock": 500
                            }
                        ]
                    }
                ],
                "metadata": {
                    "model_version": "ensemble-v1.2",
                    "forecast_accuracy_mape": 12.3,
                    "generated_at": "2026-01-21T12:00:00Z"
                }
            }
        }


# ============================================================================
# Optimization Models
# ============================================================================

class CurrentInventory(BaseModel):
    """Current inventory levels by location and SKU"""
    # Format: {"DC-ATL": {"SKU-001": 200}, "DC-CHI": {"SKU-001": 800}}
    __root__: Dict[str, Dict[str, int]]


class RebalanceRequest(BaseModel):
    """Request model for inventory rebalancing"""
    current_inventory: CurrentInventory
    constraints: Constraints
    target_date: Optional[date] = Field(
        None,
        description="Target date for optimization (null = today + 30 days)"
    )
    include_procurement: bool = Field(
        default=False,
        description="Include new procurement recommendations"
    )

    class Config:
        schema_extra = {
            "example": {
                "current_inventory": {
                    "DC-ATL": {"SKU-001": 200},
                    "DC-CHI": {"SKU-001": 800}
                },
                "constraints": {
                    "budget": 50000,
                    "max_transfers": 10
                }
            }
        }


class TransferRecommendation(BaseModel):
    """Single transfer recommendation"""
    from_location: str = Field(..., alias="from")
    to_location: str = Field(..., alias="to")
    sku_id: str
    quantity: int
    cost: Decimal
    expected_roi: Decimal = Field(..., description="Expected ROI in dollars")
    priority: Priority
    rationale: str = Field(..., description="Why this transfer is recommended")

    class Config:
        allow_population_by_field_name = True


class ProcurementRecommendation(BaseModel):
    """Procurement (new order) recommendation"""
    sku_id: str
    location_id: str
    quantity: int
    estimated_cost: Decimal
    expected_revenue: Decimal
    deadline: date = Field(..., description="Order by this date")
    supplier_id: Optional[str] = None


class RebalanceResponse(BaseModel):
    """Response model for inventory rebalancing"""
    transfer_recommendations: List[TransferRecommendation]
    procurement_recommendations: Optional[List[ProcurementRecommendation]] = None
    total_cost: Decimal
    expected_roi: Decimal
    summary: Dict[str, Any]

    class Config:
        schema_extra = {
            "example": {
                "transfer_recommendations": [
                    {
                        "from": "DC-CHI",
                        "to": "DC-ATL",
                        "sku_id": "SKU-001",
                        "quantity": 300,
                        "cost": 1200,
                        "expected_roi": 4500,
                        "priority": "HIGH",
                        "rationale": "Atlanta forecast shows 450 unit demand vs 200 stock"
                    }
                ],
                "total_cost": 1200,
                "expected_roi": 4500,
                "summary": {
                    "total_transfers": 1,
                    "roi_percentage": 375
                }
            }
        }


# ============================================================================
# Metrics Models
# ============================================================================

class ForecastAccuracyMetrics(BaseModel):
    """Forecast accuracy metrics"""
    mape: Decimal = Field(..., description="Mean Absolute Percentage Error (%)")
    rmse: Decimal = Field(..., description="Root Mean Squared Error")
    bias: Decimal = Field(..., description="Forecast bias (+ = over, - = under)")
    samples: int = Field(..., description="Number of samples evaluated")


class InventoryHealthMetrics(BaseModel):
    """Inventory health metrics"""
    total_value: Decimal = Field(..., description="Total inventory value ($)")
    turnover_ratio: Decimal = Field(..., description="Inventory turnover ratio")
    stockout_rate: Decimal = Field(..., description="Stockout rate (0-1)")
    excess_inventory_pct: Decimal = Field(
        ...,
        description="Excess inventory percentage"
    )
    days_of_supply: Decimal = Field(..., description="Average days of supply")


class ServiceLevelMetrics(BaseModel):
    """Service level metrics"""
    fill_rate: Decimal = Field(..., description="Fill rate (0-1)")
    on_time_delivery: Decimal = Field(..., description="On-time delivery rate (0-1)")
    perfect_order_rate: Decimal = Field(
        ...,
        description="Perfect order rate (0-1)"
    )


class DashboardMetrics(BaseModel):
    """Complete dashboard metrics"""
    forecast_accuracy: ForecastAccuracyMetrics
    inventory_health: InventoryHealthMetrics
    service_levels: ServiceLevelMetrics
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# Commodity Models
# ============================================================================

class CommodityForecastRequest(BaseModel):
    """Request for commodity price forecasting"""
    material_types: List[str] = Field(
        ...,
        description="Commodity types (e.g., 'steel', 'plastic', 'oil')"
    )
    planning_horizon: int = Field(
        default=90,
        ge=7,
        le=365,
        description="Forecast horizon in days"
    )


class CommodityPricePrediction(BaseModel):
    """Commodity price prediction"""
    date: date
    price: Decimal
    lower_bound: Decimal
    upper_bound: Decimal
    confidence: Decimal = Field(..., description="Confidence level (0-1)")


class ProcurementScheduleItem(BaseModel):
    """Single procurement schedule item"""
    commodity: str
    quantity: Decimal
    order_date: date
    estimated_price: Decimal
    rationale: str


class CommodityForecastResponse(BaseModel):
    """Response for commodity forecasting"""
    price_forecasts: Dict[str, List[CommodityPricePrediction]]
    procurement_schedule: List[ProcurementScheduleItem]
    total_estimated_cost: Decimal
    hedging_recommendations: Optional[List[str]] = None


# ============================================================================
# Weather Alert Models
# ============================================================================

class WeatherAlert(BaseModel):
    """Weather-driven demand alert"""
    severity: AlertSeverity
    region: str
    event_type: str
    forecast_summary: str
    demand_impact_pct: Decimal = Field(
        ...,
        description="Expected demand change (%)"
    )
    revenue_at_risk: Decimal
    recommended_actions: List[str]
    expires_at: datetime


# ============================================================================
# Health Check Models
# ============================================================================

class HealthStatus(BaseModel):
    """Health check status"""
    status: str  # "healthy", "degraded", "unhealthy"
    version: str
    timestamp: datetime
    services: Dict[str, str]  # {"database": "healthy", "redis": "healthy", ...}
    latency_ms: Optional[float] = None
