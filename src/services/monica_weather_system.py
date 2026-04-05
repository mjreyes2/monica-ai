"""
Monica AI - Global Weather System

Provides real-time weather data for any location and global weather pattern
visualization for the holographic globe.

Features:
- Current weather for any city/coordinates (Open-Meteo API - free, no key)
- 7-day forecast
- Global weather overlay data for globe rendering (cloud cover, temp, wind)
- Weather alerts and severe conditions
- Satellite cloud imagery URLs (GOES-16, Himawari, Meteosat)
- Radar imagery URLs

Usage:
    from services.monica_weather_system import get_weather_system
    ws = get_weather_system()
    weather = ws.get_weather("Orlando, FL")
    globe_data = ws.get_globe_weather_overlay()
"""

import json
import logging
import math
import time
import urllib.request
import urllib.error
import urllib.parse
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger("Monica.Weather")


@dataclass
class CurrentWeather:
    """Current weather conditions."""
    location: str
    lat: float
    lng: float
    temperature_c: float
    temperature_f: float
    feels_like_c: float
    humidity: int
    wind_speed_kmh: float
    wind_direction: int
    weather_code: int
    description: str
    cloud_cover: int  # percentage
    precipitation_mm: float
    visibility_km: float
    pressure_hpa: float
    uv_index: float
    is_day: bool
    timestamp: str


@dataclass
class DayForecast:
    """One day of weather forecast."""
    date: str
    temp_max_c: float
    temp_min_c: float
    weather_code: int
    description: str
    precipitation_sum_mm: float
    precipitation_probability: int
    wind_speed_max_kmh: float
    uv_index_max: float
    sunrise: str
    sunset: str


@dataclass
class WeatherAlert:
    """A weather alert/warning."""
    severity: str  # minor, moderate, severe, extreme
    event: str
    description: str
    location: str


# WMO Weather interpretation codes
WMO_CODES = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Foggy", 48: "Rime fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    56: "Light freezing drizzle", 57: "Dense freezing drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    66: "Light freezing rain", 67: "Heavy freezing rain",
    71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
    77: "Snow grains", 80: "Slight rain showers", 81: "Moderate rain showers",
    82: "Violent rain showers", 85: "Slight snow showers", 86: "Heavy snow showers",
    95: "Thunderstorm", 96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail",
}


