"""
Monica AI - Satellite Data System

Provides accurate geocoding, satellite imagery (NASA GIBS), and globe
coordinate math for the hologram system.

Components:
- AccurateGeocoder: Resolves place names to lat/lng using free APIs
- GIBSClient: Fetches NASA GIBS satellite imagery tiles
- GlobeCoordinateSystem: Math for projecting lat/lng onto a 3D globe

Usage:
    from services.monica_satellite_data import get_geocoder, get_gibs_client, GlobeCoordinateSystem
    geocoder = get_geocoder()
    location = geocoder.geocode("New York")
    gibs = get_gibs_client()
    imagery = gibs.get_tile(lat, lng)
"""

import json
import logging
import math
import time
import urllib.request
import urllib.error
from dataclasses import dataclass
from typing import Optional, Dict, Any, List, Tuple

logger = logging.getLogger("Monica.SatelliteData")


# ==================== Data Classes ====================

@dataclass
class GeoLocation:
    """A geocoded location with coordinates and metadata."""
    name: str
    lat: float
    lng: float
    country: str = ""
    state: str = ""
    population: int = 0
    timezone: str = ""
    display_name: str = ""


# ==================== Geocoder ====================

class AccurateGeocoder:
    """
    Resolves place names to lat/lng coordinates using free APIs.
    
    Uses Nominatim (OpenStreetMap) as primary - free, no API key.
    Has a built-in cache of major cities for instant offline lookups.
    """

    def __init__(self):
        self._cache: Dict[str, GeoLocation] = {}
        self._request_timestamps: List[float] = []
        self._load_builtin_cities()
        logger.info("AccurateGeocoder initialized")

    def _load_builtin_cities(self):
        """Pre-load major world cities for instant offline lookups."""
        cities = {
            "new york": GeoLocation("New York", 40.7128, -74.0060, "United States", "New York", 8336817),
            "los angeles": GeoLocation("Los Angeles", 34.0522, -118.2437, "United States", "California", 3979576),
            "chicago": GeoLocation("Chicago", 41.8781, -87.6298, "United States", "Illinois", 2693976),
            "houston": GeoLocation("Houston", 29.7604, -95.3698, "United States", "Texas", 2320268),
            "phoenix": GeoLocation("Phoenix", 33.4484, -112.0740, "United States", "Arizona", 1680992),
            "philadelphia": GeoLocation("Philadelphia", 39.9526, -75.1652, "United States", "Pennsylvania", 1584064),
            "san antonio": GeoLocation("San Antonio", 29.4241, -98.4936, "United States", "Texas", 1547253),
            "san diego": GeoLocation("San Diego", 32.7157, -117.1611, "United States", "California", 1423851),
            "dallas": GeoLocation("Dallas", 32.7767, -96.7970, "United States", "Texas", 1343573),
            "miami": GeoLocation("Miami", 25.7617, -80.1918, "United States", "Florida", 467963),
            "orlando": GeoLocation("Orlando", 28.5383, -81.3792, "United States", "Florida", 307573),
            "atlanta": GeoLocation("Atlanta", 33.7490, -84.3880, "United States", "Georgia", 498715),
            "seattle": GeoLocation("Seattle", 47.6062, -122.3321, "United States", "Washington", 737015),
            "denver": GeoLocation("Denver", 39.7392, -104.9903, "United States", "Colorado", 727211),
            "boston": GeoLocation("Boston", 42.3601, -71.0589, "United States", "Massachusetts", 692600),
            "san francisco": GeoLocation("San Francisco", 37.7749, -122.4194, "United States", "California", 873965),
            "las vegas": GeoLocation("Las Vegas", 36.1699, -115.1398, "United States", "Nevada", 641903),
            "washington dc": GeoLocation("Washington D.C.", 38.9072, -77.0369, "United States", "District of Columbia", 689545),
            "london": GeoLocation("London", 51.5074, -0.1278, "United Kingdom", "England", 8982000),
            "paris": GeoLocation("Paris", 48.8566, 2.3522, "France", "", 2161000),
            "tokyo": GeoLocation("Tokyo", 35.6762, 139.6503, "Japan", "", 13960000),
            "beijing": GeoLocation("Beijing", 39.9042, 116.4074, "China", "", 21540000),
            "moscow": GeoLocation("Moscow", 55.7558, 37.6173, "Russia", "", 12500000),
            "sydney": GeoLocation("Sydney", -33.8688, 151.2093, "Australia", "New South Wales", 5312000),
            "rio de janeiro": GeoLocation("Rio de Janeiro", -22.9068, -43.1729, "Brazil", "", 6748000),
            "cairo": GeoLocation("Cairo", 30.0444, 31.2357, "Egypt", "", 9540000),
            "mumbai": GeoLocation("Mumbai", 19.0760, 72.8777, "India", "Maharashtra", 12442000),
            "dubai": GeoLocation("Dubai", 25.2048, 55.2708, "United Arab Emirates", "", 3331000),
            "singapore": GeoLocation("Singapore", 1.3521, 103.8198, "Singapore", "", 5686000),
            "toronto": GeoLocation("Toronto", 43.6532, -79.3832, "Canada", "Ontario", 2731571),
            "mexico city": GeoLocation("Mexico City", 19.4326, -99.1332, "Mexico", "", 9209944),
            "berlin": GeoLocation("Berlin", 52.5200, 13.4050, "Germany", "", 3645000),
            "rome": GeoLocation("Rome", 41.9028, 12.4964, "Italy", "", 2873000),
            "madrid": GeoLocation("Madrid", 40.4168, -3.7038, "Spain", "", 3223000),
            "seoul": GeoLocation("Seoul", 37.5665, 126.9780, "South Korea", "", 9776000),
            "istanbul": GeoLocation("Istanbul", 41.0082, 28.9784, "Turkey", "", 15460000),
            "nairobi": GeoLocation("Nairobi", -1.2921, 36.8219, "Kenya", "", 4397073),
            "cape town": GeoLocation("Cape Town", -33.9249, 18.4241, "South Africa", "", 4618000),
            "buenos aires": GeoLocation("Buenos Aires", -34.6037, -58.3816, "Argentina", "", 3075646),
            "port-au-prince": GeoLocation("Port-au-Prince", 18.5944, -72.3074, "Haiti", "", 987311),
        }
        self._cache.update(cities)

    def geocode(self, query: str) -> Optional[GeoLocation]:
        """Look up a place name and return its coordinates."""
        query_lower = query.lower().strip()

        # Check cache first
        if query_lower in self._cache:
            return self._cache[query_lower]

        # Try partial match in cache
        for key, loc in self._cache.items():
            if query_lower in key or key in query_lower:
                return loc

        # Query Nominatim (OpenStreetMap) - free, no API key
        try:
            self._rate_limit()
            encoded = urllib.parse.quote(query)
            url = (f"https://nominatim.openstreetmap.org/search?"
                   f"q={encoded}&format=json&limit=1&addressdetails=1")
            headers = {"User-Agent": "MonicaAI/1.0 (Educational Assistant)"}
            req = urllib.request.Request(url, headers=headers)

            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if data:
                    result = data[0]
                    addr = result.get("address", {})
                    loc = GeoLocation(
                        name=result.get("display_name", query).split(",")[0].strip(),
                        lat=float(result["lat"]),
                        lng=float(result["lon"]),
                        country=addr.get("country", ""),
                        state=addr.get("state", ""),
                        display_name=result.get("display_name", ""),
                    )
                    self._cache[query_lower] = loc
                    return loc

        except Exception as e:
            logger.debug(f"Geocoding error for '{query}': {e}")

        return None

    def _rate_limit(self):
        """Nominatim requires max 1 request per second."""
        now = time.time()
        self._request_timestamps = [t for t in self._request_timestamps if now - t < 1.0]
        if self._request_timestamps:
            wait = 1.0 - (now - self._request_timestamps[-1])
            if wait > 0:
                time.sleep(wait)
        self._request_timestamps.append(time.time())

    def reverse_geocode(self, lat: float, lng: float) -> Optional[GeoLocation]:
        """Look up coordinates and return a named location."""
        try:
            self._rate_limit()
            url = (f"https://nominatim.openstreetmap.org/reverse?"
                   f"lat={lat}&lon={lng}&format=json&addressdetails=1")
            headers = {"User-Agent": "MonicaAI/1.0 (Educational Assistant)"}
            req = urllib.request.Request(url, headers=headers)

            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if data and "address" in data:
                    addr = data["address"]
                    name = (addr.get("city") or addr.get("town") or
                            addr.get("village") or addr.get("county") or "Unknown")
                    return GeoLocation(
                        name=name,
                        lat=lat,
                        lng=lng,
                        country=addr.get("country", ""),
                        state=addr.get("state", ""),
                        display_name=data.get("display_name", ""),
                    )
        except Exception as e:
            logger.debug(f"Reverse geocoding error: {e}")
        return None


