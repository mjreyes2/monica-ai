"""

MONICA AI - ADVANCED HOLOGRAPHIC GLOBE SYSTEM



Interactive 3D Earth with:

- Google Maps integration

- Location markers with glow effects

- Zoom capabilities

- Public webcam feeds

- Hand gesture controls

- Sci-fi sound effects

- Matrix-style image viewer

- Natural language location queries



Author: Monica AI System

Date: December 2, 2025

"""



import os

import cv2

import numpy as np

import pygame

from pygame import mixer

import requests

import json

from pathlib import Path

from typing import Dict, List, Tuple, Optional

from dataclasses import dataclass

import math

import time



try:

    from utils.location_services import get_location_services

    HAS_LOCATION_SERVICES = True

except Exception:

    HAS_LOCATION_SERVICES = False





@dataclass

class Location:

    """Represents a location on the globe."""

    name: str

    latitude: float

    longitude: float

    category: str

    marker_color: Tuple[int, int, int] = (0, 255, 255)  # Cyan glow

    webcam_urls: List[str] = None

    photos: List[str] = None





class SciFiSoundEffects:

    """

    Sci-fi sound effects for holographic interface.

    """



    def __init__(self):

        try:

            pygame.mixer.init()

            self.enabled = True

            self.sounds = {}

            self.channels = {}

            self.hologram_ambient_active = False

            self.location_pulse_active = False

            self._generate_sounds()

            self._load_external_sounds()

        except:

            self.enabled = False

            print("[WARN] Audio not available")



    def _generate_sounds(self):

        """Generate procedural sci-fi sounds."""

        # Create sound buffers

        sample_rate = 22050



        # Beep sound (for location marker)

        duration = 0.1

        frequency = 880

        samples = int(sample_rate * duration)

        wave = np.array([32767 * np.sin(2.0 * np.pi * frequency * x / sample_rate) for x in range(samples)])

        stereo = np.zeros((samples, 2), dtype=np.int16)

        stereo[:, 0] = wave

        stereo[:, 1] = wave



        try:

            self.sounds['beep'] = pygame.sndarray.make_sound(stereo)

        except:

            pass



        # Whoosh sound (for zoom)

        duration = 0.3

        samples = int(sample_rate * duration)

        frequency_start = 200

        frequency_end = 800

        wave = np.array([

            32767 * np.sin(2.0 * np.pi * (frequency_start + (frequency_end - frequency_start) * x / samples) * x / sample_rate)

            * (1 - x / samples)  # Fade out

            for x in range(samples)

        ])

        stereo = np.zeros((samples, 2), dtype=np.int16)

        stereo[:, 0] = wave

        stereo[:, 1] = wave



        try:

            self.sounds['whoosh'] = pygame.sndarray.make_sound(stereo)

        except:

            pass



        # Digital noise (for searching)

        duration = 0.5

        samples = int(sample_rate * duration)

        wave = np.random.randint(-16384, 16384, samples, dtype=np.int16)

        # Apply envelope

        envelope = np.array([min(x / (samples * 0.1), 1 - x / samples) for x in range(samples)])

        wave = (wave * envelope).astype(np.int16)

        stereo = np.zeros((samples, 2), dtype=np.int16)

        stereo[:, 0] = wave

        stereo[:, 1] = wave



        try:

            self.sounds['digital_noise'] = pygame.sndarray.make_sound(stereo)

        except:

            pass



    def _load_external_sounds(self):

        if not self.enabled:

            return

        try:

            base_dir = os.path.dirname(__file__)

            sound_dir = os.path.join(base_dir, "monica_ai", "resources", "sounds", "scifi")

            mapping = {

                "globe_turn": "globe_turn.mp3",

                "hologram_ambient": "hologramsound_one.mp3",

                "location_pulse": "globelocation_pulsating_currentlocation.mp3",

            }

            for key, filename in mapping.items():

                path = os.path.join(sound_dir, filename)

                if os.path.exists(path):

                    try:

                        self.sounds[key] = pygame.mixer.Sound(path)

                    except Exception:

                        continue

        except Exception:

            pass



    def play(self, sound_name: str):

        """Play a sound effect."""

        if self.enabled and sound_name in self.sounds:

            try:

                self.sounds[sound_name].play()

            except:

                pass



    def start_hologram_ambient(self, volume: float = 0.15):

        if not self.enabled or self.hologram_ambient_active:

            return

        sound = self.sounds.get("hologram_ambient")

        if sound is None:

            return

        try:

            channel = sound.play(loops=-1)

            if channel:

                channel.set_volume(volume)

                self.channels["hologram_ambient"] = channel

                self.hologram_ambient_active = True

        except Exception:

            pass



    def stop_hologram_ambient(self):

        if not self.enabled:

            return

        channel = self.channels.get("hologram_ambient")

        if channel:

            try:

                channel.stop()

            except Exception:

                pass

        self.channels.pop("hologram_ambient", None)

        self.hologram_ambient_active = False



    def start_location_pulse(self, volume: float = 0.2):

        if not self.enabled or self.location_pulse_active:

            return

        sound = self.sounds.get("location_pulse")

        if sound is None:

            return

        try:

            channel = sound.play(loops=-1)

            if channel:

                channel.set_volume(volume)

                self.channels["location_pulse"] = channel

                self.location_pulse_active = True

        except Exception:

            pass



    def stop_location_pulse(self):

        if not self.enabled:

            return

        channel = self.channels.get("location_pulse")

        if channel:

            try:

                channel.stop()

            except Exception:

                pass

        self.channels.pop("location_pulse", None)

        self.location_pulse_active = False



    def stop_all(self):

        if not self.enabled:

            return

        for ch in list(self.channels.values()):

            try:

                ch.stop()

            except Exception:

                pass

        self.channels.clear()

        try:

            pygame.mixer.stop()

        except Exception:

            pass





