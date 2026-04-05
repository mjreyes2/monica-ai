"""
Monica AI - Satellite Services

Provides access to satellite data, ISS tracking, NASA imagery,
asteroid tracking, people in space, and weather satellite feeds.

All data from free public APIs (no API keys required for most):
- Open Notify (ISS position, people in space)
- NASA APOD & NEO APIs (free API key: DEMO_KEY)
- GOES-16 weather satellite imagery (NOAA)

Usage:
    from utils.satellite_services import get_satellite_services
    sat = get_satellite_services()
    iss = sat.get_iss_position()
    people = sat.get_people_in_space()
"""

import json
import logging
import time
import urllib.request
import urllib.error
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

logger = logging.getLogger("Monica.Satellite")

# NASA DEMO_KEY - free, 30 requests/hour, 50/day - sufficient for personal use
NASA_API_KEY = "DEMO_KEY"


@dataclass
class ISSPosition:
    latitude: float
    longitude: float
    altitude_km: float
    velocity_km_s: float
    timestamp: float
    visibility: str = "unknown"


@dataclass
class Astronaut:
    name: str
    craft: str


class SatelliteServices:
    """Access satellite data from free public APIs."""

    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._cache_ttl: Dict[str, float] = {}
        logger.info("Satellite Services initialized")

    def _fetch_json(self, url: str, timeout: int = 15) -> Optional[Dict]:
        """Fetch JSON from a URL with caching."""
        # Check cache (60 second TTL for most endpoints)
        if url in self._cache and time.time() - self._cache_ttl.get(url, 0) < 60:
            return self._cache[url]

        try:
            headers = {"User-Agent": "MonicaAI/1.0 (Educational Satellite Tracker)"}
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                self._cache[url] = data
                self._cache_ttl[url] = time.time()
                return data
        except Exception as e:
            logger.debug(f"Satellite API error ({url[:60]}): {e}")
            return None

    # ==================== ISS Tracking ====================

    def get_iss_position(self) -> Optional[ISSPosition]:
        """Get current ISS position using Open Notify API."""
        data = self._fetch_json("http://api.open-notify.org/iss-now.json")
        if not data or data.get("message") != "success":
            return None

        pos = data.get("iss_position", {})
        lat = float(pos.get("latitude", 0))
        lon = float(pos.get("longitude", 0))

        return ISSPosition(
            latitude=lat,
            longitude=lon,
            altitude_km=408.0,  # Average ISS altitude
            velocity_km_s=7.66,  # Average ISS orbital velocity
            timestamp=data.get("timestamp", time.time()),
        )

    def get_iss_pass_times(self, lat: float, lon: float, n: int = 5) -> List[Dict]:
        """Get upcoming ISS pass times for a location."""
        url = f"http://api.open-notify.org/iss-pass.json?lat={lat}&lon={lon}&n={n}"
        data = self._fetch_json(url)
        if not data or data.get("message") != "success":
            return []

        passes = []
        for p in data.get("response", []):
            passes.append({
                "risetime": datetime.fromtimestamp(p["risetime"]).strftime("%Y-%m-%d %H:%M:%S"),
                "duration_seconds": p["duration"],
                "duration_minutes": round(p["duration"] / 60, 1),
            })
        return passes

    # ==================== People in Space ====================

    def get_people_in_space(self) -> Dict[str, Any]:
        """Get list of people currently in space."""
        data = self._fetch_json("http://api.open-notify.org/astros.json")
        if not data or data.get("message") != "success":
            return {"count": 0, "people": []}

        people = []
        for p in data.get("people", []):
            people.append(Astronaut(name=p.get("name", "Unknown"), craft=p.get("craft", "Unknown")))

        return {
            "count": data.get("number", len(people)),
            "people": people,
        }

    # ==================== NASA APIs ====================

    def get_nasa_apod(self) -> Optional[Dict]:
        """Get NASA Astronomy Picture of the Day."""
        url = f"https://api.nasa.gov/planetary/apod?api_key={NASA_API_KEY}"
        data = self._fetch_json(url)
        if not data:
            return None

        return {
            "title": data.get("title", ""),
            "date": data.get("date", ""),
            "explanation": data.get("explanation", ""),
            "url": data.get("url", ""),
            "hdurl": data.get("hdurl", ""),
            "media_type": data.get("media_type", "image"),
        }

    def get_neo_asteroids(self, days: int = 7) -> List[Dict]:
        """Get Near Earth Objects (asteroids) approaching in next N days."""
        start = datetime.now().strftime("%Y-%m-%d")
        end = (datetime.now() + timedelta(days=min(days, 7))).strftime("%Y-%m-%d")
        url = (f"https://api.nasa.gov/neo/rest/v1/feed?"
               f"start_date={start}&end_date={end}&api_key={NASA_API_KEY}")

        data = self._fetch_json(url, timeout=20)
        if not data:
            return []

        asteroids = []
        for date_str, neos in data.get("near_earth_objects", {}).items():
            for neo in neos:
                close = neo.get("close_approach_data", [{}])[0] if neo.get("close_approach_data") else {}
                miss_km = float(close.get("miss_distance", {}).get("kilometers", 0))
                diameter = neo.get("estimated_diameter", {}).get("meters", {})
                asteroids.append({
                    "name": neo.get("name", "Unknown"),
                    "id": neo.get("id", ""),
                    "is_hazardous": neo.get("is_potentially_hazardous_asteroid", False),
                    "close_approach_date": close.get("close_approach_date", date_str),
                    "miss_distance_km": miss_km,
                    "relative_velocity_kph": float(close.get("relative_velocity", {}).get("kilometers_per_hour", 0)),
                    "diameter_min_m": diameter.get("estimated_diameter_min", 0),
                    "diameter_max_m": diameter.get("estimated_diameter_max", 0),
                    "nasa_url": neo.get("nasa_jpl_url", ""),
                })

        asteroids.sort(key=lambda a: a["close_approach_date"])
        return asteroids

    def get_mars_weather(self) -> Optional[Dict]:
        """Get latest Mars weather data from NASA InSight."""
        url = f"https://api.nasa.gov/insight_weather/?api_key={NASA_API_KEY}&feedtype=json&ver=1.0"
        data = self._fetch_json(url)
        if not data:
            return None

        sol_keys = data.get("sol_keys", [])
        if not sol_keys:
            return {"status": "No recent Mars weather data available"}

        latest_sol = sol_keys[-1]
        sol_data = data.get(latest_sol, {})
        temp = sol_data.get("AT", {})
        wind = sol_data.get("HWS", {})

        return {
            "sol": latest_sol,
            "earth_date": sol_data.get("First_UTC", ""),
            "temperature_avg_c": temp.get("av"),
            "temperature_min_c": temp.get("mn"),
            "temperature_max_c": temp.get("mx"),
            "wind_speed_avg_ms": wind.get("av"),
            "season": sol_data.get("Season", ""),
        }

    # ==================== Weather Satellite Imagery ====================

    def get_weather_satellite_imagery(self) -> Dict[str, str]:
        """Get latest GOES-16 weather satellite imagery URLs."""
        base = "https://cdn.star.nesdis.noaa.gov/GOES16/ABI"
        return {
            "full_disk": f"{base}/FD/GEOCOLOR/latest.jpg",
            "conus": f"{base}/CONUS/GEOCOLOR/latest.jpg",
            "northeast_us": f"{base}/SECTOR/ne/GEOCOLOR/latest.jpg",
            "southeast_us": f"{base}/SECTOR/se/GEOCOLOR/latest.jpg",
            "gulf_mexico": f"{base}/SECTOR/gm/GEOCOLOR/latest.jpg",
            "caribbean": f"{base}/SECTOR/car/GEOCOLOR/latest.jpg",
            "tropical_atlantic": f"{base}/SECTOR/taw/GEOCOLOR/latest.jpg",
        }

    # ==================== Satellite Tracking URLs ====================

    def get_satellite_map_url(self, satellite: str = "iss") -> str:
        """Get a live tracking map URL for a satellite."""
        tracking_urls = {
            "iss": "https://www.astroviewer.net/iss/en/",
            "hubble": "https://spotthestation.nasa.gov/",
            "starlink": "https://satellitemap.space/",
            "general": "https://www.n2yo.com/",
        }
        return tracking_urls.get(satellite.lower(), tracking_urls["general"])

    def get_satellite_list(self) -> List[Dict]:
        """Get a list of notable satellites with tracking info."""
        return [
            {"name": "International Space Station (ISS)", "norad_id": 25544,
             "type": "crewed", "altitude_km": 408, "track_url": self.get_satellite_map_url("iss")},
            {"name": "Hubble Space Telescope", "norad_id": 20580,
             "type": "telescope", "altitude_km": 540, "track_url": self.get_satellite_map_url("hubble")},
            {"name": "Tiangong (China Space Station)", "norad_id": 54216,
             "type": "crewed", "altitude_km": 380, "track_url": self.get_satellite_map_url("general")},
            {"name": "James Webb Space Telescope", "norad_id": 50463,
             "type": "telescope", "altitude_km": 1500000, "track_url": "https://jwst.nasa.gov/content/webbLaunch/whereIsWebb.html"},
            {"name": "GOES-16 (Weather)", "norad_id": 41866,
             "type": "weather", "altitude_km": 35786, "track_url": self.get_satellite_map_url("general")},
        ]

    # ==================== Space Summary ====================

    def get_space_summary(self) -> str:
        """Get a comprehensive space status summary."""
        parts = ["=== SPACE STATUS SUMMARY ===\n"]

        # ISS
        iss = self.get_iss_position()
        if iss:
            parts.append(f"ISS Position: {iss.latitude:.2f}N, {iss.longitude:.2f}E")
            parts.append(f"  Altitude: {iss.altitude_km:.0f} km | Speed: {iss.velocity_km_s * 3600:.0f} km/h")
            parts.append(f"  Live tracking: {self.get_satellite_map_url('iss')}")

        # People in space
        astros = self.get_people_in_space()
        if astros["count"] > 0:
            parts.append(f"\nPeople in space: {astros['count']}")
            for p in astros["people"]:
                parts.append(f"  - {p.name} ({p.craft})")

        # NASA APOD
        apod = self.get_nasa_apod()
        if apod:
            parts.append(f"\nNASA Picture of the Day: {apod['title']}")
            parts.append(f"  {apod['explanation'][:200]}...")

        # Hazardous asteroids
        try:
            neos = self.get_neo_asteroids(days=7)
            hazardous = [a for a in neos if a["is_hazardous"]]
            if hazardous:
                parts.append(f"\nPotentially Hazardous Asteroids (next 7 days): {len(hazardous)}")
                for a in hazardous[:3]:
                    parts.append(f"  - {a['name']}: {a['miss_distance_km']:,.0f} km away on {a['close_approach_date']}")
            else:
                parts.append(f"\nNear Earth Asteroids (next 7 days): {len(neos)} total, 0 hazardous")
        except Exception:
            pass

        # Weather satellite
        imagery = self.get_weather_satellite_imagery()
        parts.append(f"\nWeather Satellite (GOES-16): {imagery['full_disk']}")

        return "\n".join(parts)

    def get_status(self) -> Dict[str, Any]:
        """Get service status."""
        return {
            "available": True,
            "apis": ["Open Notify (ISS)", "NASA APOD", "NASA NEO", "GOES-16 Weather"],
            "cache_entries": len(self._cache),
        }


# Singleton
_satellite_services = None


def get_satellite_services() -> SatelliteServices:
    global _satellite_services
    if _satellite_services is None:
        _satellite_services = SatelliteServices()
    return _satellite_services
