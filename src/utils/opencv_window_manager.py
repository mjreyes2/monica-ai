"""
OpenCV Window Manager - Proper Threading Solution
Generates frames in background threads, displays in main thread
"""
import cv2
import numpy as np
import threading
import queue
import time
import math
from typing import Optional, Dict, Any


class OpenCVWindowManager:
    """Manages OpenCV windows with proper threading"""
    
    def __init__(self):
        self.windows: Dict[str, Dict[str, Any]] = {}
        self.display_thread = None
        self.running = False
        self.frame_queue = queue.Queue(maxsize=10)
        
    def start(self):
        """Start the display thread"""
        if not self.running:
            self.running = True
            self.display_thread = threading.Thread(target=self._display_loop, daemon=True)
            self.display_thread.start()
            
    def stop(self):
        """Stop all windows and display thread"""
        self.running = False
        # Clear all windows
        for window_name in list(self.windows.keys()):
            self.close_window(window_name)
        # Signal display thread to stop
        try:
            self.frame_queue.put(None, timeout=0.1)
        except:
            pass
        if self.display_thread:
            self.display_thread.join(timeout=1.0)
            
    def create_window(self, name: str, width: int, height: int, generator_func):
        """Create a new window with frame generator"""
        if name in self.windows:
            return
            
        window_info = {
            'name': name,
            'width': width,
            'height': height,
            'generator': generator_func,
            'thread': None,
            'visible': False,
            'running': False
        }
        
        self.windows[name] = window_info
        
        # Start display thread if not running
        self.start()
        
    def show_window(self, name: str):
        """Show a window"""
        if name not in self.windows:
            return
            
        window = self.windows[name]
        if not window['running']:
            window['running'] = True
            window['visible'] = True
            # Start frame generation thread
            window['thread'] = threading.Thread(
                target=self._generate_frames, 
                args=(name,), 
                daemon=True
            )
            window['thread'].start()
        else:
            window['visible'] = True
            
    def hide_window(self, name: str):
        """Hide a window"""
        if name not in self.windows:
            return
        self.windows[name]['visible'] = False
        
    def close_window(self, name: str):
        """Close a window"""
        if name not in self.windows:
            return
            
        window = self.windows[name]
        window['running'] = False
        window['visible'] = False
        
        if window['thread']:
            window['thread'].join(timeout=0.5)
            
        # Close OpenCV window
        try:
            cv2.destroyWindow(name)
        except:
            pass
            
        del self.windows[name]
        
    def _generate_frames(self, name: str):
        """Generate frames in background thread"""
        window = self.windows[name]
        generator = window['generator']
        
        while window['running']:
            try:
                frame = generator()
                if frame is not None:
                    # Put frame in queue for display
                    try:
                        self.frame_queue.put((name, frame), timeout=0.1)
                    except queue.Full:
                        pass  # Skip frame if queue is full
                time.sleep(0.033)  # ~30 FPS
            except Exception as e:
                print(f"[Window] Error generating frame for {name}: {e}")
                time.sleep(0.1)
                
    def _display_loop(self):
        """Display frames in main thread"""
        while self.running:
            try:
                # Get frame from queue
                item = self.frame_queue.get(timeout=0.1)
                if item is None:  # Stop signal
                    break
                    
                name, frame = item
                window = self.windows.get(name)
                
                if window and window['visible']:
                    # Resize frame if needed
                    if frame.shape[:2] != (window['height'], window['width']):
                        frame = cv2.resize(frame, (window['width'], window['height']))
                    
                    # Display frame
                    cv2.imshow(name, frame)
                    
                # Process OpenCV events
                key = cv2.waitKey(1) & 0xFF
                if key == 27:  # ESC
                    break
                    
            except queue.Empty:
                # No frames, just process events
                cv2.waitKey(1)
            except Exception as e:
                print(f"[Window] Display error: {e}")
                time.sleep(0.1)
                
        # Cleanup
        cv2.destroyAllWindows()


