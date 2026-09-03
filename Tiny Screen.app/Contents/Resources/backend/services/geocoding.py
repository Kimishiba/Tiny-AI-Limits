import time
import logging
import requests
from datetime import datetime

logger = logging.getLogger("tinyscreen.services.geocoding")

_weather_cache = {"data": None, "timestamp": 0}
_WEATHER_CACHE_TTL_SECONDS = 600

def geocode_city(city_name):
    try:
        url = f"https://geocoding-api.open-meteo.com/v1/search?name={requests.utils.quote(city_name)}&count=1&language=en&format=json"
        res = requests.get(url, timeout=5)
        data = res.json()
        if "results" in data and len(data["results"]) > 0:
            result = data["results"][0]
            name = result.get("name", city_name)
            country = result.get("country_code", "")
            full_name = f"{name}, {country}".upper() if country else name.upper()
            return result["latitude"], result["longitude"], full_name
    except Exception as e:
        print(f"Geocoding error: {e}")
    return None, None, None

def get_location(cfg=None):
    cfg = cfg or {}
    if not cfg.get("auto_location", True):
        return cfg.get("lat", 52.5200), cfg.get("lon", 13.4050), cfg.get("manual_location_name", "BERLIN")
    
    try:
        res = requests.get('http://ip-api.com/json/', timeout=5)
        data = res.json()
        city = data.get('city', 'DETECTED').upper()
        return data['lat'], data['lon'], city
    except Exception:
        return 51.5074, -0.1278, "LONDON"

def get_weather(cfg=None):
    global _weather_cache
    now = time.time()
    if _weather_cache["data"] is not None and (now - _weather_cache["timestamp"]) < _WEATHER_CACHE_TTL_SECONDS:
        return dict(_weather_cache["data"])

    lat, lon, loc_name = get_location(cfg)
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&hourly=precipitation"
        res = requests.get(url, timeout=5)
        data = res.json()
        if res.status_code != 200:
            raise Exception(f"HTTP {res.status_code}: {data.get('reason', data)}")

        current_temp = data['current_weather']['temperature']
        weather_code = data['current_weather'].get('weathercode', data['current_weather'].get('weather_code', 0))

        rain_codes = {51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82, 95, 96, 99}

        hours_until_rain = -1
        if weather_code in rain_codes:
            hours_until_rain = 0
        else:
            hourly_precip = data.get('hourly', {}).get('precipitation', [])
            hourly_times = data.get('hourly', {}).get('time', [])
            current_time = data['current_weather'].get('time', '')
            current_hour_str = current_time[:13] + ":00" if len(current_time) >= 13 else current_time

            try:
                current_index = hourly_times.index(current_hour_str)
                # Cap the rain forecast horizon to next 24 hours and >= 0.1mm
                for i in range(current_index, min(current_index + 24, len(hourly_precip))):
                    if hourly_precip[i] >= 0.1:
                        hours_until_rain = i - current_index
                        break
            except (ValueError, IndexError):
                pass

        result = {
            "temperature": current_temp,
            "temp": current_temp,
            "hours_until_rain": hours_until_rain,
            "date_string": datetime.now().strftime("%a %d %b").upper(),
            "location_name": loc_name,
            "location": loc_name
        }
        _weather_cache["data"] = result
        _weather_cache["timestamp"] = now
        return dict(result)
    except Exception as e:
        print(f"Weather error: {e}")
        result = {
            "temperature": 0.0,
            "temp": 0.0,
            "hours_until_rain": -1,
            "date_string": "ERR",
            "location_name": loc_name,
            "location": loc_name
        }
        return dict(result)
