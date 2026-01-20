# Scotts Miracle-Gro ML Supply Chain Optimizer

AI-powered supply chain optimization system for commodity ordering, inventory management, and demand forecasting.

## Features

- **Multi-Source Data Integration**: POS data, historical sales, weather forecasts
- **Demand Forecasting**: ML models incorporating seasonality, weather impact, and market trends
- **Inventory Optimization**: Smart projection of inventory levels across stores
- **Commodity Ordering**: Automated optimization of raw material procurement
- **Weather-Aware Planning**: Integration of weather forecasts for demand prediction

## Architecture

```
scotts-ml-supply-chain/
├── models/              # ML models and forecasting engines
│   ├── demand_forecaster.py
│   ├── inventory_optimizer.py
│   └── commodity_planner.py
├── data/               # Data ingestion and processing
│   ├── data_loader.py
│   ├── weather_api.py
│   └── schemas.py
├── api/                # REST API endpoints
│   ├── app.py
│   └── endpoints.py
├── utils/              # Utility functions
│   └── helpers.py
└── examples/           # Usage examples
    └── demo.py
```

## Quick Start

```python
from scotts_ml_supply_chain import SupplyChainOptimizer

# Initialize optimizer
optimizer = SupplyChainOptimizer()

# Load your data
optimizer.load_sales_data('sales.csv')
optimizer.load_inventory_data('inventory.csv')

# Generate forecasts
forecast = optimizer.forecast_demand(horizon_days=90)

# Get commodity ordering recommendations
orders = optimizer.optimize_commodity_orders()

# Project inventory levels
inventory_projection = optimizer.project_inventory(days=60)
```

## Models

### 1. Demand Forecasting
- Time series decomposition (trend, seasonality, residuals)
- Weather impact regression
- Holiday and promotional adjustments
- Store-level and SKU-level predictions

### 2. Inventory Optimization
- Safety stock calculations
- Lead time variability handling
- Multi-echelon optimization
- ABC analysis integration

### 3. Commodity Planning
- Raw material requirement forecasting
- Supplier lead time optimization
- Cost minimization with constraints
- Seasonal procurement strategies

## Data Sources

- **POS Systems**: Real-time sales transactions
- **Historical Sales**: Multi-year trend analysis
- **Weather APIs**: NOAA, OpenWeather integration
- **Inventory Systems**: Current stock levels across locations
- **Supplier Data**: Lead times, pricing, MOQs
