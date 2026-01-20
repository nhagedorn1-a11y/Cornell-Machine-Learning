# Examples

This directory contains example scripts demonstrating the Scotts ML Supply Chain Optimizer.

## Running the Examples

### 1. Basic Demo (demo.py)

Complete end-to-end demonstration of all features:

```bash
cd scotts-ml-supply-chain
python examples/demo.py
```

This will:
- Generate sample data
- Train forecasting models
- Optimize inventory policies
- Project inventory levels
- Generate commodity procurement plans
- Export all results to `./demo_output/`

### 2. API Demo (api_example.py)

Demonstrates using the REST API:

**Step 1:** Start the API server
```bash
python api/app.py
```

**Step 2:** In another terminal, run the API example
```bash
python examples/api_example.py
```

This will test all API endpoints and export results to `./api_output/`

## Interactive API Documentation

Once the API server is running, visit:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## Custom Usage

### Loading Your Own Data

```python
from supply_chain_optimizer import SupplyChainOptimizer

optimizer = SupplyChainOptimizer()

# Load your actual data
optimizer.load_sales_data('path/to/sales.csv')
optimizer.load_inventory_data('path/to/inventory.csv')
optimizer.load_weather_data('path/to/weather.csv')

# Run analyses
forecast = optimizer.forecast_demand(horizon_days=90)
policies = optimizer.optimize_inventory()
orders = optimizer.plan_commodity_orders()
```

### Expected CSV Formats

**sales.csv:**
```csv
transaction_id,store_id,product_sku,quantity,revenue,timestamp,location_zip,date
TXN-001,STORE-001,PROD-001,5,125.50,2024-01-15 10:30:00,43215,2024-01-15
```

**inventory.csv:**
```csv
store_id,product_sku,quantity_on_hand,quantity_on_order,reorder_point,max_stock_level,last_restock_date,daily_sales_avg,snapshot_date,date
STORE-001,PROD-001,150,50,75,300,2024-01-10,5.2,2024-01-15,2024-01-15
```

**weather.csv:**
```csv
location_zip,date,temperature_avg,temperature_max,temperature_min,precipitation_inches,humidity_percent,sunshine_hours
43215,2024-01-15,45.5,52.0,39.0,0.1,65.0,8.5
```

## Tips

1. **Start with sample data** to understand the system before using your own data
2. **Adjust parameters** like service level, lead times, and planning horizons based on your needs
3. **Review feature importance** from the demand forecasting model to understand key drivers
4. **Monitor stockout risks** in inventory projections to prioritize ordering
5. **Use the API** for integration with existing systems