# Global window manager instance
_window_manager: Optional[OpenCVWindowManager] = None

_orb_active: bool = False
_orb_energy: float = 0.0


def get_window_manager() -> OpenCVWindowManager:
    """Get global window manager instance"""
    global _window_manager
    if _window_manager is None:
        _window_manager = OpenCVWindowManager()
    return _window_manager


def set_orb_active(active: bool) -> None:
    global _orb_active
    _orb_active = bool(active)


def is_orb_active() -> bool:
    return bool(_orb_active)


def set_orb_energy(energy: float) -> None:
    global _orb_energy
    try:
        _orb_energy = float(energy)
    except Exception:
        _orb_energy = 0.0
    if _orb_energy < 0.0:
        _orb_energy = 0.0
    if _orb_energy > 1.0:
        _orb_energy = 1.0


def get_orb_energy() -> float:
    try:
        v = float(_orb_energy)
    except Exception:
        return 0.0
    if v < 0.0:
        return 0.0
    if v > 1.0:
        return 1.0
    return v


# Orb formation state
_orb_formation_start = 0.0
_orb_is_speaking = False

# Pre-computed arrays for performance (cached)
_orb_cache = {}

def set_orb_speaking(speaking: bool):
    """Set whether Monica is currently speaking (for yellow speech indicator)"""
    global _orb_is_speaking
    _orb_is_speaking = speaking

def is_orb_speaking() -> bool:
    return _orb_is_speaking

def reset_orb_formation():
    """Reset orb formation timer when orb becomes active"""
    global _orb_formation_start
    _orb_formation_start = time.time()

