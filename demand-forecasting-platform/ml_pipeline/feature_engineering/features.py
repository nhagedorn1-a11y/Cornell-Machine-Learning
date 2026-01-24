"""
Feature Engineering Pipeline
Generates 50+ features for demand forecasting
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class FeatureEngineer:
    """
    Feature engineering pipeline for demand forecasting

    Generates 50+ features across categories:
    - Lag features (1, 7, 14, 30, 90, 365 days)
    - Rolling statistics (mean, std, min, max)
    - Time-based features (day of week, month, holidays)
    - Weather features (temperature, precipitation, degree days)
    - Economic indicators (CPI, unemployment, etc.)
    - Seasonal decomposition
    - Interaction terms
    """

    def __init__(self):
        self.feature_names = []

    def create_features(
        self,
        sales_data: pd.DataFrame,
        weather_data: Optional[pd.DataFrame] = None,
        economic_data: Optional[pd.DataFrame] = None,
        date_col: str = 'date',
        target_col: str = 'quantity',
        sku_col: str = 'sku_id',
        location_col: str = 'location_id'
    ) -> pd.DataFrame:
        """
        Create all features from raw data

        Args:
            sales_data: Historical sales data
            weather_data: Weather observations (optional)
            economic_data: Economic indicators (optional)
            date_col: Name of date column
            target_col: Name of target variable
            sku_col: Name of SKU identifier
            location_col: Name of location identifier

        Returns:
            DataFrame with features
        """
        logger.info(f"Creating features from {len(sales_data)} records")

        df = sales_data.copy()
        df[date_col] = pd.to_datetime(df[date_col])
        df = df.sort_values([sku_col, location_col, date_col])

        features_df = pd.DataFrame(index=df.index)

        # 1. Time-based features (10 features)
        features_df = pd.concat([features_df, self._create_time_features(df, date_col)], axis=1)

        # 2. Lag features (15 features)
        features_df = pd.concat([
            features_df,
            self._create_lag_features(df, target_col, [sku_col, location_col])
        ], axis=1)

        # 3. Rolling statistics (12 features)
        features_df = pd.concat([
            features_df,
            self._create_rolling_features(df, target_col, [sku_col, location_col])
        ], axis=1)

        # 4. Weather features (if available) (8 features)
        if weather_data is not None:
            features_df = pd.concat([
                features_df,
                self._create_weather_features(df, weather_data, date_col, location_col)
            ], axis=1)

        # 5. Economic features (if available) (5 features)
        if economic_data is not None:
            features_df = pd.concat([
                features_df,
                self._create_economic_features(df, economic_data, date_col)
            ], axis=1)

        # 6. Seasonal decomposition (3 features)
        features_df = pd.concat([
            features_df,
            self._create_seasonal_features(df, target_col, [sku_col, location_col])
        ], axis=1)

        # 7. Interaction features (5 features)
        features_df = self._create_interaction_features(features_df)

        # Store feature names
        self.feature_names = features_df.columns.tolist()

        logger.info(f"Created {len(self.feature_names)} features")

        return features_df

    def _create_time_features(self, df: pd.DataFrame, date_col: str) -> pd.DataFrame:
        """Time-based features"""

        features = pd.DataFrame(index=df.index)

        dates = df[date_col]

        features['day_of_week'] = dates.dt.dayofweek
        features['day_of_month'] = dates.dt.day
        features['day_of_year'] = dates.dt.dayofyear
        features['week_of_year'] = dates.dt.isocalendar().week
        features['month'] = dates.dt.month
        features['quarter'] = dates.dt.quarter
        features['year'] = dates.dt.year

        # Is weekend
        features['is_weekend'] = (dates.dt.dayofweek >= 5).astype(int)

        # Is month start/end
        features['is_month_start'] = dates.dt.is_month_start.astype(int)
        features['is_month_end'] = dates.dt.is_month_end.astype(int)

        return features

    def _create_lag_features(
        self,
        df: pd.DataFrame,
        target_col: str,
        group_cols: List[str]
    ) -> pd.DataFrame:
        """Lag features at various time windows"""

        features = pd.DataFrame(index=df.index)

        lag_periods = [1, 7, 14, 30, 90, 365]

        for lag in lag_periods:
            features[f'lag_{lag}d'] = df.groupby(group_cols)[target_col].shift(lag)

        return features

    def _create_rolling_features(
        self,
        df: pd.DataFrame,
        target_col: str,
        group_cols: List[str]
    ) -> pd.DataFrame:
        """Rolling window statistics"""

        features = pd.DataFrame(index=df.index)

        windows = [7, 30, 90]

        for window in windows:
            rolling = df.groupby(group_cols)[target_col].transform(
                lambda x: x.rolling(window=window, min_periods=1)
            )

            features[f'rolling_mean_{window}d'] = rolling.mean()
            features[f'rolling_std_{window}d'] = rolling.std()
            features[f'rolling_min_{window}d'] = rolling.min()
            features[f'rolling_max_{window}d'] = rolling.max()

        return features

    def _create_weather_features(
        self,
        df: pd.DataFrame,
        weather_data: pd.DataFrame,
        date_col: str,
        location_col: str
    ) -> pd.DataFrame:
        """Weather-related features"""

        features = pd.DataFrame(index=df.index)

        # Merge weather data
        weather = weather_data.copy()
        weather[date_col] = pd.to_datetime(weather[date_col])

        merged = df[[date_col, location_col]].merge(
            weather,
            on=[date_col, location_col],
            how='left'
        )

        # Temperature features
        if 'temperature_f' in merged.columns:
            features['temperature'] = merged['temperature_f']
            features['temp_squared'] = merged['temperature_f'] ** 2

            # Cooling/Heating degree days (base 65°F)
            features['cooling_degree_days'] = np.maximum(0, merged['temperature_f'] - 65)
            features['heating_degree_days'] = np.maximum(0, 65 - merged['temperature_f'])

        # Precipitation
        if 'precipitation_inches' in merged.columns:
            features['precipitation'] = merged['precipitation_inches']
            features['is_rainy'] = (merged['precipitation_inches'] > 0.1).astype(int)

        # Weather condition
        if 'weather_condition' in merged.columns:
            # One-hot encode top conditions
            features['is_sunny'] = (merged['weather_condition'] == 'sunny').astype(int)
            features['is_rainy_weather'] = merged['weather_condition'].isin(['rainy', 'stormy']).astype(int)

        return features

    def _create_economic_features(
        self,
        df: pd.DataFrame,
        economic_data: pd.DataFrame,
        date_col: str
    ) -> pd.DataFrame:
        """Economic indicator features"""

        features = pd.DataFrame(index=df.index)

        # Merge economic data (monthly indicators)
        econ = economic_data.copy()
        econ[date_col] = pd.to_datetime(econ[date_col])

        # Create month-year key for merging
        df_month = df[date_col].dt.to_period('M')
        econ_month = econ[date_col].dt.to_period('M')

        # Merge on month
        merged = df[[date_col]].copy()
        merged['month_period'] = df_month

        econ_monthly = econ.copy()
        econ_monthly['month_period'] = econ_month

        merged = merged.merge(
            econ_monthly,
            on='month_period',
            how='left',
            suffixes=('', '_econ')
        )

        # Economic features
        if 'cpi' in merged.columns:
            features['cpi'] = merged['cpi']
            features['cpi_change'] = merged.groupby('month_period')['cpi'].pct_change()

        if 'unemployment_rate' in merged.columns:
            features['unemployment'] = merged['unemployment_rate']

        if 'consumer_confidence' in merged.columns:
            features['consumer_confidence'] = merged['consumer_confidence']

        if 'gas_price' in merged.columns:
            features['gas_price'] = merged['gas_price']

        return features

    def _create_seasonal_features(
        self,
        df: pd.DataFrame,
        target_col: str,
        group_cols: List[str]
    ) -> pd.DataFrame:
        """Seasonal decomposition features"""

        features = pd.DataFrame(index=df.index)

        # Simple seasonal indices by month
        monthly_avg = df.groupby(group_cols + [df.index.month])[target_col].transform('mean')
        overall_avg = df.groupby(group_cols)[target_col].transform('mean')

        features['seasonal_index'] = monthly_avg / (overall_avg + 1e-6)

        # Year-over-year growth
        features['yoy_growth'] = df.groupby(group_cols)[target_col].pct_change(periods=365)

        # Cyclical component (detrended)
        features['detrended'] = df.groupby(group_cols)[target_col].transform(
            lambda x: x - x.rolling(window=30, min_periods=1, center=True).mean()
        )

        return features

    def _create_interaction_features(self, features_df: pd.DataFrame) -> pd.DataFrame:
        """Create interaction features"""

        # Temperature × Weekend
        if 'temperature' in features_df.columns and 'is_weekend' in features_df.columns:
            features_df['temp_weekend'] = features_df['temperature'] * features_df['is_weekend']

        # Temperature × Month (seasonal temperature effect)
        if 'temperature' in features_df.columns and 'month' in features_df.columns:
            features_df['temp_month'] = features_df['temperature'] * features_df['month']

        # Lag × Rolling mean (momentum)
        if 'lag_7d' in features_df.columns and 'rolling_mean_30d' in features_df.columns:
            features_df['momentum'] = features_df['lag_7d'] / (features_df['rolling_mean_30d'] + 1e-6)

        # Precipitation × Temperature
        if 'precipitation' in features_df.columns and 'temperature' in features_df.columns:
            features_df['precip_temp'] = features_df['precipitation'] * features_df['temperature']

        # Economic × Seasonal
        if 'cpi' in features_df.columns and 'seasonal_index' in features_df.columns:
            features_df['cpi_seasonal'] = features_df['cpi'] * features_df['seasonal_index']

        return features_df

    def get_feature_names(self) -> List[str]:
        """Get list of all feature names"""
        return self.feature_names

    def get_feature_groups(self) -> Dict[str, List[str]]:
        """
        Get features organized by category

        Returns:
            Dictionary mapping category -> feature names
        """
        groups = {
            'time': [],
            'lag': [],
            'rolling': [],
            'weather': [],
            'economic': [],
            'seasonal': [],
            'interaction': []
        }

        for feature in self.feature_names:
            if feature.startswith(('day_', 'week_', 'month_', 'quarter_', 'year_', 'is_')):
                groups['time'].append(feature)
            elif feature.startswith('lag_'):
                groups['lag'].append(feature)
            elif feature.startswith('rolling_'):
                groups['rolling'].append(feature)
            elif any(x in feature for x in ['temp', 'precip', 'degree', 'weather', 'sunny', 'rainy']):
                groups['weather'].append(feature)
            elif any(x in feature for x in ['cpi', 'unemployment', 'confidence', 'gas']):
                groups['economic'].append(feature)
            elif any(x in feature for x in ['seasonal', 'yoy', 'detrended']):
                groups['seasonal'].append(feature)
            else:
                groups['interaction'].append(feature)

        return groups
