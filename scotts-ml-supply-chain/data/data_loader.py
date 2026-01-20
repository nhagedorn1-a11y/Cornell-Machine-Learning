"""
Data loading and preprocessing for ML models
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from pathlib import Path

from .schemas import (
    SalesRecord, InventorySnapshot, WeatherData,
    ProductCategory, Season, StoreProfile
)


class SalesDataLoader:
    """Load and preprocess sales data"""

    def __init__(self):
        self.data = None
        self.preprocessed = False

    def load_from_csv(self, filepath: str) -> pd.DataFrame:
        """Load sales data from CSV file"""
        df = pd.read_csv(filepath)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        self.data = df
        return df

    def load_from_database(self, connection_string: str, query: str) -> pd.DataFrame:
        """Load sales data from database"""
        # Placeholder for database connection
        # In production: use SQLAlchemy or similar
        pass

    def aggregate_daily_sales(self, group_by: List[str] = None) -> pd.DataFrame:
        """Aggregate sales to daily level"""
        if group_by is None:
            group_by = ['store_id', 'product_sku']

        df = self.data.copy()
        df['date'] = df['timestamp'].dt.date

        agg_data = df.groupby(group_by + ['date']).agg({
            'quantity': 'sum',
            'revenue': 'sum',
            'transaction_id': 'count'
        }).reset_index()

        agg_data.columns = group_by + ['date', 'quantity', 'revenue', 'num_transactions']
        return agg_data

    def calculate_rolling_metrics(
        self,
        df: pd.DataFrame,
        window_days: int = 7
    ) -> pd.DataFrame:
        """Calculate rolling averages and metrics"""
        df = df.sort_values('date')

        df['quantity_ma7'] = df['quantity'].rolling(window=window_days, min_periods=1).mean()
        df['quantity_ma30'] = df['quantity'].rolling(window=30, min_periods=1).mean()
        df['revenue_ma7'] = df['revenue'].rolling(window=window_days, min_periods=1).mean()
        df['quantity_std7'] = df['quantity'].rolling(window=window_days, min_periods=1).std()

        return df

    def add_time_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add time-based features for modeling"""
        df = df.copy()
        df['date'] = pd.to_datetime(df['date'])

        df['year'] = df['date'].dt.year
        df['month'] = df['date'].dt.month
        df['week'] = df['date'].dt.isocalendar().week
        df['day_of_week'] = df['date'].dt.dayofweek
        df['day_of_year'] = df['date'].dt.dayofyear
        df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
        df['quarter'] = df['date'].dt.quarter

        # Season based on month
        df['season'] = df['month'].map({
            12: 'winter', 1: 'winter', 2: 'winter',
            3: 'spring', 4: 'spring', 5: 'spring',
            6: 'summer', 7: 'summer', 8: 'summer',
            9: 'fall', 10: 'fall', 11: 'fall'
        })

        return df

    def detect_outliers(self, df: pd.DataFrame, column: str = 'quantity') -> pd.DataFrame:
        """Detect and flag outliers using IQR method"""
        Q1 = df[column].quantile(0.25)
        Q3 = df[column].quantile(0.75)
        IQR = Q3 - Q1

        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR

        df['is_outlier'] = ((df[column] < lower_bound) | (df[column] > upper_bound)).astype(int)
        return df

    def fill_missing_dates(
        self,
        df: pd.DataFrame,
        start_date: datetime,
        end_date: datetime,
        group_cols: List[str] = None
    ) -> pd.DataFrame:
        """Fill in missing dates with zeros"""
        if group_cols is None:
            group_cols = ['store_id', 'product_sku']

        # Create complete date range
        date_range = pd.date_range(start=start_date, end=end_date, freq='D')

        # Get unique combinations of grouping columns
        unique_groups = df[group_cols].drop_duplicates()

        # Create complete grid
        complete_data = []
        for _, group in unique_groups.iterrows():
            for date in date_range:
                row = {col: group[col] for col in group_cols}
                row['date'] = date
                complete_data.append(row)

        complete_df = pd.DataFrame(complete_data)

        # Merge with actual data
        result = complete_df.merge(df, on=group_cols + ['date'], how='left')
        result['quantity'] = result['quantity'].fillna(0)
        result['revenue'] = result['revenue'].fillna(0)

        return result


