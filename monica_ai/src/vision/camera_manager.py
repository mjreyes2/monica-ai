"""
Camera Manager for Monica AI.
Handles camera capture, processing, and Spout output for OBS integration.
"""
import cv2
import numpy as np
import threading
import time
import os
import sys
from typing import Optional, Callable, List, Dict, Any, Tuple
from dataclasses import dataclass

# Suppress NVIDIA VCAMDS error messages
os.environ['OPENCV_LOG_LEVEL'] = 'ERROR'
os.environ['CUDA_LOG_LEVEL'] = 'ERROR'

# Suppress Windows error dialog for null pointer access
import ctypes
try:
    kernel32 = ctypes.windll.kernel32
    # SEM_FAILCRITICALERRORS | SEM_NOGPFAULTERRORBOX | SEM_NOOPENFILEERRORBOX
    kernel32.SetErrorMode(0x0001 | 0x0002 | 0x8000)
except Exception:
    pass

# Try to import Spout
try:
    import SpoutGL
    from OpenGL import GL
    SPOUT_AVAILABLE = True
except ImportError:
    SPOUT_AVAILABLE = False
    GL = None
    print("SpoutGL not available. OBS Spout output will be disabled.")


@dataclass
class CameraInfo:
    """Information about a camera device."""
    index: int
    name: str
    width: int
    height: int
    fps: float
    backend: str


