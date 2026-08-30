import os
import sys
import unittest
from unittest.mock import patch, MagicMock
import requests
from datetime import datetime, timedelta

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import app

class TestGeocoding(unittest.TestCase):
    @patch('app.requests.get')
    def test_geocode_city_success_with_country_code(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [{
                "name": "Rome",
                "country_code": "IT",
                "latitude": 41.9,
                "longitude": 12.5
            }]
        }
        mock_get.return_value = mock_response

        lat, lon, location_name = app.geocode_city("Rome")
        self.assertEqual(lat, 41.9)
        self.assertEqual(lon, 12.5)
        self.assertEqual(location_name, "ROME, IT")

    @patch('app.requests.get')
    def test_geocode_city_success_without_country_code(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [{
                "name": "Rome",
                "latitude": 41.9,
                "longitude": 12.5
            }]
        }
        mock_get.return_value = mock_response

        lat, lon, location_name = app.geocode_city("Rome")
        self.assertEqual(lat, 41.9)
        self.assertEqual(lon, 12.5)
        self.assertEqual(location_name, "ROME")

    @patch('app.requests.get')
    def test_geocode_city_empty_results(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {"results": []}
        mock_get.return_value = mock_response

        lat, lon, location_name = app.geocode_city("Nonexistent City")
        self.assertIsNone(lat)
        self.assertIsNone(lon)
        self.assertIsNone(location_name)

    @patch('app.requests.get')
    def test_geocode_city_network_exception(self, mock_get):
        mock_get.side_effect = requests.exceptions.RequestException("Network error")

        lat, lon, location_name = app.geocode_city("Rome")
        self.assertIsNone(lat)
        self.assertIsNone(lon)
        self.assertIsNone(location_name)

class TestLocation(unittest.TestCase):
    def test_get_location_manual(self):
        with patch.dict(app.config, {"auto_location": False, "lat": 41.9, "lon": 12.5, "manual_location_name": "ROME"}):
            lat, lon, location_name = app.get_location()
            self.assertEqual(lat, 41.9)
            self.assertEqual(lon, 12.5)
            self.assertEqual(location_name, "ROME")

    @patch('app.requests.get')
    def test_get_location_auto_success(self, mock_get):
        with patch.dict(app.config, {"auto_location": True}):
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "lat": 35.6,
                "lon": 139.6,
                "city": "Tokyo"
            }
            mock_get.return_value = mock_response

            lat, lon, location_name = app.get_location()
            self.assertEqual(lat, 35.6)
            self.assertEqual(lon, 139.6)
            self.assertEqual(location_name, "TOKYO")

    @patch('app.requests.get')
    def test_get_location_auto_fallback(self, mock_get):
        with patch.dict(app.config, {"auto_location": True}):
            mock_get.side_effect = requests.exceptions.RequestException("Network error")

            lat, lon, location_name = app.get_location()
            self.assertEqual(lat, 51.5074)
            self.assertEqual(lon, -0.1278)
            self.assertEqual(location_name, "LONDON")

class TestWeather(unittest.TestCase):
    def setUp(self):
        app._weather_cache = {"data": None, "timestamp": 0}

    def tearDown(self):
        app._weather_cache = {"data": None, "timestamp": 0}

    @patch('app.get_location', return_value=(41.9, 12.5, "ROME"))
    @patch('app.requests.get')
    def test_get_weather_caching(self, mock_get, mock_loc):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "current_weather": {"temperature": 22.0, "weathercode": 0, "time": "2026-08-30T18:00"},
            "hourly": {"time": ["2026-08-30T18:00"], "precipitation": [0.0]}
        }
        mock_get.return_value = mock_response

        weather1 = app.get_weather()
        weather2 = app.get_weather()

        self.assertEqual(mock_get.call_count, 1)
        self.assertEqual(weather1, weather2)
        self.assertEqual(weather1["temperature"], 22.0)
        self.assertEqual(weather1["location_name"], "ROME")

    @patch('app.get_location', return_value=(41.9, 12.5, "ROME"))
    @patch('app.requests.get')
    def test_get_weather_current_rain_code(self, mock_get, mock_loc):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "current_weather": {"temperature": 18.5, "weathercode": 61, "time": "2026-08-30T18:00"},
            "hourly": {"time": ["2026-08-30T18:00"], "precipitation": [1.5]}
        }
        mock_get.return_value = mock_response

        weather = app.get_weather()
        self.assertEqual(weather["hours_until_rain"], 0)
        self.assertEqual(weather["temperature"], 18.5)

    @patch('app.get_location', return_value=(41.9, 12.5, "ROME"))
    @patch('app.requests.get')
    def test_get_weather_upcoming_rain_hourly(self, mock_get, mock_loc):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "current_weather": {"temperature": 20.0, "weathercode": 1, "time": "2026-08-30T12:00"},
            "hourly": {
                "time": [
                    "2026-08-30T12:00",
                    "2026-08-30T13:00",
                    "2026-08-30T14:00",
                    "2026-08-30T15:00"
                ],
                "precipitation": [0.0, 0.0, 0.0, 2.5]
            }
        }
        mock_get.return_value = mock_response

        weather = app.get_weather()
        self.assertEqual(weather["hours_until_rain"], 3)

    @patch('app.get_location', return_value=(41.9, 12.5, "ROME"))
    @patch('app.requests.get')
    def test_get_weather_no_rain_in_forecast(self, mock_get, mock_loc):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "current_weather": {"temperature": 25.0, "weathercode": 0, "time": "2026-08-30T12:00"},
            "hourly": {
                "time": ["2026-08-30T12:00", "2026-08-30T13:00"],
                "precipitation": [0.0, 0.0]
            }
        }
        mock_get.return_value = mock_response

        weather = app.get_weather()
        self.assertEqual(weather["hours_until_rain"], -1)

    @patch('app.get_location', return_value=(41.9, 12.5, "ROME"))
    @patch('app.requests.get')
    def test_get_weather_http_error(self, mock_get, mock_loc):
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.json.return_value = {"reason": "Daily request limit exceeded"}
        mock_get.return_value = mock_response

        weather = app.get_weather()
        self.assertEqual(weather["date_string"], "ERR")
        self.assertEqual(weather["temperature"], 0.0)
        self.assertEqual(weather["location_name"], "ROME")

    @patch('app.get_location', return_value=(41.9, 12.5, "ROME"))
    @patch('app.requests.get')
    def test_get_weather_network_timeout(self, mock_get, mock_loc):
        mock_get.side_effect = requests.exceptions.Timeout("Connection timed out")

        weather = app.get_weather()
        self.assertEqual(weather["date_string"], "ERR")
        self.assertEqual(weather["temperature"], 0.0)
        self.assertEqual(weather["location_name"], "ROME")

if __name__ == '__main__':
    unittest.main()
