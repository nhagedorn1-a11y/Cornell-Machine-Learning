"""
Simplified demo that works reliably with the current system
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supply_chain_optimizer import SupplyChainOptimizer
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def print_banner(title):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def print_section(title):
    print("\n" + "-" * 80)
    print(title)
    print("-" * 80)


def main():
    print_banner("SCOTTS MIRACLE-GRO ML SUPPLY CHAIN OPTIMIZER - SIMPLIFIED DEMO")

    # Initialize
    print_section("Step 1: Initialize System")
    optimizer = SupplyChainOptimizer()

    # Generate sample data
    print_section("Step 2: Generate Artificial Data")
    print("Creating realistic sales patterns for gardening products...")

    optimizer.generate_sample_data(
        num_stores=5,
        num_products=10,
        days_history=365
    )

    print(f"\n📊 Data Summary:")
    print(f"   Products: {optimizer.sales_data['product_sku'].nunique()}")
    print(f"   Stores: {optimizer.sales_data['store_id'].nunique()}")
    print(f"   Sales Records: {len(optimizer.sales_data):,}")
    print(f"   Total Revenue: ${optimizer.sales_data['revenue'].sum():,.2f}")
    print(f"   Avg Daily Sales/Product: {optimizer.sales_data.groupby('product_sku')['quantity'].mean().mean():.1f} units")

    # Show seasonal pattern
    print(f"\n🌱 Seasonal Sales Pattern:")
    monthly = optimizer.sales_data.copy()
    monthly['month'] = pd.to_datetime(monthly['date']).dt.month
    monthly_sales = monthly.groupby('month')['quantity'].sum()
    for month in [3, 6, 9, 12]:  # Spring, Summer, Fall, Winter
        season_name = {3: "Spring", 6: "Summer", 9: "Fall", 12: "Winter"}[month]
        print(f"   {season_name:8s} (Month {month:2d}): {monthly_sales.get(month, 0):,} units")

    # Optimize inventory policies
    print_section("Step 3: Optimize Inventory Policies")
    print("Calculating optimal safety stock and reorder points...")

    policies = optimizer.optimize_inventory(service_level=0.95)

    print(f"\n✅ Optimized policies for {len(policies)} products")
    print(f"\nTop 3 Products by Daily Demand:")
    print(policies[['product_sku', 'avg_daily_demand', 'safety_stock',
                    'reorder_point', 'order_quantity']].head(3).to_string(index=False))

    # Show cost analysis
    print(f"\n💰 Total Annual Cost Optimization:")
    print(f"   Total Holding Cost: ${policies['holding_cost'].sum():,.2f}/year")
    print(f"   Total Ordering Cost: ${policies['ordering_cost'].sum():,.2f}/year")
    print(f"   Combined Total: ${policies['total_annual_cost'].sum():,.2f}/year")

    # Simple demand projection
    print_section("Step 4: Demand Projection (Simple Method)")
    print("Projecting next 30 days of demand...")

    # Use simple historical average method for demo
    products = optimizer.sales_data['product_sku'].unique()[:5]
    forecast_records = []

    for product in products:
        product_sales = optimizer.sales_data[optimizer.sales_data['product_sku'] == product]
        avg_daily = product_sales['quantity'].mean()
        std_daily = product_sales['quantity'].std()

        for day in range(30):
            date = datetime.now() + timedelta(days=day)

            # Add seasonality
            month = date.month
            if month in [3, 4, 5]:  # Spring
                seasonal_factor = 1.8
            elif month in [6, 7, 8]:  # Summer
                seasonal_factor = 1.4
            else:
                seasonal_factor = 1.0

            predicted = avg_daily * seasonal_factor

            forecast_records.append({
                'product_sku': product,
                'forecast_date': date,
                'predicted_quantity': round(predicted, 1),
                'confidence_lower': round(max(0, predicted - 1.96 * std_daily), 1),
                'confidence_upper': round(predicted + 1.96 * std_daily, 1)
            })

    simple_forecast = pd.DataFrame(forecast_records)

    print(f"✅ Generated {len(simple_forecast)} daily forecasts")
    print(f"\nSample Forecasts:")
    print(simple_forecast.head(10)[['product_sku', 'forecast_date', 'predicted_quantity']].to_string(index=False))

    # Inventory projection
    print_section("Step 5: Inventory Health Check")
    print("Analyzing current inventory levels...")

    inv_summary = []
    for product in products:
        inv = optimizer.inventory_data[optimizer.inventory_data['product_sku'] == product].iloc[0]
        policy = policies[policies['product_sku'] == product].iloc[0]

        days_of_supply = inv['quantity_on_hand'] / max(policy['avg_daily_demand'], 1)
        status = "✅ Healthy" if days_of_supply > 14 else "⚠️  Low"

        inv_summary.append({
            'Product': product,
            'On Hand': int(inv['quantity_on_hand']),
            'Reorder Point': policy['reorder_point'],
            'Days Supply': round(days_of_supply, 1),
            'Status': status
        })

    inv_df = pd.DataFrame(inv_summary)
    print(f"\n{inv_df.to_string(index=False)}")

    # Commodity planning
    print_section("Step 6: Commodity Procurement Planning")
    print("Calculating raw material requirements...")

    # Define product requirements (simplified)
    total_demand = simple_forecast['predicted_quantity'].sum()

    commodities = [
        {'name': 'Nitrogen', 'kg_per_unit': 0.15, 'price': 0.50},
        {'name': 'Phosphorus', 'kg_per_unit': 0.10, 'price': 0.75},
        {'name': 'Potassium', 'kg_per_unit': 0.08, 'price': 0.60},
        {'name': 'Organic Matter', 'kg_per_unit': 0.20, 'price': 0.30},
    ]

    print(f"\n📦 Commodity Orders Needed (30-day horizon):")
    print(f"   Total Product Units Needed: {total_demand:,.0f}")
    print()

    total_cost = 0
    for commodity in commodities:
        qty_needed = total_demand * commodity['kg_per_unit'] * 1.15  # 15% buffer
        cost = qty_needed * commodity['price']
        total_cost += cost

        urgency = "🔴 HIGH" if qty_needed > 2000 else "🟡 MED" if qty_needed > 1000 else "🟢 LOW"

        print(f"   {commodity['name']:15s}: {qty_needed:>8,.0f} kg  @  ${commodity['price']:.2f}/kg  =  ${cost:>10,.2f}  {urgency}")

    print(f"\n   {'TOTAL':15s}: {'':>8s}     {'':>7s}      ${total_cost:>10,.2f}")

    # Key insights
    print_section("Step 7: Key Insights & Recommendations")

    # Find highest demand products
    top_product = policies.nlargest(1, 'avg_daily_demand').iloc[0]

    # Find products needing reorder
    reorder_needed = []
    for _, inv in optimizer.inventory_data.iterrows():
        policy_row = policies[policies['product_sku'] == inv['product_sku']]
        if len(policy_row) > 0:
            if inv['quantity_on_hand'] <= policy_row.iloc[0]['reorder_point']:
                reorder_needed.append(inv['product_sku'])

    print("\n🎯 Strategic Recommendations:")
    print()
    print(f"1. INVENTORY OPTIMIZATION")
    print(f"   • Top selling product: {top_product['product_sku']} ({top_product['avg_daily_demand']:.1f} units/day)")
    print(f"   • {len(reorder_needed)} products need reordering now")
    print(f"   • Maintain 95% service level with optimized safety stock")
    print()

    print(f"2. PROCUREMENT PLANNING")
    print(f"   • Order ${total_cost:,.2f} in raw materials for next 30 days")
    print(f"   • Focus on nitrogen and organic matter (highest volume)")
    print(f"   • 15% safety buffer included for demand variability")
    print()

    print(f"3. SEASONAL STRATEGY")
    current_month = datetime.now().month
    if current_month in [3, 4, 5]:
        print(f"   • Currently in SPRING (peak season)")
        print(f"   • Increase stock levels by 80% vs baseline")
        print(f"   • Prioritize fertilizer and soil products")
    elif current_month in [6, 7, 8]:
        print(f"   • Currently in SUMMER (high season)")
        print(f"   • Maintain elevated inventory levels (+40%)")
        print(f"   • Focus on pest control and plant food")
    else:
        print(f"   • Currently in OFF-SEASON")
        print(f"   • Reduce inventory to avoid holding costs")
        print(f"   • Prepare for spring ramp-up")
    print()

    print(f"4. COST OPTIMIZATION")
    avg_order_cost = policies['total_annual_cost'].mean()
    print(f"   • Average annual cost per product: ${avg_order_cost:,.2f}")
    print(f"   • Consolidate orders to reduce ordering costs")
    print(f"   • Consider volume discounts for high-volume commodities")

    # Export results
    print_section("Step 8: Export Results")

    os.makedirs('./demo_output', exist_ok=True)

    # Export forecast
    simple_forecast.to_csv('./demo_output/demand_forecast.csv', index=False)
    print("✅ Saved demand_forecast.csv")

    # Export policies
    policies.to_csv('./demo_output/inventory_policies.csv', index=False)
    print("✅ Saved inventory_policies.csv")

    # Export inventory status
    inv_df.to_csv('./demo_output/inventory_status.csv', index=False)
    print("✅ Saved inventory_status.csv")

    print_banner("DEMO COMPLETE!")

    print("\n✨ What This Demo Showed:")
    print("   • Generated realistic artificial sales data with seasonality")
    print("   • Optimized inventory policies (safety stock, reorder points)")
    print("   • Projected demand for next 30 days")
    print("   • Calculated commodity procurement requirements")
    print("   • Generated actionable insights and recommendations")
    print()
    print("📁 Results saved to: ./demo_output/")
    print()
    print("🚀 Next Steps:")
    print("   1. Review the CSV files in demo_output/")
    print("   2. Try adjusting the service level or planning horizon")
    print("   3. Load your own real data using optimizer.load_sales_data()")
    print("   4. Deploy the API for production integration")
    print()


if __name__ == "__main__":
    main()
