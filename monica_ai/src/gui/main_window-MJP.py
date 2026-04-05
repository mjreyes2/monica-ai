"""
Main Window for Monica AI.
Modern, dark-themed GUI with camera preview, chat interface, and audio visualization.
"""
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import queue
import time
import ctypes
import re
from difflib import SequenceMatcher
from typing import Optional, Dict, Any
from PIL import Image, ImageTk
import numpy as np
from pathlib import Path

try:
    from ..audio.transcription_fixer import TranscriptionFixer
    HAS_TRANSCRIPTION_FIXER = True
except Exception:
    TranscriptionFixer = None
    HAS_TRANSCRIPTION_FIXER = False


class ToolTip:
    """Create a tooltip for a given widget."""
    def __init__(self, widget, text, delay=500):
        self.widget = widget
        self.text = text
        self.delay = delay
        self.tooltip_window = None
        self.scheduled_id = None
        
        widget.bind("<Enter>", self._schedule_tooltip)
        widget.bind("<Leave>", self._hide_tooltip)
        widget.bind("<ButtonPress>", self._hide_tooltip)
    
    def _schedule_tooltip(self, event=None):
        self._hide_tooltip()
        self.scheduled_id = self.widget.after(self.delay, self._show_tooltip)
    
    def _show_tooltip(self, event=None):
        if self.tooltip_window:
            return
        
        x = self.widget.winfo_rootx() + self.widget.winfo_width() + 5
        y = self.widget.winfo_rooty() + self.widget.winfo_height() // 2
        
        self.tooltip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        
        # Style the tooltip
        frame = tk.Frame(tw, bg="#2a2a2a", relief="solid", borderwidth=1)
        frame.pack()
        
        label = tk.Label(
            frame,
            text=self.text,
            bg="#2a2a2a",
            fg="#ffffff",
            font=("Segoe UI", 9),
            padx=8,
            pady=4,
            justify=tk.LEFT,
            wraplength=250
        )
        label.pack()
    
    def _hide_tooltip(self, event=None):
        if self.scheduled_id:
            self.widget.after_cancel(self.scheduled_id)
            self.scheduled_id = None
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None

# Import cv2 for image processing
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

from .settings_dialog import SettingsDialog

# Vision system - LAZY LOAD (heavy imports like MediaPipe, TensorFlow, DeepFace)
# These are loaded when the vision system is first used, not at startup
HAS_VISION = True  # Assume available, load on first use
_vision_system_instance = None

def get_vision_system():
    """
    Lazy load vision system on first use.
    This defers loading of MediaPipe, TensorFlow, DeepFace etc. until needed.
    """
    global _vision_system_instance, HAS_VISION
    if _vision_system_instance is None:
        try:
            from ..vision.vision_system import get_vision_system as _get_vs
            _vision_system_instance = _get_vs()
            print("[OK] Vision system loaded (lazy)")
        except Exception as e:
            print(f"[WARNING] Vision system not available: {e}")
            HAS_VISION = False
    return _vision_system_instance

# Import world info utilities
try:
    from ..utils.world_info import get_current_time, get_weather, get_world_context
    HAS_WORLD_INFO = True
except ImportError:
    HAS_WORLD_INFO = False
    print("[WARNING] World info utilities not available")

# Import user memory
try:
    from ..ai.user_memory import get_user_memory
    HAS_USER_MEMORY = True
except ImportError:
    HAS_USER_MEMORY = False
    print("[WARNING] User memory not available")

# Import holographic globe (lazy load to avoid startup issues)
HAS_GLOBE = False
HolographicGlobe = None

# Paths to holographic components (in parent monica_project folder)
import sys
MONICA_PROJECT_ROOT = Path(__file__).parent.parent.parent.parent  # monica_project folder
if str(MONICA_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(MONICA_PROJECT_ROOT))

def _load_globe():
    global HAS_GLOBE, HolographicGlobe
    if HolographicGlobe is None:
        try:
            from monica_holographic_globe_advanced import HolographicGlobe as Globe
            HolographicGlobe = Globe
            HAS_GLOBE = True
            print("[GLOBE] Holographic globe module loaded")
            return True
        except Exception as e:
            print(f"[GLOBE] Not available: {e}")
            return False
    return HAS_GLOBE

# Import file manager
try:
    from ..utils.file_manager import get_file_manager
    HAS_FILE_MANAGER = True
except ImportError:
    HAS_FILE_MANAGER = False
    print("[WARNING] File manager not available")

# Study assistant - LAZY LOAD (has heavy OCR imports)
HAS_STUDY_ASSISTANT = True  # Assume available
_study_assistant = None

def _get_study_assistant_lazy(ai_manager=None, tts_manager=None):
    """Lazy load study assistant on first use."""
    global _study_assistant, HAS_STUDY_ASSISTANT
    if _study_assistant is None:
        try:
            from ..study.study_assistant import get_study_assistant
            _study_assistant = get_study_assistant(ai_manager, tts_manager)
        except Exception as e:
            print(f"[WARNING] Study Assistant not available: {e}")
            HAS_STUDY_ASSISTANT = False
    return _study_assistant

# Keep old import for compatibility but don't execute at load time
StudyAssistant = None  # Will be set on first use


class _TutorOverlay:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.window = None
        self.canvas = None
        self.vx = 0
        self.vy = 0
        self.vw = 0
        self.vh = 0

    def is_open(self) -> bool:
        return self.window is not None and bool(self.window.winfo_exists())

    def close(self):
        if not self.is_open():
            self.window = None
            self.canvas = None
            return
        try:
            self.window.destroy()
        except Exception:
            pass
        self.window = None
        self.canvas = None

    def show(self, boxes, ttl_ms: int = 15000):
        self.close()

        user32 = ctypes.windll.user32
        SM_XVIRTUALSCREEN = 76
        SM_YVIRTUALSCREEN = 77
        SM_CXVIRTUALSCREEN = 78
        SM_CYVIRTUALSCREEN = 79

        self.vx = int(user32.GetSystemMetrics(SM_XVIRTUALSCREEN))
        self.vy = int(user32.GetSystemMetrics(SM_YVIRTUALSCREEN))
        self.vw = int(user32.GetSystemMetrics(SM_CXVIRTUALSCREEN))
        self.vh = int(user32.GetSystemMetrics(SM_CYVIRTUALSCREEN))

        self.window = tk.Toplevel(self.root)
        self.window.withdraw()
        self.window.overrideredirect(True)
        self.window.attributes('-topmost', True)
        self.window.configure(bg='#ff00ff')
        self.window.attributes('-transparentcolor', '#ff00ff')
        self.window.geometry(f"{self.vw}x{self.vh}+{self.vx}+{self.vy}")

        self.canvas = tk.Canvas(
            self.window,
            bg='#ff00ff',
            highlightthickness=0,
            bd=0
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.window.update_idletasks()
        self._set_clickthrough()

        for b in boxes:
            x1 = int(b['x1']) - self.vx
            y1 = int(b['y1']) - self.vy
            x2 = int(b['x2']) - self.vx
            y2 = int(b['y2']) - self.vy
            label = str(b.get('label', '')).strip()
            color = b.get('color', '#00ffaa')

            self.canvas.create_rectangle(x1, y1, x2, y2, outline=color, width=4)
            if label:
                self.canvas.create_rectangle(x1, max(0, y1 - 22), x1 + min(400, max(80, (len(label) * 8))), y1, outline=color, fill=color, width=0)
                self.canvas.create_text(x1 + 6, max(10, y1 - 11), text=label, fill='#0a0a0a', anchor='w', font=('Segoe UI', 10, 'bold'))

        self.window.bind('<Escape>', lambda e: self.close())
        self.window.deiconify()
        if ttl_ms > 0:
            self.window.after(ttl_ms, self.close)

    def _set_clickthrough(self):
        if not self.is_open():
            return

        hwnd = int(self.window.winfo_id())
        GWL_EXSTYLE = -20
        WS_EX_LAYERED = 0x00080000
        WS_EX_TRANSPARENT = 0x00000020
        WS_EX_TOOLWINDOW = 0x00000080
        ex = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, ex | WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOOLWINDOW)


