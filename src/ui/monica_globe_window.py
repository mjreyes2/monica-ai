"""
Monica Globe Window - Separate Window with Green Screen for OBS Overlay
Displays the holographic globe in its own window for chroma key compositing.
"""
import cv2
import numpy as np
import math
import time
import threading
from typing import Tuple, Optional, Dict, List
from dataclasses import dataclass
from enum import Enum

# Green screen color (pure green for chroma key)
GREEN_SCREEN = (0, 255, 0)  # BGR


@dataclass
class GlobeState:
    """State of the globe."""
    rotation_x: float = 0.0
    rotation_y: float = 0.0
    zoom: float = 1.0
    target_lat: float = 0.0
    target_lng: float = 0.0
    auto_rotate: bool = True
    show_weather: bool = False
    show_lightning: bool = False
    show_daylight: bool = False


class MonicaGlobeWindow:
    """
    Separate window displaying the holographic globe on green screen.
    Perfect for OBS chroma key overlay.
    """
    
    def __init__(self, width: int = 600, height: int = 600):
        self.width = width
        self.height = height
        self.center = (width // 2, height // 2)
        self.base_radius = min(width, height) // 3
        
        # State
        self.state = GlobeState()
        self.visible = False
        self.running = False
        self.thread: Optional[threading.Thread] = None
        
        # Animation
        self.last_update = time.time()
        self.materialize_progress = 0.0
        self.is_materializing = False
        self.is_dematerializing = False
        
        # Globe data
        self.continent_outlines = self._generate_continent_outlines()
        self.cities = self._load_cities()
        self.highlighted_city: Optional[str] = None
        
        # Weather
        self.storm_zones = self._generate_storm_zones()
        self.lightning_bolts: List[dict] = []
        
        # Try to load realistic globe renderer
        self.realistic_globe = None
        try:
            from ui.monica_realistic_globe import RealisticGlobeRenderer
            self.realistic_globe = RealisticGlobeRenderer()
            print("[GlobeWindow] Realistic globe renderer loaded")
        except ImportError:
            print("[GlobeWindow] Using basic globe renderer")
        
        # Auto-detect user location via geo-IP
        try:
            from utils.location_services import get_location_service
            loc_svc = get_location_service()
            loc = loc_svc.get_current_location()
            if loc and loc.get("lat") and loc.get("lon"):
                self.state.target_lat = loc["lat"]
                self.state.target_lng = loc["lon"]
                print(f"[GlobeWindow] User location: {loc.get('city', '?')}, {loc.get('country', '?')}")
        except Exception:
            pass
        
        print("[GlobeWindow] Globe window initialized (green screen mode)")
    
    def _generate_continent_outlines(self) -> Dict[str, List[Tuple[float, float]]]:
        """Generate simplified continent outlines (lat, lng pairs)."""
        return {
            "north_america": [
                (49, -125), (49, -95), (45, -85), (30, -85), (25, -80),
                (25, -97), (30, -105), (32, -117), (40, -124), (49, -125)
            ],
            "south_america": [
                (10, -75), (5, -55), (-5, -35), (-23, -43), (-35, -58),
                (-55, -68), (-50, -75), (-20, -70), (-5, -80), (10, -75)
            ],
            "europe": [
                (35, -10), (40, 0), (45, 10), (55, 10), (60, 25),
                (70, 30), (70, 40), (55, 40), (45, 35), (35, 25), (35, -10)
            ],
            "africa": [
                (35, -10), (30, 10), (10, 15), (5, 40), (-10, 40),
                (-35, 20), (-35, 15), (-20, 15), (0, -5), (15, -17), (35, -10)
            ],
            "asia": [
                (70, 40), (70, 180), (35, 140), (20, 120), (10, 100),
                (25, 65), (35, 45), (45, 40), (55, 40), (70, 40)
            ],
            "australia": [
                (-10, 115), (-10, 150), (-25, 153), (-35, 140),
                (-35, 115), (-20, 115), (-10, 115)
            ]
        }
    
    def _load_cities(self) -> Dict[str, Dict]:
        """Load major cities."""
        return {
            "new york": {"lat": 40.7128, "lng": -74.006, "name": "New York"},
            "london": {"lat": 51.5072, "lng": -0.1276, "name": "London"},
            "tokyo": {"lat": 35.6762, "lng": 139.6503, "name": "Tokyo"},
            "paris": {"lat": 48.8566, "lng": 2.3522, "name": "Paris"},
            "sydney": {"lat": -33.8688, "lng": 151.2093, "name": "Sydney"},
            "dubai": {"lat": 25.2048, "lng": 55.2708, "name": "Dubai"},
        }
    
    def _generate_storm_zones(self) -> List[Dict]:
        """Generate simulated storm zones."""
        return [
            {"lat": 25, "lng": -80, "intensity": 0.8, "name": "Atlantic"},
            {"lat": 15, "lng": 130, "intensity": 0.9, "name": "Pacific"},
            {"lat": -15, "lng": 90, "intensity": 0.6, "name": "Indian Ocean"},
            {"lat": 45, "lng": -30, "intensity": 0.7, "name": "North Atlantic"},
        ]
    
    def _lat_lng_to_screen(self, lat: float, lng: float, radius: int) -> Optional[Tuple[int, int]]:
        """Convert lat/lng to screen coordinates on the globe."""
        # Apply rotation to longitude (positive rotation = rotate globe left)
        lng_adjusted = lng + math.degrees(self.state.rotation_y)
        
        lat_rad = math.radians(lat)
        lng_rad = math.radians(lng_adjusted)
        
        # Check if point is on visible side (simple front hemisphere check)
        cos_lat = math.cos(lat_rad)
        if cos_lat < 0:  # Point is on the far side of the globe
            return None
        
        # Standard spherical projection with north pole up
        # x = radius * cos(lat) * sin(lng)  - horizontal position
        # y = -radius * sin(lat)            - vertical position (negative = up)
        x = radius * cos_lat * math.sin(lng_rad)
        y = -radius * math.sin(lat_rad)
        
        screen_x = int(self.center[0] + x)
        screen_y = int(self.center[1] + y)
        
        return (screen_x, screen_y)
    
    def show(self):
        """Show the globe with materialization effect."""
        if not self.visible:
            self.is_materializing = True
            self.is_dematerializing = False
            self.materialize_progress = 0.0
            print("[GlobeWindow] Globe materializing...")
    
    def hide(self):
        """Hide the globe with dematerialization effect."""
        if self.visible or self.is_materializing:
            self.is_dematerializing = True
            self.is_materializing = False
            print("[GlobeWindow] Globe dematerializing...")
    
    def set_location(self, lat: float, lng: float, city_name: str = None):
        """Set the globe to show a specific location."""
        self.state.target_lat = lat
        self.state.target_lng = lng
        self.state.rotation_y = math.radians(-lng)  # Rotate to show the location (convert to radians)
        self.highlighted_city = city_name
    
    def show_country(self, country_name: str) -> bool:
        """
        Show a country on the globe using Rest Countries API.
        
        Args:
            country_name: Name of the country (e.g., "Japan", "Brazil")
            
        Returns:
            True if country was found and globe updated
        """
        try:
            # Import the free APIs
            import sys
            sys.path.insert(0, str(__file__).replace('monica_globe_window.py', 'monica_ai/src'))
            from utils.free_apis import get_free_apis
            
            apis = get_free_apis()
            country = apis.get_country_info(country_name)
            
            if country.get("success"):
                lat = country.get("lat", 0)
                lon = country.get("lon", 0)
                name = country.get("name", country_name)
                capital = country.get("capital", "")
                
                # Set globe to show this country
                self.set_location(lat, lon, f"{name} ({capital})")
                self.state.auto_rotate = False  # Stop auto-rotate to focus on country
                
                print(f"[GlobeWindow] Showing {name} at {lat}, {lon}")
                return True
            else:
                print(f"[GlobeWindow] Country not found: {country_name}")
                return False
                
        except Exception as e:
            print(f"[GlobeWindow] Error showing country: {e}")
            return False
    
    def show_region(self, region: str) -> bool:
        """
        Show all countries in a region on the globe.
        
        Args:
            region: Region name (Africa, Americas, Asia, Europe, Oceania)
        """
        try:
            import sys
            sys.path.insert(0, str(__file__).replace('monica_globe_window.py', 'monica_ai/src'))
            from utils.free_apis import get_free_apis
            
            apis = get_free_apis()
            region_data = apis.get_countries_by_region(region)
            
            if region_data.get("success"):
                countries = region_data.get("countries", [])
                if countries:
                    # Calculate center of region
                    avg_lat = sum(c.get("lat", 0) for c in countries) / len(countries)
                    avg_lon = sum(c.get("lon", 0) for c in countries) / len(countries)
                    
                    self.set_location(avg_lat, avg_lon, f"{region} ({len(countries)} countries)")
                    self.state.auto_rotate = False
                    
                    print(f"[GlobeWindow] Showing {region} centered at {avg_lat:.1f}, {avg_lon:.1f}")
                    return True
            
            return False
            
        except Exception as e:
            print(f"[GlobeWindow] Error showing region: {e}")
            return False
    
    def toggle_weather(self, show: bool):
        """Toggle weather visualization."""
        self.state.show_weather = show
        self.state.show_lightning = show
    
    def _update(self, dt: float):
        """Update animation state."""
        # Auto-rotate
        if self.state.auto_rotate and self.visible:
            self.state.rotation_y += math.radians(dt * 5)  # 5 degrees per second (convert to radians)
            if self.state.rotation_y > math.pi:
                self.state.rotation_y -= 2 * math.pi
        
        # Materialization
        if self.is_materializing:
            self.materialize_progress += dt / 2.0  # 2 seconds to materialize
            if self.materialize_progress >= 1.0:
                self.materialize_progress = 1.0
                self.is_materializing = False
                self.visible = True
        
        # Dematerialization
        if self.is_dematerializing:
            self.materialize_progress -= dt / 1.5  # 1.5 seconds to dematerialize
            if self.materialize_progress <= 0.0:
                self.materialize_progress = 0.0
                self.is_dematerializing = False
                self.visible = False
        
        # Update lightning
        if self.state.show_lightning and (self.visible or self.is_materializing):
            # Spawn new lightning
            if np.random.random() < 0.1:
                for storm in self.storm_zones:
                    if np.random.random() < storm["intensity"] * 0.3:
                        self.lightning_bolts.append({
                            "lat": storm["lat"] + np.random.uniform(-10, 10),
                            "lng": storm["lng"] + np.random.uniform(-10, 10),
                            "birth": time.time(),
                            "lifetime": np.random.uniform(0.1, 0.3)
                        })
            
            # Remove old lightning
            current_time = time.time()
            self.lightning_bolts = [b for b in self.lightning_bolts 
                                   if current_time - b["birth"] < b["lifetime"]]
    
    def _render(self) -> np.ndarray:
        """Render the globe frame."""
        # Green screen background
        frame = np.full((self.height, self.width, 3), GREEN_SCREEN, dtype=np.uint8)
        
        if self.materialize_progress <= 0:
            return frame
        
        # Calculate current radius with materialization effect
        current_radius = int(self.base_radius * self.state.zoom * self.materialize_progress)
        
        if current_radius < 10:
            return frame
        
        # Use realistic globe if available
        if self.realistic_globe and self.materialize_progress > 0.5:
            try:
                # Create a sub-frame for the globe
                globe_frame = self.realistic_globe.render(
                    self.width, self.height,
                    self.state.rotation_y,
                    self.state.rotation_x,
                    self.state.zoom * self.materialize_progress
                )
                
                # Composite onto green screen (replace non-black pixels)
                mask = np.any(globe_frame > 20, axis=2)
                frame[mask] = globe_frame[mask]
                
                # Add materialization effect
                if self.is_materializing or self.is_dematerializing:
                    self._add_materialize_effect(frame, current_radius)
                
                return frame
            except Exception as e:
                pass  # Fall back to basic rendering
        
        # Basic globe rendering
        self._render_basic_globe(frame, current_radius)
        
        # Add materialization effect
        if self.is_materializing or self.is_dematerializing:
            self._add_materialize_effect(frame, current_radius)
        
        return frame
    
    def _render_basic_globe(self, frame: np.ndarray, radius: int):
        """Render a basic holographic globe."""
        # Outer glow
        for i in range(5, 0, -1):
            glow_radius = radius + i * 8
            alpha = 0.15 * (6 - i) / 5 * self.materialize_progress
            glow_color = (int(255 * alpha), int(200 * alpha), int(100 * alpha))  # Cyan glow
            cv2.circle(frame, self.center, glow_radius, glow_color, 2, cv2.LINE_AA)
        
        # Globe sphere with gradient
        for r in range(radius, 0, -2):
            ratio = r / radius
            intensity = 0.3 + 0.4 * (1 - ratio)
            color = (int(200 * intensity), int(150 * intensity), int(50 * intensity))  # Cyan
            cv2.circle(frame, self.center, r, color, 1, cv2.LINE_AA)
        
        # Grid lines (latitude)
        for lat in range(-60, 90, 30):
            points = []
            for lng in range(-180, 181, 10):
                pos = self._lat_lng_to_screen(lat, lng, radius)
                if pos:
                    points.append(pos)
            if len(points) > 1:
                for i in range(len(points) - 1):
                    cv2.line(frame, points[i], points[i+1], (150, 120, 50), 1, cv2.LINE_AA)
        
        # Grid lines (longitude)
        for lng in range(-180, 180, 30):
            points = []
            for lat in range(-90, 91, 10):
                pos = self._lat_lng_to_screen(lat, lng, radius)
                if pos:
                    points.append(pos)
            if len(points) > 1:
                for i in range(len(points) - 1):
                    cv2.line(frame, points[i], points[i+1], (150, 120, 50), 1, cv2.LINE_AA)
        
        # Continents - filled polygons with bright outlines
        for continent, outline in self.continent_outlines.items():
            points = []
            for lat, lng in outline:
                pos = self._lat_lng_to_screen(lat, lng, radius)
                if pos:
                    points.append(pos)
            if len(points) > 2:
                pts = np.array(points, np.int32)
                # Fill continent with semi-transparent green
                cv2.fillPoly(frame, [pts], (180, 220, 80))
                # Bright outline
                cv2.polylines(frame, [pts], True, (255, 255, 150), 2, cv2.LINE_AA)
        
        # User location - yellow pulsing dot
        if self.state.target_lat != 0 or self.state.target_lng != 0:
            loc_pos = self._lat_lng_to_screen(self.state.target_lat, self.state.target_lng, radius)
            if loc_pos:
                pulse = 0.5 + 0.5 * math.sin(time.time() * 4.0)
                pulse_r = int(6 + 8 * pulse)
                # Outer glow
                cv2.circle(frame, loc_pos, pulse_r + 4, (0, int(180 * pulse), 255), 2, cv2.LINE_AA)
                cv2.circle(frame, loc_pos, pulse_r, (0, 255, 255), -1, cv2.LINE_AA)
                # Inner bright dot
                cv2.circle(frame, loc_pos, 3, (255, 255, 255), -1, cv2.LINE_AA)
        
        # Cities
        for city_key, city in self.cities.items():
            pos = self._lat_lng_to_screen(city["lat"], city["lng"], radius)
            if pos:
                color = (0, 255, 255) if city_key == self.highlighted_city else (255, 255, 0)
                cv2.circle(frame, pos, 4, color, -1, cv2.LINE_AA)
        
        # Lightning
        for bolt in self.lightning_bolts:
            pos = self._lat_lng_to_screen(bolt["lat"], bolt["lng"], radius)
            if pos:
                age = time.time() - bolt["birth"]
                alpha = 1 - age / bolt["lifetime"]
                color = (int(255 * alpha), int(255 * alpha), int(200 * alpha))
                cv2.circle(frame, pos, 8, color, -1, cv2.LINE_AA)
                cv2.circle(frame, pos, 12, (int(200 * alpha), int(200 * alpha), int(100 * alpha)), 2, cv2.LINE_AA)
        
        # Title
        title = "HOLOGRAPHIC GLOBE"
        font = cv2.FONT_HERSHEY_SIMPLEX
        text_size = cv2.getTextSize(title, font, 0.6, 1)[0]
        text_x = (self.width - text_size[0]) // 2
        cv2.putText(frame, title, (text_x, 30), font, 0.6, (255, 200, 100), 1, cv2.LINE_AA)
    
    def _add_materialize_effect(self, frame: np.ndarray, radius: int):
        """Add scan lines and particles during materialization."""
        progress = self.materialize_progress
        
        # Horizontal scan line
        scan_y = int(self.center[1] - radius + (2 * radius * progress))
        if self.center[1] - radius < scan_y < self.center[1] + radius:
            cv2.line(frame, (self.center[0] - radius, scan_y), 
                    (self.center[0] + radius, scan_y), (255, 255, 255), 2, cv2.LINE_AA)
        
        # Particles
        num_particles = int(20 * (1 - progress))
        for _ in range(num_particles):
            angle = np.random.uniform(0, 2 * np.pi)
            dist = np.random.uniform(radius * 0.8, radius * 1.5)
            px = int(self.center[0] + dist * np.cos(angle))
            py = int(self.center[1] + dist * np.sin(angle))
            if 0 <= px < self.width and 0 <= py < self.height:
                cv2.circle(frame, (px, py), 2, (255, 200, 100), -1, cv2.LINE_AA)
    
    def _run_loop(self):
        """Main render loop."""
        cv2.namedWindow("Monica Globe", cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO)
        cv2.resizeWindow("Monica Globe", self.width, self.height)
        
        # Bring window to front
        try:
            import ctypes
            hwnd = ctypes.windll.user32.FindWindowW(None, "Monica Globe")
            if hwnd:
                ctypes.windll.user32.SetForegroundWindow(hwnd)
                ctypes.windll.user32.BringWindowToTop(hwnd)
                ctypes.windll.user32.ShowWindow(hwnd, 9)  # SW_RESTORE
        except:
            pass
        
        last_time = time.time()
        
        while self.running:
            current_time = time.time()
            dt = current_time - last_time
            last_time = current_time
            
            self._update(dt)
            frame = self._render()
            
            cv2.imshow("Monica Globe", frame)
            
            key = cv2.waitKey(16) & 0xFF  # ~60 FPS
            if key == ord('q'):
                break
            elif key == ord('s'):  # Show
                self.show()
            elif key == ord('h'):  # Hide
                self.hide()
            elif key == ord('w'):  # Toggle weather
                self.toggle_weather(not self.state.show_weather)
            elif key == ord('r'):  # Toggle rotation
                self.state.auto_rotate = not self.state.auto_rotate
        
        cv2.destroyWindow("Monica Globe")
    
    def start(self):
        """Start the globe window in a separate thread."""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._run_loop, daemon=True)
            self.thread.start()
            print("[GlobeWindow] Window started (Press 's' to show, 'h' to hide, 'w' for weather, 'q' to quit)")
    
    def stop(self):
        """Stop the globe window and clean up properly."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
        # IMPORTANT: Destroy window to prevent duplicates
        try:
            cv2.destroyWindow("Monica Globe")
        except:
            pass
        print("[GlobeWindow] Window stopped and cleaned up")
    
    def cleanup(self):
        """Force cleanup of all resources."""
        self.running = False
        try:
            cv2.destroyWindow("Monica Globe")
        except:
            pass


def get_globe_window():
    """Get singleton globe window instance."""
    if not hasattr(get_globe_window, '_instance'):
        get_globe_window._instance = MonicaGlobeWindow()
    return get_globe_window._instance


if __name__ == "__main__":
    """Run globe window standalone when executed directly."""
    print("[GlobeWindow] Running standalone...")
    globe = get_globe_window()
    globe.start()
    
    try:
        # Keep running until window is closed
        while globe.running:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("[GlobeWindow] Interrupted by user")
    finally:
        globe.stop()
        print("[GlobeWindow] Stopped")


# Singleton instance
_globe_window: Optional[MonicaGlobeWindow] = None


def get_globe_window() -> MonicaGlobeWindow:
    """Get singleton globe window instance. Cleans up old instance if exists."""
    global _globe_window
    if _globe_window is not None:
        # Clean up existing window if not running
        if not _globe_window.running:
            _globe_window.cleanup()
            _globe_window = None
    if _globe_window is None:
        _globe_window = MonicaGlobeWindow()
    return _globe_window


def cleanup_globe_window():
    """Force cleanup of globe window singleton."""
    global _globe_window
    if _globe_window is not None:
        _globe_window.cleanup()
        _globe_window = None


# Test mode
if __name__ == "__main__":
    print("Monica Globe Window - Green Screen Mode")
    print("Press 's' to show, 'h' to hide, 'w' for weather, 'r' to toggle rotation, 'q' to quit")
    
    globe = MonicaGlobeWindow(600, 600)
    globe.running = True
    globe._run_loop()
