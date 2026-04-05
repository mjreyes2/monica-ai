"""
Monica AR Hologram System
Renders 3D holograms (globe, windows, etc.) directly into the camera feed as AR overlays.
The holograms appear "next to" the user in the camera view.
"""

import cv2
import numpy as np
import math
import time
import threading
from typing import Optional, Dict, List, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import requests
import random
from datetime import datetime

# Try to import pygame for sound effects
HAS_PYGAME = False
try:
    import pygame
    pygame.mixer.init()
    HAS_PYGAME = True
except ImportError:
    pass

# Try to import webcam network
HAS_WEBCAM_NETWORK = False
try:
    from monica_global_webcams import get_webcam_network
    HAS_WEBCAM_NETWORK = True
except ImportError:
    pass

# Try to import Earth data system
HAS_EARTH_DATA = False
try:
    from monica_earth_data import get_earth_data
    HAS_EARTH_DATA = True
except ImportError:
    pass

# Try to import Google Maps globe
HAS_GOOGLE_MAPS = False
try:
    from monica_google_maps_globe import get_google_maps_globe
    HAS_GOOGLE_MAPS = True
except ImportError:
    pass

# Try to import Free Maps system (preferred over Google)
HAS_FREE_MAPS = False
try:
    from monica_free_maps import get_free_maps
    HAS_FREE_MAPS = True
except ImportError:
    pass

# Try to import Realistic Globe renderer
HAS_REALISTIC_GLOBE = False
try:
    from monica_realistic_globe import get_realistic_globe, RealisticGlobeRenderer
    HAS_REALISTIC_GLOBE = True
except ImportError:
    pass

# Try to import Accurate Satellite Data system
HAS_SATELLITE_DATA = False
try:
    from monica_satellite_data import get_geocoder, get_gibs_client, GlobeCoordinateSystem
    HAS_SATELLITE_DATA = True
    print("✅ Satellite Data System loaded (accurate geocoding)")
except ImportError as e:
    print(f"⚠️ Satellite Data System not available: {e}")

# Try to import Research System
HAS_RESEARCH_SYSTEM = False
try:
    from monica_research_system import get_research_window, get_language_support
    HAS_RESEARCH_SYSTEM = True
    print("✅ Research System loaded (scholarly search, multi-language)")
except ImportError as e:
    print(f"⚠️ Research System not available: {e}")

# Try to import Plasma Orb Window for Monica's visual presence (separate green screen window)
HAS_ORB_WINDOW = False
try:
    from monica_orb_window import get_orb_window, MonicaOrbWindow
    HAS_ORB_WINDOW = True
    print("✅ Orb Window loaded (green screen for OBS)")
except ImportError as e:
    print(f"⚠️ Orb Window not available: {e}")

# Try to import Globe Window (separate green screen window)
HAS_GLOBE_WINDOW = False
try:
    from monica_globe_window import get_globe_window, MonicaGlobeWindow
    HAS_GLOBE_WINDOW = True
    print("✅ Globe Window loaded (green screen for OBS)")
except ImportError as e:
    print(f"⚠️ Globe Window not available: {e}")

# Try to import Keyboard Window (separate green screen window)
HAS_KEYBOARD_WINDOW = False
try:
    from monica_keyboard_window import get_keyboard_window, MonicaKeyboardWindow
    HAS_KEYBOARD_WINDOW = True
    print("✅ Keyboard Window loaded (green screen for OBS)")
except ImportError as e:
    print(f"⚠️ Keyboard Window not available: {e}")

# Try to import Dial Window (separate green screen window)
HAS_DIAL_WINDOW = False
try:
    from monica_dial_window import get_dial_window, MonicaDialWindow
    HAS_DIAL_WINDOW = True
    print("✅ Dial Window loaded (green screen for OBS)")
except ImportError as e:
    print(f"⚠️ Dial Window not available: {e}")

class HologramType(Enum):
    """Types of holograms that can be displayed."""
    GLOBE = "globe"
    WEBCAM_WINDOW = "webcam_window"
    INFO_PANEL = "info_panel"
    RESEARCH_WINDOW = "research_window"
    NONE = "none"


@dataclass
class GlobeState:
    """State of the holographic globe."""
    rotation_x: float = 0.0
    rotation_y: float = 0.0
    zoom: float = 1.0
    target_lat: float = 0.0
    target_lng: float = 0.0
    highlighted_city: Optional[str] = None
    is_zooming: bool = False
    zoom_progress: float = 0.0
    # Materialization effect (Fortnite-style)
    is_materializing: bool = False
    materialize_progress: float = 0.0  # 0.0 to 1.0
    materialize_start_time: float = 0.0
    # User location
    user_lat: float = 40.7128  # Default NYC
    user_lng: float = -74.006
    user_location_name: str = "Your Location"
    # Day/night visualization
    show_daylight: bool = False
    # Beeping marker
    beep_time: float = 0.0
    # Overlay modes
    show_weather: bool = False
    show_lightning: bool = False
    show_conflicts: bool = False
    show_disasters: bool = False
    show_military: bool = False
    # Highlighted region
    highlighted_region: Optional[str] = None
    highlighted_region_bounds: Optional[List] = None
    # SMOOTH ROTATION - target rotation for animation
    target_rotation_x: float = 0.0
    target_rotation_y: float = 0.0
    is_rotating_to_target: bool = False
    rotation_speed: float = 0.05  # How fast to rotate (0-1, higher = faster)


@dataclass
class WebcamWindowState:
    """State of the webcam feed window."""
    current_feed_url: Optional[str] = None
    current_feed_name: str = ""
    feed_list: List[Dict] = None
    current_index: int = 0
    frame: Optional[np.ndarray] = None
    is_loading: bool = False
    
    def __post_init__(self):
        if self.feed_list is None:
            self.feed_list = []


@dataclass
class HandGestureState:
    """State for hand gesture control of the globe."""
    is_grabbing: bool = False
    grab_start_x: float = 0.0
    grab_start_y: float = 0.0
    last_hand_x: float = 0.0
    last_hand_y: float = 0.0
    rotation_velocity_x: float = 0.0
    rotation_velocity_y: float = 0.0
    last_update_time: float = 0.0