def _get_orb_cache(width, height):
    """Get or create cached arrays for orb rendering"""
    global _orb_cache
    key = (width, height)
    if key not in _orb_cache:
        xs = np.linspace(-1.0, 1.0, width, dtype=np.float32)
        ys = np.linspace(-1.0, 1.0, height, dtype=np.float32)
        xv, yv = np.meshgrid(xs, ys)
        r = np.sqrt(xv * xv + yv * yv)
        theta = np.arctan2(yv, xv)
        _orb_cache[key] = {
            'xv': xv, 'yv': yv, 'r': r, 'theta': theta,
            'center': (width // 2, height // 2),
            'green_bg': np.full((height, width, 3), (0, 255, 0), dtype=np.uint8)
        }
    return _orb_cache[key]


# Frame generators for different AR effects
def orb_frame_generator():
    """Generate orb animation frames - OPTIMIZED with longer formation"""
    global _orb_formation_start
    
    width, height = 500, 500
    time_val = time.time()
    
    # Get cached arrays
    cache = _get_orb_cache(width, height)
    xv, yv, r, theta = cache['xv'], cache['yv'], cache['r'], cache['theta']
    center_x, center_y = cache['center']
    
    # Green background (copy from cache)
    frame = cache['green_bg'].copy()

    if not is_orb_active():
        _orb_formation_start = 0.0
        return frame

    # Initialize formation start time
    if _orb_formation_start == 0.0:
        _orb_formation_start = time_val

    # Formation phases - EXTENDED for visibility
    elapsed = time_val - _orb_formation_start
    PHASE_ELECTRICITY = 0.0      # 0-3s: electricity sparks appear
    PHASE_CONVERGE = 3.0         # 3-6s: sparks converge to center  
    PHASE_GLOW = 6.0             # 6-9s: center glow forms and grows
    PHASE_BOOM = 9.0             # 9-10s: bright flash
    PHASE_SETTLE = 10.0          # 10s+: settle to baseline

    # ============================================================
    # PHASE 1: ELECTRICITY SPARKS (0-3s) - OPTIMIZED
    # ============================================================
    if elapsed < PHASE_CONVERGE:
        # Fewer sparks, simpler rendering
        num_sparks = 12
        spark_phase = elapsed / PHASE_CONVERGE  # 0 to 1
        
        for i in range(num_sparks):
            # Sparks orbit around edges
            angle = (i / num_sparks) * 2 * math.pi + time_val * 2
            
            # Sparks start far and move closer over time
            dist = 0.85 - spark_phase * 0.4
            
            sx = int(center_x + dist * (width // 2) * math.cos(angle))
            sy = int(center_y + dist * (height // 2) * math.sin(angle))
            
            # Flickering blue-white spark
            flicker = int(155 + 100 * math.sin(time_val * 20 + i * 5))
            spark_color = (255, 255, flicker)
            
            if 0 <= sx < width and 0 <= sy < height:
                # Draw spark glow
                cv2.circle(frame, (sx, sy), 6, spark_color, -1)
                cv2.circle(frame, (sx, sy), 10, (150, 150, 100), 2)
                
                # Lightning toward center (after 1s)
                if elapsed > 1.0:
                    progress = min(1.0, (elapsed - 1.0) / 2.0)
                    tx = int(sx + (center_x - sx) * progress * 0.7)
                    ty = int(sy + (center_y - sy) * progress * 0.7)
                    
                    # Simple jagged line (fewer points for speed)
                    mid_x = (sx + tx) // 2 + int(20 * math.sin(time_val * 30 + i))
                    mid_y = (sy + ty) // 2 + int(20 * math.cos(time_val * 30 + i))
                    
                    cv2.line(frame, (sx, sy), (mid_x, mid_y), spark_color, 2)
                    cv2.line(frame, (mid_x, mid_y), (tx, ty), spark_color, 2)
        
        # Growing center glow (after 2s)
        if elapsed > 2.0:
            glow_progress = (elapsed - 2.0) / 1.0
            glow_size = int(15 + 40 * glow_progress)
            glow_bright = int(150 + 105 * glow_progress)
            cv2.circle(frame, (center_x, center_y), glow_size, (glow_bright, glow_bright, 255), -1)
            cv2.circle(frame, (center_x, center_y), glow_size + 10, (100, 100, 200), 3)
        
        return frame

    # ============================================================
    # PHASE 2: GLOW FORMS AND GROWS (6-9s) - OPTIMIZED
    # ============================================================
    if elapsed < PHASE_BOOM:
        progress = (elapsed - PHASE_CONVERGE) / (PHASE_BOOM - PHASE_CONVERGE)
        
        # Growing orb radius
        current_radius = 0.15 + 0.47 * progress
        brightness = 0.6 + 0.4 * progress
        
        # Simple circular mask (no expensive operations)
        mask = np.clip(1.0 - (r - current_radius) / 0.1, 0.0, 1.0)
        mask = (mask * mask).astype(np.float32)
        
        # Swirling energy effect (simplified)
        swirl = 0.7 + 0.3 * np.sin(theta * 3 + time_val * 4)
        
        # Create glow
        glow_b = (255 * brightness * mask * swirl).astype(np.uint8)
        glow_g = (200 * brightness * mask * swirl).astype(np.uint8)
        glow_r = (255 * brightness * mask * swirl).astype(np.uint8)
        
        # Composite
        mask_inv = 1.0 - mask
        frame[:, :, 0] = (frame[:, :, 0] * mask_inv + glow_b * mask).astype(np.uint8)
        frame[:, :, 1] = (frame[:, :, 1] * mask_inv + glow_g * mask).astype(np.uint8)
        frame[:, :, 2] = (frame[:, :, 2] * mask_inv + glow_r * mask).astype(np.uint8)
        
        return frame

    # ============================================================
    # PHASE 3: BOOM FLASH (9-10s)
    # ============================================================
    if elapsed < PHASE_SETTLE:
        progress = (elapsed - PHASE_BOOM) / (PHASE_SETTLE - PHASE_BOOM)
        flash_intensity = 1.0 - progress
        
        # Full orb mask
        orb_radius = 0.62
        mask = np.clip(1.0 - (r - orb_radius) / 0.08, 0.0, 1.0)
        mask = (mask * mask * flash_intensity).astype(np.float32)
        
        # White flash
        frame[:, :, 0] = np.clip(frame[:, :, 0] + (255 * mask), 0, 255).astype(np.uint8)
        frame[:, :, 1] = np.clip(frame[:, :, 1] + (255 * mask), 0, 255).astype(np.uint8)
        frame[:, :, 2] = np.clip(frame[:, :, 2] + (255 * mask), 0, 255).astype(np.uint8)
        
        return frame

    # ============================================================
    # PHASE 4: SETTLED ORB - OPTIMIZED gravitational mist
    # ============================================================
    base_radius = 0.62
    pulse = 0.025 * math.sin(time_val * 2.0)
    orb_radius = base_radius + pulse

    # Simple mask
    mask = np.clip(1.0 - (r - orb_radius) / 0.08, 0.0, 1.0)
    mask = (mask * mask).astype(np.float32)

    # Gravitational mist - SIMPLIFIED for performance
    grav_cycle = math.sin(time_val * 0.4)  # Slow breathing
    
    # Single-layer noise (much faster)
    t = time_val * 0.8
    noise = np.sin(xv * 4 + t) * np.cos(yv * 4 - t) + np.sin(r * 8 - t * 2) * grav_cycle
    noise = (noise - noise.min()) / (noise.max() - noise.min() + 1e-6)
    
    # Single blur pass
    noise_u8 = (noise * 255).astype(np.uint8)
    mist = cv2.GaussianBlur(noise_u8, (15, 15), 0)
    
    # Color shift
    color_shift = int((time_val * 25) % 256)
    mist_shifted = ((mist.astype(np.int32) + color_shift) % 256).astype(np.uint8)
    
    # Single colormap
    plasma = cv2.applyColorMap(mist_shifted, cv2.COLORMAP_TURBO)

    # Brightness
    energy = get_orb_energy()
    brightness = 0.75 + 0.15 * math.sin(time_val * 3) + 0.2 * energy
    
    plasma = np.clip(plasma * brightness, 0, 255).astype(np.uint8)

    # Speech indicator - SIMPLIFIED
    if is_orb_speaking():
        speech_pulse = 0.6 + 0.4 * math.sin(time_val * 12)
        speech_mask = np.exp(-(r / 0.35) ** 2 * 2) * speech_pulse
        
        # Add yellow tint
        plasma[:, :, 1] = np.clip(plasma[:, :, 1] + 80 * speech_mask, 0, 255).astype(np.uint8)
        plasma[:, :, 2] = np.clip(plasma[:, :, 2] + 80 * speech_mask, 0, 255).astype(np.uint8)

    # Final composite
    mask3 = mask[..., None]
    out = plasma * mask3 + frame * (1.0 - mask3)
    return out.astype(np.uint8)


def globe_frame_generator():
    """Generate globe animation frames"""
    width, height = 600, 600
    rotation = time.time() * 0.5
    
    # Green background
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    frame[:, :] = (0, 255, 0)  # Green screen
    
    # Draw globe
    center_x, center_y = width // 2, height // 2
    radius = 150
    
    # Globe outline
    cv2.circle(frame, (center_x, center_y), radius, (255, 255, 255), 2)
    
    # Rotating lines
    for i in range(8):
        angle = rotation + i * math.pi / 4
        x1 = int(center_x + radius * 0.9 * math.cos(angle))
        y1 = int(center_y + radius * 0.3 * math.sin(angle))
        x2 = int(center_x - radius * 0.9 * math.cos(angle))
        y2 = int(center_y - radius * 0.3 * math.sin(angle))
        cv2.line(frame, (x1, y1), (x2, y2), (255, 255, 0), 1)
    
    # Horizontal lines
    for i in range(-2, 3):
        y = int(center_y + i * radius * 0.3)
        x_offset = int(math.sqrt(max(0, radius**2 - (i * radius * 0.3)**2)))
        cv2.line(frame, (center_x - x_offset, y), (center_x + x_offset, y), (255, 255, 0), 1)
    
    return frame


def keyboard_frame_generator():
    """Generate keyboard animation frames"""
    width, height = 800, 300
    
    # Green background
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    frame[:, :] = (0, 255, 0)  # Green screen
    
    # Draw keyboard keys
    keys = "QWERTYUIOPASDFGHJKLZXCVBNM"
    key_width, key_height = 40, 40
    start_x, start_y = 50, 50
    
    # First row
    for i, key in enumerate(keys[:10]):
        x = start_x + i * (key_width + 5)
        y = start_y
        cv2.rectangle(frame, (x, y), (x + key_width, y + key_height), (0, 0, 0), -1)
        cv2.rectangle(frame, (x, y), (x + key_width, y + key_height), (255, 255, 255), 2)
        cv2.putText(frame, key, (x + key_width//2 - 5, y + key_height//2 + 5), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    # Second row
    for i, key in enumerate(keys[10:19]):
        x = start_x + 30 + i * (key_width + 5)
        y = start_y + key_height + 10
        cv2.rectangle(frame, (x, y), (x + key_width, y + key_height), (0, 0, 0), -1)
        cv2.rectangle(frame, (x, y), (x + key_width, y + key_height), (255, 255, 255), 2)
        cv2.putText(frame, key, (x + key_width//2 - 5, y + key_height//2 + 5), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    # Third row
    for i, key in enumerate(keys[19:]):
        x = start_x + 60 + i * (key_width + 5)
        y = start_y + 2 * (key_height + 10)
        cv2.rectangle(frame, (x, y), (x + key_width, y + key_height), (0, 0, 0), -1)
        cv2.rectangle(frame, (x, y), (x + key_width, y + key_height), (255, 255, 255), 2)
        cv2.putText(frame, key, (x + key_width//2 - 5, y + key_height//2 + 5), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    # Text display area
    cv2.rectangle(frame, (50, start_y + 3 * (key_height + 10) + 10), 
                  (750, start_y + 3 * (key_height + 10) + 40), (0, 0, 0), -1)
    cv2.rectangle(frame, (50, start_y + 3 * (key_height + 10) + 10), 
                  (750, start_y + 3 * (key_height + 10) + 40), (255, 255, 255), 2)
    
    return frame


def dial_frame_generator():
    """Generate dial animation frames"""
    width, height = 400, 400
    rotation = time.time() * 0.5
    value = 0.5
    
    # Green background
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    frame[:, :] = (0, 255, 0)  # Green screen
    
    # Draw dial
    center_x, center_y = width // 2, height // 2
    radius = 120
    
    # Outer circle
    cv2.circle(frame, (center_x, center_y), radius, (255, 255, 255), 3)
    
    # Inner circle
    cv2.circle(frame, (center_x, center_y), int(radius * 0.8), (255, 255, 0), 2)
    
    # Tick marks
    for i in range(12):
        angle = i * math.pi / 6
        x1 = int(center_x + radius * 0.9 * math.cos(angle))
        y1 = int(center_y + radius * 0.9 * math.sin(angle))
        x2 = int(center_x + radius * 0.7 * math.cos(angle))
        y2 = int(center_y + radius * 0.7 * math.sin(angle))
        cv2.line(frame, (x1, y1), (x2, y2), (255, 255, 255), 2)
    
    # Needle
    needle_angle = rotation + value * math.pi * 1.5 - math.pi * 0.75
    needle_x = int(center_x + radius * 0.8 * math.cos(needle_angle))
    needle_y = int(center_y + radius * 0.8 * math.sin(needle_angle))
    cv2.line(frame, (center_x, center_y), (needle_x, needle_y), (0, 0, 255), 4)
    
    # Center
    cv2.circle(frame, (center_x, center_y), 10, (0, 0, 0), -1)
    cv2.circle(frame, (center_x, center_y), 10, (255, 255, 255), 2)
    
    # Value text
    cv2.putText(frame, f"Value: {value:.2f}", (center_x - 50, center_y + radius + 30), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    return frame
