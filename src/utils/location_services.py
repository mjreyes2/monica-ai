"""
Location Services for Monica AI.
Provides IP-based geolocation using free APIs (no API key required).

HIPAA PRIVACY NOTE:
  IP geolocation sends your public IP address to external services
  to determine approximate location. This reveals your general area
  (city-level) but NOT personal identity. If privacy is a concern,
  set MONICA_DISABLE_IP_GEOLOCATION=1 in your environment to disable.
"""
import json
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger("Monica.Location")


class LocationServices:
    """
    Provides geolocation services using free IP-based APIs.
    No API key required.
    """

    def __init__(self):
        self.current_location = None
        self._cache = {}

    def get_current_location(self) -> Optional[Dict[str, Any]]:
        """Get current location based on IP address (free, no API key).
        
        PRIVACY: Can be disabled by setting env MONICA_DISABLE_IP_GEOLOCATION=1
        """
        import os
        if os.environ.get('MONICA_DISABLE_IP_GEOLOCATION', '').strip() in ('1', 'true', 'yes'):
            logger.info("IP geolocation disabled for privacy (MONICA_DISABLE_IP_GEOLOCATION=1)")
            return None

        if self.current_location:
            return self.current_location

        # Try multiple free geolocation APIs
        apis = [
            ("http://ip-api.com/json/?fields=status,message,country,regionName,city,lat,lon,timezone,isp,query", self._parse_ip_api),
            ("https://ipapi.co/json/", self._parse_ipapi_co),
            ("https://ipwho.is/", self._parse_ipwhois),
        ]

        for url, parser in apis:
            try:
                import urllib.request
                req = urllib.request.Request(url, headers={"User-Agent": "Monica-AI/1.0"})
                with urllib.request.urlopen(req, timeout=5) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    result = parser(data)
                    if result:
                        self.current_location = result
                        logger.info(f"Location: {result.get('city', '?')}, {result.get('country', '?')} "
                                    f"({result.get('lat', 0):.4f}, {result.get('lon', 0):.4f})")
                        return result
            except Exception as e:
                logger.debug(f"Location API {url} failed: {e}")
                continue

        logger.warning("Could not determine location from any API")
        return None

    @staticmethod
    def _parse_ip_api(data: dict) -> Optional[Dict[str, Any]]:
        if data.get("status") != "success":
            return None
        return {
            "lat": data.get("lat", 0),
            "lon": data.get("lon", 0),
            "city": data.get("city", "Unknown"),
            "region": data.get("regionName", ""),
            "country": data.get("country", "Unknown"),
            "timezone": data.get("timezone", ""),
            "ip": data.get("query", ""),
            "isp": data.get("isp", ""),
        }

    @staticmethod
    def _parse_ipapi_co(data: dict) -> Optional[Dict[str, Any]]:
        if "error" in data:
            return None
        return {
            "lat": data.get("latitude", 0),
            "lon": data.get("longitude", 0),
            "city": data.get("city", "Unknown"),
            "region": data.get("region", ""),
            "country": data.get("country_name", "Unknown"),
            "timezone": data.get("timezone", ""),
            "ip": data.get("ip", ""),
            "isp": data.get("org", ""),
        }

    @staticmethod
    def _parse_ipwhois(data: dict) -> Optional[Dict[str, Any]]:
        if not data.get("success", False):
            return None
        return {
            "lat": data.get("latitude", 0),
            "lon": data.get("longitude", 0),
            "city": data.get("city", "Unknown"),
            "region": data.get("region", ""),
            "country": data.get("country", "Unknown"),
            "timezone": data.get("timezone", {}).get("id", "") if isinstance(data.get("timezone"), dict) else "",
            "ip": data.get("ip", ""),
            "isp": data.get("connection", {}).get("isp", "") if isinstance(data.get("connection"), dict) else "",
        }

    def geocode(self, place_name: str) -> Optional[Dict[str, Any]]:
        """Geocode a place name to lat/lon using free Nominatim API."""
        if place_name in self._cache:
            return self._cache[place_name]

        try:
            import urllib.request
            import urllib.parse
            encoded = urllib.parse.quote(place_name)
            url = f"https://nominatim.openstreetmap.org/search?q={encoded}&format=json&limit=1"
            req = urllib.request.Request(url, headers={"User-Agent": "Monica-AI/1.0"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                results = json.loads(resp.read().decode("utf-8"))
                if results:
                    r = results[0]
                    result = {
                        "lat": float(r.get("lat", 0)),
                        "lon": float(r.get("lon", 0)),
                        "display_name": r.get("display_name", place_name),
                    }
                    self._cache[place_name] = result
                    return result
        except Exception as e:
            logger.debug(f"Geocode failed for '{place_name}': {e}")

        return None


# Singleton
_location_services = None


def get_location_services() -> LocationServices:
    """Get singleton LocationServices instance."""
    global _location_services
    if _location_services is None:
        _location_services = LocationServices()
    return _location_services
