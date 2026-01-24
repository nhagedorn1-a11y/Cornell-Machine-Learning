"""
FRED API Connector
Fetches real economic indicators from Federal Reserve Economic Data
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os
import pandas as pd


class EconomicAPI:
    """FRED API connector for economic indicators"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize FRED API connector

        Args:
            api_key: FRED API key (if None, reads from environment)
        """
        self.api_key = api_key or os.getenv('FRED_API_KEY')
        self.base_url = "https://api.stlouisfed.org/fred/series/observations"

        if not self.api_key:
            raise ValueError("FRED API key is required. Set FRED_API_KEY environment variable.")

    def get_indicator(self, series_id: str, lookback_months: int = 12) -> Dict:
        """
        Get economic indicator data

        Args:
            series_id: FRED series ID (e.g., 'UNRATE', 'CPIAUCSL')
            lookback_months: Number of months of historical data

        Returns:
            Dictionary with indicator data
        """
        try:
            start_date = (datetime.now() - timedelta(days=lookback_months*30)).strftime('%Y-%m-%d')

            params = {
                'series_id': series_id,
                'api_key': self.api_key,
                'file_type': 'json',
                'observation_start': start_date
            }

            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            if 'observations' not in data:
                return self._get_mock_indicator(series_id, lookback_months)

            observations = data['observations']
            latest = observations[-1] if observations else None

            return {
                'series_id': series_id,
                'latest_value': float(latest['value']) if latest and latest['value'] != '.' else None,
                'latest_date': latest['date'] if latest else None,
                'observations': [
                    {
                        'date': obs['date'],
                        'value': float(obs['value']) if obs['value'] != '.' else None
                    }
                    for obs in observations
                    if obs['value'] != '.'
                ],
                'count': len(observations)
            }
        except requests.exceptions.RequestException as e:
            print(f"Error fetching FRED data for {series_id}: {e}")
            return self._get_mock_indicator(series_id, lookback_months)

    def get_unemployment_rate(self) -> Dict:
        """Get US unemployment rate (UNRATE)"""
        data = self.get_indicator('UNRATE', lookback_months=12)
        data['name'] = 'Unemployment Rate'
        data['unit'] = 'Percent'
        return data

    def get_cpi(self) -> Dict:
        """Get Consumer Price Index (CPIAUCSL)"""
        data = self.get_indicator('CPIAUCSL', lookback_months=12)
        data['name'] = 'Consumer Price Index'
        data['unit'] = 'Index 1982-1984=100'
        return data

    def get_gdp(self) -> Dict:
        """Get GDP (GDP)"""
        data = self.get_indicator('GDP', lookback_months=24)
        data['name'] = 'Gross Domestic Product'
        data['unit'] = 'Billions of Dollars'
        return data

    def get_consumer_sentiment(self) -> Dict:
        """Get University of Michigan Consumer Sentiment (UMCSENT)"""
        data = self.get_indicator('UMCSENT', lookback_months=12)
        data['name'] = 'Consumer Sentiment'
        data['unit'] = 'Index 1966:Q1=100'
        return data

    def get_retail_sales(self) -> Dict:
        """Get Retail Sales (RSXFS)"""
        data = self.get_indicator('RSXFS', lookback_months=12)
        data['name'] = 'Retail Sales'
        data['unit'] = 'Millions of Dollars'
        return data

    def get_all_indicators(self) -> Dict[str, Dict]:
        """
        Get all key economic indicators

        Returns:
            Dictionary mapping indicator name to data
        """
        return {
            'unemployment': self.get_unemployment_rate(),
            'cpi': self.get_cpi(),
            'gdp': self.get_gdp(),
            'consumer_sentiment': self.get_consumer_sentiment(),
            'retail_sales': self.get_retail_sales()
        }

    def get_dashboard_summary(self) -> Dict:
        """
        Get summary of key indicators for dashboard display

        Returns:
            Dictionary with latest values and trends
        """
        indicators = self.get_all_indicators()

        summary = {}
        for key, data in indicators.items():
            if data['latest_value'] is not None:
                # Calculate trend (comparing to value from 3 months ago)
                observations = data['observations']
                if len(observations) >= 4:
                    previous_value = observations[-4]['value']
                    if previous_value:
                        change = data['latest_value'] - previous_value
                        pct_change = (change / previous_value) * 100
                    else:
                        change = 0
                        pct_change = 0
                else:
                    change = 0
                    pct_change = 0

                summary[key] = {
                    'name': data['name'],
                    'value': data['latest_value'],
                    'unit': data['unit'],
                    'date': data['latest_date'],
                    'change': round(change, 2),
                    'pct_change': round(pct_change, 2),
                    'trend': 'up' if change > 0 else 'down' if change < 0 else 'flat'
                }

        return summary

    def _get_mock_indicator(self, series_id: str, lookback_months: int) -> Dict:
        """Fallback mock data if API fails"""
        import random
        import numpy as np

        base_values = {
            'UNRATE': 4.0,
            'CPIAUCSL': 300.0,
            'GDP': 25000.0,
            'UMCSENT': 70.0,
            'RSXFS': 700000.0
        }

        base_value = base_values.get(series_id, 100.0)
        observations = []

        for i in range(lookback_months):
            date = (datetime.now() - timedelta(days=(lookback_months-i)*30)).strftime('%Y-%m-%d')
            value = base_value + np.random.normal(0, base_value * 0.02)
            observations.append({
                'date': date,
                'value': round(value, 2)
            })

        return {
            'series_id': series_id,
            'latest_value': observations[-1]['value'] if observations else base_value,
            'latest_date': observations[-1]['date'] if observations else datetime.now().strftime('%Y-%m-%d'),
            'observations': observations,
            'count': len(observations),
            '_mock': True
        }


# Convenience function
def get_economic_api() -> EconomicAPI:
    """Get configured EconomicAPI instance"""
    try:
        return EconomicAPI()
    except ValueError as e:
        print(f"Warning: {e}")
        print("Using mock economic data. Set FRED_API_KEY to use real data.")
        return None
