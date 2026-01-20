"""
Data schemas for Scotts ML Supply Chain system
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, List
from enum import Enum


class ProductCategory(Enum):
    """Product categories for Scotts Miracle-Gro"""
    FERTILIZER = "fertilizer"
    SOIL = "soil"
    PEST_CONTROL = "pest_control"
    GRASS_SEED = "grass_seed"
    PLANT_FOOD = "plant_food"
    MULCH = "mulch"
    GARDEN_TOOLS = "garden_tools"


class Season(Enum):
    """Gardening seasons"""
    SPRING = "spring"
    SUMMER = "summer"
    FALL = "fall"
    WINTER = "winter"


@dataclass
class SalesRecord:
    """Point-of-sale sales record"""
    transaction_id: str
    store_id: str
    product_sku: str
    product_category: ProductCategory
    quantity: int
    revenue: float
    timestamp: datetime
    location_zip: str
    promotion_applied: bool = False
    discount_percent: float = 0.0


@dataclass
class InventorySnapshot:
    """Current inventory at a location"""
    store_id: str
    product_sku: str
    quantity_on_hand: int
    quantity_on_order: int
    reorder_point: int
    max_stock_level: int
    last_restock_date: datetime
    daily_sales_avg: float
    snapshot_date: datetime


@dataclass
class WeatherData:
    """Weather information for demand forecasting"""
    location_zip: str
    date: datetime
    temperature_avg: float
    temperature_max: float
    temperature_min: float
    precipitation_inches: float
    humidity_percent: float
    sunshine_hours: float
    season: Season
    growing_degree_days: float  # Important for gardening products


@dataclass
class CommodityData:
    """Raw material/commodity information"""
    commodity_id: str
    commodity_name: str
    unit_price: float
    supplier_id: str
    lead_time_days: int
    minimum_order_quantity: int
    current_inventory: float
    units: str  # tons, gallons, etc.
    price_per_unit: float
    last_order_date: Optional[datetime] = None


@dataclass
class DemandForecast:
    """Forecasted demand output"""
    product_sku: str
    store_id: str
    forecast_date: datetime
    predicted_quantity: float
    confidence_lower: float
    confidence_upper: float
    confidence_level: float = 0.95
    weather_impact_factor: float = 1.0
    seasonality_factor: float = 1.0


@dataclass
class InventoryProjection:
    """Projected inventory level"""
    store_id: str
    product_sku: str
    projection_date: datetime
    projected_quantity: float
    projected_stockout_risk: float
    recommended_reorder_quantity: int
    days_until_stockout: Optional[int] = None


@dataclass
class CommodityOrder:
    """Recommended commodity purchase order"""
    commodity_id: str
    commodity_name: str
    recommended_quantity: float
    units: str
    estimated_cost: float
    supplier_id: str
    urgency_score: float  # 0-1, higher = more urgent
    reasoning: str
    order_by_date: datetime
    expected_usage_start: datetime
    expected_usage_end: datetime


@dataclass
class StoreProfile:
    """Store/location characteristics"""
    store_id: str
    store_name: str
    location_zip: str
    square_footage: int
    climate_zone: str
    population_density: str  # urban, suburban, rural
    avg_monthly_sales: float
    primary_season: Season
    latitude: float
    longitude: float


@dataclass
class HistoricalTrend:
    """Historical sales trends"""
    product_sku: str
    year: int
    month: int
    week: int
    avg_daily_sales: float
    total_sales: float
    total_revenue: float
    year_over_year_growth: Optional[float] = None
    weather_correlation: Optional[float] = None
