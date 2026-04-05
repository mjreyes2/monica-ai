"""
Monica AI - Holographic Keyboard Window

Provides a standalone holographic keyboard that can be rendered as an overlay
on the camera feed or as a separate green-screen window for OBS.

Features:
- Sci-fi click sounds on every key press
- Fingertip detection for typing (index finger tip = sensor)
- Bright glowing fingertip indicators
- Full QWERTY layout with special keys
- Green-screen mode for OBS compositing

Usage:
    from services.monica_keyboard_window import get_keyboard_window
    kb = get_keyboard_window()
    kb.show()
"""

import logging
import math
import time
import threading
import numpy as np
from typing import Optional, Dict, Any, Tuple, List
from dataclasses import dataclass

logger = logging.getLogger("Monica.Keyboard")

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

try:
    import pygame
    HAS_PYGAME = True
except ImportError:
    HAS_PYGAME = False


@dataclass
class KeyPress:
    """Represents a detected key press."""
    key: str
    timestamp: float
    finger_x: int
    finger_y: int


class MonicaKeyboardWindow:
    """
    Holographic keyboard with sci-fi aesthetics, click sounds,
    and fingertip-based typing via hand detection.
    """

    ROWS = [
        ['ESC', '1', '2', '3', '4', '5', '6', '7', '8', '9', '0', 'DEL'],
        ['TAB', 'Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P'],
        ['CAPS', 'A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L', 'ENTER'],
        ['SHIFT', 'Z', 'X', 'C', 'V', 'B', 'N', 'M', ',', '.', '?'],
        ['CTRL', 'ALT', '________SPACE________', 'ALT', 'FN'],
    ]

    def __init__(self, width: int = 800, height: int = 300):
        self.width = width
        self.height = height
        self.visible = False
        self.offset_x = 0
        self.offset_y = 0
        self.scale = 1.0

        # Key press tracking
        self.active_key: Optional[str] = None
        self.active_key_time: float = 0
        self.last_press_time: float = 0
        self.cooldown: float = 0.25  # seconds between presses
        self.typed_text: str = ""
        self.press_history: List[KeyPress] = []

        # Fingertip state
        self.fingertip_positions: List[Tuple[int, int]] = []
        self.fingertip_brightness: float = 1.0

        # Sounds
        self._click_sound = None
        self._special_click_sound = None
        self._sounds_loaded = False
        self._load_click_sounds()

        # Key bounds cache (populated during render)
        self._key_bounds: Dict[str, Tuple[int, int, int, int]] = {}

        logger.info("Keyboard Window created")

    def _load_click_sounds(self):
        """Generate sci-fi click sounds for key presses."""
        if not HAS_PYGAME:
            return

        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=256)

            sr = 44100

            # Normal key click - short crisp sci-fi beep
            duration = 0.06
            samples = int(sr * duration)
            t = np.linspace(0, duration, samples)
            freq = 2200 - 1800 * (t / duration)  # Descending chirp
            wave = np.sin(2 * np.pi * freq * t) * 0.4
            wave += np.sin(2 * np.pi * freq * 1.5 * t) * 0.15  # Harmonic
            envelope = np.exp(-t * 40)  # Fast decay
            wave *= envelope
            wave_16 = (wave * 32767).astype(np.int16)
            stereo = np.column_stack([wave_16, wave_16])
            self._click_sound = pygame.sndarray.make_sound(stereo)
            self._click_sound.set_volume(0.5)

            # Special key click - deeper, longer
            duration = 0.1
            samples = int(sr * duration)
            t = np.linspace(0, duration, samples)
            freq = 1400 - 800 * (t / duration)
            wave = np.sin(2 * np.pi * freq * t) * 0.35
            wave += np.sin(2 * np.pi * 600 * t) * 0.2  # Bass layer
            envelope = np.exp(-t * 25)
            wave *= envelope
            wave_16 = (wave * 32767).astype(np.int16)
            stereo = np.column_stack([wave_16, wave_16])
            self._special_click_sound = pygame.sndarray.make_sound(stereo)
            self._special_click_sound.set_volume(0.5)

            self._sounds_loaded = True
            logger.info("Keyboard click sounds generated")

        except Exception as e:
            logger.debug(f"Could not generate click sounds: {e}")

    def _play_click(self, special: bool = False):
        """Play sci-fi click sound."""
        if not self._sounds_loaded:
            return
        try:
            snd = self._special_click_sound if special else self._click_sound
            if snd:
                snd.play()
        except Exception:
            pass

    def show(self):
        """Show the keyboard."""
        self.visible = True
        logger.info("Keyboard shown")

    def hide(self):
        """Hide the keyboard."""
        self.visible = False
        logger.info("Keyboard hidden")

    def toggle(self) -> bool:
        """Toggle visibility. Returns new state."""
        self.visible = not self.visible
        return self.visible

    def set_fingertip_positions(self, positions: List[Tuple[int, int]]):
        """Update fingertip positions from hand detector."""
        self.fingertip_positions = positions

    def check_fingertip_press(self, fx: int, fy: int) -> Optional[str]:
        """Check if a fingertip position hits a key."""
        now = time.time()
        if now - self.last_press_time < self.cooldown:
            return None

        for key, (kx, ky, kw, kh) in self._key_bounds.items():
            if kx <= fx <= kx + kw and ky <= fy <= ky + kh:
                self.last_press_time = now
                self.active_key = key
                self.active_key_time = now

                # Determine the actual character
                actual_key = key
                if key.startswith('________'):
                    actual_key = ' '
                elif key == 'DEL':
                    if self.typed_text:
                        self.typed_text = self.typed_text[:-1]
                    actual_key = 'DEL'
                elif key in ('SHIFT', 'CAPS', 'CTRL', 'ALT', 'FN', 'TAB', 'ESC'):
                    actual_key = key
                elif key == 'ENTER':
                    actual_key = '\n'
                else:
                    self.typed_text += key.lower()
                    actual_key = key.lower()

                if actual_key == ' ':
                    self.typed_text += ' '

                # Play sound
                is_special = key in ('ENTER', 'DEL', 'SHIFT', 'CAPS', 'CTRL', 'TAB', 'ESC', 'ALT', 'FN') or key.startswith('_')
                self._play_click(special=is_special)

                self.press_history.append(KeyPress(actual_key, now, fx, fy))
                if len(self.press_history) > 100:
                    self.press_history = self.press_history[-100:]

                return actual_key

        return None

    def render(self, frame: np.ndarray) -> np.ndarray:
        """Render the holographic keyboard onto a frame."""
        if not self.visible or not HAS_CV2:
            return frame

        h, w = frame.shape[:2]
        scale = self.scale
        key_w = int(42 * scale)
        key_h = int(36 * scale)
        margin = int(3 * scale)

        # Calculate keyboard position (bottom center)
        total_cols = 12
        kb_width = total_cols * (key_w + margin)
        kb_x = (w - kb_width) // 2 + self.offset_x
        kb_y = h - int(230 * scale) + self.offset_y

        # Highlight fade
        highlight_fade = 0.0
        if self.active_key and time.time() - self.active_key_time < 0.25:
            highlight_fade = 1.0 - (time.time() - self.active_key_time) / 0.25
        elif self.active_key:
            self.active_key = None

        # Pulse animation for ambient glow
        pulse = 0.7 + 0.3 * math.sin(time.time() * 2.0)

        self._key_bounds.clear()

        for row_idx, row in enumerate(self.ROWS):
            row_offset = row_idx * int(10 * scale)  # Stagger
            for col_idx, key in enumerate(row):
                kx = kb_x + row_offset + col_idx * (key_w + margin)
                ky = kb_y + row_idx * (key_h + margin)

                # Width adjustment for special keys
                kw = key_w
                if key.startswith('________'):
                    kw = key_w * 5
                    kx = kb_x + int(130 * scale)
                elif key in ('SHIFT', 'ENTER', 'CAPS'):
                    kw = int(key_w * 1.4)
                elif key in ('TAB', 'DEL', 'CTRL', 'ALT', 'FN', 'ESC'):
                    kw = int(key_w * 1.2)

                self._key_bounds[key] = (kx, ky, kw, key_h)

                # Colors
                is_active = (self.active_key == key and highlight_fade > 0)
                if is_active:
                    intensity = int(255 * highlight_fade)
                    border_color = (0, 255, int(100 * highlight_fade))
                    fill_alpha = 0.3 * highlight_fade
                    # Draw glow behind key
                    overlay = frame.copy()
                    cv2.rectangle(overlay, (kx - 2, ky - 2), (kx + kw + 2, ky + key_h + 2),
                                  (0, intensity, 0), -1)
                    frame = cv2.addWeighted(overlay, fill_alpha, frame, 1 - fill_alpha, 0)
                else:
                    p = int(180 * pulse)
                    border_color = (p // 2, p, p)

                # Key border (no fill - transparent holographic)
                cv2.rectangle(frame, (kx, ky), (kx + kw, ky + key_h), border_color, 1)

                # Key label
                label = key if not key.startswith('________') else 'SPACE'
                fs = 0.32 * scale
                if len(label) > 3:
                    fs *= 0.85
                text_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, fs, 1)[0]
                tx = kx + (kw - text_size[0]) // 2
                ty = ky + (key_h + text_size[1]) // 2
                text_color = (0, 255, 0) if is_active else (int(150 * pulse), int(230 * pulse), int(230 * pulse))
                cv2.putText(frame, label, (tx, ty), cv2.FONT_HERSHEY_SIMPLEX, fs, text_color, 1)

        # Draw typed text preview above keyboard
        if self.typed_text:
            preview = self.typed_text[-40:]  # Last 40 chars
            preview_y = kb_y - 15
            cv2.putText(frame, f"> {preview}", (kb_x, preview_y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5 * scale, (0, 255, 255), 1)

        # Draw bright fingertip sensors
        frame = self._draw_fingertip_sensors(frame)

        return frame

    def _draw_fingertip_sensors(self, frame: np.ndarray) -> np.ndarray:
        """Draw bright glowing circles at fingertip positions (sensor indicators)."""
        if not self.fingertip_positions:
            return frame

        pulse = 0.6 + 0.4 * math.sin(time.time() * 6.0)

        for fx, fy in self.fingertip_positions:
            # Outer glow (larger, dimmer)
            r_outer = int(12 * pulse)
            cv2.circle(frame, (fx, fy), r_outer, (0, int(100 * pulse), int(200 * pulse)), 2, cv2.LINE_AA)

            # Middle ring
            cv2.circle(frame, (fx, fy), 7, (0, 200, 255), 2, cv2.LINE_AA)

            # Inner bright core
            cv2.circle(frame, (fx, fy), 3, (180, 255, 255), -1, cv2.LINE_AA)

            # Cross-hair
            cv2.line(frame, (fx - 10, fy), (fx - 5, fy), (0, 255, 255), 1)
            cv2.line(frame, (fx + 5, fy), (fx + 10, fy), (0, 255, 255), 1)
            cv2.line(frame, (fx, fy - 10), (fx, fy - 5), (0, 255, 255), 1)
            cv2.line(frame, (fx, fy + 5), (fx, fy + 10), (0, 255, 255), 1)

        return frame

    def render_greenscreen(self) -> Optional[np.ndarray]:
        """Render keyboard on a green-screen background for OBS."""
        if not HAS_CV2:
            return None
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        frame[:] = (0, 255, 0)  # Green screen
        return self.render(frame)

    def get_typed_text(self) -> str:
        """Get the currently typed text buffer."""
        return self.typed_text

    def clear_typed_text(self):
        """Clear the typed text buffer."""
        self.typed_text = ""

    def get_status(self) -> Dict[str, Any]:
        """Get keyboard status."""
        return {
            "visible": self.visible,
            "typed_text": self.typed_text,
            "total_presses": len(self.press_history),
            "sounds_loaded": self._sounds_loaded,
        }


# Singleton
_keyboard_window: Optional[MonicaKeyboardWindow] = None


def get_keyboard_window() -> MonicaKeyboardWindow:
    global _keyboard_window
    if _keyboard_window is None:
        _keyboard_window = MonicaKeyboardWindow()
    return _keyboard_window
