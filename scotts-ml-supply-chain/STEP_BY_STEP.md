# Step-by-Step Demo Guide

## ✅ Prerequisites

- Python 3.8 or higher
- Terminal/Command Line access

## 📋 Quick Run (5 Minutes)

### Step 1: Open Terminal

Navigate to the project directory:

```bash
cd Cornell-Machine-Learning/scotts-ml-supply-chain
```

### Step 2: Install Dependencies

```bash
pip install numpy pandas scikit-learn scipy joblib
```

Expected output:
```
Successfully installed numpy-1.24.3 pandas-2.0.3 scikit-learn-1.3.0 scipy-1.11.0 joblib-1.3.0
```

### Step 3: Run the Demo

```bash
python3 examples/simple_demo.py
```

⏱️ **Runtime**: ~10 seconds

## 📊 What You'll See

### Output 1: Data Generation (3 seconds)

```
Step 2: Generate Artificial Data
Creating realistic sales patterns for gardening products...

📊 Data Summary:
   Products: 10
   Stores: 5
   Sales Records: 17,911
   Total Revenue: $3,355,397.42
   Avg Daily Sales/Product: 6.2 units

🌱 Seasonal Sales Pattern:
   Spring   (Month  3): 15,274 units  ← Peak season (2x normal)
   Summer   (Month  6): 10,759 units  ← High season (1.5x)
   Fall     (Month  9): 8,299 units   ← Moderate (1.2x)
   Winter   (Month 12): 3,988 units   ← Low season (0.6x)
```

**What this shows**: The system generates realistic sales data with seasonal patterns matching typical gardening product demand.

### Output 2: Inventory Optimization (2 seconds)

```
Step 3: Optimize Inventory Policies
Calculating optimal safety stock and reorder points...

✅ Optimized policies for 10 products

Top 3 Products by Daily Demand:
product_sku  avg_daily_demand  safety_stock  reorder_point  order_quantity
   PROD-000              6.32            19             64             304
   PROD-001              6.23            19             63             302
   PROD-002              6.08            18             61             298

💰 Total Annual Cost Optimization:
   Total Holding Cost: $8,485.00/year
   Total Ordering Cost: $7,530.82/year
   Combined Total: $16,015.82/year
```

**What this shows**:
- **Safety Stock**: Buffer inventory to handle demand variability
- **Reorder Point**: Trigger level for placing new orders (64 units)
- **Order Quantity**: Optimal order size (304 units via Economic Order Quantity formula)
- **Costs**: Balanced holding vs. ordering costs

### Output 3: Demand Forecasting (2 seconds)

```
Step 4: Demand Projection (Simple Method)
Projecting next 30 days of demand...

✅ Generated 150 daily forecasts

Sample Forecasts:
product_sku              forecast_date  predicted_quantity
   PROD-000 2026-01-20 23:41:40         6.3
   PROD-000 2026-01-21 23:41:40         6.3
   PROD-000 2026-01-22 23:41:40         6.3
```

**What this shows**: Daily demand predictions for the next 30 days with seasonality adjustments.

### Output 4: Inventory Health Check (1 second)

```
Step 5: Inventory Health Check
Analyzing current inventory levels...

 Product  On Hand  Reorder Point  Days Supply    Status
PROD-000      186             64         29.4 ✅ Healthy
PROD-001      182             63         29.2 ✅ Healthy
PROD-002      173             61         28.5 ✅ Healthy
```

**What this shows**:
- Current stock levels
- Days of supply remaining (29 days is healthy)
- Status indicators (✅ Healthy = >14 days, ⚠️ Low = <14 days)

### Output 5: Commodity Planning (1 second)

```
Step 6: Commodity Procurement Planning
Calculating raw material requirements...

📦 Commodity Orders Needed (30-day horizon):
   Total Product Units Needed: 927

   Nitrogen       :      160 kg  @  $0.50/kg  =  $79.95   🟢 LOW
   Phosphorus     :      107 kg  @  $0.75/kg  =  $79.95   🟢 LOW
   Potassium      :       85 kg  @  $0.60/kg  =  $51.17   🟢 LOW
   Organic Matter :      213 kg  @  $0.30/kg  =  $63.96   🟢 LOW

   TOTAL          :                            $275.04
```

