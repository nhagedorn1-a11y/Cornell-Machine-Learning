"""
Main orchestrator for Scotts ML Supply Chain Optimization System
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

from data import (
    SalesDataLoader, InventoryDataLoader, WeatherDataLoader,
    DataIntegrator, WeatherForecastAPI
)

from models import (
    DemandForecaster, InventoryOptimizer, CommodityPlanner,
    SeasonalityAnalyzer, StockoutPredictor
)


class SupplyChainOptimizer:
    """
    Main class orchestrating all supply chain optimization components

    Usage:
        optimizer = SupplyChainOptimizer()
        optimizer.load_sales_data('sales.csv')
        optimizer.load_inventory_data('inventory.csv')

        # Generate forecasts
        forecast = optimizer.forecast_demand(horizon_days=90)

        # Optimize inventory
        inventory_plan = optimizer.optimize_inventory()

        # Plan commodity orders
        orders = optimizer.plan_commodity_orders()
    """

    def __init__(self, weather_api_key: Optional[str] = None):
        """Initialize the optimizer with all components"""

        # Data loaders
        self.sales_loader = SalesDataLoader()
        self.inventory_loader = InventoryDataLoader()
        self.weather_loader = WeatherDataLoader()
        self.weather_api = WeatherForecastAPI(api_key=weather_api_key)

        # ML models
        self.demand_forecaster = DemandForecaster(model_type="gradient_boosting")
        self.inventory_optimizer = InventoryOptimizer(service_level=0.95)
        self.commodity_planner = CommodityPlanner()

        # Data storage
        self.sales_data = None
        self.inventory_data = None
        self.weather_data = None
        self.store_locations = {}

        # Results
        self.demand_forecast = None
        self.inventory_projections = None
        self.commodity_orders = None

        print("✅ Supply Chain Optimizer initialized")

    # ========== DATA LOADING ==========

    def load_sales_data(self, filepath: str) -> pd.DataFrame:
        """Load historical sales data"""
        print(f"Loading sales data from {filepath}...")
        self.sales_data = self.sales_loader.load_from_csv(filepath)
        # Data is already set in loader by load_from_csv
        print(f"✅ Loaded {len(self.sales_data)} sales records")
        return self.sales_data

    def load_inventory_data(self, filepath: str) -> pd.DataFrame:
        """Load current inventory data"""
        print(f"Loading inventory data from {filepath}...")
        self.inventory_data = self.inventory_loader.load_from_csv(filepath)
        print(f"✅ Loaded inventory data for {self.inventory_data['product_sku'].nunique()} products")
        return self.inventory_data

    def load_weather_data(self, filepath: str) -> pd.DataFrame:
        """Load historical weather data"""
        print(f"Loading weather data from {filepath}...")
        self.weather_data = self.weather_loader.load_from_csv(filepath)
        print(f"✅ Loaded {len(self.weather_data)} weather records")
        return self.weather_data

    def generate_sample_data(
        self,
        num_stores: int = 10,
        num_products: int = 20,
        days_history: int = 365
    ):
        """Generate sample data for testing/demo"""
        print("Generating sample data for prototype...")

        # Generate sales data
        sales_records = []
        product_skus = [f"PROD-{i:03d}" for i in range(num_products)]
        store_ids = [f"STORE-{i:03d}" for i in range(num_stores)]

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_history)

        for day in range(days_history):
            date = start_date + timedelta(days=day)

            # Seasonal factor
            month = date.month
            if month in [3, 4, 5]:  # Spring - peak season
                seasonal_factor = 2.0
            elif month in [6, 7, 8]:  # Summer - high season
                seasonal_factor = 1.5
            elif month in [9, 10]:  # Fall - moderate
                seasonal_factor = 1.2
            else:  # Winter - low season
                seasonal_factor = 0.6

            for store in store_ids:
                for product in product_skus:
                    # Random daily sales with seasonality
                    base_sales = np.random.poisson(5)
                    sales = int(base_sales * seasonal_factor)

                    if sales > 0:
                        sales_records.append({
                            'transaction_id': f"TXN-{len(sales_records)}",
                            'store_id': store,
                            'product_sku': product,
                            'quantity': sales,
                            'revenue': sales * np.random.uniform(10, 50),
                            'timestamp': date,
                            'location_zip': '43215',
                            'date': date.date()
                        })

        self.sales_data = pd.DataFrame(sales_records)
        self.sales_loader.data = self.sales_data  # Set loader data

        # Generate inventory data
        inventory_records = []
        for store in store_ids:
            for product in product_skus:
                avg_daily_sales = self.sales_data[
                    (self.sales_data['store_id'] == store) &
                    (self.sales_data['product_sku'] == product)
                ]['quantity'].mean()

                inventory_records.append({
                    'store_id': store,
                    'product_sku': product,
                    'quantity_on_hand': int(avg_daily_sales * 30),
                    'quantity_on_order': int(avg_daily_sales * 7),
                    'reorder_point': int(avg_daily_sales * 10),
                    'max_stock_level': int(avg_daily_sales * 60),
                    'last_restock_date': datetime.now() - timedelta(days=7),
                    'daily_sales_avg': avg_daily_sales,
                    'snapshot_date': datetime.now(),
                    'date': datetime.now().date()
                })

        self.inventory_data = pd.DataFrame(inventory_records)
        self.inventory_loader.data = self.inventory_data  # Set loader data

        # Generate weather data
        self.weather_data = self.weather_api.get_historical_weather(
            latitude=40.0,
            longitude=-83.0,
            start_date=start_date,
            end_date=end_date
        )
        self.weather_loader.data = self.weather_data  # Set loader data

        print(f"✅ Generated sample data:")
        print(f"   - {len(self.sales_data)} sales records")
        print(f"   - {len(self.inventory_data)} inventory records")
        print(f"   - {len(self.weather_data)} weather records")

    # ========== FORECASTING ==========

    def forecast_demand(
        self,
        horizon_days: int = 90,
        include_weather: bool = True,
        train_model: bool = True
    ) -> pd.DataFrame:
        """
        Generate demand forecasts

        Args:
            horizon_days: Number of days to forecast
            include_weather: Whether to include weather data
            train_model: Whether to train new model or use existing

        Returns:
            DataFrame with demand forecasts
        """
        print(f"\n📊 Generating {horizon_days}-day demand forecasts...")

        if self.sales_data is None:
            raise ValueError("Sales data not loaded. Call load_sales_data() first.")

        # Prepare training data
        daily_sales = self.sales_loader.aggregate_daily_sales(
            group_by=['store_id', 'product_sku']
        )

        # Add time features
        daily_sales = self.sales_loader.add_time_features(daily_sales)

        # Merge with weather if available
        if include_weather and self.weather_data is not None:
            print("   Integrating weather data...")
            daily_sales = DataIntegrator.merge_sales_weather(
                daily_sales, self.weather_data
            )

            # Calculate weather indices
            daily_sales = self.weather_loader.calculate_weather_indices(daily_sales)

        # Create lag features
        daily_sales = DataIntegrator.create_lag_features(daily_sales)

        # Train model if needed
        if train_model or not self.demand_forecaster.trained:
            print("   Training forecasting models...")
            metrics = self.demand_forecaster.train(daily_sales)
            print(f"   Model performance - MAE: {metrics['mae']:.2f}, "
                  f"RMSE: {metrics['rmse']:.2f}")

        # Generate future dates for forecasting
        last_date = daily_sales['date'].max()
        future_dates = pd.date_range(
            start=last_date + timedelta(days=1),
            periods=horizon_days,
            freq='D'
        )

        # Get weather forecasts for future period
        future_weather = None
        if include_weather:
            print("   Fetching weather forecasts...")
            future_weather = self.weather_api.get_forecast(
                latitude=40.0,
                longitude=-83.0,
                days=min(horizon_days, 14)  # Most APIs limit to ~14 days
            )

        # Create forecast dataframe
        forecast_records = []
        products = daily_sales['product_sku'].unique()[:20]  # Limit for prototype
        stores = daily_sales['store_id'].unique()[:5]

        for product in products:
            for store in stores:
                for date in future_dates:
                    record = {
                        'product_sku': product,
                        'store_id': store,
                        'date': date,
                        'location_zip': '43215'
                    }
                    forecast_records.append(record)

        forecast_df = pd.DataFrame(forecast_records)
        forecast_df = self.sales_loader.add_time_features(forecast_df)

        # Add weather forecast if available
        if future_weather is not None:
            forecast_df = forecast_df.merge(
                future_weather,
                left_on='date',
                right_on='date',
                how='left'
            )
            forecast_df = self.weather_loader.calculate_weather_indices(forecast_df)

        # Generate forecasts
        self.demand_forecast = self.demand_forecaster.forecast(
            forecast_df,
            horizon_days=horizon_days
        )

        print(f"✅ Generated forecasts for {len(self.demand_forecast)} product-store-day combinations")

        return self.demand_forecast

    # ========== INVENTORY OPTIMIZATION ==========

    def optimize_inventory(
        self,
        products: Optional[List[str]] = None,
        service_level: float = 0.95
    ) -> pd.DataFrame:
        """
        Optimize inventory policies for all products

        Returns:
            DataFrame with optimized inventory policies
        """
        print(f"\n📦 Optimizing inventory policies (service level: {service_level*100:.0f}%)...")

        if self.sales_data is None:
            raise ValueError("Sales data not loaded")

        # Prepare daily sales
        daily_sales = self.sales_loader.aggregate_daily_sales()

        # Get products to optimize
        if products is None:
            products = daily_sales['product_sku'].unique()[:20]  # Limit for prototype

        policies = []

        for product in products:
            try:
                policy = self.inventory_optimizer.optimize_inventory_policy(
                    historical_sales=daily_sales,
                    product_sku=product,
                    lead_time_days=7,
                    ordering_cost=100,
                    holding_cost_percent=0.25,
                    unit_cost=20
                )
                policies.append(policy)

            except Exception as e:
                print(f"   ⚠️ Could not optimize {product}: {e}")
                continue

        policies_df = pd.DataFrame(policies)

        print(f"✅ Optimized inventory policies for {len(policies_df)} products")

        return policies_df

    def project_inventory_levels(
        self,
        horizon_days: int = 60
    ) -> pd.DataFrame:
        """
        Project future inventory levels based on demand forecast

        Returns:
            DataFrame with inventory projections
        """
        print(f"\n📈 Projecting inventory levels for {horizon_days} days...")

        if self.demand_forecast is None or len(self.demand_forecast) == 0:
            print("   No demand forecast available. Generating forecast first...")
            self.forecast_demand(horizon_days=horizon_days)

        if self.inventory_data is None:
            raise ValueError("Inventory data not loaded")

        # Check if forecast is valid
        if self.demand_forecast is None or len(self.demand_forecast) == 0:
            print("   ⚠️ Unable to generate demand forecast. Using simple projection instead.")
            return pd.DataFrame()

        projections = []

        # Get unique products
        products = self.demand_forecast['product_sku'].unique()[:10]

        for product in products:
            # Get current inventory
            current_inv = self.inventory_data[
                self.inventory_data['product_sku'] == product
            ]

            if len(current_inv) == 0:
                continue

            current_inv = current_inv.iloc[0]

            # Get demand forecast for this product
            product_forecast = self.demand_forecast[
                self.demand_forecast['product_sku'] == product
            ].copy()

            # Project inventory
            projection = self.inventory_optimizer.project_inventory(
                current_inventory=current_inv['quantity_on_hand'],
                current_on_order=current_inv['quantity_on_order'],
                demand_forecast=product_forecast,
                reorder_point=current_inv['reorder_point'],
                order_quantity=int(current_inv['daily_sales_avg'] * 14),
                lead_time_days=7
            )

            projection['product_sku'] = product
            projections.append(projection)

        if projections:
            self.inventory_projections = pd.concat(projections, ignore_index=True)
            print(f"✅ Generated inventory projections for {len(products)} products")
            return self.inventory_projections

        return pd.DataFrame()

    # ========== COMMODITY PLANNING ==========

    def plan_commodity_orders(
        self,
        planning_horizon_days: int = 90
    ) -> List[Dict]:
        """
        Generate commodity procurement plan

        Returns:
            List of recommended commodity orders
        """
        print(f"\n🏭 Planning commodity procurement ({planning_horizon_days} days)...")

        if self.demand_forecast is None:
            print("   Generating demand forecast first...")
            self.forecast_demand(horizon_days=planning_horizon_days)

        # Define sample bill of materials
        print("   Setting up bill of materials...")
        self.commodity_planner.define_bill_of_materials(
            'PROD-001',
            {
                'nitrogen': 0.15,
                'phosphorus': 0.10,
                'potassium': 0.08,
                'organic_matter': 0.20
            }
        )

        # Calculate material requirements
        print("   Calculating material requirements...")
        mrp = self.commodity_planner.calculate_material_requirements(
            self.demand_forecast,
            buffer_percent=0.15
        )

        # Define supplier information
        supplier_info = {
            'nitrogen': {
                'lead_time_days': 14,
                'moq': 1000,  # kg
                'price_per_unit': 0.50,
                'supplier_id': 'SUP-001'
            },
            'phosphorus': {
                'lead_time_days': 21,
                'moq': 800,
                'price_per_unit': 0.75,
                'supplier_id': 'SUP-002'
            },
            'potassium': {
                'lead_time_days': 14,
                'moq': 500,
                'price_per_unit': 0.60,
                'supplier_id': 'SUP-001'
            },
            'organic_matter': {
                'lead_time_days': 7,
                'moq': 2000,
                'price_per_unit': 0.30,
                'supplier_id': 'SUP-003'
            }
        }

        # Current inventory (example)
        current_inventory = {
            'nitrogen': 500,
            'phosphorus': 300,
            'potassium': 400,
            'organic_matter': 1000
        }

        # Optimize procurement
        print("   Optimizing procurement schedule...")
        orders = self.commodity_planner.optimize_procurement_schedule(
            material_requirements=mrp,
            current_inventory=current_inventory,
            supplier_info=supplier_info,
            planning_horizon_days=planning_horizon_days
        )

        # Consolidate orders
        orders = self.commodity_planner.consolidate_orders(orders)

        self.commodity_orders = orders

        print(f"✅ Generated {len(orders)} commodity procurement orders")

        return orders

    # ========== REPORTING ==========

    def generate_executive_summary(self) -> Dict:
        """Generate executive summary of all analyses"""

        summary = {
            'timestamp': datetime.now().isoformat(),
            'data_summary': {},
            'forecast_summary': {},
            'inventory_summary': {},
            'procurement_summary': {}
        }

        # Data summary
        if self.sales_data is not None:
            summary['data_summary'] = {
                'total_sales_records': len(self.sales_data),
                'products': self.sales_data['product_sku'].nunique(),
                'stores': self.sales_data['store_id'].nunique(),
                'date_range': f"{self.sales_data['date'].min()} to {self.sales_data['date'].max()}"
            }

        # Forecast summary
        if self.demand_forecast is not None:
            summary['forecast_summary'] = {
                'forecast_points': len(self.demand_forecast),
                'total_forecasted_demand': self.demand_forecast['predicted_quantity'].sum(),
                'forecast_horizon_days': (
                    self.demand_forecast['forecast_date'].max() -
                    self.demand_forecast['forecast_date'].min()
                ).days
            }

        # Procurement summary
        if self.commodity_orders:
            orders_df = pd.DataFrame(self.commodity_orders)
            summary['procurement_summary'] = {
                'total_orders': len(self.commodity_orders),
                'total_cost': orders_df['estimated_cost'].sum(),
                'urgent_orders': len(orders_df[orders_df['urgency_score'] >= 0.7])
            }

        return summary

    def export_results(self, output_dir: str = "./output"):
        """Export all results to CSV files"""
        import os
        os.makedirs(output_dir, exist_ok=True)

        if self.demand_forecast is not None:
            self.demand_forecast.to_csv(f"{output_dir}/demand_forecast.csv", index=False)
            print(f"✅ Exported demand forecast to {output_dir}/demand_forecast.csv")

        if self.inventory_projections is not None:
            self.inventory_projections.to_csv(f"{output_dir}/inventory_projections.csv", index=False)
            print(f"✅ Exported inventory projections to {output_dir}/inventory_projections.csv")

        if self.commodity_orders:
            pd.DataFrame(self.commodity_orders).to_csv(f"{output_dir}/commodity_orders.csv", index=False)
            print(f"✅ Exported commodity orders to {output_dir}/commodity_orders.csv")