class CameraManager:
    """
    Manages camera capture and video processing for Monica AI.
    
    Features:
    - Multiple camera support
    - Resolution and FPS control
    - Frame callbacks for processing
    - Spout output for OBS integration
    - Thread-safe frame access
    """
    
    def __init__(self, config):
        """
        Initialize the camera manager.
        
        Args:
            config: Application configuration object
        """
        self.config = config
        
        # Camera state
        self.camera = None
        self.camera_index = config.CAMERA_INDEX
        self.width = config.CAMERA_WIDTH
        self.height = config.CAMERA_HEIGHT
        self.target_fps = config.TARGET_FPS
        
        # Frame storage
        self.current_frame = None
        self.frame_lock = threading.Lock()
        self.frame_count = 0
        self.actual_fps = 0.0
        
        # Capture thread
        self.is_running = False
        self.stop_event = threading.Event()
        self.capture_thread = None
        
        # Callbacks
        self.frame_callbacks: List[Callable[[np.ndarray], None]] = []
        
        # Spout output
        self.spout_enabled = config.SPOUT_ENABLED and SPOUT_AVAILABLE
        self.spout_sender = None
        self.spout_name = config.SPOUT_NAME
        
        if self.spout_enabled:
            self._init_spout()
    
    def _init_spout(self):
        """Initialize Spout sender for OBS integration."""
        if not SPOUT_AVAILABLE:
            print("[SPOUT] SpoutGL not available")
            return
        
        try:
            self.spout_sender = SpoutGL.SpoutSender()
            # CRITICAL: Create sender with dimensions FIRST before setting name
            # This is required for OBS to see the sender
            success = self.spout_sender.setSenderName(self.spout_name)
            print(f"[SPOUT] Sender '{self.spout_name}' initialized: {success}")
            print(f"[SPOUT] Ready to send {self.width}x{self.height} frames")
        except Exception as e:
            print(f"[SPOUT] Error initializing: {e}")
            import traceback
            traceback.print_exc()
            self.spout_enabled = False
    
    # ==================== Camera Control ====================
    
    def start(self) -> bool:
        """Start camera capture in background to prevent UI freeze."""
        if self.is_running:
            return True
        
        # Start camera initialization in a separate thread to prevent UI freeze
        def _start_camera_async():
            # Open camera
            if not self._open_camera():
                return

            # No warm-up needed - modern cameras are ready immediately
            # Removed warm-up to improve startup speed

            # Start capture thread
            self.is_running = True
            self.stop_event.clear()
            
            self.capture_thread = threading.Thread(
                target=self._capture_loop,
                daemon=True
            )
            self.capture_thread.start()
            
            print(f"[CAMERA] Started: {self.width}x{self.height} @ {self.target_fps}fps")
        
        # Run camera startup in background thread
        threading.Thread(target=_start_camera_async, daemon=True).start()
        return True
    
    def stop(self):
        """Stop camera capture."""
        if not self.is_running:
            return
        
        self.is_running = False
        self.stop_event.set()
        
        # Wait for thread to finish
        if self.capture_thread and self.capture_thread.is_alive():
            self.capture_thread.join(timeout=2.0)
        
        # Release camera
        if self.camera:
            self.camera.release()
            self.camera = None
        
        # Release Spout
        if self.spout_sender:
            self.spout_sender.releaseSender()
            self.spout_sender = None
        
        print("Camera stopped")
    
    def _open_camera(self) -> bool:
        """Open the camera device with optimized settings."""
        try:
            print(f"[CAMERA] Opening camera {self.camera_index}...")
            start_time = time.time()
            
            # Skip MSMF to avoid NVIDIA VCAMDS conflicts
            # Try DirectShow first (more stable with NVIDIA drivers)
            print("[CAMERA] Using DirectShow to avoid NVIDIA VCAMDS conflicts...")
            self.camera = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
            
            if not self.camera.isOpened():
                # Try MSMF as fallback
                print("[CAMERA] DirectShow failed, trying MSMF...")
                self.camera = cv2.VideoCapture(self.camera_index, cv2.CAP_MSMF)
            
            if not self.camera.isOpened():
                # Last resort: try default backend
                print("[CAMERA] Both DirectShow and MSMF failed, trying default backend...")
                self.camera = cv2.VideoCapture(self.camera_index)
            
            if not self.camera.isOpened():
                print(f"[CAMERA] Failed to open camera {self.camera_index}")
                return False
            
            print(f"[CAMERA] Camera opened in {time.time() - start_time:.2f}s")
            
            # Set camera properties BEFORE reading frames for better performance
            # Set buffer size FIRST to minimize latency
            self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            # Use MJPG codec for faster frame transfer
            self.camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
            
            # Set resolution and FPS
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self.camera.set(cv2.CAP_PROP_FPS, self.target_fps)
            
            # Get actual settings
            actual_width = int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
            actual_fps = self.camera.get(cv2.CAP_PROP_FPS)
            
            # Update our stored dimensions to match actual
            self.width = actual_width
            self.height = actual_height
            
            print(f"Camera opened: {actual_width}x{actual_height} @ {actual_fps}fps")
            
            return True
            
        except Exception as e:
            print(f"Error opening camera: {e}")
            return False
    
    def _reopen_camera(self) -> bool:
        """Safely reopen camera after error (e.g., NVIDIA VCAMDS null pointer)."""
        try:
            # Release existing camera if any
            if self.camera is not None:
                try:
                    self.camera.release()
                except Exception:
                    pass
                self.camera = None
            
            # Brief delay to let driver recover
            time.sleep(0.2)
            
            # Reopen camera
            print("[CAMERA] Reopening camera after error...")
            return self._open_camera()
            
        except Exception as e:
            print(f"[CAMERA] Failed to reopen camera: {e}")
            return False
    
    def _capture_loop(self):
        """Main capture loop."""
        last_time = time.time()
        frame_times = []
        first_frame_logged = False
        consecutive_failures = 0
        max_consecutive_failures = 10
        
        while not self.stop_event.is_set():
            try:
                # Capture frame directly with read() (more reliable than grab/retrieve)
                ret, frame = None, None
                try:
                    # Check if camera is still valid before reading
                    if self.camera is None or not self.camera.isOpened():
                        print("[CAMERA] Camera became invalid, attempting to reopen...")
                        if not self._reopen_camera():
                            time.sleep(1.0)
                            continue
                    
                    ret, frame = self.camera.read()
                    consecutive_failures = 0  # Reset on success
                except (cv2.error, Exception) as e:
                    consecutive_failures += 1
                    error_str = str(e).lower()
                    
                    # Check for null pointer / memory access errors from NVIDIA VCAMDS
                    if 'memory' in error_str or 'null' in error_str or 'access' in error_str:
                        print(f"[CAMERA] NVIDIA VCAMDS memory error detected, reopening camera...")
                        if self._reopen_camera():
                            consecutive_failures = 0
                        else:
                            time.sleep(1.0)
                        continue
                    
                    if not first_frame_logged:
                        print(f"[CAMERA] Read exception: {e}")
                    
                    if consecutive_failures >= max_consecutive_failures:
                        print(f"[CAMERA] Too many failures ({consecutive_failures}), reopening camera...")
                        if self._reopen_camera():
                            consecutive_failures = 0
                        else:
                            time.sleep(1.0)
                    else:
                        time.sleep(0.05)
                    continue
                
                if not ret or frame is None:
                    consecutive_failures += 1
                    if not first_frame_logged:
                        print(f"[CAMERA] Read failed (ret={ret}, frame is None={frame is None})")
                    
                    if consecutive_failures >= max_consecutive_failures:
                        print(f"[CAMERA] Too many read failures, reopening camera...")
                        if self._reopen_camera():
                            consecutive_failures = 0
                        else:
                            time.sleep(1.0)
                    else:
                        time.sleep(0.01)
                    continue
                
                if not first_frame_logged:
                    print(f"[CAMERA] First frame captured successfully! Shape: {frame.shape}")
                    first_frame_logged = True
                
                # Convert BGR to RGB - wrap in try/except to handle GIL issues
                try:
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                except Exception:
                    time.sleep(0.01)
                    continue
                
                # Store frame
                with self.frame_lock:
                    self.current_frame = frame_rgb
                    self.frame_count += 1
                
                # Calculate FPS
                current_time = time.time()
                frame_times.append(current_time - last_time)
                last_time = current_time
                
                # Keep only last 30 frame times
                if len(frame_times) > 30:
                    frame_times.pop(0)
                
                if frame_times:
                    self.actual_fps = 1.0 / (sum(frame_times) / len(frame_times))
                
                # NOTE: Spout sending is now handled in GUI after AR effects are applied
                # This ensures OBS receives frames WITH holograms, not just raw camera
                # The raw frame sending here is disabled to avoid duplicate/conflicting sends
                
                # Notify callbacks - OPTIMIZED: Process every frame for no lag
                if self.frame_callbacks:
                    for callback in self.frame_callbacks:
                        try:
                            callback(frame_rgb)
                        except Exception as e:
                            print(f"Error in frame callback: {e}")
                
                # Don't sleep - capture as fast as camera allows
                
            except Exception as e:
                print(f"Error in capture loop: {e}")
                time.sleep(0.1)
    
    def send_to_spout(self, frame: np.ndarray):
        """Send frame to Spout for OBS. Public method for external use."""
        try:
            if not self.spout_enabled or not self.spout_sender:
                return
            
            # Spout expects BGRA format
            if len(frame.shape) == 2:
                # Grayscale - convert to BGRA
                frame_bgra = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGRA)
            elif frame.shape[2] == 3:
                frame_bgra = cv2.cvtColor(frame, cv2.COLOR_BGR2BGRA)
            else:
                frame_bgra = frame
            
            # Ensure frame is contiguous
            frame_bgra = np.ascontiguousarray(frame_bgra)
            h, w = frame_bgra.shape[:2]
            
            # Send frame using sendImage with proper parameters
            # SpoutGL.sendImage(data, width, height, GL_format, invert, hostFBO)
            # CRITICAL: Use GL_RGBA instead of GL_BGRA to fix color inversion
            # Convert BGR to RGB first
            frame_rgba = cv2.cvtColor(frame_bgra, cv2.COLOR_BGRA2RGBA)
            frame_rgba = np.ascontiguousarray(frame_rgba)
            
            result = self.spout_sender.sendImage(
                frame_rgba.tobytes(),
                w,
                h,
                GL.GL_RGBA,
                False,
                0
            )
            
            # Log first successful send
            if not hasattr(self, '_spout_first_send') and result:
                print(f"[SPOUT] First frame sent successfully: {w}x{h}")
                self._spout_first_send = True
            
        except Exception as e:
            if not hasattr(self, '_spout_error_logged'):
                print(f"[SPOUT] Send error: {e}")
                import traceback
                traceback.print_exc()
                self._spout_error_logged = True
    
    # ==================== Frame Access ====================
    
    def get_frame(self) -> Optional[np.ndarray]:
        """Get the current camera frame (RGB format)."""
        with self.frame_lock:
            if self.current_frame is not None:
                return self.current_frame.copy()
            return None
    
    def get_frame_bgr(self) -> Optional[np.ndarray]:
        """Get the current camera frame in BGR format."""
        frame = self.get_frame()
        if frame is not None:
            return cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        return None
    
    def get_fps(self) -> float:
        """Get actual capture FPS."""
        return self.actual_fps
    
    def get_frame_count(self) -> int:
        """Get total frames captured."""
        return self.frame_count
    
    # ==================== Camera Settings ====================
    
    def set_camera(self, camera_index: int) -> bool:
        """Change the camera device."""
        was_running = self.is_running
        
        if was_running:
            self.stop()
        
        self.camera_index = camera_index
        
        if was_running:
            return self.start()
        
        return True
    
    def set_resolution(self, width: int, height: int) -> bool:
        """Set camera resolution."""
        was_running = self.is_running
        
        if was_running:
            self.stop()
        
        self.width = width
        self.height = height
        
        if was_running:
            return self.start()
        
        return True
    
    def set_fps(self, fps: int):
        """Set target FPS."""
        self.target_fps = fps
        
        if self.camera:
            self.camera.set(cv2.CAP_PROP_FPS, fps)
    
    # ==================== Device Enumeration ====================
    
    def list_cameras(self) -> List[CameraInfo]:
        """List available camera devices."""
        cameras = []
        
        # Known camera names (Windows device names)
        # We'll try to get the actual name if possible
        
        # Check multiple indices
        for i in range(10):
            cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
            
            if cap.isOpened():
                # Try to set HD resolution to see if camera supports it
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
                
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fps = cap.get(cv2.CAP_PROP_FPS)
                
                # Determine camera type based on capabilities
                if width >= 1920:
                    name = f"Camera {i} (HD 1080p)"
                elif width >= 1280:
                    name = f"Camera {i} (HD 720p)"
                else:
                    name = f"Camera {i} (SD {width}x{height})"
                
                cameras.append(CameraInfo(
                    index=i,
                    name=name,
                    width=width,
                    height=height,
                    fps=fps,
                    backend="DirectShow"
                ))
                
                cap.release()
        
        return cameras
    
    def get_supported_resolutions(self) -> List[Tuple[int, int]]:
        """Get list of common supported resolutions."""
        return [
            (640, 480),
            (800, 600),
            (1280, 720),
            (1920, 1080),
            (2560, 1440),
            (3840, 2160)
        ]
    
    # ==================== Spout Control ====================
    
    def enable_spout(self, name: str = None) -> bool:
        """Enable Spout output for OBS."""
        if not SPOUT_AVAILABLE:
            print("Spout not available")
            return False
        
        if name:
            self.spout_name = name
        
        self._init_spout()
        self.spout_enabled = self.spout_sender is not None
        
        return self.spout_enabled
    
    def disable_spout(self):
        """Disable Spout output."""
        if self.spout_sender:
            self.spout_sender.releaseSender()
            self.spout_sender = None
        
        self.spout_enabled = False
    
    def is_spout_enabled(self) -> bool:
        """Check if Spout is enabled."""
        return self.spout_enabled
    
    # ==================== Callbacks ====================
    
    def register_callback(self, callback: Callable[[np.ndarray], None]):
        """Register callback for new frames."""
        if callback not in self.frame_callbacks:
            self.frame_callbacks.append(callback)
    
    def unregister_callback(self, callback: Callable[[np.ndarray], None]):
        """Unregister frame callback."""
        if callback in self.frame_callbacks:
            self.frame_callbacks.remove(callback)