class WeatherSystem:
    """
    Global weather system using Open-Meteo API (free, no API key, unlimited).
    """

    GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
    WEATHER_URL = "https://api.open-meteo.com/v1/forecast"

    # Satellite imagery URLs for globe overlay
    SATELLITE_IMAGERY = {
        "goes_east_full": "https://cdn.star.nesdis.noaa.gov/GOES16/ABI/FD/GEOCOLOR/latest.jpg",
        "goes_east_conus": "https://cdn.star.nesdis.noaa.gov/GOES16/ABI/CONUS/GEOCOLOR/latest.jpg",
        "goes_west_full": "https://cdn.star.nesdis.noaa.gov/GOES18/ABI/FD/GEOCOLOR/latest.jpg",
        "himawari_full": "https://www.data.jma.go.jp/mscweb/data/himawari/img/fd_/fd__trm_0000.jpg",
        "meteosat_full": "https://eumetview.eumetsat.int/static-images/latestImages/EUMETSAT_MSG_RGBNatColourEnhncd_LargeFullResolution.jpg",
    }

    # Global radar/precipitation imagery
    RADAR_IMAGERY = {
        "global_precipitation": "https://tile.openweathermap.org/map/precipitation_new/{z}/{x}/{y}.png",
        "global_clouds": "https://tile.openweathermap.org/map/clouds_new/{z}/{x}/{y}.png",
        "global_temp": "https://tile.openweathermap.org/map/temp_new/{z}/{x}/{y}.png",
        "global_wind": "https://tile.openweathermap.org/map/wind_new/{z}/{x}/{y}.png",
    }

    # Grid of global weather sample points for globe overlay
    GLOBE_GRID_POINTS = []
    for _lat in range(-80, 81, 20):
        for _lng in range(-180, 180, 30):
            GLOBE_GRID_POINTS.append((_lat, _lng))

    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._cache_ttl: Dict[str, float] = {}
        self._geocode_cache: Dict[str, Tuple[float, float]] = {}
        logger.info(f"Weather System initialized ({len(self.GLOBE_GRID_POINTS)} globe grid points)")

    def _fetch_json(self, url: str, timeout: int = 10) -> Optional[Dict]:
        if url in self._cache and time.time() - self._cache_ttl.get(url, 0) < 300:
            return self._cache[url]
        try:
            headers = {"User-Agent": "MonicaAI/1.0 (Weather Assistant)"}
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                self._cache[url] = data
                self._cache_ttl[url] = time.time()
                return data
        except Exception as e:
            logger.debug(f"Weather API error: {e}")
            return None

    def _geocode(self, location: str) -> Optional[Tuple[float, float, str]]:
        """Geocode a location name to lat/lng."""
        loc_lower = location.lower().strip()
        if loc_lower in self._geocode_cache:
            lat, lng = self._geocode_cache[loc_lower]
            return (lat, lng, location)

        encoded = urllib.parse.quote(location)
        url = f"{self.GEOCODE_URL}?name={encoded}&count=1&language=en"
        data = self._fetch_json(url)
        if data and data.get("results"):
            r = data["results"][0]
            lat = r["latitude"]
            lng = r["longitude"]
            name = r.get("name", location)
            self._geocode_cache[loc_lower] = (lat, lng)
            return (lat, lng, name)
        return None

    def get_weather(self, location: str) -> Optional[CurrentWeather]:
        """Get current weather for a location (city name or 'lat,lng')."""
        # Parse location
        if "," in location and all(p.strip().replace("-", "").replace(".", "").isdigit()
                                    for p in location.split(",")[:2]):
            parts = location.split(",")
            lat, lng, name = float(parts[0]), float(parts[1]), location
        else:
            result = self._geocode(location)
            if not result:
                return None
            lat, lng, name = result

        url = (f"{self.WEATHER_URL}?latitude={lat}&longitude={lng}"
               f"&current=temperature_2m,relative_humidity_2m,apparent_temperature,"
               f"weather_code,cloud_cover,wind_speed_10m,wind_direction_10m,"
               f"precipitation,surface_pressure,visibility,uv_index,is_day"
               f"&temperature_unit=celsius&wind_speed_unit=kmh")

        data = self._fetch_json(url)
        if not data or "current" not in data:
            return None

        c = data["current"]
        temp_c = c.get("temperature_2m", 0)
        code = c.get("weather_code", 0)

        return CurrentWeather(
            location=name,
            lat=lat,
            lng=lng,
            temperature_c=temp_c,
            temperature_f=temp_c * 9 / 5 + 32,
            feels_like_c=c.get("apparent_temperature", temp_c),
            humidity=c.get("relative_humidity_2m", 0),
            wind_speed_kmh=c.get("wind_speed_10m", 0),
            wind_direction=c.get("wind_direction_10m", 0),
            weather_code=code,
            description=WMO_CODES.get(code, "Unknown"),
            cloud_cover=c.get("cloud_cover", 0),
            precipitation_mm=c.get("precipitation", 0),
            visibility_km=c.get("visibility", 10000) / 1000,
            pressure_hpa=c.get("surface_pressure", 1013),
            uv_index=c.get("uv_index", 0),
            is_day=bool(c.get("is_day", 1)),
            timestamp=c.get("time", ""),
        )

    def get_forecast(self, location: str, days: int = 7) -> List[DayForecast]:
        """Get multi-day forecast."""
        result = self._geocode(location)
        if not result:
            return []
        lat, lng, name = result

        url = (f"{self.WEATHER_URL}?latitude={lat}&longitude={lng}"
               f"&daily=temperature_2m_max,temperature_2m_min,weather_code,"
               f"precipitation_sum,precipitation_probability_max,"
               f"wind_speed_10m_max,uv_index_max,sunrise,sunset"
               f"&temperature_unit=celsius&forecast_days={days}")

        data = self._fetch_json(url)
        if not data or "daily" not in data:
            return []

        d = data["daily"]
        forecasts = []
        for i in range(len(d.get("time", []))):
            code = d["weather_code"][i] if d.get("weather_code") else 0
            forecasts.append(DayForecast(
                date=d["time"][i],
                temp_max_c=d.get("temperature_2m_max", [0])[i],
                temp_min_c=d.get("temperature_2m_min", [0])[i],
                weather_code=code,
                description=WMO_CODES.get(code, "Unknown"),
                precipitation_sum_mm=d.get("precipitation_sum", [0])[i] or 0,
                precipitation_probability=d.get("precipitation_probability_max", [0])[i] or 0,
                wind_speed_max_kmh=d.get("wind_speed_10m_max", [0])[i] or 0,
                uv_index_max=d.get("uv_index_max", [0])[i] or 0,
                sunrise=d.get("sunrise", [""])[i] or "",
                sunset=d.get("sunset", [""])[i] or "",
            ))

        return forecasts

    def get_globe_weather_overlay(self) -> List[Dict[str, Any]]:
        """
        Get weather data for globe grid points to render weather patterns.
        Returns list of {lat, lng, cloud_cover, temp_c, wind_kmh, weather_code, description}
        for rendering on the holographic globe.
        """
        # Batch request for all grid points (Open-Meteo supports multi-location)
        results = []

        # Process in batches of ~20 to avoid URL length limits
        for i in range(0, len(self.GLOBE_GRID_POINTS), 20):
            batch = self.GLOBE_GRID_POINTS[i:i + 20]
            lats = ",".join(str(p[0]) for p in batch)
            lngs = ",".join(str(p[1]) for p in batch)

            url = (f"{self.WEATHER_URL}?latitude={lats}&longitude={lngs}"
                   f"&current=temperature_2m,cloud_cover,wind_speed_10m,weather_code")

            data = self._fetch_json(url, timeout=15)
            if not data:
                continue

            # Open-Meteo returns array for multi-location
            if isinstance(data, list):
                for j, item in enumerate(data):
                    if j < len(batch) and "current" in item:
                        c = item["current"]
                        results.append({
                            "lat": batch[j][0],
                            "lng": batch[j][1],
                            "cloud_cover": c.get("cloud_cover", 0),
                            "temp_c": c.get("temperature_2m", 0),
                            "wind_kmh": c.get("wind_speed_10m", 0),
                            "weather_code": c.get("weather_code", 0),
                            "description": WMO_CODES.get(c.get("weather_code", 0), ""),
                        })
            elif "current" in data:
                # Single result (only first point)
                c = data["current"]
                results.append({
                    "lat": batch[0][0],
                    "lng": batch[0][1],
                    "cloud_cover": c.get("cloud_cover", 0),
                    "temp_c": c.get("temperature_2m", 0),
                    "wind_kmh": c.get("wind_speed_10m", 0),
                    "weather_code": c.get("weather_code", 0),
                    "description": WMO_CODES.get(c.get("weather_code", 0), ""),
                })

        return results

    def get_satellite_imagery_urls(self) -> Dict[str, str]:
        """Get satellite cloud imagery URLs for globe overlay."""
        return dict(self.SATELLITE_IMAGERY)

    def get_weather_summary(self, location: str) -> str:
        """Get a human-readable weather summary for a location."""
        weather = self.get_weather(location)
        if not weather:
            return f"Could not get weather for '{location}'."

        parts = [
            f"Weather in {weather.location}:",
            f"  {weather.description}, {weather.temperature_f:.0f}F ({weather.temperature_c:.0f}C)",
            f"  Feels like: {weather.feels_like_c * 9/5 + 32:.0f}F",
            f"  Humidity: {weather.humidity}%",
            f"  Wind: {weather.wind_speed_kmh:.0f} km/h",
            f"  Cloud cover: {weather.cloud_cover}%",
        ]

        if weather.precipitation_mm > 0:
            parts.append(f"  Precipitation: {weather.precipitation_mm:.1f} mm")
        if weather.uv_index > 5:
            parts.append(f"  UV Index: {weather.uv_index:.0f} (HIGH - wear sunscreen!)")

        forecast = self.get_forecast(location, days=3)
        if forecast:
            parts.append("\nForecast:")
            for day in forecast:
                parts.append(f"  {day.date}: {day.description}, "
                             f"{day.temp_max_c * 9/5 + 32:.0f}F / {day.temp_min_c * 9/5 + 32:.0f}F"
                             f"{f', {day.precipitation_probability}% rain' if day.precipitation_probability > 20 else ''}")

        return "\n".join(parts)

    def get_status(self) -> Dict[str, Any]:
        return {
            "available": True,
            "grid_points": len(self.GLOBE_GRID_POINTS),
            "satellite_sources": len(self.SATELLITE_IMAGERY),
            "cache_entries": len(self._cache),
        }


# Singleton
_weather_system: Optional[WeatherSystem] = None


def get_weather_system() -> WeatherSystem:
    global _weather_system
    if _weather_system is None:
        _weather_system = WeatherSystem()
    return _weather_system