class GoogleMapsIntegration:

    """

    Location data integration using FREE local APIs only.

    PRIVACY: No Google API keys. Uses OpenStreetMap Nominatim (free, no tracking).

    """



    def __init__(self):

        # PRIVACY: NO Google API key - all geocoding via free OpenStreetMap

        self.api_key = None  # Disabled for privacy - see _geocode_with_nominatim()

        self.geocoding_cache = {}



    def geocode_location(self, location_name: str) -> Optional[Dict]:

        """

        Convert location name to coordinates using Google Maps Geocoding API.



        Args:

            location_name: Name of location (e.g., "13th Judicial Circuit, Tampa")



        Returns:

            Dictionary with latitude, longitude, formatted_address

        """

        # Check cache

        if location_name in self.geocoding_cache:

            return self.geocoding_cache[location_name]



        # PRIVACY: Always use free OpenStreetMap Nominatim - no Google APIs

        return self._geocode_with_nominatim(location_name)



    def _geocode_with_nominatim(self, location_name: str) -> Optional[Dict]:

        """Fallback geocoding using free OpenStreetMap Nominatim API."""

        try:

            url = "https://nominatim.openstreetmap.org/search"

            params = {

                'q': location_name,

                'format': 'json',

                'limit': 1

            }

            headers = {'User-Agent': 'Monica-AI/1.0'}



            response = requests.get(url, params=params, headers=headers, timeout=10)

            data = response.json()



            if data:

                result = data[0]

                location_data = {

                    'latitude': float(result['lat']),

                    'longitude': float(result['lon']),

                    'formatted_address': result['display_name'],

                    'place_id': result.get('place_id')

                }



                self.geocoding_cache[location_name] = location_data

                return location_data



        except Exception as e:

            print(f"Nominatim geocoding error: {e}")



        return None





