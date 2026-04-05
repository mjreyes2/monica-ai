"""
Monica's Global Webcam Network
Extensive database of public webcams worldwide
With holographic display support
"""

from typing import Dict, List, Optional, Tuple
import math

# EXTENSIVE GLOBAL WEBCAM DATABASE
GLOBAL_WEBCAMS = {
    # NORTH AMERICA
    "times_square_nyc": {
        "name": "Times Square, New York City",
        "location": {"lat": 40.7580, "lng": -73.9855},
        "country": "USA",
        "continent": "North America",
        "url": "https://www.earthcam.com/usa/newyork/timessquare/",
        "type": "earthcam",
        "description": "The heart of NYC, the Crossroads of the World"
    },
    "central_park_nyc": {
        "name": "Central Park, New York City",
        "location": {"lat": 40.7829, "lng": -73.9654},
        "country": "USA",
        "continent": "North America",
        "url": "https://www.earthcam.com/usa/newyork/centralpark/",
        "type": "earthcam"
    },
    "statue_of_liberty": {
        "name": "Statue of Liberty, New York",
        "location": {"lat": 40.6892, "lng": -74.0445},
        "country": "USA",
        "continent": "North America",
        "url": "https://www.earthcam.com/usa/newyork/statueofliberty/",
        "type": "earthcam"
    },
    "hollywood_blvd": {
        "name": "Hollywood Boulevard, Los Angeles",
        "location": {"lat": 34.1016, "lng": -118.3267},
        "country": "USA",
        "continent": "North America",
        "url": "https://www.earthcam.com/usa/california/losangeles/hollywood/",
        "type": "earthcam"
    },
    "santa_monica_pier": {
        "name": "Santa Monica Pier, California",
        "location": {"lat": 34.0094, "lng": -118.4973},
        "country": "USA",
        "continent": "North America",
        "url": "https://www.earthcam.com/usa/california/santamonica/",
        "type": "earthcam"
    },
    "las_vegas_strip": {
        "name": "Las Vegas Strip, Nevada",
        "location": {"lat": 36.1147, "lng": -115.1728},
        "country": "USA",
        "continent": "North America",
        "url": "https://www.earthcam.com/usa/nevada/lasvegas/",
        "type": "earthcam"
    },
    "miami_beach": {
        "name": "Miami Beach, Florida",
        "location": {"lat": 25.7907, "lng": -80.1300},
        "country": "USA",
        "continent": "North America",
        "url": "https://www.earthcam.com/usa/florida/miamibeach/",
        "type": "earthcam"
    },
    "niagara_falls": {
        "name": "Niagara Falls",
        "location": {"lat": 43.0962, "lng": -79.0377},
        "country": "USA/Canada",
        "continent": "North America",
        "url": "https://www.earthcam.com/usa/newyork/niagarafalls/",
        "type": "earthcam"
    },
    "golden_gate_bridge": {
        "name": "Golden Gate Bridge, San Francisco",
        "location": {"lat": 37.8199, "lng": -122.4783},
        "country": "USA",
        "continent": "North America",
        "url": "https://www.earthcam.com/usa/california/sanfrancisco/goldengate/",
        "type": "earthcam"
    },
    "chicago_skyline": {
        "name": "Chicago Skyline, Illinois",
        "location": {"lat": 41.8781, "lng": -87.6298},
        "country": "USA",
        "continent": "North America",
        "url": "https://www.earthcam.com/usa/illinois/chicago/",
        "type": "earthcam"
    },
    "bourbon_street": {
        "name": "Bourbon Street, New Orleans",
        "location": {"lat": 29.9584, "lng": -90.0651},
        "country": "USA",
        "continent": "North America",
        "url": "https://www.earthcam.com/usa/louisiana/neworleans/bourbonstreet/",
        "type": "earthcam"
    },
    
    # EUROPE
    "abbey_road_london": {
        "name": "Abbey Road, London",
        "location": {"lat": 51.5320, "lng": -0.1780},
        "country": "UK",
        "continent": "Europe",
        "url": "https://www.earthcam.com/world/england/london/abbeyroad/",
        "type": "earthcam",
        "description": "Famous Beatles crossing"
    },
    "tower_bridge_london": {
        "name": "Tower Bridge, London",
        "location": {"lat": 51.5055, "lng": -0.0754},
        "country": "UK",
        "continent": "Europe",
        "url": "https://www.earthcam.com/world/england/london/towerbridge/",
        "type": "earthcam"
    },
    "eiffel_tower_paris": {
        "name": "Eiffel Tower, Paris",
        "location": {"lat": 48.8584, "lng": 2.2945},
        "country": "France",
        "continent": "Europe",
        "url": "https://www.earthcam.com/world/france/paris/",
        "type": "earthcam"
    },
    "champs_elysees_paris": {
        "name": "Champs-Élysées, Paris",
        "location": {"lat": 48.8698, "lng": 2.3078},
        "country": "France",
        "continent": "Europe",
        "url": "https://www.earthcam.com/world/france/paris/champselysees/",
        "type": "earthcam"
    },
    "venice_st_marks": {
        "name": "St. Mark's Square, Venice",
        "location": {"lat": 45.4343, "lng": 12.3388},
        "country": "Italy",
        "continent": "Europe",
        "url": "https://www.skylinewebcams.com/en/webcam/italia/veneto/venezia/piazza-san-marco.html",
        "type": "skyline"
    },
    "rome_colosseum": {
        "name": "Colosseum, Rome",
        "location": {"lat": 41.8902, "lng": 12.4922},
        "country": "Italy",
        "continent": "Europe",
        "url": "https://www.skylinewebcams.com/en/webcam/italia/lazio/roma/colosseo.html",
        "type": "skyline"
    },
    "amsterdam_dam_square": {
        "name": "Dam Square, Amsterdam",
        "location": {"lat": 52.3731, "lng": 4.8932},
        "country": "Netherlands",
        "continent": "Europe",
        "url": "https://www.earthcam.com/world/netherlands/amsterdam/",
        "type": "earthcam"
    },
    "barcelona_las_ramblas": {
        "name": "Las Ramblas, Barcelona",
        "location": {"lat": 41.3809, "lng": 2.1734},
        "country": "Spain",
        "continent": "Europe",
        "url": "https://www.skylinewebcams.com/en/webcam/espana/cataluna/barcelona/las-ramblas.html",
        "type": "skyline"
    },
    "berlin_brandenburg": {
        "name": "Brandenburg Gate, Berlin",
        "location": {"lat": 52.5163, "lng": 13.3777},
        "country": "Germany",
        "continent": "Europe",
        "url": "https://www.earthcam.com/world/germany/berlin/",
        "type": "earthcam"
    },
    "prague_old_town": {
        "name": "Old Town Square, Prague",
        "location": {"lat": 50.0875, "lng": 14.4214},
        "country": "Czech Republic",
        "continent": "Europe",
        "url": "https://www.skylinewebcams.com/en/webcam/ceska-republika/hlavni-mesto-praha/praha/old-town-square.html",
        "type": "skyline"
    },
    "dublin_temple_bar": {
        "name": "Temple Bar, Dublin",
        "location": {"lat": 53.3454, "lng": -6.2644},
        "country": "Ireland",
        "continent": "Europe",
        "url": "https://www.earthcam.com/world/ireland/dublin/",
        "type": "earthcam"
    },
    
    # ASIA
    "shibuya_tokyo": {
        "name": "Shibuya Crossing, Tokyo",
        "location": {"lat": 35.6595, "lng": 139.7004},
        "country": "Japan",
        "continent": "Asia",
        "url": "https://www.youtube.com/watch?v=shibuya_live",
        "type": "youtube",
        "description": "World's busiest pedestrian crossing"
    },
    "tokyo_tower": {
        "name": "Tokyo Tower",
        "location": {"lat": 35.6586, "lng": 139.7454},
        "country": "Japan",
        "continent": "Asia",
        "url": "https://www.skylinewebcams.com/en/webcam/japan/kanto/tokyo/tokyo-tower.html",
        "type": "skyline"
    },
    "hong_kong_victoria": {
        "name": "Victoria Harbour, Hong Kong",
        "location": {"lat": 22.2855, "lng": 114.1577},
        "country": "Hong Kong",
        "continent": "Asia",
        "url": "https://www.earthcam.com/world/china/hongkong/",
        "type": "earthcam"
    },
    "singapore_marina_bay": {
        "name": "Marina Bay, Singapore",
        "location": {"lat": 1.2834, "lng": 103.8607},
        "country": "Singapore",
        "continent": "Asia",
        "url": "https://www.earthcam.com/world/singapore/",
        "type": "earthcam"
    },
    "dubai_burj_khalifa": {
        "name": "Burj Khalifa, Dubai",
        "location": {"lat": 25.1972, "lng": 55.2744},
        "country": "UAE",
        "continent": "Asia",
        "url": "https://www.earthcam.com/world/unitedarabemirates/dubai/",
        "type": "earthcam",
        "description": "World's tallest building"
    },
    "bangkok_grand_palace": {
        "name": "Grand Palace Area, Bangkok",
        "location": {"lat": 13.7500, "lng": 100.4913},
        "country": "Thailand",
        "continent": "Asia",
        "url": "https://www.skylinewebcams.com/en/webcam/thailand/bangkok/bangkok/grand-palace.html",
        "type": "skyline"
    },
    "seoul_gangnam": {
        "name": "Gangnam District, Seoul",
        "location": {"lat": 37.4979, "lng": 127.0276},
        "country": "South Korea",
        "continent": "Asia",
        "url": "https://www.earthcam.com/world/southkorea/seoul/",
        "type": "earthcam"
    },
    "mumbai_gateway": {
        "name": "Gateway of India, Mumbai",
        "location": {"lat": 18.9220, "lng": 72.8347},
        "country": "India",
        "continent": "Asia",
        "url": "https://www.skylinewebcams.com/en/webcam/india/maharashtra/mumbai/gateway-of-india.html",
        "type": "skyline"
    },
    
    # OCEANIA
    "sydney_harbour": {
        "name": "Sydney Harbour",
        "location": {"lat": 33.8568, "lng": 151.2153},
        "country": "Australia",
        "continent": "Oceania",
        "url": "https://www.earthcam.com/world/australia/sydney/",
        "type": "earthcam",
        "description": "Opera House and Harbour Bridge"
    },
    "bondi_beach": {
        "name": "Bondi Beach, Sydney",
        "location": {"lat": -33.8915, "lng": 151.2767},
        "country": "Australia",
        "continent": "Oceania",
        "url": "https://www.coastalwatch.com/surf-cams-surf-reports/nsw/bondi",
        "type": "surf"
    },
    "auckland_harbour": {
        "name": "Auckland Harbour, New Zealand",
        "location": {"lat": -36.8485, "lng": 174.7633},
        "country": "New Zealand",
        "continent": "Oceania",
        "url": "https://www.earthcam.com/world/newzealand/auckland/",
        "type": "earthcam"
    },
    
    # SOUTH AMERICA
    "rio_copacabana": {
        "name": "Copacabana Beach, Rio de Janeiro",
        "location": {"lat": -22.9711, "lng": -43.1822},
        "country": "Brazil",
        "continent": "South America",
        "url": "https://www.earthcam.com/world/brazil/riodejaneiro/",
        "type": "earthcam"
    },
    "buenos_aires_obelisco": {
        "name": "Obelisco, Buenos Aires",
        "location": {"lat": -34.6037, "lng": -58.3816},
        "country": "Argentina",
        "continent": "South America",
        "url": "https://www.skylinewebcams.com/en/webcam/argentina/buenos-aires/buenos-aires/obelisco.html",
        "type": "skyline"
    },
    "machu_picchu": {
        "name": "Machu Picchu, Peru",
        "location": {"lat": -13.1631, "lng": -72.5450},
        "country": "Peru",
        "continent": "South America",
        "url": "https://www.skylinewebcams.com/en/webcam/peru/cusco/machu-picchu/machu-picchu.html",
        "type": "skyline"
    },
    
    # AFRICA
    "cape_town_table_mountain": {
        "name": "Table Mountain, Cape Town",
        "location": {"lat": -33.9628, "lng": 18.4098},
        "country": "South Africa",
        "continent": "Africa",
        "url": "https://www.earthcam.com/world/southafrica/capetown/",
        "type": "earthcam"
    },
    "cairo_pyramids": {
        "name": "Pyramids of Giza, Cairo",
        "location": {"lat": 29.9792, "lng": 31.1342},
        "country": "Egypt",
        "continent": "Africa",
        "url": "https://www.skylinewebcams.com/en/webcam/egypt/cairo/giza/pyramids-of-giza.html",
        "type": "skyline"
    },
    "marrakech_jemaa": {
        "name": "Jemaa el-Fnaa, Marrakech",
        "location": {"lat": 31.6258, "lng": -7.9891},
        "country": "Morocco",
        "continent": "Africa",
        "url": "https://www.skylinewebcams.com/en/webcam/morocco/marrakech-tensift-al-haouz/marrakech/jemaa-el-fnaa.html",
        "type": "skyline"
    },
    
    # NATURE & WILDLIFE
    "yellowstone_old_faithful": {
        "name": "Old Faithful, Yellowstone",
        "location": {"lat": 44.4605, "lng": -110.8281},
        "country": "USA",
        "continent": "North America",
        "url": "https://www.nps.gov/yell/learn/photosmultimedia/webcams.htm",
        "type": "nps",
        "description": "Famous geyser"
    },
    "african_watering_hole": {
        "name": "African Watering Hole",
        "location": {"lat": -24.0000, "lng": 31.5000},
        "country": "South Africa",
        "continent": "Africa",
        "url": "https://explore.org/livecams/african-wildlife/african-watering-hole",
        "type": "explore",
        "description": "Wildlife viewing"
    },
    "northern_lights_alaska": {
        "name": "Northern Lights, Alaska",
        "location": {"lat": 64.8378, "lng": -147.7164},
        "country": "USA",
        "continent": "North America",
        "url": "https://auroraforecast.com/webcams/",
        "type": "aurora"
    }
}