# ==================== NASA GIBS Satellite Imagery ====================

class GIBSClient:
    """
    Fetch satellite imagery tiles from NASA GIBS (Global Imagery Browse Services).
    Free, no API key required. Uses WMTS protocol.
    
    Layers available:
    - MODIS_Terra_CorrectedReflectance_TrueColor (daily true-color Earth)
    - VIIRS_SNPP_CorrectedReflectance_TrueColor (higher res daily)
    - BlueMarble_NextGeneration (static high-res composite)
    """

    BASE_URL = "https://gibs.earthdata.nasa.gov/wmts/epsg4326/best"

    LAYERS = {
        "true_color": "MODIS_Terra_CorrectedReflectance_TrueColor",
        "viirs": "VIIRS_SNPP_CorrectedReflectance_TrueColor",
        "blue_marble": "BlueMarble_NextGeneration",
        "night": "VIIRS_Black_Marble",
        "sea_temp": "GHRSST_L4_MUR_Sea_Surface_Temperature",
    }

    def __init__(self):
        self._tile_cache: Dict[str, bytes] = {}
        logger.info("GIBS Client initialized")

    def get_tile_url(self, layer: str = "true_color", date: str = None,
                     zoom: int = 3, row: int = 0, col: int = 0) -> str:
        """Build a GIBS WMTS tile URL."""
        layer_name = self.LAYERS.get(layer, layer)
        if date is None:
            from datetime import datetime, timedelta
            date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

        tile_matrix = f"2km" if zoom <= 3 else f"1km" if zoom <= 5 else f"500m"

        return (f"{self.BASE_URL}/{layer_name}/default/{date}/EPSG4326_{tile_matrix}/"
                f"{zoom}/{row}/{col}.jpg")

    def get_full_earth_url(self, layer: str = "blue_marble") -> str:
        """Get a URL for a full-earth overview image."""
        urls = {
            "blue_marble": "https://eoimages.gsfc.nasa.gov/images/imagerecords/73000/73909/world.topo.bathy.200412.3x5400x2700.jpg",
            "true_color": f"{self.BASE_URL}/MODIS_Terra_CorrectedReflectance_TrueColor/default/2024-01-01/EPSG4326_2km/0/0/0.jpg",
            "night": "https://eoimages.gsfc.nasa.gov/images/imagerecords/144000/144898/BlackMarble_2016_3km.jpg",
        }
        return urls.get(layer, urls["blue_marble"])

    def get_weather_satellite_url(self, region: str = "full_disk") -> str:
        """Get GOES-16 weather satellite imagery URL."""
        base = "https://cdn.star.nesdis.noaa.gov/GOES16/ABI"
        regions = {
            "full_disk": f"{base}/FD/GEOCOLOR/latest.jpg",
            "conus": f"{base}/CONUS/GEOCOLOR/latest.jpg",
            "northeast": f"{base}/SECTOR/ne/GEOCOLOR/latest.jpg",
            "southeast": f"{base}/SECTOR/se/GEOCOLOR/latest.jpg",
            "gulf": f"{base}/SECTOR/gm/GEOCOLOR/latest.jpg",
        }
        return regions.get(region, regions["full_disk"])

    def get_available_layers(self) -> Dict[str, str]:
        """Return available satellite imagery layers."""
        return dict(self.LAYERS)