class WebcamFinder:

    """

    Finds public webcams near locations.

    """



    def __init__(self):

        self.webcam_database = self._load_webcam_database()



    def _load_webcam_database(self) -> Dict:

        """Load database of known public webcams."""

        # Curated list of public webcams by location

        return {

            "tampa": [

                {"name": "Tampa Riverwalk", "url": "https://www.earthcam.com/usa/florida/tampa/"},

                {"name": "Tampa Bay", "url": "https://www.youtube.com/watch?v=example"}

            ],

            "paris": [

                {"name": "Eiffel Tower", "url": "https://www.earthcam.com/world/france/paris/"},

                {"name": "Champs-Élysées", "url": "https://www.skylinewebcams.com/en/webcam/france/ile-de-france/paris/champs-elysees.html"}

            ],

            "new_york": [

                {"name": "Times Square", "url": "https://www.earthcam.com/usa/newyork/timessquare/"},

                {"name": "Brooklyn Bridge", "url": "https://www.earthcam.com/usa/newyork/brooklynbridge/"}

            ]

        }



    def find_webcams(self, location_name: str, latitude: float = None, longitude: float = None) -> List[Dict]:

        """

        Find public webcams near a location.



        Args:

            location_name: Name of location

            latitude: GPS latitude (optional, for nearby search)

            longitude: GPS longitude (optional)



        Returns:

            List of webcam dictionaries with name and URL

        """

        location_key = location_name.lower().replace(' ', '_')



        # Check database

        if location_key in self.webcam_database:

            return self.webcam_database[location_key]



        # Try partial match

        for key, webcams in self.webcam_database.items():

            if key in location_key or location_key in key:

                return webcams



        # Try external API (Windy Webcams API - free)

        if latitude and longitude:

            return self._search_windy_webcams(latitude, longitude)



        return []



    def _search_windy_webcams(self, latitude: float, longitude: float, radius: int = 50) -> List[Dict]:

        """Search Windy Webcams API for nearby cams."""

        try:

            url = f"https://api.windy.com/api/webcams/v2/list/nearby={latitude},{longitude},{radius}"

            headers = {'x-windy-api-key': os.environ.get('WINDY_API_KEY', '')}



            if not headers['x-windy-api-key']:

                return []



            response = requests.get(url, headers=headers, timeout=10)

            data = response.json()



            webcams = []

            for cam in data.get('result', {}).get('webcams', []):

                webcams.append({

                    'name': cam.get('title', 'Webcam'),

                    'url': cam.get('player', {}).get('day', {}).get('embed', ''),

                    'preview': cam.get('image', {}).get('current', {}).get('preview', '')

                })



            return webcams



        except Exception as e:

            print(f"Windy webcam search error: {e}")

            return []





