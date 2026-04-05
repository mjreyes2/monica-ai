"""
Monica Hand Keyboard - Virtual keyboard controlled by hand/finger detection.
Re-exports the holographic keyboard window and integrates with hand_detector.
"""

try:
    from monica_ai.src.utils.monica_keyboard_window import MonicaKeyboardWindow, KeyState
except ImportError:
    # Provide minimal stub so downstream imports don't break
    class KeyState:
        def __init__(self, label="", x=0, y=0, width=0, height=0, pressed=False, press_time=0.0):
            self.label = label
            self.x = x
            self.y = y
            self.width = width
            self.height = height
            self.pressed = pressed
            self.press_time = press_time

    class MonicaKeyboardWindow:
        """Stub: full keyboard requires monica_ai.src.utils.monica_keyboard_window."""
        def __init__(self, width=800, height=300):
            self.width = width
            self.height = height
            self.visible = False
            self.running = False
            print("[HandKeyboard] Full keyboard not available - stub loaded")

        def show(self): pass
        def hide(self): pass

__all__ = ['MonicaKeyboardWindow', 'KeyState']
