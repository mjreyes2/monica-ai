"""
Monica Holographic Keyboard Window - Separate Window with Green Screen for OBS Overlay
Displays the holographic keyboard in its own window for chroma key compositing.
"""
import cv2
import numpy as np
import math
import time
import threading
from typing import Tuple, Optional, Dict, List, Callable
from dataclasses import dataclass

# Green screen color (pure green for chroma key)
GREEN_SCREEN = (0, 255, 0)  # BGR


@dataclass
class KeyState:
    """State of a keyboard key."""
    label: str
    x: int
    y: int
    width: int
    height: int
    pressed: bool = False
    press_time: float = 0.0


class MonicaKeyboardWindow:
    """
    Separate window displaying the holographic keyboard on green screen.
    Perfect for OBS chroma key overlay.
    """
    
    def __init__(self, width: int = 800, height: int = 300):
        self.width = width
        self.height = height
        
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
        
        # Keyboard layout
        self.keys: List[KeyState] = []
        self.typed_text = ""
        self.max_text_length = 50
        
        # Callbacks
        self.on_key_press: Optional[Callable[[str], None]] = None
        self.on_text_submit: Optional[Callable[[str], None]] = None
        
        # Colors (holographic cyan theme)
        self.key_color = (200, 150, 50)  # Cyan
        self.key_glow = (255, 200, 100)  # Bright cyan
        self.key_pressed = (255, 255, 200)  # White-cyan
        self.text_color = (255, 200, 100)
        
        # Generate keyboard layout
        self._generate_keyboard_layout()
        
        print("[KeyboardWindow] Keyboard window initialized (green screen mode)")
    
    def _generate_keyboard_layout(self):
        """Generate the keyboard key positions."""
        self.keys = []
        
        # Key dimensions
        key_w = 50
        key_h = 45
        gap = 5
        
        # Keyboard rows
        rows = [
            "1234567890",
            "QWERTYUIOP",
            "ASDFGHJKL",
            "ZXCVBNM"
        ]
        
        start_y = 60
        
        for row_idx, row in enumerate(rows):
            # Calculate row offset for staggered layout
            row_offset = row_idx * 15
            start_x = (self.width - (len(row) * (key_w + gap))) // 2 + row_offset
            
            for i, char in enumerate(row):
                key = KeyState(
                    label=char,
                    x=start_x + i * (key_w + gap),
                    y=start_y + row_idx * (key_h + gap),
                    width=key_w,
                    height=key_h
                )
                self.keys.append(key)
        
        # Add special keys
        last_row_y = start_y + 3 * (key_h + gap)
        
        # Space bar
        space_width = 250
        space_x = (self.width - space_width) // 2
        self.keys.append(KeyState(
            label="SPACE",
            x=space_x,
            y=last_row_y + key_h + gap,
            width=space_width,
            height=key_h
        ))
        
        # Backspace
        self.keys.append(KeyState(
            label="⌫",
            x=self.width - 80,
            y=start_y,
            width=60,
            height=key_h
        ))
        
        # Enter
        self.keys.append(KeyState(
            label="↵",
            x=self.width - 80,
            y=start_y + key_h + gap,
            width=60,
            height=key_h * 2 + gap
        ))
    
    def show(self):
        """Show the keyboard with materialization effect."""
        if not self.visible:
            self.is_materializing = True
            self.is_dematerializing = False
            self.materialize_progress = 0.0
            print("[KeyboardWindow] Keyboard materializing...")
    
    def hide(self):
        """Hide the keyboard with dematerialization effect."""
        if self.visible or self.is_materializing:
            self.is_dematerializing = True
            self.is_materializing = False
            print("[KeyboardWindow] Keyboard dematerializing...")
    
    def press_key(self, label: str):
        """Simulate pressing a key."""
        for key in self.keys:
            if key.label == label or (label == " " and key.label == "SPACE"):
                key.pressed = True
                key.press_time = time.time()
                self._handle_key_press(key.label)
                break
    
    def _handle_key_press(self, label: str):
        """Handle a key press."""
        if label == "SPACE":
            self.typed_text += " "
        elif label == "⌫":
            self.typed_text = self.typed_text[:-1]
        elif label == "↵":
            if self.on_text_submit and self.typed_text:
                self.on_text_submit(self.typed_text)
            self.typed_text = ""
        else:
            self.typed_text += label
        
        # Limit text length
        if len(self.typed_text) > self.max_text_length:
            self.typed_text = self.typed_text[-self.max_text_length:]
        
        if self.on_key_press:
            self.on_key_press(label)
    
    def set_text(self, text: str):
        """Set the typed text directly."""
        self.typed_text = text[-self.max_text_length:] if len(text) > self.max_text_length else text
    
    def clear_text(self):
        """Clear the typed text."""
        self.typed_text = ""
    
    def _update(self, dt: float):
        """Update animation state."""
        self.glow_phase += dt * 2
        
        # Materialization
        if self.is_materializing:
            self.materialize_progress += dt / 1.5  # 1.5 seconds to materialize
            if self.materialize_progress >= 1.0:
                self.materialize_progress = 1.0
                self.is_materializing = False
                self.visible = True
        
        # Dematerialization
        if self.is_dematerializing:
            self.materialize_progress -= dt / 1.0  # 1 second to dematerialize
            if self.materialize_progress <= 0.0:
                self.materialize_progress = 0.0
                self.is_dematerializing = False
                self.visible = False
        
        # Update key press states
        current_time = time.time()
        for key in self.keys:
            if key.pressed and current_time - key.press_time > 0.15:
                key.pressed = False
    
    def _render(self) -> np.ndarray:
        """Render the keyboard frame."""
        # Green screen background
        frame = np.full((self.height, self.width, 3), GREEN_SCREEN, dtype=np.uint8)
        
        if self.materialize_progress <= 0:
            return frame
        
        alpha = self.materialize_progress
        
        # Render each key
        for key in self.keys:
            self._render_key(frame, key, alpha)
        
        # Render typed text
        self._render_text_display(frame, alpha)
        
        # Add scan line effect during materialization
        if self.is_materializing or self.is_dematerializing:
            scan_x = int(self.width * self.materialize_progress)
            cv2.line(frame, (scan_x, 0), (scan_x, self.height), (255, 255, 255), 2, cv2.LINE_AA)
        
        return frame
    
    def _render_key(self, frame: np.ndarray, key: KeyState, alpha: float):
        """Render a single key."""
        # Glow effect
        glow_intensity = 0.3 + 0.2 * math.sin(self.glow_phase + key.x * 0.01)
        
        if key.pressed:
            # Pressed state - bright
            color = tuple(int(c * alpha) for c in self.key_pressed)
            border_color = (255, 255, 255)
            thickness = 2
        else:
            # Normal state
            color = tuple(int(c * alpha * glow_intensity) for c in self.key_color)
            border_color = tuple(int(c * alpha) for c in self.key_glow)
            thickness = 1
        
        # Key background (semi-transparent effect)
        overlay = frame.copy()
        cv2.rectangle(overlay, (key.x, key.y), (key.x + key.width, key.y + key.height),
                     color, -1, cv2.LINE_AA)
        
        # Blend with green screen
        mask = np.zeros((self.height, self.width), dtype=np.uint8)
        cv2.rectangle(mask, (key.x, key.y), (key.x + key.width, key.y + key.height), 255, -1)
        frame[mask > 0] = cv2.addWeighted(frame, 0.5, overlay, 0.5, 0)[mask > 0]
        
        # Key border
        cv2.rectangle(frame, (key.x, key.y), (key.x + key.width, key.y + key.height),
                     border_color, thickness, cv2.LINE_AA)
        
        # Key label
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.5 if len(key.label) > 1 else 0.7
        text_size = cv2.getTextSize(key.label, font, font_scale, 1)[0]
        text_x = key.x + (key.width - text_size[0]) // 2
        text_y = key.y + (key.height + text_size[1]) // 2
        
        text_color = tuple(int(c * alpha) for c in self.text_color)
        cv2.putText(frame, key.label, (text_x, text_y), font, font_scale, text_color, 1, cv2.LINE_AA)
    
    def _render_text_display(self, frame: np.ndarray, alpha: float):
        """Render the text input display."""
        # Text display area at top
        display_height = 40
        display_y = 10
        
        # Background
        cv2.rectangle(frame, (20, display_y), (self.width - 20, display_y + display_height),
                     tuple(int(c * alpha * 0.3) for c in self.key_color), -1, cv2.LINE_AA)
        cv2.rectangle(frame, (20, display_y), (self.width - 20, display_y + display_height),
                     tuple(int(c * alpha) for c in self.key_glow), 1, cv2.LINE_AA)
        
        # Text
        if self.typed_text:
            font = cv2.FONT_HERSHEY_SIMPLEX
            text_color = tuple(int(c * alpha) for c in self.text_color)
            cv2.putText(frame, self.typed_text, (30, display_y + 28), font, 0.7, text_color, 1, cv2.LINE_AA)
        
        # Cursor
        cursor_x = 30 + len(self.typed_text) * 12
        if int(time.time() * 2) % 2 == 0:  # Blinking cursor
            cv2.line(frame, (cursor_x, display_y + 8), (cursor_x, display_y + 32),
                    tuple(int(c * alpha) for c in self.text_color), 2, cv2.LINE_AA)
    
    def _run_loop(self):
        """Main render loop."""
        cv2.namedWindow("Monica Keyboard", cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO)
        cv2.resizeWindow("Monica Keyboard", self.width, self.height)
        
        # Bring window to front using Windows API
        try:
            import ctypes
            hwnd = ctypes.windll.user32.FindWindowW(None, "Monica Keyboard")
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
            
            cv2.imshow("Monica Keyboard", frame)
            
            key = cv2.waitKey(16) & 0xFF  # ~60 FPS
            if key == ord('q'):
                break
            elif key == ord('s'):  # Show
                self.show()
            elif key == ord('h'):  # Hide
                self.hide()
            elif key == 27:  # ESC - clear text
                self.clear_text()
            elif 32 <= key <= 126:  # Printable ASCII
                char = chr(key).upper()
                self.press_key(char if char != ' ' else 'SPACE')
            elif key == 8:  # Backspace
                self.press_key("⌫")
            elif key == 13:  # Enter
                self.press_key("↵")
        
        cv2.destroyWindow("Monica Keyboard")
    
    def start(self):
        """Start the keyboard window in a separate thread."""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._run_loop, daemon=True)
            self.thread.start()
            print("[KeyboardWindow] Window started (Press 's' to show, 'h' to hide, 'q' to quit)")
    
    def stop(self):
        """Stop the keyboard window."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
        print("[KeyboardWindow] Window stopped")


# Singleton instance
_keyboard_window: Optional[MonicaKeyboardWindow] = None


def get_keyboard_window() -> MonicaKeyboardWindow:
    """Get singleton keyboard window instance."""
    global _keyboard_window
    if _keyboard_window is None:
        _keyboard_window = MonicaKeyboardWindow()
    return _keyboard_window


# Test mode
if __name__ == "__main__":
    print("Monica Keyboard Window - Green Screen Mode")
    print("Press 's' to show, 'h' to hide, type to test, 'q' to quit")
    
    keyboard = MonicaKeyboardWindow(800, 300)
    keyboard.running = True
    keyboard._run_loop()
