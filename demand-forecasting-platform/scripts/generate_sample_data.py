"""
Sample Data Generator
Creates realistic sample data for testing without external dependencies
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.utils.config import settings


def generate_sales_data(
    num_skus: int = 20,
    num_locations: int = 5,
    days: int = 730,  # 2 years
    start_date: str = '2024-01-01'
) -> pd.DataFrame:
    """Generate realistic sales data with seasonality"""

    print(f"Generating sales data: {num_skus} SKUs × {num_locations} locations × {days} days...")

    dates = pd.date_range(start=start_date, periods=days, freq='D')

    records = []

    for sku_idx in range(num_skus):
        sku_id = f"SKU-{str(sku_idx+1).zfill(3)}"

        # SKU-specific characteristics
        base_demand = np.random.randint(50, 300)
        seasonality_strength = np.random.uniform(0.3, 0.8)
        trend = np.random.uniform(-0.1, 0.2)  # -10% to +20% annual trend

        for loc_idx in range(num_locations):
            location_id = f"DC-{['ATL', 'CHI', 'NYC', 'LAX', 'SEA'][loc_idx]}"

            # Location multiplier
            loc_mult = np.random.uniform(0.7, 1.3)

            for day_idx, date in enumerate(dates):
                # Trend component
                trend_factor = 1 + (trend * day_idx / 365)

                # Seasonal component (yearly + monthly cycles)
                month = date.month
                seasonal_factor = 1 + seasonality_strength * np.sin(2 * np.pi * month / 12)

                # Weekly component (weekend effect)
                day_of_week = date.dayofweek
                weekly_factor = 1.2 if day_of_week >= 5 else 1.0

                # Calculate demand
                demand = base_demand * loc_mult * trend_factor * seasonal_factor * weekly_factor

                # Add noise
                noise = np.random.normal(1.0, 0.15)
                demand *= noise

                # Ensure positive
                demand = max(0, int(demand))

                # Price (with some variation)
                unit_price = np.random.uniform(10, 50) * (1 + 0.1 * np.sin(month / 6))

                records.append({
                    'date': date,
                    'sku_id': sku_id,
                    'location_id': location_id,
                    'quantity': demand,
                    'unit_price': round(unit_price, 2),
                    'total_price': round(demand * unit_price, 2),
                    'channel': np.random.choice(['online', 'in-store', 'wholesale'], p=[0.4, 0.5, 0.1])
                })

    df = pd.DataFrame(records)

    print(f"✓ Generated {len(df):,} sales records")

    return df


def generate_weather_data(
    locations: list,
    days: int = 730,
    start_date: str = '2024-01-01'
) -> pd.DataFrame:
    """Generate realistic weather data"""

    print(f"Generating weather data for {len(locations)} locations...")

    dates = pd.date_range(start=start_date, periods=days, freq='D')

    # Location-specific base temperatures
    base_temps = {
        'DC-ATL': 65,
        'DC-CHI': 50,
        'DC-NYC': 55,
        'DC-LAX': 70,
        'DC-SEA': 52
    }

    records = []

    for location_id in locations:
        base_temp = base_temps.get(location_id, 60)

        for date in dates:
            # Seasonal temperature variation
            day_of_year = date.timetuple().tm_yday
            seasonal_temp = base_temp + 20 * np.sin(2 * np.pi * (day_of_year - 80) / 365)

            # Daily variation
            temp = seasonal_temp + np.random.normal(0, 5)

            # Precipitation (more in spring/fall)
            precip_prob = 0.1 + 0.15 * np.sin(2 * np.pi * day_of_year / 365)
            precipitation = np.random.exponential(0.3) if np.random.random() < precip_prob else 0

            records.append({
                'date': date,
                'location_id': location_id,
                'temperature_f': round(temp, 1),
                'precipitation_inches': round(precipitation, 2),
                'humidity_pct': round(np.random.uniform(40, 80), 1),
                'wind_speed_mph': round(np.random.uniform(0, 15), 1),
                'weather_condition': 'rainy' if precipitation > 0.1 else 'sunny'
            })

    df = pd.DataFrame(records)

    print(f"✓ Generated {len(df):,} weather records")

    return df


def generate_economic_data(
    days: int = 730,
    start_date: str = '2024-01-01'
) -> pd.DataFrame:
    """Generate economic indicators (monthly)"""

    print(f"Generating economic indicators...")

    # Monthly data points
    months = pd.date_range(start=start_date, periods=days//30, freq='MS')

    records = []

    cpi_base = 300
    unemployment_base = 4.0

    for idx, date in enumerate(months):
        # CPI with gradual increase
        cpi = cpi_base + idx * 0.5 + np.random.normal(0, 2)

        # Unemployment with some variation
        unemployment = unemployment_base + np.random.normal(0, 0.3)

        # Consumer confidence (inverse to unemployment)
        consumer_conf = 100 - (unemployment - 4) * 5 + np.random.normal(0, 3)

        records.append({
            'date': date,
            'cpi': round(cpi, 2),
            'unemployment_rate': round(max(0, unemployment), 2),
            'consumer_confidence': round(consumer_conf, 1),
            'gas_price': round(np.random.uniform(2.5, 4.5), 2)
        })

    df = pd.DataFrame(records)

    print(f"✓ Generated {len(df):,} economic records")

    return df


def save_to_csv(output_dir: str = 'data/sample'):
    """Generate and save all sample data"""

    print("=" * 70)
    print("SAMPLE DATA GENERATOR")
    print("=" * 70)

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Generate data
    sales_df = generate_sales_data()
    locations = sales_df['location_id'].unique().tolist()
    weather_df = generate_weather_data(locations)
    economic_df = generate_economic_data()

    # Save to CSV
    sales_path = os.path.join(output_dir, 'sales.csv')
    weather_path = os.path.join(output_dir, 'weather.csv')
    economic_path = os.path.join(output_dir, 'economic.csv')

    sales_df.to_csv(sales_path, index=False)
    weather_df.to_csv(weather_path, index=False)
    economic_df.to_csv(economic_path, index=False)

    print(f"\n✓ Saved sales data to: {sales_path}")
    print(f"✓ Saved weather data to: {weather_path}")
    print(f"✓ Saved economic data to: {economic_path}")

    print("\n" + "=" * 70)
    print("SAMPLE DATA STATISTICS")
    print("=" * 70)

    print(f"\nSales Data:")
    print(f"  Total records: {len(sales_df):,}")
    print(f"  Date range: {sales_df['date'].min()} to {sales_df['date'].max()}")
    print(f"  SKUs: {sales_df['sku_id'].nunique()}")
    print(f"  Locations: {sales_df['location_id'].nunique()}")
    print(f"  Total revenue: ${sales_df['total_price'].sum():,.2f}")

    print(f"\nWeather Data:")
    print(f"  Total records: {len(weather_df):,}")
    print(f"  Avg temperature: {weather_df['temperature_f'].mean():.1f}°F")
    print(f"  Total precipitation: {weather_df['precipitation_inches'].sum():.1f} inches")

    print(f"\nEconomic Data:")
    print(f"  Total records: {len(economic_df):,}")
    print(f"  CPI range: {economic_df['cpi'].min():.1f} - {economic_df['cpi'].max():.1f}")
    print(f"  Unemployment range: {economic_df['unemployment_rate'].min():.1f}% - {economic_df['unemployment_rate'].max():.1f}%")

    print("\n✅ Sample data generation complete!")
    print("\nNext steps:")
    print("  1. Load data: pd.read_csv('data/sample/sales.csv')")
    print("  2. Train models: python ml_pipeline/train_models.py")
    print("  3. Start API: uvicorn services.api_gateway.main:app")

    return sales_df, weather_df, economic_df


if __name__ == "__main__":
    save_to_csv()
