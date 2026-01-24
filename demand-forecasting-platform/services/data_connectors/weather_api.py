"""
OpenWeather API Connector
Fetches real weather data including temperature, precipitation, and forecasts
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os


class WeatherAPI:
    """OpenWeather API connector for real-time and historical weather data"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize weather API connector

        Args:
            api_key: OpenWeather API key (if None, reads from environment)
        """
        self.api_key = api_key or os.getenv('OPENWEATHER_API_KEY')
        self.base_url = "https://api.openweathermap.org/data/2.5"

        if not self.api_key:
            raise ValueError("OpenWeather API key is required. Set OPENWEATHER_API_KEY environment variable.")

    def get_current_weather(self, location: str) -> Dict:
        """
        Get current weather for a location

        Args:
            location: City name (e.g., "Atlanta", "Chicago", "New York")

        Returns:
            Dictionary with weather data
        """
        try:
            url = f"{self.base_url}/weather"
            params = {
                'q': location,
                'appid': self.api_key,
                'units': 'imperial'  # Fahrenheit
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            return {
                'location': location,
                'timestamp': datetime.now().isoformat(),
                'temperature': data['main']['temp'],
                'feels_like': data['main']['feels_like'],
                'humidity': data['main']['humidity'],
                'pressure': data['main']['pressure'],
                'description': data['weather'][0]['description'],
                'wind_speed': data['wind']['speed'],
                'clouds': data.get('clouds', {}).get('all', 0),
                'rain_1h': data.get('rain', {}).get('1h', 0),
                'snow_1h': data.get('snow', {}).get('1h', 0)
            }
        except requests.exceptions.RequestException as e:
            print(f"Error fetching weather data: {e}")
            return self._get_mock_weather(location)

    def get_forecast(self, location: str, days: int = 5) -> List[Dict]:
        """
        Get weather forecast for a location

        Args:
            location: City name
            days: Number of days to forecast (max 5 for free tier)

        Returns:
            List of forecast data points
        """
        try:
            url = f"{self.base_url}/forecast"
            params = {
                'q': location,
                'appid': self.api_key,
                'units': 'imperial',
                'cnt': days * 8  # API returns 3-hour intervals
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            forecasts = []
            for item in data['list']:
                forecasts.append({
                    'timestamp': item['dt_txt'],
                    'temperature': item['main']['temp'],
                    'feels_like': item['main']['feels_like'],
                    'humidity': item['main']['humidity'],
                    'description': item['weather'][0]['description'],
                    'wind_speed': item['wind']['speed'],
                    'precipitation_prob': item.get('pop', 0) * 100,  # Probability of precipitation
                    'rain_3h': item.get('rain', {}).get('3h', 0)
                })

            return forecasts
        except requests.exceptions.RequestException as e:
            print(f"Error fetching forecast data: {e}")
            return self._get_mock_forecast(location, days)

    def calculate_degree_days(self, temperature: float, base_temp: float = 65) -> Dict:
        """
        Calculate heating and cooling degree days

        Args:
            temperature: Current temperature in Fahrenheit
            base_temp: Base temperature (default 65°F)

        Returns:
            Dictionary with heating and cooling degree days
        """
        return {
            'heating_degree_days': max(0, base_temp - temperature),
            'cooling_degree_days': max(0, temperature - base_temp)
        }

    def get_weather_for_multiple_locations(self, locations: List[str]) -> Dict[str, Dict]:
        """
        Get current weather for multiple locations

        Args:
            locations: List of city names

        Returns:
            Dictionary mapping location to weather data
        """
        results = {}
        for location in locations:
            results[location] = self.get_current_weather(location)
        return results

    def _get_mock_weather(self, location: str) -> Dict:
        """Fallback mock weather data if API fails"""
        import random
        return {
            'location': location,
            'timestamp': datetime.now().isoformat(),
            'temperature': random.uniform(50, 85),
            'feels_like': random.uniform(50, 85),
            'humidity': random.uniform(30, 80),
            'pressure': random.uniform(29.8, 30.2),
            'description': 'partly cloudy',
            'wind_speed': random.uniform(0, 15),
            'clouds': random.uniform(0, 100),
            'rain_1h': 0,
            'snow_1h': 0,
            '_mock': True
        }

    def _get_mock_forecast(self, location: str, days: int) -> List[Dict]:
        """Fallback mock forecast data if API fails"""
        import random
        forecasts = []
        for i in range(days * 8):
            timestamp = datetime.now() + timedelta(hours=i*3)
            forecasts.append({
                'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'temperature': random.uniform(50, 85),
                'feels_like': random.uniform(50, 85),
                'humidity': random.uniform(30, 80),
                'description': 'partly cloudy',
                'wind_speed': random.uniform(0, 15),
                'precipitation_prob': random.uniform(0, 50),
                'rain_3h': 0,
                '_mock': True
            })
        return forecasts


# Convenience function
def get_weather_api() -> WeatherAPI:
    """Get configured WeatherAPI instance"""
    try:
        return WeatherAPI()
    except ValueError as e:
        print(f"Warning: {e}")
        print("Using mock weather data. Set OPENWEATHER_API_KEY to use real data.")
        return None
