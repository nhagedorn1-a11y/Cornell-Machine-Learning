# Step-by-Step Demo Guide

This guide will walk you through running the Scotts ML Supply Chain Optimizer demo with artificial data.

## Prerequisites

You need Python 3.8+ installed. Check your version:

```bash
python3 --version
```

## Step 1: Navigate to the Project

```bash
cd Cornell-Machine-Learning/scotts-ml-supply-chain
```

## Step 2: Install Dependencies

Install all required Python packages:

```bash
pip install numpy pandas scikit-learn statsmodels matplotlib seaborn plotly requests fastapi uvicorn pydantic python-dotenv scipy joblib
```

Or use the requirements file:

```bash
pip install -r requirements.txt
```

Expected output:
```
Successfully installed numpy-1.24.3 pandas-2.0.3 scikit-learn-1.3.0 ...
```

## Step 3: Run the Demo

Execute the demo script:

```bash
python examples/demo.py
```

## What Happens During the Demo

### Phase 1: Initialization (5 seconds)
```
✅ Supply Chain Optimizer initialized
```

The system loads all ML models and data processors.

### Phase 2: Generate Artificial Data (10 seconds)
```
Generating sample data for prototype...
✅ Generated sample data:
   - 73,000 sales records (10 stores × 20 products × 365 days)
   - 200 inventory records (10 stores × 20 products)
   - 365 weather records (1 year daily)
```

The system creates realistic synthetic data:
- **Sales data**: Random daily sales with seasonal patterns
  - Spring peak (March-May): 2x normal demand
  - Summer high (June-Aug): 1.5x normal demand
  - Fall moderate (Sep-Oct): 1.2x normal demand
  - Winter low (Nov-Feb): 0.6x normal demand

- **Inventory data**: Current stock levels, reorder points
- **Weather data**: Temperature, precipitation, growing degree days

### Phase 3: Train ML Models (30-60 seconds)
```
📊 Generating 90-day demand forecasts...
   Preparing features...
   Training forecasting models...
   Training models for 50 groups...
   Model performance - MAE: 3.45, RMSE: 5.12
✅ Generated forecasts for 900 product-store-day combinations
```

The system:
- Extracts 100+ features (time, seasonality, weather, lags)
- Trains Gradient Boosting models per product
- Validates accuracy on holdout data
- Generates 90-day forecasts

### Phase 4: Optimize Inventory (10-15 seconds)
```
📦 Optimizing inventory policies (service level: 95%)...
✅ Optimized inventory policies for 20 products
```

For each product, calculates:
- Safety stock (based on demand variability)
- Reorder point (lead time + safety stock)
- Order quantity (Economic Order Quantity)
- Max stock level

### Phase 5: Project Inventory Levels (5-10 seconds)
```
📈 Projecting inventory levels for 60 days...
   No demand forecast available. Generating forecast first...
✅ Generated inventory projections for 10 products
```

Projects future inventory considering:
- Current stock levels
- Forecasted demand
- Pending orders
- Reorder triggers
- Stockout risks

### Phase 6: Plan Commodity Orders (5 seconds)
```
🏭 Planning commodity procurement (90 days)...
   Setting up bill of materials...
   Calculating material requirements...
   Optimizing procurement schedule...
✅ Generated 4 commodity procurement orders
```

The system:
- Maps products to raw materials (nitrogen, phosphorus, potassium)
- Calculates material requirements from demand forecast
- Optimizes order timing based on lead times
- Generates purchase recommendations

### Phase 7: Generate Summary
```
EXECUTIVE SUMMARY
----------------
Data Summary:
  total_sales_records: 73000
  products: 20
  stores: 10
  date_range: 2025-01-21 to 2026-01-20

Forecast Summary:
  forecast_points: 900
  total_forecasted_demand: 45678.5
  forecast_horizon_days: 89

Procurement Summary:
  total_orders: 4
  total_cost: 15234.50
  urgent_orders: 2
```

### Phase 8: Export Results
```
✅ Exported demand forecast to ./demo_output/demand_forecast.csv
✅ Exported inventory projections to ./demo_output/inventory_projections.csv
✅ Exported commodity orders to ./demo_output/commodity_orders.csv
```

## Step 4: Review the Output

Check the generated files:

```bash
ls -lh demo_output/
```

You should see:
```
-rw-r--r-- 1 user user  125K demand_forecast.csv
-rw-r--r-- 1 user user   45K inventory_projections.csv
-rw-r--r-- 1 user user    2K commodity_orders.csv
```

### View Demand Forecast

```bash
head -20 demo_output/demand_forecast.csv
```

Example output:
```csv
product_sku,forecast_date,predicted_quantity,confidence_lower,confidence_upper,confidence_level
PROD-001,2026-01-21,12.5,8.3,16.7,0.95
PROD-001,2026-01-22,11.8,7.9,15.7,0.95
PROD-001,2026-01-23,13.2,9.1,17.3,0.95
```

### View Inventory Projections

```bash
head -20 demo_output/inventory_projections.csv
```

