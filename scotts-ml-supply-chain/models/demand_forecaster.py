"""
Demand forecasting models combining time series, weather, and seasonality
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import TimeSeriesSplit
import joblib


class DemandForecaster:
    """
    Multi-model demand forecasting system
    Combines multiple approaches for robust predictions
    """

    def __init__(self, model_type: str = "gradient_boosting"):
        """
        Args:
            model_type: 'gradient_boosting', 'random_forest', 'prophet', or 'ensemble'
        """
        self.model_type = model_type
        self.models = {}
        self.scalers = {}
        self.feature_importance = {}
        self.trained = False

    def prepare_features(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
        """Prepare features for modeling"""

        features_df = df.copy()

        # Time features
        if 'date' in features_df.columns:
            features_df['date'] = pd.to_datetime(features_df['date'])
            features_df['year'] = features_df['date'].dt.year
            features_df['month'] = features_df['date'].dt.month
            features_df['day'] = features_df['date'].dt.day
            features_df['day_of_week'] = features_df['date'].dt.dayofweek
            features_df['day_of_year'] = features_df['date'].dt.dayofyear
            features_df['week_of_year'] = features_df['date'].dt.isocalendar().week
            features_df['is_weekend'] = (features_df['day_of_week'] >= 5).astype(int)
            features_df['quarter'] = features_df['date'].dt.quarter

        # Cyclic encoding for seasonality
        if 'day_of_year' in features_df.columns:
            features_df['day_sin'] = np.sin(2 * np.pi * features_df['day_of_year'] / 365)
            features_df['day_cos'] = np.cos(2 * np.pi * features_df['day_of_year'] / 365)

        if 'month' in features_df.columns:
            features_df['month_sin'] = np.sin(2 * np.pi * features_df['month'] / 12)
            features_df['month_cos'] = np.cos(2 * np.pi * features_df['month'] / 12)

        # Lag features (if quantity exists)
        if 'quantity' in features_df.columns:
            for lag in [1, 7, 14, 30, 365]:
                features_df[f'quantity_lag_{lag}'] = features_df.groupby('product_sku')['quantity'].shift(lag)

            # Rolling statistics
            for window in [7, 30]:
                features_df[f'quantity_roll_mean_{window}'] = (
                    features_df.groupby('product_sku')['quantity']
                    .rolling(window=window, min_periods=1)
                    .mean()
                    .reset_index(level=0, drop=True)
                )
                features_df[f'quantity_roll_std_{window}'] = (
                    features_df.groupby('product_sku')['quantity']
                    .rolling(window=window, min_periods=1)
                    .std()
                    .reset_index(level=0, drop=True)
                )

        # Weather features (if available)
        weather_features = [
            'temperature_avg', 'temperature_max', 'temperature_min',
            'precipitation_inches', 'humidity_percent', 'sunshine_hours',
            'growing_degree_days'
        ]

        # Interaction features
        if 'temperature_avg' in features_df.columns and 'precipitation_inches' in features_df.columns:
            features_df['temp_precip_interaction'] = (
                features_df['temperature_avg'] * features_df['precipitation_inches']
            )

        if 'growing_degree_days' in features_df.columns and 'month' in features_df.columns:
            features_df['gdd_season_interaction'] = (
                features_df['growing_degree_days'] * features_df['month']
            )

        # Select feature columns
        feature_cols = [
            'month', 'day_of_week', 'day_of_year', 'week_of_year',
            'is_weekend', 'quarter', 'day_sin', 'day_cos', 'month_sin', 'month_cos'
        ]

        # Add lag features if they exist
        lag_cols = [col for col in features_df.columns if 'lag' in col or 'roll' in col]
        feature_cols.extend(lag_cols)

        # Add weather features if they exist
        available_weather = [col for col in weather_features if col in features_df.columns]
        feature_cols.extend(available_weather)

        # Add interaction features
        interaction_cols = [col for col in features_df.columns if 'interaction' in col]
        feature_cols.extend(interaction_cols)

        # Remove duplicates and ensure all columns exist
        feature_cols = list(set([col for col in feature_cols if col in features_df.columns]))

        return features_df, feature_cols

    def train(
        self,
        train_df: pd.DataFrame,
        target_col: str = 'quantity',
        group_col: str = 'product_sku'
    ) -> Dict[str, float]:
        """
        Train forecasting models

        Args:
            train_df: Training data with sales, weather, and features
            target_col: Column to forecast
            group_col: Column to group by (e.g., product_sku, store_id)

        Returns:
            Dictionary with training metrics
        """

        print("Preparing features...")
        features_df, feature_cols = self.prepare_features(train_df)

        # Remove rows with NaN in features or target
        features_df = features_df.dropna(subset=feature_cols + [target_col])

        # Get unique groups
        groups = features_df[group_col].unique()

        print(f"Training models for {len(groups)} groups...")

        metrics = {'mae': [], 'rmse': [], 'mape': []}

        for group in groups[:50]:  # Limit for prototype
            group_data = features_df[features_df[group_col] == group].copy()

            if len(group_data) < 60:  # Need sufficient data
                continue

            # Prepare train/val split (time-based)
            split_idx = int(len(group_data) * 0.8)
            train_data = group_data.iloc[:split_idx]
            val_data = group_data.iloc[split_idx:]

            X_train = train_data[feature_cols]
            y_train = train_data[target_col]
            X_val = val_data[feature_cols]
            y_val = val_data[target_col]

            # Scale features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_val_scaled = scaler.transform(X_val)

            # Train model
            if self.model_type == "gradient_boosting":
                model = GradientBoostingRegressor(
                    n_estimators=100,
                    learning_rate=0.1,
                    max_depth=5,
                    random_state=42
                )
            elif self.model_type == "random_forest":
                model = RandomForestRegressor(
                    n_estimators=100,
                    max_depth=10,
                    random_state=42,
                    n_jobs=-1
                )
            else:
                model = GradientBoostingRegressor(
                    n_estimators=100,
                    learning_rate=0.1,
                    max_depth=5,
                    random_state=42
                )

            model.fit(X_train_scaled, y_train)

            # Validate
            y_pred = model.predict(X_val_scaled)

            mae = np.mean(np.abs(y_val - y_pred))
            rmse = np.sqrt(np.mean((y_val - y_pred) ** 2))
            mape = np.mean(np.abs((y_val - y_pred) / np.maximum(y_val, 1))) * 100

            metrics['mae'].append(mae)
            metrics['rmse'].append(rmse)
            metrics['mape'].append(mape)

            # Store model and scaler
            self.models[group] = model
            self.scalers[group] = scaler

            # Store feature importance
            if hasattr(model, 'feature_importances_'):
                self.feature_importance[group] = dict(zip(
                    feature_cols,
                    model.feature_importances_
                ))

        self.trained = True

        # Average metrics
        avg_metrics = {k: np.mean(v) for k, v in metrics.items()}

        print(f"Training complete. Avg MAE: {avg_metrics['mae']:.2f}, "
              f"Avg RMSE: {avg_metrics['rmse']:.2f}, "
              f"Avg MAPE: {avg_metrics['mape']:.2f}%")

        return avg_metrics

    def forecast(
        self,
        forecast_df: pd.DataFrame,
        horizon_days: int = 30,
        group_col: str = 'product_sku',
        confidence_level: float = 0.95
    ) -> pd.DataFrame:
        """
        Generate demand forecasts

        Args:
            forecast_df: DataFrame with features for forecasting period
            horizon_days: Number of days to forecast
            group_col: Grouping column
            confidence_level: Confidence interval level

        Returns:
            DataFrame with forecasts and confidence intervals
        """

        if not self.trained:
            raise ValueError("Model must be trained before forecasting")

        print(f"Generating {horizon_days}-day forecasts...")

        # Prepare features
        features_df, feature_cols = self.prepare_features(forecast_df)

        forecasts = []

        for group, model in self.models.items():
            group_data = features_df[features_df[group_col] == group].copy()

            if len(group_data) == 0:
                continue

            # Prepare features
            X = group_data[feature_cols]

            # Handle missing values
            X = X.fillna(X.mean())

            # Scale
            scaler = self.scalers.get(group)
            if scaler is None:
                continue

            X_scaled = scaler.transform(X)

            # Predict
            y_pred = model.predict(X_scaled)

            # Calculate prediction intervals (simplified)
            # In production, use more sophisticated methods
            std_error = np.std(y_pred) * 0.2  # Approximate
            z_score = 1.96 if confidence_level == 0.95 else 1.645

            lower_bound = y_pred - z_score * std_error
            upper_bound = y_pred + z_score * std_error

            # Add to results
            for idx, (date_idx, row) in enumerate(group_data.iterrows()):
                forecasts.append({
                    'product_sku': group,
                    'forecast_date': row.get('date', datetime.now() + timedelta(days=idx)),
                    'predicted_quantity': max(0, y_pred[idx]),
                    'confidence_lower': max(0, lower_bound[idx]),
                    'confidence_upper': max(0, upper_bound[idx]),
                    'confidence_level': confidence_level
                })

        forecast_df = pd.DataFrame(forecasts)

        print(f"Generated {len(forecast_df)} forecast points")

        return forecast_df

    def get_feature_importance(self, top_n: int = 10) -> pd.DataFrame:
        """Get top important features across all models"""

        if not self.feature_importance:
            return pd.DataFrame()

        # Average importance across all models
        all_features = {}
        for group, importances in self.feature_importance.items():
            for feature, importance in importances.items():
                if feature not in all_features:
                    all_features[feature] = []
                all_features[feature].append(importance)

        avg_importance = {k: np.mean(v) for k, v in all_features.items()}

        # Sort and return top N
        sorted_features = sorted(avg_importance.items(), key=lambda x: x[1], reverse=True)

        df = pd.DataFrame(sorted_features[:top_n], columns=['Feature', 'Importance'])
        return df

    def save_models(self, filepath: str):
        """Save trained models to disk"""
        joblib.dump({
            'models': self.models,
            'scalers': self.scalers,
            'feature_importance': self.feature_importance,
            'model_type': self.model_type
        }, filepath)
        print(f"Models saved to {filepath}")

    def load_models(self, filepath: str):
        """Load trained models from disk"""
        data = joblib.load(filepath)
        self.models = data['models']
        self.scalers = data['scalers']
        self.feature_importance = data['feature_importance']
        self.model_type = data['model_type']
        self.trained = True
        print(f"Models loaded from {filepath}")


class SeasonalityAnalyzer:
    """Analyze and extract seasonal patterns"""

    @staticmethod
    def detect_seasonality(
        df: pd.DataFrame,
        value_col: str = 'quantity',
        date_col: str = 'date'
    ) -> Dict[str, float]:
        """Detect seasonal patterns in data"""

        df = df.copy()
        df[date_col] = pd.to_datetime(df[date_col])
        df['month'] = df[date_col].dt.month
        df['quarter'] = df[date_col].dt.quarter

        # Monthly seasonality
        monthly_avg = df.groupby('month')[value_col].mean()
        overall_avg = df[value_col].mean()

        monthly_index = (monthly_avg / overall_avg).to_dict()

        # Quarterly seasonality
        quarterly_avg = df.groupby('quarter')[value_col].mean()
        quarterly_index = (quarterly_avg / overall_avg).to_dict()

        return {
            'monthly': monthly_index,
            'quarterly': quarterly_index
        }

    @staticmethod
    def calculate_weather_correlation(
        df: pd.DataFrame,
        sales_col: str = 'quantity',
        weather_cols: List[str] = None
    ) -> pd.DataFrame:
        """Calculate correlation between sales and weather variables"""

        if weather_cols is None:
            weather_cols = [
                'temperature_avg', 'precipitation_inches',
                'humidity_percent', 'growing_degree_days'
            ]

        available_cols = [col for col in weather_cols if col in df.columns]

        if not available_cols:
            return pd.DataFrame()

        correlations = []
        for col in available_cols:
            corr = df[[sales_col, col]].corr().iloc[0, 1]
            correlations.append({
                'weather_variable': col,
                'correlation': corr,
                'abs_correlation': abs(corr)
            })

        result = pd.DataFrame(correlations)
        result = result.sort_values('abs_correlation', ascending=False)

        return result
