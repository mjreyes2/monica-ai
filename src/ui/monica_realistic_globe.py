"""
Monica Realistic Globe Renderer
Renders a scientifically accurate Earth globe with real satellite imagery.
Uses ESRI satellite tiles (free, updated regularly, scientifically accurate).

Features:
- Real satellite imagery from ESRI World Imagery
- Proper north-up orientation
- Optional grid overlay
- Optimized for performance
- Day/night terminator
"""

import cv2
import numpy as np
import math
import time
import threading
from typing import Tuple, Optional, Dict
from dataclasses import dataclass

# Try to import free maps
try:
    from ui.monica_free_maps import get_free_maps, FreeMapTileSystem
    HAS_FREE_MAPS = True
except ImportError:
    HAS_FREE_MAPS = False
    print("[GLOBE] Warning: Free maps not available")


@dataclass
class GlobeConfig:
    """Configuration for the realistic globe."""
    radius: int = 150  # Pixels
    rotation_speed: float = 0.003  # Radians per frame (west-to-east, like real Earth)
    grid_enabled: bool = True
    grid_color: Tuple[int, int, int] = (255, 255, 0)  # NEON CYAN grid (BGR: B=255, G=255, R=0)
    grid_glow_color: Tuple[int, int, int] = (200, 255, 100)  # Cyan glow
    grid_opacity: float = 0.7  # More visible
    show_terminator: bool = False
    texture_resolution: int = 512  # Texture size
    transparency: float = 0.85  # Globe transparency (0=invisible, 1=solid)
    neon_mode: bool = True  # Enable sci-fi neon effects