**What this shows**:
- Raw material requirements based on demand forecast
- Bill of materials (e.g., 0.15 kg nitrogen per product unit)
- Cost calculations
- Urgency indicators:
  - 🔴 HIGH = >2000 kg (order immediately)
  - 🟡 MED = 1000-2000 kg (order within 2 weeks)
  - 🟢 LOW = <1000 kg (monitor)

### Output 6: Strategic Insights (1 second)

```
Step 7: Key Insights & Recommendations

🎯 Strategic Recommendations:

1. INVENTORY OPTIMIZATION
   • Top selling product: PROD-005 (6.5 units/day)
   • 0 products need reordering now
   • Maintain 95% service level with optimized safety stock

2. PROCUREMENT PLANNING
   • Order $275.04 in raw materials for next 30 days
   • Focus on nitrogen and organic matter (highest volume)
   • 15% safety buffer included for demand variability

3. SEASONAL STRATEGY
   • Currently in OFF-SEASON
   • Reduce inventory to avoid holding costs
   • Prepare for spring ramp-up

4. COST OPTIMIZATION
   • Average annual cost per product: $1,601.58
   • Consolidate orders to reduce ordering costs
   • Consider volume discounts for high-volume commodities
```

**What this shows**: AI-generated actionable recommendations for supply chain management.

## 📁 Output Files

After completion, check the `demo_output/` folder:

```bash
ls -lh demo_output/
```

You'll see:
- **demand_forecast.csv** - 30-day demand predictions for all products
- **inventory_policies.csv** - Optimized safety stock, reorder points, EOQ
- **inventory_status.csv** - Current inventory health report

### View the Forecast

```bash
head -20 demo_output/demand_forecast.csv
```

Example:
```csv
product_sku,forecast_date,predicted_quantity,confidence_lower,confidence_upper
PROD-000,2026-01-21,6.3,0.0,14.5
PROD-000,2026-01-22,6.3,0.0,14.5
PROD-000,2026-01-23,6.3,0.0,14.5
```

**Columns explained**:
- `predicted_quantity`: Expected daily sales
- `confidence_lower/upper`: 95% confidence interval

### View Inventory Policies

```bash
cat demo_output/inventory_policies.csv
```

Key columns:
- `safety_stock`: Buffer inventory for unexpected demand
- `reorder_point`: When to place new order
- `order_quantity`: How much to order (EOQ)
- `total_annual_cost`: Minimized total cost

## 🎯 Understanding the Results

### How the Artificial Data Works

The demo creates realistic patterns by:

1. **Base Demand**: Random daily sales (Poisson distribution, mean=5)
2. **Seasonality**: Multipliers by season
   - Spring (Mar-May): 2.0x (peak planting season)
   - Summer (Jun-Aug): 1.5x (maintenance season)
   - Fall (Sep-Oct): 1.2x (fall planting)
   - Winter (Nov-Feb): 0.6x (low season)
3. **Weather**: Temperature, rainfall, growing degree days
4. **Multiple Products**: 10 different gardening products
5. **Multi-Location**: 5 different store locations

### Key Metrics Explained

| Metric | Meaning | Good Value |
|--------|---------|------------|
| Days of Supply | How long inventory lasts | 14-45 days |
| Service Level | % chance of being in-stock | 95-99% |
| Safety Stock | Buffer for uncertainty | 1-2 weeks demand |
| Reorder Point | When to trigger order | Lead time + safety |
| Order Quantity | Optimal order size | Balances costs |
| Holding Cost | Cost to store inventory | Minimize |
| Ordering Cost | Cost per order placed | Minimize |

### Decision Guide

**If Days of Supply < 14 days**:
- ⚠️ Risk of stockout
- Action: Place order immediately
- Increase safety stock

**If Days of Supply > 45 days**:
- ⚠️ Excess inventory cost
- Action: Reduce next order
- Review demand forecast

