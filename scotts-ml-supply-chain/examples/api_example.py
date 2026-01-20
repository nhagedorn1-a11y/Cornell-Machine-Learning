"""
Example of using the Supply Chain Optimizer API
"""

import requests
import json
from time import sleep


# API Base URL
BASE_URL = "http://localhost:8000"


def print_section(title):
    """Print section header"""
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def main():
    """Demo API usage"""

    print_section("SCOTTS ML SUPPLY CHAIN OPTIMIZER - API DEMO")

    # 1. Health check
    print_section("1. Health Check")
    response = requests.get(f"{BASE_URL}/health")
    print(json.dumps(response.json(), indent=2))

    # 2. Initialize optimizer
    print_section("2. Initialize Optimizer")
    response = requests.post(f"{BASE_URL}/initialize", params={"generate_sample": True})
    print(json.dumps(response.json(), indent=2))
    sleep(2)  # Wait for initialization

    # 3. Generate demand forecast
    print_section("3. Generate Demand Forecast")
    forecast_request = {
        "horizon_days": 90,
        "include_weather": True
    }
    response = requests.post(f"{BASE_URL}/forecast", json=forecast_request)
    result = response.json()

    print(f"Status: {result['status']}")
    print(f"Forecast Points: {result['forecast_points']}")
    print(f"Total Forecasted Demand: {result['total_forecasted_demand']:.2f}")
    print(f"\nSample Forecasts (first 5):")

    for forecast in result['forecasts'][:5]:
        print(f"  - {forecast['product_sku']} on {forecast['forecast_date']}: "
              f"{forecast['predicted_quantity']:.2f} units")

    # 4. Optimize inventory
    print_section("4. Optimize Inventory")
    inventory_request = {
        "service_level": 0.95
    }
    response = requests.post(f"{BASE_URL}/inventory/optimize", json=inventory_request)
    result = response.json()

    print(f"Status: {result['status']}")
    print(f"Products Optimized: {result['products_optimized']}")
    print(f"Service Level: {result['service_level']}")

    if result['policies']:
        print(f"\nSample Policies (first 3):")
        for policy in result['policies'][:3]:
            print(f"\n  Product: {policy['product_sku']}")
            print(f"  Avg Daily Demand: {policy['avg_daily_demand']:.2f}")
            print(f"  Safety Stock: {policy['safety_stock']}")
            print(f"  Reorder Point: {policy['reorder_point']}")
            print(f"  Order Quantity: {policy['order_quantity']}")

    # 5. Project inventory levels
    print_section("5. Project Inventory Levels")
    response = requests.post(f"{BASE_URL}/inventory/project", params={"horizon_days": 60})
    result = response.json()

    print(f"Status: {result['status']}")
    print(f"Projection Points: {result['projection_points']}")

    if result['projections']:
        # Find high-risk items
        high_risk = [p for p in result['projections'] if p['stockout_risk'] >= 0.5]

        print(f"\nHigh Stockout Risk Items: {len(high_risk)}")
        for proj in high_risk[:3]:
            print(f"  - {proj.get('product_sku', 'N/A')} on {proj['date']}: "
                  f"{proj['projected_inventory']} units (risk: {proj['stockout_risk']:.2f})")

    # 6. Plan commodity procurement
    print_section("6. Plan Commodity Procurement")
    commodity_request = {
        "planning_horizon_days": 90
    }
    response = requests.post(f"{BASE_URL}/commodities/plan", json=commodity_request)
    result = response.json()

    print(f"Status: {result['status']}")
    print(f"Total Orders: {result['total_orders']}")
    print(f"Total Cost: ${result['total_cost']:,.2f}")
    print(f"Urgent Orders: {result['urgent_orders_count']}")

    if result['orders']:
        print(f"\nRecommended Orders:")
        for order in result['orders'][:5]:
            print(f"\n  {order['commodity_name']}")
            print(f"  Quantity: {order['recommended_quantity']} {order['units']}")
            print(f"  Cost: ${order['estimated_cost']:,.2f}")
            print(f"  Urgency: {order['urgency_score']:.2f}")
            print(f"  Order by: {order['order_by_date']}")

    # 7. Get executive summary
    print_section("7. Executive Summary")
    response = requests.get(f"{BASE_URL}/summary")
    summary = response.json()

    print("\nData Summary:")
    if summary.get('data_summary'):
        for key, value in summary['data_summary'].items():
            print(f"  {key}: {value}")

    print("\nForecast Summary:")
    if summary.get('forecast_summary'):
        for key, value in summary['forecast_summary'].items():
            print(f"  {key}: {value}")

    print("\nProcurement Summary:")
    if summary.get('procurement_summary'):
        for key, value in summary['procurement_summary'].items():
            print(f"  {key}: {value}")

    # 8. Export results
    print_section("8. Export Results")
    response = requests.post(f"{BASE_URL}/export", params={"output_dir": "./api_output"})
    print(json.dumps(response.json(), indent=2))

    print_section("API DEMO COMPLETE")
    print("\nAll API endpoints tested successfully!")
    print("Check ./api_output/ for exported results")


if __name__ == "__main__":
    print("\nMake sure the API server is running:")
    print("  python api/app.py")
    print("\nThen run this script to test the API.\n")

    try:
        main()
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to API server.")
        print("Please start the API server first:")
        print("  python api/app.py")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
