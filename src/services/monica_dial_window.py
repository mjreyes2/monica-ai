"""
Monica AI - Holographic Dial Window

Provides a sci-fi rotary dial control overlay for the hologram system.
Used for adjusting parameters like volume, zoom, brightness, globe rotation, etc.

Features:
- Holographic rotating dial with tick marks
- Touch/drag control via hand detection
- Green-screen mode for OBS compositing
- Multiple dial modes (volume, zoom, rotation, etc.)

Usage:
    from services.monica_dial_window import get_dial_window
    dial = get_dial_window()
    dial.show()
"""

import logging
import math
import time
import numpy as np
from typing import Optional, Dict, Any, Tuple, List
from dataclasses import dataclass

logger = logging.getLogger("Monica.Dial")

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False


@dataclass
class DialMode:
    """Configuration for a dial mode."""
    name: str
    min_val: float
    max_val: float
    current: float
    unit: str = ""
    color: Tuple[int, int, int] = (0, 255, 255)


class MonicaDialWindow:
    """
    Holographic rotary dial control overlay.
    """

    def __init__(self, width: int = 300, height: int = 300):
        self.width = width
        self.height = height
        self.visible = False

        # Dial modes
        self.modes: Dict[str, DialMode] = {
            "volume": DialMode("VOLUME", 0, 100, 70, "%", (0, 255, 255)),
            "zoom": DialMode("ZOOM", 1, 20, 1, "x", (0, 200, 255)),
            "brightness": DialMode("BRIGHTNESS", 0, 100, 50, "%", (255, 200, 0)),
            "rotation": DialMode("ROTATION", 0, 360, 0, "deg", (0, 255, 100)),
            "speed": DialMode("SPEED", 0.1, 5.0, 1.0, "x", (200, 100, 255)),
        }
        self.current_mode: str = "volume"

        # Interaction state
        self.is_dragging = False
        self.last_angle = 0.0

        logger.info("Dial Window created")

    def show(self):
        self.visible = True

    def hide(self):
        self.visible = False

    def toggle(self) -> bool:
        self.visible = not self.visible
        return self.visible

    def set_mode(self, mode: str):
        if mode in self.modes:
            self.current_mode = mode

    def set_value(self, value: float):
        mode = self.modes[self.current_mode]
        mode.current = max(mode.min_val, min(mode.max_val, value))

    def get_value(self) -> float:
        return self.modes[self.current_mode].current

    def adjust_from_angle(self, angle_deg: float):
        """Adjust the current dial value based on rotation angle (0-360)."""
        mode = self.modes[self.current_mode]
        fraction = (angle_deg % 360) / 360.0
        mode.current = mode.min_val + fraction * (mode.max_val - mode.min_val)

    def render(self, frame: np.ndarray) -> np.ndarray:
        """Render the holographic dial onto a frame."""
        if not self.visible or not HAS_CV2:
            return frame

        h, w = frame.shape[:2]
        mode = self.modes[self.current_mode]

        cx = w - 160
        cy = h // 2
        radius = 80
        color = mode.color

        pulse = 0.7 + 0.3 * math.sin(time.time() * 2.5)

        # Outer ring
        cv2.circle(frame, (cx, cy), radius, tuple(int(c * pulse) for c in color), 2, cv2.LINE_AA)
        cv2.circle(frame, (cx, cy), radius + 5, tuple(int(c * 0.3 * pulse) for c in color), 1, cv2.LINE_AA)

        # Tick marks
        num_ticks = 24
        for i in range(num_ticks):
            angle = math.radians(i * 360 / num_ticks - 90)
            x1 = int(cx + (radius - 8) * math.cos(angle))
            y1 = int(cy + (radius - 8) * math.sin(angle))
            x2 = int(cx + radius * math.cos(angle))
            y2 = int(cy + radius * math.sin(angle))
            tick_color = tuple(int(c * 0.5) for c in color)
            cv2.line(frame, (x1, y1), (x2, y2), tick_color, 1, cv2.LINE_AA)

        # Value indicator (bright line)
        fraction = (mode.current - mode.min_val) / max(mode.max_val - mode.min_val, 0.001)
        val_angle = math.radians(fraction * 270 - 135)  # -135 to +135 degrees
        vx = int(cx + (radius - 15) * math.cos(val_angle))
        vy = int(cy + (radius - 15) * math.sin(val_angle))
        cv2.line(frame, (cx, cy), (vx, vy), (255, 255, 255), 2, cv2.LINE_AA)

        # Center dot
        cv2.circle(frame, (cx, cy), 5, color, -1, cv2.LINE_AA)

        # Arc showing value range
        start_angle = -135
        end_angle = start_angle + int(fraction * 270)
        cv2.ellipse(frame, (cx, cy), (radius - 20, radius - 20),
                     0, start_angle, end_angle, color, 3, cv2.LINE_AA)

        # Text labels
        cv2.putText(frame, mode.name, (cx - 30, cy - radius - 15),
                     cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1)
        value_str = f"{mode.current:.1f}{mode.unit}" if mode.current != int(mode.current) else f"{int(mode.current)}{mode.unit}"
        cv2.putText(frame, value_str, (cx - 20, cy + 25),
                     cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        # Mode selector dots at bottom
        modes_list = list(self.modes.keys())
        dot_y = cy + radius + 25
        for i, mname in enumerate(modes_list):
            dot_x = cx - 40 + i * 20
            is_current = mname == self.current_mode
            dot_color = self.modes[mname].color if is_current else (80, 80, 80)
            cv2.circle(frame, (dot_x, dot_y), 4 if is_current else 3, dot_color, -1)

        return frame

    def render_greenscreen(self) -> Optional[np.ndarray]:
        if not HAS_CV2:
            return None
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        frame[:] = (0, 255, 0)
        return self.render(frame)

    def get_status(self) -> Dict[str, Any]:
        mode = self.modes[self.current_mode]
        return {
            "visible": self.visible,
            "mode": self.current_mode,
            "value": mode.current,
            "modes_available": list(self.modes.keys()),
        }


_dial_window: Optional[MonicaDialWindow] = None


def get_dial_window() -> MonicaDialWindow:
    global _dial_window
    if _dial_window is None:
        _dial_window = MonicaDialWindow()
    return _dial_window
