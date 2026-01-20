"""
Inventory optimization and projection system
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from scipy import stats
from scipy.optimize import minimize


class InventoryOptimizer:
    """
    Optimize inventory levels, safety stock, and reorder points
    """

    def __init__(self, service_level: float = 0.95):
        """
        Args:
            service_level: Target service level (e.g., 0.95 = 95% in-stock probability)
        """
        self.service_level = service_level
        self.z_score = stats.norm.ppf(service_level)  # Z-score for service level
        self.optimization_results = {}

    def calculate_safety_stock(
        self,
        demand_std: float,
        lead_time_days: int,
        lead_time_std: int = 0
    ) -> int:
        """
        Calculate safety stock using standard formula

        Safety Stock = Z × √(LT × σ²_demand + D² × σ²_LT)
        Where:
            Z = Z-score for service level
            LT = Lead time
            σ_demand = Standard deviation of demand
            D = Average demand
            σ_LT = Standard deviation of lead time
        """

        if lead_time_std > 0:
            # Complex formula with variable lead time
            variance = lead_time_days * (demand_std ** 2) + (demand_std ** 2) * (lead_time_std ** 2)
            safety_stock = self.z_score * np.sqrt(variance)
        else:
            # Simplified formula with constant lead time
            safety_stock = self.z_score * demand_std * np.sqrt(lead_time_days)

        return int(np.ceil(safety_stock))

    def calculate_reorder_point(
        self,
        avg_daily_demand: float,
        lead_time_days: int,
        safety_stock: int
    ) -> int:
        """
        Calculate reorder point

        ROP = (Average Daily Demand × Lead Time) + Safety Stock
        """
        reorder_point = (avg_daily_demand * lead_time_days) + safety_stock
        return int(np.ceil(reorder_point))

    def calculate_economic_order_quantity(
        self,
        annual_demand: float,
        ordering_cost: float,
        holding_cost_per_unit: float
    ) -> int:
        """
        Calculate Economic Order Quantity (EOQ)

        EOQ = √((2 × D × S) / H)
        Where:
            D = Annual demand
            S = Ordering cost per order
            H = Holding cost per unit per year
        """
        if holding_cost_per_unit <= 0:
            return int(annual_demand / 12)  # Default to monthly order

        eoq = np.sqrt((2 * annual_demand * ordering_cost) / holding_cost_per_unit)
        return int(np.ceil(eoq))

    def optimize_inventory_policy(
        self,
        historical_sales: pd.DataFrame,
        product_sku: str,
        lead_time_days: int = 7,
        ordering_cost: float = 100,
        holding_cost_percent: float = 0.25,
        unit_cost: float = 10
    ) -> Dict:
        """
        Optimize complete inventory policy for a product

        Returns optimal:
        - Safety stock
        - Reorder point
        - Order quantity
        - Max stock level
        """

        # Filter for product
        product_data = historical_sales[
            historical_sales['product_sku'] == product_sku
        ].copy()

        if len(product_data) == 0:
            raise ValueError(f"No data found for product {product_sku}")

        # Calculate demand statistics
        avg_daily_demand = product_data['quantity'].mean()
        demand_std = product_data['quantity'].std()
        annual_demand = avg_daily_demand * 365

        # Calculate safety stock
        safety_stock = self.calculate_safety_stock(
            demand_std=demand_std,
            lead_time_days=lead_time_days
        )

        # Calculate reorder point
        reorder_point = self.calculate_reorder_point(
            avg_daily_demand=avg_daily_demand,
            lead_time_days=lead_time_days,
            safety_stock=safety_stock
        )

        # Calculate EOQ
        holding_cost_per_unit = unit_cost * holding_cost_percent
        eoq = self.calculate_economic_order_quantity(
            annual_demand=annual_demand,
            ordering_cost=ordering_cost,
            holding_cost_per_unit=holding_cost_per_unit
        )

        # Calculate max stock level
        max_stock = reorder_point + eoq

        # Calculate expected metrics
        num_orders_per_year = annual_demand / eoq
        avg_inventory = (eoq / 2) + safety_stock
        total_holding_cost = avg_inventory * holding_cost_per_unit
        total_ordering_cost = num_orders_per_year * ordering_cost
        total_cost = total_holding_cost + total_ordering_cost

        policy = {
            'product_sku': product_sku,
            'avg_daily_demand': round(avg_daily_demand, 2),
            'demand_std': round(demand_std, 2),
            'annual_demand': round(annual_demand, 2),
            'safety_stock': safety_stock,
            'reorder_point': reorder_point,
            'order_quantity': eoq,
            'max_stock_level': max_stock,
            'service_level': self.service_level,
            'lead_time_days': lead_time_days,
            'expected_orders_per_year': round(num_orders_per_year, 1),
            'avg_inventory_level': round(avg_inventory, 1),
            'total_annual_cost': round(total_cost, 2),
            'holding_cost': round(total_holding_cost, 2),
            'ordering_cost': round(total_ordering_cost, 2)
        }

        self.optimization_results[product_sku] = policy

        return policy

    def project_inventory(
        self,
        current_inventory: int,
        current_on_order: int,
        demand_forecast: pd.DataFrame,
        reorder_point: int,
        order_quantity: int,
        lead_time_days: int = 7
    ) -> pd.DataFrame:
        """
        Project inventory levels over time based on forecasted demand

        Returns DataFrame with daily projected inventory and recommended orders
        """

        forecast = demand_forecast.copy()
        forecast = forecast.sort_values('forecast_date')

        projections = []
        inventory_level = current_inventory
        on_order = current_on_order
        pending_orders = []  # List of (arrival_date, quantity)

        for idx, row in forecast.iterrows():
            date = row['forecast_date']
            expected_demand = row['predicted_quantity']

            # Check if any orders arrive today
            arriving_orders = [
                order for order in pending_orders
                if order['arrival_date'] == date
            ]
            for order in arriving_orders:
                inventory_level += order['quantity']
                on_order -= order['quantity']
                pending_orders.remove(order)

            # Subtract demand
            inventory_level = max(0, inventory_level - expected_demand)

            # Check if reorder needed
            should_reorder = (inventory_level + on_order) <= reorder_point
            order_placed = 0

            if should_reorder:
                order_placed = order_quantity
                on_order += order_quantity
                arrival_date = date + timedelta(days=lead_time_days)
                pending_orders.append({
                    'arrival_date': arrival_date,
                    'quantity': order_quantity
                })

            # Calculate stockout risk
            if inventory_level <= reorder_point * 0.3:
                stockout_risk = 0.8
            elif inventory_level <= reorder_point * 0.5:
                stockout_risk = 0.5
            elif inventory_level <= reorder_point:
                stockout_risk = 0.2
            else:
                stockout_risk = 0.05

            # Days until stockout (simple estimate)
            if expected_demand > 0:
                days_until_stockout = int(inventory_level / expected_demand)
            else:
                days_until_stockout = 999

            projections.append({
                'date': date,
                'projected_inventory': int(inventory_level),
                'on_order': int(on_order),
                'expected_demand': round(expected_demand, 1),
                'order_placed': order_placed,
                'stockout_risk': round(stockout_risk, 3),
                'days_until_stockout': days_until_stockout
            })

        return pd.DataFrame(projections)

    def calculate_abc_classification(
        self,
        sales_df: pd.DataFrame,
        value_col: str = 'revenue'
    ) -> pd.DataFrame:
        """
        Perform ABC analysis on products

        Class A: Top 20% of products by value (typically 70-80% of revenue)
        Class B: Next 30% of products (typically 15-25% of revenue)
        Class C: Bottom 50% of products (typically 5-10% of revenue)
        """

        # Aggregate by product
        product_value = sales_df.groupby('product_sku')[value_col].sum().reset_index()
        product_value = product_value.sort_values(value_col, ascending=False)

        # Calculate cumulative percentage
        total_value = product_value[value_col].sum()
        product_value['cumulative_value'] = product_value[value_col].cumsum()
        product_value['cumulative_percent'] = (
            product_value['cumulative_value'] / total_value * 100
        )

        # Classify
        product_value['abc_class'] = 'C'
        product_value.loc[product_value['cumulative_percent'] <= 80, 'abc_class'] = 'A'
        product_value.loc[
            (product_value['cumulative_percent'] > 80) &
            (product_value['cumulative_percent'] <= 95),
            'abc_class'
        ] = 'B'

        return product_value

    def multi_echelon_optimization(
        self,
        stores: List[str],
        warehouse_capacity: int,
        store_demand_forecasts: Dict[str, pd.DataFrame],
        transfer_cost: float = 50
    ) -> Dict[str, Dict]:
        """
        Optimize inventory allocation across warehouses and stores
        Simplified multi-echelon model for prototype
        """

        allocations = {}

        # Calculate total demand
        total_demand = 0
        for store_id, forecast in store_demand_forecasts.items():
            total_demand += forecast['predicted_quantity'].sum()

        # Allocate proportionally based on demand
        for store_id, forecast in store_demand_forecasts.items():
            store_demand = forecast['predicted_quantity'].sum()
            allocation_ratio = store_demand / total_demand

            allocated_inventory = int(warehouse_capacity * allocation_ratio)

            allocations[store_id] = {
                'allocated_inventory': allocated_inventory,
                'forecasted_demand': round(store_demand, 1),
                'allocation_ratio': round(allocation_ratio, 3),
                'recommended_transfer': allocated_inventory
            }

        return allocations


class StockoutPredictor:
    """Predict stockout probability and timing"""

    @staticmethod
    def calculate_stockout_probability(
        current_inventory: int,
        demand_forecast: float,
        demand_std: float,
        days: int = 7
    ) -> float:
        """
        Calculate probability of stockout within given timeframe

        Using normal distribution approximation
        """

        expected_demand = demand_forecast * days
        demand_variance = (demand_std ** 2) * days

        if demand_variance == 0:
            return 0.0 if current_inventory >= expected_demand else 1.0

        # Z-score for current inventory
        z = (current_inventory - expected_demand) / np.sqrt(demand_variance)

        # Probability that demand exceeds inventory
        stockout_prob = 1 - stats.norm.cdf(z)

        return min(1.0, max(0.0, stockout_prob))

    @staticmethod
    def days_until_stockout(
        current_inventory: int,
        daily_demand_forecast: pd.DataFrame
    ) -> Optional[int]:
        """
        Estimate days until stockout based on forecast

        Returns None if no stockout expected
        """

        inventory = current_inventory
        forecast = daily_demand_forecast.sort_values('forecast_date')

        for idx, (day, row) in enumerate(forecast.iterrows()):
            demand = row['predicted_quantity']
            inventory -= demand

            if inventory <= 0:
                return idx + 1

        return None  # No stockout in forecast period
