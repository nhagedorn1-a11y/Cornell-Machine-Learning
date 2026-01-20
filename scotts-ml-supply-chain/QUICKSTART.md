# Quick Start Guide

Get started with the Scotts ML Supply Chain Optimizer in 5 minutes.

## Installation

```bash
# Clone the repository
cd Cornell-Machine-Learning/scotts-ml-supply-chain

# Install dependencies
pip install -r requirements.txt
```

## Option 1: Quick Demo (Recommended)

Run the complete demo with sample data:

```bash
python examples/demo.py
```

This will:
- ✅ Generate synthetic sales, inventory, and weather data
- ✅ Train ML forecasting models
- ✅ Optimize inventory policies
- ✅ Project future inventory levels
- ✅ Generate commodity procurement recommendations
- ✅ Export all results to `./demo_output/`

**Expected Output:**
```
✅ Supply Chain Optimizer initialized
✅ Generated sample data:
   - 73,000 sales records
   - 200 inventory records
   - 365 weather records
📊 Generating 90-day demand forecasts...
   Training forecasting models...
   Model performance - MAE: 3.45, RMSE: 5.12
✅ Generated forecasts for 900 product-store-day combinations
📦 Optimizing inventory policies (service level: 95%)...
✅ Optimized inventory policies for 20 products
🏭 Planning commodity procurement (90 days)...
✅ Generated 4 commodity procurement orders
```

## Option 2: Python Script

```python
from supply_chain_optimizer import SupplyChainOptimizer

# Initialize
optimizer = SupplyChainOptimizer()

# Generate sample data (or load your own)
optimizer.generate_sample_data()

# Generate 90-day demand forecast
forecast = optimizer.forecast_demand(horizon_days=90)

# Optimize inventory policies
policies = optimizer.optimize_inventory(service_level=0.95)

# Project inventory levels
projections = optimizer.project_inventory_levels(horizon_days=60)

# Plan commodity orders
orders = optimizer.plan_commodity_orders(planning_horizon_days=90)

# Get summary
summary = optimizer.generate_executive_summary()
print(summary)

# Export results
optimizer.export_results("./output")
```

## Option 3: REST API

**Step 1:** Start the API server

```bash
python api/app.py
```

**Step 2:** Use the API

```bash
# Initialize with sample data
curl -X POST "http://localhost:8000/initialize?generate_sample=true"

# Generate forecast
curl -X POST "http://localhost:8000/forecast" \
  -H "Content-Type: application/json" \
  -d '{"horizon_days": 90, "include_weather": true}'

# Optimize inventory
curl -X POST "http://localhost:8000/inventory/optimize" \
  -H "Content-Type: application/json" \
  -d '{"service_level": 0.95}'

# Plan commodities
curl -X POST "http://localhost:8000/commodities/plan" \
  -H "Content-Type: application/json" \
  -d '{"planning_horizon_days": 90}'

# Get summary
curl "http://localhost:8000/summary"
```

**Interactive API Docs:** http://localhost:8000/docs

## Using Your Own Data

### 1. Prepare Your Data Files

**sales.csv:**
```csv
transaction_id,store_id,product_sku,quantity,revenue,timestamp,location_zip,date
TXN-001,STORE-001,FERT-001,5,125.50,2024-01-15 10:30:00,43215,2024-01-15
```

**inventory.csv:**
```csv
store_id,product_sku,quantity_on_hand,quantity_on_order,reorder_point,max_stock_level,last_restock_date,daily_sales_avg,snapshot_date,date
STORE-001,FERT-001,150,50,75,300,2024-01-10,5.2,2024-01-15,2024-01-15
```

### 2. Load and Analyze

```python
from supply_chain_optimizer import SupplyChainOptimizer

optimizer = SupplyChainOptimizer(weather_api_key="your_api_key")  # Optional

# Load your data
optimizer.load_sales_data('data/sales.csv')
optimizer.load_inventory_data('data/inventory.csv')

# Run analysis
forecast = optimizer.forecast_demand(horizon_days=90)
policies = optimizer.optimize_inventory()
orders = optimizer.plan_commodity_orders()

# Export results
optimizer.export_results('./results')
```

## Key Features

### 1. Demand Forecasting
- Multi-model ML approach (Gradient Boosting, Random Forest)
- Weather integration for gardening seasonality
- Trend, seasonality, and lag features
- 90-day rolling forecasts

### 2. Inventory Optimization
- Safety stock calculations
- Reorder point optimization
- Economic Order Quantity (EOQ)
- Stockout risk prediction
- Multi-echelon support

### 3. Commodity Planning
- Material Requirements Planning (MRP)
- Bill of Materials support
- Supplier optimization
- Lead time management
- Order consolidation

## What You'll Get

1. **Demand Forecasts** - Daily predictions for 90+ days
2. **Inventory Policies** - Optimal safety stock and reorder points
3. **Stockout Alerts** - Early warning for potential shortages
4. **Procurement Plans** - When and how much to order
5. **Cost Optimization** - Minimize inventory holding costs
6. **Weather Impact** - Seasonal adjustments for gardening products

## Sample Output Files

After running the demo, check `./demo_output/`:

- `demand_forecast.csv` - Daily demand predictions
- `inventory_projections.csv` - Future inventory levels
- `commodity_orders.csv` - Procurement recommendations

## Next Steps

1. **Review Results** - Check the output files
2. **Adjust Parameters** - Tune service levels, lead times, etc.
3. **Load Real Data** - Replace sample data with actual POS/inventory data
4. **Deploy API** - Integrate with existing systems
5. **Monitor Performance** - Track forecast accuracy over time

## Troubleshooting

**ImportError: No module named 'sklearn'**
```bash
pip install scikit-learn
```

**API won't start**
```bash
pip install fastapi uvicorn
```

**Need weather data**
- Free tier: weatherapi.com
- NOAA: weather.gov/api
- OpenWeather: openweathermap.org

## Support

For questions or issues, see:
- Main README: `../README.md`
- Examples: `examples/README.md`
- API Docs: http://localhost:8000/docs (when running)

## Performance Tips

- Start with 1 year of historical data minimum
- Use 2+ years for better seasonality detection
- Update forecasts weekly for best accuracy
- Monitor MAPE (Mean Absolute Percentage Error) < 20%
- Adjust safety stock for high-value items
