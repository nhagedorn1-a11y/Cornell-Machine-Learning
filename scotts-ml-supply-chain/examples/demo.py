"""
Demo script showing complete workflow of Scotts ML Supply Chain Optimizer
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supply_chain_optimizer import SupplyChainOptimizer
import pandas as pd


def main():
    """Run complete demo workflow"""

    print("=" * 80)
    print("SCOTTS MIRACLE-GRO ML SUPPLY CHAIN OPTIMIZER - DEMO")
    print("=" * 80)
    print()

    # Initialize optimizer
    print("STEP 1: Initialize Optimizer")
    print("-" * 80)
    optimizer = SupplyChainOptimizer()
    print()

    # Generate sample data
    print("STEP 2: Generate Sample Data")
    print("-" * 80)
    optimizer.generate_sample_data(
        num_stores=10,
        num_products=20,
        days_history=365
    )
    print()

    # Generate demand forecast
    print("STEP 3: Generate Demand Forecast")
    print("-" * 80)
    forecast = optimizer.forecast_demand(
        horizon_days=90,
        include_weather=True,
        train_model=True
    )

    print("\nSample Forecast:")
    print(forecast.head(10))
    print()

    # Optimize inventory
    print("STEP 4: Optimize Inventory Policies")
    print("-" * 80)
    inventory_policies = optimizer.optimize_inventory(
        service_level=0.95
    )

    print("\nSample Inventory Policies:")
    print(inventory_policies.head(5))
    print()

    # Project inventory levels
    print("STEP 5: Project Inventory Levels")
    print("-" * 80)
    projections = optimizer.project_inventory_levels(
        horizon_days=60
    )

    if len(projections) > 0:
        print("\nSample Inventory Projections:")
        print(projections.head(10))

        # Show stockout risks
        high_risk = projections[projections['stockout_risk'] >= 0.5]
        if len(high_risk) > 0:
            print(f"\n⚠️  Found {len(high_risk)} high stockout risk items:")
            print(high_risk[['product_sku', 'date', 'projected_inventory',
                           'stockout_risk']].head())
    print()

    # Plan commodity orders
    print("STEP 6: Plan Commodity Procurement")
    print("-" * 80)
    orders = optimizer.plan_commodity_orders(
        planning_horizon_days=90
    )

    if orders:
        print(f"\nGenerated {len(orders)} commodity orders:")
        for i, order in enumerate(orders[:5], 1):
            print(f"\n{i}. {order['commodity_name']}")
            print(f"   Quantity: {order['recommended_quantity']} {order['units']}")
            print(f"   Cost: ${order['estimated_cost']:,.2f}")
            print(f"   Urgency: {order['urgency_score']:.2f}")
            print(f"   Order by: {order['order_by_date']}")
            print(f"   Reasoning: {order['reasoning']}")
    print()

    # Generate executive summary
    print("STEP 7: Generate Executive Summary")
    print("-" * 80)
    summary = optimizer.generate_executive_summary()

    print("\nEXECUTIVE SUMMARY")
    print("-" * 80)

    if summary.get('data_summary'):
        print("\nData Summary:")
        for key, value in summary['data_summary'].items():
            print(f"  {key}: {value}")

    if summary.get('forecast_summary'):
        print("\nForecast Summary:")
        for key, value in summary['forecast_summary'].items():
            print(f"  {key}: {value}")

    if summary.get('procurement_summary'):
        print("\nProcurement Summary:")
        for key, value in summary['procurement_summary'].items():
            print(f"  {key}: {value}")

    print()

    # Export results
    print("STEP 8: Export Results")
    print("-" * 80)
    optimizer.export_results(output_dir="./demo_output")
    print()

    print("=" * 80)
    print("DEMO COMPLETE!")
    print("=" * 80)
    print("\nKey Outputs:")
    print("1. Demand forecasts for 90 days with weather integration")
    print("2. Optimized inventory policies (safety stock, reorder points)")
    print("3. Projected inventory levels with stockout risk analysis")
    print("4. Commodity procurement recommendations with urgency scores")
    print("5. All results exported to ./demo_output/")
    print()
    print("Next Steps:")
    print("- Review exported CSV files in ./demo_output/")
    print("- Adjust parameters (service level, lead times, etc.)")
    print("- Integrate with your actual data sources")
    print("- Deploy API for real-time optimization")
    print()


if __name__ == "__main__":
    main()