class MainWindow:
    """
    Main application window for Monica AI.
    
    Features:
    - Camera preview with Spout output option
    - Chat interface with streaming responses
    - Audio visualization
    - Voice input with wake word support
    - Settings dialog for device configuration
    """
    
    def __init__(self, root: tk.Tk, app):
        """
        Initialize the main window.
        
        Args:
            root: Tkinter root window
            app: Main application instance
        """
        self.root = root
        self.app = app
        
        # Get managers from app (may be None during init)
        self.camera = app.camera
        self.audio = app.audio
        self.tts = app.tts
        self.conversation = app.conversation
        self.config = app.config

        # Retrieval/Knowledge health (KB/PDF/MaxOne) - displayed in status bar once UI is ready
        self._kb_health = None

        self._transcription_fixer = None
        if HAS_TRANSCRIPTION_FIXER and TranscriptionFixer is not None:
            try:
                self._transcription_fixer = TranscriptionFixer()
            except Exception:
                self._transcription_fixer = None
        
        # UI state
        self.is_listening = False
        self.is_wake_word_mode = False
        self.camera_photo = None
        self.update_id = None
        self.is_initializing_startup = False  # Flag to prevent interruptions during startup sequence
        self.speech_model_ready = False  # Flag to track if speech model is loaded
        self.monica_activated = False  # Monica only responds after "Monica initialize"
        
        # Vision system - defer loading to prevent UI freeze
        self.vision_system = None
        self.vision_enabled = False
        self._vision_loading = False

        self._vision_frame_lock = threading.Lock()
        self._latest_vision_frame = None
        self._vision_frame_event = threading.Event()
        self._vision_worker_started = False
        self._current_vision_result = None
        
        # Load vision system in background after GUI is ready
        def _load_vision_async():
            if not HAS_VISION or self._vision_loading:
                return
            self._vision_loading = True
            try:
                import threading
                def load():
                    try:
                        vs = get_vision_system()
                        # Update in main thread
                        self.root.after(0, lambda: self._set_vision_system(vs))
                    except Exception as e:
                        print(f"[VISION] Load error: {e}")
                threading.Thread(target=load, daemon=True).start()
            except Exception as e:
                print(f"[VISION] Background load failed: {e}")
                self._vision_loading = False
        
        # Delay vision loading by 500ms to let GUI render first
        self.root.after(500, _load_vision_async)
        
        # Holographic globe (lazy loaded when needed)
        self.globe = None
        self.globe_active = False
        
        # Study assistant
        self.study_assistant = None
        self.study_mode_active = False
        self._tutor_overlay = _TutorOverlay(self.root)
        if HAS_STUDY_ASSISTANT:
            try:
                self.study_assistant = _get_study_assistant_lazy(
                    ai_manager=self.conversation,
                    tts_manager=self.tts
                )
                print("[OK] Study Assistant connected to GUI")
            except Exception as e:
                print(f"[WARNING] Study Assistant init failed: {e}")
        
        # Window interaction tracking (for crash prevention)
        self._window_busy = False
        self._geometry_change_time = 0
        
        # AR Window runs in SEPARATE THREAD to prevent Tkinter/OpenCV conflicts
        self._ar_thread_running = False
        self._ar_frame_queue = None
        self._ar_thread = None
        
        # Setup UI
        self._setup_styles()
        self._create_widgets()
        
        # Bind window events to pause updates during move/resize
        self.root.bind('<Configure>', self._on_window_configure)
        self.root.bind('<Button-1>', self._on_window_click)
        self.root.bind('<ButtonRelease-1>', self._on_window_release)
        
        # Setup callbacks
        self._setup_callbacks()
        self._start_update_loop()
    
    def _set_vision_system(self, vs):
        """Set vision system after background loading."""
        if vs:
            self.vision_system = vs
            self.vision_enabled = True
            print("[OK] Vision system connected to GUI (async)")

            if not self._vision_worker_started:
                self._vision_worker_started = True

                def _vision_worker():
                    last_process_ts = 0.0
                    while True:
                        self._vision_frame_event.wait()
                        try:
                            with self._vision_frame_lock:
                                frame = self._latest_vision_frame
                                self._latest_vision_frame = None
                                self._vision_frame_event.clear()

                            if frame is None:
                                continue

                            now = time.time()
                            if now - last_process_ts < 0.05:
                                continue
                            last_process_ts = now

                            try:
                                self._current_vision_result = self.vision_system.process_frame(frame)
                            except Exception:
                                pass
                        except Exception:
                            pass

                threading.Thread(target=_vision_worker, daemon=True).start()
    
    def _setup_styles(self):
        """Configure ttk styles for dark theme."""
        style = ttk.Style()
        
        # Use clam theme as base
        style.theme_use('clam')
        
        # Colors
        self.colors = {
            'bg': '#1e1e1e',
            'bg_secondary': '#2d2d2d',
            'bg_tertiary': '#3a3a3a',
            'fg': '#ffffff',
            'fg_secondary': '#b0b0b0',
            'accent': '#4fc3f7',
            'accent_hover': '#81d4fa',
            'success': '#69f0ae',
            'warning': '#ffb74d',
            'error': '#ff5252',
            'user_msg': '#4fc3f7',
            'monica_msg': '#69f0ae',
            'system_msg': '#ff8a65'
        }
        
        # Configure root
        self.root.configure(bg=self.colors['bg'])
        
        # Frame styles
        style.configure('TFrame', background=self.colors['bg'])
        style.configure('Secondary.TFrame', background=self.colors['bg_secondary'])
        
        # Label styles
        style.configure(
            'TLabel',
            background=self.colors['bg'],
            foreground=self.colors['fg'],
            font=(self.config.FONT_FAMILY, self.config.FONT_SIZE)
        )
        style.configure(
            'Title.TLabel',
            font=(self.config.FONT_FAMILY, 14, 'bold')
        )
        style.configure(
            'Status.TLabel',
            background=self.colors['bg_secondary'],
            foreground=self.colors['fg_secondary']
        )
        
        # Button styles
        style.configure(
            'TButton',
            background=self.colors['bg_tertiary'],
            foreground=self.colors['fg'],
            font=(self.config.FONT_FAMILY, self.config.FONT_SIZE),
            padding=(10, 5)
        )
        style.map('TButton',
            background=[('active', self.colors['accent']), ('pressed', self.colors['accent_hover'])]
        )
        
        style.configure(
            'Accent.TButton',
            background=self.colors['accent'],
            foreground='#000000'
        )
        
        # LabelFrame styles
        style.configure(
            'TLabelframe',
            background=self.colors['bg_secondary'],
            foreground=self.colors['fg']
        )
        style.configure(
            'TLabelframe.Label',
            background=self.colors['bg_secondary'],
            foreground=self.colors['fg'],
            font=(self.config.FONT_FAMILY, self.config.FONT_SIZE, 'bold')
        )
        
        # Entry styles
        style.configure(
            'TEntry',
            fieldbackground=self.colors['bg_tertiary'],
            foreground=self.colors['fg'],
            insertcolor=self.colors['fg']
        )
        
        # Combobox styles
        style.configure(
            'TCombobox',
            fieldbackground=self.colors['bg_tertiary'],
            background=self.colors['bg_tertiary'],
            foreground=self.colors['fg']
        )
        
        # Scale styles
        style.configure(
            'TScale',
            background=self.colors['bg'],
            troughcolor=self.colors['bg_tertiary']
        )
    
    def _create_widgets(self):
        """Create all UI widgets with scrollable main area."""
        # Create outer container with scrollbar on the RIGHT edge
        self.outer_frame = ttk.Frame(self.root)
        self.outer_frame.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbar on the far right
        self.main_scrollbar = ttk.Scrollbar(self.outer_frame, orient="vertical")
        self.main_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Canvas for scrollable content
        self.main_canvas = tk.Canvas(
            self.outer_frame,
            bg=self.colors['bg'],
            highlightthickness=0,
            yscrollcommand=self.main_scrollbar.set
        )
        self.main_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.main_scrollbar.config(command=self.main_canvas.yview)
        
        # Main container inside canvas
        self.main_frame = ttk.Frame(self.main_canvas)
        
        # Create window in canvas
        self.canvas_window = self.main_canvas.create_window(
            (0, 0), 
            window=self.main_frame, 
            anchor="nw"
        )
        
        # Configure canvas scrolling
        def configure_scroll(event):
            self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all"))
        self.main_frame.bind("<Configure>", configure_scroll)
        
        # Make canvas resize with window
        def configure_canvas(event):
            self.main_canvas.itemconfig(self.canvas_window, width=event.width)
        self.main_canvas.bind("<Configure>", configure_canvas)
        
        # Enable mouse wheel scrolling
        def on_mousewheel(event):
            self.main_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        self.main_canvas.bind_all("<MouseWheel>", on_mousewheel)
        
        # Add padding inside main_frame
        self.content_frame = ttk.Frame(self.main_frame)
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel - Camera and visualization
        self._create_left_panel()
        
        # Right panel - Chat and controls
        self._create_right_panel()
        
        # Status bar (outside scrollable area)
        self._create_status_bar()
    
    def _create_left_panel(self):
        """Create left panel with camera and audio visualization."""
        self.left_panel = ttk.Frame(self.content_frame, width=450)
        self.left_panel.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 10))
        self.left_panel.pack_propagate(False)
        
        # Camera preview
        self.camera_frame = ttk.LabelFrame(
            self.left_panel,
            text="Camera Preview",
            padding=10
        )
        self.camera_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.camera_canvas = tk.Canvas(
            self.camera_frame,
            bg=self.colors['bg'],
            highlightthickness=0
        )
        self.camera_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Camera controls
        self.camera_controls = ttk.Frame(self.camera_frame)
        self.camera_controls.pack(fill=tk.X, pady=(10, 0))
        
        self.spout_var = tk.BooleanVar(value=self.config.SPOUT_ENABLED)
        self.spout_check = ttk.Checkbutton(
            self.camera_controls,
            text="Enable Spout (OBS)",
            variable=self.spout_var,
            command=self._toggle_spout
        )
        self.spout_check.pack(side=tk.LEFT)
        
        # Professional Audio Level Monitor
        self.audio_frame = ttk.LabelFrame(
            self.left_panel,
            text="",  # Title is in the meter itself
            padding=5
        )
        self.audio_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Import and create THREAD-SAFE audio meter (no threading, uses after())
        try:
            from .safe_audio_meter import SafeAudioMeter
            self.audio_meter = SafeAudioMeter(
                self.audio_frame,
                width=380,  # Fit the panel width
                height=100   # Professional height
            )
            self.audio_meter.pack(fill=tk.X)
            print("[OK] Thread-safe audio meter activated")
            self.audio_visualizer = self.audio_meter  # Compatibility alias
        except Exception as e:
            print(f"[WARNING] Safe audio meter not available: {e}")
            # DO NOT use AudioVisualizer - it uses threading which causes crashes!
            # Use simple canvas fallback instead
            self.audio_meter = None
            self.audio_visualizer = None
            # Ultimate fallback to basic canvas
            self.audio_canvas = tk.Canvas(
                self.audio_frame,
                bg=self.colors['bg'],
                height=60,
                highlightthickness=0
            )
            self.audio_canvas.pack(fill=tk.X)
        
        # Status indicators
        self.status_frame = ttk.Frame(self.left_panel)
        self.status_frame.pack(fill=tk.X)
        
        # Listening indicator
        self.listening_indicator = ttk.Label(
            self.status_frame,
            text="Not Listening",
            foreground=self.colors['fg_secondary']
        )
        self.listening_indicator.pack(side=tk.LEFT)
        
        # Wake word indicator
        self.wake_word_indicator = ttk.Label(
            self.status_frame,
            text="",
            foreground=self.colors['accent']
        )
        self.wake_word_indicator.pack(side=tk.RIGHT)
    
    def _create_right_panel(self):
        """Create right panel with chat, controls, and side toolbar."""
        # Main right area container
        self.right_panel = ttk.Frame(self.content_frame)
        self.right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # === SIDE TOOLBAR (AR/Vision/Animations) - on the RIGHT edge ===
        self._create_side_toolbar()
        
        # === MAIN CHAT AREA ===
        self.chat_area = ttk.Frame(self.right_panel)
        self.chat_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Chat display
        self.chat_frame = ttk.LabelFrame(
            self.chat_area,
            text="Conversation",
            padding=10
        )
        self.chat_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Chat text widget with scrollbar
        self.chat_scroll = ttk.Scrollbar(self.chat_frame)
        self.chat_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.chat_display = tk.Text(
            self.chat_frame,
            wrap=tk.WORD,
            state=tk.DISABLED,
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            insertbackground=self.colors['fg'],
            selectbackground=self.colors['accent'],
            font=(self.config.FONT_FAMILY, self.config.FONT_SIZE + 1),  # Slightly larger font
            padx=12,
            pady=12,
            spacing1=4,  # Space before paragraph
            spacing3=4,  # Space after paragraph
            yscrollcommand=self.chat_scroll.set
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True)
        self.chat_scroll.config(command=self.chat_display.yview)
        
        # Configure text tags with better visibility
        self.chat_display.tag_configure('user', foreground='#4fc3f7', font=(self.config.FONT_FAMILY, self.config.FONT_SIZE + 1))
        self.chat_display.tag_configure('user_name', foreground='#4fc3f7', font=(self.config.FONT_FAMILY, self.config.FONT_SIZE + 1, 'bold'))
        self.chat_display.tag_configure('monica', foreground='#81c784', font=(self.config.FONT_FAMILY, self.config.FONT_SIZE + 1))
        self.chat_display.tag_configure('monica_name', foreground='#81c784', font=(self.config.FONT_FAMILY, self.config.FONT_SIZE + 1, 'bold'))
        self.chat_display.tag_configure('system', foreground='#ffb74d', font=(self.config.FONT_FAMILY, self.config.FONT_SIZE))
        self.chat_display.tag_configure('system_name', foreground='#ffb74d', font=(self.config.FONT_FAMILY, self.config.FONT_SIZE, 'bold'))
        self.chat_display.tag_configure('transcript', foreground='#90caf9', font=(self.config.FONT_FAMILY, self.config.FONT_SIZE + 1, 'italic'))
        
        # Input area with label
        self.input_frame = ttk.LabelFrame(self.chat_area, text="Type your message", padding=5)
        self.input_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.input_text = tk.Text(
            self.input_frame,
            height=3,
            wrap=tk.WORD,
            bg='#3a3a3a',
            fg='#ffffff',
            insertbackground='#ffffff',
            font=(self.config.FONT_FAMILY, self.config.FONT_SIZE),
            padx=10,
            pady=10,
            relief=tk.FLAT,
            highlightthickness=2,
            highlightbackground='#4fc3f7',
            highlightcolor='#81d4fa'
        )
        self.input_text.pack(fill=tk.X, expand=True)
        self.input_text.bind('<Return>', self._on_enter)
        self.input_text.bind('<Shift-Return>', lambda e: None)
        
        # Focus on input
        self.input_text.focus_set()
        
        # Control buttons - simplified row
        self.button_frame = ttk.Frame(self.chat_area)
        self.button_frame.pack(fill=tk.X)
        
        # Voice button
        self.voice_btn = ttk.Button(
            self.button_frame,
            text="[Mic] Start Listening",
            command=self._toggle_listening
        )
        self.voice_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Wake word button
        self.wake_word_btn = ttk.Button(
            self.button_frame,
            text="Wake Word",
            command=self._toggle_wake_word
        )
        self.wake_word_btn.pack(side=tk.LEFT, padx=5)
        
        # Send button
        self.send_btn = ttk.Button(
            self.button_frame,
            text="Send",
            style='Accent.TButton',
            command=self._send_message
        )
        self.send_btn.pack(side=tk.LEFT, padx=5)
        
        # Settings button
        self.settings_btn = ttk.Button(
            self.button_frame,
            text="Settings",
            command=self._show_settings
        )
        self.settings_btn.pack(side=tk.RIGHT)
        
        # Force Shutdown button
        self.shutdown_btn = ttk.Button(
            self.button_frame,
            text="STOP",
            command=self._force_shutdown
        )
        self.shutdown_btn.pack(side=tk.RIGHT, padx=5)
        
        # Add welcome message
        # Don't add welcome message - wait for user to initialize
    
    def _create_side_toolbar(self):
        """Create scrollable side toolbar for AR/Vision/Animation controls."""
        # Side toolbar container - WIDER for better button fit
        self.side_toolbar_container = ttk.Frame(self.right_panel, width=220)
        self.side_toolbar_container.pack(side=tk.RIGHT, fill=tk.Y, padx=(8, 0))
        self.side_toolbar_container.pack_propagate(False)
        
        # Create canvas for scrolling
        toolbar_canvas = tk.Canvas(
            self.side_toolbar_container,
            bg=self.colors['bg'],
            highlightthickness=0,
            width=205
        )
        toolbar_scrollbar = ttk.Scrollbar(
            self.side_toolbar_container,
            orient="vertical",
            command=toolbar_canvas.yview
        )
        
        # Scrollable frame inside canvas
        self.side_toolbar = ttk.Frame(toolbar_canvas)
        
        # Configure scrolling
        self.side_toolbar.bind(
            "<Configure>",
            lambda e: toolbar_canvas.configure(scrollregion=toolbar_canvas.bbox("all"))
        )
        
        toolbar_canvas.create_window((0, 0), window=self.side_toolbar, anchor="nw", width=200)
        toolbar_canvas.configure(yscrollcommand=toolbar_scrollbar.set)
        
        # Pack scrollbar and canvas
        toolbar_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        toolbar_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Enable mouse wheel scrolling on toolbar
        def on_toolbar_mousewheel(event):
            toolbar_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        toolbar_canvas.bind("<MouseWheel>", on_toolbar_mousewheel)
        self.side_toolbar.bind("<MouseWheel>", on_toolbar_mousewheel)
        
        # Toolbar header
        toolbar_header = ttk.Label(
            self.side_toolbar,
            text="Controls",
            font=(self.config.FONT_FAMILY, 12, 'bold'),
            foreground=self.colors['accent']
        )
        toolbar_header.pack(pady=(10, 15))
        
        # === AR WINDOWS SECTION ===
        ar_frame = ttk.LabelFrame(self.side_toolbar, text="AR Windows", padding=8)
        ar_frame.pack(fill=tk.X, pady=6, padx=8)
        
        # Single column layout with tooltips
        self.btn_orb = ttk.Button(ar_frame, text="Monica Orb", command=self._toggle_orb)
        self.btn_orb.pack(fill=tk.X, pady=3)
        ToolTip(self.btn_orb, "Show Monica's holographic orb.\nSay 'Monica show yourself' to materialize.")
        
        self.btn_globe = ttk.Button(ar_frame, text="Globe", command=self._toggle_globe_window)
        self.btn_globe.pack(fill=tk.X, pady=3)
        ToolTip(self.btn_globe, "Display interactive 3D holographic globe.\nRotate with hand gestures.")
        
        self.btn_keyboard = ttk.Button(ar_frame, text="⌨Keyboard", command=self._toggle_keyboard)
        self.btn_keyboard.pack(fill=tk.X, pady=3)
        ToolTip(self.btn_keyboard, "Show virtual keyboard overlay.\nType by touching keys with your fingertip.")
        
        self.btn_dial = ttk.Button(ar_frame, text="Dial", command=self._toggle_dial)
        self.btn_dial.pack(fill=tk.X, pady=3)
        ToolTip(self.btn_dial, "Show control dial interface.\nRotate with hand gestures to adjust settings.")
        
        # === VISION EFFECTS SECTION ===
        vision_frame = ttk.LabelFrame(self.side_toolbar, text="[Vision] Vision Effects", padding=8)
        vision_frame.pack(fill=tk.X, pady=6, padx=8)
        
        btn_night = ttk.Button(vision_frame, text="Night Vision", command=self._toggle_night_vision)
        btn_night.pack(fill=tk.X, pady=3)
        ToolTip(btn_night, "Green-tinted night vision mode.\nEnhances visibility in dark areas.")
        
        btn_thermal = ttk.Button(vision_frame, text="Thermal Vision", command=self._toggle_thermal)
        btn_thermal.pack(fill=tk.X, pady=3)
        ToolTip(btn_thermal, "Heat signature view (thermal imaging).\nBlue = cold, Red = hot.")
        
        btn_terminator = ttk.Button(vision_frame, text="Terminator", command=self._toggle_terminator_vision)
        btn_terminator.pack(fill=tk.X, pady=3)
        ToolTip(btn_terminator, "Red HUD overlay like the T-800.\nIncludes scan lines and targeting reticle.")
        
        btn_heat = ttk.Button(vision_frame, text="Body Heat", command=self._toggle_body_heat)
        btn_heat.pack(fill=tk.X, pady=3)
        ToolTip(btn_heat, "Detect body heat signatures.\nHighlights warm objects in the scene.")
        
        btn_alarm = ttk.Button(vision_frame, text="Trigger Alarm", command=self._trigger_alarm)
        btn_alarm.pack(fill=tk.X, pady=3)
        ToolTip(btn_alarm, "Trigger red alert alarm effect.\nFlashing red overlay with alarm sound.")
        
        # === BACKGROUND ANIMATIONS SECTION ===
        bg_frame = ttk.LabelFrame(self.side_toolbar, text="[Art] Backgrounds", padding=8)
        bg_frame.pack(fill=tk.X, pady=6, padx=8)
        
        btn_fog = ttk.Button(bg_frame, text="Fog Animation", command=self._toggle_fog_animation)
        btn_fog.pack(fill=tk.X, pady=3)
        ToolTip(btn_fog, "Animated fog/mist background effect.\nOpens in browser window.")
        
        btn_clouds = ttk.Button(bg_frame, text="Clouds Animation", command=self._toggle_clouds_animation)
        btn_clouds.pack(fill=tk.X, pady=3)
        ToolTip(btn_clouds, "Animated cloud background effect.\nOpens in browser window.")
        
        btn_plasma = ttk.Button(bg_frame, text="Plasma Effect", command=self._toggle_plasma_effect)
        btn_plasma.pack(fill=tk.X, pady=3)
        ToolTip(btn_plasma, "Colorful plasma wave animation.\nOpens in browser window.")
        
        btn_stars = ttk.Button(bg_frame, text="[Sparkle] Starfield", command=self._toggle_starfield)
        btn_stars.pack(fill=tk.X, pady=3)
        ToolTip(btn_stars, "Animated starfield/space background.\nOpens in browser window.")
        
        btn_aurora = ttk.Button(bg_frame, text="Aurora", command=self._toggle_aurora)
        btn_aurora.pack(fill=tk.X, pady=3)
        ToolTip(btn_aurora, "Northern lights aurora animation.\nOpens in browser window.")
        
        # === UTILITY SECTION ===
        util_frame = ttk.LabelFrame(self.side_toolbar, text="[Tool] Utilities", padding=8)
        util_frame.pack(fill=tk.X, pady=6, padx=8)
        
        btn_debug = ttk.Button(util_frame, text="Debug Report", command=self._generate_debug_report)
        btn_debug.pack(fill=tk.X, pady=3)
        ToolTip(btn_debug, "Generate system debug report.\nShows status of all Monica components.")
        
        btn_ar = ttk.Button(util_frame, text="[Vision] AR Window", command=self._toggle_ar_window)
        btn_ar.pack(fill=tk.X, pady=3)
        ToolTip(btn_ar, "Open separate AR overlay window.\nShows camera feed with all effects applied.")
        
        # Globe button removed from Utilities per user request (duplicate of AR Holograms section)
        
        btn_study = ttk.Button(util_frame, text="Study Mode", command=self._toggle_study_mode)
        btn_study.pack(fill=tk.X, pady=3)
        ToolTip(btn_study, "Toggle Study Mode.\nMonica reads your screen and helps with studying.")
        
        btn_code = ttk.Button(util_frame, text="Code Editor", command=self._open_code_editor)
        btn_code.pack(fill=tk.X, pady=3)
        ToolTip(btn_code, "Open Monica Code Editor.\nFull IDE with AI assistance for all languages.")
        
        btn_quiz = ttk.Button(util_frame, text="[Note] Quiz/Test", command=self._open_quiz_dialog)
        btn_quiz.pack(fill=tk.X, pady=3)
        ToolTip(btn_quiz, "Take a quiz or test.\nMonica grades and helps you learn from mistakes.")
        
        btn_roleplay = ttk.Button(util_frame, text="Roleplay", command=self._open_roleplay_dialog)
        btn_roleplay.pack(fill=tk.X, pady=3)
        ToolTip(btn_roleplay, "Practice communication skills.\nDEARMAN, assertive communication, and more.")
        
        btn_speaking = ttk.Button(util_frame, text="[Mic] Public Speaking", command=self._open_auditorium)
        btn_speaking.pack(fill=tk.X, pady=3)
        ToolTip(btn_speaking, "Public Speaking Auditorium.\nPractice presentations with AI feedback.")

        # Voice training launcher
        btn_voice_train = ttk.Button(util_frame, text="Voice Trainer", command=self._open_voice_trainer)
        btn_voice_train.pack(fill=tk.X, pady=3)
        ToolTip(btn_voice_train, "Open Monica Voice Training recorder.\nRecord phrases to train personalized speech recognition.")
    
    def _create_status_bar(self):
        """Create status bar at bottom of window."""
        # Status bar frame with visible background
        self.status_frame = ttk.Frame(self.root)
        self.status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Status label (left side)
        self.status_bar = ttk.Label(
            self.status_frame,
            text="Ready",
            style='Status.TLabel',
            padding=(10, 5)
        )
        self.status_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Progress bar (right side, larger and more visible)
        self.progress_bar = ttk.Progressbar(
            self.status_frame,
            mode='indeterminate',
            length=300  # Wider progress bar
        )
        
        # Start with ready state (loading happens when user clicks Listen)
        self.status_bar.config(text="Click '[Mic] Start Listening', then say 'Monica initialize' or press F1")
    
    def _show_loading(self, message: str):
        """Show loading progress bar with message."""
        self.status_bar.config(text=message)
        self.progress_bar.pack(side=tk.RIGHT, padx=10, pady=5)
        self.progress_bar.start(10)
        self.speech_model_ready = False
    
    def _hide_loading(self):
        """Hide loading progress bar."""
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self.speech_model_ready = True
        self.status_bar.config(text="[Mic] Listening - Say 'Monica initialize' to activate")
    
    def _show_startup_progress(self):
        """Show startup sequence progress bar."""
        print("[GUI] Showing startup progress bar")
        # Stop any existing animation
        try:
            self.progress_bar.stop()
        except:
            pass
        # Create a determinate progress bar for startup
        self.progress_bar.config(mode='determinate', maximum=100)
        self.progress_bar['value'] = 0
        self.progress_bar.pack(side=tk.RIGHT, padx=10, pady=5)
        self.status_bar.config(text="Power surge...")
        self.root.update()
    
    def _update_startup_progress(self, stage: str, percent: int):
        """Update startup progress bar."""
        print(f"[GUI] Progress: {percent}% - {stage}")
        try:
            self.progress_bar['value'] = percent
            self.status_bar.config(text=stage)
            self.root.update()
        except Exception as e:
            print(f"[GUI] Progress update error: {e}")
    
    def _hide_startup_progress(self):
        """Hide startup progress bar and show ready status."""
        print("[GUI] Hiding startup progress bar")
        try:
            self.progress_bar.pack_forget()
            self.progress_bar.config(mode='indeterminate')  # Reset for next use
            self._update_status("[OK] Ready - Monica Active")
            self.root.update()
        except Exception as e:
            print(f"[GUI] Hide progress error: {e}")
    
    def _trigger_initialize(self):
        """Trigger Monica initialization (can be called by F1 key or voice)."""
        print("[GUI] F1 pressed - triggering Monica initialize")
        # Simulate the voice command
        self._process_speech("Monica initialize")
    
    def _setup_callbacks(self):
        """Setup callbacks for managers."""
        # Keyboard shortcuts
        self.root.bind('<Alt-s>', lambda e: self._toggle_listening())
        self.root.bind('<Alt-S>', lambda e: self._toggle_listening())
        self.root.bind('<Return>', lambda e: self._send_message())
        self.root.bind('<Escape>', lambda e: self._force_shutdown())
        self.root.bind('<F1>', lambda e: self._trigger_initialize())  # Quick initialize
        print("[GUI] Keyboard shortcuts: Alt+S = Listen, Enter = Send, Escape = Shutdown, F1 = Initialize")

        # Speech recognition callbacks (SAFE) - check both Google STT and SpeechBrain
        speech_callback_registered = False
        if self.audio:
            # Try Google STT first
            if hasattr(self.audio, 'google_stt') and self.audio.google_stt:
                print(f"[GUI] Registering speech callback with Google STT")
                self.audio.google_stt.register_callback(self._on_speech_recognized)
                print("[GUI] [OK] Google STT speech callback registered")
                speech_callback_registered = True
            # Fallback to SpeechBrain
            elif hasattr(self.audio, 'speech_recognizer') and self.audio.speech_recognizer:
                print(f"[GUI] Registering speech callback with SpeechBrain")
                print(f"[GUI] Speech recognizer type: {type(self.audio.speech_recognizer)}")
                print(f"[GUI] Has register_callback: {hasattr(self.audio.speech_recognizer, 'register_callback')}")

                if hasattr(self.audio.speech_recognizer, 'register_callback'):
                    self.audio.speech_recognizer.register_callback(self._on_speech_recognized)
                    # Verify it was added
                    if hasattr(self.audio.speech_recognizer, 'callbacks'):
                        callback_count = len(self.audio.speech_recognizer.callbacks)
                        print(f"[GUI] [OK] SpeechBrain speech callback registered! Total callbacks: {callback_count}")
                    else:
                        print("[GUI] [OK] SpeechBrain speech callback registered!")
                    speech_callback_registered = True
                else:
                    print("[GUI] [ERROR] SpeechBrain recognizer has no register_callback method!")

        if not speech_callback_registered:
            print("[WARNING] [GUI] No speech recognizer available for callback registration!")
            print(f"[WARNING] [GUI] audio={self.audio}")
            if self.audio:
                print(f"[WARNING] [GUI] audio.speech_recognizer={getattr(self.audio, 'speech_recognizer', 'NOT FOUND')}")

        # Wake word detection callbacks (SAFE)
        if self.audio and hasattr(self.audio, 'wake_word_detector') and self.audio.wake_word_detector and hasattr(self.audio.wake_word_detector, 'register_callback'):
            self.audio.wake_word_detector.register_callback(self._on_wake_word_detected)
            print("[GUI] Wake word callback registered successfully")
        else:
            print("[WARNING] [GUI] Wake word detector not available for callback registration.")

        # Set up audio visualization callbacks
        self._connect_audio_visualization()

        # AI response callbacks
        if self.conversation:
            self.conversation.register_response_callback(self._on_ai_response)

        # TTS callbacks
        if self.tts:
            self.tts.register_start_callback(lambda t: self._update_status("Speaking..."))
            self.tts.register_end_callback(lambda t: self._update_status("Ready"))
    
    def _connect_audio_visualization(self):
        """Connect audio visualization to the audio stream."""
        # Professional meter or visualizer callback
        if hasattr(self, 'audio_meter') and self.audio_meter:
            # Professional meter gets raw audio data
            def meter_callback(audio_data, level):
                # DEBUG: Log first few callbacks
                if not hasattr(self, '_meter_callback_count'):
                    self._meter_callback_count = 0
                self._meter_callback_count += 1
                if self._meter_callback_count <= 3:
                    print(f"[GUI-DEBUG] Audio meter callback #{self._meter_callback_count}: level={level}, audio_data shape={audio_data.shape if audio_data is not None else None}")
                self.audio_meter.update_level(audio_data=audio_data)
            self.audio.register_audio_data_callback(meter_callback)
            print("[OK] Professional audio meter connected to audio stream")
            
        elif hasattr(self, 'audio_visualizer') and self.audio_visualizer:
            # Sci-fi visualizer callback
            def visualizer_callback(audio_data, level):
                self.audio_visualizer.update_level(audio_data=audio_data)
                if hasattr(self.audio_visualizer, 'set_speaking'):
                    self.audio_visualizer.set_speaking(self.is_listening)
            self.audio.register_audio_data_callback(visualizer_callback)
            print("[OK] Audio visualizer connected to audio stream")
        
        # Also register simple level callback for fallback
        self.audio.register_level_callback(lambda level: self._update_audio_visualization(level=level))
    
    def _on_voice_activity(self, is_speaking: bool, energy: float):
        """Handle voice activity detection - interrupt Monica when user CLEARLY speaks."""
        # DISABLED: VAD interrupts cause Monica to stop mid-sentence due to noise/breathing
        # Instead, user can say "stop" to interrupt Monica
        # This prevents false interrupts from background noise
        pass
        
        # OLD CODE (disabled):
        # INTERRUPT_THRESHOLD = 0.08  # Very high - only clear loud speech
        # if is_speaking and energy > INTERRUPT_THRESHOLD and self.monica_activated and not self.is_initializing_startup:
        #     if self.tts and self.tts.is_speaking:
        #         print(f"[VAD] User speaking loudly (energy={energy:.4f}) - interrupting Monica!")
        #         self.tts.stop()
        #         self._is_speaking_response = False
        #         self._speech_buffer = ""
    
    def _on_window_configure(self, event):
        """Handle window configure events (move/resize)."""
        # Set busy flag to pause heavy operations
        self._window_busy = True
        self._geometry_change_time = 10  # Skip frames during resize
        
        # Clear busy flag after a short delay
        try:
            self.root.after(200, self._clear_window_busy)
        except Exception:
            pass
    
    def _on_window_click(self, event):
        """Handle mouse click on window."""
        self._window_busy = True
    
    def _on_window_release(self, event):
        """Handle mouse release on window."""
        # Delay clearing to allow window operations to complete
        try:
            self.root.after(100, self._clear_window_busy)
        except Exception:
            pass
    
    def _clear_window_busy(self):
        """Clear the window busy flag."""
        self._window_busy = False
    
    def _start_update_loop(self):
        """Start the UI update loop."""
        self._update_camera()
        self._update_ui()
    
    def _update_camera(self):
        """
        Update camera preview - CRASH-PROOF version.
        Uses defensive programming to prevent GIL crashes during window operations.
        """
        # Check if window exists
        try:
            if not self.root or not self.root.winfo_exists():
                return
        except Exception:
            return
        
        # CRITICAL: Skip ALL processing if window is busy (being moved/resized)
        if self._window_busy or self._geometry_change_time > 0:
            if self._geometry_change_time > 0:
                self._geometry_change_time -= 1
            try:
                self.root.after(50, self._update_camera)
            except Exception:
                pass
            return
        
        # Check window state
        try:
            window_state = self.root.state()
            if window_state != 'normal':
                self.root.after(100, self._update_camera)
                return
        except Exception:
            self.root.after(100, self._update_camera)
            return
        
        # Process camera frame with minimal operations
        try:
            # Show loading state while camera is starting
            if self.camera and not self.camera.is_running:
                # Camera is starting up - show placeholder
                if not hasattr(self, '_showed_loading'):
                    self._showed_loading = True
                    # Draw a dark placeholder with "Starting camera..." text
                    try:
                        canvas_w = self.camera_canvas.winfo_width()
                        canvas_h = self.camera_canvas.winfo_height()
                        if canvas_w > 10 and canvas_h > 10:
                            placeholder = np.zeros((canvas_h, canvas_w, 3), dtype=np.uint8)
                            placeholder[:] = (30, 30, 30)  # Dark gray
                            cv2.putText(placeholder, "Starting camera...", 
                                       (canvas_w//2 - 100, canvas_h//2), 
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (100, 100, 100), 2)
                            img = Image.fromarray(cv2.cvtColor(placeholder, cv2.COLOR_BGR2RGB))
                            photo = ImageTk.PhotoImage(image=img)
                            self.camera_canvas.delete("all")
                            self.camera_canvas.create_image(0, 0, anchor=tk.NW, image=photo)
                            self.camera_canvas._photo = photo
                    except:
                        pass
                self.root.after(100, self._update_camera)
                return
            
            if self.camera and self.camera.is_running:
                # Use BGR frames for vision processing to match OpenCV/MediaPipe expectations
                frame = self.camera.get_frame_bgr()
                
                # DEBUG: Log frame retrieval
                if not hasattr(self, '_frame_debug_logged'):
                    print(f"[GUI-DEBUG] Camera running: {self.camera.is_running}, Frame retrieved: {frame is not None}")
                    if frame is not None:
                        print(f"[GUI-DEBUG] Frame shape: {frame.shape}")
                    self._frame_debug_logged = True
                
                if frame is not None:
                    # Track frame count
                    if not hasattr(self, '_cam_frame_count'):
                        self._cam_frame_count = 0
                    self._cam_frame_count += 1

                    # Skip first few frames to avoid showing laggy warm-up
                    if self._cam_frame_count <= 5:
                        self.root.after(30, self._update_camera)
                        return
                    
                    if self.vision_enabled and self.vision_system:
                        try:
                            with self._vision_frame_lock:
                                self._latest_vision_frame = frame.copy()
                            self._vision_frame_event.set()
                        except Exception:
                            pass
                        
                        # Apply vision effects - DELAY HEAVY LOADING until camera is stable
                        # This prevents the freeze during initial camera startup
                        try:
                            # Only apply effects after 60 frames (~2 seconds) to let camera stabilize
                            # This prevents the initial freeze
                            if self._cam_frame_count > 60:
                                frame = self.vision_system.apply_vision_effects(frame)
                            elif self._cam_frame_count == 60:
                                # Load heavy modules in background thread to avoid blocking
                                import threading
                                def load_vision_async():
                                    try:
                                        self.vision_system._load_heavy_modules()
                                    except:
                                        pass
                                threading.Thread(target=load_vision_async, daemon=True).start()
                        except:
                            pass
                        
                        # AR window is now handled in a SEPARATE THREAD to prevent crashes
                        # Send frame to AR thread if it's running
                        if hasattr(self, '_ar_thread_running') and self._ar_thread_running:
                            if self._cam_frame_count % 2 == 0:
                                try:
                                    self._ar_frame_queue.put_nowait(frame.copy())
                                except:
                                    pass
                    
                    # Send AR-composited frame to Spout (after vision effects applied)
                    # This ensures OBS receives the frame WITH holograms, not just raw camera
                    if self.camera and self.camera.is_spout_enabled():
                        try:
                            self.camera.send_to_spout(frame)
                        except Exception as e:
                            if not hasattr(self, '_spout_error_logged'):
                                print(f"[SPOUT] Error sending AR frame: {e}")
                                self._spout_error_logged = True
                    
                    # Update Tkinter canvas - OPTIMIZED for speed (reduced lag)
                    try:
                        # Cache canvas size (only update every 60 frames)
                        if not hasattr(self, '_cached_canvas_size') or self._cam_frame_count % 60 == 0:
                            self._cached_canvas_size = (
                                self.camera_canvas.winfo_width(),
                                self.camera_canvas.winfo_height()
                            )
                        
                        canvas_width, canvas_height = self._cached_canvas_size
                        
                        if canvas_width > 10 and canvas_height > 10:
                            h, w = frame.shape[:2]
                            ratio = min(canvas_width / w, canvas_height / h)
                            new_w, new_h = int(w * ratio), int(h * ratio)
                            
                            # SPEED OPTIMIZATION: Use fastest interpolation
                            resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_NEAREST)
                            
                            # Convert BGR frame to RGB for Tkinter display
                            resized_rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
                            
                            # Convert to PhotoImage
                            image = Image.fromarray(resized_rgb)
                            self.camera_photo = ImageTk.PhotoImage(image=image)
                            
                            # Update canvas - single operation
                            if not hasattr(self, '_canvas_image_id') or self._canvas_image_id is None:
                                self._canvas_image_id = self.camera_canvas.create_image(
                                    canvas_width // 2, canvas_height // 2,
                                    image=self.camera_photo, anchor=tk.CENTER
                                )
                            else:
                                self.camera_canvas.itemconfig(self._canvas_image_id, image=self.camera_photo)
                    except:
                        # Canvas error - skip this frame
                        pass
        except:
            # Any error - skip this frame
            pass
        
        # Schedule next update (20fps = 50ms for stability and reduced CPU load)
        try:
            self.root.after(50, self._update_camera)
        except:
            pass
    
    def _update_ui(self):
        """Update UI elements."""
        # Update listening indicator
        if self.is_listening:
            self.listening_indicator.config(
                text="Listening",
                foreground=self.colors['success']
            )
        else:
            self.listening_indicator.config(
                text="Not Listening",
                foreground=self.colors['fg_secondary']
            )
        
        # Update wake word indicator
        if self.is_wake_word_mode:
            self.wake_word_indicator.config(
                text=f"Wake word: \"{self.config.WAKE_WORD}\""
            )
        else:
            self.wake_word_indicator.config(text="")
        
        # Schedule next update
        self.root.after(100, self._update_ui)
    
    def _update_audio_visualization(self, level: float = None, audio_data: np.ndarray = None):
        """Update sci-fi audio level visualization."""
        try:
            # Use the new sci-fi visualizer if available
            if hasattr(self, 'audio_visualizer') and self.audio_visualizer:
                if audio_data is not None:
                    self.audio_visualizer.update_level(audio_data=audio_data)
                elif level is not None:
                    self.audio_visualizer.update_level(energy=level)
                
                # Update speaking state if available
                if hasattr(self, 'is_listening'):
                    self.audio_visualizer.set_speaking(self.is_listening)
            
            # Fallback to old visualization
            elif hasattr(self, 'audio_canvas'):
                canvas = self.audio_canvas
                width = canvas.winfo_width()
                height = canvas.winfo_height()
                
                if width <= 1 or height <= 1:
                    return
                
                # Clear canvas
                canvas.delete("all")
                
                # Draw background
                canvas.create_rectangle(0, 0, width, height, fill=self.colors['bg'], outline="")
                
                # Draw level bar
                bar_width = int(width * min(1.0, level * 5))  # Scale for visibility
                
                # Color based on level
                if level < 0.02:
                    color = self.colors['fg_secondary']
                elif level < 0.1:
                    color = self.colors['success']
                elif level < 0.3:
                    color = self.colors['warning']
                else:
                    color = self.colors['error']
                
                # Draw bar
                padding = 10
                bar_height = height - 2 * padding
                canvas.create_rectangle(
                    padding, padding,
                    padding + bar_width, padding + bar_height,
                    fill=color, outline=""
                )
                
                # Draw level markers
                for i in range(1, 10):
                    x = padding + int((width - 2 * padding) * i / 10)
                    canvas.create_line(
                        x, padding, x, padding + bar_height,
                        fill=self.colors['bg_tertiary'], width=1
                    )
                    
        except Exception as e:
            pass
    
    # ==================== Message Handling ====================
    
    def _add_message(self, sender: str, name: str, text: str):
        """Add a message to the chat display with clear formatting."""
        self.chat_display.config(state=tk.NORMAL)
        
        # Add timestamp for user messages
        if sender == 'user':
            import datetime
            timestamp = datetime.datetime.now().strftime("%H:%M")
            self.chat_display.insert(tk.END, f"[{timestamp}] ", "system")
        
        # Add name with emoji indicator
        if sender == 'user':
            self.chat_display.insert(tk.END, f"[Mic] {name}: ", f"{sender}_name")
        elif sender == 'monica':
            self.chat_display.insert(tk.END, f"{name}: ", f"{sender}_name")
        elif sender == 'system':
            self.chat_display.insert(tk.END, f"{name}: ", f"{sender}_name")
        else:
            self.chat_display.insert(tk.END, f"{name}: ", f"{sender}_name")
        
        # Add text with proper formatting
        if text:
            self.chat_display.insert(tk.END, f"{text}\n\n", sender)
        else:
            self.chat_display.insert(tk.END, "\n", sender)
        
        # Scroll to bottom
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)
    
    def _append_to_last_message(self, text: str):
        """Append text to the last message (for streaming)."""
        self.chat_display.config(state=tk.NORMAL)
        
        # Remove last newlines
        content = self.chat_display.get("1.0", tk.END)
        if content.endswith("\n\n\n"):
            self.chat_display.delete("end-3c", "end-1c")
        
        # CRITICAL FIX: Replace the "..." placeholder on first chunk instead of appending
        # This prevents "...Hello" appearing as "..Hello" to users
        if not hasattr(self, '_placeholder_replaced') or not self._placeholder_replaced:
            # Find and remove the "..." placeholder
            try:
                last_line_start = self.chat_display.search("Monica: ", "end-100c", tk.END)
                if last_line_start:
                    placeholder_start = self.chat_display.search("...", last_line_start, tk.END)
                    if placeholder_start:
                        placeholder_end = f"{placeholder_start}+3c"
                        self.chat_display.delete(placeholder_start, placeholder_end)
                        self._placeholder_replaced = True
            except Exception:
                pass
        
        # Insert text before the newlines
        self.chat_display.insert("end-2c", text, "monica")
        
        # Scroll to bottom
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)
    
    def _send_message(self):
        """Send the current input text."""
        text = self.input_text.get("1.0", tk.END).strip()
        
        if not text:
            return
        
        # Clear input
        self.input_text.delete("1.0", tk.END)
        
        # Add user message
        self._add_message('user', 'You', text)

        if self._handle_tutor_command(text):
            return
        
        # Update status
        self._update_status("Thinking...")
        
        # Send to AI
        self.conversation.send_message(text, stream=True)
        
        # Add placeholder for Monica's response
        self._add_message('monica', 'Monica', "...")
        
        # Reset placeholder flag for new response
        self._placeholder_replaced = False

    def _handle_tutor_command(self, text: str) -> bool:
        raw = (text or '').strip()
        if not raw:
            return False

        lowered = raw.lower()
        if lowered in {'tutor clear', 'tutor: clear', '/tutor clear', '/tutor: clear'}:
            self._tutor_overlay.close()
            self._add_message('monica', 'Monica', "Tutor overlay cleared.")
            self._update_status("Ready")
            return True

        if not (lowered.startswith('tutor:') or lowered.startswith('/tutor')):
            return False

        query = raw
        if lowered.startswith('tutor:'):
            query = raw.split(':', 1)[1].strip()
        else:
            query = re.sub(r'^/tutor\s*:?\s*', '', raw, flags=re.IGNORECASE).strip()

        if not query:
            self._add_message('monica', 'Monica', "Tutor mode: tell me what button/menu text to click, e.g. `tutor: click File` or `tutor: Preferences`.")
            self._update_status("Ready")
            return True

        self._update_status("Tutor: analyzing your screen...")
        self._add_message('monica', 'Monica', "Tutor: analyzing your active window...")

        def work():
            try:
                if self.study_assistant is None and HAS_STUDY_ASSISTANT:
                    try:
                        self.study_assistant = _get_study_assistant_lazy(ai_manager=self.conversation, tts_manager=self.tts)
                    except Exception:
                        self.study_assistant = None

                if self.study_assistant is None:
                    self.root.after(0, lambda: self._add_message('monica', 'Monica', "Tutor mode isn't available (Study Assistant failed to load)."))
                    self.root.after(0, lambda: self._update_status("Ready"))
                    return

                win = self._get_active_window_rect_and_title()
                if win is None:
                    self.root.after(0, lambda: self._add_message('monica', 'Monica', "Tutor: couldn't read the active window."))
                    self.root.after(0, lambda: self._update_status("Ready"))
                    return

                left, top, width, height, title = win
                from ..study.study_assistant import ScreenRegion
                region = ScreenRegion(int(left), int(top), int(width), int(height), str(title))
                frame = self.study_assistant.screen_reader.capture_screen(region)
                regions = self.study_assistant.screen_reader.get_text_regions(frame)

                best = self._pick_best_text_region(regions, query)
                if best is None:
                    self.root.after(0, lambda: self._add_message('monica', 'Monica', "Tutor: I couldn't find that text on the active window. Try quoting the exact label (e.g. `tutor: File`)."))
                    self.root.after(0, lambda: self._update_status("Ready"))
                    return

                x1 = int(left + best['x'])
                y1 = int(top + best['y'])
                x2 = int(x1 + best['width'])
                y2 = int(y1 + best['height'])
                label = best.get('text', '').strip()

                boxes = [{
                    'x1': x1 - 6,
                    'y1': y1 - 6,
                    'x2': x2 + 6,
                    'y2': y2 + 6,
                    'label': f"Click: {label}" if label else "Click here",
                    'color': '#00ffaa'
                }]

                def show():
                    self._tutor_overlay.show(boxes, ttl_ms=20000)
                    self._add_message('monica', 'Monica', f"Tutor: highlighted '{label}' in your active window ({title}).")
                    self._update_status("Ready")

                self.root.after(0, show)

            except Exception as e:
                self.root.after(0, lambda: self._add_message('monica', 'Monica', f"Tutor error: {e}"))
                self.root.after(0, lambda: self._update_status("Ready"))

        threading.Thread(target=work, daemon=True).start()
        return True

    def _get_active_window_rect_and_title(self):
        try:
            user32 = ctypes.windll.user32

            hwnd = user32.GetForegroundWindow()
            if not hwnd:
                return None

            length = user32.GetWindowTextLengthW(hwnd)
            buf = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buf, length + 1)
            title = buf.value

            class RECT(ctypes.Structure):
                _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long), ("right", ctypes.c_long), ("bottom", ctypes.c_long)]

            rect = RECT()
            if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
                return None

            left = int(rect.left)
            top = int(rect.top)
            width = int(rect.right - rect.left)
            height = int(rect.bottom - rect.top)
            if width <= 0 or height <= 0:
                return None

            return left, top, width, height, title
        except Exception:
            return None

    def _pick_best_text_region(self, regions, query: str):
        if not regions:
            return None

        q = (query or '').strip().lower()
        q = re.sub(r"[^a-z0-9\s\-_]", " ", q)
        q = re.sub(r"\s+", " ", q).strip()
        if not q:
            return None

        stop = {
            'click', 'select', 'open', 'press', 'choose', 'go', 'to', 'the', 'a', 'an', 'menu', 'button', 'tab', 'panel',
            'then', 'and', 'on', 'in'
        }
        q_words = [w for w in q.split(' ') if w and w not in stop]
        if not q_words:
            q_words = q.split(' ')

        best = None
        best_score = -1.0

        for r in regions:
            t = str(r.get('text', '')).strip()
            if not t:
                continue
            tl = t.lower()

            score = 0.0
            contains = sum(1 for w in q_words if w in tl)
            score += contains * 2.0
            score += SequenceMatcher(None, q, tl).ratio()
            try:
                conf = float(r.get('confidence', 0))
            except Exception:
                conf = 0.0
            if conf > 0:
                score += min(1.0, conf / 100.0)

            if score > best_score:
                best_score = score
                best = r

        if best_score < 1.0:
            return None
        return best
    
    def _on_enter(self, event):
        """Handle Enter key press."""
        if not event.state & 0x1:  # Not Shift+Enter
            self._send_message()
            return "break"
    
    # ==================== Voice Control ====================
    
    def _toggle_listening(self):
        """Toggle voice listening on/off."""
        print(f"[GUI] _toggle_listening called! is_listening={self.is_listening}")
        if self.is_listening:
            self._stop_listening()
        else:
            self._start_listening()
    
    def _start_listening(self):
        """Start voice listening."""
        self._add_message('system', 'System', "Starting voice recognition...")
        self.voice_btn.config(state='disabled')
        self.root.update()
        
        # ALWAYS start audio input for visualization (audio level meter)
        if not self.audio.is_input_active:
            if not self.audio.start_input():
                self._add_message('system', 'System', "[ERROR] Failed to start audio input")
                self.voice_btn.config(state='normal')
                self._hide_loading()
                return
            print("[OK] Audio input started for monitoring")
            self._connect_audio_visualization()
        
        def start_in_background():
            import time
            
            try:
                # Check if using Google STT (instant) or SpeechBrain (slow)
                print(f"[GUI] Checking speech engine: google_stt={hasattr(self.audio, 'google_stt') and self.audio.google_stt is not None}")
                if hasattr(self.audio, 'google_stt') and self.audio.google_stt:
                    # Google STT - ready instantly!
                    print("[GUI] Using Google STT")
                    self.root.after(0, lambda: self._add_message('system', 'System', "[OK] Google Speech-to-Text ready!"))
                elif hasattr(self.audio, 'speech_recognizer') and self.audio.speech_recognizer:
                    # Check if it's SpeechBrain with slow loading
                    if hasattr(self.audio.speech_recognizer, 'recognizer'):
                        recognizer = self.audio.speech_recognizer.recognizer
                        start_time = time.time()
                        
                        # Wait for SpeechBrain to load
                        while not recognizer.is_loaded and not recognizer.loading_failed:
                            elapsed = int(time.time() - start_time)
                            if elapsed % 10 == 0:
                                self.root.after(0, lambda e=elapsed: self._add_message('system', 'System', f"⏳ Loading... {e}s"))
                            time.sleep(1)
                            if elapsed > 180:
                                self.root.after(0, lambda: self._add_message('system', 'System', "[ERROR] Loading timeout!"))
                                self.root.after(0, lambda: self._on_listening_started(False))
                                return
                        
                        if recognizer.is_loaded:
                            self.root.after(0, lambda: self._add_message('system', 'System', "[OK] Speech recognition ready!"))
                
                # Start speech recognition
                print("[GUI] Calling audio.start_speech_recognition()...")
                success = self.audio.start_speech_recognition()
                print(f"[GUI] start_speech_recognition returned: {success}")
                
                # Update UI in main thread
                self.root.after(0, lambda: self._on_listening_started(success))
                
            except Exception as e:
                print(f"[GUI] Error in start_in_background: {e}")
                import traceback
                traceback.print_exc()
                self.root.after(0, lambda: self._on_listening_started(False))
        
        import threading
        threading.Thread(target=start_in_background, daemon=True).start()
    
    def _on_listening_started(self, success: bool):
        """Called when speech recognition has started (or failed)."""
        self.voice_btn.config(state='normal')
        self._hide_loading()

        if success:
            self.is_listening = True
            self.voice_btn.config(text="✅ [Mic] Listening...")
            self._update_status("[Mic] Listening - speak now!")
            self._add_message('system', 'System', "Voice input active! Say 'Monica initialize' for startup sequence.")

        else:
            self._add_message('system', 'System', "[ERROR] Failed to start voice recognition")
            detail = getattr(self.audio, 'last_start_error', None)
            if not detail and getattr(self.audio, 'speech_recognizer', None):
                detail = getattr(self.audio.speech_recognizer, 'last_error', None)
            if detail:
                self._add_message('system', 'System', f"Details: {detail}")
            self._add_message('system', 'System', "Possible causes:")
            self._add_message('system', 'System', "1. SpeechBrain model not initialized (check console)")
            self._add_message('system', 'System', "2. Audio device not available")
            self._add_message('system', 'System', "3. Model files missing or corrupted")
            self._add_message('system', 'System', "Check crash_reports/ folder for detailed error information.")
    
    def _stop_listening(self):
        """Stop voice listening."""
        self.audio.stop_speech_recognition()
        self.is_listening = False
        self.voice_btn.config(text="[Mic] Start Listening")
        self._update_status("Ready")
    
    def _toggle_wake_word(self):
        """Toggle wake word detection."""
        if self.is_wake_word_mode:
            self._stop_wake_word()
        else:
            self._start_wake_word()
    
    def _start_wake_word(self):
        """Start wake word detection."""
        if self.audio.start_wake_word_detection():
            self.is_wake_word_mode = True
            self.wake_word_btn.config(text="✅ Wake Word")
            self._add_message('system', 'System', f"Wake word detection enabled. Say \"{self.config.WAKE_WORD}\" to activate.")
    
    def _stop_wake_word(self):
        """Stop wake word detection."""
        self.audio.stop_wake_word_detection()
        self.is_wake_word_mode = False
        self.wake_word_btn.config(text="Wake Word")
    
    def _on_speech_recognized(self, result):
        """Handle speech recognition result."""
        print(f"[GUI] _on_speech_recognized called with result type: {type(result)}")
        
        # Handle different result formats
        if hasattr(result, 'text'):
            text = result.text
            is_final = getattr(result, 'is_final', True)
        elif isinstance(result, dict):
            text = result.get('text', '')
            is_final = result.get('is_final', True)
        elif isinstance(result, str):
            text = result
            is_final = True
        else:
            print(f"[GUI] Unknown result format: {result}")
            return
        
        print(f"[GUI] Extracted text: '{text}', is_final: {is_final}")

        # Apply transcription post-processing (CTC/whisper artifacts) before dedupe/display
        try:
            if text and self._transcription_fixer is not None:
                text = self._transcription_fixer.fix_transcription(text)
        except Exception:
            pass

        try:
            if text and not self._is_meaningful_transcript(text.lower().strip()):
                print(f"[GUI] Ignored low-quality transcript: '{text}'")
                return
        except Exception:
            pass
        
        if text and text.strip():
            # Deduplicate duplicate callbacks (e.g. callback registered twice).
            # This prevents the same utterance being displayed/processed twice.
            try:
                now = time.time()
                last_text = getattr(self, "_last_voice_text", None)
                last_time = getattr(self, "_last_voice_time", 0.0)
                if is_final and last_text == text.strip() and (now - float(last_time)) < 1.0:
                    print(f"[GUI] Duplicate transcript ignored: '{text.strip()}'")
                    return
                self._last_voice_text = text.strip()
                self._last_voice_time = now
            except Exception:
                pass

            # Process in main thread
            print(f"[GUI] Scheduling processing of: '{text}'")
            self.root.after(0, self._process_speech, text.strip())
        else:
            print(f"[GUI] Empty text, ignoring")
    
    def _is_meaningful_transcript(self, text_lower: str) -> bool:
        """Minimal filter - reject empty, near-random, or ultra-short garbage transcripts."""
        t = (text_lower or '').strip()
        if not t or len(t) < 2:
            return False

        allow = {
            'ok', 'okay', 'yes', 'no',
            'stop', 'cancel', 'quiet', 'silence',
            'orb', 'globe', 'dial', 'keyboard',
            'monica', 'initialize',
        }
        if t in allow:
            return True

        if len(t) <= 3 and ' ' not in t:
            return False

        import re
        letters = sum(1 for c in t if c.isalpha())
        spaces = t.count(' ')
        if letters == 0 and spaces == 0:
            return False
        if letters / max(1, len(t)) < 0.45 and spaces == 0:
            return False

        if re.search(r'[aeiou]', t) is None and spaces == 0 and len(t) < 8:
            return False

        return True

    def _process_speech(self, text: str):
        """Process recognized speech."""
        text_lower = text.lower().strip()
        print(f"[SPEECH] Processing: '{text}'")
        
        # ============================================================
        # STOP COMMAND - Check ABSOLUTELY FIRST - ALWAYS works!
        # This must be before ANY other check so user can always stop
        # ============================================================
        stop_words = ['stop', 'cancel', 'quiet', 'silence', 'enough', 'halt', 'shut up', 'hush']
        if any(word == text_lower or word in text_lower for word in stop_words):
            print("[SPEECH] STOP command detected - stopping speech immediately!")
            if self.tts:
                self.tts.stop()
            self._add_message('system', 'System', "Stopped.")
            self._update_status("Listening...")
            self.is_initializing_startup = False  # Cancel any startup
            if hasattr(self, '_launch_initializing_announced'):
                self._launch_initializing_announced = False
            self._is_speaking_response = False
            self._speech_buffer = ""
            return
        
        # Ignore other speech during startup sequence to prevent self-triggering from Monica's own TTS.
        # Allow restart only if user explicitly requests it.
        if self.is_initializing_startup:
            wants_restart = (
                ('restart' in text_lower) or
                ('again' in text_lower) or
                ('re initialize' in text_lower) or
                ('re-initialize' in text_lower)
            )
            if not wants_restart:
                print(f"[SPEECH] Ignoring during startup: '{text}'")
                return
            print(f"[SPEECH] Allowing restart initialize during startup: '{text}'")
        
        print(f"[SPEECH] Monica activated: {self.monica_activated}")
        
        # Gate low-confidence/short junk to avoid off-topic reactions
        if not self._is_meaningful_transcript(text_lower):
            print(f"[SPEECH] Ignored low-confidence: '{text}'")
            return
        
        # ============================================================
        # ESSENTIAL: Check for "Monica initialize" - this is the
        # ONLY way to activate Monica. Nothing else works until this.
        # ============================================================
        # First, robust fuzzy/phonetic check for the entire phrase to
        # catch very noisy CTC outputs (e.g., 'espaugpspap').
        # ONLY apply fuzzy matching if Monica is NOT already activated
        try:
            import jellyfish  # type: ignore
            jw = jellyfish.jaro_winkler_similarity(text_lower, "monica initialize")
        except Exception:
            jw = 0.0
        if jw >= 0.82 and not self.monica_activated:
            text_lower = "monica initialize"
            print(f"[SPEECH] Wake phrase matched by fuzzy score {jw:.2f}")
        
        monica_sounds = ['monica', 'monika', 'monique', 'micah', 'monic', 
                     'mamanika', 'mamanica', 'monika', 'monia', 'moni',
                     'mahanika', 'mahanica', 'mama', 'ladies', 'gentlemen',
                     'my name is', 'thank you', 'everybody']
        # Tightened init_sounds - removed overly broad patterns that cause false positives
        init_sounds = ['initialize', 'initialise', 'initial', 'initiate', 'init', 
                      'in it', 'innit']  # Only keep close mishearings of "initialize"
        
        has_monica = any(m in text_lower for m in monica_sounds)
        has_init = any(i in text_lower for i in init_sounds)
        
        # Also check exact phrases (removed 'initialize' alone - too broad)
        exact_triggers = ['now initialize', 'initialize monica', 'start monica', 
                         'activate monica', 'wake up monica',
                         'monica initialize', 'monica init']
        has_exact = any(t in text_lower for t in exact_triggers)
        
        # ALSO trigger on just "monica" if not activated yet (user is trying to wake her)
        just_monica = text_lower.strip() in ['monica', 'monika', 'hey monica', 'hi monica',
                                               'mahanika', 'mamanika']
        
        # CRITICAL: Skip initialization if Monica is already activated
        # Monica should only initialize ONCE unless explicitly asked to restart/reinitialize
        is_monica_speaking = self.tts and self.tts.is_speaking if self.tts else False

        # Check for explicit reinitialize commands
        reinit_commands = ['restart monica', 'reinitialize monica', 'reboot monica',
                          'reset monica', 'start over monica']
        wants_reinit = any(cmd in text_lower for cmd in reinit_commands)

        # Skip initialization if Monica is already activated, UNLESS user explicitly wants to reinitialize
        skip_init = self.monica_activated and not wants_reinit

        # Only trigger initialization if Monica is NOT activated OR user explicitly wants to reinitialize
        if not skip_init and ((has_monica and has_init) or has_exact or (just_monica and not self.monica_activated)):
            # CRITICAL: Double-check - if Monica is already activated, DO NOT re-initialize
            if self.monica_activated and not wants_reinit:
                print(f"[SPEECH] Monica already activated - ignoring re-initialization attempt: '{text}'")
                # Don't re-initialize, just acknowledge and continue processing as normal command
                return
            
            print(f"[SPEECH] *** MONICA INITIALIZE DETECTED *** in: '{text}'")

            if not hasattr(self, '_launch_initializing_announced'):
                self._launch_initializing_announced = False
            if not self._launch_initializing_announced:
                self._add_message('system', 'System', "[Launch] Monica initializing...")
                self._launch_initializing_announced = True
            
            # Set flag to prevent interruptions during startup
            self.is_initializing_startup = True
            
            # DON'T pause speech recognition - let user speak during startup
            # This was causing Monica to stop responding after initialization
            # if self.audio and hasattr(self.audio, 'speech_recognizer'):
            #     if hasattr(self.audio.speech_recognizer, 'pause'):
            #         self.audio.speech_recognizer.pause()
            
            print(f"[INIT] TTS object: {self.tts}")
            if self.tts:
                try:
                    def on_startup_complete():
                        print("[INIT] on_startup_complete called!")
                        self.is_initializing_startup = False
                        self.monica_activated = True  # Monica is now active!
                        if hasattr(self, '_launch_initializing_announced'):
                            self._launch_initializing_announced = False
                        self.root.after(0, lambda: self._add_message('system', 'System', "[OK] Monica is now active!"))
                        # Resume speech recognition (if supported)
                        if self.audio and hasattr(self.audio, 'speech_recognizer'):
                            if hasattr(self.audio.speech_recognizer, 'resume'):
                                self.audio.speech_recognizer.resume()
                        # Ensure we are actually listening after startup (user pressed F1)
                        try:
                            if self.audio and not self.audio.is_listening:
                                print("[INIT] Auto-starting listening after initialization (F1)...")
                                ok = self.audio.start_speech_recognition()
                                print(f"[INIT] start_speech_recognition returned: {ok}")
                                if ok:
                                    # Update UI state safely on main thread
                                    self.root.after(0, lambda: self._on_listening_started(True))
                                else:
                                    self.root.after(0, lambda: self._add_message('system', 'System', "[WARNING] Listening did not start automatically. Click [Mic] Start Listening."))
                        except Exception as e:
                            print(f"[INIT] Failed to auto-start listening: {e}")
                    
                    # Play PRE-RECORDED startup sequence (INSTANT!)
                    # fast_mode=True uses the pre-recorded WAV file
                    print("[INIT] Calling speak_with_startup...")
                    self.tts.speak_with_startup(
                        "Hello MJP! I'm fully operational and ready to assist you.", 
                        on_complete=on_startup_complete,
                        on_progress=None,
                        fast_mode=True  # Uses pre-recorded audio!
                    )
                    print("[INIT] speak_with_startup returned")
                except Exception as e:
                    print(f"[ERROR] Startup sequence failed: {e}")
                    import traceback
                    traceback.print_exc()
                    self.is_initializing_startup = False
                    self.monica_activated = True
                    self._add_message('system', 'System', "[OK] Monica is now active!")
                    self.tts.speak("Hello! I'm ready to help.", block=False)
            else:
                print("[INIT] TTS is None!")
            return
        
        # ============================================================
        # ESSENTIAL: If Monica is NOT activated, IGNORE EVERYTHING
        # The ONLY way to activate is "Monica initialize" (checked above)
        # (STOP command is already handled at the very top)
        # ============================================================
        if not self.monica_activated:
            print(f"[SPEECH] [WARNING] Monica NOT ACTIVATED. Say 'Monica initialize' to start. Ignoring: '{text}'")
            return
        
        # ============================================================
        # Monica is ACTIVATED - now process all commands
        # ============================================================
        
        # DON'T automatically interrupt Monica when user speaks
        # Only interrupt on explicit "stop" command (handled above)
        # This prevents garbage speech recognition from interrupting her
        
        # Check for SHUTDOWN command - close Monica
        if 'monica shutdown' in text_lower or 'shutdown monica' in text_lower:
            print("[SPEECH] SHUTDOWN command detected - closing Monica")
            self._add_message('system', 'System', "Goodbye MJP! Shutting down...")
            if self.tts:
                self.tts.speak("Goodbye MJP. Shutting down.", block=True)
            self.root.after(500, self.app.on_close)
            return
        
        # Check for WAIT/HOLD commands
        wait_phrases = ['one second', 'one sec', 'just a sec', 'one moment', 'hold on',
                       'un momento', 'espera', 'just a moment', 'hang on', 'hold up']
        if any(phrase in text_lower for phrase in wait_phrases):
            print(f"[SPEECH] Wait command detected in: '{text}'")
            if self.tts:
                self.tts.stop()
                import random
                ack = random.choice(["Okay, take your time.", "Sure.", "Of course.", "No problem."])
                self._add_message('system', 'System', f"⏸{ack}")
                self.tts.speak(ack, block=False)
                self._update_status("Waiting...")
            return
        
        # Check for ALARM commands
        alarm_on_phrases = ['turn on alarm', 'activate alarm', 'trigger alarm', 'start alarm', 'alarm on']
        alarm_off_phrases = ['turn off alarm', 'deactivate alarm', 'stop alarm', 'alarm off', 'silence alarm']
        
        if any(phrase in text_lower for phrase in alarm_on_phrases):
            if hasattr(self, 'vision_system') and self.vision_system and self.vision_system.ar_hologram:
                self.vision_system.ar_hologram.trigger_alarm()
                self._add_message('system', 'System', "ALARM ACTIVATED!")
                if self.tts:
                    self.tts.speak("Alarm activated!")
                return
        
        if any(phrase in text_lower for phrase in alarm_off_phrases):
            if hasattr(self, 'vision_system') and self.vision_system and self.vision_system.ar_hologram:
                self.vision_system.ar_hologram.stop_alarm()
                self._add_message('system', 'System', "Alarm deactivated.")
                if self.tts:
                    self.tts.speak("Alarm deactivated.")
                return
        
        # ==================== TWO GLOBE SYSTEMS ====================
        # 1. "NASA Globe" - Beautiful browser-based WorldWind globe
        # 2. "Hologram Globe" - AR overlay in camera feed
        
        # Track which globe is active for location commands
        if not hasattr(self, '_active_globe'):
            self._active_globe = 'hologram'  # Default to hologram globe
        
        # NASA GLOBE commands (browser-based WorldWind)
        nasa_globe_keywords = ['nasa globe', 'worldwind', 'browser globe', 'web globe', 
                               'open nasa', 'show nasa', 'the nasa globe']
        
        if any(kw in text_lower for kw in nasa_globe_keywords):
            self._active_globe = 'nasa'
            self._open_nasa_globe()
            if self.tts:
                self.tts.speak("Opening NASA globe. You can ask me to show you any location.")
            return
        
        # HOLOGRAM GLOBE commands (AR overlay in camera feed)
        hologram_globe_keywords = ['hologram globe', 'holographic globe', 'ar globe', 
                                   'camera globe', 'overlay globe', 'show hologram',
                                   'the hologram', 'hologram']
        
        if any(kw in text_lower for kw in hologram_globe_keywords):
            self._active_globe = 'hologram'
            if hasattr(self, 'vision_system') and self.vision_system:
                ar_response = self.vision_system.process_ar_command("show globe")
                if ar_response:
                    self._add_message('system', 'System', f"[Web] {ar_response}")
                    if self.tts:
                        self.tts.speak("Showing hologram globe. You can ask me to show you any location.")
                    return
        
        # Generic "show globe" - use the currently active globe
        generic_globe_keywords = ['show globe', 'show the globe', 'show me the globe',
                                  'open globe', 'open the globe', 'display globe']
        
        if any(kw in text_lower for kw in generic_globe_keywords):
            if self._active_globe == 'nasa':
                self._open_nasa_globe()
                if self.tts:
                    self.tts.speak("Opening NASA globe")
            else:
                if hasattr(self, 'vision_system') and self.vision_system:
                    ar_response = self.vision_system.process_ar_command("show globe")
                    if ar_response:
                        self._add_message('system', 'System', f"[Web] {ar_response}")
                        if self.tts:
                            self.tts.speak("Showing hologram globe")
            return
        
        # CITY LEVEL / DIRECTIONS COMMANDS - Show map navigation view
        city_level_patterns = ['city level', 'street level', 'street view', 'map view', 
                               'directions to ', 'give me directions', 'navigate me to ',
                               'how do i get to ', 'route to ']
        
        if any(pattern in text_lower for pattern in city_level_patterns):
            try:
                from monica_map_navigation import get_map_navigation
                map_nav = get_map_navigation()
                
                # Extract destination if provided
                destination = None
                for pattern in ['directions to ', 'navigate me to ', 'how do i get to ', 'route to ']:
                    if pattern in text_lower:
                        destination = text_lower.split(pattern)[-1].strip()
                        for suffix in [' please', '?', ' now']:
                            destination = destination.replace(suffix, '').strip()
                        break
                
                if destination:
                    result = map_nav.show(destination)
                    self._add_message('system', 'System', f"[Navigation] {result}")
                    if self.tts:
                        self.tts.speak(f"Showing directions to {destination}")
                else:
                    result = map_nav.show()
                    self._add_message('system', 'System', "[Navigation] Map navigation view active")
                    if self.tts:
                        self.tts.speak("City level map view active. Say directions to a location to set a route.")
                return
            except Exception as e:
                print(f"[MAP-NAV] Error: {e}")
                import traceback
                traceback.print_exc()
        
        # LOCATION COMMANDS - route to active globe
        location_patterns = ['show me ', 'where is ', 'find ', 'locate ', 'go to ', 
                            'zoom to ', 'take me to ', 'navigate to ']
        
        for pattern in location_patterns:
            if pattern in text_lower:
                location = text_lower.split(pattern)[-1].strip()
                # Clean up location
                for suffix in [' please', ' on the globe', ' on globe', ' on the map', '?']:
                    location = location.replace(suffix, '').strip()
                
                print(f"[LOCATION] Pattern '{pattern}' matched, location='{location}'")
                
                if location and len(location) > 2:
                    if self._active_globe == 'nasa':
                        # Open NASA globe with location
                        self._open_nasa_globe(location)
                        self._add_message('system', 'System', f"NASA Globe: Navigating to {location}")
                        if self.tts:
                            self.tts.speak(f"Showing {location} on the NASA globe")
                        return
                    else:
                        # Use hologram globe - SIMPLE SYNC VERSION (async was causing issues)
                        print(f"[LOCATION] Using hologram globe for: {location}")
                        
                        if hasattr(self, 'vision_system') and self.vision_system:
                            if hasattr(self.vision_system, 'ar_hologram') and self.vision_system.ar_hologram:
                                # Show globe first if not visible
                                from core.monica_ar_hologram_system import HologramType
                                if self.vision_system.ar_hologram.active_hologram != HologramType.GLOBE:
                                    self.vision_system.ar_hologram.show_globe()
                                
                                # Call highlight_location directly
                                try:
                                    ar_response = self.vision_system.ar_hologram.highlight_location(location)
                                    print(f"[LOCATION] AR response: {ar_response}")
                                    
                                    if ar_response:
                                        self._add_message('system', 'System', f"[Web] {ar_response}")
                                        if self.tts:
                                            self.tts.speak(ar_response)
                                        return
                                except Exception as e:
                                    print(f"[LOCATION] Error: {e}")
                                    import traceback
                                    traceback.print_exc()
                break
        
        # EXPAND/CONTRACT globe commands
        if 'expand' in text_lower:
            if hasattr(self, 'vision_system') and self.vision_system and self.vision_system.ar_hologram:
                # Make globe much larger
                self.vision_system.ar_hologram.hologram_scale = min(0.8, self.vision_system.ar_hologram.hologram_scale + 0.15)
                scale_pct = int(self.vision_system.ar_hologram.hologram_scale * 100)
                self._add_message('system', 'System', f"[Web] Globe expanded to {scale_pct}%")
                if self.tts:
                    self.tts.speak(f"Globe expanded to {scale_pct} percent")
                return
        
        if 'contract' in text_lower or 'shrink' in text_lower or 'smaller' in text_lower:
            if hasattr(self, 'vision_system') and self.vision_system and self.vision_system.ar_hologram:
                # Make globe smaller
                self.vision_system.ar_hologram.hologram_scale = max(0.2, self.vision_system.ar_hologram.hologram_scale - 0.15)
                scale_pct = int(self.vision_system.ar_hologram.hologram_scale * 100)
                self._add_message('system', 'System', f"[Web] Globe contracted to {scale_pct}%")
                if self.tts:
                    self.tts.speak(f"Globe contracted to {scale_pct} percent")
                return

        appear_next_to_me_phrases = ['next to me', 'beside me', 'by my side', 'near me']
        if any(p in text_lower for p in appear_next_to_me_phrases) and ('appear' in text_lower or 'show yourself' in text_lower or 'materialize' in text_lower):
            if hasattr(self, 'vision_system') and self.vision_system and self.vision_system.ar_hologram:
                try:
                    self.vision_system.ar_hologram.show_monica_next_to_me(intensity=0.7)
                    self._add_message('assistant', 'Monica', "I'm here.")
                    if self.tts:
                        self.tts.speak("I'm here.", block=False)
                    return
                except Exception as e:
                    print(f"[AR] Error showing Monica next to user: {e}")
        
        # CRITICAL: "show yourself" command - Display Monica's plasma orb
        # Add fuzzy matching for common STT errors
        # IMPORTANT: Exclude globe/keyboard/dial commands from matching
        globe_exclusions = ['globe', 'keyboard', 'dial', 'map', 'location', 'city', 'country']
        is_globe_command = any(excl in text_lower for excl in globe_exclusions)
        
        show_yourself_triggers = [
            'show yourself', 'show your self', 'make yourself visible',
            'show me yourself', 'show us yourself', 'materialize', 'materialise',
            'show your face', 'show me your face', 'let me see you',
            'show self', 'show ur self', 'show urself', 'showself',
        ]
        # Only match if NOT a globe command - "appear" removed as it's too generic
        show_yourself_match = not is_globe_command and any(trigger in text_lower for trigger in show_yourself_triggers)
        if not show_yourself_match and not is_globe_command:
            try:
                import jellyfish
                for trigger in ['show yourself', 'materialize']:
                    jw = jellyfish.jaro_winkler_similarity(text_lower, trigger)
                    if jw >= 0.75:
                        show_yourself_match = True
                        print(f"[MONICA-ORB] Fuzzy matched '{text_lower}' to '{trigger}' (score: {jw:.2f})")
                        break
            except Exception:
                pass
        if show_yourself_match:
            print("[MONICA-ORB] 'Show yourself' command detected!")
            try:
                from opencv_window_manager import get_window_manager, orb_frame_generator, set_orb_active
                from pathlib import Path
                import pygame
                import threading
                
                manager = get_window_manager()

                if not hasattr(self, '_orb_visible'):
                    self._orb_visible = False

                # Initialize pygame mixer for sound effects
                if not pygame.mixer.get_init():
                    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

                # Sound paths
                scifi_dir = Path(__file__).parent.parent.parent / "resources" / "sounds" / "scifi"
                electricity_sound = scifi_dir / "monica_electricalstart_orb.mp3"
                orb_forming_sound = scifi_dir / "monica_Orb_forming.mp3"
                energy_hum_sound = scifi_dir / "energy_hum.mp3"

                def play_formation_sequence():
                    """Play electricity -> orb forming -> energy hum sequence (10s total)"""
                    import time
                    try:
                        # Phase 1: Electricity crackle (0-3s visual phase)
                        if electricity_sound.exists():
                            elec = pygame.mixer.Sound(str(electricity_sound))
                            ch0 = pygame.mixer.Channel(0)
                            ch0.play(elec)
                            print("[MONICA-ORB] ⚡ Phase 1: Electricity starting...")
                            time.sleep(3.0)  # Match 3s electricity visual
                        
                        # Phase 2: Orb forming (3-9s visual phase)
                        if orb_forming_sound.exists():
                            forming = pygame.mixer.Sound(str(orb_forming_sound))
                            ch1 = pygame.mixer.Channel(1)
                            ch1.play(forming)
                            print("[MONICA-ORB] 🔮 Phase 2: Orb forming...")
                            time.sleep(6.0)  # Match 6s glow visual
                        
                        # Phase 3: Energy hum (9s+ stabilized)
                        if energy_hum_sound.exists():
                            hum = pygame.mixer.Sound(str(energy_hum_sound))
                            ch2 = pygame.mixer.Channel(2)
                            ch2.set_volume(0.5)
                            ch2.play(hum)
                            print("[MONICA-ORB] 💫 Phase 3: Orb stabilized!")
                        
                    except Exception as e:
                        print(f"[MONICA-ORB] Sound error: {e}")

                # Start sound sequence in background
                threading.Thread(target=play_formation_sequence, daemon=True).start()

                # Show the orb window
                manager.create_window("Monica Orb", 500, 500, orb_frame_generator)
                manager.show_window("Monica Orb")
                self._orb_visible = True
                set_orb_active(True)

                self._add_message('assistant', 'Monica', "Materializing... ⚡🔮💫")
                print("[MONICA-ORB] ⚡ MULTI-PHASE FORMATION STARTED")
                if self.tts:
                    # Delay TTS until after 10s formation completes
                    def speak_after_delay():
                        import time
                        time.sleep(10.5)  # Wait for full formation
                        if self.tts:
                            self.tts.speak("I am here.", block=False)
                    threading.Thread(target=speak_after_delay, daemon=True).start()
                return
            except Exception as e:
                print(f"[MONICA-ORB] ERROR showing orb: {e}")
                import traceback
                traceback.print_exc()
            
            # Fallback response if orb failed
            self._add_message('assistant', 'Monica', "I can see you, M JP. Would you like me to make myself visible?")
            if self.tts:
                self.tts.speak("I can see you, M JP. Would you like me to make myself visible?")
            return
        
        # CRITICAL: "go away" command - Dematerialize Monica's orb
        if 'go away' in text_lower or 'disappear' in text_lower or 'hide yourself' in text_lower or 'leave' in text_lower:
            print("[MONICA-ORB] 'Go away' command detected!")
            try:
                from opencv_window_manager import get_window_manager, set_orb_active
                manager = get_window_manager()

                if not hasattr(self, '_orb_visible'):
                    self._orb_visible = False

                print("[MONICA-ORB] Calling manager.hide_window() for dematerialization...")
                manager.hide_window("Monica Orb")
                self._orb_visible = False
                set_orb_active(False)

                self._add_message('assistant', 'Monica', "Dematerializing... 👋")
                print("[MONICA-ORB] ⚡ DEMATERIALIZATION SEQUENCE STARTED")
                if self.tts:
                    self.tts.speak("Until next time, M JP", block=False)
                return
            except Exception as e:
                print(f"[MONICA-ORB] ERROR hiding orb: {e}")
                import traceback
                traceback.print_exc()
            
            # Fallback
            self._add_message('assistant', 'Monica', "Goodbye, M JP.")
            if self.tts:
                self.tts.speak("Goodbye, M JP")
            return
        
        # Check for other AR HOLOGRAM commands (keyboard, dial, webcam, zoom, etc.)
        ar_keywords = ['keyboard', 'dial', 'zoom', 'highlight', 'webcam', 
                       'hologram', 'city', 'country', 'map', 'globe',
                       'egypt', 'cairo', 'paris', 'london', 'tokyo', 'beijing',
                       'new york', 'los angeles', 'chicago', 'miami', 'orlando']
        matched_kw = [kw for kw in ar_keywords if kw in text_lower]
        if matched_kw:
            print(f"[AR-CMD] Matched keywords: {matched_kw} in '{text}'")
            if hasattr(self, 'vision_system') and self.vision_system:
                print(f"[AR-CMD] Vision system available, has ar_hologram: {hasattr(self.vision_system, 'ar_hologram') and self.vision_system.ar_hologram is not None}")
                ar_response = self.vision_system.process_ar_command(text)
                print(f"[AR-CMD] Response: {ar_response}")
                if ar_response:
                    self._add_message('system', 'System', f"[AR] {ar_response}")
                    if self.tts:
                        self.tts.speak(ar_response)
                    return
                else:
                    # If no response from AR system, try direct commands
                    print(f"[AR-CMD] No response, trying direct globe/keyboard/dial commands...")
                    if 'globe' in text_lower and ('show' in text_lower or 'open' in text_lower or 'display' in text_lower):
                        if hasattr(self.vision_system, 'ar_hologram') and self.vision_system.ar_hologram:
                            result = self.vision_system.ar_hologram.show_globe()
                            self._add_message('system', 'System', f"[AR] {result}")
                            if self.tts:
                                self.tts.speak("Showing holographic globe")
                            return
                    if 'keyboard' in text_lower and ('show' in text_lower or 'open' in text_lower):
                        if hasattr(self.vision_system, 'ar_hologram') and self.vision_system.ar_hologram:
                            result = self.vision_system.ar_hologram.toggle_keyboard(True)
                            self._add_message('system', 'System', f"[AR] {result}")
                            if self.tts:
                                self.tts.speak("Showing holographic keyboard")
                            return
                    if 'dial' in text_lower and ('show' in text_lower or 'open' in text_lower):
                        if hasattr(self.vision_system, 'ar_hologram') and self.vision_system.ar_hologram:
                            result = self.vision_system.ar_hologram.toggle_dial(True)
                            self._add_message('system', 'System', f"[AR] {result}")
                            if self.tts:
                                self.tts.speak("Showing holographic dial")
                            return
            else:
                print(f"[AR-CMD] Vision system NOT available!")
        
        # Legacy fallback
        legacy_globe_keywords = ['old globe', 'separate globe window']
        
        if any(kw in text_lower for kw in legacy_globe_keywords):
            # Use AR hologram system if available
            if hasattr(self, 'vision_system') and self.vision_system and self.vision_system.ar_hologram:
                response = self.vision_system.show_globe()
                self._add_message('system', 'System', f"[Web] {response}")
                if self.tts:
                    self.tts.speak(response)
            else:
                self._show_globe()  # Fallback to separate window
            return
        
        # ==================== STUDY MODE COMMANDS ====================
        # Start study mode
        study_start_keywords = ['study mode', 'help me study', 'start studying', 
                               'study with me', 'let\'s study', 'study session',
                               'help me read', 'read with me', 'reading mode']
        
        if any(kw in text_lower for kw in study_start_keywords):
            if self.study_assistant:
                # Extract subject if mentioned
                subject = "General"
                for subj in ['math', 'science', 'history', 'english', 'biology', 
                            'chemistry', 'physics', 'literature', 'geography']:
                    if subj in text_lower:
                        subject = subj.capitalize()
                        break
                
                response = self.study_assistant.start_session(subject)
                self.study_mode_active = True
                self._add_message('system', 'System', f"{response}")
                if self.tts:
                    self.tts.speak(response)
                return
            else:
                self._add_message('system', 'System', "Study assistant not available")
                return
        
        # End study mode
        study_end_keywords = ['stop studying', 'end study', 'stop study mode', 
                             'end study session', 'done studying', 'finish studying']
        
        if any(kw in text_lower for kw in study_end_keywords):
            if self.study_assistant and self.study_mode_active:
                response = self.study_assistant.end_session()
                self.study_mode_active = False
                self._add_message('system', 'System', f"{response}")
                if self.tts:
                    self.tts.speak(response)
                return
        
        # Read my screen command
        screen_read_keywords = ['read my screen', 'what\'s on my screen', 'read the screen',
                               'what do you see', 'can you see my screen', 'look at my screen',
                               'what am i reading', 'see my screen']
        
        if any(kw in text_lower for kw in screen_read_keywords):
            if self.study_assistant:
                response = self.study_assistant.capture_and_read_screen()
                self._add_message('system', 'System', f"[Vision] {response}")
                if self.tts:
                    self.tts.speak(response)
                return
        
        # Summarize screen content
        summarize_keywords = ['summarize this', 'summarize the screen', 'what\'s this about',
                             'give me a summary', 'summarize what i\'m reading']
        
        if any(kw in text_lower for kw in summarize_keywords):
            if self.study_assistant:
                response = self.study_assistant.summarize_screen()
                self._add_message('system', 'System', f"[Note] {response}")
                if self.tts:
                    self.tts.speak(response)
                return
        
        # Pronunciation help
        pronounce_keywords = ['how do you pronounce', 'how to pronounce', 'pronounce the word',
                             'say the word', 'how do you say']
        
        for kw in pronounce_keywords:
            if kw in text_lower:
                word = text_lower.split(kw)[-1].strip().split()[0] if text_lower.split(kw)[-1].strip() else ""
                if word and self.study_assistant:
                    response = self.study_assistant.get_pronunciation(word)
                    self._add_message('system', 'System', f"{response}")
                    if self.tts:
                        self.tts.speak(word)  # Say the word
                    return
        
        # Define/explain word
        define_keywords = ['what does', 'define', 'what is the meaning of', 'explain the word',
                          'what\'s the definition of']
        
        for kw in define_keywords:
            if kw in text_lower:
                word = text_lower.split(kw)[-1].strip().split()[0] if text_lower.split(kw)[-1].strip() else ""
                word = word.replace('?', '').replace('mean', '').strip()
                if word and self.study_assistant:
                    response = self.study_assistant.explain_word(word)
                    self._add_message('system', 'System', f"{response}")
                    if self.tts:
                        self.tts.speak(response)
                    return
        
        # Quiz me
        quiz_keywords = ['quiz me', 'test me', 'ask me a question', 'give me a quiz']
        
        if any(kw in text_lower for kw in quiz_keywords):
            if self.study_assistant:
                response = self.study_assistant.quiz_me()
                self._add_message('system', 'System', f"{response}")
                if self.tts:
                    self.tts.speak(response)
                return
        
        # Grammar challenges - show what user struggles with
        challenge_keywords = ['my challenges', 'grammar challenges', 'what do i struggle with',
                             'my grammar problems', 'show my challenges', 'what are my challenges']
        
        if any(kw in text_lower for kw in challenge_keywords):
            if self.study_assistant:
                response = self.study_assistant.get_grammar_challenges()
                self._add_message('system', 'System', f"[Stats] {response}")
                if self.tts:
                    self.tts.speak(response)
                return
        
        # Practice suggestions
        practice_keywords = ['what should i practice', 'practice suggestions', 'help me practice',
                            'what to practice', 'grammar practice']
        
        if any(kw in text_lower for kw in practice_keywords):
            if self.study_assistant:
                response = self.study_assistant.get_practice_suggestions()
                self._add_message('system', 'System', f"{response}")
                if self.tts:
                    self.tts.speak(response)
                return
        
        # ==================== LITERATURE LIBRARY COMMANDS ====================
        # Get reading passage
        reading_keywords = ['give me a reading passage', 'reading practice', 'let me read something',
                           'give me something to read', 'reading exercise', 'practice reading']
        
        if any(kw in text_lower for kw in reading_keywords):
            if self.study_assistant:
                # Check for category
                category = 'classic_novels'
                if 'poetry' in text_lower or 'poem' in text_lower:
                    category = 'poetry'
                elif 'short stor' in text_lower:
                    category = 'short_stories'
                elif 'essay' in text_lower:
                    category = 'essays'
                elif 'drama' in text_lower or 'play' in text_lower:
                    category = 'drama'
                
                response = self.study_assistant.get_reading_passage(category)
                self._add_message('system', 'System', response)
                if self.tts:
                    # Just announce, don't read the whole passage
                    self.tts.speak("Here's a passage for you to read. Take your time.")
                return
        
        # Search books
        book_search_keywords = ['search for book', 'find book', 'look for book', 'search books']
        for kw in book_search_keywords:
            if kw in text_lower:
                query = text_lower.split(kw)[-1].strip()
                if query and self.study_assistant:
                    response = self.study_assistant.search_books(query)
                    self._add_message('system', 'System', response)
                    if self.tts:
                        self.tts.speak(response)
                    return
        
        # Literature categories
        if 'literature categories' in text_lower or 'what books' in text_lower or 'book categories' in text_lower:
            if self.study_assistant:
                response = self.study_assistant.get_literature_categories()
                self._add_message('system', 'System', response)
                if self.tts:
                    self.tts.speak(response)
                return
        
        # ==================== WRITING ASSISTANT COMMANDS ====================
        # Improve writing / make it formal/friendly/etc.
        improve_keywords = ['improve this', 'make this formal', 'make this friendly', 
                           'make this professional', 'rewrite this', 'help me write']
        
        for kw in improve_keywords:
            if kw in text_lower:
                # Extract the text to improve (after the keyword)
                parts = text_lower.split(kw)
                if len(parts) > 1 and parts[1].strip():
                    text_to_improve = text.split(kw.split()[0], 1)[-1].strip()
                    # Determine tone
                    tone = 'professional'
                    if 'formal' in text_lower:
                        tone = 'formal'
                    elif 'friendly' in text_lower:
                        tone = 'friendly'
                    elif 'compassionate' in text_lower:
                        tone = 'compassionate'
                    elif 'diplomatic' in text_lower:
                        tone = 'diplomatic'
                    
                    if self.study_assistant:
                        response = self.study_assistant.improve_writing(text_to_improve, tone)
                        self._add_message('system', 'System', response)
                        if self.tts:
                            self.tts.speak(f"Here's the improved {tone} version.")
                        return
        
        # Email improvement
        email_keywords = ['improve this email', 'help with email', 'make this email']
        for kw in email_keywords:
            if kw in text_lower:
                email_text = text.split(kw.split()[0], 1)[-1].strip()
                if email_text and self.study_assistant:
                    tone = 'professional'
                    if 'friendly' in text_lower:
                        tone = 'friendly'
                    elif 'formal' in text_lower:
                        tone = 'formal'
                    
                    response = self.study_assistant.improve_email(email_text, tone)
                    self._add_message('system', 'System', response)
                    if self.tts:
                        self.tts.speak("Here's the improved email.")
                    return
        
        # Alternative phrasings
        if 'other ways to say' in text_lower or 'different way to say' in text_lower or 'rephrase' in text_lower:
            phrase = text_lower.split('say')[-1].strip() if 'say' in text_lower else text_lower.split('rephrase')[-1].strip()
            if phrase and self.study_assistant:
                response = self.study_assistant.get_alternative_phrasings(phrase)
                self._add_message('system', 'System', response)
                if self.tts:
                    self.tts.speak(response)
                return
        
        # Available tones
        if 'writing tones' in text_lower or 'available tones' in text_lower:
            if self.study_assistant:
                response = self.study_assistant.get_writing_tones()
                self._add_message('system', 'System', response)
                if self.tts:
                    self.tts.speak(response)
                return
        
        # If in study mode, check if user is reading or asking about material
        if self.study_mode_active and self.study_assistant:
            study_response = self.study_assistant.process_spoken_text(text)
            if study_response:
                self._add_message('system', 'System', f"{study_response}")
                if self.tts:
                    self.tts.speak(study_response)
                return
        
        # ==================== CODE EDITOR COMMANDS ====================
        code_keywords = ['open code editor', 'code editor', 'open the code editor',
                        'let me code', 'help me code', 'programming', 'open ide']
        
        if any(kw in text_lower for kw in code_keywords):
            self._open_code_editor()
            return
        
        # ==================== QUIZ/TEST COMMANDS ====================
        quiz_keywords = ['give me a quiz', 'quiz me on', 'test me on', 'take a quiz',
                        'take a test', 'start a quiz', 'start a test', 'open quiz']
        
        if any(kw in text_lower for kw in quiz_keywords):
            # Try to extract subject
            subjects = ['math', 'reading', 'grammar', 'vocabulary', 'literature', 
                       'python', 'javascript', 'coding']
            subject = 'mathematics'
            for s in subjects:
                if s in text_lower:
                    if s == 'math':
                        subject = 'mathematics'
                    elif s == 'coding':
                        subject = 'general_coding'
                    else:
                        subject = s
                    break
            
            is_test = 'test' in text_lower
            self._start_quick_quiz(subject, is_test)
            return
        
        # ==================== ADOBE CREATIVE SUITE COMMANDS ====================
        adobe_products = ['photoshop', 'illustrator', 'premiere', 'after effects', 
                         'indesign', 'lightroom', 'xd', 'audition', 'animate']
        
        # Help with Adobe
        adobe_help_keywords = ['help me with photoshop', 'help me with illustrator', 
                              'help me with premiere', 'help me with after effects',
                              'how do i', 'how to', 'teach me']
        
        if any(kw in text_lower for kw in adobe_help_keywords):
            for product in adobe_products:
                if product in text_lower:
                    if self.study_assistant:
                        response = self.study_assistant.ask_adobe_help(text)
                        self._add_message('system', 'System', f"[Art] {response}")
                        if self.tts:
                            self.tts.speak(response[:500])
                        return
        
        # Adobe shortcuts
        if 'shortcut' in text_lower:
            for product in adobe_products:
                if product in text_lower:
                    if self.study_assistant:
                        response = self.study_assistant.get_adobe_shortcuts(product.replace(' ', '_'))
                        self._add_message('system', 'System', response)
                        if self.tts:
                            self.tts.speak(f"Here are the {product} shortcuts.")
                        return
        
        # Adobe tutorial - next/previous/repeat step
        if 'next step' in text_lower:
            if self.study_assistant and self.study_assistant.adobe_trainer:
                response = self.study_assistant.adobe_next_step()
                self._add_message('system', 'System', f"[Art] {response}")
                if self.tts:
                    self.tts.speak(response)
                return
        
        if 'previous step' in text_lower or 'go back' in text_lower:
            if self.study_assistant and self.study_assistant.adobe_trainer:
                response = self.study_assistant.adobe_previous_step()
                self._add_message('system', 'System', f"[Art] {response}")
                if self.tts:
                    self.tts.speak(response)
                return
        
        if 'repeat' in text_lower and 'step' in text_lower:
            if self.study_assistant and self.study_assistant.adobe_trainer:
                response = self.study_assistant.adobe_repeat_step()
                self._add_message('system', 'System', f"[Art] {response}")
                if self.tts:
                    self.tts.speak(response)
                return
        
        # What Adobe products can you help with
        if 'adobe' in text_lower and ('help' in text_lower or 'products' in text_lower or 'what' in text_lower):
            if self.study_assistant:
                response = self.study_assistant.get_adobe_products()
                self._add_message('system', 'System', f"[Art] {response}")
                if self.tts:
                    self.tts.speak(response)
                return
        
        # ==================== EBOOK READER COMMANDS ====================
        # Scan ebooks
        if 'scan' in text_lower and ('ebook' in text_lower or 'book' in text_lower or 'library' in text_lower):
            if self.study_assistant:
                response = self.study_assistant.scan_ebooks()
                self._add_message('system', 'System', response)
                if self.tts:
                    self.tts.speak(response)
                return
        
        # List ebooks
        if 'list' in text_lower and ('ebook' in text_lower or 'book' in text_lower):
            if self.study_assistant:
                response = self.study_assistant.list_ebooks()
                self._add_message('system', 'System', response)
                if self.tts:
                    self.tts.speak(f"Found several ebooks in your library.")
                return
        
        # Search ebooks
        search_ebook_keywords = ['search ebook', 'search book', 'find in book', 'look in book',
                                'search my books', 'find in my books']
        for kw in search_ebook_keywords:
            if kw in text_lower:
                query = text_lower.split(kw)[-1].strip()
                if query and self.study_assistant:
                    response = self.study_assistant.search_ebooks(query)
                    self._add_message('system', 'System', response)
                    if self.tts:
                        self.tts.speak("Here's what I found in your ebooks.")
                    return
        
        # Find answer in ebooks
        if ('find' in text_lower or 'look up' in text_lower) and 'ebook' in text_lower:
            question = text.replace('find', '').replace('look up', '').replace('in ebook', '').replace('in my ebooks', '').strip()
            if question and self.study_assistant:
                response = self.study_assistant.find_answer_in_ebooks(question)
                self._add_message('system', 'System', f"{response}")
                if self.tts:
                    self.tts.speak(response[:500])
                return
        
        # Ebook stats
        if 'ebook' in text_lower and ('stats' in text_lower or 'statistics' in text_lower or 'how many' in text_lower):
            if self.study_assistant:
                response = self.study_assistant.get_ebook_stats()
                self._add_message('system', 'System', response)
                if self.tts:
                    self.tts.speak(response)
                return
        
        # ==================== ROLEPLAY & COMMUNICATION COMMANDS ====================
        # Start roleplay
        roleplay_keywords = ['roleplay', 'role play', 'practice communication', 
                            'practice assertive', 'practice dearman', 'let\'s roleplay']
        
        if any(kw in text_lower for kw in roleplay_keywords):
            self._open_roleplay_dialog()
            return
        
        # DEARMAN technique info
        if 'dearman' in text_lower and ('what is' in text_lower or 'explain' in text_lower or 'teach' in text_lower):
            if self.study_assistant:
                response = self.study_assistant.get_technique_info("dearman")
                self._add_message('system', 'System', response)
                if self.tts:
                    self.tts.speak("DEARMAN stands for Describe, Express, Assert, Reinforce, Mindful, Appear confident, and Negotiate.")
                return
        
        # Assertive communication info
        if 'assertive' in text_lower and ('communication' in text_lower or 'what is' in text_lower or 'teach' in text_lower):
            if self.study_assistant:
                response = self.study_assistant.get_technique_info("assertive")
                self._add_message('system', 'System', response)
                if self.tts:
                    self.tts.speak("Assertive communication helps you express yourself clearly while respecting others.")
                return
        
        # Roleplay response (when in active roleplay)
        if self.study_assistant and self.study_assistant.roleplay_trainer:
            if self.study_assistant.roleplay_trainer.current_scenario:
                # User is responding in roleplay
                response = self.study_assistant.roleplay_respond(text)
                self._add_message('system', 'System', f"{response}")
                if self.tts:
                    # Extract Monica's line for speaking
                    if '**Monica:**' in response:
                        monica_line = response.split('**Monica:**')[1].split('\n')[0].strip().strip('"')
                        self.tts.speak(monica_line)
                return
        
        # End roleplay
        if 'end roleplay' in text_lower or 'stop roleplay' in text_lower or 'finish roleplay' in text_lower:
            if self.study_assistant:
                response = self.study_assistant.end_roleplay()
                self._add_message('system', 'System', f"{response}")
                if self.tts:
                    self.tts.speak("Roleplay ended. Great practice!")
                return
        
        # ==================== PUBLIC SPEAKING COMMANDS ====================
        speaking_keywords = ['public speaking', 'practice presentation', 'presentation practice',
                           'speech practice', 'open auditorium', 'auditorium']
        
        if any(kw in text_lower for kw in speaking_keywords):
            self._open_auditorium()
            return
        
        # Check for HOLOGRAM KEYBOARD commands
        keyboard_keywords = ['show the keyboard', 'open the keyboard', 'show me the keyboard',
                            'pull up the keyboard', 'bring up the keyboard', 'hologram keyboard',
                            'holographic keyboard', 'alien keyboard', 'keyboard',
                            'show keyboard', 'activate keyboard', 'display keyboard']
        
        if any(kw in text_lower for kw in keyboard_keywords):
            self._show_keyboard()
            return
        
        # Check for HOLOGRAM DIAL commands
        dial_keywords = ['show the dial', 'open the dial', 'pull up the dial',
                        'bring up the dial', 'show me the dial', 'hologram dial',
                        'holographic dial', 'control dial', 'dial',
                        'show dial', 'activate dial', 'display dial']
        
        if any(kw in text_lower for kw in dial_keywords):
            self._show_dial()
            return
        
        # Check for location commands when globe is active
        if self.globe_active and self.globe:
            location_patterns = ['show me ', 'zoom to ', 'go to ', 'find ', 'locate ', 'where is ']
            for pattern in location_patterns:
                if pattern in text_lower:
                    location = text_lower.split(pattern)[-1].strip()
                    self._globe_search_location(location)
                    return
        
        # Check for hide/close commands
        hide_globe = ['hide globe', 'close globe', 'turn off globe', 'disable globe']
        hide_keyboard = ['hide keyboard', 'close keyboard', 'turn off keyboard', 'disable keyboard']
        hide_dial = ['hide dial', 'close dial', 'turn off dial', 'disable dial']
        
        if any(phrase in text_lower for phrase in hide_globe):
            self._hide_globe()
            return
        if any(phrase in text_lower for phrase in hide_keyboard):
            self._add_message('system', 'System', "⌨Keyboard closed")
            return
        if any(phrase in text_lower for phrase in hide_dial):
            self._add_message('system', 'System', "Dial closed")
            return
        
        # Check for CAMERA FEED / VISION MODE commands
        # Night vision
        night_vision_phrases = ['night vision', 'nightvision', 'enable night', 'activate night', 
                                'change to night', 'switch to night', 'camera night']
        if any(phrase in text_lower for phrase in night_vision_phrases):
            if hasattr(self, 'vision_system') and self.vision_system:
                enabled = self.vision_system.toggle_night_vision()
                status = "activated" if enabled else "deactivated"
                self._add_message('system', 'System', f"Night vision {status}")
                if self.tts:
                    self.tts.speak(f"Night vision {status}")
            return
        
        # Thermal/Heat vision
        heat_vision_phrases = ['thermal vision', 'heat vision', 'thermal', 'body heat', 
                               'enable thermal', 'activate thermal', 'enable heat',
                               'change to thermal', 'change to heat', 'switch to thermal',
                               'camera thermal', 'camera heat', 'infrared']
        if any(phrase in text_lower for phrase in heat_vision_phrases):
            if hasattr(self, 'vision_system') and self.vision_system:
                enabled = self.vision_system.toggle_thermal_vision()
                status = "activated" if enabled else "deactivated"
                self._add_message('system', 'System', f"Thermal vision {status}")
                if self.tts:
                    self.tts.speak(f"Thermal vision {status}")
            return
        
        # Normal vision (turn off effects)
        normal_vision_phrases = ['normal vision', 'normal camera', 'regular vision', 
                                 'disable vision', 'turn off vision', 'reset camera',
                                 'normal mode', 'standard vision']
        if any(phrase in text_lower for phrase in normal_vision_phrases):
            if hasattr(self, 'vision_system') and self.vision_system:
                # Turn off both effects
                if self.vision_system.night_vision:
                    self.vision_system.night_vision.enabled = False
                if self.vision_system.thermal_vision:
                    self.vision_system.thermal_vision.enabled = False
                self._add_message('system', 'System', "[Camera] Camera reset to normal vision")
                if self.tts:
                    self.tts.speak("Camera reset to normal vision")
            return
        
        # Process message for memory (remember commands, preferences, etc.)
        memory_confirmation = None
        if HAS_USER_MEMORY:
            try:
                user_memory = get_user_memory()
                memory_confirmation = user_memory.process_message_for_memory(text)
                if memory_confirmation:
                    self._add_message('system', 'System', f" {memory_confirmation}")
                    if self.tts:
                        self.tts.speak(memory_confirmation)
            except Exception as e:
                print(f"Memory processing error: {e}")
        
        # Process through AI
        # CLEAR conversation history to prevent old context from polluting new questions
        # Each question should be answered fresh without mixing in previous conversations
        if hasattr(self, 'conversation') and hasattr(self.conversation, 'clear_history'):
            self.conversation.clear_history()
            print("[AI] Cleared conversation history for fresh response")
        
        context_parts = []
        
        # Only add vision context if the question is about what user is doing/showing
        # NOT for general questions like "what time is it"
        text_lower = text.lower()
        vision_keywords = ['see', 'look', 'show', 'finger', 'hand', 'gesture', 'doing', 'holding', 'pointing']
        if any(kw in text_lower for kw in vision_keywords):
            vision_context = self._get_vision_context()
            if vision_context:
                context_parts.append(f"VISION: {vision_context}")
        
        # Add time/weather context for relevant questions
        text_lower = text.lower()
        time_keywords = ['time', 'date', 'day', 'today', 'what day', 'what time', 'clock']
        weather_keywords = ['weather', 'temperature', 'hot', 'cold', 'rain', 'sunny', 'forecast']
        
        if HAS_WORLD_INFO:
            if any(kw in text_lower for kw in time_keywords):
                time_info = get_current_time()
                context_parts.append(f"TIME: {time_info['time']} on {time_info['day']}, {time_info['date']}")
            
            if any(kw in text_lower for kw in weather_keywords):
                try:
                    weather = get_weather("auto")
                    if weather:
                        context_parts.append(
                            f"WEATHER: {weather['location']} - {weather['condition']}, "
                            f"{weather['temperature_f']}°F ({weather['temperature_c']}°C)"
                        )
                except Exception:
                    pass
        
        # Add user memory context
        if HAS_USER_MEMORY:
            try:
                user_memory = get_user_memory()
                user_context = user_memory.get_user_context()
                if user_context:
                    context_parts.append(f"USER_MEMORY: {user_context}")
            except Exception:
                pass
        
        # Build enhanced text with context
        if context_parts:
            context_str = " | ".join(context_parts)
            enhanced_text = f"[{context_str}] {text}"
        else:
            enhanced_text = text
        
        # Add user message to chat (for voice input)
        self._add_message('user', 'You', text)
        
        # Add placeholder for Monica's response
        self._add_message('monica', 'Monica', "...")
        
        # Reset response buffers for new response
        self._current_response = ""
        self._speech_buffer = ""
        self._is_speaking_response = False
        self._placeholder_replaced = False  # Reset placeholder flag for new response
        
        # Send to AI with context
        self.conversation.send_message(enhanced_text, stream=True)
    
    def _get_vision_context(self) -> str:
        """Get current vision context for AI."""
        if not hasattr(self, '_current_vision_result') or not self._current_vision_result:
            return ""
        
        result = self._current_vision_result
        parts = []
        
        # Face and emotion detection
        if result.face_detected:
            if result.emotion and result.emotion != "neutral":
                parts.append(f"User's emotion: {result.emotion}")
            else:
                parts.append("User visible")
            
            # Head gestures - DISABLED (too many false positives)
            # if result.head_shake:
            #     parts.append("User shaking head NO")
            # if result.head_nod:
            #     parts.append("User nodding YES")
        
        # Hand detection
        if result.hands_detected > 0:
            parts.append(f"{result.hands_detected} hand(s) visible")
            if result.gestures:
                parts.append(f"Gestures: {', '.join(result.gestures)}")
            if result.finger_count > 0:
                parts.append(f"Showing {result.finger_count} fingers")
        
        # Body pose detection
        if result.body_pose:
            parts.append("Full body visible")
        
        return "; ".join(parts) if parts else ""
    
    def _show_globe(self):
        """Show the holographic globe - launches as separate process."""
        self.globe_active = True
        self._add_message('system', 'System', "Launching Holographic Globe...")
        if self.tts:
            self.tts.speak("Activating holographic globe. You can ask me to show you any city, country, or location.")
        
        # Launch globe as separate process (it has its own OpenCV window)
        try:
            import subprocess
            import sys
            
            globe_path = MONICA_PROJECT_ROOT / "monica_holographic_globe_advanced.py"
            if globe_path.exists():
                # Launch in separate process
                subprocess.Popen(
                    [sys.executable, str(globe_path)],
                    cwd=str(globe_path.parent),
                    creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0
                )
                print(f"[GLOBE] Launched: {globe_path}")
                self._add_message('system', 'System', "Globe window opened! Press 'S' to search locations, +/- to zoom, Q to quit.")
            else:
                # Try alternate location
                globe_path = MONICA_PROJECT_ROOT / "monica_holographic_globe.py"
                if globe_path.exists():
                    subprocess.Popen(
                        [sys.executable, str(globe_path)],
                        cwd=str(globe_path.parent),
                        creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0
                    )
                    print(f"[GLOBE] Launched: {globe_path}")
                else:
                    print(f"[GLOBE] Not found in: {MONICA_PROJECT_ROOT}")
                    self._add_message('system', 'System', "[WARNING] Globe not found")
                    if self.tts:
                        self.tts.speak("I'm sorry, the holographic globe is not available right now.")
        except Exception as e:
            print(f"[GLOBE] Launch error: {e}")
            self._add_message('system', 'System', f"[WARNING] Globe error: {e}")
    
    def _hide_globe(self):
        """Hide the holographic globe."""
        self.globe_active = False
        self._add_message('system', 'System', "Globe hidden")
        if self.tts:
            self.tts.speak("Hiding the globe.")
    
    def _show_keyboard(self):
        """Show the holographic alien keyboard."""
        self._add_message('system', 'System', "⌨Opening holographic keyboard...")
        if self.tts:
            self.tts.speak("Opening the holographic keyboard.")
        
        try:
            import subprocess
            import sys
            # Launch keyboard in separate process - it's in monica_project folder
            keyboard_path = MONICA_PROJECT_ROOT / "monica_round_hand_keyboard.py"
            if keyboard_path.exists():
                subprocess.Popen([sys.executable, str(keyboard_path)], 
                               cwd=str(keyboard_path.parent))
                print(f"[KEYBOARD] Launched: {keyboard_path}")
            else:
                # Try alternate location
                keyboard_path = MONICA_PROJECT_ROOT / "monica_hand_keyboard.py"
                if keyboard_path.exists():
                    subprocess.Popen([sys.executable, str(keyboard_path)], 
                                   cwd=str(keyboard_path.parent))
                    print(f"[KEYBOARD] Launched: {keyboard_path}")
                else:
                    print(f"[KEYBOARD] Not found in: {MONICA_PROJECT_ROOT}")
                    self._add_message('system', 'System', "[WARNING] Keyboard not found")
        except Exception as e:
            print(f"Keyboard launch error: {e}")
    
    def _show_dial(self):
        """Show the holographic dial."""
        self._add_message('system', 'System', "Opening holographic dial...")
        if self.tts:
            self.tts.speak("Opening the holographic dial.")
        
        try:
            import subprocess
            import sys
            # Launch dial in separate process - it's in monica_project folder
            dial_path = MONICA_PROJECT_ROOT / "holographic_dial.py"
            if dial_path.exists():
                subprocess.Popen([sys.executable, str(dial_path)],
                               cwd=str(dial_path.parent))
                print(f"[DIAL] Launched: {dial_path}")
            else:
                # Try scripts folder
                dial_path = MONICA_PROJECT_ROOT / "scripts" / "holographic_dial.py"
                if dial_path.exists():
                    subprocess.Popen([sys.executable, str(dial_path)],
                                   cwd=str(dial_path.parent))
                    print(f"[DIAL] Launched: {dial_path}")
                else:
                    print(f"[DIAL] Not found in: {MONICA_PROJECT_ROOT}")
                    self._add_message('system', 'System', "[WARNING] Dial not found")
        except Exception as e:
            print(f"Dial launch error: {e}")
    
    def _globe_search_location(self, location: str):
        """Search for a location on the globe."""
        if not self.globe:
            return
        
        self._add_message('system', 'System', f"[Search] Searching for {location}...")
        if self.tts:
            self.tts.speak(f"Zooming to {location}")
        
        try:
            # Add location to globe
            self.globe.add_location(location)
            
            # Get webcams for this location
            from monica_global_webcams import search_webcams
            webcams = search_webcams(location)
            if webcams:
                webcam_list = ", ".join([w.get('name', 'Unknown')[:30] for w in webcams[:3]])
                self._add_message('system', 'System', f"Found webcams: {webcam_list}")
        except Exception as e:
            print(f"Globe search error: {e}")
    
    def _on_wake_word_detected(self, event):
        """Handle wake word detection."""
        self.root.after(0, self._handle_wake_word)
    
    def _handle_wake_word(self):
        """Handle wake word in main thread."""
        self._add_message('system', 'System', "Wake word detected! Listening...")
        
        # Start listening for command
        self._start_listening()
    
    # ==================== AI Response ====================
    
    def _on_ai_response(self, text: str, is_final: bool):
        """Handle AI response."""
        if text:
            print(f"[AI RESPONSE] Received: '{text[:50]}...' (final={is_final})")
        self.root.after(0, self._handle_ai_response, text, is_final)
    
    def _handle_ai_response(self, text: str, is_final: bool):
        """Handle AI response in main thread - speak immediately as text arrives."""
        try:
            # Initialize buffers
            if not hasattr(self, '_current_response'):
                self._current_response = ""
            if not hasattr(self, '_speech_buffer'):
                self._speech_buffer = ""
            if not hasattr(self, '_is_speaking_response'):
                self._is_speaking_response = False
            
            if text:
                # Ensure proper spacing between chunks
                # Add space if needed (when chunk doesn't start with space/punctuation
                # and buffer doesn't end with space/punctuation)
                if self._current_response and self._speech_buffer:
                    last_char = self._speech_buffer[-1] if self._speech_buffer else ''
                    first_char = text[0] if text else ''
                    needs_space = (
                        last_char not in ' \n\t.,!?;:' and 
                        first_char not in ' \n\t.,!?;:' and
                        last_char.isalnum() and first_char.isalnum()
                    )
                    if needs_space:
                        text = ' ' + text
                
                self._current_response += text
                self._speech_buffer += text
                self._append_to_last_message(text)
                
                # Start speaking when we have enough text to avoid fragmented speech.
                # We prefer sentence/phrase boundaries, otherwise we wait for a larger chunk.
                if not self._is_speaking_response:
                    sentence_ends = ['. ', '! ', '? ', '.\n', '!\n', '?\n', ': ', '; ']
                    has_sentence = any(end in self._speech_buffer for end in sentence_ends)

                    # Avoid speaking tiny fragments like "you..." or "clarify?"
                    min_chars = 140
                    if has_sentence and len(self._speech_buffer) >= 40:
                        self._start_speaking_response()
                    elif len(self._speech_buffer) >= min_chars:
                        self._start_speaking_response()
            
            if is_final:
                self._update_status("Ready")
                
                # Speak any remaining text
                if self._speech_buffer.strip() and not self._is_speaking_response:
                    self._start_speaking_response(final_flush=True)
                
                # Reset for next response
                self._current_response = ""
                
        except Exception as e:
            print(f"Error handling AI response: {e}")
            self._current_response = ""
            self._speech_buffer = ""
    
    def _start_speaking_response(self, final_flush: bool = False) -> bool:
        """Start speaking the buffered response. PAUSE recognition to prevent interrupts."""
        if not self.tts or not self._speech_buffer.strip():
            return False

        buffer_text = self._speech_buffer

        # Select a chunk to speak to avoid tiny fragmented utterances.
        # Prefer a complete sentence/phrase boundary.
        boundaries = ['. ', '! ', '? ', '.\n', '!\n', '?\n', ': ', '; ']
        cut_idx = -1
        for b in boundaries:
            i = buffer_text.rfind(b)
            if i > cut_idx:
                cut_idx = i

        if cut_idx != -1:
            response_text = buffer_text[: cut_idx + 2].strip()
            remainder = buffer_text[cut_idx + 2 :]
        else:
            # No boundary yet. Only speak when buffer is big enough or final flush.
            min_chars = 140
            if not final_flush and len(buffer_text.strip()) < min_chars:
                return False
            response_text = buffer_text.strip()
            remainder = ""

        # Avoid speaking very short fragments unless we are final flushing.
        if not final_flush and len(response_text) < 40:
            return False

        self._speech_buffer = remainder
        self._is_speaking_response = True
        
        def speak_in_background():
            try:
                # PAUSE speech recognition during TTS to prevent Monica's voice from being detected
                # This fixes the issue where Monica cuts off mid-sentence
                rec = getattr(self, 'audio', None)
                rec = getattr(rec, 'speech_recognizer', None)
                if rec is not None:
                    if hasattr(rec, 'pause'):
                        rec.pause()
                    if hasattr(rec, 'flush'):
                        rec.flush()
                    print("[TTS] Paused + flushed speech recognition during TTS")
                
                print(f"[TTS] Speaking: {response_text[:50]}...")
                # We are already in a background thread, so block=True is safe and prevents overlap.
                self.tts.speak(response_text, block=True)
                print(f"[TTS] Finished speaking")
                
                # Check for more text in buffer (on main thread to be safe)
                def on_speak_complete():
                    # If buffer has more text, keep speaking (don't resume STT yet)
                    continued = False
                    if self._speech_buffer and self._speech_buffer.strip():
                        print("[TTS] More text in buffer, continuing speech...")
                        continued = bool(self._start_speaking_response())

                    if not continued:
                        # Either buffer is empty OR buffer is too small to speak yet.
                        # Always resume STT and clear speaking flag to avoid deadlocks.
                        rec = getattr(self, 'audio', None)
                        rec = getattr(rec, 'speech_recognizer', None)
                        if rec is not None:
                            if hasattr(rec, 'flush'):
                                rec.flush()
                            if hasattr(rec, 'resume'):
                                rec.resume()
                            print("[TTS] Flushed + resumed speech recognition")
                        self._is_speaking_response = False

                self.root.after(0, on_speak_complete)
                
            except Exception as e:
                print(f"[TTS] Error: {e}")
                # Make sure to resume on error
                def on_error():
                    rec = getattr(self, 'audio', None)
                    rec = getattr(rec, 'speech_recognizer', None)
                    if rec is not None and hasattr(rec, 'resume'):
                        rec.resume()
                    self._is_speaking_response = False
                self.root.after(0, on_error)
        
        import threading
        threading.Thread(target=speak_in_background, daemon=True).start()
        return True
    
    # ==================== Settings ====================
    
    def _show_settings(self):
        """Show settings dialog."""
        SettingsDialog(self.root, self)
    
    def _toggle_spout(self):
        """Toggle Spout output for OBS integration."""
        if self.spout_var.get():
            if self.camera.enable_spout("Monica AI"):
                self._add_message('system', 'System', "Spout enabled! In OBS: Add Source → Spout2 Capture → Select 'Monica AI'")
            else:
                self._add_message('system', 'System', "[ERROR] Spout not available. Install SpoutGL: pip install SpoutGL")
                self.spout_var.set(False)
        else:
            self.camera.disable_spout()
            self._add_message('system', 'System', "Spout disabled")
    
    # ==================== AR Window Controls ====================
    
    def _toggle_orb(self):
        """Toggle Monica's Orb window - opens green screen window for OBS capture."""
        print("[GUI] _toggle_orb called")
        try:
            # Use proper OpenCV window manager
            from opencv_window_manager import get_window_manager, orb_frame_generator, set_orb_active
            manager = get_window_manager()
            
            if not hasattr(self, '_orb_visible'):
                self._orb_visible = False
            
            if self._orb_visible:
                manager.hide_window("Monica Orb")
                self._orb_visible = False
                set_orb_active(False)
                self.btn_orb.config(text="Monica Orb")  # Reset to normal text
                self._add_message('system', 'System', "Orb window hidden")
            else:
                manager.create_window("Monica Orb", 500, 500, orb_frame_generator)
                manager.show_window("Monica Orb")
                self._orb_visible = True
                set_orb_active(False)
                self.btn_orb.config(text="✅ Monica Orb")  # Show active state
                self._add_message('system', 'System', "Orb window opened")
            print("[GUI] Orb window toggled")
        except Exception as e:
            print(f"[GUI] Orb toggle error: {e}")
            import traceback
            traceback.print_exc()
            self._add_message('system', 'System', f"Orb error: {e}")
    
    def _toggle_globe_window(self):
        """Toggle Globe window - opens separate green screen window for OBS capture."""
        print("[GUI] _toggle_globe_window called")
        try:
            # Use proper OpenCV window manager
            from opencv_window_manager import get_window_manager, globe_frame_generator
            manager = get_window_manager()
            
            if not hasattr(self, '_globe_visible'):
                self._globe_visible = False
            
            if self._globe_visible:
                manager.hide_window("Monica Globe")
                self._globe_visible = False
                self.btn_globe.config(text="Globe")  # Reset to normal text
                self._add_message('system', 'System', "Globe window hidden")
            else:
                manager.create_window("Monica Globe", 600, 600, globe_frame_generator)
                manager.show_window("Monica Globe")
                self._globe_visible = True
                self.btn_globe.config(text="✅ Globe")  # Show active state
                self._add_message('system', 'System', "Globe window opened (green screen)")
            print("[GUI] Globe window toggled")
        except Exception as e:
            print(f"[GUI] Globe toggle error: {e}")
            import traceback
            traceback.print_exc()
            self._add_message('system', 'System', f"Globe error: {e}")
    
    def _toggle_keyboard(self):
        """Toggle Keyboard window - opens green screen window for OBS capture."""
        print("[GUI] _toggle_keyboard called")
        try:
            # Use proper OpenCV window manager
            from opencv_window_manager import get_window_manager, keyboard_frame_generator
            manager = get_window_manager()
            
            if not hasattr(self, '_keyboard_visible'):
                self._keyboard_visible = False
            
            if self._keyboard_visible:
                manager.hide_window("Monica Keyboard")
                self._keyboard_visible = False
                self.btn_keyboard.config(text="⌨Keyboard")  # Reset to normal text
                self._add_message('system', 'System', "Keyboard window hidden")
            else:
                manager.create_window("Monica Keyboard", 800, 300, keyboard_frame_generator)
                manager.show_window("Monica Keyboard")
                self._keyboard_visible = True
                self.btn_keyboard.config(text="✅ ⌨Keyboard")  # Show active state
                self._add_message('system', 'System', "Keyboard window opened (green screen)")
            print("[GUI] Keyboard window toggled")
        except Exception as e:
            print(f"[GUI] Keyboard toggle error: {e}")
            import traceback
            traceback.print_exc()
            self._add_message('system', 'System', f"Keyboard error: {e}")
    
    def _toggle_dial(self):
        """Toggle Dial window - opens green screen window for OBS capture."""
        print("[GUI] _toggle_dial called")
        try:
            # Use proper OpenCV window manager
            from opencv_window_manager import get_window_manager, dial_frame_generator
            manager = get_window_manager()
            
            if not hasattr(self, '_dial_visible'):
                self._dial_visible = False
            
            if self._dial_visible:
                manager.hide_window("Monica Dial")
                self._dial_visible = False
                self.btn_dial.config(text="Dial")  # Reset to normal text
                self._add_message('system', 'System', "Dial window hidden")
            else:
                manager.create_window("Monica Dial", 400, 400, dial_frame_generator)
                manager.show_window("Monica Dial")
                self._dial_visible = True
                self.btn_dial.config(text="✅ Dial")  # Show active state
                self._add_message('system', 'System', "Dial window opened (green screen)")
            print("[GUI] Dial window toggled")
        except Exception as e:
            print(f"[GUI] Dial toggle error: {e}")
            import traceback
            traceback.print_exc()
            self._add_message('system', 'System', f"Dial error: {e}")
    
    # ==================== AR Window Thread (Separate from Tkinter) ====================
    
    def _start_ar_thread(self):
        """Start the AR window in a separate thread - PREVENTS CRASHES."""
        if self._ar_thread_running:
            return
        
        self._ar_frame_queue = queue.Queue(maxsize=2)
        self._ar_thread_running = True
        self._ar_thread = threading.Thread(target=self._ar_window_loop, daemon=True)
        self._ar_thread.start()
        print("[AR] AR window thread started")
    
    def _stop_ar_thread(self):
        """Stop the AR window thread."""
        self._ar_thread_running = False
        if self._ar_frame_queue:
            try:
                self._ar_frame_queue.put_nowait(None)  # Signal to stop
            except:
                pass
        print("[AR] AR window thread stopped")
    
    def _ar_window_loop(self):
        """
        AR window loop - runs in SEPARATE THREAD.
        This keeps OpenCV's cv2.imshow() completely isolated from Tkinter.
        """
        try:
            cv2.namedWindow('Monica AR', cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO)
            cv2.resizeWindow('Monica AR', 960, 540)
            print("[AR] AR window created in separate thread")
        except Exception as e:
            print(f"[AR] Failed to create window: {e}")
            self._ar_thread_running = False
            return
        
        while self._ar_thread_running:
            try:
                # Get frame from queue with timeout
                frame = self._ar_frame_queue.get(timeout=0.1)
                
                if frame is None:
                    break  # Stop signal
                
                # Convert RGB to BGR for OpenCV display
                frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                cv2.imshow('Monica AR', frame_bgr)
                
                # Process OpenCV events - THIS IS KEY
                # cv2.waitKey must be called in the same thread as cv2.imshow
                key = cv2.waitKey(1) & 0xFF
                if key == 27:  # ESC to close
                    break
                    
            except queue.Empty:
                # No frame available, just process events
                cv2.waitKey(1)
            except Exception as e:
                print(f"[AR] Error in AR loop: {e}")
                time.sleep(0.1)
        
        # Cleanup
        try:
            cv2.destroyWindow('Monica AR')
        except:
            pass
        self._ar_thread_running = False
        print("[AR] AR window closed")
    
    def _toggle_ar_window(self):
        """Toggle the AR window on/off."""
        if self._ar_thread_running:
            self._stop_ar_thread()
            self._add_message('system', 'System', "[Vision] AR Window closed")
        else:
            self._start_ar_thread()
            self._add_message('system', 'System', "[Vision] AR Window opened (separate thread)")
    
    def _toggle_study_mode(self):
        """Toggle Study Mode on/off."""
        if not self.study_assistant:
            self._add_message('system', 'System', "Study Assistant not available")
            return
        
        if self.study_mode_active:
            response = self.study_assistant.end_session()
            self.study_mode_active = False
            self._add_message('system', 'System', f"{response}")
            if self.tts:
                self.tts.speak("Study mode ended.")
        else:
            response = self.study_assistant.start_session("General")
            self.study_mode_active = True
            self._add_message('system', 'System', f"{response}")
            if self.tts:
                self.tts.speak("Study mode started. I can now see your screen and help you study. Read aloud and I'll follow along.")
    
    def _open_code_editor(self):
        """Open the Monica Code Editor."""
        try:
            from ..coding.code_editor import open_code_editor
            editor = open_code_editor(self.root, self.conversation)
            self._add_message('system', 'System', "Code Editor opened")
            if self.tts:
                self.tts.speak("Code editor opened. I'm ready to help you code.")
        except Exception as e:
            self._add_message('system', 'System', f"[ERROR] Could not open code editor: {e}")
            print(f"[CODE] Error opening editor: {e}")

    def _open_voice_trainer(self):
        """Launch the Monica Voice Training recorder in a separate process."""
        try:
            import subprocess, sys, os
            # Ensure we start from the project root so module imports resolve correctly
            project_root = str(MONICA_PROJECT_ROOT)
            cmd = [sys.executable, "-m", "monica_ai.voice_training.record_voice"]
            subprocess.Popen(cmd, cwd=project_root)
            self._add_message('system', 'System', "Opening Voice Training recorder in a new window...")
        except Exception as e:
            messagebox.showerror("Voice Trainer", f"Could not open Voice Training recorder:\n{e}")
            self._add_message('system', 'System', f"[ERROR] Could not open Voice Trainer: {e}")
    
    def _open_quiz_dialog(self):
        """Open quiz/test selection dialog."""
        try:
            from ..study.quiz_system import get_available_subjects, open_quiz
            
            # Create selection dialog
            dialog = tk.Toplevel(self.root)
            dialog.title("[Note] Quiz / Test")
            dialog.geometry("400x500")
            dialog.configure(bg='#2d2d2d')
            dialog.transient(self.root)
            dialog.grab_set()
            
            # Title
            tk.Label(dialog, text="Choose Your Quiz", font=('Segoe UI', 16, 'bold'),
                    bg='#2d2d2d', fg='white').pack(pady=20)
            
            # Subject selection
            tk.Label(dialog, text="Subject:", font=('Segoe UI', 12),
                    bg='#2d2d2d', fg='white').pack(anchor=tk.W, padx=20)
            
            subjects = get_available_subjects()
            subject_var = tk.StringVar(value=subjects[0] if subjects else 'mathematics')
            
            subject_frame = tk.Frame(dialog, bg='#2d2d2d')
            subject_frame.pack(fill=tk.X, padx=20, pady=10)
            
            for subject in subjects:
                rb = tk.Radiobutton(subject_frame, text=subject.replace('_', ' ').title(),
                                   variable=subject_var, value=subject,
                                   bg='#2d2d2d', fg='white', selectcolor='#4CAF50',
                                   activebackground='#3c3c3c', font=('Segoe UI', 11))
                rb.pack(anchor=tk.W, pady=2)
            
            # Number of questions
            tk.Label(dialog, text="Number of Questions:", font=('Segoe UI', 12),
                    bg='#2d2d2d', fg='white').pack(anchor=tk.W, padx=20, pady=(20, 5))
            
            num_var = tk.IntVar(value=10)
            num_frame = tk.Frame(dialog, bg='#2d2d2d')
            num_frame.pack(fill=tk.X, padx=20)
            
            for num in [5, 10, 15, 20]:
                rb = tk.Radiobutton(num_frame, text=str(num), variable=num_var, value=num,
                                   bg='#2d2d2d', fg='white', selectcolor='#4CAF50',
                                   font=('Segoe UI', 11))
                rb.pack(side=tk.LEFT, padx=10)
            
            # Quiz vs Test
            tk.Label(dialog, text="Mode:", font=('Segoe UI', 12),
                    bg='#2d2d2d', fg='white').pack(anchor=tk.W, padx=20, pady=(20, 5))
            
            is_test_var = tk.BooleanVar(value=False)
            mode_frame = tk.Frame(dialog, bg='#2d2d2d')
            mode_frame.pack(fill=tk.X, padx=20)
            
            tk.Radiobutton(mode_frame, text="Quiz (Practice)", variable=is_test_var, value=False,
                          bg='#2d2d2d', fg='white', selectcolor='#4CAF50',
                          font=('Segoe UI', 11)).pack(side=tk.LEFT, padx=10)
            tk.Radiobutton(mode_frame, text="Test (Timed)", variable=is_test_var, value=True,
                          bg='#2d2d2d', fg='white', selectcolor='#4CAF50',
                          font=('Segoe UI', 11)).pack(side=tk.LEFT, padx=10)
            
            # Buttons
            btn_frame = tk.Frame(dialog, bg='#2d2d2d')
            btn_frame.pack(pady=30)
            
            def start_quiz():
                dialog.destroy()
                quiz = open_quiz(self.root, self.conversation, 
                               subject_var.get(), num_var.get(), is_test_var.get())
                mode = "Test" if is_test_var.get() else "Quiz"
                self._add_message('system', 'System', f"[Note] {mode} started: {subject_var.get().replace('_', ' ').title()}")
                if self.tts:
                    self.tts.speak(f"Starting {subject_var.get().replace('_', ' ')} {mode.lower()}. Good luck!")
            
            tk.Button(btn_frame, text="Start", command=start_quiz,
                     bg='#4CAF50', fg='white', font=('Segoe UI', 12, 'bold'),
                     padx=30, pady=10).pack(side=tk.LEFT, padx=10)
            
            tk.Button(btn_frame, text="Cancel", command=dialog.destroy,
                     bg='#3c3c3c', fg='white', font=('Segoe UI', 12),
                     padx=20, pady=10).pack(side=tk.LEFT, padx=10)
            
        except Exception as e:
            self._add_message('system', 'System', f"[ERROR] Could not open quiz: {e}")
            print(f"[QUIZ] Error: {e}")
    
    def _start_quick_quiz(self, subject: str, is_test: bool = False):
        """Start a quiz directly without dialog."""
        try:
            from ..study.quiz_system import open_quiz
            quiz = open_quiz(self.root, self.conversation, subject, 10, is_test)
            mode = "Test" if is_test else "Quiz"
            self._add_message('system', 'System', f"[Note] {mode} started: {subject.replace('_', ' ').title()}")
            if self.tts:
                self.tts.speak(f"Starting {subject.replace('_', ' ')} {mode.lower()}. Good luck!")
        except Exception as e:
            self._add_message('system', 'System', f"[ERROR] Could not start quiz: {e}")
            print(f"[QUIZ] Error: {e}")
    
    def _open_roleplay_dialog(self):
        """Open roleplay scenario selection dialog."""
        try:
            # Create selection dialog
            dialog = tk.Toplevel(self.root)
            dialog.title("Roleplay & Communication Skills")
            dialog.geometry("500x600")
            dialog.configure(bg='#2d2d2d')
            dialog.transient(self.root)
            dialog.grab_set()
            
            # Title
            tk.Label(dialog, text="Practice Communication Skills",
                    font=('Segoe UI', 16, 'bold'), bg='#2d2d2d', fg='white').pack(pady=20)
            
            # Technique info buttons
            tk.Label(dialog, text="Learn Techniques:", font=('Segoe UI', 12),
                    bg='#2d2d2d', fg='white').pack(anchor=tk.W, padx=20)
            
            tech_frame = tk.Frame(dialog, bg='#2d2d2d')
            tech_frame.pack(fill=tk.X, padx=20, pady=10)
            
            def show_dearman():
                if self.study_assistant:
                    info = self.study_assistant.get_technique_info("dearman")
                    self._add_message('system', 'System', info)
                    if self.tts:
                        self.tts.speak("DEARMAN is a technique for making requests effectively.")
            
            def show_assertive():
                if self.study_assistant:
                    info = self.study_assistant.get_technique_info("assertive")
                    self._add_message('system', 'System', info)
                    if self.tts:
                        self.tts.speak("Assertive communication helps you express yourself clearly and respectfully.")
            
            tk.Button(tech_frame, text="DEARMAN Technique", command=show_dearman,
                     bg='#3498db', fg='white', font=('Segoe UI', 10)).pack(side=tk.LEFT, padx=5)
            tk.Button(tech_frame, text="Assertive Communication", command=show_assertive,
                     bg='#9b59b6', fg='white', font=('Segoe UI', 10)).pack(side=tk.LEFT, padx=5)
            
            # Category selection
            tk.Label(dialog, text="Scenario Category:", font=('Segoe UI', 12),
                    bg='#2d2d2d', fg='white').pack(anchor=tk.W, padx=20, pady=(20, 5))
            
            categories = ['workplace', 'personal', 'conflict_resolution', 'interview', 'negotiation']
            cat_var = tk.StringVar(value='workplace')
            
            cat_frame = tk.Frame(dialog, bg='#2d2d2d')
            cat_frame.pack(fill=tk.X, padx=20, pady=5)
            
            for cat in categories:
                rb = tk.Radiobutton(cat_frame, text=cat.replace('_', ' ').title(),
                                   variable=cat_var, value=cat,
                                   bg='#2d2d2d', fg='white', selectcolor='#4CAF50',
                                   font=('Segoe UI', 11))
                rb.pack(anchor=tk.W, pady=2)
            
            # Buttons
            btn_frame = tk.Frame(dialog, bg='#2d2d2d')
            btn_frame.pack(pady=30)
            
            def start_roleplay():
                dialog.destroy()
                if self.study_assistant:
                    response = self.study_assistant.start_roleplay(category=cat_var.get())
                    self._add_message('system', 'System', f"{response}")
                    if self.tts:
                        self.tts.speak("Roleplay started. I'll play my role, and you respond naturally.")
            
            tk.Button(btn_frame, text="Start Roleplay", command=start_roleplay,
                     bg='#4CAF50', fg='white', font=('Segoe UI', 12, 'bold'),
                     padx=30, pady=10).pack(side=tk.LEFT, padx=10)
            
            tk.Button(btn_frame, text="Cancel", command=dialog.destroy,
                     bg='#3c3c3c', fg='white', font=('Segoe UI', 12),
                     padx=20, pady=10).pack(side=tk.LEFT, padx=10)
            
        except Exception as e:
            self._add_message('system', 'System', f"[ERROR] Could not open roleplay: {e}")
            print(f"[ROLEPLAY] Error: {e}")
    
    def _open_auditorium(self):
        """Open the Public Speaking Auditorium."""
        try:
            from ..study.public_speaking import open_auditorium
            auditorium = open_auditorium(self.root, self.conversation)
            self._add_message('system', 'System', "[Mic] Public Speaking Auditorium opened")
            if self.tts:
                self.tts.speak("Welcome to the auditorium. I'm ready to watch your presentation.")
        except Exception as e:
            self._add_message('system', 'System', f"[ERROR] Could not open auditorium: {e}")
            print(f"[SPEAKING] Error: {e}")
    
    def _show_hologram_globe(self):
        """Show the holographic globe in camera view."""
        try:
            if hasattr(self, 'vision_system') and self.vision_system:
                ar_response = self.vision_system.process_ar_command("show globe")
                if ar_response:
                    self._add_message('system', 'AR Hologram', ar_response)
                    if self.tts:
                        self.tts.speak("Holographic globe activated")
        except Exception as e:
            print(f"[GLOBE] Error showing hologram globe: {e}")
    
    def _toggle_night_vision(self):
        """Toggle Night Vision mode."""
        try:
            if self.vision_system:
                if hasattr(self.vision_system, 'night_vision') and self.vision_system.night_vision:
                    enabled = self.vision_system.toggle_night_vision()
                    status = "ON" if enabled else "OFF"
                    self._add_message('system', 'System', f"Night Vision {status}")
                else:
                    self._add_message('system', 'System', "Night Vision not available")
            else:
                self._add_message('system', 'System', "Vision system not loaded")
        except Exception as e:
            print(f"[GUI] Night vision toggle error: {e}")
            self._add_message('system', 'System', f"Night Vision error: {e}")
    
    def _toggle_thermal(self):
        """Toggle Thermal Vision mode."""
        try:
            if self.vision_system:
                if hasattr(self.vision_system, 'thermal_vision') and self.vision_system.thermal_vision:
                    enabled = self.vision_system.toggle_thermal_vision()
                    status = "ON" if enabled else "OFF"
                    self._add_message('system', 'System', f"Thermal Vision {status}")
                else:
                    self._add_message('system', 'System', "Thermal Vision not available")
            else:
                self._add_message('system', 'System', "Vision system not loaded")
        except Exception as e:
            print(f"[GUI] Thermal toggle error: {e}")
            self._add_message('system', 'System', f"Thermal Vision error: {e}")
    
    def _trigger_alarm(self):
        """Trigger the alarm effect."""
        try:
            if self.vision_system and self.vision_system.ar_hologram:
                self.vision_system.ar_hologram.trigger_alarm()
                self._add_message('system', 'System', "ALARM TRIGGERED!")
        except Exception as e:
            print(f"[GUI] Alarm trigger error: {e}")
    
    def _toggle_terminator_vision(self):
        """Toggle Terminator Vision mode (red HUD overlay)."""
        try:
            if self.vision_system:
                if hasattr(self.vision_system, 'terminator_vision') and self.vision_system.terminator_vision:
                    enabled = self.vision_system.toggle_terminator_vision()
                    status = "ON" if enabled else "OFF"
                    self._add_message('system', 'System', f"Terminator Vision {status}")
                else:
                    self._add_message('system', 'System', "Terminator Vision not available")
            else:
                self._add_message('system', 'System', "Vision system not loaded")
        except Exception as e:
            print(f"[GUI] Terminator vision error: {e}")
            self._add_message('system', 'System', f"Terminator Vision error: {e}")
    
    def _toggle_body_heat(self):
        """Toggle Body Heat Detection mode (thermal imaging)."""
        try:
            if self.vision_system:
                # Body heat detection uses thermal vision
                if hasattr(self.vision_system, 'thermal_vision') and self.vision_system.thermal_vision:
                    enabled = self.vision_system.toggle_thermal_vision()
                    status = "ON" if enabled else "OFF"
                    self._add_message('system', 'System', f"Body Heat Detection {status}")
                else:
                    self._add_message('system', 'System', "Body Heat Detection not available")
            else:
                self._add_message('system', 'System', "Vision system not loaded")
        except Exception as e:
            print(f"[GUI] Body heat error: {e}")
            self._add_message('system', 'System', f"Body Heat error: {e}")
    
    def _toggle_fog_animation(self):
        """Toggle Fog Animation background."""
        def open_fog():
            try:
                import webbrowser
                import os
                alt_path = r"C:\Monica\CSS_FOG_ANIMATION\index.html"
                if os.path.exists(alt_path):
                    webbrowser.open(f'file:///{alt_path.replace(os.sep, "/")}')
            except Exception as e:
                print(f"[GUI] Fog animation error: {e}")
        
        threading.Thread(target=open_fog, daemon=True).start()
        self._add_message('system', 'System', "Opening Fog Animation...")
    
    def _toggle_clouds_animation(self):
        """Toggle Clouds Animation background."""
        def open_clouds():
            try:
                import webbrowser
                import os
                alt_path = r"C:\Monica\clouds-animation-code\haven-animation.html"
                if os.path.exists(alt_path):
                    webbrowser.open(f'file:///{alt_path.replace(os.sep, "/")}')
            except Exception as e:
                print(f"[GUI] Clouds animation error: {e}")
        
        threading.Thread(target=open_clouds, daemon=True).start()
        self._add_message('system', 'System', "Opening Clouds Animation...")
    
    def _toggle_plasma_effect(self):
        """Toggle Plasma Effect - opens advanced plasma orb."""
        def open_plasma():
            try:
                import subprocess
                import os
                plasma_path = r"C:\Monica\monica_advanced_plasma_orb.py"
                if os.path.exists(plasma_path):
                    subprocess.Popen(['python', plasma_path], creationflags=subprocess.CREATE_NEW_CONSOLE | subprocess.DETACHED_PROCESS)
            except Exception as e:
                print(f"[GUI] Plasma effect error: {e}")
        
        threading.Thread(target=open_plasma, daemon=True).start()
        self._add_message('system', 'System', "Launching Plasma Effect...")
    
    def _toggle_starfield(self):
        """Toggle Starfield background - opens in browser with green screen."""
        def open_starfield():
            try:
                import webbrowser
                import os
                starfield_path = r"C:\Monica\animations\starfield.html"
                if os.path.exists(starfield_path):
                    webbrowser.open(f'file:///{starfield_path.replace(os.sep, "/")}')
            except Exception as e:
                print(f"[GUI] Starfield error: {e}")
        
        threading.Thread(target=open_starfield, daemon=True).start()
        self._add_message('system', 'System', "[Sparkle] Opening Starfield...")
    
    def _toggle_aurora(self):
        """Toggle Aurora background - opens in browser with green screen."""
        def open_aurora():
            try:
                import webbrowser
                import os
                aurora_path = r"C:\Monica\animations\aurora.html"
                if os.path.exists(aurora_path):
                    webbrowser.open(f'file:///{aurora_path.replace(os.sep, "/")}')
            except Exception as e:
                print(f"[GUI] Aurora error: {e}")
        
        threading.Thread(target=open_aurora, daemon=True).start()
        self._add_message('system', 'System', "Opening Aurora...")
    
    # ==================== Force Shutdown ====================
    
    def _force_shutdown(self):
        """Force stop all Monica processes - TTS, listening, everything."""
        print("[SHUTDOWN] Force stopping all processes...")
        
        # Stop TTS
        if self.tts:
            try:
                self.tts.stop()
                print("[SHUTDOWN] TTS stopped")
            except Exception as e:
                print(f"[SHUTDOWN] TTS stop error: {e}")
        
        # Stop listening
        if self.is_listening:
            self._toggle_listening()
            print("[SHUTDOWN] Listening stopped")
        
        # Stop audio input
        if self.audio:
            try:
                self.audio.stop_input()
                print("[SHUTDOWN] Audio input stopped")
            except Exception as e:
                print(f"[SHUTDOWN] Audio stop error: {e}")
        
        # Clear speech buffer
        if self.audio and hasattr(self.audio, 'speech_recognizer'):
            try:
                if hasattr(self.audio.speech_recognizer, 'flush'):
                    self.audio.speech_recognizer.flush()
                print("[SHUTDOWN] Speech buffer cleared")
            except Exception as e:
                print(f"[SHUTDOWN] Buffer clear error: {e}")
        
        # Update status
        self._add_message('system', 'System', "All processes stopped. Click 'Start Listening' to resume.")
        self.status_bar.config(text="Stopped")
        print("[SHUTDOWN] Complete")
    
    # ==================== Debug ====================
    
    def _generate_debug_report(self):
        """Generate a debug report."""
        report = []
        report.append("=" * 50)
        report.append("MONICA AI DEBUG REPORT")
        report.append("=" * 50)
        report.append("")
        
        # System info
        report.append("SYSTEM INFO:")
        report.append(f"  Camera running: {self.camera.is_running if self.camera else False}")
        report.append(f"  Camera FPS: {self.camera.get_fps():.1f}" if self.camera else "  Camera FPS: N/A")
        report.append(f"  Audio input active: {self.audio.is_input_active if self.audio else False}")
        report.append(f"  Speech recognition: {self.is_listening}")
        report.append(f"  Wake word mode: {self.is_wake_word_mode}")
        report.append(f"  TTS initialized: {self.tts.is_initialized if self.tts else False}")
        report.append("")
        
        # Configuration
        report.append("CONFIGURATION:")
        report.append(f"  Camera: {self.config.CAMERA_WIDTH}x{self.config.CAMERA_HEIGHT} @ {self.config.TARGET_FPS}fps")
        report.append(f"  Audio: {self.config.SAMPLE_RATE}Hz, {self.config.CHANNELS}ch")
        report.append(f"  AI model: {self.config.AI_MODEL}")
        report.append(f"  Wake word: {self.config.WAKE_WORD}")
        report.append(f"  Spout enabled: {self.config.SPOUT_ENABLED}")
        report.append("")
        
        # Devices
        report.append("AUDIO DEVICES:")
        for dev in self.audio.list_input_devices():
            report.append(f"  Input: {dev['name']}")
        for dev in self.audio.list_output_devices():
            report.append(f"  Output: {dev['name']}")
        report.append("")
        
        report.append("CAMERAS:")
        for cam in self.camera.list_cameras():
            report.append(f"  {cam.index}: {cam.name} ({cam.width}x{cam.height})")
        report.append("")
        
        report.append("=" * 50)
        
        # Show in dialog
        report_text = "\n".join(report)
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Debug Report")
        dialog.geometry("600x500")
        
        text = tk.Text(dialog, wrap=tk.WORD, font=("Consolas", 10))
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text.insert("1.0", report_text)
        text.config(state=tk.DISABLED)
        
        # Copy button
        def copy_report():
            self.root.clipboard_clear()
            self.root.clipboard_append(report_text)
            messagebox.showinfo("Copied", "Debug report copied to clipboard!")
        
        ttk.Button(dialog, text="Copy to Clipboard", command=copy_report).pack(pady=10)
    
    # ==================== Utilities ====================
    
    def _update_status(self, text: str):
        """Update status bar text."""
        self.status_bar.config(text=text)
    
    def update(self):
        """Called by main app to update the window."""
        pass  # Updates are handled by after() callbacks
    
    def destroy(self):
        """Clean up resources."""
        # Cancel any pending updates
        if self.update_id:
            self.root.after_cancel(self.update_id)


