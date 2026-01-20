"""
Commodity ordering and raw material planning optimization
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import asdict


class CommodityPlanner:
    """
    Optimize raw material procurement based on production forecasts
    """

    def __init__(self):
        self.commodity_requirements = {}  # SKU -> commodity mapping
        self.supplier_data = {}
        self.procurement_plan = {}

    def define_bill_of_materials(
        self,
        product_sku: str,
        commodities: Dict[str, float]
    ):
        """
        Define raw material requirements for a product

        Args:
            product_sku: Product SKU
            commodities: Dict of {commodity_id: units_per_product}

        Example:
            planner.define_bill_of_materials(
                'FERT-001',
                {
                    'nitrogen': 0.15,  # 0.15 kg per unit
                    'phosphorus': 0.10,
                    'potassium': 0.08
                }
            )
        """
        self.commodity_requirements[product_sku] = commodities

    def calculate_material_requirements(
        self,
        demand_forecast: pd.DataFrame,
        buffer_percent: float = 0.10
    ) -> pd.DataFrame:
        """
        Calculate Material Requirements Planning (MRP) based on demand forecast

        Args:
            demand_forecast: Product demand forecast
            buffer_percent: Safety buffer percentage

        Returns:
            DataFrame with commodity requirements
        """

        requirements = []

        for _, row in demand_forecast.iterrows():
            product_sku = row['product_sku']
            quantity = row['predicted_quantity']
            date = row['forecast_date']

            # Get commodity requirements for this product
            if product_sku not in self.commodity_requirements:
                continue

            commodities = self.commodity_requirements[product_sku]

            for commodity_id, units_per_product in commodities.items():
                required_quantity = quantity * units_per_product
                buffered_quantity = required_quantity * (1 + buffer_percent)

                requirements.append({
                    'commodity_id': commodity_id,
                    'product_sku': product_sku,
                    'date': date,
                    'required_quantity': round(required_quantity, 2),
                    'buffered_quantity': round(buffered_quantity, 2)
                })

        mrp_df = pd.DataFrame(requirements)

        # Aggregate by commodity and date
        if len(mrp_df) > 0:
            agg_requirements = mrp_df.groupby(['commodity_id', 'date']).agg({
                'required_quantity': 'sum',
                'buffered_quantity': 'sum'
            }).reset_index()

            return agg_requirements

        return pd.DataFrame()

    def optimize_procurement_schedule(
        self,
        material_requirements: pd.DataFrame,
        current_inventory: Dict[str, float],
        supplier_info: Dict[str, Dict],
        planning_horizon_days: int = 90
    ) -> List[Dict]:
        """
        Create optimized procurement schedule

        Args:
            material_requirements: Output from calculate_material_requirements
            current_inventory: {commodity_id: current_quantity}
            supplier_info: {commodity_id: {
                'lead_time_days': int,
                'moq': float,
                'price_per_unit': float,
                'supplier_id': str
            }}
            planning_horizon_days: Planning horizon

        Returns:
            List of recommended purchase orders
        """

        self.supplier_data = supplier_info
        orders = []

        # Group by commodity
        commodities = material_requirements['commodity_id'].unique()

        for commodity_id in commodities:
            # Get requirements for this commodity
            commodity_reqs = material_requirements[
                material_requirements['commodity_id'] == commodity_id
            ].copy()

            commodity_reqs = commodity_reqs.sort_values('date')

            # Get supplier info
            supplier = supplier_info.get(commodity_id, {})
            lead_time = supplier.get('lead_time_days', 14)
            moq = supplier.get('moq', 0)
            price = supplier.get('price_per_unit', 0)
            supplier_id = supplier.get('supplier_id', 'UNKNOWN')

            # Calculate cumulative requirements
            commodity_reqs['cumulative_requirement'] = commodity_reqs['buffered_quantity'].cumsum()

            # Current inventory for this commodity
            current_stock = current_inventory.get(commodity_id, 0)

            # Determine order points
            inventory_position = current_stock

            for _, req in commodity_reqs.iterrows():
                req_date = req['date']
                req_quantity = req['buffered_quantity']

                # Account for lead time - order must arrive before needed
                order_by_date = req_date - timedelta(days=lead_time)

                # Check if order needed
                if inventory_position < req_quantity:
                    # Calculate order quantity
                    shortage = req_quantity - inventory_position
                    order_quantity = max(shortage, moq)

                    # Round up to MOQ multiples
                    if moq > 0:
                        order_quantity = np.ceil(order_quantity / moq) * moq

                    # Calculate urgency score
                    days_until_needed = (req_date - datetime.now()).days
                    if days_until_needed < lead_time:
                        urgency = 1.0  # Critical
                    elif days_until_needed < lead_time * 1.5:
                        urgency = 0.7  # High
                    elif days_until_needed < lead_time * 2:
                        urgency = 0.4  # Medium
                    else:
                        urgency = 0.2  # Low

                    orders.append({
                        'commodity_id': commodity_id,
                        'commodity_name': commodity_id.replace('_', ' ').title(),
                        'recommended_quantity': round(order_quantity, 2),
                        'units': 'kg',  # Default unit
                        'estimated_cost': round(order_quantity * price, 2),
                        'supplier_id': supplier_id,
                        'urgency_score': round(urgency, 2),
                        'order_by_date': order_by_date,
                        'expected_usage_start': req_date,
                        'expected_usage_end': req_date + timedelta(days=7),
                        'reasoning': f"Projected shortage of {round(shortage, 1)} units. "
                                   f"Current inventory: {round(inventory_position, 1)}. "
                                   f"Required: {round(req_quantity, 1)}."
                    })

                    # Update inventory position
                    inventory_position += order_quantity

                # Consume requirement
                inventory_position -= req_quantity

        # Sort by urgency and date
        orders_df = pd.DataFrame(orders)
        if len(orders_df) > 0:
            orders_df = orders_df.sort_values(['urgency_score', 'order_by_date'],
                                             ascending=[False, True])
            return orders_df.to_dict('records')

        return []

    def calculate_seasonal_buffer(
        self,
        commodity_id: str,
        season: str,
        historical_volatility: float = 0.15
    ) -> float:
        """
        Calculate seasonal safety buffer for commodity ordering

        Args:
            commodity_id: Commodity identifier
            season: Current season (spring, summer, fall, winter)
            historical_volatility: Historical demand volatility

        Returns:
            Buffer multiplier (e.g., 1.25 = 25% buffer)
        """

        # Gardening products have high spring/summer demand
        seasonal_factors = {
            'spring': 1.30,  # 30% buffer - peak season
            'summer': 1.25,  # 25% buffer - high season
            'fall': 1.15,    # 15% buffer - moderate season
            'winter': 1.05   # 5% buffer - low season
        }

        base_buffer = seasonal_factors.get(season.lower(), 1.10)

        # Adjust for volatility
        volatility_adjustment = 1 + (historical_volatility * 0.5)

        return base_buffer * volatility_adjustment

    def optimize_supplier_selection(
        self,
        commodity_id: str,
        required_quantity: float,
        suppliers: List[Dict]
    ) -> Dict:
        """
        Select optimal supplier based on cost, lead time, and reliability

        Args:
            commodity_id: Commodity to purchase
            required_quantity: Quantity needed
            suppliers: List of supplier options with pricing and terms

        Returns:
            Best supplier choice
        """

        if not suppliers:
            return {}

        scores = []

        for supplier in suppliers:
            # Extract supplier attributes
            price = supplier.get('price_per_unit', float('inf'))
            lead_time = supplier.get('lead_time_days', 30)
            reliability = supplier.get('reliability_score', 0.8)  # 0-1
            moq = supplier.get('moq', 0)

            # Check if MOQ can be met
            if moq > required_quantity:
                quantity_penalty = 0.5
            else:
                quantity_penalty = 1.0

            # Calculate total cost
            actual_quantity = max(required_quantity, moq)
            total_cost = actual_quantity * price

            # Multi-criteria scoring
            # Lower cost is better (normalize to 0-1)
            max_cost = max([s.get('price_per_unit', 0) * required_quantity for s in suppliers])
            cost_score = 1 - (total_cost / max_cost) if max_cost > 0 else 0

            # Lower lead time is better
            max_lead_time = max([s.get('lead_time_days', 0) for s in suppliers])
            lead_time_score = 1 - (lead_time / max_lead_time) if max_lead_time > 0 else 0

            # Higher reliability is better
            reliability_score = reliability

            # Weighted composite score
            composite_score = (
                cost_score * 0.5 +
                lead_time_score * 0.3 +
                reliability_score * 0.2
            ) * quantity_penalty

            scores.append({
                'supplier': supplier,
                'score': composite_score,
                'total_cost': total_cost,
                'actual_quantity': actual_quantity
            })

        # Select best supplier
        best = max(scores, key=lambda x: x['score'])

        return {
            'supplier_id': best['supplier'].get('supplier_id'),
            'supplier_name': best['supplier'].get('name', 'Unknown'),
            'price_per_unit': best['supplier'].get('price_per_unit'),
            'total_cost': best['total_cost'],
            'order_quantity': best['actual_quantity'],
            'lead_time_days': best['supplier'].get('lead_time_days'),
            'score': round(best['score'], 3)
        }

    def consolidate_orders(
        self,
        orders: List[Dict],
        consolidation_window_days: int = 7
    ) -> List[Dict]:
        """
        Consolidate multiple small orders into larger orders to reduce costs

        Args:
            orders: List of recommended orders
            consolidation_window_days: Time window for consolidation

        Returns:
            Consolidated order list
        """

        if not orders:
            return []

        orders_df = pd.DataFrame(orders)
        orders_df['order_by_date'] = pd.to_datetime(orders_df['order_by_date'])

        consolidated = []

        # Group by commodity and supplier
        for (commodity, supplier), group in orders_df.groupby(['commodity_id', 'supplier_id']):
            # Sort by date
            group = group.sort_values('order_by_date')

            current_order = None

            for _, order in group.iterrows():
                if current_order is None:
                    current_order = order.to_dict()
                else:
                    # Check if within consolidation window
                    days_diff = (order['order_by_date'] - current_order['order_by_date']).days

                    if days_diff <= consolidation_window_days:
                        # Consolidate
                        current_order['recommended_quantity'] += order['recommended_quantity']
                        current_order['estimated_cost'] += order['estimated_cost']
                        current_order['urgency_score'] = max(
                            current_order['urgency_score'],
                            order['urgency_score']
                        )
                        current_order['reasoning'] += f" + Consolidated order."
                    else:
                        # Save current and start new
                        consolidated.append(current_order)
                        current_order = order.to_dict()

            if current_order is not None:
                consolidated.append(current_order)

        return consolidated

    def generate_procurement_report(
        self,
        orders: List[Dict],
        material_requirements: pd.DataFrame
    ) -> Dict:
        """
        Generate summary report for procurement planning

        Returns:
            Summary statistics and insights
        """

        if not orders:
            return {
                'total_orders': 0,
                'total_cost': 0,
                'recommendations': []
            }

        orders_df = pd.DataFrame(orders)

        report = {
            'total_orders': len(orders),
            'total_cost': orders_df['estimated_cost'].sum(),
            'high_urgency_orders': len(orders_df[orders_df['urgency_score'] >= 0.7]),
            'commodities_needed': orders_df['commodity_id'].nunique(),
            'avg_order_value': orders_df['estimated_cost'].mean(),
            'top_commodities': orders_df.groupby('commodity_id')['estimated_cost'].sum()
                                      .sort_values(ascending=False).head(5).to_dict(),
            'urgent_orders': orders_df[orders_df['urgency_score'] >= 0.7]
                                      .to_dict('records'),
            'recommendations': []
        }

        # Generate recommendations
        if report['high_urgency_orders'] > 0:
            report['recommendations'].append(
                f"⚠️ {report['high_urgency_orders']} urgent orders require immediate attention"
            )

        if report['total_cost'] > 100000:
            report['recommendations'].append(
                "💰 High total procurement cost. Consider negotiating volume discounts."
            )

        return report
