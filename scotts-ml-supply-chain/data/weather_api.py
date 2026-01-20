"""
Weather API integration for forecasting
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os


class WeatherForecastAPI:
    """
    Integrate with weather forecast APIs for demand planning
    Supports: OpenWeather, NOAA, WeatherAPI
    """

    def __init__(self, api_key: Optional[str] = None, provider: str = "openweather"):
        self.api_key = api_key or os.getenv("WEATHER_API_KEY")
        self.provider = provider

        self.base_urls = {
            "openweather": "https://api.openweathermap.org/data/2.5",
            "weatherapi": "https://api.weatherapi.com/v1",
            "noaa": "https://www.ncdc.noaa.gov/cdo-web/api/v2"
        }

    def get_forecast(
        self,
        latitude: float,
        longitude: float,
        days: int = 7
    ) -> pd.DataFrame:
        """Get weather forecast for a location"""

        if self.provider == "openweather":
            return self._get_openweather_forecast(latitude, longitude, days)
        elif self.provider == "weatherapi":
            return self._get_weatherapi_forecast(latitude, longitude, days)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    def _get_openweather_forecast(
        self,
        latitude: float,
        longitude: float,
        days: int
    ) -> pd.DataFrame:
        """Get forecast from OpenWeather API"""

        if not self.api_key:
            # Return mock data for prototype
            return self._generate_mock_forecast(latitude, longitude, days)

        url = f"{self.base_urls['openweather']}/forecast"
        params = {
            "lat": latitude,
            "lon": longitude,
            "appid": self.api_key,
            "units": "imperial"  # Fahrenheit
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            # Parse response
            forecasts = []
            for item in data.get('list', []):
                forecasts.append({
                    'date': datetime.fromtimestamp(item['dt']),
                    'temperature_avg': item['main']['temp'],
                    'temperature_max': item['main']['temp_max'],
                    'temperature_min': item['main']['temp_min'],
                    'humidity_percent': item['main']['humidity'],
                    'precipitation_inches': item.get('rain', {}).get('3h', 0) / 25.4,  # mm to inches
                    'weather_description': item['weather'][0]['description']
                })

            df = pd.DataFrame(forecasts)
            return df

        except Exception as e:
            print(f"Error fetching weather forecast: {e}")
            return self._generate_mock_forecast(latitude, longitude, days)

    def _get_weatherapi_forecast(
        self,
        latitude: float,
        longitude: float,
        days: int
    ) -> pd.DataFrame:
        """Get forecast from WeatherAPI.com"""

        if not self.api_key:
            return self._generate_mock_forecast(latitude, longitude, days)

        url = f"{self.base_urls['weatherapi']}/forecast.json"
        params = {
            "key": self.api_key,
            "q": f"{latitude},{longitude}",
            "days": min(days, 10)  # Free tier limit
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            forecasts = []
            for day in data.get('forecast', {}).get('forecastday', []):
                forecasts.append({
                    'date': datetime.strptime(day['date'], '%Y-%m-%d'),
                    'temperature_avg': day['day']['avgtemp_f'],
                    'temperature_max': day['day']['maxtemp_f'],
                    'temperature_min': day['day']['mintemp_f'],
                    'humidity_percent': day['day']['avghumidity'],
                    'precipitation_inches': day['day']['totalprecip_in'],
                    'sunshine_hours': day['day'].get('uv', 5)  # Approximate
                })

            return pd.DataFrame(forecasts)

        except Exception as e:
            print(f"Error fetching weather forecast: {e}")
            return self._generate_mock_forecast(latitude, longitude, days)

    def _generate_mock_forecast(
        self,
        latitude: float,
        longitude: float,
        days: int
    ) -> pd.DataFrame:
        """Generate mock weather forecast for prototype testing"""

        import numpy as np

        # Determine season-based patterns
        month = datetime.now().month
        if month in [3, 4, 5]:  # Spring
            base_temp = 65
            temp_var = 15
        elif month in [6, 7, 8]:  # Summer
            base_temp = 80
            temp_var = 10
        elif month in [9, 10, 11]:  # Fall
            base_temp = 60
            temp_var = 12
        else:  # Winter
            base_temp = 40
            temp_var = 15

        forecasts = []
        for i in range(days):
            date = datetime.now() + timedelta(days=i)

            # Add some randomness
            temp_avg = base_temp + np.random.normal(0, temp_var/2)
            temp_max = temp_avg + np.random.uniform(5, 12)
            temp_min = temp_avg - np.random.uniform(5, 12)

            forecasts.append({
                'date': date,
                'temperature_avg': round(temp_avg, 1),
                'temperature_max': round(temp_max, 1),
                'temperature_min': round(temp_min, 1),
                'humidity_percent': round(np.random.uniform(40, 80), 1),
                'precipitation_inches': round(np.random.exponential(0.1), 2),
                'sunshine_hours': round(np.random.uniform(4, 12), 1)
            })

        df = pd.DataFrame(forecasts)

        # Calculate growing degree days
        df['growing_degree_days'] = df.apply(
            lambda row: max(0, ((row['temperature_max'] + row['temperature_min']) / 2) - 50),
            axis=1
        )

        return df

    def get_historical_weather(
        self,
        latitude: float,
        longitude: float,
        start_date: datetime,
        end_date: datetime
    ) -> pd.DataFrame:
        """Get historical weather data (for model training)"""

        # For prototype, generate synthetic historical data
        days = (end_date - start_date).days

        import numpy as np

        historical = []
        for i in range(days):
            date = start_date + timedelta(days=i)
            month = date.month

            # Seasonal temperature patterns
            if month in [12, 1, 2]:
                base_temp = 35
            elif month in [3, 4, 5]:
                base_temp = 60
            elif month in [6, 7, 8]:
                base_temp = 80
            else:
                base_temp = 55

            temp_avg = base_temp + np.random.normal(0, 10)

            historical.append({
                'date': date,
                'location_zip': '43215',  # Default zip for prototype
                'temperature_avg': round(temp_avg, 1),
                'temperature_max': round(temp_avg + np.random.uniform(5, 12), 1),
                'temperature_min': round(temp_avg - np.random.uniform(5, 12), 1),
                'precipitation_inches': round(np.random.exponential(0.12), 2),
                'humidity_percent': round(np.random.uniform(45, 75), 1),
                'sunshine_hours': round(np.random.uniform(5, 11), 1)
            })

        df = pd.DataFrame(historical)

        # Calculate GDD
        df['growing_degree_days'] = df.apply(
            lambda row: max(0, ((row['temperature_max'] + row['temperature_min']) / 2) - 50),
            axis=1
        )

        return df

    def batch_get_forecasts(
        self,
        locations: List[Dict[str, float]],
        days: int = 7
    ) -> Dict[str, pd.DataFrame]:
        """Get forecasts for multiple locations"""

        forecasts = {}

        for loc in locations:
            store_id = loc.get('store_id', f"{loc['latitude']}_{loc['longitude']}")
            forecast = self.get_forecast(
                latitude=loc['latitude'],
                longitude=loc['longitude'],
                days=days
            )
            forecasts[store_id] = forecast

        return forecasts
