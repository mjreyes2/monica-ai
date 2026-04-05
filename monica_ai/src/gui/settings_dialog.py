"""
Settings Dialog for Monica AI.
Allows configuration of audio/video devices and other settings.
"""
import tkinter as tk
from tkinter import ttk
from typing import Optional, Dict, Any, List


class SettingsDialog:
    """Settings dialog for Monica AI configuration."""
    
    def __init__(self, parent, app):
        """
        Initialize the settings dialog.
        
        Args:
            parent: Parent window
            app: Main application instance
        """
        self.parent = parent
        self.app = app
        self.config = app.config
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Monica AI Settings")
        self.dialog.geometry("500x600")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center on parent
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 500) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 600) // 2
        self.dialog.geometry(f"+{x}+{y}")
        
        # Style
        self.dialog.configure(bg='#1e1e1e')
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.dialog)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create tabs
        self._create_audio_tab()
        self._create_video_tab()
        self._create_ai_tab()
        self._create_voice_tab()
        
        # Buttons
        self._create_buttons()
        
        # Load current settings
        self._load_settings()
    
    def _create_audio_tab(self):
        """Create audio settings tab."""
        frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(frame, text="Audio")
        
        # Input device
        ttk.Label(frame, text="Input Device (Microphone):").pack(anchor=tk.W, pady=(0, 5))
        
        self.input_device_var = tk.StringVar()
        self.input_device_combo = ttk.Combobox(
            frame,
            textvariable=self.input_device_var,
            state='readonly',
            width=50
        )
        self.input_device_combo.pack(fill=tk.X, pady=(0, 15))
        
        # Populate input devices
        input_devices = self.app.audio.list_input_devices() if self.app.audio else []
        self.input_devices = input_devices
        self.input_device_combo['values'] = [d['name'] for d in input_devices]
        
        # Output device
        ttk.Label(frame, text="Output Device (Speakers):").pack(anchor=tk.W, pady=(0, 5))
        
        self.output_device_var = tk.StringVar()
        self.output_device_combo = ttk.Combobox(
            frame,
            textvariable=self.output_device_var,
            state='readonly',
            width=50
        )
        self.output_device_combo.pack(fill=tk.X, pady=(0, 15))
        
        # Populate output devices
        output_devices = self.app.audio.list_output_devices() if self.app.audio else []
        self.output_devices = output_devices
        self.output_device_combo['values'] = [d['name'] for d in output_devices]
        
        # Sample rate
        ttk.Label(frame, text="Sample Rate:").pack(anchor=tk.W, pady=(0, 5))
        
        self.sample_rate_var = tk.StringVar()
        sample_rate_combo = ttk.Combobox(
            frame,
            textvariable=self.sample_rate_var,
            state='readonly',
            values=['16000', '22050', '44100', '48000'],
            width=20
        )
        sample_rate_combo.pack(anchor=tk.W, pady=(0, 15))
        
        # Energy threshold
        ttk.Label(frame, text="Voice Detection Sensitivity:").pack(anchor=tk.W, pady=(0, 5))
        
        self.energy_var = tk.DoubleVar()
        energy_scale = ttk.Scale(
            frame,
            from_=0.01,
            to=0.1,
            variable=self.energy_var,
            orient=tk.HORIZONTAL,
            length=300
        )
        energy_scale.pack(anchor=tk.W, pady=(0, 5))
        ttk.Label(frame, text="(Lower = more sensitive, Higher = less background noise)").pack(anchor=tk.W)
    
    def _create_video_tab(self):
        """Create video settings tab."""
        frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(frame, text="Video")
        
        # Camera selection
        ttk.Label(frame, text="Camera:").pack(anchor=tk.W, pady=(0, 5))
        
        self.camera_var = tk.StringVar()
        self.camera_combo = ttk.Combobox(
            frame,
            textvariable=self.camera_var,
            state='readonly',
            width=50
        )
        self.camera_combo.pack(fill=tk.X, pady=(0, 15))
        
        # Populate cameras
        cameras = self.app.camera.list_cameras() if self.app.camera else []
        self.cameras = cameras
        self.camera_combo['values'] = [f"{c.index}: {c.name} ({c.width}x{c.height})" for c in cameras]
        
        # Resolution
        ttk.Label(frame, text="Resolution:").pack(anchor=tk.W, pady=(0, 5))
        
        self.resolution_var = tk.StringVar()
        resolution_combo = ttk.Combobox(
            frame,
            textvariable=self.resolution_var,
            state='readonly',
            values=['640x480', '1280x720', '1920x1080'],
            width=20
        )
        resolution_combo.pack(anchor=tk.W, pady=(0, 15))
        
        # FPS
        ttk.Label(frame, text="Target FPS:").pack(anchor=tk.W, pady=(0, 5))
        
        self.fps_var = tk.StringVar()
        fps_combo = ttk.Combobox(
            frame,
            textvariable=self.fps_var,
            state='readonly',
            values=['15', '24', '30', '60'],
            width=20
        )
        fps_combo.pack(anchor=tk.W, pady=(0, 15))
        
        # Spout
        self.spout_var = tk.BooleanVar()
        spout_check = ttk.Checkbutton(
            frame,
            text="Enable Spout Output (for OBS)",
            variable=self.spout_var
        )
        spout_check.pack(anchor=tk.W, pady=(0, 15))
    
    def _create_ai_tab(self):
        """Create AI settings tab."""
        frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(frame, text="AI")
        
        # AI Model
        ttk.Label(frame, text="AI Model:").pack(anchor=tk.W, pady=(0, 5))
        
        self.ai_model_var = tk.StringVar()
        ai_model_combo = ttk.Combobox(
            frame,
            textvariable=self.ai_model_var,
            values=['llama3.2', 'llama3.1', 'mistral', 'mixtral', 'phi3', 'gemma2'],
            width=30
        )
        ai_model_combo.pack(anchor=tk.W, pady=(0, 15))
        
        # Speech recognition engine (SpeechBrain only)
        ttk.Label(frame, text="Speech Recognition: SpeechBrain (personalized)").pack(anchor=tk.W, pady=(0, 15))
        
        # Temperature
        ttk.Label(frame, text="AI Temperature:").pack(anchor=tk.W, pady=(15, 5))
        
        self.temp_var = tk.DoubleVar()
        temp_scale = ttk.Scale(
            frame,
            from_=0.0,
            to=1.0,
            variable=self.temp_var,
            orient=tk.HORIZONTAL,
            length=300
        )
        temp_scale.pack(anchor=tk.W, pady=(0, 5))
        ttk.Label(frame, text="(Lower = more focused, Higher = more creative)").pack(anchor=tk.W)
        
        # Wake word
        ttk.Label(frame, text="Wake Word:").pack(anchor=tk.W, pady=(15, 5))
        
        self.wake_word_var = tk.StringVar()
        wake_word_entry = ttk.Entry(frame, textvariable=self.wake_word_var, width=30)
        wake_word_entry.pack(anchor=tk.W, pady=(0, 15))
    
    def _create_voice_tab(self):
        """Create voice/TTS settings tab."""
        frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(frame, text="Voice")
        
        # Voice model
        ttk.Label(frame, text="Voice Model:").pack(anchor=tk.W, pady=(0, 5))
        
        self.voice_var = tk.StringVar()
        voice_combo = ttk.Combobox(
            frame,
            textvariable=self.voice_var,
            state='readonly',
            values=[
                'en_US-amy-medium (Female, Warm)',
                'en_US-lessac-medium (Female, Clear)',
                'en_US-libritts_r-medium (Multi-speaker)',
                'en_GB-alba-medium (British Female)',
            ],
            width=40
        )
        voice_combo.pack(anchor=tk.W, pady=(0, 15))
        
        # Speech speed
        ttk.Label(frame, text="Speech Speed:").pack(anchor=tk.W, pady=(0, 5))
        
        self.speed_var = tk.DoubleVar()
        speed_scale = ttk.Scale(
            frame,
            from_=0.5,
            to=2.0,
            variable=self.speed_var,
            orient=tk.HORIZONTAL,
            length=300
        )
        speed_scale.pack(anchor=tk.W, pady=(0, 5))
        ttk.Label(frame, text="(0.5 = slow, 1.0 = normal, 2.0 = fast)").pack(anchor=tk.W)
        
        # Pause threshold
        ttk.Label(frame, text="Pause Before Response (seconds):").pack(anchor=tk.W, pady=(15, 5))
        
        self.pause_var = tk.DoubleVar()
        pause_scale = ttk.Scale(
            frame,
            from_=0.5,
            to=3.0,
            variable=self.pause_var,
            orient=tk.HORIZONTAL,
            length=300
        )
        pause_scale.pack(anchor=tk.W, pady=(0, 5))
        ttk.Label(frame, text="(How long to wait after you stop speaking)").pack(anchor=tk.W)
    
    def _create_buttons(self):
        """Create dialog buttons."""
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(
            button_frame,
            text="Save",
            command=self._save_settings
        ).pack(side=tk.RIGHT, padx=(5, 0))
        
        ttk.Button(
            button_frame,
            text="Cancel",
            command=self.dialog.destroy
        ).pack(side=tk.RIGHT)
        
        ttk.Button(
            button_frame,
            text="Apply",
            command=self._apply_settings
        ).pack(side=tk.RIGHT, padx=(0, 5))
    
    def _load_settings(self):
        """Load current settings into the dialog."""
        # Audio
        self.sample_rate_var.set(str(self.config.SAMPLE_RATE))
        self.energy_var.set(self.config.ENERGY_THRESHOLD)
        
        # Try to select current input device
        if self.input_devices:
            current_input = self.config.get('input_device_index', 0)
            if current_input < len(self.input_devices):
                self.input_device_combo.current(current_input)
            else:
                self.input_device_combo.current(0)
        
        # Try to select current output device
        if self.output_devices:
            current_output = self.config.get('output_device_index', 0)
            if current_output < len(self.output_devices):
                self.output_device_combo.current(current_output)
            else:
                self.output_device_combo.current(0)
        
        # Video
        if self.cameras:
            current_cam = self.config.CAMERA_INDEX
            for i, cam in enumerate(self.cameras):
                if cam.index == current_cam:
                    self.camera_combo.current(i)
                    break
            else:
                self.camera_combo.current(0)
        
        self.resolution_var.set(f"{self.config.CAMERA_WIDTH}x{self.config.CAMERA_HEIGHT}")
        self.fps_var.set(str(self.config.TARGET_FPS))
        self.spout_var.set(self.config.SPOUT_ENABLED)
        
        # AI
        self.ai_model_var.set(self.config.AI_MODEL)
        self.temp_var.set(self.config.AI_TEMPERATURE)
        self.wake_word_var.set(self.config.WAKE_WORD)
        
        # Voice
        voice_model = self.config.DEFAULT_VOICE_MODEL
        for i, v in enumerate(self.voice_var.master.children.get('!combobox', self.voice_var)['values'] if hasattr(self.voice_var, 'master') else []):
            if voice_model in str(v):
                self.voice_var.set(v)
                break
        else:
            self.voice_var.set('en_US-amy-medium (Female, Warm)')
        
        self.speed_var.set(self.config.TTS_SPEED)
        self.pause_var.set(self.config.PAUSE_THRESHOLD)
    
    def _apply_settings(self):
        """Apply settings without closing."""
        try:
            # Audio device selection
            input_idx = self.input_device_combo.current()
            if input_idx >= 0 and self.input_devices:
                device_id = self.input_devices[input_idx].get('index', input_idx)
                if self.app.audio:
                    self.app.audio.set_input_device(device_id)
                    print(f"Input device set to: {self.input_devices[input_idx]['name']}")
            
            output_idx = self.output_device_combo.current()
            if output_idx >= 0 and self.output_devices:
                device_id = self.output_devices[output_idx].get('index', output_idx)
                if self.app.audio:
                    self.app.audio.set_output_device(device_id)
                    print(f"Output device set to: {self.output_devices[output_idx]['name']}")
            
            # Camera
            cam_idx = self.camera_combo.current()
            if cam_idx >= 0 and self.cameras:
                cam = self.cameras[cam_idx]
                if self.app.camera and self.app.camera.camera_index != cam.index:
                    self.app.camera.stop()
                    self.app.camera.camera_index = cam.index
                    self.app.camera.start()
                    print(f"Camera changed to: {cam.name}")
            
            # Resolution
            res = self.resolution_var.get().split('x')
            if len(res) == 2:
                self.config.CAMERA_WIDTH = int(res[0])
                self.config.CAMERA_HEIGHT = int(res[1])
            
            # Other settings
            self.config.TARGET_FPS = int(self.fps_var.get())
            self.config.SAMPLE_RATE = int(self.sample_rate_var.get())
            self.config.ENERGY_THRESHOLD = self.energy_var.get()
            self.config.AI_MODEL = self.ai_model_var.get()
            self.config.WHISPER_MODEL_SIZE = self.whisper_var.get()
            self.config.AI_TEMPERATURE = self.temp_var.get()
            self.config.WAKE_WORD = self.wake_word_var.get()
            self.config.TTS_SPEED = self.speed_var.get()
            self.config.PAUSE_THRESHOLD = self.pause_var.get()
            self.config.SPOUT_ENABLED = self.spout_var.get()
            
            # Voice model
            voice_selection = self.voice_var.get()
            if 'amy' in voice_selection.lower():
                self.config.DEFAULT_VOICE_MODEL = 'en_US-amy-medium'
            elif 'lessac' in voice_selection.lower():
                self.config.DEFAULT_VOICE_MODEL = 'en_US-lessac-medium'
            elif 'libritts' in voice_selection.lower():
                self.config.DEFAULT_VOICE_MODEL = 'en_US-libritts_r-medium'
            elif 'alba' in voice_selection.lower():
                self.config.DEFAULT_VOICE_MODEL = 'en_GB-alba-medium'
            
            print("Settings applied!")
            
        except Exception as e:
            print(f"Error applying settings: {e}")
            import traceback
            traceback.print_exc()
    
    def _save_settings(self):
        """Save settings and close."""
        self._apply_settings()
        
        # Save to config file
        try:
            self.config.save()
            print("Settings saved to config file")
        except Exception as e:
            print(f"Error saving config: {e}")
        
        self.dialog.destroy()
