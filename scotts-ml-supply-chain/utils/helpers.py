"""
Helper utilities for the supply chain optimizer
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple


def calculate_mape(actual: np.ndarray, predicted: np.ndarray) -> float:
    """
    Calculate Mean Absolute Percentage Error

    Args:
        actual: Actual values
        predicted: Predicted values

    Returns:
        MAPE as percentage
    """
    mask = actual != 0
    return np.mean(np.abs((actual[mask] - predicted[mask]) / actual[mask])) * 100


def calculate_forecast_accuracy(actual: np.ndarray, predicted: np.ndarray) -> Dict[str, float]:
    """
    Calculate multiple forecast accuracy metrics

    Returns:
        Dictionary with MAE, RMSE, MAPE, and accuracy metrics
    """
    mae = np.mean(np.abs(actual - predicted))
    rmse = np.sqrt(np.mean((actual - predicted) ** 2))
    mape = calculate_mape(actual, predicted)

    # Forecast bias
    bias = np.mean(predicted - actual)

    # Tracking signal
    cumulative_error = np.cumsum(predicted - actual)
    mad = np.mean(np.abs(predicted - actual))
    tracking_signal = cumulative_error[-1] / mad if mad > 0 else 0

    return {
        'mae': mae,
        'rmse': rmse,
        'mape': mape,
        'bias': bias,
        'tracking_signal': tracking_signal
    }


def get_season_from_date(date: datetime) -> str:
    """Get gardening season from date"""
    month = date.month

    if month in [3, 4, 5]:
        return 'spring'
    elif month in [6, 7, 8]:
        return 'summer'
    elif month in [9, 10, 11]:
        return 'fall'
    else:
        return 'winter'


def calculate_service_level(stockouts: int, total_opportunities: int) -> float:
    """
    Calculate service level percentage

    Args:
        stockouts: Number of stockout incidents
        total_opportunities: Total opportunities to stock out

    Returns:
        Service level as percentage
    """
    if total_opportunities == 0:
        return 100.0

    return ((total_opportunities - stockouts) / total_opportunities) * 100


def format_currency(amount: float) -> str:
    """Format amount as currency"""
    return f"${amount:,.2f}"


def format_percentage(value: float) -> str:
    """Format value as percentage"""
    return f"{value:.1f}%"


def date_range_generator(start_date: datetime, end_date: datetime, freq: str = 'D'):
    """Generate date range"""
    return pd.date_range(start=start_date, end=end_date, freq=freq)


def validate_data_quality(df: pd.DataFrame, required_columns: List[str]) -> Dict:
    """
    Validate data quality

    Returns:
        Dictionary with validation results
    """
    issues = []

    # Check required columns
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        issues.append(f"Missing columns: {missing_cols}")

    # Check for nulls
    null_counts = df[required_columns].isnull().sum()
    null_cols = null_counts[null_counts > 0]
    if len(null_cols) > 0:
        issues.append(f"Columns with nulls: {null_cols.to_dict()}")

    # Check for duplicates
    duplicates = df.duplicated().sum()
    if duplicates > 0:
        issues.append(f"Duplicate rows: {duplicates}")

    return {
        'is_valid': len(issues) == 0,
        'issues': issues,
        'row_count': len(df),
        'null_percentage': (df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100
    }


def aggregate_by_week(df: pd.DataFrame, date_col: str, value_col: str) -> pd.DataFrame:
    """Aggregate data by week"""
    df = df.copy()
    df['year_week'] = pd.to_datetime(df[date_col]).dt.strftime('%Y-%W')

    weekly = df.groupby('year_week')[value_col].sum().reset_index()
    weekly.columns = ['year_week', f'{value_col}_weekly']

    return weekly


def calculate_inventory_turnover(
    annual_sales: float,
    average_inventory: float
) -> float:
    """Calculate inventory turnover ratio"""
    if average_inventory == 0:
        return 0

    return annual_sales / average_inventory


def calculate_days_inventory_outstanding(
    inventory_turnover: float
) -> float:
    """Calculate days inventory outstanding (DIO)"""
    if inventory_turnover == 0:
        return 365

    return 365 / inventory_turnover