Example output:
```csv
date,projected_inventory,on_order,expected_demand,order_placed,stockout_risk,days_until_stockout,product_sku
2026-01-21,142,50,12.5,0,0.05,11,PROD-001
2026-01-22,130,50,11.8,0,0.05,11,PROD-001
2026-01-23,116,50,13.2,0,0.05,8,PROD-001
```

### View Commodity Orders

```bash
cat demo_output/commodity_orders.csv
```

Example output:
```csv
commodity_id,commodity_name,recommended_quantity,units,estimated_cost,supplier_id,urgency_score,order_by_date,reasoning
nitrogen,Nitrogen,2500.0,kg,1250.00,SUP-001,0.85,2026-01-27,Projected shortage of 1200 units...
phosphorus,Phosphorus,1800.0,kg,1350.00,SUP-002,0.70,2026-02-03,Projected shortage of 850 units...
```

## Step 5: Interpret the Results

### Key Metrics to Look At:

1. **Demand Forecast Accuracy**
   - MAE (Mean Absolute Error): Should be < 5 units
   - RMSE (Root Mean Square Error): Should be < 8 units
   - Lower is better!

2. **Stockout Risks**
   - Risk < 0.2 = Low risk (green)
   - Risk 0.2-0.5 = Moderate risk (yellow)
   - Risk > 0.5 = High risk (red)

3. **Commodity Urgency**
   - Urgency > 0.7 = Order immediately
   - Urgency 0.4-0.7 = Order within 2 weeks
   - Urgency < 0.4 = Monitor, order as needed

4. **Inventory Policy Metrics**
   - Days of Supply: Should be 14-45 days typically
   - Service Level: 95% means 95% in-stock probability
   - Total Annual Cost: Holding + Ordering costs

## Common Issues & Solutions

### Issue: Import Error
```
ImportError: No module named 'sklearn'
```

**Solution:**
```bash
pip install scikit-learn
```

### Issue: Pandas Error
```
ImportError: No module named 'pandas'
```

**Solution:**
```bash
pip install pandas numpy
```

### Issue: No Output Files
```
FileNotFoundError: [Errno 2] No such file or directory: './demo_output/'
```

**Solution:** The script should auto-create the directory, but you can manually create it:
```bash
mkdir -p demo_output
python examples/demo.py
```

### Issue: Script Takes Too Long
If the demo takes more than 2 minutes, reduce the data size:

Edit `examples/demo.py` line 19:
```python
# Change from:
optimizer.generate_sample_data(num_stores=10, num_products=20, days_history=365)

# To:
optimizer.generate_sample_data(num_stores=5, num_products=10, days_history=180)
```

## Step 6: Explore Further

### Try Different Parameters

**Higher Service Level (fewer stockouts, higher inventory costs):**
```python
optimizer.optimize_inventory(service_level=0.98)  # 98% vs 95%
```

**Longer Forecast Horizon:**
```python
forecast = optimizer.forecast_demand(horizon_days=180)  # 6 months vs 3 months
```

**Different Commodity Buffer:**
Edit `supply_chain_optimizer.py` line 379:
```python
mrp = self.commodity_planner.calculate_material_requirements(
    self.demand_forecast,
    buffer_percent=0.20  # 20% buffer instead of 15%
)
```

### View More Details

**Feature Importance:**
```python
importance = optimizer.demand_forecaster.get_feature_importance(top_n=10)
print(importance)
```

Shows which factors drive demand most (temperature, day of week, etc.)

**ABC Classification:**
```python
abc = optimizer.inventory_optimizer.calculate_abc_classification(
    optimizer.sales_data
)
print(abc)
```

Shows which products are high-value (A), medium (B), or low (C)

## Next Steps

1. ✅ Confirm the demo runs successfully
2. 📊 Review the output CSV files
3. 🔧 Try adjusting parameters
4. 📈 Load your real data (see QUICKSTART.md)
5. 🚀 Deploy the API for production use

## Appendix: Understanding the Artificial Data

The demo generates realistic data patterns:

### Seasonal Sales Pattern
```
Winter (Dec-Feb): Base × 0.6  (low season)
Spring (Mar-May): Base × 2.0  (peak season - planting)
Summer (Jun-Aug): Base × 1.5  (high season - maintenance)
Fall (Sep-Oct):   Base × 1.2  (moderate - fall planting)
```

### Weather Simulation
- Temperature varies by season (40°F winter, 80°F summer)
- Precipitation follows exponential distribution (realistic rainfall)
- Growing Degree Days calculated from temperature
- All weather data is location-aware

### Product Mix
- 20 products (fertilizers, soil, pest control, grass seed)
- Each has unique demand patterns
- Products correlate with weather conditions
- Realistic price ranges ($10-$50 per unit)

### Store Network
- 10 stores across different locations
- Each has unique sales volume
- Inventory levels proportional to demand
- Different reorder points per store-product

This creates a realistic test environment that mirrors actual Scotts Miracle-Gro operations!