class HolographicWebcamDisplay:
    """
    Holographic display system for webcam feeds.
    Creates portal/TV-like holographic effect.
    """
    
    def __init__(self):
        self.webcams = GLOBAL_WEBCAMS
        self.current_webcam = None
        self.display_mode = "hologram"  # hologram, portal, screen
        
        print(f"✅ Global Webcam Network initialized")
        print(f"   📷 {len(self.webcams)} webcams worldwide")
        print(f"   🌍 Covering all continents")
    
    def get_webcam(self, webcam_id: str) -> Optional[Dict]:
        """Get webcam by ID"""
        return self.webcams.get(webcam_id)
    
    def find_nearest_webcam(self, lat: float, lng: float) -> Optional[str]:
        """Find nearest webcam to coordinates"""
        min_dist = float('inf')
        nearest = None
        
        for webcam_id, webcam in self.webcams.items():
            loc = webcam["location"]
            dist = math.sqrt((loc["lat"] - lat)**2 + (loc["lng"] - lng)**2)
            if dist < min_dist:
                min_dist = dist
                nearest = webcam_id
        
        return nearest
    
    def search_webcams(self, query: str) -> List[Dict]:
        """Search webcams by name, country, or continent"""
        query_lower = query.lower()
        results = []
        
        for webcam_id, webcam in self.webcams.items():
            if (query_lower in webcam["name"].lower() or
                query_lower in webcam.get("country", "").lower() or
                query_lower in webcam.get("continent", "").lower() or
                query_lower in webcam_id.lower()):
                results.append({"id": webcam_id, **webcam})
        
        return results
    
    def get_webcams_by_continent(self, continent: str) -> List[Dict]:
        """Get all webcams in a continent"""
        return [
            {"id": wid, **w} for wid, w in self.webcams.items()
            if w.get("continent", "").lower() == continent.lower()
        ]
    
    def get_webcams_by_country(self, country: str) -> List[Dict]:
        """Get all webcams in a country"""
        return [
            {"id": wid, **w} for wid, w in self.webcams.items()
            if country.lower() in w.get("country", "").lower()
        ]
    
    def list_all_locations(self) -> List[str]:
        """List all webcam locations"""
        return [w["name"] for w in self.webcams.values()]
    
    def get_hologram_config(self, webcam_id: str) -> Dict:
        """Get holographic display configuration for a webcam"""
        webcam = self.get_webcam(webcam_id)
        if not webcam:
            return {}
        
        return {
            "webcam": webcam,
            "display_mode": self.display_mode,
            "hologram_settings": {
                "glow_color": (0, 200, 255),  # Cyan glow
                "transparency": 0.8,
                "border_style": "portal",
                "animation": "pulse",
                "size": (640, 480)
            },
            "portal_settings": {
                "shape": "oval",
                "edge_effect": "energy_ripple",
                "depth_effect": True
            }
        }
    
    def set_display_mode(self, mode: str):
        """Set display mode: hologram, portal, or screen"""
        if mode in ["hologram", "portal", "screen"]:
            self.display_mode = mode
            return True
        return False


# Singleton
_webcam_network = None

def get_webcam_network() -> HolographicWebcamDisplay:
    global _webcam_network
    if _webcam_network is None:
        _webcam_network = HolographicWebcamDisplay()
    return _webcam_network


if __name__ == "__main__":
    network = get_webcam_network()
    
    print("\n--- Webcams by Continent ---")
    for continent in ["North America", "Europe", "Asia", "Africa", "Oceania", "South America"]:
        cams = network.get_webcams_by_continent(continent)
        print(f"  {continent}: {len(cams)} webcams")
    
    print("\n--- Search: 'paris' ---")
    results = network.search_webcams("paris")
    for r in results:
        print(f"  📷 {r['name']}")
    
    print("\n--- Nearest to NYC (40.7, -74.0) ---")
    nearest = network.find_nearest_webcam(40.7, -74.0)
    if nearest:
        cam = network.get_webcam(nearest)
        print(f"  📷 {cam['name']}")
