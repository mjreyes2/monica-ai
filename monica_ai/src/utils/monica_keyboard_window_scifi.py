"""
Monica Sci-Fi Holographic Keyboard - Round Layout with Alien Hieroglyphs
Features:
- Circular/round keyboard layout
- Alien hieroglyphs instead of letters
- Glowing neon effects (bright cyan/magenta/yellow)
- Fingertip highlighting for both index fingers
- Keyboard click sounds
- Energy trails between keys
"""
import cv2
import numpy as np
import math
import time
import random
import threading
import os
from typing import Tuple, Optional, Dict, List, Callable
from dataclasses import dataclass

# Green screen color (pure green for chroma key)
GREEN_SCREEN = (0, 255, 0)  # BGR

# Try to import pygame for sound effects
HAS_PYGAME = False
try:
    import pygame
    if not pygame.mixer.get_init():
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
    HAS_PYGAME = True
except:
    pass


def generate_alien_hieroglyph(seed: int) -> np.ndarray:
    """
    Generate a unique alien hieroglyph symbol.
    Returns a 40x40 image with the symbol.
    """
    img = np.zeros((40, 40, 3), dtype=np.uint8)
    random.seed(seed)
    
    # Random geometric alien symbol
    symbol_type = random.randint(0, 5)
    color = (255, 200, 100)  # Cyan glow
    
    if symbol_type == 0:
        # Angular lines
        pts = []
        for _ in range(random.randint(3, 6)):
            pts.append((random.randint(5, 35), random.randint(5, 35)))
        pts = np.array(pts, np.int32)
        cv2.polylines(img, [pts], False, color, 2, cv2.LINE_AA)
    
    elif symbol_type == 1:
        # Circles with lines
        cv2.circle(img, (20, 20), 12, color, 2, cv2.LINE_AA)
        cv2.line(img, (20, 8), (20, 32), color, 2, cv2.LINE_AA)
        cv2.line(img, (8, 20), (32, 20), color, 2, cv2.LINE_AA)
    
    elif symbol_type == 2:
        # Triangle with inner pattern
        pts = np.array([[20, 5], [35, 30], [5, 30]], np.int32)
        cv2.polylines(img, [pts], True, color, 2, cv2.LINE_AA)
        cv2.circle(img, (20, 20), 5, color, 1, cv2.LINE_AA)
    
    elif symbol_type == 3:
        # Spiral-like
        for i in range(0, 360, 30):
            angle = math.radians(i)
            r = 5 + i / 30
            x = int(20 + r * math.cos(angle))
            y = int(20 + r * math.sin(angle))
            cv2.circle(img, (x, y), 2, color, -1, cv2.LINE_AA)
    
    elif symbol_type == 4:
        # Cross with dots
        cv2.line(img, (10, 20), (30, 20), color, 2, cv2.LINE_AA)
        cv2.line(img, (20, 10), (20, 30), color, 2, cv2.LINE_AA)
        for x, y in [(10, 10), (30, 10), (10, 30), (30, 30)]:
            cv2.circle(img, (x, y), 3, color, -1, cv2.LINE_AA)
    
    else:
        # Diamond with inner lines
        pts = np.array([[20, 5], [35, 20], [20, 35], [5, 20]], np.int32)
        cv2.polylines(img, [pts], True, color, 2, cv2.LINE_AA)
        cv2.line(img, (20, 5), (20, 35), color, 1, cv2.LINE_AA)
        cv2.line(img, (5, 20), (35, 20), color, 1, cv2.LINE_AA)
    
    return img


@dataclass
class RoundKeyState:
    """State of a keyboard key in round layout."""
    label: str
    char: str  # Actual character to type
    angle: float  # Position angle in radians
    radius: float  # Distance from center
    size: int  # Key size
    hieroglyph: np.ndarray  # Alien symbol image
    pressed: bool = False
    press_time: float = 0.0
    glow_phase: float = 0.0


