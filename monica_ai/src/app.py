"""
Main Application for Monica AI.
Integrates all components into a cohesive application.
"""
import os
import sys
import warnings
from pathlib import Path

# ============================================================
# SET CUDA_HOME FOR DEEPSPEED (MUST BE BEFORE ANY TORCH IMPORTS)
# ============================================================
if 'CUDA_HOME' not in os.environ:
    cuda_paths = [
        r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.0",
        r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.9",
        r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8",
        r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.4",
    ]
    for cuda_path in cuda_paths:
        nvcc_path = Path(cuda_path) / "bin" / "nvcc.exe"
        if nvcc_path.exists():
            os.environ['CUDA_HOME'] = cuda_path
            os.environ['CUDA_PATH'] = cuda_path
            print(f"[MONICA] Set CUDA_HOME={cuda_path}")
            break

# ============================================================
# PROFESSIONAL CONSOLE OUTPUT - SUPPRESS ALL WARNINGS/ERRORS
# ============================================================

# Suppress TensorFlow warnings BEFORE importing
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['OPENCV_VIDEOIO_DEBUG'] = '0'
os.environ['OPENCV_LOG_LEVEL'] = 'ERROR'

# Suppress Python warnings
warnings.filterwarnings('ignore', category=DeprecationWarning)
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=UserWarning)
warnings.filterwarnings('ignore', module='pygame.pkgdata')
warnings.filterwarnings('ignore', message='.*pkg_resources.*deprecated.*')
warnings.filterwarnings('ignore', message='.*speechbrain.pretrained.*deprecated.*')

# Suppress TensorFlow logging
import logging
logging.getLogger('tensorflow').setLevel(logging.ERROR)
logging.getLogger('absl').setLevel(logging.ERROR)

# Windows-specific: Suppress DirectShow errors
if sys.platform == 'win32':
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetErrorMode(0x0001 | 0x0002)
    except:
        pass

import tkinter as tk
import threading
import time
import math
import random

from .config.settings import config, AppConfig
from .audio.audio_manager import AudioManager
from .tts.tts_manager import TTSManager
from .ai.conversation_manager import ConversationManager