class InventoryDataLoader:
    """Load and process inventory data"""

    def __init__(self):
        self.data = None

    def load_from_csv(self, filepath: str) -> pd.DataFrame:
        """Load inventory snapshots from CSV"""
        df = pd.read_csv(filepath)
        df['snapshot_date'] = pd.to_datetime(df['snapshot_date'])
        if 'last_restock_date' in df.columns:
            df['last_restock_date'] = pd.to_datetime(df['last_restock_date'])
        self.data = df
        return df

    def calculate_days_of_supply(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate days of supply based on current inventory and sales rate"""
        df = df.copy()
        df['days_of_supply'] = np.where(
            df['daily_sales_avg'] > 0,
            df['quantity_on_hand'] / df['daily_sales_avg'],
            999  # Effectively infinite if no sales
        )
        return df

    def calculate_inventory_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate key inventory metrics"""
        df = df.copy()

        # Stockout risk (simple heuristic)
        df['stockout_risk'] = np.where(
            df['quantity_on_hand'] <= df['reorder_point'],
            1.0,
            np.maximum(0, 1 - (df['quantity_on_hand'] - df['reorder_point']) / df['reorder_point'])
        )

        # Overstock indicator
        df['is_overstock'] = (df['quantity_on_hand'] > df['max_stock_level'] * 1.2).astype(int)

        # Inventory turnover rate (annualized)
        df['turnover_rate'] = (df['daily_sales_avg'] * 365) / np.maximum(df['quantity_on_hand'], 1)

        return df

    def get_low_stock_items(self, df: pd.DataFrame, threshold: float = 0.7) -> pd.DataFrame:
        """Get items below reorder threshold"""
        df = self.calculate_inventory_metrics(df)
        return df[df['stockout_risk'] >= threshold].sort_values('stockout_risk', ascending=False)


class WeatherDataLoader:
    """Load and process weather data"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.data = None

    def load_from_csv(self, filepath: str) -> pd.DataFrame:
        """Load historical weather data from CSV"""
        df = pd.read_csv(filepath)
        df['date'] = pd.to_datetime(df['date'])
        self.data = df
        return df

    def calculate_growing_degree_days(
        self,
        df: pd.DataFrame,
        base_temp: float = 50.0  # Base temperature in Fahrenheit
    ) -> pd.DataFrame:
        """Calculate Growing Degree Days (GDD) - important for gardening"""
        df = df.copy()

        # GDD = ((Tmax + Tmin) / 2) - Tbase
        df['growing_degree_days'] = np.maximum(
            0,
            ((df['temperature_max'] + df['temperature_min']) / 2) - base_temp
        )

        return df

    def calculate_weather_indices(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate weather-based demand indices"""
        df = df.copy()

        # Gardening favorability index (0-1)
        # Higher when: moderate temp, low rain, high sunshine
        df['gardening_index'] = (
            (df['temperature_avg'].clip(50, 80) - 50) / 30 * 0.4 +
            (1 - df['precipitation_inches'].clip(0, 2) / 2) * 0.3 +
            (df['sunshine_hours'] / 14) * 0.3
        )

        # Lawn care index
        df['lawn_care_index'] = (
            (df['temperature_avg'].clip(60, 85) - 60) / 25 * 0.5 +
            (df['precipitation_inches'].clip(0, 1) / 1) * 0.3 +
            (df['humidity_percent'] / 100) * 0.2
        )

        return df

    def aggregate_weekly_weather(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aggregate daily weather to weekly"""
        df = df.copy()
        df['year_week'] = df['date'].dt.strftime('%Y-%W')

        weekly = df.groupby(['location_zip', 'year_week']).agg({
            'temperature_avg': 'mean',
            'temperature_max': 'max',
            'temperature_min': 'min',
            'precipitation_inches': 'sum',
            'humidity_percent': 'mean',
            'sunshine_hours': 'sum',
            'growing_degree_days': 'sum',
            'date': 'min'
        }).reset_index()

        weekly.rename(columns={'date': 'week_start_date'}, inplace=True)

        return weekly


class DataIntegrator:
    """Integrate sales, inventory, and weather data"""

    @staticmethod
    def merge_sales_weather(
        sales_df: pd.DataFrame,
        weather_df: pd.DataFrame,
        on_date: str = 'date',
        on_location: str = 'location_zip'
    ) -> pd.DataFrame:
        """Merge sales data with weather data"""

        # Ensure date columns are in correct format
        sales_df = sales_df.copy()
        weather_df = weather_df.copy()

        sales_df[on_date] = pd.to_datetime(sales_df[on_date])
        weather_df[on_date] = pd.to_datetime(weather_df[on_date])

        # Merge
        merged = sales_df.merge(
            weather_df,
            on=[on_date, on_location],
            how='left'
        )

        return merged

    @staticmethod
    def create_training_dataset(
        sales_df: pd.DataFrame,
        weather_df: pd.DataFrame,
        inventory_df: Optional[pd.DataFrame] = None
    ) -> pd.DataFrame:
        """Create comprehensive training dataset for ML models"""

        # Merge sales and weather
        dataset = DataIntegrator.merge_sales_weather(sales_df, weather_df)

        # Add inventory data if available
        if inventory_df is not None:
            dataset = dataset.merge(
                inventory_df,
                on=['store_id', 'product_sku', 'date'],
                how='left'
            )

        # Sort by date
        dataset = dataset.sort_values(['store_id', 'product_sku', 'date'])

        return dataset

    @staticmethod
    def create_lag_features(
        df: pd.DataFrame,
        target_col: str = 'quantity',
        lags: List[int] = [1, 7, 14, 30, 365]
    ) -> pd.DataFrame:
        """Create lagged features for time series modeling"""
        df = df.copy()

        for lag in lags:
            df[f'{target_col}_lag_{lag}'] = df.groupby(['store_id', 'product_sku'])[target_col].shift(lag)

        return df
