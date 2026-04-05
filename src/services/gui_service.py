"""
GUI Service for Monica AI.
Provides the main application window with video feed, controls, and chat.
Uses tkinter for the GUI framework.
"""

import threading
import time
import logging
import sys
import os
import queue
from pathlib import Path
from typing import Optional, Any

logger = logging.getLogger("Monica.GUI")

# Import tkinter
try:
    import tkinter as tk
    from tkinter import ttk, scrolledtext
    HAS_TK = True
except ImportError:
    HAS_TK = False
    logger.error("tkinter not available")

# Import PIL for image display in tkinter
try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    logger.warning("Pillow not available - video feed will be limited")

# OpenCV for frame processing
try:
    import cv2
    import numpy as np
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False


class MonicaGUI:
    """
    Main GUI for Monica AI.
    
    Features:
    - Live video feed with face detection, biometrics, hand tracking, globe overlay
    - Chat panel for conversation
    - Service status indicators
    - Controls for vision features
    """

    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
        
        # State
        self.is_running = False
        self.root: Optional[tk.Tk] = None
        self.video_label = None
        self.chat_display = None
        self.chat_input = None
        self.status_labels = {}
        self.mic_combo = None
        self.mic_devices = []
        
        # Thread-safe chat queue (background threads put here, main thread drains)
        import queue as _queue
        self._chat_queue = _queue.Queue()
        
        # Video feed update rate — 15fps is smooth enough, halves PIL/PhotoImage overhead
        self.video_update_ms = 67  # ~15fps
        self._last_frame_id = None  # Track frame changes to skip redundant PhotoImage creation
        
        # Photo reference (must keep reference to prevent GC)
        self._photo = None
        
        # Monica initialization state
        self._monica_initialized = False
        
        # STT mode: 'off', 'hands_free', 'push_to_talk'
        # Default to hands_free so voice works immediately
        self._stt_mode = 'hands_free'
        self._ptt_active = False  # Push-to-talk button held
        
        # Mic level bar
        self._mic_level_canvas = None
        self._mic_level = 0.0
        
        logger.info("MonicaGUI created")

    def run(self):
        """Run the GUI main loop (blocks until window is closed)."""
        if not HAS_TK:
            logger.error("Cannot run GUI: tkinter not available")
            self._run_opencv_fallback()
            return
        
        # Disable automatic GC — we'll run it manually from the main thread only.
        # This prevents Tcl_AsyncDelete crashes when Python's GC runs in a
        # background thread (CUDA/Whisper) and collects Tcl async handler objects.
        import gc
        gc.disable()
        self._gc_counter = 0
        
        self.root = tk.Tk()
        self.root.title("Monica AI")
        self.root.geometry("1280x800")
        self.root.configure(bg='#1a1a2e')
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # Apply dark theme
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Dark.TFrame', background='#1a1a2e')
        style.configure('Dark.TLabel', background='#1a1a2e', foreground='#e0e0e0',
                        font=('Segoe UI', 10))
        style.configure('Title.TLabel', background='#1a1a2e', foreground='#00d4ff',
                        font=('Segoe UI', 14, 'bold'))
        style.configure('Status.TLabel', background='#1a1a2e', foreground='#00ff88',
                        font=('Segoe UI', 9))
        style.configure('Dark.TButton', background='#16213e', foreground='#e0e0e0',
                        font=('Segoe UI', 10))
        
        # Show login dialog before building UI
        self._authenticated = False
        try:
            from security.auth_manager import get_auth_manager
            self._auth_manager = get_auth_manager()
            if self._auth_manager.is_setup():
                from ui.security_panel import LoginDialog
                login = LoginDialog(self.root, self._auth_manager)
                if not login.show():
                    self.root.destroy()
                    return
            self._authenticated = True
        except Exception as e:
            logger.warning(f"Auth module not available, skipping login: {e}")
            self._authenticated = True
        
        self._build_ui()
        
        # Start video feed updates
        self.is_running = True
        self.root.after(100, self._update_video)
        self.root.after(2000, self._update_status)
        
        logger.info("GUI main loop starting")
        self.root.mainloop()

    def _build_ui(self):
        """Build the main UI layout."""
        # Main container
        main_frame = ttk.Frame(self.root, style='Dark.TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Title bar
        title_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        title_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(title_frame, text="MONICA AI", style='Title.TLabel').pack(side=tk.LEFT)
        
        # Status indicators
        self.status_labels['stt'] = ttk.Label(title_frame, text="STT: --", style='Status.TLabel')
        self.status_labels['stt'].pack(side=tk.RIGHT, padx=10)
        self.status_labels['tts'] = ttk.Label(title_frame, text="TTS: --", style='Status.TLabel')
        self.status_labels['tts'].pack(side=tk.RIGHT, padx=10)
        self.status_labels['vision'] = ttk.Label(title_frame, text="Vision: --", style='Status.TLabel')
        self.status_labels['vision'].pack(side=tk.RIGHT, padx=10)
        self.status_labels['ai'] = ttk.Label(title_frame, text="AI: --", style='Status.TLabel')
        self.status_labels['ai'].pack(side=tk.RIGHT, padx=10)
        
        # Content area: video + chat side by side
        content_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # RIGHT side FIRST (must pack before left so it gets space)
        right_frame = ttk.Frame(content_frame, style='Dark.TFrame', width=350)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))
        right_frame.pack_propagate(False)
        self._right_frame = right_frame  # store reference for later
        
        # Left: Video feed + buttons
        video_frame = ttk.Frame(content_frame, style='Dark.TFrame')
        video_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        ttk.Label(video_frame, text="Live Feed", style='Dark.TLabel').pack(anchor=tk.W)
        
        video_container = tk.Frame(video_frame, bg='#0a0a1a', height=360)
        video_container.pack(fill=tk.X)
        video_container.pack_propagate(False)  # Prevent children from resizing container
        self.video_label = tk.Label(video_container, bg='#0a0a1a')
        self.video_label.pack(fill=tk.BOTH, expand=True)
        
        # Globe mouse interaction state
        self._globe_drag_start = None
        self._globe_drag_rot_start = 0.0
        
        # Bind mouse events for globe drag
        self.video_label.bind('<ButtonPress-1>', self._on_video_mouse_down)
        self.video_label.bind('<B1-Motion>', self._on_video_mouse_drag)
        self.video_label.bind('<ButtonRelease-1>', self._on_video_mouse_up)
        self.video_label.bind('<MouseWheel>', self._on_video_mouse_wheel)
        
        # === ROW 0: Hands-Free / Push-to-Talk / Initialize ===
        mode_btn_frame = tk.Frame(video_frame, bg='#1a1a2e')
        mode_btn_frame.pack(fill=tk.X, pady=(3, 0))
        
        mbtn = {"relief": tk.FLAT, "font": ("Segoe UI", 10, "bold"), "width": 14}
        
        self._handsfree_btn = tk.Button(
            mode_btn_frame, text="Hands-Free [ON]", bg="#00aa55", fg="#ffffff",
            activebackground="#1a4e2e", activeforeground="#00ff88",
            command=self._toggle_hands_free, **mbtn)
        self._handsfree_btn.pack(side=tk.LEFT, padx=3, ipady=4)
        
        self._ptt_btn = tk.Button(
            mode_btn_frame, text="Push to Talk", bg="#2e1a1a", fg="#ff6644",
            activebackground="#4e1a1a", activeforeground="#ff6644",
            command=self._toggle_push_to_talk, **mbtn)
        self._ptt_btn.pack(side=tk.LEFT, padx=3, ipady=4)
        # Bind mouse hold for push-to-talk
        self._ptt_btn.bind('<ButtonPress-1>', self._ptt_press)
        self._ptt_btn.bind('<ButtonRelease-1>', self._ptt_release)
        
        self._init_btn = tk.Button(
            mode_btn_frame, text="Monica Initialize", bg="#16213e", fg="#00d4ff",
            activebackground="#1a1a4e", activeforeground="#00d4ff",
            command=self._monica_initialize, **mbtn)
        self._init_btn.pack(side=tk.LEFT, padx=3, ipady=4)
        
        # Mic level bar
        mic_level_frame = tk.Frame(mode_btn_frame, bg='#1a1a2e')
        mic_level_frame.pack(side=tk.RIGHT, padx=5, fill=tk.Y)
        tk.Label(mic_level_frame, text="MIC", bg='#1a1a2e', fg='#888888',
                 font=('Segoe UI', 7)).pack(side=tk.LEFT, padx=(0,2))
        self._mic_level_canvas = tk.Canvas(mic_level_frame, width=100, height=16,
                                            bg='#0a0a1a', highlightthickness=0)
        self._mic_level_canvas.pack(side=tk.LEFT)
        
        # Video control buttons
        vid_btn_frame = tk.Frame(video_frame, bg='#1a1a2e')
        vid_btn_frame.pack(fill=tk.X, pady=(3, 0))
        
        vbtn = {"bg": "#16213e", "fg": "#00d4ff", "activebackground": "#1a1a4e",
                "activeforeground": "#00d4ff", "relief": tk.FLAT, "font": ("Segoe UI", 9)}
        
        # Camera toggle — camera is OFF by default
        self._camera_btn = tk.Button(vid_btn_frame, text="Camera", bg="#2e1a1a", fg="#ff6644",
            activebackground="#4e1a1a", activeforeground="#ff6644",
            relief=tk.FLAT, font=("Segoe UI", 9, "bold"), command=self._toggle_camera)
        self._camera_btn.pack(side=tk.LEFT, padx=2)
        
        tk.Button(vid_btn_frame, text="Show Globe", command=self._toggle_globe, **vbtn).pack(side=tk.LEFT, padx=2)
        tk.Button(vid_btn_frame, text="OBS/Spout", command=self._toggle_spout, **vbtn).pack(side=tk.LEFT, padx=2)
        tk.Button(vid_btn_frame, text="Virtual Keyboard", command=self._show_keyboard, **vbtn).pack(side=tk.LEFT, padx=2)
        tk.Button(vid_btn_frame, text="Desktop Teach", command=self._show_desktop_teach, **vbtn).pack(side=tk.LEFT, padx=2)
        
        # Second row: STT training buttons
        train_btn_frame = tk.Frame(video_frame, bg='#1a1a2e')
        train_btn_frame.pack(fill=tk.X, pady=(2, 0))
        
        tbtn = {"bg": "#1e3a2e", "fg": "#00ff88", "activebackground": "#1a4e2e",
                "activeforeground": "#00ff88", "relief": tk.FLAT, "font": ("Segoe UI", 9)}
        
        tk.Button(train_btn_frame, text="Record Voice (STT)", command=self._launch_stt_training, **tbtn).pack(side=tk.LEFT, padx=2)
        tk.Button(train_btn_frame, text="Apply to STT", command=self._apply_stt_recordings, **tbtn).pack(side=tk.LEFT, padx=2)
        tk.Button(train_btn_frame, text="Reindex PDFs", command=self._reindex_knowledge, **tbtn).pack(side=tk.LEFT, padx=2)
        
        # Third row: OBS effect browser windows (fog, clouds, stars, aurora)
        obs_btn_frame = tk.Frame(video_frame, bg='#1a1a2e')
        obs_btn_frame.pack(fill=tk.X, pady=(2, 0))
        
        obtn = {"bg": "#2e1a3e", "fg": "#cc88ff", "activebackground": "#3e1a4e",
                "activeforeground": "#cc88ff", "relief": tk.FLAT, "font": ("Segoe UI", 9)}
        
        tk.Button(obs_btn_frame, text="Fog", command=lambda: self._launch_obs_effect('fog'), **obtn).pack(side=tk.LEFT, padx=2)
        tk.Button(obs_btn_frame, text="Clouds", command=lambda: self._launch_obs_effect('clouds'), **obtn).pack(side=tk.LEFT, padx=2)
        tk.Button(obs_btn_frame, text="Star Field", command=lambda: self._launch_obs_effect('starfield'), **obtn).pack(side=tk.LEFT, padx=2)
        tk.Button(obs_btn_frame, text="Aurora", command=lambda: self._launch_obs_effect('aurora'), **obtn).pack(side=tk.LEFT, padx=2)
        
        # Chat section (in right_frame which was packed earlier)
        chat_frame = ttk.Frame(self._right_frame, style='Dark.TFrame')
        chat_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(chat_frame, text="Chat", style='Dark.TLabel').pack(anchor=tk.W)
        
        # Chat display
        self.chat_display = scrolledtext.ScrolledText(
            chat_frame,
            bg='#0f0f23',
            fg='#e0e0e0',
            font=('Segoe UI', 10),
            wrap=tk.WORD,
            state=tk.DISABLED,
            height=12
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True, pady=(5, 5))
        
        # Configure tags for colored text
        self.chat_display.tag_configure('user', foreground='#00d4ff')
        self.chat_display.tag_configure('monica', foreground='#00ff88')
        self.chat_display.tag_configure('system', foreground='#888888')
        
        # Chat input
        input_frame = ttk.Frame(chat_frame, style='Dark.TFrame')
        input_frame.pack(fill=tk.X)
        
        self.chat_input = tk.Entry(
            input_frame,
            bg='#16213e',
            fg='#e0e0e0',
            insertbackground='#00d4ff',
            font=('Segoe UI', 10),
            relief=tk.FLAT
        )
        self.chat_input.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5)
        self.chat_input.bind('<Return>', self._on_send)
        
        send_btn = tk.Button(
            input_frame,
            text="Send",
            bg='#16213e',
            fg='#00d4ff',
            activebackground='#1a1a4e',
            activeforeground='#00d4ff',
            relief=tk.FLAT,
            font=('Segoe UI', 10),
            command=lambda: self._on_send(None)
        )
        send_btn.pack(side=tk.RIGHT, padx=(5, 0), ipady=3)
        
        # Security & Teaching Panel (below chat)
        security_frame = tk.Frame(self._right_frame, bg='#1a1a2e')
        security_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        try:
            from ui.security_panel import SecurityPanel
            self.security_panel = SecurityPanel(security_frame, self.root)
        except Exception as e:
            logger.warning(f"Security panel not available: {e}")
            tk.Label(security_frame, text="Security panel unavailable",
                     bg='#1a1a2e', fg='#666666', font=('Segoe UI', 9)).pack()
        
        # Microphone selection panel
        mic_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        mic_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Label(mic_frame, text="Mic:", style='Dark.TLabel').pack(side=tk.LEFT, padx=(0, 3))
        
        self.mic_var = tk.StringVar()
        self.mic_combo = ttk.Combobox(
            mic_frame,
            textvariable=self.mic_var,
            state='readonly',
            width=30,
            font=('Segoe UI', 9)
        )
        self.mic_combo.pack(side=tk.LEFT, padx=(0, 5))
        self.mic_combo.bind('<<ComboboxSelected>>', self._on_mic_changed)
        
        tk.Button(mic_frame, text="Refresh", bg='#16213e', fg='#00d4ff',
                  activebackground='#1a1a4e', activeforeground='#00d4ff',
                  relief=tk.FLAT, font=('Segoe UI', 9),
                  command=self._refresh_microphones).pack(side=tk.LEFT, padx=(0, 10))
        
        # Headphones / audio output device selector
        ttk.Label(mic_frame, text="Output:", style='Dark.TLabel').pack(side=tk.LEFT, padx=(0, 3))
        
        self.output_var = tk.StringVar()
        self.output_combo = ttk.Combobox(
            mic_frame,
            textvariable=self.output_var,
            state='readonly',
            width=30,
            font=('Segoe UI', 9)
        )
        self.output_combo.pack(side=tk.LEFT, padx=(0, 5))
        self.output_combo.bind('<<ComboboxSelected>>', self._on_output_changed)
        self.output_devices = []
        
        tk.Button(mic_frame, text="Refresh", bg='#16213e', fg='#00d4ff',
                  activebackground='#1a1a4e', activeforeground='#00d4ff',
                  relief=tk.FLAT, font=('Segoe UI', 9),
                  command=self._refresh_outputs).pack(side=tk.LEFT)
        
        # Populate device lists
        self._refresh_microphones()
        self._refresh_outputs()
        
        # Add welcome message
        self._append_chat("Monica AI loaded.", 'system')
        self._append_chat("Voice: Hands-Free ON (speak anytime)", 'system')
        self._append_chat("1. Click 'Camera' to turn on your camera.", 'system')
        self._append_chat("2. Say or type 'Monica Initialize' to activate.", 'system')
        self._append_chat("3. Say 'show globe' to see the interactive globe.", 'system')

    def _update_video(self):
        """Update the video feed from the vision service."""
        if not self.is_running or not self.root:
            return
        
        # Drain cross-thread chat queue (safe: runs in main thread only)
        try:
            while not self._chat_queue.empty():
                text, tag = self._chat_queue.get_nowait()
                self._append_chat(text, tag)
        except Exception:
            pass
        
        try:
            frame = None
            
            # Get processed frame from orchestrator (includes all overlays)
            if self.orchestrator:
                frame = self.orchestrator.get_shared('vision_frame')
            
            # Skip if frame hasn't changed (avoids redundant PIL/PhotoImage work)
            frame_id = self.orchestrator.get_shared('vision_frame_id', -1) if self.orchestrator else -1
            if frame is not None and HAS_PIL and HAS_CV2 and frame_id != self._last_frame_id:
                self._last_frame_id = frame_id
                
                # Use pre-converted RGB from vision thread (avoids cvtColor here)
                frame_rgb = None
                if self.orchestrator:
                    frame_rgb = self.orchestrator.get_shared('vision_frame_rgb')
                if frame_rgb is None:
                    frame_rgb = cv2.cvtColor(frame.copy(), cv2.COLOR_BGR2RGB)
                else:
                    frame_rgb = frame_rgb.copy()
                
                # Get video label dimensions
                label_w = self.video_label.winfo_width()
                label_h = self.video_label.winfo_height()
                
                if label_w > 1 and label_h > 1:
                    # Resize frame to fit label (INTER_NEAREST is fastest)
                    fh, fw = frame_rgb.shape[:2]
                    scale = min(label_w / fw, label_h / fh)
                    new_w = int(fw * scale)
                    new_h = int(fh * scale)
                    
                    frame_resized = cv2.resize(frame_rgb, (new_w, new_h),
                                               interpolation=cv2.INTER_NEAREST)
                    
                    # Convert to PhotoImage
                    img = Image.fromarray(frame_resized)
                    self._photo = ImageTk.PhotoImage(image=img)
                    self.video_label.configure(image=self._photo)
            
            # Update mic level bar
            if self.orchestrator and self._mic_level_canvas:
                mic_energy = self.orchestrator.get_shared('mic_energy', 0.0)
                self._update_mic_level(mic_energy)
            
            # Check for new STT transcripts
            if self.orchestrator:
                transcript = self.orchestrator.get_shared('last_transcript')
                consumed = self.orchestrator.get_shared('stt_consumed', True)
                if transcript and not consumed:
                    # Mark as consumed immediately so we don't double-process
                    self.orchestrator.set_shared('stt_consumed', True)
                    
                    # Check for voice init command (robust to transcript variants)
                    if self._is_initialize_command(transcript):
                        self._monica_initialize()
                        return self._schedule_next_update()

                    # Check for stop/quiet commands — instantly stop TTS
                    t_lower = transcript.lower().strip().rstrip('.!?,')
                    stop_phrases = ('stop', 'monica stop', 'be quiet', 'shut up',
                                    'hush', 'enough', 'ok stop', 'okay stop', 'silence')
                    if t_lower in stop_phrases or t_lower.startswith('stop talking'):
                        tts = self.orchestrator.get_service('tts')
                        if tts:
                            tts.stop_speaking()
                        self._append_chat("[Stopped speaking]", 'system')
                        return self._schedule_next_update()

                    # For normal transcripts, only process when voice mode is active
                    allow_chat = (
                        self._stt_mode == 'hands_free' or
                        (self._stt_mode == 'push_to_talk' and self._ptt_active)
                    )
                    if not allow_chat:
                        return self._schedule_next_update()
                    
                    # GATE: Monica must be initialized before processing any input
                    if not self._monica_initialized:
                        if self._is_low_quality_wake_transcript(transcript):
                            return self._schedule_next_update()
                        print(f"[SPEECH] Monica NOT ACTIVATED. Say 'Monica initialize' to start. Ignoring: '{transcript}'")
                        return self._schedule_next_update()
                    
                    self._append_chat(f"You: {transcript}", 'user')
                    
                    # Send transcript to AI service for processing
                    ai_service = self.orchestrator.get_service('ai')
                    if ai_service:
                        ai_service.ask(transcript)
            
            # Check for AI responses (always — typed messages need responses too)
            if self.orchestrator:
                ai_response = self.orchestrator.get_shared('ai_response')
                ai_consumed = self.orchestrator.get_shared('ai_consumed', True)
                if ai_response and not ai_consumed:
                    # Mark consumed so we don't repeat
                    self.orchestrator.set_shared('ai_consumed', True)
                    
                    self._append_chat(f"Monica: {ai_response}", 'monica')
                    
                    # Send to TTS
                    tts = self.orchestrator.get_service('tts')
                    if tts:
                        tts.speak(ai_response)
        
        except Exception as e:
            logger.debug(f"Video update error: {e}")
        
        # Schedule next update
        self._schedule_next_update()

    def _schedule_next_update(self):
        """Schedule the next video update frame."""
        if self.is_running and self.root:
            try:
                self.root.after(self.video_update_ms, self._update_video)
            except Exception:
                pass

    def _update_mic_level(self, energy: float):
        """Draw the mic level indicator bar."""
        if not self._mic_level_canvas:
            return
        self._mic_level_canvas.delete('all')
        # Normalize energy to 0-100 pixel width
        level = min(100, int(energy * 3000))  # Scale for visibility
        # Color: green for low, yellow for medium, red for high
        if level < 40:
            color = '#00ff88'
        elif level < 70:
            color = '#ffdd00'
        else:
            color = '#ff4444'
        if level > 1:
            self._mic_level_canvas.create_rectangle(0, 2, level, 14, fill=color, outline='')
        # Draw threshold marker
        self._mic_level_canvas.create_line(33, 0, 33, 16, fill='#555555', width=1)

    def _toggle_hands_free(self):
        """Toggle hands-free (always listening) mode."""
        if self._stt_mode == 'hands_free':
            self._stt_mode = 'off'
            self._handsfree_btn.configure(bg='#1e3a2e', text='Hands-Free')
            self._append_chat("Voice mode: OFF", 'system')
        else:
            self._stt_mode = 'hands_free'
            self._handsfree_btn.configure(bg='#00aa55', text='Hands-Free [ON]')
            self._ptt_btn.configure(bg='#2e1a1a', text='Push to Talk')
            self._append_chat("Voice mode: Hands-Free (always listening)", 'system')

    def _toggle_push_to_talk(self):
        """Toggle push-to-talk mode."""
        if self._stt_mode == 'push_to_talk':
            self._stt_mode = 'off'
            self._ptt_btn.configure(bg='#2e1a1a', text='Push to Talk')
            self._append_chat("Voice mode: OFF", 'system')
        else:
            self._stt_mode = 'push_to_talk'
            self._ptt_btn.configure(bg='#aa4400', text='Push to Talk [ON]')
            self._handsfree_btn.configure(bg='#1e3a2e', text='Hands-Free')
            self._append_chat("Voice mode: Push-to-Talk (hold button to speak)", 'system')

    def _ptt_press(self, event=None):
        """Push-to-talk button pressed - start listening."""
        if self._stt_mode == 'push_to_talk':
            self._ptt_active = True
            self._ptt_btn.configure(bg='#ff4400', text='LISTENING...')

    def _ptt_release(self, event=None):
        """Push-to-talk button released - stop listening."""
        if self._stt_mode == 'push_to_talk':
            self._ptt_active = False
            self._ptt_btn.configure(bg='#aa4400', text='Push to Talk [ON]')

    def _toggle_camera(self):
        """Toggle camera on/off via vision service."""
        if not self.orchestrator:
            self._append_chat("Orchestrator not available", 'system')
            return
        vision = self.orchestrator.get_service('vision')
        if not vision:
            self._append_chat("Vision service not available", 'system')
            return
        
        if vision.camera_active:
            vision.stop_camera()
            self._camera_btn.configure(bg='#2e1a1a', fg='#ff6644', text='Camera')
            self._append_chat("Camera OFF", 'system')
        else:
            # Clear any previous camera error
            self.orchestrator.set_shared('camera_error', None)
            vision.start_camera()
            # Check for errors after a short delay (camera starts async)
            def _check_camera():
                import time as _t
                _t.sleep(3)
                err = self.orchestrator.get_shared('camera_error')
                if err:
                    self._chat_queue.put((f"Camera error: {err}", 'system'))
                elif not vision.camera_active:
                    self._chat_queue.put(("Camera failed to start. Check if another app is using it.", 'system'))
            import threading
            threading.Thread(target=_check_camera, daemon=True).start()
            self._camera_btn.configure(bg='#00aa55', fg='#ffffff', text='Camera [ON]')
            self._append_chat("Camera starting...", 'system')

    def _monica_initialize(self):
        """Trigger Monica's initialization sequence (sounds + TTS). Only runs once."""
        if self._monica_initialized:
            self._append_chat("Monica is already initialized this session.", 'system')
            return
        
        self._monica_initialized = True
        self._init_btn.configure(bg='#004422', text='Initialized', state=tk.DISABLED)
        self._append_chat("Monica initializing... playing startup sequence.", 'system')
        
        import threading
        
        def _run_init():
            played = False
            # Method 1: Try the launcher's initialization sequence (sounds + TTS)
            try:
                if self.orchestrator and hasattr(self.orchestrator, '_play_initialization_sequence'):
                    self.orchestrator._play_initialization_sequence()
                    played = True
            except Exception as e:
                self._safe_chat(f"Sound init: {e}", 'system')
            
            # Method 2: If no sound played, use AI service's init sequence (TTS only)
            if not played:
                try:
                    ai = self.orchestrator.get_service('ai') if self.orchestrator else None
                    if ai and hasattr(ai, '_do_initialize_sequence'):
                        result = ai._do_initialize_sequence()
                        self._safe_chat(result, 'monica')
                        played = True
                except Exception as e:
                    self._safe_chat(f"AI init: {e}", 'system')
            
            # Method 3: Direct TTS fallback
            if not played:
                try:
                    tts = self.orchestrator.get_service('tts') if self.orchestrator else None
                    if tts and hasattr(tts, 'speak'):
                        tts.speak("Monica initializing. All systems online.")
                        played = True
                except Exception:
                    pass
            
            if played:
                self._safe_chat("Monica initialization complete.", 'system')
            else:
                self._safe_chat("Could not play initialization sounds.", 'system')
        
        threading.Thread(target=_run_init, daemon=True).start()
        
        if self.orchestrator:
            self.orchestrator._monica_initialized = True

    def _safe_chat(self, text, tag='system'):
        """Thread-safe chat append (can be called from background threads).
        Uses a queue instead of root.after() to avoid Tcl_AsyncDelete crashes."""
        try:
            self._chat_queue.put_nowait((text, tag))
        except Exception:
            pass

    def _update_status(self):
        """Update service status indicators."""
        if not self.is_running or not self.root:
            return
        
        try:
            if self.orchestrator:
                statuses = self.orchestrator.get_service_status()
                for name, state in statuses.items():
                    if name in self.status_labels:
                        color = '#00ff88' if state == 'running' else '#ff4444'
                        self.status_labels[name].configure(
                            text=f"{name.upper()}: {state}",
                            foreground=color
                        )
        except Exception:
            pass
        
        if self.is_running and self.root:
            self.root.after(5000, self._update_status)

    def _on_send(self, event):
        """Handle send button / Enter key."""
        if not self.chat_input:
            return
        
        text = self.chat_input.get().strip()
        if not text:
            return
        
        self.chat_input.delete(0, tk.END)
        
        # Check for typed init command
        if self._is_initialize_command(text):
            self._monica_initialize()
            return
        
        # GATE: Monica must be initialized before processing any input
        if not self._monica_initialized:
            self._append_chat("Say 'Monica initialize' or click the Initialize button first.", 'system')
            return
        
        self._append_chat(f"You: {text}", 'user')
        
        # Send to AI service
        if self.orchestrator:
            ai_service = self.orchestrator.get_service('ai')
            if ai_service:
                ai_service.ask(text)
            else:
                self._append_chat("AI service is not running. Check monica_services.log for errors.", 'system')

    def _append_chat(self, text: str, tag: str = 'system'):
        """Append text to chat display."""
        if not self.chat_display:
            return
        
        self.chat_display.configure(state=tk.NORMAL)
        self.chat_display.insert(tk.END, text + "\n", tag)
        self.chat_display.configure(state=tk.DISABLED)
        self.chat_display.see(tk.END)

    @staticmethod
    def _is_low_quality_wake_transcript(text: str) -> bool:
        """Filter common STT fragments so wake prompt doesn't spam on noise."""
        if not text:
            return True
        t = text.lower().strip().rstrip('.!?,')
        if len(t) <= 1:
            return True
        if t in ('a', 'i', 'an', 'uh', 'um', 'hmm', 'mm', 'ah', 'oh'):
            return True
        words = t.split()
        if len(words) == 1 and words[0] in ('a', 'i', 'an', 'uh', 'um', 'hmm'):
            return True
        return False

    @staticmethod
    def _is_initialize_command(text: str) -> bool:
        """Return True if text means "Monica initialize" (voice/typed variants).
        Whisper frequently mistranscribes this as: 'Monica interlaced',
        'Omega Initialoates', 'Monica Angel Ace', etc.
        Uses fuzzy matching to catch these variants."""
        if not text:
            return False
        t = text.lower().strip().rstrip('.!?,')
        # Exact keyword matches
        init_keywords = (
            'initialize', 'initialise', 'initializing', 'initialising',
            'init', 'start up', 'startup', 'system online', 'system ready',
            'interlaced', 'initialoates', 'angel ace', 'in itialize',
        )
        if any(k in t for k in init_keywords):
            return True
        # Exact short forms Whisper often produces
        if t in ('monica in', 'monica init', 'monika in', 'monica inn',
                 'monica and', 'monica en', 'monica hint'):
            return True
        # Fuzzy: if text contains "monica" (or sounds like it) AND starts with "ini" or similar
        has_monica = any(w in t for w in ('monica', 'monika', 'omega', 'monic'))
        has_init_sound = any(t.find(p) >= 0 for p in ('ini', 'inti', 'angel', 'in a', ' in'))
        if has_monica and has_init_sound:
            return True
        # Fuzzy: check if any word starts with "init" or "inti"
        words = t.split()
        for w in words:
            if w.startswith(('init', 'inti', 'initi')):
                return True
        return False

    # ==================== Globe Mouse Interaction ====================
    
    def _get_vision_service(self):
        """Get the vision service from orchestrator."""
        if self.orchestrator:
            return self.orchestrator.get_service('vision')
        return None
    
    def _on_video_mouse_down(self, event):
        """Start globe drag if click is in the globe area (bottom-left)."""
        vision = self._get_vision_service()
        if not vision or not getattr(vision, 'globe_enabled', False):
            return
        # Globe is at bottom-left of the video: x=10, y=h-gs-10
        gs = getattr(vision, 'globe_size', 180)
        # Check if click is roughly in the globe area
        label_h = self.video_label.winfo_height()
        gx, gy = 10, label_h - gs - 10
        if gx <= event.x <= gx + gs and gy <= event.y <= gy + gs:
            self._globe_drag_start = (event.x, event.y)
            self._globe_drag_rot_start = vision.globe_rotation
            # Pause auto-rotation during drag
            import time as _t
            vision._rotation_paused_until = _t.time() + 60
    
    def _on_video_mouse_drag(self, event):
        """Rotate globe based on mouse drag distance."""
        if self._globe_drag_start is None:
            return
        vision = self._get_vision_service()
        if not vision:
            return
        dx = event.x - self._globe_drag_start[0]
        # Map pixel drag to degrees (1 pixel = 0.5 degrees)
        vision.globe_rotation = (self._globe_drag_rot_start + dx * 0.5) % 360
    
    def _on_video_mouse_up(self, event):
        """End globe drag."""
        self._globe_drag_start = None
    
    def _on_video_mouse_wheel(self, event):
        """Zoom globe with mouse wheel."""
        vision = self._get_vision_service()
        if not vision or not getattr(vision, 'globe_enabled', False):
            return
        current = getattr(vision, 'globe_size', 180)
        if event.delta > 0:
            vision.globe_size = min(600, current + 20)
        else:
            vision.globe_size = max(80, current - 20)
    
    def _refresh_microphones(self):
        """Refresh the list of available microphones."""
        try:
            from services.stt_service import STTService
            self.mic_devices = STTService.list_microphones()
        except Exception as e:
            logger.debug(f"Could not list microphones via STTService: {e}")
            self.mic_devices = []
            # Direct fallback
            try:
                import pyaudio
                pa = pyaudio.PyAudio()
                for i in range(pa.get_device_count()):
                    info = pa.get_device_info_by_index(i)
                    if info.get('maxInputChannels', 0) > 0:
                        self.mic_devices.append({
                            'index': i,
                            'name': info.get('name', f'Device {i}'),
                            'sample_rate': int(info.get('defaultSampleRate', 16000)),
                            'channels': int(info.get('maxInputChannels', 1))
                        })
                pa.terminate()
            except Exception:
                pass
        
        if self.mic_combo:
            names = [f"[{d['index']}] {d['name']}" for d in self.mic_devices]
            self.mic_combo['values'] = names if names else ['(No microphones found)']
            
            # Unbind event to prevent programmatic .current() from triggering _on_mic_changed
            self.mic_combo.unbind('<<ComboboxSelected>>')

            # Try to select currently configured device
            current_idx = None
            if self.orchestrator:
                stt = self.orchestrator.get_service('stt')
                if stt:
                    current_idx = getattr(stt, 'input_device_index', None)
            
            if current_idx is not None:
                for i, d in enumerate(self.mic_devices):
                    if d['index'] == current_idx:
                        self.mic_combo.current(i)
                        break
            elif names:
                # Select Maonocaster or first real mic in dropdown (display only)
                selected = 0
                for i, d in enumerate(self.mic_devices):
                    name_l = d['name'].lower()
                    if 'maonocaster' in name_l or 'headset' in name_l:
                        selected = i
                        break
                self.mic_combo.current(selected)

            # Re-bind after programmatic selection
            self.mic_combo.bind('<<ComboboxSelected>>', self._on_mic_changed)

    def _on_mic_changed(self, event=None):
        """Handle microphone selection change."""
        sel = self.mic_combo.current()
        if sel < 0 or sel >= len(self.mic_devices):
            return
        
        device = self.mic_devices[sel]
        device_index = device['index']
        device_name = device['name']
        
        # Update STT service
        if self.orchestrator:
            stt = self.orchestrator.get_service('stt')
            if stt and hasattr(stt, 'set_microphone'):
                stt.set_microphone(device_index=device_index, device_name=device_name)
                self._append_chat(f"Microphone changed to: {device_name}", 'system')
            else:
                self._append_chat(f"STT service not available for mic change", 'system')

    def _refresh_outputs(self):
        """Refresh the list of audio output devices (headphones/speakers)."""
        self.output_devices = []
        try:
            import pyaudio
            pa = pyaudio.PyAudio()
            for i in range(pa.get_device_count()):
                info = pa.get_device_info_by_index(i)
                if info.get('maxOutputChannels', 0) > 0:
                    self.output_devices.append({
                        'index': i,
                        'name': info.get('name', f'Device {i}'),
                    })
            pa.terminate()
        except Exception:
            pass
        
        if self.output_combo:
            names = [f"[{d['index']}] {d['name']}" for d in self.output_devices]
            self.output_combo['values'] = names if names else ['(No output devices)']
            if names:
                self.output_combo.current(0)

    def _on_output_changed(self, event=None):
        """Handle audio output device selection change — sets sounddevice default output."""
        sel = self.output_combo.current()
        if sel < 0 or sel >= len(self.output_devices):
            return
        device = self.output_devices[sel]
        device_idx = device['index']
        device_name = device['name']
        
        # Set sounddevice default output so TTS plays through this device
        try:
            import sounddevice as sd
            sd.default.device = (sd.default.device[0], device_idx)
            self._append_chat(f"Audio output: {device_name}", 'system')
        except Exception as e:
            self._append_chat(f"Output device error: {e}", 'system')

    def _toggle_globe(self):
        """Toggle globe overlay on/off."""
        if self.orchestrator:
            vision = self.orchestrator.get_service('vision')
            if vision:
                vision.globe_enabled = not vision.globe_enabled
                if vision.globe_enabled and vision.globe_renderer:
                    vision.globe_renderer.show()
                elif vision.globe_renderer:
                    vision.globe_renderer.hide()
                state = "ON" if vision.globe_enabled else "OFF"
                self._append_chat(f"Globe overlay: {state}", 'system')
            else:
                self._append_chat("Vision service not available", 'system')

    def _toggle_spout(self):
        """Toggle OBS/Spout output."""
        if self.orchestrator:
            vision = self.orchestrator.get_service('vision')
            if vision and vision.camera_manager:
                try:
                    spout_on = getattr(vision.camera_manager, 'spout_enabled', False)
                    vision.camera_manager.spout_enabled = not spout_on
                    state = "Connected" if not spout_on else "Disconnected"
                    self._append_chat(f"OBS/Spout: {state}", 'system')
                except Exception as e:
                    self._append_chat(f"Spout error: {e}", 'system')
            else:
                self._append_chat("Camera not available for Spout", 'system')

    def _show_keyboard(self):
        """Launch the virtual keyboard with hand tracking."""
        try:
            from vision.monica_hand_keyboard import get_hand_keyboard
            kb = get_hand_keyboard()
            if self.orchestrator:
                vision = self.orchestrator.get_service('vision')
                if vision and vision.hand_controller:
                    kb.set_hand_controller(vision.hand_controller)
            kb.show()
            self._append_chat("Virtual Keyboard launched (use fingertips to type)", 'system')
        except Exception as e:
            self._append_chat(f"Keyboard not available: {e}", 'system')

    def _show_desktop_teach(self):
        """Start desktop assistant mode — Monica sees your screen and helps."""
        import threading
        def _capture():
            try:
                from PIL import ImageGrab
                import subprocess, json as _json
                
                # Capture screenshot
                screenshot = ImageGrab.grab()
                # Save to temp for reference
                ss_path = "data/desktop_screenshot.png"
                screenshot.save(ss_path)
                
                # Get list of visible windows via PowerShell
                windows_info = ""
                try:
                    ps = subprocess.run(
                        ["powershell", "-Command",
                         "Get-Process | Where-Object {$_.MainWindowTitle -ne ''} | Select-Object -Property MainWindowTitle | ConvertTo-Json"],
                        capture_output=True, text=True, timeout=5
                    )
                    if ps.stdout:
                        wins = _json.loads(ps.stdout)
                        if isinstance(wins, list):
                            titles = [w.get('MainWindowTitle', '') for w in wins if w.get('MainWindowTitle')]
                        elif isinstance(wins, dict):
                            titles = [wins.get('MainWindowTitle', '')]
                        else:
                            titles = []
                        windows_info = "Open windows: " + ", ".join(titles[:10])
                except Exception:
                    windows_info = "Could not detect open windows."
                
                # Get active window title
                active_win = ""
                try:
                    ps2 = subprocess.run(
                        ["powershell", "-Command",
                         "(Get-Process | Where-Object {$_.MainWindowHandle -eq (Add-Type -MemberDefinition '[DllImport(\"user32.dll\")] public static extern IntPtr GetForegroundWindow();' -Name Win32 -Namespace Temp -PassThru)::GetForegroundWindow()}).MainWindowTitle"],
                        capture_output=True, text=True, timeout=5
                    )
                    if ps2.stdout.strip():
                        active_win = f"Active window: {ps2.stdout.strip()}"
                except Exception:
                    pass
                
                # Send context to AI
                context = f"[DESKTOP ASSISTANT MODE]\n{active_win}\n{windows_info}\nScreenshot saved. I can see the user's desktop. I should help them with whatever they're working on."
                
                if self.orchestrator:
                    ai = self.orchestrator.get_service('ai')
                    if ai:
                        ai.ask(f"[System: Desktop assistant activated. {context}] The user wants help with what's on their screen. Briefly describe what you know they have open and offer to help.")
                
                self._append_chat("Desktop assistant active — I can see your screen! Ask me anything about what you're working on.", 'system')
                
            except Exception as e:
                self._append_chat(f"Desktop assistant error: {e}", 'system')
        
        threading.Thread(target=_capture, daemon=True).start()

    def _launch_stt_training(self):
        """Launch STT voice recording training in a separate process."""
        import subprocess
        import sys
        project = str(Path(__file__).parent.parent.parent)
        script = str(Path(project) / "scripts" / "audio" / "record_stt_training.py")
        try:
            subprocess.Popen(
                [sys.executable, script],
                cwd=project,
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            self._append_chat("STT Voice Training launched in new window. Read phrases aloud!", 'system')
        except Exception as e:
            self._append_chat(f"Could not launch STT training: {e}", 'system')

    def _apply_stt_recordings(self):
        """Apply recorded voice samples to update the STT model."""
        self._append_chat("Applying voice recordings to STT model...", 'system')
        try:
            import subprocess, sys
            project = str(Path(__file__).parent.parent.parent)
            script = str(Path(project) / "scripts" / "enhanced_stt_pipeline.py")
            if Path(script).exists():
                subprocess.Popen(
                    [sys.executable, script],
                    cwd=project,
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
                self._append_chat("STT model update started in new window.", 'system')
            else:
                self._append_chat("STT pipeline script not found. Recordings saved for future training.", 'system')
        except Exception as e:
            self._append_chat(f"STT apply error: {e}", 'system')

    def _reindex_knowledge(self):
        """Force reindex all PDFs and documents in the knowledge base."""
        self._append_chat("Reindexing all PDFs and documents...", 'system')
        try:
            from ai.knowledge_watcher import get_knowledge_watcher
            watcher = get_knowledge_watcher()
            watcher.force_reindex()
            stats = watcher.get_stats()
            self._append_chat(
                f"Reindex complete: {stats.get('total_documents', 0)} docs, "
                f"{stats.get('total_chunks', 0)} chunks indexed.", 'system')
        except Exception as e:
            self._append_chat(f"Reindex error: {e}", 'system')

    def _launch_obs_effect(self, effect_name: str):
        """Launch an OBS browser effect (fog, clouds, starfield, aurora) in default browser."""
        import webbrowser
        project = Path(__file__).parent.parent.parent
        effect_map = {
            'fog': project / 'src' / 'ui' / 'CSS_FOG_ANIMATION' / 'index.html',
            'clouds': project / 'src' / 'ui' / 'clouds-animation-code' / 'haven-animation.html',
            'starfield': project / 'animations' / 'starfield.html',
            'aurora': project / 'animations' / 'aurora.html',
        }
        html_path = effect_map.get(effect_name)
        if html_path and html_path.exists():
            webbrowser.open(str(html_path))
            self._append_chat(f"OBS Effect: {effect_name} opened in browser (add as Browser Source in OBS)", 'system')
        else:
            self._append_chat(f"Effect file not found: {effect_name}", 'system')

    def _on_close(self):
        """Handle window close — stop services, then force-exit to avoid Tcl GC crash."""
        self.is_running = False
        root = self.root
        self.root = None  # Prevent any further after() scheduling

        # Stop orchestrator synchronously (with timeout) so threads wind down
        if self.orchestrator:
            import threading
            done = threading.Event()
            def _stop_services():
                try:
                    self.orchestrator.stop()
                except Exception:
                    pass
                finally:
                    done.set()
            threading.Thread(target=_stop_services, daemon=True).start()
            done.wait(timeout=3)  # Wait up to 3s for clean shutdown

        if root:
            try:
                root.destroy()
            except Exception:
                pass

        # Force exit to prevent Python GC from triggering Tcl_AsyncDelete
        import os
        os._exit(0)

    def _run_opencv_fallback(self):
        """Fallback: show video in OpenCV window if tkinter is not available."""
        if not HAS_CV2:
            logger.error("Neither tkinter nor OpenCV available for GUI")
            return
        
        logger.info("Running OpenCV fallback GUI")
        self.is_running = True
        
        while self.is_running:
            frame = None
            if self.orchestrator:
                frame = self.orchestrator.get_shared('vision_frame')
            
            if frame is not None:
                cv2.imshow("Monica AI", frame)
            
            key = cv2.waitKey(33)
            if key == 27 or key == ord('q'):  # ESC or Q
                break
        
        cv2.destroyAllWindows()
        self.is_running = False

    def stop(self):
        """Stop the GUI."""
        self._on_close()