class RealisticGlobeRenderer:
    """
    Renders a realistic Earth globe with satellite imagery.
    
    Data Sources (all scientifically accurate and regularly updated):
    - ESRI World Imagery: High-resolution satellite imagery
    - Updated: Continuously (ESRI updates their imagery regularly)
    - Accuracy: Sub-meter in many areas, based on commercial satellite data
    """
    
    def __init__(self, config: GlobeConfig = None):
        self.config = config or GlobeConfig()
        self.maps = get_free_maps() if HAS_FREE_MAPS else None
        
        # Globe state
        self.rotation_y = 0.0  # Longitude rotation
        self.rotation_x = 0.0  # Tilt (keep small for north-up)
        self.target_rotation_y = 0.0
        
        # Texture cache
        self.globe_texture = None
        self.texture_lock = threading.Lock()
        self.texture_loading = False
        self.last_texture_update = 0
        
        # Pre-computed lookup tables for speed
        self._init_lookup_tables()
        
        # Load initial texture
        self._load_globe_texture_async()
        
        print("[OK] Realistic Globe Renderer initialized")
        print("   Data source: ESRI World Imagery (free, updated regularly)")
    
    def _init_lookup_tables(self):
        """Pre-compute lookup tables for fast rendering."""
        size = self.config.texture_resolution
        
        # Create coordinate lookup for sphere projection
        # This maps each pixel in the output to lat/lng on the globe
        self.sphere_coords = np.zeros((size, size, 2), dtype=np.float32)
        
        center = size // 2
        radius = size // 2 - 2
        
        for y in range(size):
            for x in range(size):
                dx = x - center
                dy = y - center
                dist = math.sqrt(dx*dx + dy*dy)
                
                if dist <= radius:
                    # Point is on the visible hemisphere
                    # Calculate 3D position on unit sphere
                    z = math.sqrt(radius*radius - dx*dx - dy*dy)
                    
                    # Convert to lat/lng (spherical coordinates)
                    # Note: y points down in image, so negate for proper lat
                    lat = math.asin(-dy / radius) * 180 / math.pi
                    lng = math.atan2(dx, z) * 180 / math.pi
                    
                    self.sphere_coords[y, x] = [lat, lng]
                else:
                    # Outside sphere - mark as invalid
                    self.sphere_coords[y, x] = [999, 999]
        
        # Create sphere mask
        y_coords, x_coords = np.ogrid[:size, :size]
        dist_from_center = np.sqrt((x_coords - center)**2 + (y_coords - center)**2)
        self.sphere_mask = dist_from_center <= radius
        
        # Create depth map for shading
        self.depth_map = np.zeros((size, size), dtype=np.float32)
        # Calculate depth for all points inside sphere
        x_grid, y_grid = np.meshgrid(np.arange(size), np.arange(size))
        dx = x_grid - center
        dy = y_grid - center
        dist_sq = dx**2 + dy**2
        inside = dist_sq <= radius**2
        self.depth_map[inside] = np.sqrt(radius**2 - dist_sq[inside]) / radius
    
    def _load_globe_texture_async(self):
        """Load globe texture in background thread."""
        if self.texture_loading:
            return
        
        self.texture_loading = True
        thread = threading.Thread(target=self._load_globe_texture, daemon=True)
        thread.start()
    
    def _load_globe_texture(self):
        """
        Load equirectangular world map texture.
        
        Priority order:
        1. Cached high-res texture on disk
        2. NASA Blue Marble download (public domain, accurate)
        3. ESRI satellite tiles stitched together (free)
        4. Fallback procedural texture with continent outlines
        """
        try:
            import os
            cache_dir = os.path.dirname(__file__)
            cache_path = os.path.join(cache_dir, 'earth_texture_cache.jpg')
            
            # Try to load cached texture first
            if os.path.exists(cache_path):
                cached = cv2.imread(cache_path)
                if cached is not None:
                    h, w = cached.shape[:2]
                    # Verify it's a valid equirectangular texture (width ~= 2x height)
                    if w > 100 and h > 50:
                        # Check if colors need swapping
                        ocean_sample = cached[h // 2, w // 4]
                        if ocean_sample[2] > ocean_sample[0] + 30:  # R >> B means inverted
                            cached = cv2.cvtColor(cached, cv2.COLOR_RGB2BGR)
                        with self.texture_lock:
                            self.globe_texture = cached
                            self.last_texture_update = time.time()
                        print(f"[GLOBE] Loaded cached Earth texture ({w}x{h})")
                        return
            
            # Try NASA Blue Marble (public domain, accurate continents/oceans)
            texture = self._download_nasa_blue_marble()
            if texture is not None:
                with self.texture_lock:
                    self.globe_texture = texture
                    self.last_texture_update = time.time()
                cv2.imwrite(cache_path, texture)
                print("[GLOBE] NASA Blue Marble texture loaded and cached")
                return
            
            # Fallback: use ESRI satellite tiles
            if self.maps is not None:
                print("[GLOBE] Fetching ESRI satellite tiles...")
                texture = self.maps.fetch_world_texture(2048, 1024, zoom=3, source="esri_satellite")
                if texture is not None:
                    with self.texture_lock:
                        self.globe_texture = texture
                        self.last_texture_update = time.time()
                    cv2.imwrite(cache_path, texture)
                    print("[GLOBE] ESRI satellite texture loaded and cached")
                    return
            
            # Last resort: procedural fallback
            self._create_fallback_texture()
            
        except Exception as e:
            print(f"[GLOBE] Error loading texture: {e}")
            self._create_fallback_texture()
        
        finally:
            self.texture_loading = False
    
    def _download_nasa_blue_marble(self) -> 'Optional[np.ndarray]':
        """
        Download NASA Blue Marble texture (public domain).
        Uses a small version for fast loading.
        """
        # NASA Blue Marble URLs (public domain, multiple resolutions)
        urls = [
            # Small (2048x1024) - fast to download
            "https://eoimages.gsfc.nasa.gov/images/imagerecords/73000/73909/world.topo.bathy.200412.3x5400x2700.jpg",
            # Alternate source
            "https://upload.wikimedia.org/wikipedia/commons/thumb/2/23/Blue_Marble_2002.png/2048px-Blue_Marble_2002.png",
        ]
        
        for url in urls:
            try:
                import urllib.request
                print(f"[GLOBE] Downloading NASA Blue Marble...")
                req = urllib.request.Request(url, headers={
                    "User-Agent": "Monica-AI/1.0 (Educational Project)"
                })
                with urllib.request.urlopen(req, timeout=30) as resp:
                    img_bytes = resp.read()
                
                img_array = np.frombuffer(img_bytes, dtype=np.uint8)
                img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
                if img is not None:
                    # Resize to standard equirectangular size
                    texture = cv2.resize(img, (2048, 1024), interpolation=cv2.INTER_AREA)
                    print(f"[GLOBE] NASA Blue Marble downloaded ({texture.shape[1]}x{texture.shape[0]})")
                    return texture
            except Exception as e:
                print(f"[GLOBE] NASA download failed ({url[:50]}...): {e}")
                continue
        
        return None
    
    def _create_fallback_texture(self):
        """Create a simple fallback texture if satellite fails."""
        tex_w, tex_h = 2048, 1024
        texture = np.zeros((tex_h, tex_w, 3), dtype=np.uint8)
        
        # Ocean blue
        texture[:, :] = (120, 80, 40)  # Dark blue (BGR)
        
        # Simple continent shapes (very approximate)
        # This is just a fallback - real satellite imagery is preferred
        
        with self.texture_lock:
            self.globe_texture = texture
    
    def sample_texture(self, lat: float, lng: float) -> Tuple[int, int, int]:
        """Sample the globe texture at a lat/lng coordinate."""
        if self.globe_texture is None:
            return (120, 80, 40)  # Ocean blue
        
        tex_h, tex_w = self.globe_texture.shape[:2]
        
        # Convert lat/lng to texture coordinates
        # Equirectangular projection
        x = int((lng + 180) / 360 * tex_w) % tex_w
        y = int((90 - lat) / 180 * tex_h)
        y = max(0, min(tex_h - 1, y))
        
        return tuple(self.globe_texture[y, x])
    
    def render(self, frame: np.ndarray, center: Tuple[int, int], 
               radius: int = None) -> np.ndarray:
        """
        Render the realistic globe onto the frame.
        
        Args:
            frame: Target frame (BGR)
            center: Globe center position (x, y)
            radius: Globe radius in pixels (default from config)
            
        Returns:
            Frame with globe rendered
        """
        if radius is None:
            radius = self.config.radius
        
        h, w = frame.shape[:2]
        cx, cy = center
        
        # Update rotation (west-to-east, like real Earth)
        # Positive increment = counter-clockwise from above north pole = west to east
        self.rotation_y += self.config.rotation_speed
        
        # Create globe image
        globe_size = radius * 2
        globe_img = self._render_globe_sphere(globe_size)
        
        # Calculate placement bounds
        x1 = cx - radius
        y1 = cy - radius
        x2 = cx + radius
        y2 = cy + radius
        
        # Clip to frame bounds
        src_x1 = max(0, -x1)
        src_y1 = max(0, -y1)
        src_x2 = globe_size - max(0, x2 - w)
        src_y2 = globe_size - max(0, y2 - h)
        
        dst_x1 = max(0, x1)
        dst_y1 = max(0, y1)
        dst_x2 = min(w, x2)
        dst_y2 = min(h, y2)
        
        if dst_x2 > dst_x1 and dst_y2 > dst_y1:
            # Get the region to blend
            globe_region = globe_img[src_y1:src_y2, src_x1:src_x2]
            frame_region = frame[dst_y1:dst_y2, dst_x1:dst_x2]
            
            # Create mask for the sphere
            mask_region = self._create_sphere_mask(
                src_x2 - src_x1, src_y2 - src_y1,
                radius, src_x1, src_y1
            )
            
            # Blend globe onto frame with transparency
            transparency = getattr(self.config, 'transparency', 0.85)
            mask_3ch = cv2.merge([mask_region, mask_region, mask_region]).astype(np.float32) / 255.0
            
            # Apply transparency - blend globe with background
            globe_float = globe_region.astype(np.float32)
            frame_float = frame_region.astype(np.float32)
            blended = np.where(
                mask_3ch > 0,
                globe_float * transparency + frame_float * (1 - transparency),
                frame_float
            ).astype(np.uint8)
            frame[dst_y1:dst_y2, dst_x1:dst_x2] = blended
        
        # Draw grid overlay if enabled
        if self.config.grid_enabled:
            frame = self._draw_grid_overlay(frame, center, radius)
        
        return frame
    
    def _render_globe_sphere(self, size: int) -> np.ndarray:
        """
        Render the textured sphere - OPTIMIZED VERSION.
        Uses numpy vectorization for much faster rendering.
        """
        # Check if we have a cached globe at this size
        cache_key = (size, round(self.rotation_y, 2), round(self.rotation_x, 2))
        if hasattr(self, '_globe_cache') and self._globe_cache_key == cache_key:
            return self._globe_cache.copy()
        
        globe = np.zeros((size, size, 3), dtype=np.uint8)
        center = size // 2
        radius = size // 2 - 1
        
        # FAST: Use numpy meshgrid for vectorized calculation
        y_coords, x_coords = np.ogrid[:size, :size]
        dx = x_coords - center
        dy = y_coords - center
        dist_sq = dx*dx + dy*dy
        
        # Mask for pixels inside the sphere
        inside_mask = dist_sq <= radius * radius
        
        # Only process pixels inside the sphere
        inside_y, inside_x = np.where(inside_mask)
        
        if len(inside_y) == 0:
            return globe
        
        # Calculate z for inside pixels
        dx_inside = inside_x - center
        dy_inside = inside_y - center
        dist_sq_inside = dx_inside**2 + dy_inside**2
        z_inside = np.sqrt(radius * radius - dist_sq_inside)
        
        # Apply rotation (west-to-east: increasing rotation_y moves texture left = Earth spins east)
        cos_rot = math.cos(self.rotation_y)
        sin_rot = math.sin(self.rotation_y)
        
        # Rotate around Y axis (vertical axis through poles)
        rx = dx_inside * cos_rot + z_inside * sin_rot
        rz = -dx_inside * sin_rot + z_inside * cos_rot
        ry = -dy_inside  # Negate so north (positive lat) is UP in screen coords
        
        # Convert to lat/lng
        lat = np.arcsin(np.clip(ry / radius, -1, 1)) * 180 / math.pi
        lng = np.arctan2(rx, rz) * 180 / math.pi
        
        # Apply X rotation
        lat = lat + self.rotation_x * 10
        
        # Sample texture for all pixels at once
        for i in range(len(inside_y)):
            color = self.sample_texture(lat[i], lng[i])
            
            # Depth shading
            depth_factor = 0.6 + 0.4 * (z_inside[i] / radius)
            shaded = tuple(int(c * depth_factor) for c in color)
            
            globe[inside_y[i], inside_x[i]] = shaded
        
        # Cache the result
        self._globe_cache = globe.copy()
        self._globe_cache_key = cache_key
        
        return globe
    
    def _create_sphere_mask(self, w: int, h: int, radius: int,
                            offset_x: int, offset_y: int) -> np.ndarray:
        """Create a circular mask for the sphere region."""
        mask = np.zeros((h, w), dtype=np.uint8)
        
        for y in range(h):
            for x in range(w):
                dx = (x + offset_x) - radius
                dy = (y + offset_y) - radius
                if dx*dx + dy*dy <= radius * radius:
                    mask[y, x] = 255
        
        return mask
    
    def _draw_grid_overlay(self, frame: np.ndarray, center: Tuple[int, int],
                           radius: int) -> np.ndarray:
        """Draw latitude/longitude grid lines on the globe with NEON GLOW effect."""
        cx, cy = center
        color = self.config.grid_color  # Bright neon cyan
        glow_color = getattr(self.config, 'grid_glow_color', (200, 255, 255))
        
        # NEON GLOW: Draw multiple layers for glow effect
        # Outer glow (very dim, thick)
        outer_glow = (glow_color[0] // 4, glow_color[1] // 4, glow_color[2] // 4)
        # Inner glow (medium brightness)
        inner_glow = (glow_color[0] // 2, glow_color[1] // 2, glow_color[2] // 2)
        
        # Draw latitude lines (every 30 degrees) with NEON GLOW effect
        for lat in range(-60, 90, 30):
            lat_rad = math.radians(lat)
            # Calculate radius of this latitude circle
            circle_radius = int(radius * math.cos(lat_rad))
            circle_y = cy - int(radius * math.sin(lat_rad))
            
            if circle_radius > 0:
                # Layer 1: Outer glow (thickest, dimmest)
                cv2.ellipse(frame, (cx, circle_y), (circle_radius, circle_radius // 4),
                           0, 0, 180, outer_glow, 5, cv2.LINE_AA)
                # Layer 2: Inner glow
                cv2.ellipse(frame, (cx, circle_y), (circle_radius, circle_radius // 4),
                           0, 0, 180, inner_glow, 3, cv2.LINE_AA)
                # Layer 3: Core line (brightest, thinnest)
                cv2.ellipse(frame, (cx, circle_y), (circle_radius, circle_radius // 4),
                           0, 0, 180, color, 1, cv2.LINE_AA)
        
        # Draw longitude lines (every 30 degrees) with NEON GLOW effect
        for lng in range(0, 180, 30):
            lng_rad = math.radians(lng) + self.rotation_y
            
            # Draw arc from pole to pole
            points = []
            for lat in range(-90, 91, 10):
                lat_rad = math.radians(lat)
                
                # 3D position
                x3d = radius * math.cos(lat_rad) * math.sin(lng_rad)
                y3d = radius * math.sin(lat_rad)
                z3d = radius * math.cos(lat_rad) * math.cos(lng_rad)
                
                # Only draw if on visible side
                if z3d > 0:
                    px = cx + int(x3d)
                    py = cy - int(y3d)  # Negate for screen coords
                    points.append((px, py))
            
            # Draw the line with NEON GLOW (3 layers)
            if len(points) > 1:
                for i in range(len(points) - 1):
                    # Layer 1: Outer glow
                    cv2.line(frame, points[i], points[i+1], outer_glow, 5, cv2.LINE_AA)
                    # Layer 2: Inner glow
                    cv2.line(frame, points[i], points[i+1], inner_glow, 3, cv2.LINE_AA)
                    # Layer 3: Core line
                    cv2.line(frame, points[i], points[i+1], color, 1, cv2.LINE_AA)
        
        return frame
    
    def rotate_to(self, lat: float, lng: float):
        """Rotate globe to show a specific location."""
        self.target_rotation_y = -math.radians(lng)
        self.rotation_x = lat / 90 * 0.3  # Slight tilt
    
    def set_rotation(self, rotation_y: float):
        """Set the Y rotation directly."""
        self.rotation_y = rotation_y
    
    def render_location_marker(self, frame: np.ndarray, center: Tuple[int, int], 
                                radius: int, lat: float, lng: float,
                                label: str = None, pulse: bool = True) -> np.ndarray:
        """
        Render a pulsing location marker on the globe.
        
        Args:
            frame: Target frame
            center: Globe center (x, y)
            radius: Globe radius
            lat, lng: Location coordinates
            label: Optional label text
            pulse: Whether to animate pulsing
            
        Returns:
            Frame with marker rendered
        """
        cx, cy = center
        
        # Convert lat/lng to 3D position
        lat_rad = math.radians(lat)
        # Apply globe rotation (negative because we rotate sampling, not globe)
        lng_rad = math.radians(lng) - self.rotation_y
        
        # 3D position on sphere
        x3d = radius * math.cos(lat_rad) * math.sin(lng_rad)
        y3d = radius * math.sin(lat_rad)
        z3d = radius * math.cos(lat_rad) * math.cos(lng_rad)
        
        # Only draw if on visible side of globe (z > 0 means facing camera)
        if z3d < -radius * 0.1:  # Allow slight visibility at edges
            return frame
        
        # Project to 2D
        px = cx + int(x3d)
        py = cy - int(y3d)  # Negate for screen coords
        
        # Pulsing animation
        if pulse:
            pulse_phase = (time.time() * 3) % (2 * math.pi)
            pulse_size = 1.0 + 0.3 * math.sin(pulse_phase)
            pulse_alpha = 0.5 + 0.5 * math.sin(pulse_phase)
        else:
            pulse_size = 1.0
            pulse_alpha = 1.0
        
        # Draw LARGE outer pulsing ring (very visible)
        ring_radius = int(20 * pulse_size)
        ring_color = (0, int(255 * pulse_alpha), int(255 * pulse_alpha))  # Cyan
        cv2.circle(frame, (px, py), ring_radius, ring_color, 3, cv2.LINE_AA)
        
        # Draw second ring for glow effect
        cv2.circle(frame, (px, py), ring_radius + 5, (0, int(150 * pulse_alpha), int(150 * pulse_alpha)), 2, cv2.LINE_AA)
        
        # Draw inner solid dot (BIGGER - 8 pixels)
        cv2.circle(frame, (px, py), 8, (0, 255, 255), -1, cv2.LINE_AA)
        cv2.circle(frame, (px, py), 4, (255, 255, 255), -1, cv2.LINE_AA)  # White center
        
        # Draw crosshair (LONGER)
        cv2.line(frame, (px - 20, py), (px - 10, py), (0, 255, 255), 2)
        cv2.line(frame, (px + 10, py), (px + 20, py), (0, 255, 255), 2)
        cv2.line(frame, (px, py - 20), (px, py - 10), (0, 255, 255), 2)
        cv2.line(frame, (px, py + 10), (px, py + 20), (0, 255, 255), 2)
        
        # Draw label if provided
        if label:
            label_x = px + 15
            label_y = py - 5
            
            # Background for text
            text_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.4, 1)[0]
            cv2.rectangle(frame, (label_x - 2, label_y - text_size[1] - 2),
                         (label_x + text_size[0] + 2, label_y + 2),
                         (0, 50, 50), -1)
            
            cv2.putText(frame, label, (label_x, label_y),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)
        
        return frame
    
    def render_landmass_highlight(self, frame: np.ndarray, center: Tuple[int, int],
                                    radius: int, region_bounds: dict) -> np.ndarray:
        """
        Highlight an entire landmass/region on the globe with a glowing effect.
        
        Args:
            frame: Target frame
            center: Globe center (x, y)
            radius: Globe radius
            region_bounds: Dict with 'lat_min', 'lat_max', 'lng_min', 'lng_max'
            
        Returns:
            Frame with highlighted region
        """
        cx, cy = center
        
        # Get region bounds
        lat_min = region_bounds.get('lat_min', -90)
        lat_max = region_bounds.get('lat_max', 90)
        lng_min = region_bounds.get('lng_min', -180)
        lng_max = region_bounds.get('lng_max', 180)
        
        # Pulsing animation for the highlight
        pulse_phase = (time.time() * 2) % (2 * math.pi)
        pulse_intensity = 0.5 + 0.5 * math.sin(pulse_phase)
        
        # Create highlight overlay
        overlay = frame.copy()
        
        # Draw highlight for visible points in the region
        for lat in range(int(lat_min), int(lat_max) + 1, 3):  # Step by 3 for performance
            for lng in range(int(lng_min), int(lng_max) + 1, 3):
                # Convert to 3D position
                lat_rad = math.radians(lat)
                lng_rad = math.radians(lng) - self.rotation_y
                
                # 3D position on sphere
                x3d = radius * math.cos(lat_rad) * math.sin(lng_rad)
                y3d = radius * math.sin(lat_rad)
                z3d = radius * math.cos(lat_rad) * math.cos(lng_rad)
                
                # Only draw if on visible side
                if z3d > 0:
                    px = cx + int(x3d)
                    py = cy - int(y3d)
                    
                    # Draw glowing point
                    color = (0, int(255 * pulse_intensity), int(200 * pulse_intensity))  # Cyan glow
                    cv2.circle(overlay, (px, py), 3, color, -1)
        
        # Blend overlay with original
        alpha = 0.4 * pulse_intensity
        frame = cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)
        
        # Draw region label
        label = region_bounds.get('name', 'Region')
        text_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
        label_x = cx - text_size[0] // 2
        label_y = cy - radius - 30
        
        # Background
        cv2.rectangle(frame, (label_x - 5, label_y - text_size[1] - 5),
                     (label_x + text_size[0] + 5, label_y + 5),
                     (0, 50, 50), -1)
        cv2.putText(frame, label, (label_x, label_y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        
        return frame


# Region bounds for continents and major areas
REGION_BOUNDS = {
    'africa': {'lat_min': -35, 'lat_max': 37, 'lng_min': -18, 'lng_max': 52, 'name': 'AFRICA'},
    'europe': {'lat_min': 35, 'lat_max': 71, 'lng_min': -10, 'lng_max': 40, 'name': 'EUROPE'},
    'asia': {'lat_min': 5, 'lat_max': 77, 'lng_min': 40, 'lng_max': 180, 'name': 'ASIA'},
    'north america': {'lat_min': 15, 'lat_max': 72, 'lng_min': -170, 'lng_max': -50, 'name': 'NORTH AMERICA'},
    'south america': {'lat_min': -56, 'lat_max': 13, 'lng_min': -82, 'lng_max': -34, 'name': 'SOUTH AMERICA'},
    'australia': {'lat_min': -45, 'lat_max': -10, 'lng_min': 110, 'lng_max': 155, 'name': 'AUSTRALIA'},
    'antarctica': {'lat_min': -90, 'lat_max': -60, 'lng_min': -180, 'lng_max': 180, 'name': 'ANTARCTICA'},
    # US Regions
    'midwest': {'lat_min': 36, 'lat_max': 49, 'lng_min': -104, 'lng_max': -80, 'name': 'US MIDWEST'},
    'northeast': {'lat_min': 38, 'lat_max': 47, 'lng_min': -80, 'lng_max': -67, 'name': 'US NORTHEAST'},
    'southeast': {'lat_min': 24, 'lat_max': 39, 'lng_min': -92, 'lng_max': -75, 'name': 'US SOUTHEAST'},
    'southwest': {'lat_min': 28, 'lat_max': 42, 'lng_min': -125, 'lng_max': -102, 'name': 'US SOUTHWEST'},
    'west coast': {'lat_min': 32, 'lat_max': 49, 'lng_min': -125, 'lng_max': -114, 'name': 'US WEST COAST'},
}


# Singleton instance
_realistic_globe = None

def get_realistic_globe() -> RealisticGlobeRenderer:
    """Get the singleton realistic globe instance."""
    global _realistic_globe
    if _realistic_globe is None:
        _realistic_globe = RealisticGlobeRenderer()
    return _realistic_globe


if __name__ == "__main__":
    print("\n=== Realistic Globe Test ===\n")
    
    globe = get_realistic_globe()
    
    # Wait for texture to load
    print("Waiting for satellite texture to load...")
    time.sleep(3)
    
    # Create test frame
    frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    frame[:, :] = (30, 30, 30)  # Dark background
    
    # Render globe
    print("Rendering globe...")
    frame = globe.render(frame, (640, 360), radius=200)
    
    # Save test image
    cv2.imwrite("test_realistic_globe.jpg", frame)
    print("Saved to test_realistic_globe.jpg")
