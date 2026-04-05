"""
Monica Holographic Dial Window - Separate Window with Green Screen for OBS Overlay
Displays the holographic dial/control interface in its own window for chroma key compositing.
"""
import cv2
import numpy as np
import math
import time
import threading
from typing import Tuple, Optional, List, Callable

# Green screen color (pure green for chroma key)
GREEN_SCREEN = (0, 255, 0)  # BGR


class MonicaDialWindow:
    """
    Separate window displaying a holographic dial/control interface on green screen.
    Perfect for OBS chroma key overlay.
    """
    
    def __init__(self, width: int = 400, height: int = 400):
        self.width = width
        self.height = height
        self.center = (width // 2, height // 2)
        self.radius = min(width, height) // 3
        
        # State
        self.visible = False
        self.running = False
        self.thread: Optional[threading.Thread] = None
        
        # Animation
        self.last_update = time.time()
        self.materialize_progress = 0.0
        self.is_materializing = False
        self.is_dematerializing = False
        self.rotation = 0.0
        self.glow_phase = 0.0
        self.scan_angle = 0.0
        
        # Dial value (0.0 to 1.0)
        self.value = 0.5
        self.target_value = 0.5
        self.prev_value = 0.5
        
        # Rotation direction detection
        self.rotation_direction = 0  # -1=counterclockwise, 0=none, 1=clockwise
        self.value_history = []  # Track recent values
        self.max_history = 5
        
        # Dial segments
        self.num_segments = 12
        self.active_segment = 6
        
        # Colors (holographic cyan theme)
        self.dial_color = (255, 180, 80)  # Cyan
        self.dial_glow = (255, 220, 150)  # Bright cyan
        self.dial_active = (100, 255, 255)  # Yellow highlight
        self.text_color = (255, 200, 100)
        
        # Callbacks
        self.on_value_change: Optional[Callable[[float], None]] = None
        
        # Alarm state
        self.alarm_active = False
        self.alarm_sound = None
        self.alarm_channel = None
        
        # Load alarm sound
        self._load_alarm_sound()
        
        print("[DialWindow] Dial window initialized (green screen mode)")
    
    def _load_alarm_sound(self):
        """Load facility alarm sound."""
        try:
            import pygame
            import os
            sound_path = os.path.join(os.path.dirname(__file__), 'monica_ai', 'resources', 'sounds', 'scifi', 'sci-fi-facility-alarm-loop-96113.mp3')
            if os.path.exists(sound_path):
                self.alarm_sound = pygame.mixer.Sound(sound_path)
                self.alarm_sound.set_volume(0.7)
                print("[DialWindow] Facility alarm sound loaded")
        except Exception as e:
            print(f"[DialWindow] Could not load alarm sound: {e}")
    
    def show(self):
        """Show the dial with materialization effect."""
        if not self.visible:
            self.is_materializing = True
            self.is_dematerializing = False
            self.materialize_progress = 0.0
            print("[DialWindow] Dial materializing...")
    
    def hide(self):
        """Hide the dial with dematerialization effect."""
        if self.visible or self.is_materializing:
            self.is_dematerializing = True
            self.is_materializing = False
            print("[DialWindow] Dial dematerializing...")
    
    def set_value(self, value: float):
        """Set the dial value (0.0 to 1.0)."""
        self.prev_value = self.value
        self.target_value = max(0.0, min(1.0, value))
        
        # Track value history for direction detection
        self.value_history.append(value)
        if len(self.value_history) > self.max_history:
            self.value_history.pop(0)
        
        # Detect rotation direction
        self._detect_rotation_direction()
        
        # Control alarm based on direction
        if self.rotation_direction == 1:  # Clockwise
            self.activate_alarm()
        elif self.rotation_direction == -1:  # Counterclockwise
            self.deactivate_alarm()
    
    def get_value(self) -> float:
        """Get the current dial value."""
        return self.value
    
    def _detect_rotation_direction(self):
        """Detect if dial is rotating clockwise or counterclockwise."""
        if len(self.value_history) < 3:
            self.rotation_direction = 0
            return
        
        # Check trend in recent values
        recent = self.value_history[-3:]
        if recent[-1] > recent[0] + 0.05:  # Increasing
            self.rotation_direction = 1  # Clockwise
        elif recent[-1] < recent[0] - 0.05:  # Decreasing
            self.rotation_direction = -1  # Counterclockwise
        else:
            self.rotation_direction = 0  # No significant change
    
    def activate_alarm(self):
        """Activate facility alarm (looping)."""
        if not self.alarm_active and self.alarm_sound:
            try:
                self.alarm_channel = self.alarm_sound.play(-1)  # Loop indefinitely
                self.alarm_active = True
                print("[DialWindow] ⚠️ FACILITY ALARM ACTIVATED")
            except Exception as e:
                print(f"[DialWindow] Alarm activation error: {e}")
    
    def deactivate_alarm(self):
        """Deactivate facility alarm."""
        if self.alarm_active:
            try:
                if self.alarm_channel:
                    self.alarm_channel.stop()
                self.alarm_active = False
                print("[DialWindow] Alarm deactivated")
            except Exception as e:
                print(f"[DialWindow] Alarm deactivation error: {e}")
    
    def _update(self, dt: float):
        """Update animation state."""
        self.rotation += dt * 0.3
        self.glow_phase += dt * 3
        self.scan_angle += dt * 180  # Degrees per second
        
        # Smooth value transition
        diff = self.target_value - self.value
        if abs(diff) > 0.001:
            self.value += diff * dt * 5
            if self.on_value_change:
                self.on_value_change(self.value)
        
        # Update active segment based on value
        self.active_segment = int(self.value * (self.num_segments - 1))
        
        # Materialization
        if self.is_materializing:
            self.materialize_progress += dt / 1.5
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
    
    def _render(self) -> np.ndarray:
        """Render the dial frame."""
        # Green screen background
        frame = np.full((self.height, self.width, 3), GREEN_SCREEN, dtype=np.uint8)
        
        if self.materialize_progress <= 0:
            return frame
        
        alpha = self.materialize_progress
        current_radius = int(self.radius * alpha)
        
        if current_radius < 10:
            return frame
        
        # Outer glow rings - ENHANCED for brighter neon appearance
        glow_layers = 8 if self.alarm_active else 6
        for i in range(glow_layers, 0, -1):
            glow_radius = current_radius + i * 15
            glow_intensity = 0.35 * (glow_layers - i + 1) / glow_layers * alpha
            if self.alarm_active:
                # Red pulsing glow when alarm active
                pulse = 0.5 + 0.5 * math.sin(self.glow_phase * 4)
                glow_color = (int(50 * glow_intensity), int(50 * glow_intensity), int(255 * glow_intensity * pulse))
            else:
                glow_color = tuple(int(c * glow_intensity * 1.5) for c in self.dial_glow)
            cv2.circle(frame, self.center, glow_radius, glow_color, 3, cv2.LINE_AA)
        
        # Main dial circle - BRIGHTER
        main_color = self.dial_color if not self.alarm_active else (50, 50, 255)
        cv2.circle(frame, self.center, current_radius, 
                  tuple(int(c * alpha * 1.2) for c in main_color), 3, cv2.LINE_AA)
        
        # Inner circle
        inner_radius = int(current_radius * 0.6)
        cv2.circle(frame, self.center, inner_radius,
                  tuple(int(c * alpha * 0.5) for c in self.dial_color), 1, cv2.LINE_AA)
        
        # Innermost circle
        innermost_radius = int(current_radius * 0.3)
        cv2.circle(frame, self.center, innermost_radius,
                  tuple(int(c * alpha * 0.3) for c in self.dial_color), 1, cv2.LINE_AA)
        
        # Draw segments
        for i in range(self.num_segments):
            angle = (2 * math.pi * i / self.num_segments) + self.rotation
            
            # Segment lines
            inner_x = int(self.center[0] + inner_radius * math.cos(angle))
            inner_y = int(self.center[1] + inner_radius * math.sin(angle))
            outer_x = int(self.center[0] + current_radius * math.cos(angle))
            outer_y = int(self.center[1] + current_radius * math.sin(angle))
            
            # Color based on active segment
            if i == self.active_segment:
                seg_color = tuple(int(c * alpha) for c in self.dial_active)
                thickness = 3
            elif i <= self.active_segment:
                intensity = 0.5 + 0.5 * (i / max(1, self.active_segment))
                seg_color = tuple(int(c * alpha * intensity) for c in self.dial_glow)
                thickness = 2
            else:
                seg_color = tuple(int(c * alpha * 0.3) for c in self.dial_color)
                thickness = 1
            
            cv2.line(frame, (inner_x, inner_y), (outer_x, outer_y), seg_color, thickness, cv2.LINE_AA)
            
            # Segment dots at outer edge
            dot_radius = 4 if i == self.active_segment else 2
            cv2.circle(frame, (outer_x, outer_y), dot_radius, seg_color, -1, cv2.LINE_AA)
        
        # Arc showing value
        start_angle = -90 + math.degrees(self.rotation)
        end_angle = start_angle + self.value * 360
        
        # Draw filled arc segments
        for a in range(int(start_angle), int(end_angle), 5):
            a_rad = math.radians(a)
            arc_inner = int(inner_radius * 1.05)
            arc_outer = int(current_radius * 0.95)
            
            x1 = int(self.center[0] + arc_inner * math.cos(a_rad))
            y1 = int(self.center[1] + arc_inner * math.sin(a_rad))
            x2 = int(self.center[0] + arc_outer * math.cos(a_rad))
            y2 = int(self.center[1] + arc_outer * math.sin(a_rad))
            
            arc_color = tuple(int(c * alpha * 0.4) for c in self.dial_active)
            cv2.line(frame, (x1, y1), (x2, y2), arc_color, 2, cv2.LINE_AA)
        
        # Center indicator needle
        indicator_angle = math.radians(-90 + self.value * 360) + self.rotation
        indicator_len = int(current_radius * 0.85)
        indicator_x = int(self.center[0] + indicator_len * math.cos(indicator_angle))
        indicator_y = int(self.center[1] + indicator_len * math.sin(indicator_angle))
        
        # Indicator line with glow
        cv2.line(frame, self.center, (indicator_x, indicator_y),
                tuple(int(c * alpha * 0.3) for c in self.dial_active), 8, cv2.LINE_AA)
        cv2.line(frame, self.center, (indicator_x, indicator_y),
                tuple(int(c * alpha * 0.6) for c in self.dial_active), 4, cv2.LINE_AA)
        cv2.line(frame, self.center, (indicator_x, indicator_y),
                tuple(int(c * alpha) for c in self.dial_active), 2, cv2.LINE_AA)
        
        # Indicator tip
        cv2.circle(frame, (indicator_x, indicator_y), 6, 
                  tuple(int(c * alpha) for c in self.dial_active), -1, cv2.LINE_AA)
        
        # Center dot
        cv2.circle(frame, self.center, 10, tuple(int(c * alpha) for c in self.dial_glow), -1, cv2.LINE_AA)
        cv2.circle(frame, self.center, 6, (255, 255, 255), -1, cv2.LINE_AA)
        
        # Scanning line effect during materialization
        if self.is_materializing or self.is_dematerializing:
            scan_rad = math.radians(self.scan_angle)
            scan_x = int(self.center[0] + current_radius * 1.2 * math.cos(scan_rad))
            scan_y = int(self.center[1] + current_radius * 1.2 * math.sin(scan_rad))
            cv2.line(frame, self.center, (scan_x, scan_y), (255, 255, 255), 1, cv2.LINE_AA)
        
        # Value text
        value_text = f"{int(self.value * 100)}%"
        font = cv2.FONT_HERSHEY_SIMPLEX
        text_size = cv2.getTextSize(value_text, font, 0.8, 2)[0]
        text_x = self.center[0] - text_size[0] // 2
        text_y = self.center[1] + current_radius + 50
        
        cv2.putText(frame, value_text, (text_x, text_y), font, 0.8,
                   tuple(int(c * alpha) for c in self.text_color), 2, cv2.LINE_AA)
        
        # Title
        title = "CONTROL DIAL"
        title_size = cv2.getTextSize(title, font, 0.5, 1)[0]
        title_x = self.center[0] - title_size[0] // 2
        cv2.putText(frame, title, (title_x, 30), font, 0.5,
                   tuple(int(c * alpha) for c in self.text_color), 1, cv2.LINE_AA)
        
        return frame
    
    def _run_loop(self):
        """Main render loop."""
        cv2.namedWindow("Monica Dial", cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO)
        cv2.resizeWindow("Monica Dial", self.width, self.height)
        
        # Bring window to front using Windows API
        try:
            import ctypes
            hwnd = ctypes.windll.user32.FindWindowW(None, "Monica Dial")
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
            
            cv2.imshow("Monica Dial", frame)
            
            key = cv2.waitKey(16) & 0xFF  # ~60 FPS
            if key == ord('q'):
                break
            elif key == ord('s'):  # Show
                self.show()
            elif key == ord('h'):  # Hide
                self.hide()
            elif key == ord('+'): # Increase value
                self.set_value(self.value + 0.1)
            elif key == ord('-'):  # Decrease value
                self.set_value(self.value - 0.1)
        
        cv2.destroyWindow("Monica Dial")
    
    def start(self):
        """Start the dial window in a separate thread."""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._run_loop, daemon=True)
            self.thread.start()
            print("[DialWindow] Window started (Press 's' to show, 'h' to hide, '+/-' to adjust, 'q' to quit)")
    
    def stop(self):
        """Stop the dial window."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
        print("[DialWindow] Window stopped")


# Singleton instance
_dial_window: Optional[MonicaDialWindow] = None


def get_dial_window() -> MonicaDialWindow:
    """Get singleton dial window instance."""
    global _dial_window
    if _dial_window is None:
        _dial_window = MonicaDialWindow()
    return _dial_window


if __name__ == "__main__":
    """Run dial window standalone when executed directly."""
    print("[DialWindow] Running standalone...")
    dial = get_dial_window()
    dial.start()
    
    try:
        # Keep running until window is closed
        while dial.running:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("[DialWindow] Interrupted by user")
    finally:
        dial.stop()
        print("[DialWindow] Stopped")


# Test mode
if __name__ == "__main__":
    print("Monica Dial Window - Green Screen Mode")
    print("Press 's' to show, 'h' to hide, '+/-' to adjust value, 'q' to quit")
    
    dial = MonicaDialWindow(400, 400)
    dial.running = True
    dial._run_loop()