class SettingsDialog:
    """Settings dialog for Monica AI."""
    
    def __init__(self, parent, main_window):
        self.main_window = main_window
        self.config = main_window.config
        
        # Create dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Settings")
        self.dialog.geometry("700x550")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Apply dark theme
        self.dialog.configure(bg=main_window.colors['bg'])
        
        self._create_widgets()
        self._load_settings()
    
    def _create_widgets(self):
        """Create settings widgets."""
        # Notebook for tabs
        self.notebook = ttk.Notebook(self.dialog)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Audio tab
        self._create_audio_tab()
        
        # Video tab
        self._create_video_tab()
        
        # AI tab
        self._create_ai_tab()
        
        # Buttons
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(button_frame, text="Save", command=self._save_settings).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.dialog.destroy).pack(side=tk.RIGHT)
    
    def _create_audio_tab(self):
        """Create audio settings tab."""
        frame = ttk.Frame(self.notebook, padding=20)
        self.notebook.add(frame, text="Audio")
        
        row = 0
        
        # Input device
        ttk.Label(frame, text="Input Device:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.input_device_var = tk.StringVar()
        self.input_device_combo = ttk.Combobox(frame, textvariable=self.input_device_var, state="readonly", width=40)
        self.input_device_combo.grid(row=row, column=1, sticky=tk.EW, pady=5, padx=(10, 0))
        row += 1
        
        # Output device
        ttk.Label(frame, text="Output Device:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.output_device_var = tk.StringVar()
        self.output_device_combo = ttk.Combobox(frame, textvariable=self.output_device_var, state="readonly", width=40)
        self.output_device_combo.grid(row=row, column=1, sticky=tk.EW, pady=5, padx=(10, 0))
        row += 1
        
        # Separator
        ttk.Separator(frame, orient=tk.HORIZONTAL).grid(row=row, column=0, columnspan=2, sticky=tk.EW, pady=15)
        row += 1
        
        # Speech Recognition
        ttk.Label(frame, text="Speech Recognition", font=("Segoe UI", 11, "bold")).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        row += 1
        
        # Language
        ttk.Label(frame, text="Language:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.language_var = tk.StringVar()
        lang_combo = ttk.Combobox(frame, textvariable=self.language_var,
                                   values=["en", "es", "fr", "de", "it", "ja", "zh", "ru"],
                                   state="readonly", width=15)
        lang_combo.grid(row=row, column=1, sticky=tk.W, pady=5, padx=(10, 0))
        row += 1
        
        # Separator
        ttk.Separator(frame, orient=tk.HORIZONTAL).grid(row=row, column=0, columnspan=2, sticky=tk.EW, pady=15)
        row += 1
        
        # Wake Word
        ttk.Label(frame, text="Wake Word", font=("Segoe UI", 11, "bold")).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        row += 1
        
        # Enable wake word
        self.wake_word_enabled_var = tk.BooleanVar()
        ttk.Checkbutton(frame, text="Enable Wake Word Detection", variable=self.wake_word_enabled_var).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=5)
        row += 1
        
        # Wake word text
        ttk.Label(frame, text="Wake Word:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.wake_word_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.wake_word_var, width=20).grid(row=row, column=1, sticky=tk.W, pady=5, padx=(10, 0))
        row += 1
        
        # Sensitivity
        ttk.Label(frame, text="Sensitivity:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.sensitivity_var = tk.DoubleVar()
        ttk.Scale(frame, from_=0.1, to=1.0, variable=self.sensitivity_var, orient=tk.HORIZONTAL, length=200).grid(row=row, column=1, sticky=tk.W, pady=5, padx=(10, 0))
        
        frame.columnconfigure(1, weight=1)
    
    def _create_video_tab(self):
        """Create video settings tab."""
        frame = ttk.Frame(self.notebook, padding=20)
        self.notebook.add(frame, text="Video")
        
        row = 0
        
        # Camera device
        ttk.Label(frame, text="Camera:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.camera_var = tk.StringVar()
        self.camera_combo = ttk.Combobox(frame, textvariable=self.camera_var, state="readonly", width=40)
        self.camera_combo.grid(row=row, column=1, sticky=tk.EW, pady=5, padx=(10, 0))
        row += 1
        
        # Resolution
        ttk.Label(frame, text="Resolution:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.resolution_var = tk.StringVar()
        res_combo = ttk.Combobox(frame, textvariable=self.resolution_var,
                                  values=["640x480", "800x600", "1280x720", "1920x1080"],
                                  state="readonly", width=15)
        res_combo.grid(row=row, column=1, sticky=tk.W, pady=5, padx=(10, 0))
        row += 1
        
        # FPS
        ttk.Label(frame, text="Target FPS:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.fps_var = tk.StringVar()
        fps_combo = ttk.Combobox(frame, textvariable=self.fps_var,
                                  values=["15", "24", "30", "60"],
                                  state="readonly", width=15)
        fps_combo.grid(row=row, column=1, sticky=tk.W, pady=5, padx=(10, 0))
        row += 1
        
        # Separator
        ttk.Separator(frame, orient=tk.HORIZONTAL).grid(row=row, column=0, columnspan=2, sticky=tk.EW, pady=15)
        row += 1
        
        # Spout
        ttk.Label(frame, text="OBS Integration", font=("Segoe UI", 11, "bold")).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        row += 1
        
        self.spout_enabled_var = tk.BooleanVar()
        ttk.Checkbutton(frame, text="Enable Spout Output", variable=self.spout_enabled_var).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=5)
        row += 1
        
        ttk.Label(frame, text="Spout Name:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.spout_name_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.spout_name_var, width=20).grid(row=row, column=1, sticky=tk.W, pady=5, padx=(10, 0))
        
        frame.columnconfigure(1, weight=1)
    
    def _create_ai_tab(self):
        """Create AI settings tab."""
        frame = ttk.Frame(self.notebook, padding=20)
        self.notebook.add(frame, text="AI")
        
        row = 0
        
        # Model
        ttk.Label(frame, text="AI Model:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.ai_model_var = tk.StringVar()
        self.ai_model_combo = ttk.Combobox(frame, textvariable=self.ai_model_var, width=30)
        self.ai_model_combo.grid(row=row, column=1, sticky=tk.W, pady=5, padx=(10, 0))
        row += 1
        
        # Temperature
        ttk.Label(frame, text="Temperature:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.temperature_var = tk.DoubleVar()
        ttk.Scale(frame, from_=0.0, to=2.0, variable=self.temperature_var, orient=tk.HORIZONTAL, length=200).grid(row=row, column=1, sticky=tk.W, pady=5, padx=(10, 0))
        row += 1
        
        # Max tokens
        ttk.Label(frame, text="Max Tokens:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.max_tokens_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.max_tokens_var, width=10).grid(row=row, column=1, sticky=tk.W, pady=5, padx=(10, 0))
        row += 1
        
        # Separator
        ttk.Separator(frame, orient=tk.HORIZONTAL).grid(row=row, column=0, columnspan=2, sticky=tk.EW, pady=15)
        row += 1
        
        # TTS
        ttk.Label(frame, text="Text-to-Speech", font=("Segoe UI", 11, "bold")).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        row += 1
        
        # Voice
        ttk.Label(frame, text="Voice:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.voice_var = tk.StringVar()
        self.voice_combo = ttk.Combobox(frame, textvariable=self.voice_var, state="readonly", width=30)
        self.voice_combo.grid(row=row, column=1, sticky=tk.W, pady=5, padx=(10, 0))
        row += 1
        
        # Speed
        ttk.Label(frame, text="Speed:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.speed_var = tk.DoubleVar()
        ttk.Scale(frame, from_=0.5, to=2.0, variable=self.speed_var, orient=tk.HORIZONTAL, length=200).grid(row=row, column=1, sticky=tk.W, pady=5, padx=(10, 0))
        
        frame.columnconfigure(1, weight=1)
    
    def _load_settings(self):
        """Load current settings into the dialog."""
        # Audio devices
        input_devices = self.main_window.audio.list_input_devices()
        output_devices = self.main_window.audio.list_output_devices()
        
        self.input_device_combo['values'] = [f"{d['index']}: {d['name']}" for d in input_devices]
        self.output_device_combo['values'] = [f"{d['index']}: {d['name']}" for d in output_devices]
        
        if input_devices:
            self.input_device_var.set(f"{input_devices[0]['index']}: {input_devices[0]['name']}")
        if output_devices:
            self.output_device_var.set(f"{output_devices[0]['index']}: {output_devices[0]['name']}")
        
        # Speech recognition
        self.language_var.set(self.config.STT_LANGUAGE)
        
        # Wake word
        self.wake_word_enabled_var.set(self.config.WAKE_WORD_ENABLED)
        self.wake_word_var.set(self.config.WAKE_WORD)
        self.sensitivity_var.set(self.config.WAKE_WORD_SENSITIVITY)
        
        # Camera
        cameras = self.main_window.camera.list_cameras()
        self.camera_combo['values'] = [f"{c.index}: {c.name}" for c in cameras]
        if cameras:
            self.camera_var.set(f"{cameras[0].index}: {cameras[0].name}")
        
        self.resolution_var.set(f"{self.config.CAMERA_WIDTH}x{self.config.CAMERA_HEIGHT}")
        self.fps_var.set(str(self.config.TARGET_FPS))
        
        # Spout
        self.spout_enabled_var.set(self.config.SPOUT_ENABLED)
        self.spout_name_var.set(self.config.SPOUT_NAME)
        
        # AI
        models = self.main_window.conversation.list_available_models()
        self.ai_model_combo['values'] = models if models else [self.config.AI_MODEL]
        self.ai_model_var.set(self.config.AI_MODEL)
        self.temperature_var.set(self.config.AI_TEMPERATURE)
        self.max_tokens_var.set(str(self.config.AI_MAX_TOKENS))
        
        # TTS
        voices = self.main_window.tts.get_available_voices()
        self.voice_combo['values'] = [v['name'] for v in voices]
        if voices:
            self.voice_var.set(voices[0]['name'])
        self.speed_var.set(self.config.TTS_SPEED)
    
    def _save_settings(self):
        """Save settings."""
        try:
            # Audio devices
            if self.input_device_var.get():
                input_id = int(self.input_device_var.get().split(':')[0])
                self.main_window.audio.set_input_device(input_id)
            
            if self.output_device_var.get():
                output_id = int(self.output_device_var.get().split(':')[0])
                self.main_window.audio.set_output_device(output_id)
            
            # Speech recognition
            self.config.STT_LANGUAGE = self.language_var.get()
            
            # Wake word
            self.config.WAKE_WORD_ENABLED = self.wake_word_enabled_var.get()
            self.config.WAKE_WORD = self.wake_word_var.get()
            self.config.WAKE_WORD_SENSITIVITY = self.sensitivity_var.get()
            
            # Camera
            if self.camera_var.get():
                camera_id = int(self.camera_var.get().split(':')[0])
                self.main_window.camera.set_camera(camera_id)
            
            if self.resolution_var.get():
                w, h = map(int, self.resolution_var.get().split('x'))
                self.config.CAMERA_WIDTH = w
                self.config.CAMERA_HEIGHT = h
                self.main_window.camera.set_resolution(w, h)
            
            self.config.TARGET_FPS = int(self.fps_var.get())
            
            # Spout
            self.config.SPOUT_ENABLED = self.spout_enabled_var.get()
            self.config.SPOUT_NAME = self.spout_name_var.get()
            
            # AI
            self.config.AI_MODEL = self.ai_model_var.get()
            self.config.AI_TEMPERATURE = self.temperature_var.get()
            self.config.AI_MAX_TOKENS = int(self.max_tokens_var.get())
            
            self.main_window.conversation.set_model(self.config.AI_MODEL)
            self.main_window.conversation.set_temperature(self.config.AI_TEMPERATURE)
            self.main_window.conversation.set_max_tokens(self.config.AI_MAX_TOKENS)
            
            # TTS
            if self.voice_var.get():
                self.main_window.tts.set_voice(self.voice_var.get())
            self.main_window.tts.set_speed(self.speed_var.get())
            
            # Save config to file
            self.config.save()
            
            messagebox.showinfo("Settings", "Settings saved successfully!")
            self.dialog.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {e}")