class HolographicGlobe:

    """

    Interactive 3D holographic globe with location markers and zoom.

    """



    def __init__(self, width=1280, height=720):

        self.width = width

        self.height = height



        # Globe properties

        self.globe_center = (width // 2, height // 2)

        self.globe_radius = min(width, height) // 3

        self.zoom_level = 1.0

        self.rotation_x = 0.0

        self.rotation_y = 0.0



        # Locations

        self.locations: List[Location] = []

        self.selected_location: Optional[Location] = None



        # Visual effects

        self.glow_pulse = 0.0

        self.marker_animations = {}



        # Integrations

        self.maps = GoogleMapsIntegration()

        self.webcam_finder = WebcamFinder()

        self.sound_effects = SciFiSoundEffects()



        # State

        self.mode = "globe"  # globe, map, location_detail, webcam_view

        self.is_searching = False



        self.current_location = None

        self.current_location_marker: Optional[Location] = None

        self.last_rotate_sound_time = 0.0

        self.rotate_sound_interval = 1.5



        if HAS_LOCATION_SERVICES:

            try:

                services = get_location_services()

                loc = services.get_current_location()

                if loc:

                    self.current_location = loc

                    self._add_current_location(loc)

            except Exception:

                pass



        self.sound_effects.start_hologram_ambient()

        if self.current_location is not None:

            self.sound_effects.start_location_pulse()



    def add_location(self, name: str, latitude: float = None, longitude: float = None):

        """

        Add a location to the globe.



        Args:

            name: Location name

            latitude: GPS latitude (if None, will geocode)

            longitude: GPS longitude

        """

        # Geocode if coords not provided

        if latitude is None or longitude is None:

            geocode_result = self.maps.geocode_location(name)

            if geocode_result:

                latitude = geocode_result['latitude']

                longitude = geocode_result['longitude']

                name = geocode_result['formatted_address']

            else:

                print(f"Could not find location: {name}")

                return



        # Find webcams

        webcams = self.webcam_finder.find_webcams(name, latitude, longitude)



        # Create location

        location = Location(

            name=name,

            latitude=latitude,

            longitude=longitude,

            category="user_added",

            webcam_urls=[w['url'] for w in webcams]

        )



        self.locations.append(location)

        self.sound_effects.play('beep')



        print(f"[OK] Added location: {name}")

        print(f"   Coordinates: ({latitude}, {longitude})")

        if webcams:

            print(f"   Found {len(webcams)} webcams")



    def _lat_lon_to_3d(self, latitude: float, longitude: float) -> Tuple[float, float, float]:

        """Convert lat/lon to 3D globe coordinates."""

        lat_rad = math.radians(latitude)

        lon_rad = math.radians(longitude)



        x = math.cos(lat_rad) * math.cos(lon_rad)

        y = math.cos(lat_rad) * math.sin(lon_rad)

        z = math.sin(lat_rad)



        return (x, y, z)



    def _project_3d_to_2d(self, x: float, y: float, z: float) -> Tuple[int, int]:

        """Project 3D globe coordinates to 2D screen with rotation."""

        # Apply rotation

        cos_rx = math.cos(self.rotation_x)

        sin_rx = math.sin(self.rotation_x)

        cos_ry = math.cos(self.rotation_y)

        sin_ry = math.sin(self.rotation_y)



        # Rotate around Y axis

        x_rot = x * cos_ry - z * sin_ry

        z_rot = x * sin_ry + z * cos_ry



        # Rotate around X axis

        y_rot = y * cos_rx - z_rot * sin_rx

        z_final = y * sin_rx + z_rot * cos_rx



        # Scale by zoom and radius

        radius = self.globe_radius * self.zoom_level



        # Project to 2D

        screen_x = int(self.globe_center[0] + x_rot * radius)

        screen_y = int(self.globe_center[1] - y_rot * radius)



        return (screen_x, screen_y, z_final)



    def _add_current_location(self, loc) -> None:

        try:

            location = Location(

                name=f"Current location",

                latitude=loc.latitude,

                longitude=loc.longitude,

                category="current_location",

                marker_color=(0, 255, 255),

            )

            self.locations.append(location)

            self.current_location_marker = location

        except Exception:

            pass



    def render(self, frame):

        """

        Render the holographic globe.



        Args:

            frame: OpenCV image to render onto



        Returns:

            Modified frame

        """

        overlay = np.zeros_like(frame)



        if self.mode == "globe":

            self.rotation_y += 0.002

            now = time.time()

            if now - self.last_rotate_sound_time >= self.rotate_sound_interval:

                self.sound_effects.play("globe_turn")

                self.last_rotate_sound_time = now

            self._draw_globe_wireframe(overlay)

            self._draw_location_markers(overlay)

        elif self.mode == "map":

            self._draw_map_view(overlay)

            self._draw_location_markers_map(overlay)



        if self.selected_location:

            self._draw_location_info(overlay)



        if self.is_searching:

            self._draw_searching_effect(overlay)



        glow = cv2.GaussianBlur(overlay, (0, 0), sigmaX=18, sigmaY=18)

        hologram = cv2.addWeighted(glow, 0.6, overlay, 1.0, 0)

        frame = cv2.addWeighted(hologram, 0.9, frame, 0.1, 0)



        return frame



    def _draw_globe_wireframe(self, frame):

        """Draw 3D wireframe globe."""

        color = (255, 255, 200)



        # Draw latitude lines

        for lat in range(-80, 90, 20):

            points = []

            for lon in range(0, 360, 10):

                x, y, z = self._lat_lon_to_3d(lat, lon)

                screen_x, screen_y, z_depth = self._project_3d_to_2d(x, y, z)



                if z_depth > 0:  # Only draw front-facing

                    points.append((screen_x, screen_y))



            if len(points) > 1:

                for i in range(len(points) - 1):

                    cv2.line(frame, points[i], points[i + 1], color, 1)



        # Draw longitude lines

        for lon in range(0, 360, 30):

            points = []

            for lat in range(-90, 91, 10):

                x, y, z = self._lat_lon_to_3d(lat, lon)

                screen_x, screen_y, z_depth = self._project_3d_to_2d(x, y, z)



                if z_depth > 0:

                    points.append((screen_x, screen_y))



            if len(points) > 1:

                for i in range(len(points) - 1):

                    cv2.line(frame, points[i], points[i + 1], color, 1)



    def _draw_location_markers(self, frame):

        """Draw glowing markers for locations."""

        self.glow_pulse += 0.1



        for location in self.locations:

            x, y, z = self._lat_lon_to_3d(location.latitude, location.longitude)

            screen_x, screen_y, z_depth = self._project_3d_to_2d(x, y, z)



            if z_depth > 0:  # Front-facing

                pulse = abs(math.sin(self.glow_pulse))

                radius = int(6 + pulse * 4)

                is_current = location is self.current_location_marker or location.category == "current_location"

                color = (0, 255, 255) if is_current else location.marker_color

                if is_current and pulse > 0.5:

                    cv2.circle(frame, (screen_x, screen_y), radius + 10, color, 2)

                cv2.circle(frame, (screen_x, screen_y), radius + 4, color, 2)

                cv2.circle(frame, (screen_x, screen_y), radius, color, -1)

                cv2.putText(frame, location.name[:20], (screen_x + 10, screen_y),

                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)



    def _get_map_rect(self) -> Tuple[int, int, int, int]:

        map_w = int(self.width * 0.8)

        map_h = int(self.height * 0.45)

        map_x = (self.width - map_w) // 2

        map_y = self.height // 2 - map_h // 2

        return map_x, map_y, map_w, map_h



    def _draw_map_view(self, frame):

        map_x, map_y, map_w, map_h = self._get_map_rect()

        color = (255, 255, 200)

        cv2.rectangle(frame, (map_x, map_y), (map_x + map_w, map_y + map_h), color, 1)

        rows = 12

        cols = 24

        for i in range(1, rows):

            y = map_y + int(map_h * i / rows)

            cv2.line(frame, (map_x, y), (map_x + map_w, y), color, 1)

        for j in range(1, cols):

            x = map_x + int(map_w * j / cols)

            cv2.line(frame, (x, map_y), (x, map_y + map_h), color, 1)

        base_offset = 40

        base_x = map_x + 40

        base_y = map_y + map_h + base_offset

        base_w = map_w - 80

        base_h = 20

        cv2.rectangle(frame, (base_x, base_y), (base_x + base_w, base_y + base_h), color, 1)

        cv2.line(frame, (map_x, map_y + map_h), (base_x, base_y), color, 1)

        cv2.line(frame, (map_x + map_w, map_y + map_h), (base_x + base_w, base_y), color, 1)



    def _lat_lon_to_map_xy(self, latitude: float, longitude: float) -> Tuple[int, int]:

        map_x, map_y, map_w, map_h = self._get_map_rect()

        x_norm = (longitude + 180.0) / 360.0

        y_norm = (90.0 - latitude) / 180.0

        x = map_x + int(x_norm * map_w)

        y = map_y + int(y_norm * map_h)

        return x, y



    def _draw_location_markers_map(self, frame):

        self.glow_pulse += 0.1

        for location in self.locations:

            x, y = self._lat_lon_to_map_xy(location.latitude, location.longitude)

            pulse = abs(math.sin(self.glow_pulse))

            radius = int(5 + pulse * 4)

            is_current = location is self.current_location_marker or location.category == "current_location"

            color = (0, 255, 255) if is_current else location.marker_color

            if is_current and pulse > 0.5:

                cv2.circle(frame, (x, y), radius + 10, color, 2)

            cv2.circle(frame, (x, y), radius + 3, color, 2)

            cv2.circle(frame, (x, y), radius, color, -1)



    def _draw_location_info(self, frame):

        """Draw detailed info panel for selected location."""

        # Info panel (top-right)

        panel_x, panel_y = self.width - 350, 50

        panel_w, panel_h = 330, 200



        # Draw panel background

        cv2.rectangle(frame, (panel_x, panel_y), (panel_x + panel_w, panel_y + panel_h),

                     (20, 20, 20), -1)

        cv2.rectangle(frame, (panel_x, panel_y), (panel_x + panel_w, panel_y + panel_h),

                     (0, 255, 255), 2)



        # Title

        cv2.putText(frame, "LOCATION DATA", (panel_x + 10, panel_y + 25),

                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)



        # Info

        y_offset = 55

        info_lines = [

            f"Name: {self.selected_location.name}",

            f"Lat: {self.selected_location.latitude:.4f}",

            f"Lon: {self.selected_location.longitude:.4f}",

            f"Category: {self.selected_location.category}",

            f"Webcams: {len(self.selected_location.webcam_urls or [])}"

        ]



        for line in info_lines:

            cv2.putText(frame, line, (panel_x + 10, panel_y + y_offset),

                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)

            y_offset += 25



    def _draw_searching_effect(self, frame):

        """Draw animated searching/scanning effect."""

        # Scanning line

        scan_y = int((math.sin(self.glow_pulse * 2) + 1) * self.height / 2)

        cv2.line(frame, (0, scan_y), (self.width, scan_y), (0, 255, 255), 2)



        # "SEARCHING..." text

        text = "SEARCHING LOCATION..."

        cv2.putText(frame, text, (self.width // 2 - 150, 50),

                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)



    def zoom_in(self):

        """Zoom into globe."""

        self.zoom_level = min(3.0, self.zoom_level + 0.2)

        self.sound_effects.play('whoosh')



    def zoom_out(self):

        """Zoom out of globe."""

        self.zoom_level = max(0.5, self.zoom_level - 0.2)

        self.sound_effects.play('whoosh')



    def rotate(self, dx: float, dy: float):

        """Rotate globe."""

        self.rotation_x += dy * 0.01

        self.rotation_y += dx * 0.01

        now = time.time()

        if now - self.last_rotate_sound_time >= self.rotate_sound_interval:

            self.sound_effects.play("globe_turn")

            self.last_rotate_sound_time = now



    def search_location(self, query: str):

        """

        Search for location by natural language query.



        Args:

            query: Natural language query (e.g., "Show me Paris", "13th Judicial Circuit Tampa")

        """

        self.is_searching = True

        self.sound_effects.play('digital_noise')



        # Extract location name from query

        # Simple extraction - can be enhanced with NLP

        query_lower = query.lower()



        # Remove common phrases

        for phrase in ["show me", "where is", "find", "locate", "zoom to"]:

            query_lower = query_lower.replace(phrase, "")



        location_name = query_lower.strip()



        # Add location

        self.add_location(location_name)



        self.is_searching = False



        # Select the new location

        if self.locations:

            self.selected_location = self.locations[-1]





# Test/demo function

def demo_holographic_globe():

    """Demo the holographic globe system."""

    print("MONICA HOLOGRAPHIC GLOBE - Demo")

    print("=" * 70)



    globe = HolographicGlobe(width=1280, height=720)



    # Add some locations

    print("\nAdding locations...")

    globe.add_location("Paris, France")

    globe.add_location("13th Judicial Circuit, Tampa, Florida")

    globe.add_location("New York City")



    print("\nStarting visualization...")

    print("\nControls:")

    print("  Mouse drag - Rotate globe")

    print("  + / - - Zoom in/out")

    print("  1-3 - Select location")

    print("  S - Search for location")

    print("  Q - Quit")



    cv2.namedWindow('Monica Holographic Globe', cv2.WINDOW_NORMAL)



    # Mouse control

    drag_start = None

    dragging = False



    def mouse_callback(event, x, y, flags, param):

        nonlocal drag_start, dragging



        if event == cv2.EVENT_LBUTTONDOWN:

            drag_start = (x, y)

            dragging = True

        elif event == cv2.EVENT_LBUTTONUP:

            dragging = False

        elif event == cv2.EVENT_MOUSEMOVE and dragging and drag_start:

            dx = x - drag_start[0]

            dy = y - drag_start[1]

            globe.rotate(dx, dy)

            drag_start = (x, y)



    cv2.setMouseCallback('Monica Holographic Globe', mouse_callback)



    while True:

        # Create frame

        frame = np.zeros((720, 1280, 3), dtype=np.uint8)



        # Render globe

        frame = globe.render(frame)



        # Display

        cv2.imshow('Monica Holographic Globe', frame)



        # Handle input

        key = cv2.waitKey(16) & 0xFF



        if key == ord('q'):

            break

        elif key == ord('+') or key == ord('='):

            globe.zoom_in()

        elif key == ord('-') or key == ord('_'):

            globe.zoom_out()

        elif key == ord('1') and len(globe.locations) > 0:

            globe.selected_location = globe.locations[0]

        elif key == ord('2') and len(globe.locations) > 1:

            globe.selected_location = globe.locations[1]

        elif key == ord('3') and len(globe.locations) > 2:

            globe.selected_location = globe.locations[2]

        elif key == ord('s'):

            location_query = input("\nEnter location: ")

            globe.search_location(location_query)



    cv2.destroyAllWindows()





if __name__ == "__main__":

    import os  # Import needed for environment variables

    demo_holographic_globe()