# ==================== Globe Coordinate System ====================

class GlobeCoordinateSystem:
    """
    Math utilities for mapping lat/lng to 3D globe positions.
    Used by the hologram system to render accurate globe rotations.
    """

    @staticmethod
    def lat_lng_to_xyz(lat: float, lng: float, radius: float = 1.0) -> Tuple[float, float, float]:
        """Convert lat/lng (degrees) to 3D cartesian coordinates."""
        lat_rad = math.radians(lat)
        lng_rad = math.radians(lng)
        x = radius * math.cos(lat_rad) * math.cos(lng_rad)
        y = radius * math.cos(lat_rad) * math.sin(lng_rad)
        z = radius * math.sin(lat_rad)
        return (x, y, z)

    @staticmethod
    def xyz_to_lat_lng(x: float, y: float, z: float) -> Tuple[float, float]:
        """Convert 3D cartesian coordinates to lat/lng (degrees)."""
        lat = math.degrees(math.asin(z / math.sqrt(x*x + y*y + z*z)))
        lng = math.degrees(math.atan2(y, x))
        return (lat, lng)

    @staticmethod
    def rotation_to_show_location(lat: float, lng: float) -> Tuple[float, float]:
        """
        Calculate globe rotation angles to center a given lat/lng.
        Returns (rotation_x, rotation_y) in RADIANS.
        
        Must match the convention used in show_globe():
          rotation_y = math.radians(lng)  -- longitude rotation
          rotation_x = math.radians(lat) * factor -- latitude tilt
        """
        rot_x = math.radians(lat) * 0.3   # Moderate tilt to show latitude
        rot_y = math.radians(lng)          # Rotate to show longitude
        return (rot_x, rot_y)

    @staticmethod
    def distance_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Calculate great-circle distance between two points (Haversine formula)."""
        R = 6371.0  # Earth's mean radius in km
        lat1_r, lat2_r = math.radians(lat1), math.radians(lat2)
        dlat = math.radians(lat2 - lat1)
        dlng = math.radians(lng2 - lng1)

        a = (math.sin(dlat / 2) ** 2 +
             math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlng / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    @staticmethod
    def bearing(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Calculate initial bearing from point 1 to point 2 (degrees)."""
        lat1_r, lat2_r = math.radians(lat1), math.radians(lat2)
        dlng = math.radians(lng2 - lng1)

        x = math.sin(dlng) * math.cos(lat2_r)
        y = (math.cos(lat1_r) * math.sin(lat2_r) -
             math.sin(lat1_r) * math.cos(lat2_r) * math.cos(dlng))
        return (math.degrees(math.atan2(x, y)) + 360) % 360

    @staticmethod
    def lat_lng_to_screen(lat: float, lng: float, center_x: int, center_y: int,
                          radius: int, rot_x: float = 0, rot_y: float = 0) -> Optional[Tuple[int, int]]:
        """
        Project lat/lng onto a 2D circle (globe front face).
        Returns (screen_x, screen_y) or None if point is on back face.
        """
        lat_rad = math.radians(lat + rot_x)
        lng_rad = math.radians(lng + rot_y)

        x = math.cos(lat_rad) * math.sin(lng_rad)
        y = -math.sin(lat_rad)
        z = math.cos(lat_rad) * math.cos(lng_rad)

        if z < 0:
            return None  # Back face

        screen_x = int(center_x + x * radius)
        screen_y = int(center_y + y * radius)
        return (screen_x, screen_y)


# ==================== Singletons ====================

_geocoder: Optional[AccurateGeocoder] = None
_gibs_client: Optional[GIBSClient] = None


def get_geocoder() -> AccurateGeocoder:
    """Get the singleton geocoder instance."""
    global _geocoder
    if _geocoder is None:
        _geocoder = AccurateGeocoder()
    return _geocoder


def get_gibs_client() -> GIBSClient:
    """Get the singleton GIBS client instance."""
    global _gibs_client
    if _gibs_client is None:
        _gibs_client = GIBSClient()
    return _gibs_client