class MonicaARHologramSystem:
    """
    AR Hologram System that renders 3D content into the camera feed.
    Supports globe, webcam windows, and info panels.
    
    PERFORMANCE OPTIMIZATIONS:
    - Pre-computed globe geometry (cached NumPy arrays)
    - Frame skipping (render every N frames)
    - Vectorized NumPy operations (no Python loops for transforms)
    - Cached overlay buffer (reuse between frames)
    - Lazy rendering (skip when no hologram active)
    - Background thread for webcam loading
    """
    
    def __init__(self):
        self.active_hologram = HologramType.NONE
        self.globe_state = GlobeState()
        self.webcam_state = WebcamWindowState()
        
        # Position settings (where hologram appears in frame)
        self.hologram_position = "left"  # left, right, center
        self.hologram_scale = 0.45  # 45% of frame width (larger globe)
        self.globe_transparency = 0.85  # Globe transparency (0=invisible, 1=solid)
        
        # Fine-grained position control (offset from base position)
        self.hologram_position_offset_x = 0  # Horizontal offset in pixels (positive = right)
        self.hologram_position_offset_y = 0  # Vertical offset in pixels (positive = down)
        self.hologram_rotation = 0  # Rotation angle in degrees (for tilt adjustment)
        self.position_step = 20  # Pixels to move per command

        self.last_face_location = None
        
        # ===== PERFORMANCE SETTINGS =====
        # OPTIMIZED: Render AR overlay on separate schedule from video
        # This prevents AR rendering from blocking the video feed
        self.render_every_n_frames = 2  # Render AR every 2 frames (balanced)
        self.frame_counter = 0
        self.cached_overlay = None  # Cache last rendered overlay
        self.last_frame_shape = None  # Track frame size changes
        self.use_low_res_rendering = False  # Keep full resolution for quality
        self.render_scale = 1.0  # Full resolution
        
        # Async rendering state
        self._render_lock = threading.Lock()
        self._pending_frame = None
        
        # Globe rendering - PRE-COMPUTED GEOMETRY
        self.globe_texture = None
        self.globe_points = []  # List of (type, points_array)
        self.globe_points_np = None  # NumPy array for vectorized transforms
        self.continent_polygons = []  # Continent outlines for filled look
        self.continent_points_np = None  # NumPy array for continent vertices
        self.earth_radius = 100
        self._generate_globe_points()
        self._generate_continent_outlines()  # Add continent shapes
        self._precompute_globe_geometry()  # Vectorized geometry
        
        # City database with coordinates
        self.cities = self._load_cities()
        
        # Pre-compute city 3D positions
        self.city_positions_3d = {}
        for name, city in self.cities.items():
            self.city_positions_3d[name] = self._lat_lng_to_3d(city["lat"], city["lng"])
        
        # Animation
        self.animation_time = 0
        self.last_update = time.time()
        
        # Webcam feed thread
        self.webcam_thread = None
        self.webcam_stop_event = threading.Event()
        
        # Colors for holographic effect (pre-computed as numpy arrays for speed)
        self.hologram_color = (0, 255, 255)  # Cyan
        self.highlight_color = (0, 255, 255)  # Yellow (BGR)
        self.glow_color = (255, 200, 100)  # Light blue glow
        
        # Materialization effect settings
        self.materialize_duration = 2.0  # seconds for full materialization
        self.pixel_particles = []  # Blue pixel particles for effect
        
        # Sound effects
        self.sounds_loaded = False
        # Core sound handles
        self.materialize_sound = None
        self.beep_sound = None
        self.alarm_sound = None
        # Globe-specific external sounds (from Monica's sci-fi library)
        self.hologram_ambient_sound = None
        self.location_pulse_sound = None
        self.globe_turn_sound = None
        # Runtime sound channels/state
        self.hologram_ambient_channel = None
        self.location_pulse_channel = None
        self.last_globe_turn_sound = 0.0
        self.globe_turn_interval = 1.5  # seconds between turn sounds
        self._load_sounds()
        
        # Get user's actual location (detect on first use)
        # Location detection moved to lazy initialization to avoid startup errors
        
        # Earth data system for real-time overlays
        self.earth_data = None
        if HAS_EARTH_DATA:
            try:
                self.earth_data = get_earth_data()
                print("  [EARTH] Real-time Earth data loaded")
            except Exception as e:
                print(f"  [EARTH] Could not load Earth data: {e}")
        
        # Lightning flash animation
        self.lightning_flashes = []  # List of (lat, lng, time, intensity)
        
        # Hand gesture control state
        self.hand_gesture = HandGestureState()
        self.hand_history = []  # Track hand positions for swipe detection
        self.max_hand_history = 10
        
        # Globe control panel state
        self.show_control_panel = True  # Show control buttons
        self.control_buttons = self._create_control_buttons()
        
        # Free Maps integration (preferred - no API key needed!)
        self.free_maps = None
        self.google_maps = None
        self.use_satellite_texture = False  # Toggle for satellite imagery
        self.city_view_active = False
        self.city_view_location = None
        self.city_view_image = None
        self.show_webcam_markers = False
        
        # Try free maps first (ESRI satellite is free!)
        if HAS_FREE_MAPS:
            try:
                self.free_maps = get_free_maps()
                print("  [MAPS] Free Maps system loaded (ESRI satellite - no key needed!)")
            except Exception as e:
                print(f"  [MAPS] Could not load Free Maps: {e}")
        
        # Google Maps as backup
        if HAS_GOOGLE_MAPS and not self.free_maps:
            try:
                self.google_maps = get_google_maps_globe()
                print("  [MAPS] Google Maps globe loaded (backup)")
            except Exception as e:
                print(f"  [MAPS] Could not load Google Maps: {e}")
        
        # Realistic globe renderer (satellite imagery)
        self.realistic_globe = None
        self.use_realistic_globe = False  # Use holographic wireframe by default
        if HAS_REALISTIC_GLOBE:
            try:
                self.realistic_globe = get_realistic_globe()
                print("  [GLOBE] Realistic satellite globe loaded")
            except Exception as e:
                print(f"  [GLOBE] Could not load realistic globe: {e}")

        self.monica_in_frame_target = False
        self.monica_in_frame_alpha = 0.0
        self.monica_in_frame_intensity = 0.0
        
        # Performance: Skip control panel rendering (was causing yellow box)
        self.show_control_panel = False  # Disable for now - use voice commands
        
        # Holographic keyboard state
        self.show_holographic_keyboard = False  # Hidden by default, say "show keyboard" to enable
        self.keyboard_keys = self._create_keyboard_layout()
        self.keyboard_typed_text = ""
        self.keyboard_active_key = None
        self.keyboard_last_press_time = 0
        self.keyboard_cooldown = 0.3  # seconds between key presses
        self.keyboard_offset_x = 0  # For moving keyboard
        self.keyboard_offset_y = 0
        self.keyboard_scale = 1.0  # For enlarging keyboard
        self.keyboard_highlight_time = 0  # For key highlight animation
        
        # Monica's Orb Window (separate green screen window for OBS)
        self.orb_window = None
        if HAS_ORB_WINDOW:
            try:
                self.orb_window = get_orb_window()
                # Don't auto-start - wait for GUI button
                print("  [ORB] Monica's Orb Window loaded (use GUI button to show)")
            except Exception as e:
                print(f"  [ORB] Could not load Orb Window: {e}")
        
        # Globe Window (separate green screen window for OBS)
        self.globe_window = None
        if HAS_GLOBE_WINDOW:
            try:
                self.globe_window = get_globe_window()
                # Don't auto-start - wait for GUI button
                print("  [GLOBE] Globe Window loaded (use GUI button to show)")
            except Exception as e:
                print(f"  [GLOBE] Could not load Globe Window: {e}")
        
        # Keyboard Window (separate green screen window for OBS)
        self.keyboard_window = None
        if HAS_KEYBOARD_WINDOW:
            try:
                self.keyboard_window = get_keyboard_window()
                # Don't auto-start - wait for GUI button
                print("  [KEYBOARD] Keyboard Window loaded (use GUI button to show)")
            except Exception as e:
                print(f"  [KEYBOARD] Could not load Keyboard Window: {e}")
        
        # Dial Window (separate green screen window for OBS)
        self.dial_window = None
        if HAS_DIAL_WINDOW:
            try:
                self.dial_window = get_dial_window()
                # Don't auto-start - wait for GUI button
                print("  [DIAL] Dial Window loaded (use GUI button to show)")
            except Exception as e:
                print(f"  [DIAL] Could not load Dial Window: {e}")
        
        print("✅ AR Hologram System initialized (optimized)")
    
    def _load_cities(self) -> Dict[str, Dict]:
        """Load city database with coordinates."""
        return {
            "new york": {"lat": 40.7128, "lng": -74.006, "name": "New York City", "country": "USA"},
            "london": {"lat": 51.5072, "lng": -0.1276, "name": "London", "country": "UK"},
            "tokyo": {"lat": 35.6762, "lng": 139.6503, "name": "Tokyo", "country": "Japan"},
            "paris": {"lat": 48.8566, "lng": 2.3522, "name": "Paris", "country": "France"},
            "sydney": {"lat": -33.8688, "lng": 151.2093, "name": "Sydney", "country": "Australia"},
            "dubai": {"lat": 25.2048, "lng": 55.2708, "name": "Dubai", "country": "UAE"},
            "singapore": {"lat": 1.3521, "lng": 103.8198, "name": "Singapore", "country": "Singapore"},
            "hong kong": {"lat": 22.3193, "lng": 114.1694, "name": "Hong Kong", "country": "China"},
            "los angeles": {"lat": 34.0522, "lng": -118.2437, "name": "Los Angeles", "country": "USA"},
            "chicago": {"lat": 41.8781, "lng": -87.6298, "name": "Chicago", "country": "USA"},
            "miami": {"lat": 25.7617, "lng": -80.1918, "name": "Miami", "country": "USA"},
            "san francisco": {"lat": 37.7749, "lng": -122.4194, "name": "San Francisco", "country": "USA"},
            "seattle": {"lat": 47.6062, "lng": -122.3321, "name": "Seattle", "country": "USA"},
            "boston": {"lat": 42.3601, "lng": -71.0589, "name": "Boston", "country": "USA"},
            "washington": {"lat": 38.9072, "lng": -77.0369, "name": "Washington D.C.", "country": "USA"},
            "toronto": {"lat": 43.6532, "lng": -79.3832, "name": "Toronto", "country": "Canada"},
            "vancouver": {"lat": 49.2827, "lng": -123.1207, "name": "Vancouver", "country": "Canada"},
            "mexico city": {"lat": 19.4326, "lng": -99.1332, "name": "Mexico City", "country": "Mexico"},
            "sao paulo": {"lat": -23.5505, "lng": -46.6333, "name": "São Paulo", "country": "Brazil"},
            "rio de janeiro": {"lat": -22.9068, "lng": -43.1729, "name": "Rio de Janeiro", "country": "Brazil"},
            "buenos aires": {"lat": -34.6037, "lng": -58.3816, "name": "Buenos Aires", "country": "Argentina"},
            "berlin": {"lat": 52.52, "lng": 13.405, "name": "Berlin", "country": "Germany"},
            "rome": {"lat": 41.9028, "lng": 12.4964, "name": "Rome", "country": "Italy"},
            "madrid": {"lat": 40.4168, "lng": -3.7038, "name": "Madrid", "country": "Spain"},
            "barcelona": {"lat": 41.3851, "lng": 2.1734, "name": "Barcelona", "country": "Spain"},
            "amsterdam": {"lat": 52.3676, "lng": 4.9041, "name": "Amsterdam", "country": "Netherlands"},
            "moscow": {"lat": 55.7558, "lng": 37.6173, "name": "Moscow", "country": "Russia"},
            "beijing": {"lat": 39.9042, "lng": 116.4074, "name": "Beijing", "country": "China"},
            "shanghai": {"lat": 31.2304, "lng": 121.4737, "name": "Shanghai", "country": "China"},
            "mumbai": {"lat": 19.076, "lng": 72.8777, "name": "Mumbai", "country": "India"},
            "delhi": {"lat": 28.6139, "lng": 77.209, "name": "Delhi", "country": "India"},
            "bangkok": {"lat": 13.7563, "lng": 100.5018, "name": "Bangkok", "country": "Thailand"},
            "seoul": {"lat": 37.5665, "lng": 126.978, "name": "Seoul", "country": "South Korea"},
            "cairo": {"lat": 30.0444, "lng": 31.2357, "name": "Cairo", "country": "Egypt"},
            "egypt": {"lat": 30.0444, "lng": 31.2357, "name": "Cairo", "country": "Egypt"},
            "cairo egypt": {"lat": 30.0444, "lng": 31.2357, "name": "Cairo", "country": "Egypt"},
            "orlando": {"lat": 28.5383, "lng": -81.3792, "name": "Orlando", "country": "USA"},
            "tampa": {"lat": 27.9506, "lng": -82.4572, "name": "Tampa", "country": "USA"},
            "florida": {"lat": 27.6648, "lng": -81.5158, "name": "Florida", "country": "USA"},
            "safety harbor": {"lat": 27.9906, "lng": -82.6926, "name": "Safety Harbor", "country": "USA"},
            "johannesburg": {"lat": -26.2041, "lng": 28.0473, "name": "Johannesburg", "country": "South Africa"},
            "cape town": {"lat": -33.9249, "lng": 18.4241, "name": "Cape Town", "country": "South Africa"},
            "lagos": {"lat": 6.5244, "lng": 3.3792, "name": "Lagos", "country": "Nigeria"},
            "nairobi": {"lat": -1.2921, "lng": 36.8219, "name": "Nairobi", "country": "Kenya"},
            "istanbul": {"lat": 41.0082, "lng": 28.9784, "name": "Istanbul", "country": "Turkey"},
            "athens": {"lat": 37.9838, "lng": 23.7275, "name": "Athens", "country": "Greece"},
            "vienna": {"lat": 48.2082, "lng": 16.3738, "name": "Vienna", "country": "Austria"},
            "zurich": {"lat": 47.3769, "lng": 8.5417, "name": "Zurich", "country": "Switzerland"},
            "stockholm": {"lat": 59.3293, "lng": 18.0686, "name": "Stockholm", "country": "Sweden"},
            "oslo": {"lat": 59.9139, "lng": 10.7522, "name": "Oslo", "country": "Norway"},
            "copenhagen": {"lat": 55.6761, "lng": 12.5683, "name": "Copenhagen", "country": "Denmark"},
            "helsinki": {"lat": 60.1699, "lng": 24.9384, "name": "Helsinki", "country": "Finland"},
            "dublin": {"lat": 53.3498, "lng": -6.2603, "name": "Dublin", "country": "Ireland"},
            "lisbon": {"lat": 38.7223, "lng": -9.1393, "name": "Lisbon", "country": "Portugal"},
            "prague": {"lat": 50.0755, "lng": 14.4378, "name": "Prague", "country": "Czech Republic"},
            "budapest": {"lat": 47.4979, "lng": 19.0402, "name": "Budapest", "country": "Hungary"},
            "warsaw": {"lat": 52.2297, "lng": 21.0122, "name": "Warsaw", "country": "Poland"},
            "kuala lumpur": {"lat": 3.139, "lng": 101.6869, "name": "Kuala Lumpur", "country": "Malaysia"},
            "jakarta": {"lat": -6.2088, "lng": 106.8456, "name": "Jakarta", "country": "Indonesia"},
            "manila": {"lat": 14.5995, "lng": 120.9842, "name": "Manila", "country": "Philippines"},
            "hanoi": {"lat": 21.0285, "lng": 105.8542, "name": "Hanoi", "country": "Vietnam"},
            "auckland": {"lat": -36.8485, "lng": 174.7633, "name": "Auckland", "country": "New Zealand"},
            "melbourne": {"lat": -37.8136, "lng": 144.9631, "name": "Melbourne", "country": "Australia"},
            "perth": {"lat": -31.9505, "lng": 115.8605, "name": "Perth", "country": "Australia"},
            "denver": {"lat": 39.7392, "lng": -104.9903, "name": "Denver", "country": "USA"},
            "phoenix": {"lat": 33.4484, "lng": -112.074, "name": "Phoenix", "country": "USA"},
            "las vegas": {"lat": 36.1699, "lng": -115.1398, "name": "Las Vegas", "country": "USA"},
            "atlanta": {"lat": 33.749, "lng": -84.388, "name": "Atlanta", "country": "USA"},
            "dallas": {"lat": 32.7767, "lng": -96.797, "name": "Dallas", "country": "USA"},
            "houston": {"lat": 29.7604, "lng": -95.3698, "name": "Houston", "country": "USA"},
        }
    
    def _create_control_buttons(self) -> List[Dict]:
        """
        Create holographic control buttons for globe manipulation.
        Buttons: Up, Down, Left, Right, Larger (+), Smaller (-)
        """
        button_size = 40
        spacing = 10
        
        # Buttons will be positioned relative to globe in render
        buttons = [
            # Direction pad
            {"id": "up", "label": "▲", "action": "move_up", "row": 0, "col": 1},
            {"id": "down", "label": "▼", "action": "move_down", "row": 2, "col": 1},
            {"id": "left", "label": "◀", "action": "move_left", "row": 1, "col": 0},
            {"id": "right", "label": "▶", "action": "move_right", "row": 1, "col": 2},
            # Size controls
            {"id": "larger", "label": "+", "action": "size_up", "row": 0, "col": 3},
            {"id": "smaller", "label": "-", "action": "size_down", "row": 2, "col": 3},
        ]
        
        return buttons
    
    def process_hand_gesture(self, hand_landmarks: List, frame_width: int, frame_height: int):
        """
        Process hand landmarks to detect swipe gestures for globe rotation and dial control.
        Called from vision system when hands are detected.
        
        Dial Control:
        - Clockwise hand rotation = increase dial value (turn ON)
        - Counter-clockwise hand rotation = decrease dial value (turn OFF)
        
        Args:
            hand_landmarks: MediaPipe hand landmarks
            frame_width: Frame width for coordinate conversion
            frame_height: Frame height for coordinate conversion
        """
        # Process dial control if dial window is active
        if self.dial_window and self.dial_window.visible:
            self._process_dial_hand_control(hand_landmarks, frame_width, frame_height)
        
        if self.active_hologram != HologramType.GLOBE:
            return
        
        if not hand_landmarks:
            # No hand - apply momentum/friction to rotation
            self.hand_gesture.is_grabbing = False
            # Apply friction to slow down rotation
            self.hand_gesture.rotation_velocity_y *= 0.95
            self.globe_state.rotation_y += self.hand_gesture.rotation_velocity_y
            return
        
        # Get index finger tip position (landmark 8)
        try:
            index_tip = hand_landmarks[8]
            hand_x = index_tip.x * frame_width
            hand_y = index_tip.y * frame_height
            
            current_time = time.time()
            
            # Track hand position history
            self.hand_history.append((hand_x, hand_y, current_time))
            if len(self.hand_history) > self.max_hand_history:
                self.hand_history.pop(0)
            
            # Check if hand is near the globe area
            # Globe is on the right side of the frame
            globe_center_x = frame_width * 0.75  # Right side
            globe_center_y = frame_height * 0.5
            globe_radius = min(frame_width, frame_height) * self.hologram_scale * 0.5
            
            dist_to_globe = math.sqrt((hand_x - globe_center_x)**2 + (hand_y - globe_center_y)**2)
            
            if dist_to_globe < globe_radius * 1.5:  # Hand is near globe
                if not self.hand_gesture.is_grabbing:
                    # Start grabbing
                    self.hand_gesture.is_grabbing = True
                    self.hand_gesture.grab_start_x = hand_x
                    self.hand_gesture.grab_start_y = hand_y
                    self.hand_gesture.last_hand_x = hand_x
                    self.hand_gesture.last_hand_y = hand_y
                    self.hand_gesture.last_update_time = current_time
                else:
                    # Calculate swipe velocity
                    dt = current_time - self.hand_gesture.last_update_time
                    if dt > 0:
                        dx = hand_x - self.hand_gesture.last_hand_x
                        
                        # Convert horizontal movement to rotation
                        # Swipe right = rotate globe right (positive Y rotation)
                        rotation_speed = dx * 0.005  # Adjust sensitivity
                        self.hand_gesture.rotation_velocity_y = rotation_speed
                        self.globe_state.rotation_y += rotation_speed
                    
                    self.hand_gesture.last_hand_x = hand_x
                    self.hand_gesture.last_hand_y = hand_y
                    self.hand_gesture.last_update_time = current_time
            else:
                self.hand_gesture.is_grabbing = False
                
        except (IndexError, AttributeError):
            pass
    
    def _process_dial_hand_control(self, hand_landmarks: List, frame_width: int, frame_height: int):
        """
        Process hand rotation to control the dial.
        Clockwise = increase value (turn ON)
        Counter-clockwise = decrease value (turn OFF)
        """
        if not hand_landmarks or not self.dial_window:
            return
        
        try:
            # Get wrist (0) and middle finger tip (12) to detect rotation
            wrist = hand_landmarks[0]
            middle_tip = hand_landmarks[12]
            
            # Calculate angle from wrist to middle finger
            dx = middle_tip.x - wrist.x
            dy = middle_tip.y - wrist.y
            current_angle = math.atan2(dy, dx)
            
            # Track angle history for rotation detection
            if not hasattr(self, '_dial_angle_history'):
                self._dial_angle_history = []
                self._last_dial_angle = current_angle
            
            # Calculate angle change
            angle_diff = current_angle - self._last_dial_angle
            
            # Normalize angle difference to handle wrap-around
            if angle_diff > math.pi:
                angle_diff -= 2 * math.pi
            elif angle_diff < -math.pi:
                angle_diff += 2 * math.pi
            
            # Apply rotation to dial value
            # Positive angle_diff = clockwise = increase value
            # Negative angle_diff = counter-clockwise = decrease value
            sensitivity = 0.3
            new_value = self.dial_window.value + (angle_diff * sensitivity)
            new_value = max(0.0, min(1.0, new_value))
            
            self.dial_window.set_value(new_value)
            
            # Check for alarm trigger (value > 0.8 = ON, value < 0.2 = OFF)
            if new_value > 0.8 and not getattr(self, '_alarm_triggered_by_dial', False):
                self.trigger_alarm()
                self._alarm_triggered_by_dial = True
                print("[DIAL] Alarm triggered by clockwise rotation!")
            elif new_value < 0.2 and getattr(self, '_alarm_triggered_by_dial', False):
                self.stop_alarm()
                self._alarm_triggered_by_dial = False
                print("[DIAL] Alarm stopped by counter-clockwise rotation!")
            
            self._last_dial_angle = current_angle
            
        except (IndexError, AttributeError) as e:
            pass
    
    def handle_control_button(self, button_id: str):
        """
        Handle control button press.
        
        Args:
            button_id: ID of the pressed button
        """
        move_amount = 20  # pixels
        size_amount = 0.02  # scale factor
        
        if button_id == "move_up":
            # Move globe up (decrease Y offset)
            self.hologram_position_offset_y = getattr(self, 'hologram_position_offset_y', 0) - move_amount
        elif button_id == "move_down":
            self.hologram_position_offset_y = getattr(self, 'hologram_position_offset_y', 0) + move_amount
        elif button_id == "move_left":
            self.hologram_position_offset_x = getattr(self, 'hologram_position_offset_x', 0) - move_amount
        elif button_id == "move_right":
            self.hologram_position_offset_x = getattr(self, 'hologram_position_offset_x', 0) + move_amount
        elif button_id == "size_up":
            self.hologram_scale = min(0.6, self.hologram_scale + size_amount)
        elif button_id == "size_down":
            self.hologram_scale = max(0.1, self.hologram_scale - size_amount)
        
        print(f"[GLOBE] Control: {button_id}")
    
    def _render_control_panel(self, frame: np.ndarray, globe_x: int, globe_y: int, globe_size: int) -> np.ndarray:
        """
        Render the holographic control panel below the globe.
        """
        if not self.show_control_panel or self.globe_state.is_materializing:
            return frame

        h, w = frame.shape[:2]
        
        # Panel position (below globe)
        panel_x = globe_x - 80
        panel_y = globe_y + globe_size // 2 + 20
        
        button_size = 35
        spacing = 5
        
        # Draw panel background
        panel_w = button_size * 4 + spacing * 5
        panel_h = button_size * 3 + spacing * 4
        
        # Semi-transparent background
        overlay = frame.copy()
        cv2.rectangle(overlay, 
                     (panel_x - 10, panel_y - 10),
                     (panel_x + panel_w + 10, panel_y + panel_h + 10),
                     (50, 50, 50), -1)
        cv2.addWeighted(overlay, 0.5, frame, 0.5, 0, frame)
        
        # Draw border
        cv2.rectangle(frame, 
                     (panel_x - 10, panel_y - 10),
                     (panel_x + panel_w + 10, panel_y + panel_h + 10),
                     (0, 255, 255), 1)
        
        # Draw buttons
        for button in self.control_buttons:
            bx = panel_x + button['col'] * (button_size + spacing)
            by = panel_y + button['row'] * (button_size + spacing)
            
            # Button background
            cv2.rectangle(frame, (bx, by), (bx + button_size, by + button_size),
                         (80, 80, 80), -1)
            cv2.rectangle(frame, (bx, by), (bx + button_size, by + button_size),
                         (0, 255, 255), 1)
            
            # Button label
            label = button['label']
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
            label_x = bx + (button_size - label_size[0]) // 2
            label_y = by + (button_size + label_size[1]) // 2
            cv2.putText(frame, label, (label_x, label_y),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            
            # Store button bounds for click detection
            button['bounds'] = (bx, by, bx + button_size, by + button_size)
        
        # Label
        cv2.putText(frame, "GLOBE CONTROL", (panel_x, panel_y - 15),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)
        
        return frame

    
    def check_button_press(self, finger_x: int, finger_y: int) -> Optional[str]:
        """
        Check if a finger position is pressing a control button.
        
        Args:
            finger_x, finger_y: Finger tip position in frame coordinates
            
        Returns:
            Button action if pressed, None otherwise
        """
        for button in self.control_buttons:
            if 'bounds' in button:
                x1, y1, x2, y2 = button['bounds']
                if x1 <= finger_x <= x2 and y1 <= finger_y <= y2:
                    return button['action']
        return None
    
    def _create_keyboard_layout(self) -> List[Dict]:
        """Create holographic keyboard layout."""
        keys = []
        
        # QWERTY layout
        rows = [
            ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0'],
            ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P'],
            ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L'],
            ['Z', 'X', 'C', 'V', 'B', 'N', 'M']
        ]
        
        key_width = 45
        key_height = 40
        key_margin = 5
        
        for row_idx, row in enumerate(rows):
            for col_idx, char in enumerate(row):
                keys.append({
                    'char': char,
                    'row': row_idx,
                    'col': col_idx,
                    'width': key_width,
                    'height': key_height,
                    'active': False
                })
        
        # Space bar
        keys.append({
            'char': 'SPACE',
            'row': 4,
            'col': 2,
            'width': key_width * 5,
            'height': key_height,
            'active': False
        })
        
        # Backspace
        keys.append({
            'char': '←',
            'row': 0,
            'col': 10,
            'width': key_width * 2,
            'height': key_height,
            'active': False
        })
        
        # Enter
        keys.append({
            'char': 'ENTER',
            'row': 2,
            'col': 9,
            'width': key_width * 2,
            'height': key_height,
            'active': False
        })
        
        return keys
    
    def _render_holographic_keyboard(self, frame: np.ndarray) -> np.ndarray:
        """
        Render a minimal holographic keyboard - keys only, no background box.
        Features: arrow keys for movement, alien enlarge button, highlight on click.
        """
        h, w = frame.shape[:2]
        
        # Scale-adjusted dimensions
        scale = self.keyboard_scale
        key_width = int(40 * scale)
        key_height = int(35 * scale)
        key_margin = int(4 * scale)
        
        # Keyboard position with offset
        keyboard_width = 11 * (key_width + key_margin)
        keyboard_x = (w - keyboard_width) // 2 + self.keyboard_offset_x
        keyboard_y = h - int(220 * scale) + self.keyboard_offset_y
        
        # Check for highlight animation fade
        highlight_fade = 0
        if self.keyboard_active_key and time.time() - self.keyboard_highlight_time < 0.3:
            highlight_fade = 1.0 - (time.time() - self.keyboard_highlight_time) / 0.3
        else:
            self.keyboard_active_key = None
        
        # Main keyboard rows (keys only - no background)
        rows = [
            ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '←'],
            ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P'],
            ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L'],
            ['Z', 'X', 'C', 'V', 'B', 'N', 'M', '.', ','],
            ['SPACE']
        ]
        
        for row_idx, row in enumerate(rows):
            row_x = keyboard_x + row_idx * int(12 * scale)  # Stagger rows
            
            for col_idx, char in enumerate(row):
                # Calculate key position
                kx = row_x + col_idx * (key_width + key_margin)
                ky = keyboard_y + row_idx * (key_height + key_margin)
                
                # Adjust width for special keys
                kw = key_width
                if char == 'SPACE':
                    kw = key_width * 5
                    kx = keyboard_x + int(100 * scale)  # Center space bar
                elif char == '←':
                    kw = int(key_width * 1.3)
                
                # Key colors - cyan holographic glow
                base_color = (0, 180, 180)  # Cyan
                glow_color = (0, 255, 255)
                
                # Highlight active key with bright green glow
                is_active = (self.keyboard_active_key == char and highlight_fade > 0)
                if is_active:
                    intensity = int(255 * highlight_fade)
                    base_color = (0, intensity, 0)  # Green highlight
                    glow_color = (0, 255, 0)
                    # Draw glow effect
                    cv2.rectangle(frame, (kx-2, ky-2), (kx + kw + 2, ky + key_height + 2),
                                 (0, int(100 * highlight_fade), 0), -1)
                
                # Draw key outline (no fill - transparent keys)
                cv2.rectangle(frame, (kx, ky), (kx + kw, ky + key_height),
                             glow_color, 1)
                
                # Draw key label
                label = char if char != 'SPACE' else '________'
                font_scale = 0.35 * scale
                label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 1)[0]
                label_x = kx + (kw - label_size[0]) // 2
                label_y = ky + (key_height + label_size[1]) // 2
                cv2.putText(frame, label, (label_x, label_y),
                           cv2.FONT_HERSHEY_SIMPLEX, font_scale, glow_color, 1)
        
        # Arrow keys (bottom right) for moving keyboard
        arrow_x = keyboard_x + keyboard_width + int(20 * scale)
        arrow_y = keyboard_y + int(60 * scale)
        arrow_size = int(25 * scale)
        
        arrows = [
            ('↑', 0, -1),   # Up
            ('↓', 0, 1),    # Down
            ('←', -1, 0),   # Left (arrow key, not backspace)
            ('→', 1, 0),    # Right
        ]
        
        for i, (arrow, dx, dy) in enumerate(arrows):
            ax = arrow_x + (1 + dx) * (arrow_size + 3)
            ay = arrow_y + (1 + dy) * (arrow_size + 3)
            
            # Draw arrow key
            cv2.rectangle(frame, (ax, ay), (ax + arrow_size, ay + arrow_size),
                         (0, 200, 200), 1)
            
            # Highlight if this arrow is active
            if self.keyboard_active_key == f'ARROW_{arrow}':
                cv2.rectangle(frame, (ax, ay), (ax + arrow_size, ay + arrow_size),
                             (0, 255, 0), -1)
            
            cv2.putText(frame, arrow, (ax + 5, ay + arrow_size - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4 * scale, (0, 255, 255), 1)
        
        # Alien Enlarge Button (hexagonal alien shape)
        enlarge_x = arrow_x + int(30 * scale)
        enlarge_y = arrow_y + int(90 * scale)
        alien_size = int(35 * scale)
        
        # Draw alien hexagon shape
        pts = np.array([
            [enlarge_x + alien_size//2, enlarge_y],
            [enlarge_x + alien_size, enlarge_y + alien_size//3],
            [enlarge_x + alien_size, enlarge_y + alien_size*2//3],
            [enlarge_x + alien_size//2, enlarge_y + alien_size],
            [enlarge_x, enlarge_y + alien_size*2//3],
            [enlarge_x, enlarge_y + alien_size//3],
        ], np.int32)
        
        # Highlight if active
        if self.keyboard_active_key == 'ENLARGE':
            cv2.fillPoly(frame, [pts], (0, 150, 0))
        
        cv2.polylines(frame, [pts], True, (0, 255, 200), 2)
        
        # Alien eye in center
        eye_x = enlarge_x + alien_size // 2
        eye_y = enlarge_y + alien_size // 2
        cv2.circle(frame, (eye_x, eye_y), int(8 * scale), (0, 255, 200), 1)
        cv2.circle(frame, (eye_x, eye_y), int(3 * scale), (0, 255, 200), -1)
        
        # Store button bounds for click detection
        self._keyboard_arrow_bounds = {
            'UP': (arrow_x + arrow_size + 3, arrow_y, arrow_size, arrow_size),
            'DOWN': (arrow_x + arrow_size + 3, arrow_y + 2*(arrow_size + 3), arrow_size, arrow_size),
            'LEFT': (arrow_x, arrow_y + arrow_size + 3, arrow_size, arrow_size),
            'RIGHT': (arrow_x + 2*(arrow_size + 3), arrow_y + arrow_size + 3, arrow_size, arrow_size),
            'ENLARGE': (enlarge_x, enlarge_y, alien_size, alien_size),
        }
        
        return frame
    
    def check_keyboard_press(self, finger_x: int, finger_y: int, frame_height: int, frame_width: int) -> Optional[str]:
        """
        Check if finger is pressing a keyboard key.
        Handles: letter keys, arrow keys for movement, alien enlarge button.
        
        Returns:
            Character pressed or None
        """
        current_time = time.time()
        if current_time - self.keyboard_last_press_time < self.keyboard_cooldown:
            return None
        
        scale = self.keyboard_scale
        key_width = int(40 * scale)
        key_height = int(35 * scale)
        key_margin = int(4 * scale)
        
        keyboard_width = 11 * (key_width + key_margin)
        keyboard_x = (frame_width - keyboard_width) // 2 + self.keyboard_offset_x
        keyboard_y = frame_height - int(220 * scale) + self.keyboard_offset_y
        
        # Check arrow keys and enlarge button first
        if hasattr(self, '_keyboard_arrow_bounds'):
            for action, (bx, by, bw, bh) in self._keyboard_arrow_bounds.items():
                if bx <= finger_x <= bx + bw and by <= finger_y <= by + bh:
                    self.keyboard_last_press_time = current_time
                    self.keyboard_highlight_time = current_time
                    
                    if action == 'UP':
                        self.keyboard_offset_y -= 20
                        self.keyboard_active_key = 'ARROW_↑'
                    elif action == 'DOWN':
                        self.keyboard_offset_y += 20
                        self.keyboard_active_key = 'ARROW_↓'
                    elif action == 'LEFT':
                        self.keyboard_offset_x -= 20
                        self.keyboard_active_key = 'ARROW_←'
                    elif action == 'RIGHT':
                        self.keyboard_offset_x += 20
                        self.keyboard_active_key = 'ARROW_→'
                    elif action == 'ENLARGE':
                        self.keyboard_scale = min(2.0, self.keyboard_scale + 0.2)
                        self.keyboard_active_key = 'ENLARGE'
                    
                    # Play key click sound
                    self._play_key_click_sound()
                    return action
        
        # Check main keyboard keys
        rows = [
            ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '←'],
            ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P'],
            ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L'],
            ['Z', 'X', 'C', 'V', 'B', 'N', 'M', '.', ','],
            ['SPACE']
        ]
        
        for row_idx, row in enumerate(rows):
            row_x = keyboard_x + row_idx * int(12 * scale)
            
            for col_idx, char in enumerate(row):
                kx = row_x + col_idx * (key_width + key_margin)
                ky = keyboard_y + row_idx * (key_height + key_margin)
                
                kw = key_width
                if char == 'SPACE':
                    kw = key_width * 5
                    kx = keyboard_x + int(100 * scale)
                elif char == '←':
                    kw = int(key_width * 1.3)
                
                # Check if finger is in key bounds
                if kx <= finger_x <= kx + kw and ky <= finger_y <= ky + key_height:
                    self.keyboard_last_press_time = current_time
                    self.keyboard_active_key = char
                    self.keyboard_highlight_time = current_time
                    
                    # Play key click sound
                    self._play_key_click_sound()
                    
                    # Handle special keys
                    if char == '←':
                        self.keyboard_typed_text = self.keyboard_typed_text[:-1]
                    elif char == 'SPACE':
                        self.keyboard_typed_text += ' '
                    else:
                        self.keyboard_typed_text += char.lower()
                    
                    return char
        
        return None
    
    def _play_key_click_sound(self):
        """Play sci-fi key click sound."""
        if not HAS_PYGAME or not self.sounds_loaded:
            return
        
        try:
            # Generate a quick sci-fi click sound
            import pygame
            sample_rate = 22050
            duration = 0.05  # 50ms click
            
            t = np.linspace(0, duration, int(sample_rate * duration), False)
            # High-pitched click with quick decay
            click = np.sin(2 * np.pi * 1200 * t) * np.exp(-t * 50)
            click = (click * 32767 * 0.3).astype(np.int16)
            
            # Stereo
            stereo = np.column_stack([click, click])
            sound = pygame.sndarray.make_sound(stereo)
            sound.play()
        except Exception:
            pass
    
    def _play_keyboard_appear_sound(self):
        """Play sci-fi sound when keyboard appears."""
        if not HAS_PYGAME or not self.sounds_loaded:
            return
        
        try:
            import pygame
            sample_rate = 22050
            duration = 0.3  # 300ms whoosh
            
            t = np.linspace(0, duration, int(sample_rate * duration), False)
            # Rising frequency whoosh
            freq = 400 + 800 * t / duration
            whoosh = np.sin(2 * np.pi * freq * t) * np.exp(-t * 3)
            whoosh = (whoosh * 32767 * 0.4).astype(np.int16)
            
            stereo = np.column_stack([whoosh, whoosh])
            sound = pygame.sndarray.make_sound(stereo)
            sound.play()
        except Exception:
            pass
    
    def toggle_keyboard(self, show: bool = None) -> str:
        """Toggle the holographic keyboard visibility with sci-fi sound."""
        if show is None:
            self.show_holographic_keyboard = not self.show_holographic_keyboard
        else:
            self.show_holographic_keyboard = show
        
        if self.show_holographic_keyboard:
            # Play appear sound
            self._play_keyboard_appear_sound()
            # DISABLED: Separate window - render on camera feed only
            # if self.keyboard_window:
            #     self.keyboard_window.show()
            return "Holographic keyboard enabled."
        else:
            # DISABLED: Separate window - render on camera feed only
            # if self.keyboard_window:
            #     self.keyboard_window.hide()
            return "Holographic keyboard hidden."

    def _load_sounds(self):
        """Load sci-fi sound effects and Monica's globe sounds."""
        if not HAS_PYGAME:
            print("  [SOUND] Pygame not available, sounds disabled")
            return

        try:
            # Generate synthetic sci-fi sounds using pygame
            self._generate_materialize_sound()
            self._generate_beep_sound()
            self._generate_alarm_sound()

            # Load Monica's external sci-fi sounds for globe hologram
            try:
                import os
                scifi_dir = os.path.join(os.path.dirname(__file__), 'monica_ai', 'resources', 'sounds', 'scifi')
                mapping = {
                    'globe_turn_sound': 'globe_turn.mp3',
                    'hologram_ambient_sound': 'hologramsound_one.mp3',
                    'location_pulse_sound': 'globelocation_pulsating_currentlocation.mp3',
                }
                if os.path.isdir(scifi_dir):
                    import pygame as _pg
                    for attr, filename in mapping.items():
                        path = os.path.join(scifi_dir, filename)
                        if os.path.exists(path):
                            try:
                                snd = _pg.mixer.Sound(path)
                                # Set base volumes (fine-tuned for subtle background)
                                if attr == 'hologram_ambient_sound':
                                    snd.set_volume(0.15)
                                elif attr == 'location_pulse_sound':
                                    snd.set_volume(0.2)
                                elif attr == 'globe_turn_sound':
                                    snd.set_volume(0.4)
                                setattr(self, attr, snd)
                            except Exception as e:
                                print(f"  [SOUND] Could not load {filename}: {e}")
            except Exception as e:
                print(f"  [SOUND] Sci-fi globe sounds load error: {e}")

            self.sounds_loaded = True
            print("  [SOUND] Sci-fi sounds loaded")
        except Exception as e:
            print(f"  [SOUND] Could not load sounds: {e}")

    def _generate_materialize_sound(self):
        """Generate a digital materialization sound effect."""
        if not HAS_PYGAME:
            return
        
        try:
            # Create a rising digital tone
            sample_rate = 22050
            duration = 2.0
            samples = int(sample_rate * duration)
            
            # Generate rising frequency sweep with digital artifacts
            t = np.linspace(0, duration, samples)
            freq_start, freq_end = 200, 800
            freq = freq_start + (freq_end - freq_start) * (t / duration) ** 2
            
            # Main tone with harmonics
            wave = np.sin(2 * np.pi * freq * t) * 0.3
            wave += np.sin(2 * np.pi * freq * 2 * t) * 0.15  # Harmonic
            wave += np.sin(2 * np.pi * freq * 3 * t) * 0.1   # Harmonic
            
            # Add digital "glitch" artifacts
            glitch_times = np.random.random(20) * duration
            for gt in glitch_times:
                idx = int(gt * sample_rate)
                if idx < samples - 100:
                    wave[idx:idx+100] *= np.random.random() * 0.5 + 0.5
            
            # Envelope
            envelope = np.linspace(0, 1, samples // 4)
            envelope = np.concatenate([envelope, np.ones(samples - len(envelope))])
            wave *= envelope
            
            # Convert to 16-bit
            wave = (wave * 32767).astype(np.int16)
            
            # Create stereo
            stereo = np.column_stack([wave, wave])
            
            self.materialize_sound = pygame.sndarray.make_sound(stereo)
            self.materialize_sound.set_volume(0.4)
        except Exception as e:
            print(f"  [SOUND] Materialize sound error: {e}")
            self.materialize_sound = None
    
    def _generate_beep_sound(self):
        """Generate a location beep sound."""
        if not HAS_PYGAME:
            return
        
        try:
            sample_rate = 22050
            duration = 0.15
            samples = int(sample_rate * duration)
            
            t = np.linspace(0, duration, samples)
            freq = 1200
            
            # Sharp beep
            wave = np.sin(2 * np.pi * freq * t) * 0.5
            
            # Quick envelope
            envelope = np.exp(-t * 15)
            wave *= envelope
            
            wave = (wave * 32767).astype(np.int16)
            stereo = np.column_stack([wave, wave])
            
            self.beep_sound = pygame.sndarray.make_sound(stereo)
            self.beep_sound.set_volume(0.3)
        except Exception as e:
            print(f"  [SOUND] Beep sound error: {e}")
            self.beep_sound = None
    
    def _generate_alarm_sound(self):
        """Generate a deep spaceship alarm - 'brrrr (pause) brrraarrr' style."""
        if not HAS_PYGAME:
            return
        
        try:
            sample_rate = 44100  # Higher sample rate for better bass
            
            # Create 4 "brrrr" bursts with pauses
            burst_duration = 0.6  # Each brrrr
            pause_duration = 0.3  # Pause between
            total_duration = 4 * burst_duration + 3 * pause_duration
            
            total_samples = int(sample_rate * total_duration)
            wave = np.zeros(total_samples)
            
            for burst_num in range(4):
                # Calculate start position for this burst
                start_time = burst_num * (burst_duration + pause_duration)
                start_sample = int(start_time * sample_rate)
                burst_samples = int(burst_duration * sample_rate)
                
                t = np.linspace(0, burst_duration, burst_samples)
                
                # Deep bass frequencies (spaceship rumble from floor)
                base_freq = 45 + burst_num * 5  # Slight variation each burst
                
                # Main deep rumble
                burst = np.sin(2 * np.pi * base_freq * t) * 0.5
                
                # Add sub-bass for floor vibration feel
                burst += np.sin(2 * np.pi * 30 * t) * 0.3
                
                # Add growling harmonics for "brrrr" texture
                burst += np.sin(2 * np.pi * base_freq * 2 * t) * 0.2
                burst += np.sin(2 * np.pi * base_freq * 3 * t) * 0.1
                
                # Add slight frequency modulation for "brrraarrr" effect
                mod_freq = 8 + burst_num  # Modulation speed
                burst *= (1 + 0.3 * np.sin(2 * np.pi * mod_freq * t))
                
                # Add rumble/vibration texture
                rumble = np.random.uniform(-0.1, 0.1, burst_samples)
                rumble_filtered = np.convolve(rumble, np.ones(100)/100, mode='same')
                burst += rumble_filtered * 0.15
                
                # Envelope - quick attack, sustain, quick release
                env = np.ones(burst_samples)
                attack = int(burst_samples * 0.05)
                release = int(burst_samples * 0.15)
                env[:attack] = np.linspace(0, 1, attack)
                env[-release:] = np.linspace(1, 0, release)
                burst *= env
                
                # Place burst in wave
                end_sample = min(start_sample + burst_samples, total_samples)
                wave[start_sample:end_sample] = burst[:end_sample - start_sample]
            
            # Normalize and convert to 16-bit stereo
            max_val = np.max(np.abs(wave))
            if max_val > 0:
                wave = wave / max_val * 0.8
            wave = (wave * 32767).astype(np.int16)
            stereo = np.column_stack([wave, wave])
            
            self.alarm_sound = pygame.sndarray.make_sound(stereo)
            self.alarm_sound.set_volume(0.7)  # Louder for impact
            print("  [SOUND] Deep spaceship alarm loaded")
        except Exception as e:
            print(f"  [SOUND] Alarm sound error: {e}")
            self.alarm_sound = None
    def toggle_dial(self, show: bool = None) -> str:
        """Toggle the holographic dial visibility."""
        if show is None:
            self.show_holographic_dial = not self.show_holographic_dial
        else:
            self.show_holographic_dial = show
        
        if self.show_holographic_dial:
            # DISABLED: Separate window - render on camera feed only
            # if self.dial_window:
            #     self.dial_window.show()
            return "Holographic dial enabled."
        else:
            # DISABLED: Separate window - render on camera feed only
            # if self.dial_window:
            #     self.dial_window.hide()
            return "Holographic dial hidden."
    
    def trigger_alarm(self):
        """
        Trigger sci-fi alarm mode - red blinking effect.
        Called when user rotates hand quickly on the dial.
        """
        if not hasattr(self, 'alarm_active'):
            self.alarm_active = False
            self.alarm_start_time = 0
            self.alarm_duration = 5.0  # Seconds
        
        self.alarm_active = True
        self.alarm_start_time = time.time()
        
        # Play alarm sound
        self._play_ui_sound("alarm")
        
        print("[AR] 🚨 ALARM TRIGGERED!")
        return "Alert! Alarm activated!"
    
    def stop_alarm(self):
        """Stop the alarm."""
        if hasattr(self, 'alarm_active'):
            self.alarm_active = False
            print("[AR] 🔕 Alarm stopped!")
            return "Alarm deactivated."
        return "No alarm was active."
    
    def show_monica_next_to_me(self, intensity: float = 0.7):
        """
        Show Monica's holographic presence next to the user in the camera feed.
        This creates a subtle glowing orb effect positioned to the side.
        
        Args:
            intensity: Brightness of the hologram (0.0 to 1.0)
        """
        # Store state for rendering Monica's presence
        self.monica_next_to_me = True
        self.monica_presence_intensity = intensity
        self.monica_presence_start_time = time.time()
        self.monica_presence_duration = 30.0  # Show for 30 seconds
        
        # Play materialization sound
        if hasattr(self, 'materialize_sound') and self.materialize_sound:
            try:
                self.materialize_sound.play()
            except Exception:
                pass
        
        print(f"[AR] Monica appearing next to user (intensity: {intensity})")
        return "I'm appearing next to you."
    
    def hide_monica_presence(self):
        """Hide Monica's holographic presence."""
        self.monica_next_to_me = False
        print("[AR] Monica presence hidden")
        return "Stepping back."
    
    def render_monica_presence(self, frame: np.ndarray) -> np.ndarray:
        """Render Monica's holographic presence next to user."""
        if not getattr(self, 'monica_next_to_me', False):
            return frame
        
        # Check if duration expired
        elapsed = time.time() - getattr(self, 'monica_presence_start_time', 0)
        if elapsed > getattr(self, 'monica_presence_duration', 30.0):
            self.monica_next_to_me = False
            return frame
        
        h, w = frame.shape[:2]
        intensity = getattr(self, 'monica_presence_intensity', 0.7)
        
        # Create a subtle glowing orb on the right side of the frame
        orb_x = int(w * 0.85)  # Right side
        orb_y = int(h * 0.4)   # Upper portion
        orb_radius = int(min(w, h) * 0.15)
        
        # Pulsing effect
        pulse = 0.8 + 0.2 * math.sin(elapsed * 3)
        
        # Draw glowing orb with cyan/blue color (Monica's signature color)
        overlay = frame.copy()
        
        # Multiple layers for glow effect
        for i in range(5, 0, -1):
            radius = int(orb_radius * (1 + i * 0.2))
            alpha = intensity * pulse * (0.1 / i)
            color = (255, 200, 100)  # Cyan-ish
            cv2.circle(overlay, (orb_x, orb_y), radius, color, -1)
            frame = cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)
            overlay = frame.copy()
        
        # Core orb
        cv2.circle(frame, (orb_x, orb_y), orb_radius, (255, 220, 150), -1)
        
        return frame
    
    def is_alarm_active(self) -> bool:
        """Check if alarm is currently active."""
        if not hasattr(self, 'alarm_active'):
            return False
        
        if self.alarm_active:
            elapsed = time.time() - self.alarm_start_time
            if elapsed > self.alarm_duration:
                self.alarm_active = False
                print("[AR] Alarm deactivated")
        
        return self.alarm_active
    
    def render_alarm_effect(self, frame: np.ndarray) -> np.ndarray:
        """Render red blinking alarm effect on frame."""
        if not self.is_alarm_active():
            return frame
        
        elapsed = time.time() - self.alarm_start_time
        
        # Blinking effect - alternate between red overlay and normal
        blink_rate = 4  # Hz
        blink_on = int(elapsed * blink_rate * 2) % 2 == 0
        
        if blink_on:
            # Red overlay
            red_overlay = frame.copy()
            red_overlay[:, :, 2] = np.clip(red_overlay[:, :, 2].astype(np.int32) + 80, 0, 255).astype(np.uint8)
            red_overlay[:, :, 0] = np.clip(red_overlay[:, :, 0].astype(np.int32) - 30, 0, 255).astype(np.uint8)
            red_overlay[:, :, 1] = np.clip(red_overlay[:, :, 1].astype(np.int32) - 30, 0, 255).astype(np.uint8)
            frame = cv2.addWeighted(frame, 0.5, red_overlay, 0.5, 0)
            
            # Red border
            h, w = frame.shape[:2]
            border_size = 10
            frame[:border_size, :] = (0, 0, 255)
            frame[-border_size:, :] = (0, 0, 255)
            frame[:, :border_size] = (0, 0, 255)
            frame[:, -border_size:] = (0, 0, 255)
            
            # Alert text
            cv2.putText(frame, "! ALERT !", (w // 2 - 80, 50),
                       cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3, cv2.LINE_AA)
        
        return frame
    
    def _generate_globe_points(self):
        """Generate 3D points for globe wireframe."""
        self.globe_points = []
        
        # Latitude lines
        for lat in range(-80, 90, 20):
            lat_rad = math.radians(lat)
            points = []
            for lng in range(0, 361, 10):
                lng_rad = math.radians(lng)
                x = self.earth_radius * math.cos(lat_rad) * math.cos(lng_rad)
                y = self.earth_radius * math.cos(lat_rad) * math.sin(lng_rad)
                z = self.earth_radius * math.sin(lat_rad)
                points.append((x, y, z))
            self.globe_points.append(("lat", points))
        
        # Longitude lines
        for lng in range(0, 180, 30):
            lng_rad = math.radians(lng)
            points = []
            for lat in range(-90, 91, 10):
                lat_rad = math.radians(lat)
                x = self.earth_radius * math.cos(lat_rad) * math.cos(lng_rad)
                y = self.earth_radius * math.cos(lat_rad) * math.sin(lng_rad)
                z = self.earth_radius * math.sin(lat_rad)
                points.append((x, y, z))
            self.globe_points.append(("lng", points))
    
    def _generate_continent_outlines(self):
        """
        Generate simplified continent outlines for a filled globe look.
        These are approximate outlines that give the globe a recognizable Earth appearance.
        """
        self.continent_polygons = []
        
        # Simplified continent outlines (lat, lng pairs)
        # North America
        north_america = [
            (70, -170), (70, -140), (65, -140), (60, -140), (55, -130),
            (50, -125), (45, -125), (40, -125), (35, -120), (30, -118),
            (25, -110), (20, -105), (15, -95), (15, -85), (10, -80),
            (10, -75), (25, -80), (30, -82), (30, -85), (25, -97),
            (30, -95), (30, -90), (35, -90), (40, -75), (45, -70),
            (50, -65), (55, -60), (60, -65), (65, -70), (70, -80),
            (75, -90), (80, -100), (75, -140), (70, -170)
        ]
        self.continent_polygons.append(("north_america", north_america))
        
        # South America
        south_america = [
            (10, -75), (5, -77), (0, -80), (-5, -80), (-10, -78),
            (-15, -75), (-20, -70), (-25, -65), (-30, -70), (-35, -72),
            (-40, -73), (-45, -75), (-50, -73), (-55, -68), (-55, -65),
            (-50, -60), (-45, -60), (-40, -58), (-35, -55), (-30, -50),
            (-25, -48), (-20, -42), (-15, -40), (-10, -38), (-5, -35),
            (0, -50), (5, -60), (10, -70), (10, -75)
        ]
        self.continent_polygons.append(("south_america", south_america))
        
        # Europe
        europe = [
            (70, -10), (70, 30), (65, 30), (60, 30), (55, 20),
            (50, 5), (45, 0), (40, -5), (35, -10), (35, 0),
            (40, 5), (45, 10), (50, 15), (55, 25), (60, 30),
            (65, 25), (70, 20), (70, -10)
        ]
        self.continent_polygons.append(("europe", europe))
        
        # Africa
        africa = [
            (35, -10), (35, 10), (30, 32), (25, 35), (20, 40),
            (15, 50), (10, 50), (5, 45), (0, 42), (-5, 40),
            (-10, 40), (-15, 35), (-20, 35), (-25, 32), (-30, 28),
            (-35, 20), (-35, 18), (-30, 15), (-25, 15), (-20, 12),
            (-15, 12), (-10, 15), (-5, 10), (0, 8), (5, 0),
            (10, -5), (15, -15), (20, -17), (25, -15), (30, -10),
            (35, -10)
        ]
        self.continent_polygons.append(("africa", africa))
        
        # Asia
        asia = [
            (70, 30), (75, 80), (75, 100), (70, 140), (65, 170),
            (60, 170), (55, 160), (50, 145), (45, 140), (40, 130),
            (35, 135), (30, 120), (25, 120), (20, 110), (15, 100),
            (10, 100), (5, 105), (0, 105), (-5, 105), (-10, 120),
            (0, 130), (10, 140), (20, 145), (30, 145), (35, 140),
            (40, 140), (45, 145), (50, 155), (55, 165), (60, 170),
            (65, 180), (70, 180), (70, 140), (65, 100), (60, 80),
            (55, 60), (50, 50), (45, 40), (40, 30), (35, 25),
            (40, 30), (45, 35), (50, 40), (55, 50), (60, 55),
            (65, 50), (70, 40), (70, 30)
        ]
        self.continent_polygons.append(("asia", asia))
        
        # Australia
        australia = [
            (-10, 142), (-15, 130), (-20, 118), (-25, 114),
            (-30, 115), (-35, 117), (-38, 140), (-35, 150),
            (-30, 153), (-25, 153), (-20, 148), (-15, 145),
            (-10, 142)
        ]
        self.continent_polygons.append(("australia", australia))
        
        # Convert to 3D points
        self.continent_3d = []
        for name, outline in self.continent_polygons:
            points_3d = []
            for lat, lng in outline:
                point = self._lat_lng_to_3d(lat, lng)
                points_3d.append(point)
            self.continent_3d.append((name, points_3d))
        
        print(f"  [PERF] Generated {len(self.continent_polygons)} continent outlines")
    
    def _precompute_globe_geometry(self):
        """
        Pre-compute globe geometry as NumPy arrays for vectorized transforms.
        This avoids Python loops during rendering for massive speedup.
        """
        # Flatten all points into a single NumPy array
        all_points = []
        self.line_indices = []  # Store start/end indices for each line
        
        current_idx = 0
        for line_type, points in self.globe_points:
            start_idx = current_idx
            for p in points:
                all_points.append(p)
                current_idx += 1
            end_idx = current_idx
            self.line_indices.append((line_type, start_idx, end_idx))
        
        # Convert to NumPy array (N x 3)
        self.globe_points_np = np.array(all_points, dtype=np.float32)
        print(f"  [PERF] Pre-computed {len(all_points)} globe vertices")
    
    def _rotate_points_vectorized(self, points: np.ndarray, rot_x: float, rot_y: float) -> np.ndarray:
        """
        Rotate all points using vectorized NumPy operations.
        ~100x faster than Python loop for large point sets.
        """
        # Build rotation matrices
        cos_y, sin_y = np.cos(rot_y), np.sin(rot_y)
        cos_x, sin_x = np.cos(rot_x), np.sin(rot_x)
        
        # Rotation matrix for Y axis
        rot_y_matrix = np.array([
            [cos_y, 0, sin_y],
            [0, 1, 0],
            [-sin_y, 0, cos_y]
        ], dtype=np.float32)
        
        # Rotation matrix for X axis
        rot_x_matrix = np.array([
            [1, 0, 0],
            [0, cos_x, -sin_x],
            [0, sin_x, cos_x]
        ], dtype=np.float32)
        
        # Combined rotation (Y then X)
        rot_matrix = rot_x_matrix @ rot_y_matrix
        
        # Apply rotation to all points at once
        return points @ rot_matrix.T
    
    def _project_points_vectorized(self, points: np.ndarray, center: Tuple[int, int], scale: float) -> np.ndarray:
        """
        Project all 3D points to 2D using vectorized operations.
        Returns array of (screen_x, screen_y, z) for each point.
        """
        fov = 300.0
        z_offset = 200.0
        
        # Calculate projection factors
        z_vals = points[:, 2] + z_offset
        valid_mask = z_vals > 0
        
        factors = np.zeros(len(points), dtype=np.float32)
        factors[valid_mask] = fov / z_vals[valid_mask]
        
        # Project to screen coordinates
        screen_x = (center[0] + points[:, 0] * factors * scale).astype(np.int32)
        screen_y = (center[1] - points[:, 1] * factors * scale).astype(np.int32)
        
        # Stack results
        result = np.column_stack([screen_x, screen_y, points[:, 2]])
        result[~valid_mask] = [-1, -1, -1000]  # Mark invalid points
        
        return result
    
    def _rotate_point(self, point: Tuple[float, float, float], 
                      rot_x: float, rot_y: float) -> Tuple[float, float, float]:
        """Rotate a 3D point around X and Y axes (legacy, for single points)."""
        x, y, z = point
        
        # Rotate around Y axis
        cos_y = math.cos(rot_y)
        sin_y = math.sin(rot_y)
        x_new = x * cos_y + z * sin_y
        z_new = -x * sin_y + z * cos_y
        x, z = x_new, z_new
        
        # Rotate around X axis
        cos_x = math.cos(rot_x)
        sin_x = math.sin(rot_x)
        y_new = y * cos_x - z * sin_x
        z_new = y * sin_x + z * cos_x
        y, z = y_new, z_new
        
        return (x, y, z)
    
    def _project_point(self, point: Tuple[float, float, float], 
                       center: Tuple[int, int], scale: float) -> Tuple[int, int, float]:
        """Project 3D point to 2D screen coordinates (legacy, for single points)."""
        x, y, z = point
        
        # Simple perspective projection
        fov = 300
        z_offset = 200
        
        if z + z_offset <= 0:
            return None
        
        factor = fov / (z + z_offset)
        screen_x = int(center[0] + x * factor * scale)
        screen_y = int(center[1] - y * factor * scale)
        
        return (screen_x, screen_y, z)
    
    def _lat_lng_to_3d(self, lat: float, lng: float) -> Tuple[float, float, float]:
        """Convert latitude/longitude to 3D coordinates on globe."""
        lat_rad = math.radians(lat)
        lng_rad = math.radians(lng)
        
        x = self.earth_radius * math.cos(lat_rad) * math.cos(lng_rad)
        y = self.earth_radius * math.sin(lat_rad)
        z = self.earth_radius * math.cos(lat_rad) * math.sin(lng_rad)
        
        return (x, y, z)
    
    # ==================== Globe Commands ====================
    
    def show_globe(self):
        """
        Show the holographic globe with Fortnite-style materialization effect.
        - Blue digital pixels appear and coalesce into the globe
        - Sci-fi sound plays during materialization
        - Globe starts facing user's location
        - User's location is highlighted and beeping
        """
        self.active_hologram = HologramType.GLOBE
        self.use_realistic_globe = False
        
        # Reset globe state but keep user location
        user_lat = self.globe_state.user_lat
        user_lng = self.globe_state.user_lng
        user_name = self.globe_state.user_location_name
        
        self.globe_state = GlobeState()
        self.globe_state.user_lat = user_lat
        self.globe_state.user_lng = user_lng
        self.globe_state.user_location_name = user_name
        
        # Start materialization effect
        self.globe_state.is_materializing = True
        self.globe_state.materialize_progress = 0.0
        self.globe_state.materialize_start_time = time.time()
        
        # Generate pixel particles for materialization
        self._generate_materialize_particles()
        
        # Set initial rotation to show USER'S LOCATION
        print(f"[AR] User location: ({user_lat}, {user_lng}) - {user_name}")
        
        # CORRECT ROTATION CALCULATION:
        # Texture mapping appears to be: 
        # Positive rotation -> Negative longitude
        # To show user_lng, we need rotation that maps to that longitude
        # Removing negation seems to fix the "Show Asia" issue for US locations
        
        self.globe_state.rotation_y = math.radians(user_lng)
        self.globe_state.rotation_x = math.radians(user_lat) * 0.15
        
        print(f"[AR] Initial rotation: y={math.degrees(self.globe_state.rotation_y):.1f}° (to show lng={user_lng})")
        
        # Also set target rotation to match
        self.globe_state.target_rotation_y = self.globe_state.rotation_y
        self.globe_state.target_rotation_x = self.globe_state.rotation_x
        
        # HIGHLIGHT USER'S CURRENT LOCATION on startup
        self.globe_state.target_lat = user_lat
        self.globe_state.target_lng = user_lng
        self.globe_state.highlighted_city = user_name  # Show user's location marker
        
        # Play materialization sound
        self._play_materialize_sound()
        
        # Start hologram ambient + location pulse while globe/map is active
        self._start_hologram_ambient()
        self._start_location_pulse()
        
        # Hide keyboard when showing globe (they overlap)
        self.show_holographic_keyboard = False
        
        # DISABLED: Separate window - render on camera feed only
        # if self.globe_window:
        #     self.globe_window.set_location(user_lat, user_lng, user_name)
        #     self.globe_window.show()
        
        print(f"[AR] Globe materializing at {user_name} ({user_lat}, {user_lng})")
        return "Holographic globe activated."
    
    def _generate_materialize_particles(self):
        """Generate blue pixel particles for materialization effect."""
        self.pixel_particles = []
        num_particles = 150
        
        for _ in range(num_particles):
            # Random position around globe area
            particle = {
                'x': random.uniform(-150, 150),
                'y': random.uniform(-150, 150),
                'z': random.uniform(-50, 50),
                'size': random.randint(2, 6),
                'speed': random.uniform(0.5, 2.0),
                'delay': random.uniform(0, 1.5),  # Staggered appearance
                'alpha': random.uniform(0.5, 1.0),
                'target_x': random.uniform(-80, 80),
                'target_y': random.uniform(-80, 80),
            }
            self.pixel_particles.append(particle)
    
    def hide_globe(self):
        """Hide the globe with sci-fi shutdown effect."""
        # Play shutdown sound
        self._play_ui_sound("shutdown")
        
        # Hide the globe
        self.active_hologram = HologramType.NONE
        self.city_view_active = False  # Also exit city view if active
        
        # Clear highlighted location
        self.globe_state.highlighted_city = None
        
        # DISABLED: Separate window - render on camera feed only
        # if self.globe_window:
        #     self.globe_window.hide()
        
        # Stop hologram-specific ambient sounds
        self._stop_hologram_ambient()
        self._stop_location_pulse()
        print("[AR] Globe hologram hidden")
        return "Globe hidden."

    def show_monica_next_to_me(self, intensity: float = 0.6) -> str:
        self.monica_in_frame_target = True
        try:
            self.monica_in_frame_intensity = float(intensity)
        except Exception:
            self.monica_in_frame_intensity = 0.6
        if self.monica_in_frame_intensity < 0.0:
            self.monica_in_frame_intensity = 0.0
        if self.monica_in_frame_intensity > 1.0:
            self.monica_in_frame_intensity = 1.0
        return ""

    def hide_monica_next_to_me(self) -> str:
        self.monica_in_frame_target = False
        return ""

    def _render_monica_in_frame(self, frame: np.ndarray) -> np.ndarray:
        h, w = frame.shape[:2]
        dt = 1.0 / 30.0
        try:
            dt = max(0.001, min(0.2, time.time() - self.last_update))
        except Exception:
            pass

        fade_speed = 2.2
        if self.monica_in_frame_target:
            self.monica_in_frame_alpha = min(1.0, self.monica_in_frame_alpha + dt * fade_speed)
        else:
            self.monica_in_frame_alpha = max(0.0, self.monica_in_frame_alpha - dt * fade_speed)

        if self.monica_in_frame_alpha <= 0.01:
            return frame

        x0 = int(w * 0.75)
        y0 = int(h * 0.35)
        face = getattr(self, 'last_face_location', None)
        try:
            if face and len(face) == 4:
                fx, fy, fw, fh = face
                x0 = min(w - 1, fx + fw + int(fw * 0.55))
                y0 = max(0, min(h - 1, fy + int(fh * 0.35)))
        except Exception:
            pass

        diameter = int(min(w, h) * (0.28 + 0.10 * self.monica_in_frame_intensity))
        radius = max(24, diameter // 2)
        x1 = max(0, x0 - radius)
        y1 = max(0, y0 - radius)
        x2 = min(w, x0 + radius)
        y2 = min(h, y0 + radius)

        roi = frame[y1:y2, x1:x2]
        if roi.size == 0:
            return frame

        rh, rw = roi.shape[:2]
        xs = np.linspace(-1.0, 1.0, rw, dtype=np.float32)
        ys = np.linspace(-1.0, 1.0, rh, dtype=np.float32)
        xv, yv = np.meshgrid(xs, ys)
        r = np.sqrt(xv * xv + yv * yv)
        softness = 0.22
        mask = 1.0 - np.clip((r - (1.0 - softness)) / max(softness, 1e-6), 0.0, 1.0)
        mask = (mask * mask).astype(np.float32)

        t = time.time()
        n1 = np.sin((xv * 5.0 + yv * 3.0) + t * 1.1)
        n2 = np.sin((xv * -4.0 + yv * 6.0) + t * 1.6)
        swirl = np.sin((np.arctan2(yv, xv) * 3.5) + (r * 9.0) - t * 1.4)
        noise = (0.5 * n1 + 0.35 * n2 + 0.35 * swirl).astype(np.float32)
        noise = (noise - noise.min()) / (noise.max() - noise.min() + 1e-6)
        noise_u8 = (noise * 255.0).astype(np.uint8)

        blur1 = cv2.GaussianBlur(noise_u8, (0, 0), sigmaX=6.0, sigmaY=6.0)
        blur2 = cv2.GaussianBlur(noise_u8, (0, 0), sigmaX=14.0, sigmaY=14.0)
        mist = cv2.addWeighted(blur1, 0.7, blur2, 0.3, 0)

        plasma = cv2.applyColorMap(mist, cv2.COLORMAP_TURBO)

        base_brightness = 0.75 + 0.35 * self.monica_in_frame_intensity
        pulse = 0.18 * math.sin(t * (2.8 + 2.0 * self.monica_in_frame_intensity))
        brightness = max(0.35, min(1.35, base_brightness + pulse))
        plasma_f = np.clip(plasma.astype(np.float32) * brightness, 0.0, 255.0).astype(np.uint8)

        alpha = self.monica_in_frame_alpha
        mask3 = (mask[..., None] * alpha).astype(np.float32)
        out = plasma_f.astype(np.float32) * mask3 + roi.astype(np.float32) * (1.0 - mask3)
        frame[y1:y2, x1:x2] = out.astype(np.uint8)
        return frame
    
    def highlight_location(self, query: str) -> str:
        """
        Highlight a location on the globe using accurate satellite data system.
        Called when user asks "where is X located?"
        
        Uses AccurateGeocoder which has:
        - 200+ verified locations (continents, countries, cities, landmarks)
        - OpenStreetMap Nominatim fallback
        - Caching for fast repeated lookups
        """
        if self.active_hologram != HologramType.GLOBE:
            self.show_globe()
        
        # FIRST: Try local cities database (instant, no network)
        query_lower = query.lower().strip()
        for key, data in self.cities.items():
            if key in query_lower or query_lower in key:
                self.globe_state.target_lat = data["lat"]
                self.globe_state.target_lng = data["lng"]
                self.globe_state.highlighted_city = data["name"]
                
                rot_x, rot_y = GlobeCoordinateSystem.rotation_to_show_location(
                    data["lat"], data["lng"]
                )
                self.globe_state.target_rotation_x = rot_x
                self.globe_state.target_rotation_y = rot_y
                self.globe_state.is_rotating_to_target = True
                self._play_ui_sound("highlight")
                
                print(f"[AR] Found {data['name']} in local database")
                return f"{data['name']} is in {data['country']}. Rotating globe to show it."
            if data["name"].lower() in query_lower or query_lower in data["name"].lower():
                self.globe_state.target_lat = data["lat"]
                self.globe_state.target_lng = data["lng"]
                self.globe_state.highlighted_city = data["name"]
                
                rot_x, rot_y = GlobeCoordinateSystem.rotation_to_show_location(
                    data["lat"], data["lng"]
                )
                self.globe_state.target_rotation_x = rot_x
                self.globe_state.target_rotation_y = rot_y
                self.globe_state.is_rotating_to_target = True
                self._play_ui_sound("highlight")
                
                print(f"[AR] Found {data['name']} in local database")
                return f"{data['name']} is in {data['country']}. Rotating globe to show it."
        
        # SECOND: Try geocoder (network call - may be slow)
        if HAS_SATELLITE_DATA:
            geocoder = get_geocoder()
            location = geocoder.geocode(query)
            
            if location:
                self.globe_state.target_lat = location.lat
                self.globe_state.target_lng = location.lng
                self.globe_state.highlighted_city = location.name
                
                # Use accurate rotation calculation
                rot_x, rot_y = GlobeCoordinateSystem.rotation_to_show_location(
                    location.lat, location.lng
                )
                
                # SET TARGET ROTATION for smooth animation
                # Globe will smoothly rotate to show this location
                self.globe_state.target_rotation_x = rot_x
                self.globe_state.target_rotation_y = rot_y
                self.globe_state.is_rotating_to_target = True
                
                # Play highlight sound
                self._play_ui_sound("highlight")
                
                print(f"[AR] Highlighting {location.name} at ({location.lat:.4f}, {location.lng:.4f})")
                print(f"[AR] Target rotation: x={math.degrees(rot_x):.1f}°, y={math.degrees(rot_y):.1f}°")
                
                if location.country:
                    return f"{location.name} is in {location.country}. Rotating globe to show it."
                else:
                    return f"Found {location.name}. Rotating globe to show it."
            else:
                return f"I couldn't find '{query}' on the map. Try a city, country, or landmark name."
        
        # Fallback to old method if satellite data not available
        query_lower = query.lower().strip()
        city = None
        
        for key, data in self.cities.items():
            if key in query_lower or query_lower in key:
                city = data
                break
            if data["name"].lower() in query_lower or query_lower in data["name"].lower():
                city = data
                break
        
        if city:
            self.globe_state.target_lat = city["lat"]
            self.globe_state.target_lng = city["lng"]
            self.globe_state.highlighted_city = city["name"]
            self.globe_state.rotation_y = -math.radians(city["lng"])
            self.globe_state.rotation_x = math.radians(city["lat"]) * 0.5
            
            print(f"[AR] Highlighting {city['name']} at ({city['lat']}, {city['lng']})")
            return f"{city['name']} is located in {city['country']}. I'm highlighting it on the globe."
        else:
            return self._geocode_and_highlight(query)
    
    def _geocode_and_highlight(self, query: str) -> str:
        """
        Use geocoding API to find location with improved accuracy.
        Uses OpenStreetMap Nominatim for free, accurate geocoding.
        """
        # Clean up the query - remove common filler words
        query_clean = query.lower().strip()
        filler_words = ['the', 'a', 'an', 'in', 'on', 'at', 'to', 'me', 'please', 'can you', 'show']
        for word in filler_words:
            query_clean = query_clean.replace(word + ' ', '')
        query_clean = query_clean.strip()
        
        # Handle continent/region names specially
        region_coords = {
            'south america': (-14.235, -51.925, 'South America'),
            'north america': (37.09, -95.71, 'North America'),
            'europe': (48.86, 2.35, 'Europe'),
            'africa': (-1.29, 36.82, 'Africa'),  # Nairobi area
            'asia': (35.68, 139.69, 'Asia'),
            'australia': (-25.27, 133.78, 'Australia'),
            'antarctica': (-82.86, 135.0, 'Antarctica'),
            'middle east': (25.28, 51.53, 'Middle East'),
            'brazil': (-15.79, -47.88, 'Brazil'),  # Brasilia
            'nairobi': (-1.2921, 36.8219, 'Nairobi, Kenya'),
            'kenya': (-1.2921, 36.8219, 'Kenya'),
        }
        
        # Check for region match first
        for region, (lat, lng, name) in region_coords.items():
            if region in query_clean:
                self.globe_state.target_lat = lat
                self.globe_state.target_lng = lng
                self.globe_state.highlighted_city = name
                # FIXED: Correct rotation calculation
                # Longitude: negative to rotate globe so location faces camera
                # The globe rotates around Y axis, so we need to bring the longitude to front
                self.globe_state.rotation_y = math.radians(-lng)
                self.globe_state.rotation_x = math.radians(lat) * 0.3
                print(f"[AR] Found region {name} at ({lat}, {lng})")
                return f"I found {name}. Highlighting it on the globe."
        
        try:
            # Use Nominatim with better parameters
            response = requests.get(
                "https://nominatim.openstreetmap.org/search",
                params={
                    "q": query_clean,
                    "format": "json",
                    "limit": 1,
                    "addressdetails": 1,
                    "accept-language": "en"
                },
                headers={"User-Agent": "MonicaAI/1.0 (Educational Project)"},
                timeout=10
            )
            data = response.json()
            
            if data:
                result = data[0]
                lat = float(result["lat"])
                lng = float(result["lon"])
                
                # Get a cleaner name
                if "address" in result:
                    addr = result["address"]
                    name = addr.get("city") or addr.get("town") or addr.get("country") or result["display_name"].split(",")[0]
                else:
                    name = result["display_name"].split(",")[0]
                
                self.globe_state.target_lat = lat
                self.globe_state.target_lng = lng
                self.globe_state.highlighted_city = name
                
                # FIXED: Correct rotation to face the location
                # Rotate globe so the longitude is at the front (facing camera)
                self.globe_state.rotation_y = math.radians(-lng)
                self.globe_state.rotation_x = math.radians(lat) * 0.3
                
                print(f"[AR] Geocoded '{query}' -> {name} at ({lat}, {lng})")
                return f"I found {name}. Highlighting it on the globe."
            else:
                print(f"[AR] No results for '{query}'")
                return f"I couldn't find {query} on the map. Try being more specific."
        except Exception as e:
            print(f"[AR] Geocoding error: {e}")
            return f"I had trouble finding {query}. Please try again."
    
    def zoom_in(self) -> str:
        """Zoom into the globe."""
        if self.active_hologram == HologramType.GLOBE:
            self.globe_state.zoom = min(3.0, self.globe_state.zoom + 0.5)
            self._play_ui_sound("zoom")
            print(f"[AR] Globe zoom: {self.globe_state.zoom}")
            return "Zooming in."
        return "No globe to zoom."
    
    def zoom_out(self) -> str:
        """Zoom out of the globe."""
        if self.active_hologram == HologramType.GLOBE:
            self.globe_state.zoom = max(0.5, self.globe_state.zoom - 0.5)
            self._play_ui_sound("zoom")
            print(f"[AR] Globe zoom: {self.globe_state.zoom}")
            return "Zooming out."
        return "No globe to zoom."
    
    def zoom_to_city_level(self, location: str = None) -> str:
        """
        Zoom to city/street level - shows a holographic map window.
        Replaces the globe with a detailed map view.
        """
        # Use current highlighted location if none provided
        if location is None:
            if self.globe_state.highlighted_city:
                lat = self.globe_state.target_lat
                lng = self.globe_state.target_lng
                name = self.globe_state.highlighted_city
            else:
                lat = self.globe_state.user_lat
                lng = self.globe_state.user_lng
                name = self.globe_state.user_location_name
        else:
            # Geocode the location
            if HAS_SATELLITE_DATA:
                geocoder = get_geocoder()
                loc = geocoder.geocode(location)
                if loc:
                    lat, lng, name = loc.lat, loc.lng, loc.name
                else:
                    return f"Couldn't find {location} for city view."
            else:
                return "Location services not available."
        
        # Activate city view mode
        self.city_view_active = True
        self.city_view_lat = lat
        self.city_view_lng = lng
        self.city_view_location = name
        self.city_view_zoom = 15  # Street level zoom
        
        # Play zoom sound
        self._play_ui_sound("zoom")
        
        print(f"[AR] City view: {name} ({lat}, {lng})")
        return f"Zooming to city level at {name}. Showing map view."
    
    def show_map_view(self, location: str) -> str:
        """
        Show a holographic map view of a location.
        Globe goes away, map appears. Globe returns when map is closed. CRASH-SAFE.
        """
        try:
            # Geocode the location
            lat, lng, name = None, None, location
            if HAS_SATELLITE_DATA:
                geocoder = get_geocoder()
                loc = geocoder.geocode(location)
                if loc:
                    lat, lng, name = loc.lat, loc.lng, loc.name
                else:
                    return f"Couldn't find {location} for map view."
            else:
                # Fallback - try to find in cities dict
                city = self.cities.get(location.lower())
                if city:
                    lat, lng = city.get('lat', 40.7128), city.get('lng', -74.006)
                    name = location.title()
                else:
                    return "Location services not available."
            
            # Store globe state so we can return to it
            if hasattr(self, 'globe_state') and self.globe_state:
                self._saved_globe_state = {
                    'rotation_y': getattr(self.globe_state, 'rotation_y', 0),
                    'rotation_x': getattr(self.globe_state, 'rotation_x', 0),
                    'highlighted_city': getattr(self.globe_state, 'highlighted_city', None),
                }
            
            # Fetch city map image BEFORE activating city view
            try:
                if self.free_maps:
                    self.city_view_image = self.free_maps.get_city_map(lat, lng, zoom=14)
                elif self.google_maps:
                    self.city_view_image = self.google_maps.get_city_map(lat, lng, zoom=14)
            except Exception as e:
                print(f"[AR] Could not fetch map: {e}")
                self.city_view_image = None
            
            # Activate map view mode (replaces globe)
            self.city_view_active = True
            self.city_view_lat = lat
            self.city_view_lng = lng
            self.city_view_location = (lat, lng, name)
            self.city_view_zoom = 14  # City level zoom
            
            print(f"[AR] Map view: {name} ({lat}, {lng})")
            return f"Showing map of {name}. Say 'close map' to return to globe."
        except Exception as e:
            print(f"[AR] Map view error (safe): {e}")
            return f"Showing map of {location}."
    
    def close_map_view(self) -> str:
        """Close the map view and return to globe."""
        if self.city_view_active:
            self.city_view_active = False
            
            # Restore globe state if saved
            if hasattr(self, '_saved_globe_state') and self._saved_globe_state:
                self.globe_state.rotation_y = self._saved_globe_state['rotation_y']
                self.globe_state.rotation_x = self._saved_globe_state['rotation_x']
                self.globe_state.highlighted_city = self._saved_globe_state['highlighted_city']
            
            self._play_ui_sound("close")
            print("[AR] Map view closed, returning to globe")
            return "Map closed. Returning to globe view."
        return "No map view is currently open."
    
    def highlight_landmass(self, region: str) -> str:
        """
        Highlight an entire landmass/continent on the globe.
        The region glows with a pulsing effect.
        """
        from monica_realistic_globe import REGION_BOUNDS
        
        region_lower = region.lower().strip()
        
        if region_lower not in REGION_BOUNDS:
            return f"I don't have bounds for '{region}'. Try: Africa, Europe, Asia, North America, South America, Australia, Antarctica."
        
        # Show globe if not visible
        if self.active_hologram != HologramType.GLOBE:
            self.show_globe()
        
        # Get region bounds
        bounds = REGION_BOUNDS[region_lower]
        
        # Store the highlighted region
        self.globe_state.highlighted_region = region_lower
        self.globe_state.highlighted_region_bounds = bounds
        
        # Rotate globe to show the region
        center_lat = (bounds['lat_min'] + bounds['lat_max']) / 2
        center_lng = (bounds['lng_min'] + bounds['lng_max']) / 2
        
        # Set target rotation
        self.globe_state.target_rotation_y = -math.radians(center_lng)
        self.globe_state.target_rotation_x = math.radians(center_lat) * 0.15
        self.globe_state.is_rotating_to_target = True
        
        # Clear city highlight (we're highlighting a region now)
        self.globe_state.highlighted_city = None
        
        self._play_ui_sound("highlight")
        print(f"[AR] Highlighting landmass: {bounds['name']}")
        return f"Highlighting {bounds['name']} on the globe."
    
    def rotate_globe(self, direction: str) -> str:
        """Rotate the globe in a direction."""
        if self.active_hologram != HologramType.GLOBE:
            return "No globe to rotate."
        
        rotation_amount = 0.3
        if "left" in direction:
            self.globe_state.rotation_y -= rotation_amount
        elif "right" in direction:
            self.globe_state.rotation_y += rotation_amount
        elif "up" in direction:
            self.globe_state.rotation_x -= rotation_amount
        elif "down" in direction:
            self.globe_state.rotation_x += rotation_amount
        
        # Explicit rotation - trigger turn sound as feedback
        self._maybe_play_globe_turn_sound()
        return f"Rotating globe {direction}."
    
    # ==================== Hologram Position Control ====================
    
    def move_hologram(self, direction: str) -> str:
        """
        Move the hologram position in the specified direction.
        
        Args:
            direction: "up", "down", "left", "right"
        """
        direction = direction.lower()
        
        if "up" in direction:
            self.hologram_position_offset_y -= self.position_step
            return "Moving hologram up."
        elif "down" in direction:
            self.hologram_position_offset_y += self.position_step
            return "Moving hologram down."
        elif "left" in direction:
            self.hologram_position_offset_x -= self.position_step
            return "Moving hologram left."
        elif "right" in direction:
            self.hologram_position_offset_x += self.position_step
            return "Moving hologram right."
        else:
            return "Unknown direction. Try up, down, left, or right."
    
    def tilt_hologram(self, direction: str) -> str:
        """
        Tilt/rotate the hologram to adjust its orientation.
        
        Args:
            direction: "left" (counter-clockwise), "right" (clockwise), "upright" (reset)
        """
        direction = direction.lower()
        tilt_amount = 5  # degrees per command
        
        if "upright" in direction or "straight" in direction or "reset" in direction:
            self.hologram_rotation = 0
            return "Hologram set upright."
        elif "left" in direction or "counter" in direction:
            self.hologram_rotation -= tilt_amount
            return f"Tilting hologram left. Current angle: {self.hologram_rotation}°"
        elif "right" in direction or "clockwise" in direction:
            self.hologram_rotation += tilt_amount
            return f"Tilting hologram right. Current angle: {self.hologram_rotation}°"
        else:
            return "Unknown tilt direction. Try left, right, or upright."
    
    def set_hologram_position(self, position: str) -> str:
        """
        Set the hologram to a preset position.
        
        Args:
            position: "left", "right", "center"
        """
        position = position.lower()
        
        if "left" in position:
            self.hologram_position = "left"
            self.hologram_position_offset_x = 0
            self.hologram_position_offset_y = 0
            return "Hologram moved to left side."
        elif "right" in position:
            self.hologram_position = "right"
            self.hologram_position_offset_x = 0
            self.hologram_position_offset_y = 0
            return "Hologram moved to right side."
        elif "center" in position or "middle" in position:
            self.hologram_position = "center"
            self.hologram_position_offset_x = 0
            self.hologram_position_offset_y = 0
            return "Hologram moved to center."
        else:
            return "Unknown position. Try left, right, or center."
    
    def resize_hologram(self, direction: str) -> str:
        """
        Resize the hologram (make it bigger or smaller).
        
        Args:
            direction: "bigger", "smaller"
        """
        direction = direction.lower()
        
        if "bigger" in direction or "larger" in direction or "increase" in direction:
            self.hologram_scale = min(0.8, self.hologram_scale + 0.05)
            return f"Hologram enlarged. Size: {int(self.hologram_scale * 100)}%"
        elif "smaller" in direction or "decrease" in direction or "reduce" in direction:
            self.hologram_scale = max(0.2, self.hologram_scale - 0.05)
            return f"Hologram reduced. Size: {int(self.hologram_scale * 100)}%"
        else:
            return "Unknown size direction. Try bigger or smaller."
    
    def reset_hologram_position(self) -> str:
        """Reset hologram to default position and orientation."""
        self.hologram_position = "left"
        self.hologram_position_offset_x = 0
        self.hologram_position_offset_y = 0
        self.hologram_rotation = 0
        self.hologram_scale = 0.45
        return "Hologram position reset to default."
    
    def fix_hologram_position(self) -> str:
        """Alias for reset - 'fix the position' command."""
        return self.reset_hologram_position()
    
    def search_poi(self, poi_type: str) -> str:
        """
        Search for Points of Interest (stores, schools, etc.) near current location.
        Uses OpenStreetMap Overpass API (free). CRASH-SAFE.
        
        Args:
            poi_type: "store", "school", "restaurant", "hospital", etc.
        """
        try:
            # Get current location (highlighted or user location)
            if hasattr(self, 'globe_state') and self.globe_state and self.globe_state.highlighted_city:
                lat = getattr(self.globe_state, 'target_lat', 40.7128)
                lng = getattr(self.globe_state, 'target_lng', -74.006)
                location_name = self.globe_state.highlighted_city
            else:
                lat = getattr(self.globe_state, 'user_lat', 40.7128) if hasattr(self, 'globe_state') else 40.7128
                lng = getattr(self.globe_state, 'user_lng', -74.006) if hasattr(self, 'globe_state') else -74.006
                location_name = getattr(self.globe_state, 'user_location_name', 'your area') if hasattr(self, 'globe_state') else 'your area'
            
            # Map POI types to OSM tags
            poi_tags = {
                "store": "shop",
                "shop": "shop",
                "school": "amenity=school",
                "restaurant": "amenity=restaurant",
                "hospital": "amenity=hospital",
                "pharmacy": "amenity=pharmacy",
                "bank": "amenity=bank",
                "gas": "amenity=fuel",
                "hotel": "tourism=hotel",
                "park": "leisure=park",
            }
            
            osm_tag = poi_tags.get(poi_type, f"amenity={poi_type}")
            
            # Store POI search state for rendering
            self.poi_search_active = True
            self.poi_search_type = poi_type
            self.poi_search_lat = lat
            self.poi_search_lng = lng
            
            # Fetch city map image BEFORE activating city view
            try:
                if self.free_maps:
                    self.city_view_image = self.free_maps.get_city_map(lat, lng, zoom=15)
                elif self.google_maps:
                    self.city_view_image = self.google_maps.get_city_map(lat, lng, zoom=15)
            except Exception as e:
                print(f"[AR] Could not fetch map: {e}")
                self.city_view_image = None
            
            # Zoom to city level to show POIs
            self.city_view_active = True
            self.city_view_lat = lat
            self.city_view_lng = lng
            self.city_view_location = (lat, lng, location_name)
            self.city_view_zoom = 15
            
            print(f"[AR] Searching for {poi_type} near {location_name}")
            return f"Searching for {poi_type}s near {location_name}. Showing map view."
        except Exception as e:
            print(f"[AR] POI search error (safe): {e}")
            return f"Searching for {poi_type}s..."
    
    # ==================== Webcam Window Commands ====================
    
    def show_webcam_feed(self, location: str = None, feeds: List[Dict] = None) -> str:
        """
        Show webcam feed window, replacing the globe.
        If location is provided, search for webcams near that location.
        """
        self.active_hologram = HologramType.WEBCAM_WINDOW
        
        # If location provided, search webcam network
        if location and HAS_WEBCAM_NETWORK:
            webcam_network = get_webcam_network()
            search_results = webcam_network.search_webcams(location)
            if search_results:
                feeds = search_results
                print(f"[AR] Found {len(feeds)} webcams for '{location}'")
            else:
                # Try to find nearest webcam to the location
                city = self.cities.get(location.lower())
                if city:
                    nearest_id = webcam_network.find_nearest_webcam(city["lat"], city["lng"])
                    if nearest_id:
                        nearest = webcam_network.get_webcam(nearest_id)
                        if nearest:
                            feeds = [{"id": nearest_id, **nearest}]
        
        if feeds:
            self.webcam_state.feed_list = feeds
            self.webcam_state.current_index = 0
            self._load_webcam_feed(feeds[0])
            feed_name = feeds[0].get('name', 'webcam')
            print(f"[AR] Webcam window activated: {feed_name}")
            return f"Showing live feed from {feed_name}."
        elif HAS_WEBCAM_NETWORK:
            # Show all available webcams if no specific location
            webcam_network = get_webcam_network()
            all_webcams = [{"id": wid, **w} for wid, w in webcam_network.webcams.items()]
            if all_webcams:
                self.webcam_state.feed_list = all_webcams[:20]  # Limit to 20
                self.webcam_state.current_index = 0
                self._load_webcam_feed(all_webcams[0])
                return f"Showing live feed from {all_webcams[0].get('name', 'webcam')}. Say 'next' to switch feeds."
        
        print("[AR] Webcam window activated (no feeds)")
        return "Webcam window opened but no feeds available."
    
    def _load_webcam_feed(self, feed: Dict):
        """Load a webcam feed in background thread."""
        self.webcam_state.is_loading = True
        self.webcam_state.current_feed_name = feed.get("name", "Unknown")
        self.webcam_state.current_feed_url = feed.get("url", "")
        
        # Start loading thread
        self.webcam_stop_event.clear()
        self.webcam_thread = threading.Thread(target=self._webcam_loader, daemon=True)
        self.webcam_thread.start()
    
    def _webcam_loader(self):
        """Background thread to load webcam frames."""
        url = self.webcam_state.current_feed_url
        if not url:
            return
        
        try:
            cap = cv2.VideoCapture(url)
            while not self.webcam_stop_event.is_set():
                ret, frame = cap.read()
                if ret:
                    self.webcam_state.frame = frame
                    self.webcam_state.is_loading = False
                time.sleep(0.033)  # ~30 FPS
            cap.release()
        except Exception as e:
            print(f"[AR] Webcam error: {e}")
            self.webcam_state.is_loading = False
    
    def next_webcam(self) -> str:
        """Switch to next webcam feed."""
        if self.active_hologram != HologramType.WEBCAM_WINDOW:
            return "No webcam window open."
        
        if self.webcam_state.feed_list:
            self.webcam_state.current_index = (self.webcam_state.current_index + 1) % len(self.webcam_state.feed_list)
            feed = self.webcam_state.feed_list[self.webcam_state.current_index]
            self.webcam_stop_event.set()
            time.sleep(0.1)
            self._load_webcam_feed(feed)
            return f"Switching to {feed.get('name', 'next feed')}."
        return "No more feeds available."
    
    def previous_webcam(self) -> str:
        """Switch to previous webcam feed."""
        if self.active_hologram != HologramType.WEBCAM_WINDOW:
            return "No webcam window open."
        
        if self.webcam_state.feed_list:
            self.webcam_state.current_index = (self.webcam_state.current_index - 1) % len(self.webcam_state.feed_list)
            feed = self.webcam_state.feed_list[self.webcam_state.current_index]
            self.webcam_stop_event.set()
            time.sleep(0.1)
            self._load_webcam_feed(feed)
            return f"Switching to {feed.get('name', 'previous feed')}."
        return "No more feeds available."
    
    def close_webcam_window(self) -> str:
        """Close webcam window and return to globe."""
        if self.active_hologram == HologramType.WEBCAM_WINDOW:
            self.webcam_stop_event.set()
            self.active_hologram = HologramType.GLOBE
            return "Closing webcam window and returning to globe."
        return "No webcam window to close."
    
    def return_to_globe(self) -> str:
        """Return to globe view from any hologram or city view."""
        self.webcam_stop_event.set()
        self.active_hologram = HologramType.GLOBE
        
        # Exit city view if active
        if self.city_view_active:
            self.city_view_active = False
            self.city_view_location = None
            if self.google_maps:
                self.google_maps.exit_city_view()
            return "Returning to globe from city view."
        
        return "Returning to globe."
    
    # ==================== Rendering ====================
    
    def render_overlay(self, frame: np.ndarray) -> np.ndarray:
        """
        Render the active hologram onto the camera frame.
        
        PERFORMANCE OPTIMIZATIONS:
        - Frame skipping: Only re-render every N frames
        - Cached overlay: Reuse last render between frames
        - Early exit: Skip if no hologram active
        
        Args:
            frame: BGR camera frame
            
        Returns:
            Frame with hologram overlay
        """
        # OPTIMIZATION: Early exit if no hologram
        if self.active_hologram == HologramType.NONE:
            return frame
        
        # OPTIMIZATION: Frame skipping with cached overlay
        # BUT: Don't skip during materialization (need smooth animation)
        self.frame_counter += 1
        frame_shape = frame.shape[:2]
        
        is_animating = (
            self.active_hologram == HologramType.GLOBE and 
            (self.globe_state.is_materializing or self.globe_state.is_rotating_to_target)
        )
        
        # Check if we should use cached overlay
        use_cache = (
            self.cached_overlay is not None and
            self.last_frame_shape == frame_shape and
            self.frame_counter % self.render_every_n_frames != 0 and
            not is_animating  # Don't cache during materialization
        )
        
        if use_cache:
            # Blend cached overlay onto current frame (fast operation)
            # This keeps the hologram visible while skipping expensive re-render
            return self._apply_cached_overlay(frame)
        
        # Update animation time
        current_time = time.time()
        dt = current_time - self.last_update
        self.last_update = current_time
        self.animation_time += dt
        
        # Update materialization progress
        if self.globe_state.is_materializing:
            # Materialize over 1.5 seconds
            self.globe_state.materialize_progress += dt / 1.5
            if self.globe_state.materialize_progress >= 1.0:
                self.globe_state.materialize_progress = 1.0
                self.globe_state.is_materializing = False
                print("[AR] Globe materialization complete")
        
        # Render new overlay
        if self.active_hologram == HologramType.GLOBE:
            # Check if in city view mode
            if self.city_view_active:
                frame = self._render_city_view(frame)
            elif self.use_realistic_globe and self.realistic_globe:
                # Use realistic satellite globe (accurate, filled)
                frame = self._render_realistic_globe(frame)
            else:
                # Fallback to wireframe hologram
                frame = self._render_globe_optimized(frame)
        elif self.active_hologram == HologramType.WEBCAM_WINDOW:
            frame = self._render_webcam_window(frame)
        elif self.active_hologram == HologramType.RESEARCH_WINDOW:
            # Render Matrix-style research window
            if HAS_RESEARCH_SYSTEM:
                research_window = get_research_window()
                frame = research_window.render(frame)
        
        # Always render holographic keyboard if enabled
        if self.show_holographic_keyboard:
            frame = self._render_holographic_keyboard(frame)
        
        # Render alarm effect if active (red blinking)
        frame = self.render_alarm_effect(frame)
        
        # Render Monica's presence next to user if active
        frame = self.render_monica_presence(frame)

        try:
            if self.monica_in_frame_target or self.monica_in_frame_alpha > 0.01:
                frame = self._render_monica_in_frame(frame)
        except Exception:
            pass
        
        # DON'T render orb in camera feed - it has its own green screen window for OBS
        # This reduces lag and lets user capture orb separately
        # if self.orb_window and hasattr(self.orb_window, 'state'):
        #     from monica_orb_window import OrbState
        #     if self.orb_window.state != OrbState.HIDDEN:
        #         frame = self._render_orb_in_frame(frame)
        
        # Cache this frame's overlay info
        self.last_frame_shape = frame_shape
        self.cached_overlay = frame.copy()
        
        return frame
    
    def _apply_cached_overlay(self, frame: np.ndarray) -> np.ndarray:
        """
        Apply cached overlay to current frame.
        Fast operation - just copies the hologram region.
        """
        if self.cached_overlay is None:
            return frame
        
        # For now, just return the cached frame
        # In future, could do region-based blending for even better perf
        return self.cached_overlay
    
    def _render_realistic_globe(self, frame: np.ndarray) -> np.ndarray:
        """
        Render the realistic satellite globe.
        Uses ESRI satellite imagery - scientifically accurate and updated.
        """
        if not self.realistic_globe:
            return self._render_globe_optimized(frame)
        
        h, w = frame.shape[:2]
        # Keep a copy of the original camera frame so we can blend
        base_frame = frame.copy()
        
        # Calculate position and size WITH ZOOM
        base_size = int(min(w, h) * self.hologram_scale)
        hologram_size = int(base_size * self.globe_state.zoom)  # Apply zoom!
        radius = hologram_size // 2
        
        # Get position offsets
        offset_x = getattr(self, 'hologram_position_offset_x', 0)
        offset_y = getattr(self, 'hologram_position_offset_y', 0)
        
        if self.hologram_position == "right":
            center_x = w - hologram_size // 2 - 50 + offset_x
        elif self.hologram_position == "left":
            center_x = hologram_size // 2 + 50 + offset_x
        else:
            center_x = w // 2 + offset_x
        
        center_y = h // 2 + offset_y
        
        # SMOOTH ROTATION ANIMATION
        # If rotating to a target location, smoothly interpolate
        if self.globe_state.is_rotating_to_target:
            # Calculate difference to target
            diff_x = self.globe_state.target_rotation_x - self.globe_state.rotation_x
            diff_y = self.globe_state.target_rotation_y - self.globe_state.rotation_y
            
            # Handle wraparound for Y rotation (longitude)
            # Normalize diff_y to be between -pi and pi
            while diff_y > math.pi:
                diff_y -= 2 * math.pi
            while diff_y < -math.pi:
                diff_y += 2 * math.pi
            
            # INSTANT rotation - jump directly to target for fast response
            speed = 0.5  # Very fast - reaches target in ~6 frames
            self.globe_state.rotation_x += diff_x * speed
            self.globe_state.rotation_y += diff_y * speed
            
            # Check if we've reached the target (close enough)
            if abs(diff_x) < 0.1 and abs(diff_y) < 0.1:
                self.globe_state.rotation_x = self.globe_state.target_rotation_x
                self.globe_state.rotation_y = self.globe_state.target_rotation_y
                self.globe_state.is_rotating_to_target = False
                print("[AR] Globe rotation complete - staying on location")
        elif self.globe_state.highlighted_city:
            # STAY on highlighted location - NO spinning when location is shown
            pass
        else:
            # Gentle idle rotation ONLY when no location is highlighted
            self.globe_state.rotation_y += 0.003

        # Play subtle globe turn sound while globe is rotating
        self._maybe_play_globe_turn_sound()
        
        # Sync rotation with realistic globe renderer
        self.realistic_globe.rotation_y = self.globe_state.rotation_y
        self.realistic_globe.rotation_x = self.globe_state.rotation_x
        
        # Render the realistic globe onto a hologram overlay instead of directly on the camera
        # This lets us apply a blue glow and then blend with the live frame.
        # Handle materialization transparency
        original_transparency = getattr(self.realistic_globe.config, 'transparency', 0.85)
        if self.globe_state.is_materializing:
            # Fade in from 0 to original_transparency
            current_transparency = original_transparency * self.globe_state.materialize_progress
            self.realistic_globe.config.transparency = current_transparency
        
        # Start from a black overlay so the globe is purely holographic
        overlay = np.zeros_like(frame)
        overlay = self.realistic_globe.render(overlay, (center_x, center_y), radius)
        
        # Render user's location with pulsing marker (auto-detected)
        if self.globe_state.user_lat and self.globe_state.user_lng:
            overlay = self.realistic_globe.render_location_marker(
                overlay, (center_x, center_y), radius,
                self.globe_state.user_lat, self.globe_state.user_lng,
                label=self.globe_state.user_location_name,
                pulse=True
            )
        
        # Render highlighted city if different from user location
        if (self.globe_state.highlighted_city and 
            self.globe_state.highlighted_city != self.globe_state.user_location_name):
            overlay = self.realistic_globe.render_location_marker(
                overlay, (center_x, center_y), radius,
                self.globe_state.target_lat, self.globe_state.target_lng,
                label=self.globe_state.highlighted_city,
                pulse=True
            )
        
        # Render highlighted landmass/region if set
        if self.globe_state.highlighted_region and self.globe_state.highlighted_region_bounds:
            overlay = self.realistic_globe.render_landmass_highlight(
                overlay, (center_x, center_y), radius,
                self.globe_state.highlighted_region_bounds
            )
        
        # Render weather patterns and lightning if enabled, on top of the hologram
        if self.globe_state.show_weather or self.globe_state.show_lightning:
            overlay = self._render_weather_overlay(overlay, (center_x, center_y), radius)
        
        # Render materialization particles into the hologram overlay
        if self.globe_state.is_materializing:
            # Restore original transparency for future frames
            self.realistic_globe.config.transparency = original_transparency
            overlay = self._render_materialize_particles(overlay, (center_x, center_y), hologram_size)
        
        # Add title and attribution into the hologram so they also get a subtle glow
        title = "EARTH - LIVE SATELLITE"
        title_size = cv2.getTextSize(title, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
        title_x = center_x - title_size[0] // 2
        title_y = center_y - radius - 10
        cv2.putText(overlay, title, (title_x, title_y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 200, 255), 1)
        
        attr = "Source: NASA Blue Marble"
        cv2.putText(overlay, attr, (center_x - 70, center_y + radius + 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.35, (150, 150, 150), 1)
        
        # Apply a blue glow to the hologram overlay, then blend strongly over the camera feed
        glow = cv2.GaussianBlur(overlay, (0, 0), sigmaX=18, sigmaY=18)
        hologram = cv2.addWeighted(glow, 0.6, overlay, 1.0, 0)
        frame = cv2.addWeighted(hologram, 0.9, base_frame, 0.1, 0)
        
        return frame
    
    def _render_materialize_particles(self, frame: np.ndarray, center: Tuple[int, int], size: int) -> np.ndarray:
        """
        Render Fortnite-style blue digital pixel particles during materialization.
        Particles converge from random positions toward the globe center.
        """
        progress = self.globe_state.materialize_progress
        
        for particle in self.pixel_particles:
            # Check if particle should be visible yet (staggered appearance)
            if progress < particle['delay'] / self.materialize_duration:
                continue
            
            # Calculate particle position (moving toward center)
            local_progress = min(1.0, (progress - particle['delay'] / self.materialize_duration) * 2)
            
            # Interpolate from start position to target
            start_x = particle['x']
            start_y = particle['y']
            target_x = particle['target_x']
            target_y = particle['target_y']
            
            # Ease-in-out interpolation
            t = local_progress
            ease_t = t * t * (3 - 2 * t)  # Smoothstep
            
            current_x = int(center[0] + start_x + (target_x - start_x) * ease_t)
            current_y = int(center[1] + start_y + (target_y - start_y) * ease_t)
            
            # Particle size decreases as it approaches target
            current_size = max(1, int(particle['size'] * (1 - ease_t * 0.7)))
            
            # Blue digital color with some variation
            blue_intensity = int(200 + random.randint(-30, 55))
            cyan_intensity = int(255 * particle['alpha'])
            color = (blue_intensity, cyan_intensity, cyan_intensity)  # Cyan-blue
            
            # Draw pixel particle (square for digital look)
            if 0 <= current_x < frame.shape[1] and 0 <= current_y < frame.shape[0]:
                # Main pixel
                cv2.rectangle(frame, 
                             (current_x - current_size, current_y - current_size),
                             (current_x + current_size, current_y + current_size),
                             color, -1)
                
                # Glow effect
                if current_size > 2 and random.random() > 0.7:
                    cv2.rectangle(frame,
                                 (current_x - current_size - 1, current_y - current_size - 1),
                                 (current_x + current_size + 1, current_y + current_size + 1),
                                 (blue_intensity // 2, cyan_intensity // 2, cyan_intensity // 2), 1)
        
        # Add some random sparkle particles
        if progress < 0.9:
            for _ in range(5):
                spark_x = center[0] + random.randint(-size//2, size//2)
                spark_y = center[1] + random.randint(-size//2, size//2)
                spark_size = random.randint(1, 3)
                cv2.rectangle(frame,
                             (spark_x, spark_y),
                             (spark_x + spark_size, spark_y + spark_size),
                             (255, 255, 255), -1)
        
        return frame
    
    def _render_weather_overlay(self, frame: np.ndarray, center: Tuple[int, int], radius: int) -> np.ndarray:
        """
        Render global weather patterns with clouds and lightning on the globe.
        Uses simulated storm systems at realistic locations.
        """
        import time as time_module
        
        # Major storm/weather zones (lat, lng, intensity, name)
        # These represent typical storm-prone regions
        storm_zones = [
            # Atlantic Hurricane Zone
            (25.0, -75.0, 0.9, "Atlantic"),
            (18.0, -65.0, 0.7, "Caribbean"),
            # Pacific Typhoon Zone
            (20.0, 130.0, 0.85, "W. Pacific"),
            (15.0, 145.0, 0.6, "Mariana"),
            # Indian Ocean Cyclone Zone
            (12.0, 85.0, 0.7, "Bay of Bengal"),
            (-15.0, 65.0, 0.5, "Indian Ocean"),
            # Tornado Alley
            (35.0, -98.0, 0.8, "Tornado Alley"),
            # European Storms
            (55.0, -10.0, 0.6, "N. Atlantic"),
            # African ITCZ
            (8.0, 20.0, 0.5, "ITCZ Africa"),
            # South American
            (-25.0, -55.0, 0.6, "S. America"),
            # Australian
            (-20.0, 140.0, 0.5, "Australia"),
        ]
        
        current_time = time_module.time()
        
        for lat, lng, intensity, name in storm_zones:
            # Convert to 3D and project
            lat_rad = math.radians(lat)
            lng_rad = math.radians(lng)
            
            # 3D position on sphere
            x = radius * math.cos(lat_rad) * math.sin(lng_rad)
            y = radius * math.sin(lat_rad)
            z = radius * math.cos(lat_rad) * math.cos(lng_rad)
            
            # Apply globe rotation
            rot_y = self.globe_state.rotation_y
            rot_x = self.globe_state.rotation_x
            
            # Rotate around Y axis
            x2 = x * math.cos(rot_y) + z * math.sin(rot_y)
            z2 = -x * math.sin(rot_y) + z * math.cos(rot_y)
            
            # Rotate around X axis
            y2 = y * math.cos(rot_x) - z2 * math.sin(rot_x)
            z3 = y * math.sin(rot_x) + z2 * math.cos(rot_x)
            
            # Only render if on visible side
            if z3 < -radius * 0.1:
                continue
            
            # Project to 2D
            px = center[0] + int(x2)
            py = center[1] - int(y2)
            
            # Pulsing cloud effect
            pulse = 0.7 + 0.3 * math.sin(current_time * 2 + lat)
            cloud_radius = int(15 * intensity * pulse)
            
            # Draw cloud/storm system (white/gray swirl)
            cloud_color = (200, 200, 200)  # Light gray clouds
            cv2.circle(frame, (px, py), cloud_radius, cloud_color, 2, cv2.LINE_AA)
            cv2.circle(frame, (px, py), cloud_radius - 4, (180, 180, 180), 1, cv2.LINE_AA)
            
            # Draw spiral pattern for cyclone effect
            for angle in range(0, 360, 45):
                angle_rad = math.radians(angle + current_time * 50)
                spiral_x = px + int(cloud_radius * 0.6 * math.cos(angle_rad))
                spiral_y = py + int(cloud_radius * 0.6 * math.sin(angle_rad))
                cv2.circle(frame, (spiral_x, spiral_y), 2, (220, 220, 220), -1)
            
            # Lightning effect (random flashes)
            if self.globe_state.show_lightning and intensity > 0.5:
                # Random lightning flash
                if random.random() < 0.15 * intensity:
                    # Lightning bolt
                    bolt_start = (px, py)
                    bolt_end = (px + random.randint(-20, 20), py + random.randint(10, 30))
                    
                    # Bright flash
                    cv2.line(frame, bolt_start, bolt_end, (255, 255, 255), 2, cv2.LINE_AA)
                    cv2.line(frame, bolt_start, bolt_end, (200, 200, 255), 4, cv2.LINE_AA)
                    
                    # Branch
                    mid_x = (bolt_start[0] + bolt_end[0]) // 2
                    mid_y = (bolt_start[1] + bolt_end[1]) // 2
                    branch_end = (mid_x + random.randint(-15, 15), mid_y + random.randint(5, 15))
                    cv2.line(frame, (mid_x, mid_y), branch_end, (255, 255, 255), 1, cv2.LINE_AA)
                    
                    # Glow effect
                    cv2.circle(frame, bolt_end, 8, (200, 200, 255), 1, cv2.LINE_AA)
        
        # Add weather legend
        legend_x = center[0] - radius - 60
        legend_y = center[1] - radius + 20
        cv2.putText(frame, "WEATHER", (legend_x, legend_y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
        cv2.circle(frame, (legend_x + 10, legend_y + 15), 5, (200, 200, 200), 1)
        cv2.putText(frame, "Storm", (legend_x + 20, legend_y + 18),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.3, (180, 180, 180), 1)
        
        if self.globe_state.show_lightning:
            cv2.line(frame, (legend_x + 5, legend_y + 28), (legend_x + 15, legend_y + 38), (255, 255, 200), 2)
            cv2.putText(frame, "Lightning", (legend_x + 20, legend_y + 36),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 255, 200), 1)
        
        return frame
    
    def _render_daylight(self, frame: np.ndarray, center: Tuple[int, int], scale: float) -> np.ndarray:
        """
        Render day/night terminator on the globe.
        Shows which parts of Earth are in sunlight vs darkness.
        """
        # Calculate sun position based on current UTC time
        now = datetime.utcnow()
        
        # Sun longitude (roughly -15 degrees per hour from noon at 0 longitude)
        hours_from_noon = (now.hour - 12) + now.minute / 60.0
        sun_lng = -hours_from_noon * 15  # 15 degrees per hour
        
        # Sun latitude (varies with season, simplified)
        day_of_year = now.timetuple().tm_yday
        sun_lat = 23.5 * math.sin(2 * math.pi * (day_of_year - 81) / 365)  # Approximate declination
        
        # Draw terminator line (boundary between day and night)
        terminator_points = []
        for lat in range(-90, 91, 5):
            # Calculate longitude of terminator at this latitude
            lat_rad = math.radians(lat)
            sun_lat_rad = math.radians(sun_lat)
            
            # Terminator is 90 degrees from sun position
            term_lng = sun_lng + 90
            
            point_3d = self._lat_lng_to_3d(lat, term_lng)
            rotated = self._rotate_point(point_3d, 
                                         self.globe_state.rotation_x, 
                                         self.globe_state.rotation_y)
            projected = self._project_point(rotated, center, scale)
            
            if projected and projected[2] > -30:
                terminator_points.append((int(projected[0]), int(projected[1])))
        
        # Draw terminator line
        if len(terminator_points) >= 2:
            for i in range(len(terminator_points) - 1):
                cv2.line(frame, terminator_points[i], terminator_points[i+1], 
                        (0, 150, 255), 2, cv2.LINE_AA)  # Orange for sun line
        
        # Draw sun indicator
        sun_3d = self._lat_lng_to_3d(sun_lat, sun_lng)
        sun_rotated = self._rotate_point(sun_3d, 
                                         self.globe_state.rotation_x, 
                                         self.globe_state.rotation_y)
        sun_projected = self._project_point(sun_rotated, center, scale)
        
        if sun_projected and sun_projected[2] > -30:
            # Sun glow
            cv2.circle(frame, (sun_projected[0], sun_projected[1]), 12, (0, 200, 255), -1)
            cv2.circle(frame, (sun_projected[0], sun_projected[1]), 8, (0, 255, 255), -1)
            cv2.circle(frame, (sun_projected[0], sun_projected[1]), 4, (255, 255, 255), -1)
        
        return frame
    
    def _render_conflicts(self, frame: np.ndarray, center: Tuple[int, int], scale: float) -> np.ndarray:
        """
        Render conflict/war zones on the globe.
        Red pulsing circles indicate active conflicts.
        """
        if not self.earth_data:
            return frame
        
        conflicts = self.earth_data.get_conflict_zones()
        
        for conflict in conflicts:
            lat, lng = conflict['center']
            severity = conflict.get('severity', 'medium')
            
            # Convert to 3D and project
            point_3d = self._lat_lng_to_3d(lat, lng)
            rotated = self._rotate_point(point_3d, 
                                         self.globe_state.rotation_x, 
                                         self.globe_state.rotation_y)
            projected = self._project_point(rotated, center, scale)
            
            if projected and projected[2] > -30:
                # Pulsing effect
                pulse = abs(math.sin(self.animation_time * 2 + hash(conflict['name']) % 10))
                
                # Color based on severity
                if severity == 'critical':
                    color = (0, 0, 255)  # Red
                    base_radius = 8
                elif severity == 'high':
                    color = (0, 100, 255)  # Orange-red
                    base_radius = 6
                else:
                    color = (0, 165, 255)  # Orange
                    base_radius = 5
                
                radius = int(base_radius + pulse * 4)
                
                # Outer glow
                cv2.circle(frame, (projected[0], projected[1]), radius + 4, 
                          (color[0]//2, color[1]//2, color[2]//2), -1)
                # Main circle
                cv2.circle(frame, (projected[0], projected[1]), radius, color, -1)
                # Inner bright spot
                cv2.circle(frame, (projected[0], projected[1]), radius//2, 
                          (100, 100, 255), -1)
        
        return frame
    
    def _render_lightning(self, frame: np.ndarray, center: Tuple[int, int], scale: float) -> np.ndarray:
        """
        Render lightning strikes on the globe.
        White flashes that fade out quickly.
        """
        current_time = time.time()
        
        # Update lightning data periodically
        if self.earth_data and (not self.lightning_flashes or 
                                 current_time - getattr(self, '_last_lightning_update', 0) > 30):
            try:
                strikes = self.earth_data.get_lightning_data()
                self.lightning_flashes = [
                    {'lat': s['lat'], 'lng': s['lng'], 'time': current_time, 
                     'intensity': random.uniform(0.7, 1.0)}
                    for s in strikes[:50]  # Limit to 50 strikes
                ]
                self._last_lightning_update = current_time
            except:
                pass
        
        # Render active flashes
        active_flashes = []
        for flash in self.lightning_flashes:
            age = current_time - flash['time']
            if age < 2.0:  # Flash visible for 2 seconds
                active_flashes.append(flash)
                
                # Calculate fade
                fade = max(0, 1.0 - age / 2.0)
                
                # Convert to 3D and project
                point_3d = self._lat_lng_to_3d(flash['lat'], flash['lng'])
                rotated = self._rotate_point(point_3d, 
                                             self.globe_state.rotation_x, 
                                             self.globe_state.rotation_y)
                projected = self._project_point(rotated, center, scale)
                
                if projected and projected[2] > -30:
                    intensity = int(255 * fade * flash['intensity'])
                    
                    # Lightning bolt effect
                    if age < 0.1:  # Initial bright flash
                        cv2.circle(frame, (projected[0], projected[1]), 8, 
                                  (255, 255, 255), -1)
                    else:
                        cv2.circle(frame, (projected[0], projected[1]), 4, 
                                  (intensity, intensity, intensity), -1)
                        # Add slight glow
                        cv2.circle(frame, (projected[0], projected[1]), 6, 
                                  (intensity//2, intensity//2, intensity), 1)
        
        self.lightning_flashes = active_flashes
        return frame
    
    def _render_region_highlight(self, frame: np.ndarray, center: Tuple[int, int], scale: float) -> np.ndarray:
        """
        Highlight a specific region or continent on the globe.
        """
        if not self.globe_state.highlighted_region:
            return frame
        
        region_name = self.globe_state.highlighted_region.lower()
        
        # Get region boundary
        boundary = None
        if self.earth_data:
            boundary = self.earth_data.get_continent_boundary(region_name)
            if not boundary:
                region_info = self.earth_data.find_region_by_query(region_name)
                if region_info and 'boundary' in region_info:
                    boundary = region_info['boundary']
        
        if not boundary:
            # Use stored bounds if available
            boundary = self.globe_state.highlighted_region_bounds
        
        if boundary:
            # Project boundary points
            projected_points = []
            for lat, lng in boundary:
                point_3d = self._lat_lng_to_3d(lat, lng)
                rotated = self._rotate_point(point_3d, 
                                             self.globe_state.rotation_x, 
                                             self.globe_state.rotation_y)
                projected = self._project_point(rotated, center, scale)
                
                if projected and projected[2] > -50:
                    projected_points.append((int(projected[0]), int(projected[1])))
            
            if len(projected_points) >= 3:
                pts = np.array(projected_points, dtype=np.int32)
                
                # Pulsing highlight
                pulse = abs(math.sin(self.animation_time * 2))
                
                # Semi-transparent fill
                overlay = frame.copy()
                cv2.fillPoly(overlay, [pts], (0, int(200 + 55 * pulse), 255))  # Yellow-orange
                cv2.addWeighted(overlay, 0.25, frame, 0.75, 0, frame)
                
                # Bright outline
                cv2.polylines(frame, [pts], True, (0, 255, 255), 2, cv2.LINE_AA)
        
        return frame
    
    def _render_disasters(self, frame: np.ndarray, center: Tuple[int, int], scale: float) -> np.ndarray:
        """
        Render natural disaster zones on the globe.
        """
        if not self.earth_data:
            return frame
        
        disasters = self.earth_data.get_disasters()
        
        for disaster in disasters:
            lat, lng = disaster['lat'], disaster['lng']
            disaster_type = disaster.get('type', 'unknown')
            
            # Convert to 3D and project
            point_3d = self._lat_lng_to_3d(lat, lng)
            rotated = self._rotate_point(point_3d, 
                                         self.globe_state.rotation_x, 
                                         self.globe_state.rotation_y)
            projected = self._project_point(rotated, center, scale)
            
            if projected and projected[2] > -30:
                # Color based on disaster type
                if disaster_type == 'earthquake':
                    color = (0, 165, 255)  # Orange
                    symbol = 'E'
                elif disaster_type == 'storm':
                    color = (255, 100, 100)  # Light blue
                    symbol = 'S'
                elif disaster_type == 'flood':
                    color = (255, 0, 0)  # Blue
                    symbol = 'F'
                elif disaster_type == 'volcano':
                    color = (0, 0, 200)  # Dark red
                    symbol = 'V'
                elif disaster_type == 'wildfire':
                    color = (0, 100, 255)  # Orange-red
                    symbol = 'W'
                else:
                    color = (128, 128, 128)  # Gray
                    symbol = '!'
                
                # Pulsing effect
                pulse = abs(math.sin(self.animation_time * 3))
                radius = int(6 + pulse * 3)
                
                # Draw marker
                cv2.circle(frame, (projected[0], projected[1]), radius, color, -1)
                cv2.circle(frame, (projected[0], projected[1]), radius + 2, (255, 255, 255), 1)
        
        return frame
    
    def _render_military(self, frame: np.ndarray, center: Tuple[int, int], scale: float) -> np.ndarray:
        """
        Render military installations on the globe.
        """
        if not self.earth_data:
            return frame
        
        bases = self.earth_data.get_military_installations()
        
        for base in bases:
            lat, lng = base['lat'], base['lng']
            
            # Convert to 3D and project
            point_3d = self._lat_lng_to_3d(lat, lng)
            rotated = self._rotate_point(point_3d, 
                                         self.globe_state.rotation_x, 
                                         self.globe_state.rotation_y)
            projected = self._project_point(rotated, center, scale)
            
            if projected and projected[2] > -30:
                # Green diamond for military
                size = 5
                pts = np.array([
                    [projected[0], projected[1] - size],
                    [projected[0] + size, projected[1]],
                    [projected[0], projected[1] + size],
                    [projected[0] - size, projected[1]]
                ], dtype=np.int32)
                
                cv2.fillPoly(frame, [pts], (0, 200, 0))  # Green
                cv2.polylines(frame, [pts], True, (0, 255, 0), 1)
        
        return frame
    
    def _render_globe_optimized(self, frame: np.ndarray) -> np.ndarray:
        """
        Render the holographic globe using VECTORIZED NumPy operations.
        Includes materialization effect, beeping marker, and Earth rotation.
        """
        h, w = frame.shape[:2]
        
        # Calculate hologram position and size
        hologram_size = int(min(w, h) * self.hologram_scale)
        
        # Get position offsets (from control panel)
        offset_x = getattr(self, 'hologram_position_offset_x', 0)
        offset_y = getattr(self, 'hologram_position_offset_y', 0)
        
        if self.hologram_position == "right":
            center_x = w - hologram_size // 2 - 50 + offset_x
        elif self.hologram_position == "left":
            center_x = hologram_size // 2 + 50 + offset_x
        else:
            center_x = w // 2 + offset_x
        
        center_y = h // 2 + offset_y
        center = (center_x, center_y)
        
        # Update materialization progress
        if self.globe_state.is_materializing:
            elapsed = time.time() - self.globe_state.materialize_start_time
            self.globe_state.materialize_progress = min(1.0, elapsed / self.materialize_duration)
            
            if self.globe_state.materialize_progress >= 1.0:
                self.globe_state.is_materializing = False
                print("[AR] Globe materialization complete")
            
            # Draw materialization particles
            frame = self._render_materialize_particles(frame, center, hologram_size)
        
        # Earth rotation (like real Earth, ~0.004 degrees per frame at 30fps = 1 rotation per day scaled)
        # Rotate slowly in the direction Earth rotates (west to east)
        self.globe_state.rotation_y += 0.003  # Gentle eastward rotation
        
        # Scale based on zoom - also affected by materialization
        scale = self.globe_state.zoom * (hologram_size / 200)
        
        # VECTORIZED: Rotate all points at once
        rotated_points = self._rotate_points_vectorized(
            self.globe_points_np,
            self.globe_state.rotation_x,
            self.globe_state.rotation_y
        )
        
        # VECTORIZED: Project all points at once
        projected_points = self._project_points_vectorized(rotated_points, center, scale)
        
        # Draw ocean sphere first (blue glow background)
        radius = int(hologram_size * 0.4 * self.globe_state.zoom)
        
        glow_layer = np.zeros_like(frame, dtype=np.uint8)
        cv2.circle(glow_layer, center, int(radius * 1.25), (255, 140, 30), -1)
        cv2.circle(glow_layer, center, int(radius * 1.05), (255, 220, 80), -1)
        try:
            glow_layer = cv2.GaussianBlur(glow_layer, (0, 0), sigmaX=max(1.0, radius * 0.10), sigmaY=max(1.0, radius * 0.10))
        except Exception:
            pass
        frame = cv2.addWeighted(frame, 1.0, glow_layer, 0.45, 0)
        cv2.circle(frame, center, radius, (120, 40, 0), -1)
        
        # Draw latitude/longitude grid lines with neon glow
        for line_type, start_idx, end_idx in self.line_indices:
            line_points = projected_points[start_idx:end_idx]
            
            # Draw line segments
            for i in range(len(line_points) - 1):
                p1 = line_points[i]
                p2 = line_points[i + 1]
                
                # Skip invalid points (behind camera)
                if p1[2] < -50 or p2[2] < -50:
                    continue
                
                # Calculate opacity based on depth
                avg_z = (p1[2] + p2[2]) / 2
                opacity = max(0.3, min(1.0, (avg_z + 100) / 200))
                
                # Neon cyan grid lines with glow effect
                # Draw glow first (thicker, dimmer)
                glow_color = (
                    int(255 * opacity * 0.28),
                    int(180 * opacity * 0.28),
                    int(60 * opacity * 0.28)
                )
                cv2.line(frame, (int(p1[0]), int(p1[1])), (int(p2[0]), int(p2[1])), glow_color, 3, cv2.LINE_AA)
                
                # Draw bright core line
                core_color = (
                    int(255 * opacity),
                    int(220 * opacity),
                    int(120 * opacity)
                )
                cv2.line(frame, (int(p1[0]), int(p1[1])), (int(p2[0]), int(p2[1])), core_color, 1, cv2.LINE_AA)
        
        # Draw continent outlines with semi-transparent fill
        if hasattr(self, 'continent_3d'):
            for continent_name, points_3d in self.continent_3d:
                # Rotate and project continent points
                projected_continent = []
                visible_count = 0
                
                for point in points_3d:
                    rotated = self._rotate_point(point, 
                                                self.globe_state.rotation_x, 
                                                self.globe_state.rotation_y)
                    projected = self._project_point(rotated, center, scale)
                    if projected and projected[2] > -30:  # More lenient visibility
                        projected_continent.append((int(projected[0]), int(projected[1])))
                        visible_count += 1
                    else:
                        projected_continent.append(None)
                
                # Draw continent outline if mostly visible
                if visible_count > len(points_3d) * 0.3:
                    # Filter valid points for polygon
                    valid_points = [p for p in projected_continent if p is not None]
                    
                    if len(valid_points) >= 3:
                        # Draw filled polygon with transparency
                        pts = np.array(valid_points, dtype=np.int32)
                        
                        overlay = frame.copy()
                        cv2.fillPoly(overlay, [pts], (255, 170, 40))
                        cv2.addWeighted(overlay, 0.50, frame, 0.50, 0, frame)
                        cv2.polylines(frame, [pts], True, (255, 220, 120), 2, cv2.LINE_AA)
                        cv2.polylines(frame, [pts], True, (255, 255, 200), 1, cv2.LINE_AA)
        
        # Draw day/night terminator if enabled
        if self.globe_state.show_daylight:
            frame = self._render_daylight(frame, center, scale)
        
        # Draw region highlight if enabled
        if self.globe_state.highlighted_region:
            frame = self._render_region_highlight(frame, center, scale)
        
        # Draw conflict zones if enabled
        if self.globe_state.show_conflicts:
            frame = self._render_conflicts(frame, center, scale)
        
        # Draw disaster zones if enabled
        if self.globe_state.show_disasters:
            frame = self._render_disasters(frame, center, scale)
        
        # Draw military installations if enabled
        if self.globe_state.show_military:
            frame = self._render_military(frame, center, scale)
        
        # Draw lightning if enabled
        if self.globe_state.show_lightning:
            frame = self._render_lightning(frame, center, scale)
        
        # Draw highlighted city marker with BEEPING effect
        if self.globe_state.highlighted_city and not self.globe_state.is_materializing:
            city_3d = self._lat_lng_to_3d(self.globe_state.target_lat, self.globe_state.target_lng)
            rotated = self._rotate_point(city_3d, 
                                         self.globe_state.rotation_x, 
                                         self.globe_state.rotation_y)
            projected = self._project_point(rotated, center, scale)
            
            if projected and projected[2] > -50:
                # Beeping effect - pulse with sound
                beep_cycle = self.animation_time % 1.0  # 1 second cycle
                is_beep_on = beep_cycle < 0.3  # Beep visible for 0.3 seconds
                
                # Play beep sound periodically
                if beep_cycle < 0.05 and self.animation_time - self.globe_state.beep_time > 0.9:
                    self._play_beep_sound()
                    self.globe_state.beep_time = self.animation_time
                
                # Pulsing yellow marker
                pulse = abs(math.sin(self.animation_time * 6))  # Faster pulse
                radius = int(6 + pulse * 4)
                
                # Yellow glow with beep flash
                if is_beep_on:
                    # Bright flash during beep
                    cv2.circle(frame, (projected[0], projected[1]), radius + 8, (0, 255, 255), -1)
                    cv2.circle(frame, (projected[0], projected[1]), radius + 4, (255, 255, 255), -1)
                else:
                    # Normal glow
                    cv2.circle(frame, (projected[0], projected[1]), radius + 5, (0, 200, 255), -1)
                
                cv2.circle(frame, (projected[0], projected[1]), radius, (0, 255, 255), -1)
                
                # Radar ring effect
                ring_radius = int(15 + (beep_cycle * 30))
                ring_alpha = max(0, 1.0 - beep_cycle)
                if ring_alpha > 0.1:
                    cv2.circle(frame, (projected[0], projected[1]), ring_radius, 
                              (0, int(255 * ring_alpha), int(255 * ring_alpha)), 1)
                
                # City name label
                label = self.globe_state.highlighted_city
                label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
                label_x = projected[0] - label_size[0] // 2
                label_y = projected[1] - radius - 12
                
                # Label background
                cv2.rectangle(frame, 
                             (label_x - 3, label_y - label_size[1] - 3),
                             (label_x + label_size[0] + 3, label_y + 3),
                             (0, 0, 0), -1)
                cv2.rectangle(frame, 
                             (label_x - 3, label_y - label_size[1] - 3),
                             (label_x + label_size[0] + 3, label_y + 3),
                             (0, 255, 255), 1)
                
                cv2.putText(frame, label, (label_x, label_y),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
        
        # Draw holographic frame border
        border_color = (255, 200, 100)  # Light blue
        pulse = abs(math.sin(self.animation_time * 2))
        border_intensity = 0.5 + pulse * 0.5
        
        # Corner decorations
        corner_size = 30
        corners = [
            (center_x - hologram_size // 2, center_y - hologram_size // 2),  # Top-left
            (center_x + hologram_size // 2, center_y - hologram_size // 2),  # Top-right
            (center_x - hologram_size // 2, center_y + hologram_size // 2),  # Bottom-left
            (center_x + hologram_size // 2, center_y + hologram_size // 2),  # Bottom-right
        ]
        
        for i, (cx, cy) in enumerate(corners):
            # Draw corner brackets
            if i == 0:  # Top-left
                cv2.line(frame, (cx, cy), (cx + corner_size, cy), border_color, 2)
                cv2.line(frame, (cx, cy), (cx, cy + corner_size), border_color, 2)
            elif i == 1:  # Top-right
                cv2.line(frame, (cx, cy), (cx - corner_size, cy), border_color, 2)
                cv2.line(frame, (cx, cy), (cx, cy + corner_size), border_color, 2)
            elif i == 2:  # Bottom-left
                cv2.line(frame, (cx, cy), (cx + corner_size, cy), border_color, 2)
                cv2.line(frame, (cx, cy), (cx, cy - corner_size), border_color, 2)
            elif i == 3:  # Bottom-right
                cv2.line(frame, (cx, cy), (cx - corner_size, cy), border_color, 2)
                cv2.line(frame, (cx, cy), (cx, cy - corner_size), border_color, 2)
        
        # Title
        title = "HOLOGRAPHIC GLOBE"
        title_size = cv2.getTextSize(title, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
        title_x = center_x - title_size[0] // 2
        title_y = center_y - hologram_size // 2 - 10
        cv2.putText(frame, title, (title_x, title_y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, border_color, 1)
        
        # Render control panel
        frame = self._render_control_panel(frame, center_x, center_y, hologram_size)
        
        # Show hand interaction hint if hand is near globe
        if self.hand_gesture.is_grabbing:
            hint = "SWIPE TO ROTATE"
            hint_size = cv2.getTextSize(hint, cv2.FONT_HERSHEY_SIMPLEX, 0.4, 1)[0]
            hint_x = center_x - hint_size[0] // 2
            hint_y = center_y + hologram_size // 2 + 15
            cv2.putText(frame, hint, (hint_x, hint_y),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
        
        return frame
    
    def _render_webcam_window(self, frame: np.ndarray) -> np.ndarray:
        """Render the webcam feed window onto the frame."""
        h, w = frame.shape[:2]
        
        # Window size and position
        window_w = int(w * 0.45)
        window_h = int(window_w * 9 / 16)  # 16:9 aspect ratio
        
        if self.hologram_position == "right":
            window_x = w - window_w - 30
        elif self.hologram_position == "left":
            window_x = 30
        else:
            window_x = (w - window_w) // 2
        
        window_y = (h - window_h) // 2
        
        # Draw window frame
        border_color = (255, 200, 100)  # Light blue
        
        # Background
        cv2.rectangle(frame, (window_x, window_y), 
                     (window_x + window_w, window_y + window_h),
                     (20, 20, 20), -1)
        
        # Border
        cv2.rectangle(frame, (window_x, window_y), 
                     (window_x + window_w, window_y + window_h),
                     border_color, 2)
        
        # Draw webcam feed or placeholder
        if self.webcam_state.frame is not None:
            try:
                feed_frame = cv2.resize(self.webcam_state.frame, (window_w - 10, window_h - 40))
                frame[window_y + 30:window_y + 30 + feed_frame.shape[0],
                      window_x + 5:window_x + 5 + feed_frame.shape[1]] = feed_frame
            except Exception:
                pass
        else:
            # Show placeholder with webcam info
            center_y = window_y + window_h // 2
            
            if self.webcam_state.is_loading:
                status_text = "Connecting..."
            else:
                status_text = "Feed Unavailable"
            
            text_size = cv2.getTextSize(status_text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
            text_x = window_x + (window_w - text_size[0]) // 2
            cv2.putText(frame, status_text, (text_x, center_y - 20),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, border_color, 2)
            
            # Show URL hint
            if self.webcam_state.current_feed_url:
                url_hint = "Visit URL in browser"
                hint_size = cv2.getTextSize(url_hint, cv2.FONT_HERSHEY_SIMPLEX, 0.4, 1)[0]
                hint_x = window_x + (window_w - hint_size[0]) // 2
                cv2.putText(frame, url_hint, (hint_x, center_y + 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, (150, 150, 150), 1)
            
            # Draw camera icon placeholder
            icon_x = window_x + window_w // 2
            icon_y = center_y + 40
            cv2.circle(frame, (icon_x, icon_y), 25, border_color, 2)
            cv2.circle(frame, (icon_x - 8, icon_y), 5, border_color, -1)
            cv2.rectangle(frame, (icon_x - 15, icon_y + 10), (icon_x + 15, icon_y + 20), border_color, 2)
        
        # Title bar
        title = f"LIVE: {self.webcam_state.current_feed_name}"
        cv2.putText(frame, title, (window_x + 10, window_y + 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, border_color, 1)
        
        # Navigation hint
        nav_text = "Say 'next' or 'previous' to switch feeds"
        cv2.putText(frame, nav_text, (window_x + 10, window_y + window_h - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (150, 150, 150), 1)
        
        return frame
    
    # ==================== Command Processing ====================
    
    def process_command(self, text: str) -> Optional[str]:
        """
        Process voice/text commands for AR holograms.
        
        Returns response text if command was handled, None otherwise.
        """
        text_lower = text.lower().strip()
        
        # ===== KEYBOARD COMMANDS (CHECK FIRST - highest priority) =====
        keyboard_show_patterns = [
            "show keyboard", "show the keyboard", "show me the keyboard",
            "display keyboard", "open keyboard", "bring up keyboard",
            "pull up keyboard", "activate keyboard", "keyboard please"
        ]
        if any(phrase in text_lower for phrase in keyboard_show_patterns):
            self._play_ui_sound("open")
            return self.toggle_keyboard(True)
        
        keyboard_hide_patterns = [
            "hide keyboard", "close keyboard", "remove keyboard",
            "turn off keyboard", "disable keyboard", "store keyboard",
            "put away keyboard", "store the keyboard", "put away the keyboard"
        ]
        if any(phrase in text_lower for phrase in keyboard_hide_patterns):
            self._play_ui_sound("close")
            return self.toggle_keyboard(False)
        
        # ===== DIAL COMMANDS =====
        dial_show_patterns = [
            "show dial", "show the dial", "show me the dial",
            "display dial", "open dial", "bring up dial",
            "pull up dial", "activate dial"
        ]
        if any(phrase in text_lower for phrase in dial_show_patterns):
            self._play_ui_sound("open")
            return self.toggle_dial(True)
        
        dial_hide_patterns = [
            "hide dial", "close dial", "remove dial", "turn off dial",
            "disable dial", "store dial", "put away dial",
            "store the dial", "put away the dial"
        ]
        if any(phrase in text_lower for phrase in dial_hide_patterns):
            self._play_ui_sound("close")
            return self.toggle_dial(False)
        
        # ===== GLOBE COMMANDS =====
        globe_show_patterns = [
            "show globe", "show the globe", "display globe", "open globe",
            "show earth", "show the earth", "display earth", "bring up globe",
            "pull up globe", "activate globe", "show me the globe",
            "bring up the globe", "bring up the earth", "open the globe",
            "show hologram", "show world", "view globe"
        ]
        if any(phrase in text_lower for phrase in globe_show_patterns):
            self._play_ui_sound("materialize")
            return self.show_globe()
        
        globe_hide_patterns = [
            "hide globe", "close globe", "remove globe", "turn off globe",
            "disable globe", "hide earth", "close earth", "store globe",
            "put away globe", "store the globe", "put away the globe",
            "close the globe", "shut down globe", "turn globe off",
            "dismiss globe", "close hologram", "hide hologram",
            "stop showing globe", "take away globe"
        ]
        if any(phrase in text_lower for phrase in globe_hide_patterns):
            # Sound is played in hide_globe()
            return self.hide_globe()
        
        # ===== CLOSE MAP COMMAND =====
        close_map_patterns = [
            "close map", "close the map", "hide map", "back to globe",
            "return to globe", "exit map", "close map view",
            "switch to globe", "turn to globe"
        ]
        if any(phrase in text_lower for phrase in close_map_patterns):
            return self.close_map_view()
        
        # ===== LOCATION QUERIES =====
        non_location_words = ['keyboard', 'globe', 'weather', 'satellite', 'webcam', 
                              'camera', 'dial', 'daylight', 'night', 'thermal']
        
        # 1. MAP VIEW: "show me the map of Orlando" or "show map of Chicago"
        map_patterns = ["show me the map of", "show the map of", "show map of", 
                        "open map of", "display map of", "map of"]
        for pattern in map_patterns:
            if pattern in text_lower:
                location = text_lower.split(pattern)[-1].strip()
                location = location.replace("please", "").replace("?", "").strip()
                if location and len(location) > 1:
                    self._play_ui_sound("zoom")
                    return self.show_map_view(location)
        
        # 2. HIGHLIGHT LANDMASS: "highlight Africa" or "highlight South America"
        highlight_patterns = ["highlight"]
        for pattern in highlight_patterns:
            if pattern in text_lower:
                region = text_lower.split(pattern)[-1].strip()
                region = region.replace("please", "").replace("?", "").strip()
                if region and len(region) > 1:
                    # Check if it's a continent/region (highlight landmass)
                    from monica_realistic_globe import REGION_BOUNDS
                    if region.lower() in REGION_BOUNDS:
                        return self.highlight_landmass(region)
                    else:
                        # It's a city/country - show marker
                        return self.highlight_location(region)
        
        # 3. SHOW LOCATION: "show me Orlando" or "where is Chicago" (city marker)
        location_patterns = [
            "where is", "where's", "show me", "find", "locate",
            "point to", "zoom to", "go to", "take me to",
            "zoom in to", "zoom in on", "focus on", "center on",
            "can you show me", "i want to see", "show location of",
            "highlight location of", "search for", "look for"
        ]
        for pattern in location_patterns:
            if pattern in text_lower:
                location = text_lower.split(pattern)[-1].strip()
                location = location.replace("located", "").replace("?", "")
                location = location.replace(" on the globe", "").replace(" on the map", "")
                location = location.replace(" please", "").strip()
                # Remove leading words like "the" if it's just "the chicago" -> "chicago"
                if location.startswith("the "):
                    location = location[4:].strip()
                
                if any(word in location for word in non_location_words):
                    continue
                    
                if location and len(location) > 1:
                    return self.highlight_location(location)
        
        # Zoom commands - more flexible
        zoom_in_patterns = [
            "zoom in", "closer", "magnify", "bigger", "enlarge",
            "zoom closer", "get closer", "make it bigger"
        ]
        if any(phrase in text_lower for phrase in zoom_in_patterns):
            return self.zoom_in()
        
        zoom_out_patterns = [
            "zoom out", "farther", "smaller", "zoom back",
            "make it smaller", "pull back", "zoom away"
        ]
        if any(phrase in text_lower for phrase in zoom_out_patterns):
            return self.zoom_out()
        
        # City-level zoom (shows map window)
        city_zoom_patterns = [
            "zoom to city", "city level", "street level", "zoom in to city", 
            "show city", "city view", "zoom to city level", "show map",
            "show area map", "show street map", "change globe to map",
            "turn to map", "switch to map"
        ]
        if any(phrase in text_lower for phrase in city_zoom_patterns):
            self._play_ui_sound("zoom")
            return self.zoom_to_city_level()
        
        # ===== POI SEARCH (stores, schools, webcams) =====
        # Show stores/shops
        store_patterns = ["show stores", "show shops", "show the stores", "show me stores", 
                         "where are the stores", "find stores", "nearby stores"]
        if any(phrase in text_lower for phrase in store_patterns):
            self._play_ui_sound("success")
            return self.search_poi("store")
        
        # Show schools
        school_patterns = ["show schools", "show the schools", "show me schools",
                          "where are the schools", "find schools", "nearby schools"]
        if any(phrase in text_lower for phrase in school_patterns):
            self._play_ui_sound("success")
            return self.search_poi("school")
        
        # Show restaurants
        restaurant_patterns = ["show restaurants", "show food", "show the restaurants",
                              "where can i eat", "find restaurants", "nearby restaurants"]
        if any(phrase in text_lower for phrase in restaurant_patterns):
            self._play_ui_sound("success")
            return self.search_poi("restaurant")
        
        # Show hospitals
        hospital_patterns = ["show hospitals", "show the hospitals", "show me hospitals",
                            "where are the hospitals", "find hospitals", "nearby hospitals"]
        if any(phrase in text_lower for phrase in hospital_patterns):
            self._play_ui_sound("success")
            return self.search_poi("hospital")
        
        # Show public webcams
        public_webcam_patterns = ["show public webcams", "show public cameras", "show webcams",
                                  "show live cameras", "public cams", "show cameras on globe", 
                                  "nearby cams", "nearby cameras"]
        if any(phrase in text_lower for phrase in public_webcam_patterns):
            self._play_ui_sound("success")
            return self.toggle_webcam_markers(True)
        
        if any(phrase in text_lower for phrase in ["hide webcams", "hide cameras"]):
            return self.toggle_webcam_markers(False)
        
        # Satellite/terrain toggle
        if any(phrase in text_lower for phrase in ["show satellite", "satellite view", "show terrain"]):
            return self.toggle_satellite_view(True)
        
        if any(phrase in text_lower for phrase in ["hide satellite", "wireframe", "hologram view"]):
            return self.toggle_satellite_view(False)
        
        # Rotation commands
        if "rotate" in text_lower:
            if "left" in text_lower:
                return self.rotate_globe("left")
            elif "right" in text_lower:
                return self.rotate_globe("right")
            elif "up" in text_lower:
                return self.rotate_globe("up")
            elif "down" in text_lower:
                return self.rotate_globe("down")
        
        # ===== HOLOGRAM POSITION CONTROL =====
        # Move hologram commands
        move_patterns = ["move hologram", "move the hologram", "move it", "shift hologram", 
                        "move globe", "move the globe", "nudge"]
        if any(phrase in text_lower for phrase in move_patterns):
            if "up" in text_lower:
                return self.move_hologram("up")
            elif "down" in text_lower:
                return self.move_hologram("down")
            elif "left" in text_lower:
                return self.move_hologram("left")
            elif "right" in text_lower:
                return self.move_hologram("right")
        
        # Tilt/orientation commands
        tilt_patterns = ["tilt", "straighten", "upright", "sideways", "sit up"]
        if any(phrase in text_lower for phrase in tilt_patterns):
            if "upright" in text_lower or "straight" in text_lower or "sit up" in text_lower:
                return self.tilt_hologram("upright")
            elif "left" in text_lower:
                return self.tilt_hologram("left")
            elif "right" in text_lower:
                return self.tilt_hologram("right")
            elif "sideways" in text_lower:
                # If it's sideways, make it upright
                return self.tilt_hologram("upright")
        
        # Fix position commands
        fix_patterns = ["fix position", "fix the position", "reset position", "reset hologram",
                       "fix hologram", "default position", "original position"]
        if any(phrase in text_lower for phrase in fix_patterns):
            return self.fix_hologram_position()
        
        # Set position to side
        position_patterns = ["put hologram", "place hologram", "hologram on the", "move hologram to"]
        if any(phrase in text_lower for phrase in position_patterns):
            if "left" in text_lower:
                return self.set_hologram_position("left")
            elif "right" in text_lower:
                return self.set_hologram_position("right")
            elif "center" in text_lower or "middle" in text_lower:
                return self.set_hologram_position("center")
        
        # Resize commands
        resize_patterns = ["make hologram", "make it", "hologram bigger", "hologram smaller",
                          "enlarge hologram", "shrink hologram"]
        if any(phrase in text_lower for phrase in resize_patterns):
            if "bigger" in text_lower or "larger" in text_lower or "enlarge" in text_lower:
                return self.resize_hologram("bigger")
            elif "smaller" in text_lower or "shrink" in text_lower:
                return self.resize_hologram("smaller")
        
        # Webcam window commands with location extraction
        webcam_patterns = [
            "show webcam", "show live", "show camera", "live feed", "show feed",
            "show me live", "live cam", "webcam in", "webcam from", "camera in",
            "show live feed", "show live cam"
        ]
        for pattern in webcam_patterns:
            if pattern in text_lower:
                # Try to extract location
                location = None
                location_markers = [" in ", " from ", " of ", " at "]
                for marker in location_markers:
                    if marker in text_lower:
                        location = text_lower.split(marker)[-1].strip()
                        break
                return self.show_webcam_feed(location=location)
        
        if any(phrase in text_lower for phrase in ["next feed", "next webcam", "next camera", "switch feed", "next"]):
            if self.active_hologram == HologramType.WEBCAM_WINDOW:
                return self.next_webcam()
        
        if any(phrase in text_lower for phrase in ["previous feed", "previous webcam", "last feed", "previous"]):
            if self.active_hologram == HologramType.WEBCAM_WINDOW:
                return self.previous_webcam()
        
        if any(phrase in text_lower for phrase in ["close webcam", "close feed", "close window"]):
            return self.close_webcam_window()
        
        # Return to globe
        if any(phrase in text_lower for phrase in ["return to globe", "back to globe", "show globe again", "go back to globe"]):
            return self.return_to_globe()
        
        # Daylight/sunlight toggle
        if any(phrase in text_lower for phrase in ["show daylight", "show sunlight", "show day night", "day and night", "sun position"]):
            return self.toggle_daylight(True)
        
        if any(phrase in text_lower for phrase in ["hide daylight", "hide sunlight", "no daylight", "turn off daylight"]):
            return self.toggle_daylight(False)
        
        # Weather and lightning commands
        weather_show_patterns = [
            "show weather", "show clouds", "weather patterns", "show lightning", 
            "lightning detection", "global weather", "show global weather",
            "show me weather", "show me the weather", "weather on globe",
            "show storms", "show storm patterns", "display weather",
            "show weather patterns", "show the weather patterns",
            "weather with lightning", "show weather with lightning"
        ]
        if any(phrase in text_lower for phrase in weather_show_patterns):
            return self.toggle_weather(True)
        
        weather_hide_patterns = [
            "hide weather", "hide clouds", "hide lightning",
            "turn off weather", "remove weather", "no weather"
        ]
        if any(phrase in text_lower for phrase in weather_hide_patterns):
            return self.toggle_weather(False)
        
        # Conflict/war zone commands
        if any(phrase in text_lower for phrase in ["show war", "war zones", "show conflicts", "conflict zones", "show fighting", "active conflicts"]):
            return self.toggle_conflicts(True)
        
        if any(phrase in text_lower for phrase in ["hide war", "hide conflicts"]):
            return self.toggle_conflicts(False)
        
        # Disaster zone commands
        if any(phrase in text_lower for phrase in ["show disasters", "disaster zones", "natural disasters", "show earthquakes", "show storms"]):
            return self.toggle_disasters(True)
        
        if any(phrase in text_lower for phrase in ["hide disasters"]):
            return self.toggle_disasters(False)
        
        # Military installation commands
        if any(phrase in text_lower for phrase in ["show military", "military bases", "military installations", "show bases"]):
            return self.toggle_military(True)
        
        if any(phrase in text_lower for phrase in ["hide military", "hide bases"]):
            return self.toggle_military(False)
        
        # ===== RESEARCH COMMANDS =====
        research_patterns = [
            "research ", "study ", "investigate ", "look up ", "find information on ",
            "scholarly search ", "academic search ", "search for papers on "
        ]
        for pattern in research_patterns:
            if pattern in text_lower:
                topic = text_lower.split(pattern)[-1].strip()
                if topic and len(topic) > 2:
                    return self.start_research(topic)
        
        # Close research window
        if any(phrase in text_lower for phrase in ["close research", "hide research", "stop research"]):
            return self.close_research()
        
        # Add research note
        if "add note" in text_lower or "note that" in text_lower:
            note = text_lower.split("note")[-1].strip()
            if note:
                return self.add_research_note(note)
        
        # Translation commands
        translate_patterns = ["translate ", "say in ", "how do you say "]
        for pattern in translate_patterns:
            if pattern in text_lower:
                # Extract text and target language
                parts = text_lower.split(pattern)[-1]
                return self.translate_text(parts)
        
        # Region highlighting commands ("show me Europe", "highlight Asia")
        region_patterns = ["show me ", "highlight ", "show "]
        for pattern in region_patterns:
            if pattern in text_lower:
                region = text_lower.split(pattern)[-1].strip()
                # Check if it's a continent or region
                if self.earth_data:
                    result = self.earth_data.find_region_by_query(region)
                    if result:
                        return self.highlight_region(result['name'], result.get('boundary'))
        
        # Monica orb commands - "Monica show yourself" / "Monica go away"
        show_orb_patterns = [
            "show yourself", "appear", "show your form", "materialize",
            "come out", "reveal yourself", "show me yourself"
        ]
        if any(phrase in text_lower for phrase in show_orb_patterns):
            return self.show_monica_orb()
        
        hide_orb_patterns = [
            "go away", "disappear", "hide yourself", "dematerialize",
            "leave", "vanish", "hide your form"
        ]
        if any(phrase in text_lower for phrase in hide_orb_patterns):
            return self.hide_monica_orb()
        
        # ===== WINDOW/GLOBE MOVEMENT COMMANDS =====
        # Move globe/window in direction
        move_patterns = {
            'left': ['move left', 'go left', 'shift left', 'pan left'],
            'right': ['move right', 'go right', 'shift right', 'pan right'],
            'up': ['move up', 'go up', 'shift up', 'pan up'],
            'down': ['move down', 'go down', 'shift down', 'pan down']
        }
        for direction, patterns in move_patterns.items():
            if any(p in text_lower for p in patterns):
                return self.move_view(direction)
        
        # ===== EXPAND/ZOOM WINDOW COMMANDS =====
        expand_patterns = ['expand window', 'expand the window', 'expand image', 
                          'expand the image', 'make bigger', 'enlarge window',
                          'maximize window', 'full screen', 'fullscreen']
        if any(p in text_lower for p in expand_patterns):
            return self.expand_city_window()
        
        # ===== NEARBY/LOCAL AREA DETECTION =====
        # "near me", "in my area", "nearby" = user's location
        # "nearest", "in the city", or just asking while viewing city = city in window
        my_area_patterns = ['near me', 'in my area', 'nearby me', 'around me', 
                           'close to me', 'my location', 'where i am']
        city_area_patterns = ['nearest', 'in the city', 'in this city', 'in that city',
                             'show me the nearest', 'find nearest', 'local', 'nearby']
        
        # Check for POI searches with location context
        poi_types = {
            'school': ['school', 'schools', 'university', 'college', 'education'],
            'restaurant': ['restaurant', 'restaurants', 'food', 'eat', 'dining', 'places to eat'],
            'hospital': ['hospital', 'hospitals', 'medical', 'clinic', 'emergency', 'doctor'],
            'hotel': ['hotel', 'hotels', 'motel', 'lodging', 'stay', 'accommodation'],
            'store': ['store', 'stores', 'shop', 'shops', 'shopping', 'mall'],
            'webcam': ['webcam', 'webcams', 'camera', 'cameras', 'cam', 'cams', 'live feed']
        }
        
        for poi_type, keywords in poi_types.items():
            if any(kw in text_lower for kw in keywords):
                # Determine if user's area or city window
                # If user says "near me" or "in my area" -> user's location
                # Otherwise, if we're viewing a city -> use that city
                use_my_location = any(p in text_lower for p in my_area_patterns)
                
                # If not explicitly "near me" and we're viewing a city, use the city
                if not use_my_location and hasattr(self, 'current_city_name') and self.current_city_name:
                    use_my_location = False  # Use the city we're viewing
                
                return self.search_poi_with_context(poi_type, use_my_location)
        
        # ===== COMPILE LIST COMMAND =====
        list_patterns = ['compile a list', 'list them', 'list them for me', 
                        'show me a list', 'make a list', 'give me a list']
        if any(p in text_lower for p in list_patterns):
            return self.compile_poi_list()
        
        # ===== SHOW SPECIFIC WEBCAM BY NAME =====
        show_cam_patterns = ['show me ', 'open ', 'display ']
        for pattern in show_cam_patterns:
            if pattern in text_lower and ('cam' in text_lower or 'camera' in text_lower or 'feed' in text_lower):
                # Extract the name after the pattern
                name = text_lower.split(pattern)[-1].strip()
                name = name.replace(' camera', '').replace(' cam', '').replace(' feed', '').strip()
                if name and len(name) > 2:
                    return self.show_webcam_by_name(name)
        
        # ===== EXIT WEBCAM / RETURN TO LIST =====
        exit_cam_patterns = ['get out of the cam', 'exit cam', 'close cam', 'back to list',
                            'return to list', 'exit camera', 'close camera', 'leave cam']
        if any(p in text_lower for p in exit_cam_patterns):
            return self.exit_webcam_to_list()
        
        # ===== RETURN TO CITY VIEW =====
        city_view_patterns = ['return to city', 'city view', 'city zoom', 'back to city',
                             'return to the city', 'go back to city', 'show city again']
        if any(p in text_lower for p in city_view_patterns):
            return self.return_to_city_view()
        
        # ===== REAL-TIME WEATHER ON GLOBE =====
        realtime_weather_patterns = ['real time weather', 'realtime weather', 'real-time weather',
                                    'live weather', 'current weather on globe', 'show cloud movements',
                                    'global weather', 'weather on the globe']
        if any(p in text_lower for p in realtime_weather_patterns):
            return self.show_realtime_weather()
        
        return None
    
    def show_monica_orb(self) -> str:
        """Show Monica's orb with materialization effect."""
        if self.orb_window:
            # Start the window thread if not running
            if not self.orb_window.running:
                self.orb_window.start()
            # Now show the orb with materialization
            self.orb_window.show()
            return ""  # The orb will speak the materialization phrases
        return "Orb window not available."
    
    def hide_monica_orb(self) -> str:
        """Hide Monica's orb with dematerialization effect."""
        if self.orb_window:
            self.orb_window.hide()
            return "Fading away..."
        return "Orb window not available."
    
    def set_orb_speaking(self, speaking: bool, intensity: float = 0.5):
        """Set the orb's speaking state for animation."""
        if self.orb_window:
            self.orb_window.set_speaking(speaking, intensity)
    
    def _render_orb_in_frame(self, frame: np.ndarray) -> np.ndarray:
        """Render Monica's orb directly into the camera frame (appears behind user).
        
        Features:
        - Electricity sparks during materialization
        - Jupiter-like swirling plasma clouds
        - Color changes based on speech intensity
        - Room brightness effect during formation
        - Pulsating plasma core
        """
        if not self.orb_window:
            return frame
        
        try:
            import math
            import random
            from monica_orb_window import OrbState
            
            h, w = frame.shape[:2]
            
            # Position orb in upper right area (behind user's shoulder)
            orb_center_x = int(w * 0.75)
            orb_center_y = int(h * 0.35)
            orb_radius = int(min(w, h) * 0.18)  # Slightly larger
            
            # Get orb state
            orb = self.orb_window
            alpha = orb.visibility if hasattr(orb, 'visibility') else 1.0
            is_speaking = orb.is_speaking if hasattr(orb, 'is_speaking') else False
            speak_intensity = orb.speak_intensity if hasattr(orb, 'speak_intensity') else 0.0
            
            if alpha < 0.01:
                return frame
            
            # Animation time
            t = time.time()
            
            # === JUPITER-LIKE COLOR PALETTE (changes with speech) ===
            # Base colors cycle through Jupiter-like oranges, browns, whites
            color_phase = t * 0.5 + (speak_intensity * 2 if is_speaking else 0)
            
            # Jupiter palette: orange, brown, cream, white bands
            jupiter_colors = [
                (100, 140, 220),   # BGR - orange/tan
                (120, 160, 200),   # BGR - lighter orange
                (180, 200, 230),   # BGR - cream
                (80, 100, 180),    # BGR - brown band
                (200, 220, 240),   # BGR - white band
                (60, 120, 200),    # BGR - deep orange
            ]
            
            # Select color based on phase and speech
            color_idx = int(color_phase) % len(jupiter_colors)
            next_idx = (color_idx + 1) % len(jupiter_colors)
            blend = color_phase % 1.0
            
            base_color = tuple(int(jupiter_colors[color_idx][i] * (1 - blend) + 
                                   jupiter_colors[next_idx][i] * blend) for i in range(3))
            
            # Speaking makes it brighter/more cyan
            if is_speaking:
                speak_boost = speak_intensity * 0.5
                base_color = tuple(int(min(255, c + 50 * speak_boost)) for c in base_color)
            
            # Pulse effect - stronger when speaking
            pulse_speed = 3 + (speak_intensity * 5 if is_speaking else 0)
            pulse = 1.0 + 0.15 * math.sin(t * pulse_speed)
            current_radius = int(orb_radius * pulse * alpha)
            
            # === ROOM BRIGHTNESS EFFECT (during materialization) ===
            if orb.state == OrbState.MATERIALIZING:
                # Brighten the entire frame based on materialization progress
                brightness_factor = alpha * 0.3  # Up to 30% brighter
                if brightness_factor > 0.05:
                    bright_overlay = np.ones_like(frame, dtype=np.float32) * 255
                    frame = cv2.addWeighted(frame, 1.0, bright_overlay.astype(np.uint8), brightness_factor, 0)
            
            # === ELECTRICITY SPARKS (during materialization) ===
            if orb.state == OrbState.MATERIALIZING or orb.state == OrbState.DEMATERIALIZING:
                # More bolts during early materialization
                num_bolts = random.randint(8, 15) if alpha < 0.5 else random.randint(3, 6)
                
                for _ in range(num_bolts):
                    # Random angle from center
                    angle = random.uniform(0, 2 * math.pi)
                    
                    # Start from FAR outside (edge of screen), end at center
                    start_dist = random.uniform(current_radius * 2, current_radius * 4)
                    start_x = int(orb_center_x + start_dist * math.cos(angle))
                    start_y = int(orb_center_y + start_dist * math.sin(angle))
                    
                    end_dist = random.uniform(0, current_radius * 0.4)
                    end_angle = random.uniform(0, 2 * math.pi)
                    end_x = int(orb_center_x + end_dist * math.cos(end_angle))
                    end_y = int(orb_center_y + end_dist * math.sin(end_angle))
                    
                    # Draw jagged lightning with more segments
                    points = [(start_x, start_y)]
                    num_segs = random.randint(6, 12)
                    for i in range(num_segs):
                        progress = (i + 1) / num_segs
                        base_x = start_x + (end_x - start_x) * progress
                        base_y = start_y + (end_y - start_y) * progress
                        jitter = (1 - progress) * 50  # More jitter
                        px = int(base_x + random.uniform(-jitter, jitter))
                        py = int(base_y + random.uniform(-jitter, jitter))
                        points.append((px, py))
                    
                    # Draw lightning with intense glow
                    bolt_alpha = alpha * random.uniform(0.6, 1.0)
                    bolt_color = (255, 220, 180)  # Bright electric blue-white
                    
                    for i in range(len(points) - 1):
                        # Outer glow (wide)
                        cv2.line(frame, points[i], points[i+1], 
                                (int(bolt_color[0] * bolt_alpha * 0.2), 
                                 int(bolt_color[1] * bolt_alpha * 0.2), 
                                 int(bolt_color[2] * bolt_alpha * 0.2)), 
                                12, cv2.LINE_AA)
                        # Middle glow
                        cv2.line(frame, points[i], points[i+1],
                                (int(bolt_color[0] * bolt_alpha * 0.5), 
                                 int(bolt_color[1] * bolt_alpha * 0.5), 
                                 int(bolt_color[2] * bolt_alpha * 0.5)),
                                6, cv2.LINE_AA)
                        # Inner glow
                        cv2.line(frame, points[i], points[i+1],
                                (int(bolt_color[0] * bolt_alpha * 0.8), 
                                 int(bolt_color[1] * bolt_alpha * 0.8), 
                                 int(bolt_color[2] * bolt_alpha * 0.8)),
                                3, cv2.LINE_AA)
                        # Core (white hot)
                        cv2.line(frame, points[i], points[i+1],
                                (255, 255, 255),
                                1, cv2.LINE_AA)
            
            if current_radius < 5:
                return frame
            
            # === MASSIVE OUTER GLOW (room-filling brightness) ===
            for i in range(12, 0, -1):
                glow_radius = current_radius + i * 25
                glow_alpha = 0.12 * (13 - i) / 12 * alpha
                glow_color = tuple(int(min(255, c * glow_alpha * 1.2)) for c in base_color)
                cv2.circle(frame, (orb_center_x, orb_center_y), glow_radius, glow_color, 4, cv2.LINE_AA)
            
            # === JUPITER-LIKE SWIRLING BANDS ===
            num_bands = 8
            for band in range(num_bands):
                band_offset = band * (current_radius // num_bands)
                band_radius = current_radius - band_offset
                if band_radius < 5:
                    continue
                
                # Swirl angle changes with time and band
                swirl = t * (0.5 + band * 0.1) + band * 0.7
                
                # Band color varies
                band_color_idx = (color_idx + band) % len(jupiter_colors)
                band_color = jupiter_colors[band_color_idx]
                
                # Draw arc segments for swirling effect
                for seg in range(6):
                    start_angle = int((swirl + seg * 60) % 360)
                    end_angle = start_angle + 40
                    
                    seg_alpha = alpha * (0.4 + 0.3 * math.sin(t * 2 + band + seg))
                    seg_color = tuple(int(min(255, c * seg_alpha)) for c in band_color)
                    
                    cv2.ellipse(frame, (orb_center_x, orb_center_y), 
                               (band_radius, int(band_radius * 0.9)),
                               0, start_angle, end_angle, seg_color, 3, cv2.LINE_AA)
            
            # === PLASMA CORE with turbulence ===
            for r in range(current_radius, 0, -4):
                ratio = r / current_radius
                intensity = 0.4 + 0.6 * (1 - ratio) ** 1.2
                
                # Turbulent variation
                turb = math.sin(t * 4 + r * 0.08) * 0.2 + math.cos(t * 3 + r * 0.12) * 0.15
                pulse_var = 1 + turb
                
                layer_color = tuple(int(min(255, c * intensity * pulse_var * alpha)) for c in base_color)
                cv2.circle(frame, (orb_center_x, orb_center_y), r, layer_color, 3, cv2.LINE_AA)
            
            # === BRIGHT CORE (white hot center) ===
            core_radius = int(current_radius * 0.3)
            
            # Core pulses more when speaking
            core_pulse = 1 + 0.2 * math.sin(t * 8) + (speak_intensity * 0.3 if is_speaking else 0)
            core_radius = int(core_radius * core_pulse)
            
            # Gradient core
            for cr in range(core_radius, 0, -2):
                cr_ratio = cr / core_radius
                cr_intensity = 1.5 - cr_ratio * 0.5
                core_color = tuple(int(min(255, c * cr_intensity * alpha)) for c in base_color)
                cv2.circle(frame, (orb_center_x, orb_center_y), cr, core_color, -1, cv2.LINE_AA)
            
            # White hot center
            cv2.circle(frame, (orb_center_x, orb_center_y), max(3, int(core_radius * 0.4)), 
                      (255, 255, 255), -1, cv2.LINE_AA)
            
        except Exception as e:
            print(f"[ORB-RENDER] Error: {e}")
            import traceback
            traceback.print_exc()
        
        return frame
    
    def toggle_daylight(self, show: bool) -> str:
        """Toggle day/night visualization on the globe."""
        self.globe_state.show_daylight = show
        if show:
            return "Showing day and night areas on the globe."
        else:
            return "Hiding daylight visualization."
    
    def toggle_weather(self, show: bool) -> str:
        """Toggle weather/lightning visualization."""
        self.globe_state.show_weather = show
        self.globe_state.show_lightning = show
        if show:
            return "Showing weather patterns and lightning detection on the globe."
        else:
            return "Hiding weather visualization."
    
    def toggle_conflicts(self, show: bool) -> str:
        """Toggle conflict/war zone visualization."""
        self.globe_state.show_conflicts = show
        if show:
            return "Showing current war zones and conflict areas on the globe."
        else:
            return "Hiding conflict zones."
    
    def toggle_disasters(self, show: bool) -> str:
        """Toggle disaster zone visualization."""
        self.globe_state.show_disasters = show
        if show:
            return "Showing current natural disasters on the globe."
        else:
            return "Hiding disaster zones."
    
    def toggle_military(self, show: bool) -> str:
        """Toggle military installation visualization."""
        self.globe_state.show_military = show
        if show:
            return "Showing known military installations on the globe."
        else:
            return "Hiding military installations."
    
    # ==================== Globe/City Window Control ====================
    
    def move_view(self, direction: str) -> str:
        """Move the globe or city window in specified direction. CRASH-SAFE."""
        try:
            amount = 30  # pixels
            
            # Initialize offsets if they don't exist
            if not hasattr(self, 'hologram_position_offset_x'):
                self.hologram_position_offset_x = 0
            if not hasattr(self, 'hologram_position_offset_y'):
                self.hologram_position_offset_y = 0
            
            if direction == 'left':
                self.hologram_position_offset_x -= amount
                if hasattr(self, 'globe_state') and self.globe_state:
                    self.globe_state.rotation_y -= 10
            elif direction == 'right':
                self.hologram_position_offset_x += amount
                if hasattr(self, 'globe_state') and self.globe_state:
                    self.globe_state.rotation_y += 10
            elif direction == 'up':
                self.hologram_position_offset_y -= amount
                if hasattr(self, 'globe_state') and self.globe_state:
                    self.globe_state.rotation_x -= 5
            elif direction == 'down':
                self.hologram_position_offset_y += amount
                if hasattr(self, 'globe_state') and self.globe_state:
                    self.globe_state.rotation_x += 5
            
            return f"Moving {direction}."
        except Exception as e:
            print(f"[AR] Move error (safe): {e}")
            return f"Moving {direction}."
    
    def expand_city_window(self) -> str:
        """Expand/maximize the city window. CRASH-SAFE."""
        try:
            # Initialize if needed
            if not hasattr(self, 'hologram_scale'):
                self.hologram_scale = 0.3
            if not hasattr(self, 'map_window_scale'):
                self.map_window_scale = 1.0
            
            self.hologram_scale = min(0.9, self.hologram_scale + 0.2)
            self.map_window_scale = min(2.0, self.map_window_scale + 0.4)
            
            # Also zoom in on the globe if viewing city
            if hasattr(self, 'globe_state') and self.globe_state:
                self.globe_state.zoom = min(3.0, getattr(self.globe_state, 'zoom', 1.0) + 0.5)
            
            return "Expanding and zooming in on the city view."
        except Exception as e:
            print(f"[AR] Expand error (safe): {e}")
            return "Expanding window."
    
    def zoom_in(self) -> str:
        """Zoom in on current view. CRASH-SAFE."""
        try:
            if hasattr(self, 'globe_state') and self.globe_state:
                self.globe_state.zoom = min(4.0, getattr(self.globe_state, 'zoom', 1.0) + 0.3)
            if not hasattr(self, 'hologram_scale'):
                self.hologram_scale = 0.3
            self.hologram_scale = min(0.9, self.hologram_scale + 0.1)
            
            try:
                self._play_ui_sound("zoom")
            except:
                pass
            
            return "Zooming in."
        except Exception as e:
            print(f"[AR] Zoom in error (safe): {e}")
            return "Zooming in."
    
    def zoom_out(self) -> str:
        """Zoom out from current view. CRASH-SAFE."""
        try:
            if hasattr(self, 'globe_state') and self.globe_state:
                self.globe_state.zoom = max(0.5, getattr(self.globe_state, 'zoom', 1.0) - 0.3)
            if not hasattr(self, 'hologram_scale'):
                self.hologram_scale = 0.3
            self.hologram_scale = max(0.2, self.hologram_scale - 0.1)
            
            try:
                self._play_ui_sound("zoom")
            except:
                pass
            
            return "Zooming out."
        except Exception as e:
            print(f"[AR] Zoom out error (safe): {e}")
            return "Zooming out."
    
    def search_poi_with_context(self, poi_type: str, use_my_location: bool) -> str:
        """Search for POI with location context (user's area vs city in window). CRASH-SAFE."""
        try:
            if use_my_location:
                # Use user's actual location
                lat = getattr(self.globe_state, 'user_lat', 40.7128) if hasattr(self, 'globe_state') else 40.7128
                lng = getattr(self.globe_state, 'user_lng', -74.006) if hasattr(self, 'globe_state') else -74.006
                location_name = "your area"
            else:
                # Use the city currently being viewed
                lat = getattr(self.globe_state, 'target_lat', 40.7128) if hasattr(self, 'globe_state') else 40.7128
                lng = getattr(self.globe_state, 'target_lng', -74.006) if hasattr(self, 'globe_state') else -74.006
                location_name = getattr(self, 'current_city_name', 'the city')
                if not location_name or location_name == 'the city':
                    location_name = f"the area at {lat:.2f}, {lng:.2f}"
            
            # Store POI results for later listing
            if not hasattr(self, 'current_poi_results'):
                self.current_poi_results = []
            
            # Generate sample POI data with positions
            poi_data = {
                'school': [
                    {'name': 'Central High School', 'x': 0.3, 'y': 0.4, 'color': (255, 200, 0)},
                    {'name': 'Lincoln Elementary', 'x': 0.6, 'y': 0.3, 'color': (255, 200, 0)},
                    {'name': 'State University', 'x': 0.7, 'y': 0.6, 'color': (255, 200, 0)},
                    {'name': 'Community College', 'x': 0.2, 'y': 0.7, 'color': (255, 200, 0)},
                ],
                'restaurant': [
                    {'name': 'The Italian Place', 'x': 0.4, 'y': 0.5, 'color': (0, 165, 255)},
                    {'name': 'Golden Dragon', 'x': 0.5, 'y': 0.4, 'color': (0, 165, 255)},
                    {'name': 'Burger Palace', 'x': 0.3, 'y': 0.6, 'color': (0, 165, 255)},
                    {'name': 'Cafe Mocha', 'x': 0.7, 'y': 0.3, 'color': (0, 165, 255)},
                ],
                'hospital': [
                    {'name': 'City General Hospital', 'x': 0.5, 'y': 0.5, 'color': (0, 0, 255)},
                    {'name': 'St. Mary Medical Center', 'x': 0.2, 'y': 0.4, 'color': (0, 0, 255)},
                    {'name': 'Emergency Care Clinic', 'x': 0.8, 'y': 0.6, 'color': (0, 0, 255)},
                ],
                'hotel': [
                    {'name': 'Grand Plaza Hotel', 'x': 0.5, 'y': 0.3, 'color': (255, 0, 255)},
                    {'name': 'City Inn', 'x': 0.3, 'y': 0.5, 'color': (255, 0, 255)},
                    {'name': 'Comfort Suites', 'x': 0.7, 'y': 0.7, 'color': (255, 0, 255)},
                ],
                'store': [
                    {'name': 'Main Street Mall', 'x': 0.4, 'y': 0.4, 'color': (0, 255, 0)},
                    {'name': 'Corner Grocery', 'x': 0.6, 'y': 0.5, 'color': (0, 255, 0)},
                    {'name': 'Tech Electronics', 'x': 0.2, 'y': 0.3, 'color': (0, 255, 0)},
                    {'name': 'Fashion Outlet', 'x': 0.8, 'y': 0.4, 'color': (0, 255, 0)},
                ],
                'webcam': [
                    {'name': 'Downtown Camera', 'x': 0.5, 'y': 0.5, 'color': (255, 255, 0)},
                    {'name': 'Beach View Cam', 'x': 0.8, 'y': 0.3, 'color': (255, 255, 0)},
                    {'name': 'City Hall Live', 'x': 0.3, 'y': 0.4, 'color': (255, 255, 0)},
                    {'name': 'Park Webcam', 'x': 0.6, 'y': 0.7, 'color': (255, 255, 0)},
                ],
            }
            
            self.current_poi_results = poi_data.get(poi_type, [])
            self.current_poi_type = poi_type
            self.show_poi_markers = True
            self.poi_pulse_time = time.time()
            self.current_city_name = location_name
            
            return f"Showing {len(self.current_poi_results)} {poi_type}s in {location_name}. I'm highlighting them with pulsating markers."
        except Exception as e:
            print(f"[AR] POI search error (safe): {e}")
            return f"Searching for {poi_type}s..."
    
    def compile_poi_list(self) -> str:
        """Compile and display a list of POI results in the window."""
        if not hasattr(self, 'current_poi_results') or not self.current_poi_results:
            return "No search results to list. Please search for something first."
        
        self.show_poi_list = True
        self.poi_list_scroll = 0
        
        poi_type = getattr(self, 'current_poi_type', 'items')
        return f"Listing {len(self.current_poi_results)} {poi_type}s."
    
    def show_webcam_by_name(self, name: str) -> str:
        """Show a specific webcam by its name."""
        if hasattr(self, 'current_poi_results'):
            for cam in self.current_poi_results:
                if name.lower() in cam.lower():
                    self.active_webcam_name = cam
                    self.show_webcam_fullscreen = True
                    return f"Showing {cam}."
        return f"Could not find webcam named '{name}'."
    
    def exit_webcam_to_list(self) -> str:
        """Exit current webcam view and return to the list."""
        self.show_webcam_fullscreen = False
        self.show_poi_list = True
        return "Returning to the list."
    
    def return_to_city_view(self) -> str:
        """Return to the city view with highlighted POIs."""
        self.show_webcam_fullscreen = False
        self.show_poi_list = False
        self.show_poi_markers = True
        return "Returning to city view with highlighted locations."
    
    def return_to_globe(self) -> str:
        """Zoom back out to globe view with animation."""
        self.show_poi_markers = False
        self.show_poi_list = False
        self.show_webcam_fullscreen = False
        
        # Animate zoom out
        self.globe_state.zoom = 1.0
        self.globe_state.is_zooming = True
        self.globe_state.zoom_progress = 0.0
        
        self._play_ui_sound("zoom")
        return "Zooming back out to globe view."
    
    def show_realtime_weather(self) -> str:
        """Show real-time weather with cloud movements on globe."""
        self.globe_state.show_weather = True
        self.globe_state.show_lightning = True
        self.realtime_weather_enabled = True
        return "Showing real-time weather patterns with cloud movements on the globe."
    
    # ==================== Research System ====================
    
    def start_research(self, topic: str) -> str:
        """
        Start a research session on a topic.
        Opens the Matrix-style green research window.
        """
        if not HAS_RESEARCH_SYSTEM:
            return "Research system not available."
        
        research_window = get_research_window()
        research_window.start_research(topic)
        
        # Show research window
        self.active_hologram = HologramType.RESEARCH_WINDOW
        self._play_ui_sound("success")
        
        print(f"[AR] Starting research on: {topic}")
        return f"Starting scholarly research on '{topic}'. Searching academic databases..."
    
    def close_research(self) -> str:
        """Close the research window."""
        if HAS_RESEARCH_SYSTEM:
            research_window = get_research_window()
            research_window.close()
        
        self.active_hologram = HologramType.NONE
        self._play_ui_sound("close")
        return "Research window closed."
    
    def add_research_note(self, note: str) -> str:
        """Add a note to the current research session."""
        if not HAS_RESEARCH_SYSTEM:
            return "Research system not available."
        
        research_window = get_research_window()
        return research_window.add_note(note)
    
    def translate_text(self, text: str) -> str:
        """
        Translate text to another language.
        Parses input like "hello to spanish" or "bonjour to english"
        """
        if not HAS_RESEARCH_SYSTEM:
            return "Translation not available."
        
        lang_support = get_language_support()
        
        # Parse target language from text
        target_lang = "es"  # Default to Spanish
        source_text = text
        
        # Check for "to [language]" pattern
        lang_map = {
            "spanish": "es", "french": "fr", "german": "de",
            "italian": "it", "portuguese": "pt", "chinese": "zh",
            "japanese": "ja", "korean": "ko", "arabic": "ar",
            "russian": "ru", "hindi": "hi", "english": "en"
        }
        
        for lang_name, lang_code in lang_map.items():
            if f" to {lang_name}" in text.lower():
                target_lang = lang_code
                source_text = text.lower().replace(f" to {lang_name}", "").strip()
                break
            if f" in {lang_name}" in text.lower():
                target_lang = lang_code
                source_text = text.lower().replace(f" in {lang_name}", "").strip()
                break
        
        # Translate
        translated = lang_support.translate(source_text, target_lang)
        target_name = lang_support.get_language_name(target_lang)
        
        return f"In {target_name}: {translated}"
    
    def highlight_region(self, region_name: str, boundary: Optional[List] = None) -> str:
        """
        Highlight a specific region or continent on the globe.
        Also rotates the globe to face that region.
        """
        self.globe_state.highlighted_region = region_name
        self.globe_state.highlighted_region_bounds = boundary
        
        # Find center of region and rotate to face it
        if self.earth_data:
            result = self.earth_data.find_region_by_query(region_name)
            if result and 'center' in result:
                center_lat, center_lng = result['center']
                self.globe_state.rotation_y = -math.radians(center_lng)
                self.globe_state.rotation_x = math.radians(center_lat) * 0.3
        
        return f"Highlighting {region_name} on the globe."
    
    def zoom_to_city_level(self) -> str:
        """
        Zoom to city level using Free Maps (ESRI) or Google Maps.
        Uses the currently highlighted city or user's location.
        """
        if not self.free_maps and not self.google_maps:
            return "Map integration not available."
        
        # Determine which location to zoom to
        if self.globe_state.highlighted_city:
            lat = self.globe_state.target_lat
            lng = self.globe_state.target_lng
            city_name = self.globe_state.highlighted_city
        else:
            lat = self.globe_state.user_lat
            lng = self.globe_state.user_lng
            city_name = self.globe_state.user_location_name
        
        # Activate city view
        self.city_view_active = True
        self.city_view_location = (lat, lng, city_name)
        
        # Fetch city map - prefer free maps
        if self.free_maps:
            self.city_view_image = self.free_maps.fetch_composite_map(lat, lng, 16, (640, 640))
            provider = self.free_maps.current_provider
            return f"Zooming to city level: {city_name} (using {provider} - FREE!)"
        elif self.google_maps:
            self.google_maps.get_city_view(lat, lng, zoom=16)
            self.city_view_image = self.google_maps.city_view_image
            return f"Zooming to city level: {city_name} (using Google Maps)"
        
        return f"Zooming to city level: {city_name}"
    
    def exit_city_view(self) -> str:
        """Exit city-level view and return to globe."""
        self.city_view_active = False
        self.city_view_location = None
        if self.google_maps:
            self.google_maps.exit_city_view()
        return "Returning to globe view."
    
    def toggle_webcam_markers(self, show: bool) -> str:
        """Toggle webcam location markers on the globe."""
        self.show_webcam_markers = show
        if show:
            return "Showing webcam locations on the globe."
        else:
            return "Hiding webcam markers."
    
    def toggle_satellite_view(self, show: bool) -> str:
        """Toggle satellite/terrain texture on the globe."""
        self.use_satellite_texture = show
        if show:
            return "Switching to satellite view."
        else:
            return "Switching to holographic wireframe view."
    
    def _render_city_view(self, frame: np.ndarray) -> np.ndarray:
        """
        Render the city-level map view (Free Maps or Google Maps). CRASH-SAFE.
        """
        try:
            if not self.city_view_active:
                return frame
            
            h, w = frame.shape[:2]
            
            # Get city map from stored image or Google Maps
            city_map = getattr(self, 'city_view_image', None)
            if city_map is None and self.google_maps:
                city_map = getattr(self.google_maps, 'city_view_image', None)
            
            # If no map image, create a placeholder
            if city_map is None:
                map_size = int(min(w, h) * 0.5)
                city_map = np.zeros((map_size, map_size, 3), dtype=np.uint8)
                city_map[:, :] = (30, 30, 30)  # Dark gray background
                
                # Draw "Loading..." text
                cv2.putText(city_map, "Loading map...", (map_size // 4, map_size // 2),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (100, 100, 100), 2)
                
                # Draw grid lines
                for i in range(0, map_size, 50):
                    cv2.line(city_map, (i, 0), (i, map_size), (50, 50, 50), 1)
                    cv2.line(city_map, (0, i), (map_size, i), (50, 50, 50), 1)
            
            # Calculate position (same as globe)
            map_size = int(min(w, h) * 0.5)
            offset_x = getattr(self, 'hologram_position_offset_x', 0)
            offset_y = getattr(self, 'hologram_position_offset_y', 0)
            
            if self.hologram_position == "right":
                center_x = w - map_size // 2 - 50 + offset_x
            else:
                center_x = w // 2 + offset_x
            
            center_y = h // 2 + offset_y
            
            # Resize map to fit
            map_resized = cv2.resize(city_map, (map_size, map_size))
            
            # Calculate placement
            x1 = center_x - map_size // 2
            y1 = center_y - map_size // 2
            x2 = x1 + map_size
            y2 = y1 + map_size
            
            # Clip to frame bounds
            x1_clip = max(0, x1)
            y1_clip = max(0, y1)
            x2_clip = min(w, x2)
            y2_clip = min(h, y2)
            
            # Calculate corresponding map region
            mx1 = x1_clip - x1
            my1 = y1_clip - y1
            mx2 = map_size - (x2 - x2_clip)
            my2 = map_size - (y2 - y2_clip)
            
            if mx2 > mx1 and my2 > my1:
                # Build a holographic overlay for the map region with a strong blue tint
                overlay = np.zeros_like(frame)
                map_region = map_resized[my1:my2, mx1:mx2].copy()
                tint = np.full_like(map_region, (180, 120, 40))  # Deep blue/cyan tint (BGR)
                holographic_region = cv2.addWeighted(map_region, 0.25, tint, 0.75, 0)
                overlay[y1_clip:y2_clip, x1_clip:x2_clip] = holographic_region
                
                # Apply glow and blend strongly over the camera feed
                glow = cv2.GaussianBlur(overlay, (0, 0), sigmaX=14, sigmaY=14)
                hologram = cv2.addWeighted(glow, 0.6, overlay, 1.0, 0)
                frame = cv2.addWeighted(hologram, 0.9, frame, 0.1, 0)
            
            # Draw border
            cv2.rectangle(frame, (x1_clip, y1_clip), (x2_clip-1, y2_clip-1), (0, 255, 255), 2)
            
            # Draw title
            if hasattr(self, 'city_view_location') and self.city_view_location:
                if isinstance(self.city_view_location, tuple) and len(self.city_view_location) >= 3:
                    title = f"CITY VIEW: {self.city_view_location[2]}"
                else:
                    title = f"CITY VIEW: {self.city_view_location}"
                cv2.putText(frame, title, (x1_clip + 10, y1_clip + 25),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                
                # Draw "Back to Globe" hint
                hint = "Say 'back to globe' to exit"
                cv2.putText(frame, hint, (x1_clip + 10, y2_clip - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
            
            return frame
        except Exception as e:
            print(f"[AR] City view render error (safe): {e}")
            return frame
    
    def cleanup(self):
        """Clean up resources."""
        self.webcam_stop_event.set()
        if self.webcam_thread:
            self.webcam_thread.join(timeout=1)
        print("[AR] Hologram system cleaned up")


# Singleton instance
_ar_hologram_system = None

def get_ar_hologram_system() -> MonicaARHologramSystem:
    """Get the singleton AR hologram system instance."""
    global _ar_hologram_system
    if _ar_hologram_system is None:
        _ar_hologram_system = MonicaARHologramSystem()
    return _ar_hologram_system
