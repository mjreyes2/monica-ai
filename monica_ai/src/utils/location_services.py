"""
Location-Based Services for Monica AI
Provides geolocation, nearby places, weather, and mapping capabilities.
"""
import requests
import json
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Location:
    """Represents a geographic location."""
    latitude: float
    longitude: float
    city: str = ""
    region: str = ""
    country: str = ""
    timezone: str = ""
    ip_address: str = ""

class LocationServices:
    """
    Location-based services for Monica AI.
    Uses free APIs - no API keys required!
    """
    
    def __init__(self):
        self.current_location: Optional[Location] = None
        self.cache_timeout = 300  # 5 minutes
        self._last_location_fetch = 0
        
        # Free API endpoints
        self.IP_GEOLOCATION_API = "http://ip-api.com/json/"
        self.NOMINATIM_API = "https://nominatim.openstreetmap.org"
        self.OVERPASS_API = "https://overpass-api.de/api/interpreter"
        
        print("[LOCATION] Location Services initialized")
    
    def get_current_location(self, force_refresh: bool = False) -> Optional[Location]:
        """Get current location based on IP address (free, no API key)."""
        import time
        
        # Use cached location if available and not expired
        if not force_refresh and self.current_location:
            if time.time() - self._last_location_fetch < self.cache_timeout:
                return self.current_location
        
        try:
            response = requests.get(self.IP_GEOLOCATION_API, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    self.current_location = Location(
                        latitude=data.get('lat', 0),
                        longitude=data.get('lon', 0),
                        city=data.get('city', ''),
                        region=data.get('regionName', ''),
                        country=data.get('country', ''),
                        timezone=data.get('timezone', ''),
                        ip_address=data.get('query', '')
                    )
                    self._last_location_fetch = time.time()
                    print(f"[LOCATION] Current location: {self.current_location.city}, {self.current_location.country}")
                    return self.current_location
        except Exception as e:
            print(f"[LOCATION] Error getting location: {e}")
        
        return None
    
    def geocode(self, address: str) -> Optional[Tuple[float, float]]:
        """Convert address to coordinates using OpenStreetMap Nominatim (free)."""
        try:
            params = {
                'q': address,
                'format': 'json',
                'limit': 1
            }
            headers = {'User-Agent': 'MonicaAI/1.0'}
            response = requests.get(
                f"{self.NOMINATIM_API}/search",
                params=params,
                headers=headers,
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                if data:
                    return (float(data[0]['lat']), float(data[0]['lon']))
        except Exception as e:
            print(f"[LOCATION] Geocoding error: {e}")
        return None
    
    def reverse_geocode(self, lat: float, lon: float) -> Optional[str]:
        """Convert coordinates to address using OpenStreetMap Nominatim (free)."""
        try:
            params = {
                'lat': lat,
                'lon': lon,
                'format': 'json'
            }
            headers = {'User-Agent': 'MonicaAI/1.0'}
            response = requests.get(
                f"{self.NOMINATIM_API}/reverse",
                params=params,
                headers=headers,
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                return data.get('display_name', '')
        except Exception as e:
            print(f"[LOCATION] Reverse geocoding error: {e}")
        return None
    
    def find_nearby_places(self, place_type: str, radius_meters: int = 1000) -> List[Dict[str, Any]]:
        """
        Find nearby places using OpenStreetMap Overpass API (free).
        
        Place types: restaurant, cafe, hospital, pharmacy, gas_station, 
                    atm, bank, supermarket, park, school, library, etc.
        """
        if not self.current_location:
            self.get_current_location()
        
        if not self.current_location:
            return []
        
        # Map common place types to OSM tags
        osm_tags = {
            'restaurant': 'amenity=restaurant',
            'cafe': 'amenity=cafe',
            'hospital': 'amenity=hospital',
            'pharmacy': 'amenity=pharmacy',
            'gas_station': 'amenity=fuel',
            'atm': 'amenity=atm',
            'bank': 'amenity=bank',
            'supermarket': 'shop=supermarket',
            'park': 'leisure=park',
            'school': 'amenity=school',
            'library': 'amenity=library',
            'police': 'amenity=police',
            'fire_station': 'amenity=fire_station',
            'hotel': 'tourism=hotel',
            'museum': 'tourism=museum',
            'gym': 'leisure=fitness_centre',
            'cinema': 'amenity=cinema',
            'bar': 'amenity=bar',
            'fast_food': 'amenity=fast_food',
            'parking': 'amenity=parking'
        }
        
        tag = osm_tags.get(place_type.lower(), f'amenity={place_type}')
        
        query = f"""
        [out:json][timeout:10];
        (
          node[{tag}](around:{radius_meters},{self.current_location.latitude},{self.current_location.longitude});
          way[{tag}](around:{radius_meters},{self.current_location.latitude},{self.current_location.longitude});
        );
        out center 10;
        """
        
        try:
            response = requests.post(
                self.OVERPASS_API,
                data={'data': query},
                timeout=15
            )
            if response.status_code == 200:
                data = response.json()
                places = []
                for element in data.get('elements', []):
                    tags = element.get('tags', {})
                    lat = element.get('lat') or element.get('center', {}).get('lat')
                    lon = element.get('lon') or element.get('center', {}).get('lon')
                    
                    if lat and lon:
                        places.append({
                            'name': tags.get('name', 'Unknown'),
                            'type': place_type,
                            'latitude': lat,
                            'longitude': lon,
                            'address': tags.get('addr:street', ''),
                            'phone': tags.get('phone', ''),
                            'website': tags.get('website', ''),
                            'opening_hours': tags.get('opening_hours', '')
                        })
                
                print(f"[LOCATION] Found {len(places)} {place_type}(s) nearby")
                return places
        except Exception as e:
            print(f"[LOCATION] Error finding nearby places: {e}")
        
        return []
    
    def get_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points in kilometers using Haversine formula."""
        import math
        
        R = 6371  # Earth's radius in km
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    def get_directions_url(self, destination: str) -> str:
        """Get a Google Maps directions URL to a destination."""
        if not self.current_location:
            self.get_current_location()
        
        if self.current_location:
            origin = f"{self.current_location.latitude},{self.current_location.longitude}"
            return f"https://www.google.com/maps/dir/{origin}/{destination.replace(' ', '+')}"
        else:
            return f"https://www.google.com/maps/search/{destination.replace(' ', '+')}"
    
    def get_map_url(self, lat: float = None, lon: float = None, zoom: int = 15) -> str:
        """Get a map URL for a location."""
        if lat is None or lon is None:
            if not self.current_location:
                self.get_current_location()
            if self.current_location:
                lat = self.current_location.latitude
                lon = self.current_location.longitude
            else:
                return "https://www.openstreetmap.org"
        
        return f"https://www.openstreetmap.org/?mlat={lat}&mlon={lon}#map={zoom}/{lat}/{lon}"
    
    def get_location_summary(self) -> str:
        """Get a human-readable summary of current location."""
        loc = self.get_current_location()
        if loc:
            return f"You are in {loc.city}, {loc.region}, {loc.country}. Coordinates: {loc.latitude:.4f}, {loc.longitude:.4f}. Timezone: {loc.timezone}"
        return "Unable to determine your location."


# Singleton instance
_location_services = None

def get_location_services() -> LocationServices:
    """Get the singleton LocationServices instance."""
    global _location_services
    if _location_services is None:
        _location_services = LocationServices()
    return _location_services