class MonicaAI:
    """
    Main application class for Monica AI.
    
    Integrates:
    - Camera capture with Spout output
    - Audio input/output with speech recognition
    - Wake word detection
    - Text-to-speech synthesis
    - AI-powered conversation
    - Modern GUI interface
    """
    
    def __init__(self, config_path: Path = None):
        """
        Initialize Monica AI.
        
        Args:
            config_path: Optional path to configuration file
        """
        print("=" * 50)
        print("MONICA AI - Starting...")
        print("=" * 50)
        
        # Load configuration
        if config_path:
            self.config = AppConfig.load(config_path)
        else:
            self.config = config

        try:
            # Use USB headphones microphone instead of sensitive desktop mic
            self.config.INPUT_DEVICE_NAME = "USB"
            # Prefer name-based selection over unstable indices on Windows
            self.config.INPUT_DEVICE_INDEX = None
        except Exception:
            pass
        
        print(f"Configuration loaded from: {self.config.CONFIG_FILE}")
        
        # Register app instance globally for vision system to access biometric data
        import sys
        sys._monica_app = self
        
        # Initialize Tkinter FIRST
        self.root = tk.Tk()
        self.root.title("Monica AI")
        self.root.geometry(f"{self.config.WINDOW_WIDTH}x{self.config.WINDOW_HEIGHT}")
        self.root.minsize(1024, 768)
        
        # Set window icon (if available)
        icon_path = self.config.ICONS_DIR / "monica.ico"
        if icon_path.exists():
            try:
                self.root.iconbitmap(str(icon_path))
            except Exception:
                pass
        
        # Placeholder managers (will be initialized in background)
        self.audio = None
        self.tts = None
        self.camera = None
        self.conversation = None
        self.biometric = None  # Biometric detection (emotion, age, identity, heartbeat)
        self.main_window = None
        self._init_complete = False
        
        # Show loading screen
        self._show_loading_screen()
        
        # Initialize managers in background thread
        self.root.after(100, self._init_managers_async)
        
        # Bind window events
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.bind("<Escape>", lambda e: self.on_close())
    
    def _show_loading_screen(self):
        """Show an animated loading screen while initializing."""
        
        self.loading_frame = tk.Frame(self.root, bg='#0a0a0a')
        self.loading_frame.pack(fill=tk.BOTH, expand=True)
        
        # Monica chooses her animation style!
        self.ANIMATION_STYLES = ['mechanical', 'pulse', 'wave', 'matrix', 'hologram', 'particles', 'typewriter', 'glitch']
        self.animation_style = random.choice(self.ANIMATION_STYLES)
        print(f"[LOADING] Monica chose animation style: {self.animation_style}")
        
        # Canvas for animated logo
        self.logo_canvas = tk.Canvas(
            self.loading_frame,
            width=600,
            height=180,
            bg='#0a0a0a',
            highlightthickness=0
        )
        self.logo_canvas.pack(expand=True, pady=(80, 10))
        
        # Initialize animation variables
        self.animation_frame = 0
        self.capability_index = 0
        self.typewriter_index = 0
        self.particles = []
        
        # Draw initial logo
        self._draw_animated_logo()
        
        # Capabilities label - LARGER (22pt) and positioned HIGHER (between logo and progress)
        self.capability_label = tk.Label(
            self.loading_frame,
            text="",
            font=("Segoe UI", 22, "italic"),  # Larger font!
            fg='#00ffaa',
            bg='#0a0a0a'
        )
        self.capability_label.pack(pady=(15, 25))  # More space
        
        # Progress bar
        from tkinter import ttk
        style = ttk.Style()
        style.theme_use('clam')
        style.configure(
            "Monica.Horizontal.TProgressbar",
            background='#00ffaa',
            darkcolor='#008866',
            lightcolor='#00ffcc',
            bordercolor='#0a0a0a',
            troughcolor='#1a1a1a'
        )
        
        self.progress = ttk.Progressbar(
            self.loading_frame,
            style="Monica.Horizontal.TProgressbar",
            length=400,
            mode='determinate',
            maximum=100
        )
        self.progress.pack(pady=10)
        
        # Status label - below progress bar
        self.status_label = tk.Label(
            self.loading_frame,
            text="Initializing Neural Networks...",
            font=("Segoe UI", 11),
            fg='#888888',
            bg='#0a0a0a'
        )
        self.status_label.pack(pady=5)
        
        # Animation style indicator
        style_label = tk.Label(
            self.loading_frame,
            text=f"[Sparkle] {self.animation_style.title()} Mode",
            font=("Segoe UI", 9, "italic"),
            fg='#444444',
            bg='#0a0a0a'
        )
        style_label.pack(pady=5)
        
        # Creator label
        creator_label = tk.Label(
            self.loading_frame,
            text="Created by MJP",
            font=("Segoe UI", 9),
            fg='#555555',
            bg='#0a0a0a'
        )
        creator_label.pack(side='bottom', pady=20)
        
        # Start animations
        self._animate_logo()
        self._cycle_capabilities()
        
        # Force update
        self.root.update()
    
    def _draw_animated_logo(self):
        """Draw the animated Monica AI logo based on chosen style."""
        
        self.logo_canvas.delete("all")
        cx, cy = 300, 90
        
        # Call the appropriate animation style
        style = getattr(self, 'animation_style', 'mechanical')
        
        if style == 'mechanical':
            self._draw_mechanical(cx, cy)
        elif style == 'pulse':
            self._draw_pulse(cx, cy)
        elif style == 'wave':
            self._draw_wave(cx, cy)
        elif style == 'matrix':
            self._draw_matrix(cx, cy)
        elif style == 'hologram':
            self._draw_hologram(cx, cy)
        elif style == 'particles':
            self._draw_particles(cx, cy)
        elif style == 'typewriter':
            self._draw_typewriter(cx, cy)
        elif style == 'glitch':
            self._draw_glitch(cx, cy)
        else:
            self._draw_mechanical(cx, cy)
    
    def _draw_mechanical(self, cx, cy):
        """Original mechanical split animation."""
        offset = math.sin(self.animation_frame * 0.1) * 3
        split_offset = abs(math.sin(self.animation_frame * 0.15)) * 5
        
        main_color = '#00ffaa'
        accent_color = '#00ff88'
        
        self.logo_canvas.create_text(cx - 170 - split_offset, cy + offset,
            text='M', font=('Arial Black', 64, 'bold'), fill=main_color, anchor='w')
        self.logo_canvas.create_line(cx - 130, cy - 30, cx - 130, cy + 30, fill=accent_color, width=2)
        self.logo_canvas.create_text(cx - 110, cy, text='onica', font=('Segoe UI', 42), fill='#ffffff', anchor='w')
        self.logo_canvas.create_text(cx + 90, cy - split_offset, text='AI', font=('Arial Black', 50, 'bold'), fill=main_color, anchor='w')
    
    def _draw_pulse(self, cx, cy):
        """Pulsing glow effect."""
        pulse = abs(math.sin(self.animation_frame * 0.08))
        
        for i in range(5, 0, -1):
            alpha = pulse * (0.3 - i * 0.05)
            size = 48 + i * 4
            color = f'#{int(alpha*255):02x}{int(255*alpha):02x}{int(170*alpha):02x}'
            self.logo_canvas.create_text(cx, cy, text='Monica AI', font=('Arial Black', size, 'bold'), fill=color, anchor='center')
        
        main_color = f'#{0:02x}{int(200 + 55*pulse):02x}{int(150 + 50*pulse):02x}'
        self.logo_canvas.create_text(cx, cy, text='Monica AI', font=('Arial Black', 48, 'bold'), fill=main_color, anchor='center')
    
    def _draw_wave(self, cx, cy):
        """Wave motion effect."""
        text = "Monica AI"
        start_x = cx - 150
        
        for i, char in enumerate(text):
            wave_offset = math.sin(self.animation_frame * 0.15 + i * 0.5) * 10
            hue_shift = int(abs(math.sin(self.animation_frame * 0.1 + i * 0.3)) * 50)
            color = f'#00{200 + hue_shift:02x}{150 + hue_shift:02x}'
            self.logo_canvas.create_text(start_x + i * 35, cy + wave_offset, text=char, font=('Arial Black', 48, 'bold'), fill=color, anchor='center')
    
    def _draw_matrix(self, cx, cy):
        """Matrix-style digital rain effect."""
        chars = "01"
        for i in range(15):
            x = random.randint(50, 550)
            y = (self.animation_frame * 3 + i * 40) % 180
            char = random.choice(chars)
            alpha = 1 - (y / 180)
            color = f'#00{int(100 + 100*alpha):02x}{int(50 + 50*alpha):02x}'
            self.logo_canvas.create_text(x, y, text=char, font=('Consolas', 14), fill=color)
        
        self.logo_canvas.create_text(cx, cy, text='Monica AI', font=('Arial Black', 48, 'bold'), fill='#00ff00', anchor='center')
    
    def _draw_hologram(self, cx, cy):
        """Holographic flicker effect."""
        flicker = random.random()
        offset = int(math.sin(self.animation_frame * 0.2) * 3)
        
        # Tkinter doesn't support alpha in hex colors, use solid colors
        if flicker > 0.1:
            self.logo_canvas.create_text(cx - offset, cy, text='Monica AI', font=('Arial Black', 48, 'bold'), fill='#ff3333', anchor='center')
        if flicker > 0.15:
            self.logo_canvas.create_text(cx + offset, cy, text='Monica AI', font=('Arial Black', 48, 'bold'), fill='#3366ff', anchor='center')
        if flicker > 0.05:
            self.logo_canvas.create_text(cx, cy, text='Monica AI', font=('Arial Black', 48, 'bold'), fill='#00ffaa', anchor='center')
        
        for y in range(0, 180, 4):
            if random.random() > 0.7:
                self.logo_canvas.create_line(0, y, 600, y, fill='#004433', width=1)
    
    def _draw_particles(self, cx, cy):
        """Particle burst effect."""
        
        if len(self.particles) < 30:
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(1, 3)
            self.particles.append({'x': cx, 'y': cy, 'vx': math.cos(angle) * speed, 'vy': math.sin(angle) * speed, 'life': 60, 'size': random.randint(2, 5)})
        
        new_particles = []
        for p in self.particles:
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['life'] -= 1
            if p['life'] > 0:
                alpha = p['life'] / 60
                color = f'#00{int(255*alpha):02x}{int(170*alpha):02x}'
                self.logo_canvas.create_oval(p['x'] - p['size'], p['y'] - p['size'], p['x'] + p['size'], p['y'] + p['size'], fill=color, outline='')
                new_particles.append(p)
        self.particles = new_particles
        
        self.logo_canvas.create_text(cx, cy, text='Monica AI', font=('Arial Black', 48, 'bold'), fill='#00ffaa', anchor='center')
    
    def _draw_typewriter(self, cx, cy):
        """Typewriter reveal effect."""
        full_text = "Monica AI"
        if self.animation_frame % 8 == 0:
            self.typewriter_index = (self.typewriter_index + 1) % (len(full_text) + 10)
        
        visible_chars = min(self.typewriter_index, len(full_text))
        visible_text = full_text[:visible_chars]
        
        self.logo_canvas.create_text(cx - 120, cy, text=visible_text, font=('Courier New', 48, 'bold'), fill='#00ffaa', anchor='w')
        
        if self.animation_frame % 20 < 10 and visible_chars < len(full_text):
            cursor_x = cx - 120 + visible_chars * 30
            self.logo_canvas.create_text(cursor_x, cy, text='_', font=('Courier New', 48, 'bold'), fill='#00ffaa', anchor='w')
    
    def _draw_glitch(self, cx, cy):
        """Glitch/distortion effect."""
        glitch = random.random() < 0.15
        
        if glitch:
            for i in range(5):
                y_offset = (i - 2) * 15
                x_offset = random.randint(-20, 20) if random.random() < 0.3 else 0
                colors = ['#00ffaa', '#ff00aa', '#00aaff', '#ffaa00']
                color = random.choice(colors) if random.random() < 0.2 else '#00ffaa'
                self.logo_canvas.create_text(cx + x_offset, cy + y_offset, text='Monica AI', 
                                          font=('Arial Black', 48, 'bold'), fill=color, anchor='center')
        else:
            offset = math.sin(self.animation_frame * 0.1) * 2
            self.logo_canvas.create_text(cx + offset, cy, text='Monica AI', 
                                      font=('Arial Black', 48, 'bold'), fill='#00ffaa', anchor='center')
    
    def _animate_logo(self):
        """Animate the logo."""
        if not hasattr(self, 'loading_frame') or not self.loading_frame.winfo_exists():
            return
        
        self.animation_frame += 1
        self._draw_animated_logo()
        
        # Continue animation
        self.root.after(50, self._animate_logo)
    
    def _cycle_capabilities(self):
        """Cycle through Monica's capabilities."""
        if not hasattr(self, 'loading_frame') or not self.loading_frame.winfo_exists():
            return
        
        capabilities = [
            "Psychology & Behavioral Sciences",
            "Biology & Life Sciences", 
            "Philosophy & Ethics",
            "Complete K-12 Education",
            "60+ Languages",
            "Computer Vision",
            "Real-Time Global Cameras",
            "Advanced Mathematics",
            "Programming & Software",
            "Creative Arts",
            "Medical Knowledge",
            "Counseling & Therapy",
            "Data Analysis",
            "Music Theory",
            "Quantum Physics",
        ]
        
        # Update capability text
        self.capability_label.config(text=capabilities[self.capability_index])
        
        # Next capability
        self.capability_index = (self.capability_index + 1) % len(capabilities)
        
        # Continue cycling
        self.root.after(2000, self._cycle_capabilities)
    
    def _update_loading_status(self, text: str):
        """Update loading status text in a thread-safe manner."""
        if not hasattr(self, 'status_label'):
            return
            
        def update_label():
            if hasattr(self, 'status_label') and self.status_label.winfo_exists():
                self.status_label.config(text=text)
        
        # Schedule the update on the main thread
        self.root.after(0, update_label)
    
    def _init_managers_async(self):
        """Initialize managers in parallel for faster loading."""
        def init_in_thread():
            try:
                total_steps = 5  # Audio, TTS, Camera, AI, Biometric
                completed_steps = 0
                
                def update_progress(step_name):
                    nonlocal completed_steps
                    completed_steps += 1
                    progress_percent = int((completed_steps / total_steps) * 100)
                    
                    if hasattr(self, 'progress') and self.progress.winfo_exists():
                        self.progress['value'] = progress_percent
                    
                    self.root.after(0, lambda: self._update_loading_status(f"Loaded {step_name}"))
                    print(f"  - {step_name} [OK]")
                
                # 1. Initialize Audio Manager (lightweight init)
                print("[INIT] Initializing Audio Manager...")
                self.audio = AudioManager(self.config)
                update_progress("Audio Manager")
                
                # 2. Initialize TTS Manager (lazy load models)
                print("[INIT] Initializing TTS Manager...")
                self.tts = TTSManager(self.config)
                # Wire anti-barge-in: TTS waits for brief silence and stops if user speaks
                try:
                    if self.audio:
                        self.audio.register_tts_manager(self.tts)
                        # CRITICAL: Wire TTS manager to config for echo cancellation
                        self.config.tts_manager = self.tts
                        # CRITICAL: Wire speech recognizer to TTS for echo cancellation
                        # This allows TTS to pause/resume STT during playback
                        if hasattr(self.audio, 'speech_recognizer') and self.audio.speech_recognizer:
                            self.tts.speech_recognizer = self.audio.speech_recognizer
                            print("[INIT] [OK] TTS->STT echo cancellation wired!")
                except Exception as e:
                    print(f"[INIT] Anti-barge-in wiring failed: {e}")
                update_progress("TTS Manager")
                
                # 3. Initialize Camera Manager (lazy load camera)
                print("[INIT] Initializing Camera Manager...")
                from .vision.camera_manager import CameraManager
                self.camera = CameraManager(self.config)
                update_progress("Camera Manager")
                
                # 4. Initialize AI Manager (lazy load models)
                print("[INIT] Initializing AI Manager...")
                self.conversation = ConversationManager(self.config)
                update_progress("AI Manager")

                # 5. Initialize Biometric Detection System
                print("[INIT] Initializing Biometric Detector...")
                try:
                    from .biometric import BiometricDetector
                    self.biometric = BiometricDetector(owner_name="MJP")
                    print("[INIT] Biometric system ready")
                except Exception as bio_err:
                    print(f"[INIT] Biometric initialization failed: {bio_err}")
                    self.biometric = None
                update_progress("Biometric Detector")

                # Signal completion
                self.root.after(0, self._finish_initialization)
                
            except Exception as e:
                print(f"Error during initialization: {e}")
                import traceback
                traceback.print_exc()
                error_msg = str(e)
                self.root.after(0, lambda msg=error_msg: self._show_error(msg))
        
        # Run in background thread
        threading.Thread(target=init_in_thread, daemon=True).start()
    
    def _finish_initialization(self):
        """Finish initialization and show main window with optimized startup."""
        try:
            # Remove loading screen
            if hasattr(self, 'loading_frame'):
                self.loading_frame.destroy()
            
            # Import and create GUI
            from .gui.main_window import MainWindow
            
            print("  - GUI")
            self.main_window = MainWindow(self.root, self)
            
            self._init_complete = True
            
            print("Initialization complete!")
            print("=" * 50)

            # Start camera immediately (no delay needed - camera.start() is already async)
            # Camera initialization happens in background thread (see camera_manager.py:154)
            if self.camera:
                def start_camera_delayed():
                    import time
                    # Minimal delay to let GUI finish rendering (reduced from 3s to 0.2s)
                    time.sleep(0.2)

                    # Update status to show camera is starting
                    if hasattr(self, 'main_window') and self.main_window:
                        self.root.after(0, lambda: self.main_window._update_status("Initializing camera..."))

                    # Start camera in background
                    if self.camera and not self.camera.is_running:
                        self.camera.start()
                        print("[CAMERA] Started (delayed for smooth UI)")

                        # Register biometric detector with camera
                        if self.biometric:
                            try:
                                # CameraManager exposes register_callback(frame_rgb)
                                self.camera.register_callback(self.biometric.process_frame)
                                print("[BIOMETRIC] Connected to camera feed")
                                
                                # Connect biometric results to vision system for overlay display
                                if hasattr(self, 'main_window') and self.main_window and hasattr(self.main_window, 'vision_system'):
                                    def update_vision_overlays(identity_result):
                                        if self.main_window.vision_system:
                                            if identity_result.identified:
                                                self.main_window.vision_system.identity_label = identity_result.identity
                                            else:
                                                self.main_window.vision_system.identity_label = "Unknown"
                                    self.biometric.identity_callbacks.append(update_vision_overlays)
                                    print("[BIOMETRIC] Connected to vision system overlays")
                            except Exception as e:
                                print(f"[BIOMETRIC] Camera connection failed: {e}")

                        # Update status when done
                        if hasattr(self, 'main_window') and self.main_window:
                            self.root.after(0, lambda: self.main_window._update_status("Camera ready"))
                    elif self.camera and self.camera.is_running:
                        print("[CAMERA] Already running")

                # Start in daemon thread so it doesn't block
                threading.Thread(target=start_camera_delayed, daemon=True).start()
                print("[CAMERA] Starting immediately (async background thread)")
            
            # Only register callback, don't auto-start listening
            if self.audio:
                self.audio.register_speech_callback(self._handle_speech_result)
                print("[AUDIO] Speech callback registered (manual start required)")
            
            print("\nMonica AI is ready!")
            print("- Say 'Monica initialize' to start")
            print("- Or click 'Start Listening' to use voice input")
            print("- Type in the text box and press Enter to chat")
            
        except Exception as e:
            print(f"Error finishing initialization: {e}")
            self._show_error(str(e))
    
    def _handle_speech_result(self, result):
        """Handle speech recognition results."""
        # Handle both string (Google STT) and object (SpeechBrain) results
        if isinstance(result, str):
            text = result
            is_final = True
        elif hasattr(result, 'text'):
            text = result.text
            is_final = getattr(result, 'is_final', True)
        else:
            return
        
        if not text:
            return

        print(f"[SPEECH] {text}")
        
        # Check for stop command
        text_lower = text.lower()
        if 'stop' in text_lower and len(text_lower) < 20:
            if self.audio and self.audio.is_listening:
                self.audio.stop_speech_recognition()
                print("Stopped listening due to stop command")
                
                # Update UI if needed
                if hasattr(self, 'main_window') and self.main_window:
                    self.root.after(0, lambda: self.main_window.update_ui_state())
            return
        
        # Delegate to main window for processing (it checks activation)
        if hasattr(self, 'main_window') and self.main_window and is_final:
            # Create a simple result object for compatibility
            class SpeechResult:
                def __init__(self, txt):
                    self.text = txt
                    self.is_final = True
            self.root.after(0, lambda: self.main_window._on_speech_recognized(SpeechResult(text)))

    def _show_error(self, message: str):
        """Show error message."""
        if hasattr(self, 'loading_frame') and self.loading_frame.winfo_exists():
            self.loading_frame.destroy()
            
        error_frame = tk.Frame(self.root, bg='#1e1e1e')
        error_frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(
            error_frame,
            text="Initialization Error",
            font=('Segoe UI', 24, 'bold'),
            fg='#ff4d4d',
            bg='#1e1e1e'
        ).pack(pady=(100, 20))
        
        tk.Label(
            error_frame,
            text=message,
            font=('Segoe UI', 12),
            fg='#ffffff',
            bg='#1e1e1e',
            wraplength=600,
            justify='center'
        ).pack(pady=(0, 30))
        
        tk.Button(
            error_frame,
            text="Exit",
            command=self.root.quit,
            font=('Segoe UI', 12, 'bold'),
            bg='#ff4d4d',
            fg='white',
            bd=0,
            padx=20,
            pady=10,
            activebackground='#ff6666',
            activeforeground='white'
        ).pack(pady=20)

    def run(self):
        """Run the application."""
        # Run main loop
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            print("\nInterrupted by user")
            self.on_close()
    
    def on_close(self):
        """Handle application close."""
        print("\nShutting down Monica AI...")
        
        # Stop all managers
        if self.audio:
            print("  - Stopping audio...")
            self.audio.stop()

        if self.camera:
            print("  - Stopping camera...")
            self.camera.stop()
        
        if self.tts:
            print("  - Stopping TTS...")
            self.tts.stop()
        
        # Save configuration
        print("  - Saving configuration...")
        self.config.save()
        
        # Destroy window
        print("  - Closing window...")
        self.root.destroy()
        
        print("Goodbye!")
        sys.exit(0)


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Monica AI - Your AI Assistant")
    parser.add_argument("--config", type=str, help="Path to configuration file")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    
    args = parser.parse_args()
    
    if args.debug:
        import logging
        import sys
        logging.basicConfig(
            level=logging.DEBUG,
            handlers=[logging.StreamHandler(stream=sys.stdout)]
        )
    
    # Create and run application
    config_path = Path(args.config) if args.config else None
    app = MonicaAI(config_path)
    app.run()


if __name__ == "__main__":
    main()
