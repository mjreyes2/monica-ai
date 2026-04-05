"""
Public Satellite Services for Monica AI
Access to satellite imagery, Earth observation data, and space assets.
All using FREE public APIs - no API keys required!
"""
import requests
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass

@dataclass
class SatellitePass:
    """Represents a satellite pass over a location."""
    satellite_name: str
    rise_time: datetime
    rise_azimuth: float
    max_altitude_time: datetime
    max_altitude: float
    set_time: datetime
    set_azimuth: float
    duration_seconds: int
    visible: bool

@dataclass 
class SatellitePosition:
    """Current position of a satellite."""
    name: str
    latitude: float
    longitude: float
    altitude_km: float
    velocity_km_s: float
    timestamp: datetime

class SatelliteServices:
    """
    Public satellite and space services for Monica AI.
    Uses free APIs - no API keys required!
    """
    
    def __init__(self):
        # Free satellite tracking APIs
        self.N2YO_API = "https://api.n2yo.com/rest/v1/satellite"
        self.WHERETHEISS_API = "https://api.wheretheiss.at/v1"
        self.NASA_API = "https://api.nasa.gov"
        self.NASA_DEMO_KEY = "DEMO_KEY"  # Free demo key, 30 requests/hour
        
        # Satellite NORAD IDs
        self.SATELLITES = {
            'iss': 25544,           # International Space Station
            'hubble': 20580,        # Hubble Space Telescope
            'tiangong': 48274,      # Chinese Space Station
            'starlink': 44713,      # Example Starlink satellite
            'goes-16': 41866,       # GOES-16 Weather Satellite
            'goes-17': 43226,       # GOES-17 Weather Satellite
            'landsat-8': 39084,     # Landsat 8 Earth Observation
            'landsat-9': 49260,     # Landsat 9 Earth Observation
            'sentinel-2a': 40697,   # Sentinel-2A (ESA)
            'terra': 25994,         # NASA Terra (Earth observation)
            'aqua': 27424,          # NASA Aqua (Earth observation)
            'noaa-20': 43013,       # NOAA-20 Weather
        }
        
        print("[SATELLITE] Satellite Services initialized")
    
    def get_iss_position(self) -> Optional[SatellitePosition]:
        """Get current ISS position (free, no API key)."""
        try:
            response = requests.get(
                f"{self.WHERETHEISS_API}/satellites/25544",
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                return SatellitePosition(
                    name="International Space Station (ISS)",
                    latitude=data.get('latitude', 0),
                    longitude=data.get('longitude', 0),
                    altitude_km=data.get('altitude', 0),
                    velocity_km_s=data.get('velocity', 0) / 3600,  # Convert km/h to km/s
                    timestamp=datetime.fromtimestamp(data.get('timestamp', 0))
                )
        except Exception as e:
            print(f"[SATELLITE] Error getting ISS position: {e}")
        return None
    
    def get_iss_passes(self, lat: float, lon: float, days: int = 7) -> List[Dict[str, Any]]:
        """Get upcoming ISS passes over a location."""
        try:
            # Use Open Notify API (free)
            response = requests.get(
                f"http://api.open-notify.org/iss-pass.json",
                params={'lat': lat, 'lon': lon, 'n': 10},
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                passes = []
                for p in data.get('response', []):
                    rise_time = datetime.fromtimestamp(p['risetime'])
                    passes.append({
                        'rise_time': rise_time.strftime('%Y-%m-%d %H:%M:%S'),
                        'duration_minutes': p['duration'] / 60,
                        'visible': True
                    })
                return passes
        except Exception as e:
            print(f"[SATELLITE] Error getting ISS passes: {e}")
        return []
    
    def get_people_in_space(self) -> Dict[str, Any]:
        """Get list of people currently in space (free)."""
        try:
            response = requests.get(
                "http://api.open-notify.org/astros.json",
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                return {
                    'count': data.get('number', 0),
                    'people': [
                        {'name': p['name'], 'craft': p['craft']}
                        for p in data.get('people', [])
                    ]
                }
        except Exception as e:
            print(f"[SATELLITE] Error getting astronauts: {e}")
        return {'count': 0, 'people': []}
    
    def get_nasa_apod(self) -> Optional[Dict[str, Any]]:
        """Get NASA Astronomy Picture of the Day (free with demo key)."""
        try:
            response = requests.get(
                f"{self.NASA_API}/planetary/apod",
                params={'api_key': self.NASA_DEMO_KEY},
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                return {
                    'title': data.get('title', ''),
                    'explanation': data.get('explanation', ''),
                    'url': data.get('url', ''),
                    'hdurl': data.get('hdurl', ''),
                    'date': data.get('date', ''),
                    'media_type': data.get('media_type', 'image')
                }
        except Exception as e:
            print(f"[SATELLITE] Error getting NASA APOD: {e}")
        return None
    
    def get_earth_imagery_url(self, lat: float, lon: float, date: str = None) -> str:
        """
        Get NASA Earth imagery URL for a location.
        Date format: YYYY-MM-DD (defaults to recent imagery)
        """
        if date is None:
            date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        return f"{self.NASA_API}/planetary/earth/imagery?lon={lon}&lat={lat}&date={date}&api_key={self.NASA_DEMO_KEY}"
    
    def get_landsat_imagery_info(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """Get Landsat satellite imagery information for a location."""
        try:
            response = requests.get(
                f"{self.NASA_API}/planetary/earth/assets",
                params={
                    'lon': lon,
                    'lat': lat,
                    'api_key': self.NASA_DEMO_KEY
                },
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                return {
                    'date': data.get('date', ''),
                    'id': data.get('id', ''),
                    'url': data.get('url', ''),
                    'resource': data.get('resource', {})
                }
        except Exception as e:
            print(f"[SATELLITE] Error getting Landsat imagery: {e}")
        return None
    
    def get_mars_weather(self) -> Optional[Dict[str, Any]]:
        """Get latest Mars weather data from NASA InSight."""
        try:
            response = requests.get(
                f"{self.NASA_API}/insight_weather/",
                params={'api_key': self.NASA_DEMO_KEY, 'feedtype': 'json', 'ver': '1.0'},
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                # Get the most recent sol (Martian day)
                sol_keys = data.get('sol_keys', [])
                if sol_keys:
                    latest_sol = sol_keys[-1]
                    sol_data = data.get(latest_sol, {})
                    return {
                        'sol': latest_sol,
                        'earth_date': sol_data.get('First_UTC', ''),
                        'temperature': sol_data.get('AT', {}),
                        'pressure': sol_data.get('PRE', {}),
                        'wind_speed': sol_data.get('HWS', {}),
                        'season': sol_data.get('Season', '')
                    }
        except Exception as e:
            print(f"[SATELLITE] Error getting Mars weather: {e}")
        return None
    
    def get_neo_asteroids(self, start_date: str = None, end_date: str = None) -> List[Dict[str, Any]]:
        """Get Near Earth Objects (asteroids) from NASA."""
        if start_date is None:
            start_date = datetime.now().strftime('%Y-%m-%d')
        if end_date is None:
            end_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        
        try:
            response = requests.get(
                f"{self.NASA_API}/neo/rest/v1/feed",
                params={
                    'start_date': start_date,
                    'end_date': end_date,
                    'api_key': self.NASA_DEMO_KEY
                },
                timeout=15
            )
            if response.status_code == 200:
                data = response.json()
                asteroids = []
                for date, neos in data.get('near_earth_objects', {}).items():
                    for neo in neos:
                        asteroids.append({
                            'name': neo.get('name', ''),
                            'id': neo.get('id', ''),
                            'diameter_min_m': neo.get('estimated_diameter', {}).get('meters', {}).get('estimated_diameter_min', 0),
                            'diameter_max_m': neo.get('estimated_diameter', {}).get('meters', {}).get('estimated_diameter_max', 0),
                            'is_hazardous': neo.get('is_potentially_hazardous_asteroid', False),
                            'close_approach_date': date,
                            'miss_distance_km': float(neo.get('close_approach_data', [{}])[0].get('miss_distance', {}).get('kilometers', 0)),
                            'velocity_km_h': float(neo.get('close_approach_data', [{}])[0].get('relative_velocity', {}).get('kilometers_per_hour', 0))
                        })
                return asteroids
        except Exception as e:
            print(f"[SATELLITE] Error getting NEO data: {e}")
        return []
    
    def get_satellite_map_url(self, satellite: str = 'iss') -> str:
        """Get a live tracking map URL for a satellite."""
        norad_id = self.SATELLITES.get(satellite.lower(), 25544)
        return f"https://www.n2yo.com/satellite/?s={norad_id}"
    
    def get_weather_satellite_imagery(self, region: str = 'us') -> Dict[str, str]:
        """Get weather satellite imagery URLs (GOES satellites)."""
        base_url = "https://cdn.star.nesdis.noaa.gov/GOES16/ABI"
        
        imagery = {
            'full_disk': f"{base_url}/FD/GEOCOLOR/latest.jpg",
            'conus': f"{base_url}/CONUS/GEOCOLOR/latest.jpg",  # Continental US
            'mesoscale_1': f"{base_url}/MESO/M1/GEOCOLOR/latest.jpg",
            'mesoscale_2': f"{base_url}/MESO/M2/GEOCOLOR/latest.jpg",
        }
        
        return imagery
    
    def get_space_summary(self) -> str:
        """Get a summary of current space activity."""
        summary_parts = []
        
        # ISS position
        iss = self.get_iss_position()
        if iss:
            summary_parts.append(
                f"The ISS is currently over {iss.latitude:.2f}N, {iss.longitude:.2f}E "
                f"at {iss.altitude_km:.0f}km altitude, traveling at {iss.velocity_km_s:.1f} km/s."
            )
        
        # People in space
        astros = self.get_people_in_space()
        if astros['count'] > 0:
            summary_parts.append(f"There are {astros['count']} people currently in space.")
        
        return " ".join(summary_parts) if summary_parts else "Unable to retrieve space data."


# Singleton instance
_satellite_services = None

def get_satellite_services() -> SatelliteServices:
    """Get the singleton SatelliteServices instance."""
    global _satellite_services
    if _satellite_services is None:
        _satellite_services = SatelliteServices()
    return _satellite_services
