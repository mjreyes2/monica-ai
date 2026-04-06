"""
Monica Map Navigation System
City-level map view with dark theme, route lines, markers, and distance indicators.
Displays navigation directions in a futuristic sci-fi style.
"""

import cv2
import numpy as np
import math
import time
import threading
from typing import Optional, Dict, List, Tuple, Any
from dataclasses import dataclass
import requests

# Try to import geocoding
HAS_GEOCODER = False
try:
    from geopy.geocoders import Nominatim
    from geopy.distance import geodesic
    HAS_GEOCODER = True
except ImportError:
    pass

# OpenCV window manager for green screen display
HAS_WINDOW_MANAGER = False
try:
    from opencv_window_manager import get_window_manager
    HAS_WINDOW_MANAGER = True
except ImportError:
    pass


@dataclass
class RoutePoint:
    """A point along a route."""
    lat: float
    lng: float
    name: str = ""
    is_waypoint: bool = False


@dataclass
class NavigationRoute:
    """A navigation route between two points."""
    start: RoutePoint
    end: RoutePoint
    waypoints: List[RoutePoint]
    distance_km: float
    estimated_time_min: int
    route_points: List[Tuple[float, float]]  # List of (lat, lng) for the route line


class MapNavigationWindow:
    """
    Renders a dark-themed city-level map with route navigation.
    Style: Futuristic sci-fi like the reference image.
    """
    
    def __init__(self, width: int = 800, height: int = 600):
        self.width = width
        self.height = height
        self.is_visible = False
        
        # Map state
        self.center_lat = 27.9506  # Default Tampa
        self.center_lng = -82.4572
        self.zoom_level = 14  # City street level
        
        # Current route
        self.current_route: Optional[NavigationRoute] = None
        
        # Animation
        self.animation_time = 0.0
        self.pulse_phase = 0.0
        
        # Colors (dark sci-fi theme)
        self.bg_color = (15, 15, 25)  # Very dark blue-black
        self.grid_color = (30, 40, 60)  # Dark blue grid
        self.road_color = (45, 55, 75)  # Slightly lighter roads
        self.route_color = (255, 180, 0)  # Bright orange/gold route
        self.route_glow = (255, 220, 100)  # Route glow
        self.marker_color = (0, 200, 255)  # Cyan markers
        self.text_color = (200, 220, 255)  # Light blue text
        self.distance_color = (255, 255, 255)  # White distance
        
        # Geocoder for location lookup
        self.geocoder = None
        if HAS_GEOCODER:
            try:
                self.geocoder = Nominatim(user_agent="monica_ai_navigator")
            except:
                pass
        
        # Window manager
        self.window_manager = None
        self.window_name = "Monica Navigation"
        
        print("[MAP-NAV] Map Navigation System initialized")
    
    def _geocode_location(self, location: str) -> Optional[Tuple[float, float, str]]:
        """Convert location name to coordinates."""
        if self.geocoder:
            try:
                result = self.geocoder.geocode(location, timeout=5)
                if result:
                    return (result.latitude, result.longitude, result.address)
            except Exception as e:
                print(f"[MAP-NAV] Geocode error: {e}")
        
        # Fallback: common locations
        known_locations = {
            "tampa": (27.9506, -82.4572, "Tampa, FL"),
            "orlando": (28.5383, -81.3792, "Orlando, FL"),
            "miami": (25.7617, -80.1918, "Miami, FL"),
            "jacksonville": (30.3322, -81.6557, "Jacksonville, FL"),
            "clearwater": (27.9659, -82.8001, "Clearwater, FL"),
            "st petersburg": (27.7676, -82.6403, "St. Petersburg, FL"),
            "new york": (40.7128, -74.0060, "New York, NY"),
            "los angeles": (34.0522, -118.2437, "Los Angeles, CA"),
            "chicago": (41.8781, -87.6298, "Chicago, IL"),
        }
        
        loc_lower = location.lower().strip()
        if loc_lower in known_locations:
            return known_locations[loc_lower]
        
        return None
    
    def set_route(self, start_location: str, end_location: str) -> str:
        """Set a navigation route between two locations."""
        # Geocode start
        start_geo = self._geocode_location(start_location)
        if not start_geo:
            return f"Could not find location: {start_location}"
        
        # Geocode end
        end_geo = self._geocode_location(end_location)
        if not end_geo:
            return f"Could not find location: {end_location}"
        
        start_point = RoutePoint(lat=start_geo[0], lng=start_geo[1], name=start_geo[2])
        end_point = RoutePoint(lat=end_geo[0], lng=end_geo[1], name=end_geo[2])
        
        # Calculate distance
        if HAS_GEOCODER:
            try:
                distance = geodesic((start_geo[0], start_geo[1]), (end_geo[0], end_geo[1])).kilometers
            except:
                distance = self._haversine_distance(start_geo[0], start_geo[1], end_geo[0], end_geo[1])
        else:
            distance = self._haversine_distance(start_geo[0], start_geo[1], end_geo[0], end_geo[1])
        
        # Estimate time (assuming 50 km/h average city driving)
        estimated_time = int(distance / 50 * 60)
        if estimated_time < 1:
            estimated_time = 1
        
        # Generate route points (simplified - straight line with some waypoints)
        route_points = self._generate_route_points(start_point, end_point)
        
        self.current_route = NavigationRoute(
            start=start_point,
            end=end_point,
            waypoints=[],
            distance_km=distance,
            estimated_time_min=estimated_time,
            route_points=route_points
        )
        
        # Center map on route midpoint
        self.center_lat = (start_geo[0] + end_geo[0]) / 2
        self.center_lng = (start_geo[1] + end_geo[1]) / 2
        
        # Adjust zoom based on distance
        if distance < 5:
            self.zoom_level = 15
        elif distance < 20:
            self.zoom_level = 13
        elif distance < 50:
            self.zoom_level = 11
        else:
            self.zoom_level = 9
        
        return f"Route set: {distance:.1f} km, approximately {estimated_time} minutes"
    
    def set_destination(self, destination: str) -> str:
        """Set destination from current location."""
        # Use Tampa as default start (user's location)
        return self.set_route("Tampa, FL", destination)
    
    def _haversine_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Calculate distance between two points using Haversine formula."""
        R = 6371  # Earth radius in km
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lng = math.radians(lng2 - lng1)
        
        a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lng/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    def _generate_route_points(self, start: RoutePoint, end: RoutePoint, num_points: int = 20) -> List[Tuple[float, float]]:
        """Generate points along a route (simplified - adds some randomness for realistic look)."""
        points = []
        
        for i in range(num_points + 1):
            t = i / num_points
            
            # Linear interpolation with slight curve
            lat = start.lat + (end.lat - start.lat) * t
            lng = start.lng + (end.lng - start.lng) * t
            
            # Add slight variation for more realistic route look
            if 0 < i < num_points:
                offset = math.sin(t * math.pi * 3) * 0.002  # Small offset
                lat += offset
                lng += offset * 0.5
            
            points.append((lat, lng))
        
        return points
    
    def _lat_lng_to_screen(self, lat: float, lng: float) -> Tuple[int, int]:
        """Convert lat/lng to screen coordinates."""
        # Simplified Mercator projection
        scale = 256 * (2 ** self.zoom_level) / 360
        
        x = (lng - self.center_lng) * scale + self.width / 2
        y = (self.center_lat - lat) * scale * 1.2 + self.height / 2  # 1.2 factor for latitude stretch
        
        return (int(x), int(y))
    
    def _draw_grid(self, frame: np.ndarray):
        """Draw the background grid."""
        # Draw vertical lines
        for x in range(0, self.width, 40):
            cv2.line(frame, (x, 0), (x, self.height), self.grid_color, 1)
        
        # Draw horizontal lines
        for y in range(0, self.height, 40):
            cv2.line(frame, (0, y), (self.width, y), self.grid_color, 1)
    
    def _draw_roads(self, frame: np.ndarray):
        """Draw simplified road network."""
        # Generate procedural roads based on position
        np.random.seed(int(self.center_lat * 1000 + self.center_lng * 100) % 10000)
        
        # Main roads (horizontal and vertical)
        for i in range(5):
            # Horizontal roads
            y = int(self.height * (0.15 + i * 0.2))
            cv2.line(frame, (0, y), (self.width, y), self.road_color, 2)
            
            # Vertical roads
            x = int(self.width * (0.1 + i * 0.2))
            cv2.line(frame, (x, 0), (x, self.height), self.road_color, 2)
        
        # Secondary roads (diagonal and curved)
        for _ in range(8):
            x1 = np.random.randint(0, self.width)
            y1 = np.random.randint(0, self.height)
            x2 = x1 + np.random.randint(-200, 200)
            y2 = y1 + np.random.randint(-200, 200)
            cv2.line(frame, (x1, y1), (x2, y2), self.road_color, 1)
    
    def _draw_route(self, frame: np.ndarray):
        """Draw the navigation route with glow effect."""
        if not self.current_route or not self.current_route.route_points:
            return
        
        # Convert route points to screen coordinates
        screen_points = []
        for lat, lng in self.current_route.route_points:
            x, y = self._lat_lng_to_screen(lat, lng)
            screen_points.append((x, y))
        
        # Draw glow (multiple passes)
        for glow_size in [8, 5, 3]:
            pts = np.array(screen_points, np.int32).reshape((-1, 1, 2))
            alpha = 0.3 if glow_size > 5 else 0.5
            glow_color = tuple(int(c * alpha) for c in self.route_glow)
            cv2.polylines(frame, [pts], False, glow_color, glow_size)
        
        # Draw main route line
        pts = np.array(screen_points, np.int32).reshape((-1, 1, 2))
        cv2.polylines(frame, [pts], False, self.route_color, 2)
        
        # Animated pulse along route
        pulse_pos = int((self.pulse_phase % 1.0) * len(screen_points))
        if 0 <= pulse_pos < len(screen_points):
            px, py = screen_points[pulse_pos]
            cv2.circle(frame, (px, py), 8, self.route_glow, -1)
            cv2.circle(frame, (px, py), 12, self.route_color, 2)
    
    def _draw_markers(self, frame: np.ndarray):
        """Draw start and end markers."""
        if not self.current_route:
            return
        
        # Start marker (cyan circle with ring)
        start_x, start_y = self._lat_lng_to_screen(
            self.current_route.start.lat, 
            self.current_route.start.lng
        )
        cv2.circle(frame, (start_x, start_y), 15, self.marker_color, -1)
        cv2.circle(frame, (start_x, start_y), 20, self.marker_color, 2)
        cv2.circle(frame, (start_x, start_y), 25, (100, 150, 200), 1)
        
        # End marker (cyan pin shape)
        end_x, end_y = self._lat_lng_to_screen(
            self.current_route.end.lat,
            self.current_route.end.lng
        )
        # Draw pin
        pts = np.array([
            [end_x, end_y - 30],
            [end_x - 10, end_y - 15],
            [end_x, end_y],
            [end_x + 10, end_y - 15]
        ], np.int32)
        cv2.fillPoly(frame, [pts], self.marker_color)
        cv2.circle(frame, (end_x, end_y - 25), 8, (255, 255, 255), -1)
    
    def _draw_distance_indicator(self, frame: np.ndarray):
        """Draw the distance indicator on the route."""
        if not self.current_route:
            return
        
        # Draw distance label at midpoint of route
        if self.current_route.route_points:
            mid_idx = len(self.current_route.route_points) // 2
            mid_lat, mid_lng = self.current_route.route_points[mid_idx]
            mid_x, mid_y = self._lat_lng_to_screen(mid_lat, mid_lng)
            
            # Distance text with background
            distance_text = f"{self.current_route.distance_km:.1f} km"
            (text_w, text_h), _ = cv2.getTextSize(distance_text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            
            # Background rectangle
            pad = 8
            cv2.rectangle(frame, 
                         (mid_x - text_w//2 - pad, mid_y - text_h - pad),
                         (mid_x + text_w//2 + pad, mid_y + pad),
                         (30, 40, 60), -1)
            cv2.rectangle(frame,
                         (mid_x - text_w//2 - pad, mid_y - text_h - pad),
                         (mid_x + text_w//2 + pad, mid_y + pad),
                         self.route_color, 1)
            
            # Distance text
            cv2.putText(frame, distance_text,
                       (mid_x - text_w//2, mid_y),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, self.distance_color, 2)
    
    def _draw_header(self, frame: np.ndarray):
        """Draw the header with MAP NAVIGATION title."""
        # Title
        cv2.putText(frame, "MAP NAVIGATION", (15, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, self.text_color, 2)
        
        # Location info (top right)
        if self.current_route:
            loc_text = f"LOCATION: {self.current_route.end.name[:30]}"
        else:
            loc_text = f"LOCATION: {self.center_lat:.4f}, {self.center_lng:.4f}"
        
        (text_w, _), _ = cv2.getTextSize(loc_text, cv2.FONT_HERSHEY_SIMPLEX, 0.4, 1)
        cv2.putText(frame, loc_text, (self.width - text_w - 15, 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (150, 170, 200), 1)
        
        # Save button indicator (top right corner)
        cv2.putText(frame, "+ Save", (self.width - 60, 45),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, self.text_color, 1)
    
    def _draw_info_panel(self, frame: np.ndarray):
        """Draw route info panel at bottom."""
        if not self.current_route:
            return
        
        # Panel background
        panel_h = 60
        panel_y = self.height - panel_h
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, panel_y), (self.width, self.height), (20, 25, 35), -1)
        cv2.addWeighted(overlay, 0.8, frame, 0.2, 0, frame)
        
        # Route info
        info_text = f"Route: {self.current_route.distance_km:.1f} km | ETA: {self.current_route.estimated_time_min} min"
        cv2.putText(frame, info_text, (15, panel_y + 25),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, self.text_color, 1)
        
        # Destination
        dest_text = f"To: {self.current_route.end.name[:40]}"
        cv2.putText(frame, dest_text, (15, panel_y + 45),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (150, 170, 200), 1)
    
    def _draw_similar_images_badge(self, frame: np.ndarray):
        """Draw 'Similar images' badge like in reference."""
        badge_text = "Similar images"
        (text_w, text_h), _ = cv2.getTextSize(badge_text, cv2.FONT_HERSHEY_SIMPLEX, 0.4, 1)
        
        x = self.width - text_w - 20
        y = self.height - 80
        
        # Background
        cv2.rectangle(frame, (x - 5, y - text_h - 5), (x + text_w + 5, y + 5), (40, 50, 70), -1)
        cv2.putText(frame, badge_text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.4, self.text_color, 1)
    
    def render_frame(self) -> np.ndarray:
        """Render a single frame of the map navigation view."""
        # Create dark background
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        frame[:] = self.bg_color
        
        # Update animation
        self.animation_time = time.time()
        self.pulse_phase = (self.animation_time * 0.5) % 1.0
        
        # Draw layers
        self._draw_grid(frame)
        self._draw_roads(frame)
        self._draw_route(frame)
        self._draw_markers(frame)
        self._draw_distance_indicator(frame)
        self._draw_header(frame)
        self._draw_info_panel(frame)
        
        return frame
    
    def show(self, destination: str = None) -> str:
        """Show the map navigation window."""
        if destination:
            result = self.set_destination(destination)
        else:
            result = "Map navigation ready. Say 'directions to [location]' to set a route."
        
        self.is_visible = True
        
        # Use OpenCV window manager if available
        if HAS_WINDOW_MANAGER:
            manager = get_window_manager()
            manager.create_window(self.window_name, self.width, self.height, self._frame_generator)
            manager.show_window(self.window_name)
        
        return result
    
    def _frame_generator(self):
        """Generator function for window manager."""
        while self.is_visible:
            yield self.render_frame()
            time.sleep(0.033)  # ~30 FPS
    
    def hide(self) -> str:
        """Hide the map navigation window."""
        self.is_visible = False
        
        if HAS_WINDOW_MANAGER:
            manager = get_window_manager()
            manager.hide_window(self.window_name)
        
        return "Map navigation hidden."
    
    def go_to_city_level(self, city: str = None) -> str:
        """Zoom to city level view."""
        if city:
            geo = self._geocode_location(city)
            if geo:
                self.center_lat = geo[0]
                self.center_lng = geo[1]
                self.zoom_level = 14
                return f"Showing city level view of {geo[2]}"
        
        self.zoom_level = 14
        return "City level view activated"


# Global instance
_map_navigation: Optional[MapNavigationWindow] = None


def get_map_navigation() -> MapNavigationWindow:
    """Get the global map navigation instance."""
    global _map_navigation
    if _map_navigation is None:
        _map_navigation = MapNavigationWindow()
    return _map_navigation


# Test
if __name__ == "__main__":
    nav = get_map_navigation()
    nav.set_route("Tampa, FL", "Orlando, FL")
    
    # Show preview
    while True:
        frame = nav.render_frame()
        cv2.imshow("Map Navigation Test", frame)
        if cv2.waitKey(30) & 0xFF == 27:  # ESC to quit
            break
    
    cv2.destroyAllWindows()