class MonicaSciFiKeyboard:
    """
    Sci-fi holographic keyboard with round layout and alien hieroglyphs.
    Green screen background for OBS chroma key.
    """
    
    def __init__(self, width: int = 900, height: int = 900):
        self.width = width
        self.height = height
        self.center = (width // 2, height // 2)
        
        # State
        self.visible = False
        self.running = False
        self.thread: Optional[threading.Thread] = None
        
        # Animation
        self.last_update = time.time()
        self.materialize_progress = 0.0
        self.is_materializing = False
        self.is_dematerializing = False
        self.glow_phase = 0.0
        self.rotation = 0.0
        
        # Keyboard layout
        self.keys: List[RoundKeyState] = []
        self.typed_text = ""
        self.max_text_length = 50
        
        # Fingertip tracking
        self.left_index_pos: Optional[Tuple[int, int]] = None
        self.right_index_pos: Optional[Tuple[int, int]] = None
        self.fingertip_radius = 30  # Detection radius
        
        # Colors (neon sci-fi theme)
        self.key_color = (255, 180, 80)  # Cyan
        self.key_glow = (255, 220, 150)  # Bright cyan
        self.key_pressed = (100, 255, 255)  # Yellow highlight
        self.text_color = (255, 200, 100)
        self.fingertip_color = (0, 255, 255)  # Yellow for fingertips
        
        # Sound effects
        self.sounds = {}
        self._load_sounds()
        
        # Generate round keyboard layout with hieroglyphs
        self._generate_round_keyboard()
        
        # Callbacks
        self.on_key_press: Optional[Callable[[str], None]] = None
        self.on_text_submit: Optional[Callable[[str], None]] = None
        
        print("[SciFiKeyboard] Round keyboard with alien hieroglyphs initialized")
    
    def _load_sounds(self):
        """Load keyboard sound effects."""
        if not HAS_PYGAME:
            return
        
        try:
            # Find sound files
            sound_dir = os.path.join(os.path.dirname(__file__), 'monica_ai', 'resources', 'sounds', 'scifi')
            
            # Load keyboard hologram sound (ambient)
            keyboard_sound_path = os.path.join(sound_dir, 'keyboardhologram_sound.mp3')
            if os.path.exists(keyboard_sound_path):
                self.sounds['ambient'] = pygame.mixer.Sound(keyboard_sound_path)
                self.sounds['ambient'].set_volume(0.3)
                print("[SciFiKeyboard] Loaded ambient keyboard sound")
            
            # Generate click sound
            self._generate_click_sound()
            
        except Exception as e:
            print(f"[SciFiKeyboard] Sound loading error: {e}")
    
    def _generate_click_sound(self):
        """Generate sci-fi key click sound."""
        if not HAS_PYGAME:
            return
        
        try:
            sample_rate = 22050
            duration = 0.08
            t = np.linspace(0, duration, int(sample_rate * duration), False)
            
            # High-pitched click with quick decay
            freq = 1400 + 200 * np.sin(2 * np.pi * 10 * t)
            click = np.sin(2 * np.pi * freq * t) * np.exp(-t * 40)
            click = (click * 32767 * 0.4).astype(np.int16)
            
            stereo = np.column_stack([click, click])
            self.sounds['click'] = pygame.sndarray.make_sound(stereo)
            self.sounds['click'].set_volume(0.5)
        except Exception as e:
            print(f"[SciFiKeyboard] Click sound generation error: {e}")
    
    def _generate_round_keyboard(self):
        """Generate round keyboard layout with alien hieroglyphs."""
        self.keys = []
        
        # Character mapping (what gets typed)
        chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        
        # Arrange in 3 concentric circles
        circles = [
            {"radius": 150, "chars": "ABCDEFGHIJ", "size": 60},
            {"radius": 250, "chars": "KLMNOPQRSTUVWXYZ", "size": 55},
            {"radius": 350, "chars": "0123456789", "size": 50}
        ]
        
        key_index = 0
        for circle in circles:
            radius = circle["radius"]
            chars_in_circle = circle["chars"]
            key_size = circle["size"]
            num_keys = len(chars_in_circle)
            
            for i, char in enumerate(chars_in_circle):
                angle = (2 * math.pi * i / num_keys) - math.pi / 2  # Start at top
                
                # Generate unique hieroglyph for this key
                hieroglyph = generate_alien_hieroglyph(key_index)
                
                key = RoundKeyState(
                    label=char,
                    char=char,
                    angle=angle,
                    radius=radius,
                    size=key_size,
                    hieroglyph=hieroglyph,
                    glow_phase=random.uniform(0, 2 * math.pi)
                )
                self.keys.append(key)
                key_index += 1
        
        # Add special keys in center
        # Space bar
        self.keys.append(RoundKeyState(
            label="SPACE",
            char=" ",
            angle=0,
            radius=0,
            size=80,
            hieroglyph=generate_alien_hieroglyph(100),
            glow_phase=0
        ))
        
        # Backspace and Enter around space
        self.keys.append(RoundKeyState(
            label="⌫",
            char="BACKSPACE",
            angle=math.pi,
            radius=50,
            size=45,
            hieroglyph=generate_alien_hieroglyph(101)
        ))
        
        self.keys.append(RoundKeyState(
            label="↵",
            char="ENTER",
            angle=0,
            radius=50,
            size=45,
            hieroglyph=generate_alien_hieroglyph(102)
        ))
        
        print(f"[SciFiKeyboard] Generated {len(self.keys)} keys in round layout")
    
    def set_fingertip_positions(self, left_index: Optional[Tuple[int, int]], 
                                right_index: Optional[Tuple[int, int]]):
        """Update fingertip positions for highlighting."""
        self.left_index_pos = left_index
        self.right_index_pos = right_index
        
        # Check for key presses
        self._check_fingertip_key_press()
    
    def _check_fingertip_key_press(self):
        """Check if fingertips are pressing any keys."""
        current_time = time.time()
        
        for fingertip in [self.left_index_pos, self.right_index_pos]:
            if fingertip is None:
                continue
            
            fx, fy = fingertip
            
            for key in self.keys:
                # Calculate key position
                kx = int(self.center[0] + key.radius * math.cos(key.angle + self.rotation))
                ky = int(self.center[1] + key.radius * math.sin(key.angle + self.rotation))
                
                # Check distance
                dist = math.sqrt((fx - kx)**2 + (fy - ky)**2)
                
                if dist < key.size // 2 + self.fingertip_radius:
                    # Key press detected
                    if not key.pressed or current_time - key.press_time > 0.5:
                        key.pressed = True
                        key.press_time = current_time
                        self._handle_key_press(key.char)
                        self._play_click_sound()
    
    def _handle_key_press(self, char: str):
        """Handle a key press."""
        if char == "BACKSPACE":
            self.typed_text = self.typed_text[:-1]
        elif char == "ENTER":
            if self.on_text_submit and self.typed_text:
                self.on_text_submit(self.typed_text)
            self.typed_text = ""
        else:
            self.typed_text += char
        
        # Limit text length
        if len(self.typed_text) > self.max_text_length:
            self.typed_text = self.typed_text[-self.max_text_length:]
        
        if self.on_key_press:
            self.on_key_press(char)
    
    def _play_click_sound(self):
        """Play key click sound."""
        if HAS_PYGAME and 'click' in self.sounds:
            try:
                self.sounds['click'].play()
            except:
                pass
    
    def _play_ambient_sound(self):
        """Play ambient keyboard sound."""
        if HAS_PYGAME and 'ambient' in self.sounds:
            try:
                if not pygame.mixer.get_busy():
                    self.sounds['ambient'].play(-1)  # Loop
            except:
                pass
    
    def show(self):
        """Show the keyboard with materialization effect."""
        if not self.visible:
            self.is_materializing = True
            self.is_dematerializing = False
            self.materialize_progress = 0.0
            self._play_ambient_sound()
            print("[SciFiKeyboard] Keyboard materializing...")
    
    def hide(self):
        """Hide the keyboard with dematerialization effect."""
        if self.visible or self.is_materializing:
            self.is_dematerializing = True
            self.is_materializing = False
            print("[SciFiKeyboard] Keyboard dematerializing...")
    
    def _update(self, dt: float):
        """Update animation state."""
        self.glow_phase += dt * 2
        self.rotation += dt * 0.1  # Slow rotation
        
        # Materialization
        if self.is_materializing:
            self.materialize_progress += dt / 2.0  # 2 seconds to materialize
            if self.materialize_progress >= 1.0:
                self.materialize_progress = 1.0
                self.is_materializing = False
                self.visible = True
        
        # Dematerialization
        if self.is_dematerializing:
            self.materialize_progress -= dt / 1.0
            if self.materialize_progress <= 0.0:
                self.materialize_progress = 0.0
                self.is_dematerializing = False
                self.visible = False
        
        # Update key press states
        current_time = time.time()
        for key in self.keys:
            if key.pressed and current_time - key.press_time > 0.15:
                key.pressed = False
            key.glow_phase += dt * 2
    
    def _render(self) -> np.ndarray:
        """Render the keyboard frame."""
        # Green screen background
        frame = np.full((self.height, self.width, 3), GREEN_SCREEN, dtype=np.uint8)
        
        if self.materialize_progress <= 0:
            return frame
        
        alpha = self.materialize_progress
        
        # Draw energy field (outer glow)
        for i in range(5, 0, -1):
            glow_radius = int(400 * alpha) + i * 20
            glow_intensity = 0.15 * (6 - i) / 5 * alpha
            glow_color = tuple(int(c * glow_intensity) for c in self.key_glow)
            cv2.circle(frame, self.center, glow_radius, glow_color, 3, cv2.LINE_AA)
        
        # Draw keys
        for key in self.keys:
            self._render_key(frame, key, alpha)
        
        # Draw fingertip highlights
        self._render_fingertips(frame, alpha)
        
        # Draw text display
        self._render_text_display(frame, alpha)
        
        # Scan line effect during materialization
        if self.is_materializing or self.is_dematerializing:
            scan_angle = self.materialize_progress * 2 * math.pi
            scan_len = 450
            scan_x = int(self.center[0] + scan_len * math.cos(scan_angle))
            scan_y = int(self.center[1] + scan_len * math.sin(scan_angle))
            cv2.line(frame, self.center, (scan_x, scan_y), (255, 255, 255), 2, cv2.LINE_AA)
        
        return frame
    
    def _render_key(self, frame: np.ndarray, key: RoundKeyState, alpha: float):
        """Render a single key with hieroglyph."""
        # Calculate key position
        kx = int(self.center[0] + key.radius * math.cos(key.angle + self.rotation))
        ky = int(self.center[1] + key.radius * math.sin(key.angle + self.rotation))
        
        # Glow effect
        glow_intensity = 0.5 + 0.3 * math.sin(key.glow_phase)
        
        if key.pressed:
            # Pressed state - bright yellow
            color = tuple(int(c * alpha) for c in self.key_pressed)
            glow_color = (255, 255, 255)
            glow_layers = 6
        else:
            # Normal state - cyan glow
            color = tuple(int(c * alpha * glow_intensity) for c in self.key_color)
            glow_color = tuple(int(c * alpha * glow_intensity) for c in self.key_glow)
            glow_layers = 4
        
        # Multi-layer glow
        for i in range(glow_layers, 0, -1):
            glow_radius = key.size // 2 + i * 8
            glow_alpha = 0.2 * (glow_layers - i + 1) / glow_layers * alpha
            g_color = tuple(int(c * glow_alpha) for c in glow_color)
            cv2.circle(frame, (kx, ky), glow_radius, g_color, 2, cv2.LINE_AA)
        
        # Key circle
        cv2.circle(frame, (kx, ky), key.size // 2, color, 2, cv2.LINE_AA)
        
        # Inner circle
        inner_radius = key.size // 2 - 8
        if inner_radius > 0:
            cv2.circle(frame, (kx, ky), inner_radius, 
                      tuple(int(c * alpha * 0.5) for c in color), 1, cv2.LINE_AA)
        
        # Render hieroglyph
        h_size = min(key.size - 20, 40)
        if h_size > 10:
            hieroglyph = cv2.resize(key.hieroglyph, (h_size, h_size))
            # Apply alpha
            hieroglyph = (hieroglyph * alpha).astype(np.uint8)
            
            # Place hieroglyph
            h_x = kx - h_size // 2
            h_y = ky - h_size // 2
            
            if 0 <= h_x < self.width - h_size and 0 <= h_y < self.height - h_size:
                # Blend hieroglyph
                roi = frame[h_y:h_y+h_size, h_x:h_x+h_size]
                mask = (hieroglyph.sum(axis=2) > 0).astype(np.uint8) * 255
                frame[h_y:h_y+h_size, h_x:h_x+h_size] = cv2.addWeighted(
                    roi, 0.3, hieroglyph, 0.7, 0
                )
    
    def _render_fingertips(self, frame: np.ndarray, alpha: float):
        """Render fingertip highlights."""
        for fingertip in [self.left_index_pos, self.right_index_pos]:
            if fingertip is None:
                continue
            
            fx, fy = fingertip
            
            # Pulsating glow
            pulse = 1.0 + 0.3 * math.sin(self.glow_phase * 3)
            radius = int(self.fingertip_radius * pulse)
            
            # Multi-layer glow
            for i in range(5, 0, -1):
                glow_r = radius + i * 10
                glow_alpha = 0.25 * (6 - i) / 5 * alpha
                g_color = tuple(int(c * glow_alpha) for c in self.fingertip_color)
                cv2.circle(frame, (fx, fy), glow_r, g_color, 2, cv2.LINE_AA)
            
            # Center dot
            cv2.circle(frame, (fx, fy), 8, 
                      tuple(int(c * alpha) for c in self.fingertip_color), -1, cv2.LINE_AA)
            cv2.circle(frame, (fx, fy), 8, (255, 255, 255), 2, cv2.LINE_AA)
    
    def _render_text_display(self, frame: np.ndarray, alpha: float):
        """Render the text input display at top."""
        display_height = 60
        display_y = 30
        display_width = self.width - 100
        display_x = 50
        
        # Background with glow
        for i in range(3, 0, -1):
            glow_alpha = 0.15 * (4 - i) / 3 * alpha
            g_color = tuple(int(c * glow_alpha) for c in self.key_glow)
            cv2.rectangle(frame, 
                         (display_x - i*5, display_y - i*5),
                         (display_x + display_width + i*5, display_y + display_height + i*5),
                         g_color, 2, cv2.LINE_AA)
        
        # Main background
        cv2.rectangle(frame, (display_x, display_y), 
                     (display_x + display_width, display_y + display_height),
                     tuple(int(c * alpha * 0.3) for c in self.key_color), -1, cv2.LINE_AA)
        cv2.rectangle(frame, (display_x, display_y),
                     (display_x + display_width, display_y + display_height),
                     tuple(int(c * alpha) for c in self.key_glow), 2, cv2.LINE_AA)
        
        # Text
        if self.typed_text:
            font = cv2.FONT_HERSHEY_SIMPLEX
            text_color = tuple(int(c * alpha) for c in self.text_color)
            cv2.putText(frame, self.typed_text, (display_x + 20, display_y + 40),
                       font, 0.9, text_color, 2, cv2.LINE_AA)
        
        # Blinking cursor
        cursor_x = display_x + 20 + len(self.typed_text) * 18
        if int(time.time() * 2) % 2 == 0:
            cv2.line(frame, (cursor_x, display_y + 15), (cursor_x, display_y + 45),
                    tuple(int(c * alpha) for c in self.text_color), 3, cv2.LINE_AA)
    
    def _run_loop(self):
        """Main render loop."""
        cv2.namedWindow("Monica Sci-Fi Keyboard", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Monica Sci-Fi Keyboard", self.width, self.height)
        
        last_time = time.time()
        
        while self.running:
            current_time = time.time()
            dt = current_time - last_time
            last_time = current_time
            
            self._update(dt)
            frame = self._render()
            
            cv2.imshow("Monica Sci-Fi Keyboard", frame)
            
            key = cv2.waitKey(16) & 0xFF  # ~60 FPS
            if key == ord('q'):
                break
            elif key == ord('s'):
                self.show()
            elif key == ord('h'):
                self.hide()
        
        cv2.destroyWindow("Monica Sci-Fi Keyboard")
    
    def start(self):
        """Start the keyboard window in a separate thread."""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._run_loop, daemon=True)
            self.thread.start()
            print("[SciFiKeyboard] Window started")
    
    def stop(self):
        """Stop the keyboard window."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
        print("[SciFiKeyboard] Window stopped")


# Singleton instance
_scifi_keyboard: Optional[MonicaSciFiKeyboard] = None


def get_scifi_keyboard() -> MonicaSciFiKeyboard:
    """Get singleton sci-fi keyboard instance."""
    global _scifi_keyboard
    if _scifi_keyboard is None:
        _scifi_keyboard = MonicaSciFiKeyboard()
    return _scifi_keyboard


# Test mode
if __name__ == "__main__":
    print("Monica Sci-Fi Keyboard - Round Layout with Alien Hieroglyphs")
    print("Press 's' to show, 'h' to hide, 'q' to quit")
    
    keyboard = MonicaSciFiKeyboard(900, 900)
    keyboard.running = True
    keyboard._run_loop()