**If Order Quantity seems high**:
- May indicate: High ordering costs
- Solution: Negotiate lower minimum order quantities
- Or: Find suppliers with lower ordering costs

**If Total Annual Cost is high**:
- Check: Is holding cost or ordering cost higher?
- If holding: Order less frequently
- If ordering: Order more frequently

## 🔧 Customization

### Change Planning Horizon

Edit `examples/simple_demo.py` line 74:

```python
# Change from 30 days to 90 days
for day in range(90):  # Was: range(30)
```

### Change Service Level

Edit `examples/simple_demo.py` line 48:

```python
# Change from 95% to 98% (fewer stockouts, higher costs)
policies = optimizer.optimize_inventory(service_level=0.98)
```

### More Products/Stores

Edit `examples/simple_demo.py` line 27:

```python
optimizer.generate_sample_data(
    num_stores=10,    # Increase from 5
    num_products=20,  # Increase from 10
    days_history=730  # 2 years instead of 1
)
```

### Change Commodity Prices

Edit `examples/simple_demo.py` line 103:

```python
commodities = [
    {'name': 'Nitrogen', 'kg_per_unit': 0.15, 'price': 0.75},  # Increase from 0.50
    # ... update other prices
]
```

## 🚀 Next Steps

### 1. Review the Data

Open the CSV files in Excel or Google Sheets:

```bash
# Mac
open demo_output/demand_forecast.csv

# Linux
xdg-open demo_output/demand_forecast.csv

# Windows
start demo_output/demand_forecast.csv
```

### 2. Run with Different Parameters

Try different scenarios:

```bash
# High service level (fewer stockouts)
# Edit service_level to 0.98 in simple_demo.py
python3 examples/simple_demo.py

# Longer planning horizon
# Edit range(30) to range(90)
python3 examples/simple_demo.py
```

### 3. Load Your Real Data

Create a Python script:

```python
from supply_chain_optimizer import SupplyChainOptimizer

optimizer = SupplyChainOptimizer()

# Load your actual data files
optimizer.load_sales_data('path/to/sales.csv')
optimizer.load_inventory_data('path/to/inventory.csv')

# Run optimization
policies = optimizer.optimize_inventory()
print(policies)
```

### 4. Deploy the API

Start the REST API server:

```bash
python3 api/app.py
```

Then visit http://localhost:8000/docs for interactive API documentation.

## ❓ Troubleshooting

### Issue: Command not found

```
python3: command not found
```

**Solution**: Try `python` instead of `python3`:

```bash
python examples/simple_demo.py
```

### Issue: Module not found

```
ModuleNotFoundError: No module named 'pandas'
```

**Solution**: Install dependencies:

```bash
pip install pandas numpy scikit-learn scipy joblib
```

If `pip` doesn't work, try `pip3`:

```bash
pip3 install pandas numpy scikit-learn scipy joblib
```

### Issue: Permission denied

```
Permission denied: 'demo_output'
```

**Solution**: Create directory manually:

```bash
mkdir -p demo_output
chmod 755 demo_output
python3 examples/simple_demo.py
```

### Issue: Demo takes too long

If it takes >30 seconds:

**Solution**: Reduce data size in line 27 of `simple_demo.py`:

```python
optimizer.generate_sample_data(
    num_stores=3,     # Reduce from 5
    num_products=5,   # Reduce from 10
    days_history=180  # Reduce from 365
)
```

## 📚 Additional Resources

- **Full Documentation**: See `README.md`
- **API Guide**: See `api/README.md`
- **Quick Start**: See `QUICKSTART.md`
- **Advanced Demo**: Try `examples/demo.py` (uses ML forecasting)

## 🎉 Success!

You've successfully run the Scotts ML Supply Chain Optimizer demo!

The system has:
- ✅ Generated realistic artificial sales data
- ✅ Optimized inventory policies
- ✅ Forecasted demand for 30 days
- ✅ Calculated commodity requirements
- ✅ Generated strategic recommendations
- ✅ Exported results to CSV files

You're now ready to integrate this with real Scotts Miracle-Gro data!
