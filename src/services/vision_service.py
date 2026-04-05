"""
Vision Service for Monica AI.
Integrates camera capture, face detection, biometrics, hand tracking,
and globe overlay into a unified vision pipeline.
"""

import threading
import time
import logging
import cv2
import numpy as np
from typing import Optional, Callable, List, Dict, Any, Tuple

logger = logging.getLogger("Monica.Vision")


class VisionService:
    """
    Unified vision service combining:
    - Camera capture (via CameraManager)
    - Face detection (Haar cascade + optional DeepFace)
    - Biometric analysis (emotion, age, identity, heartbeat)
    - Hand detection with fingertip tracking (MediaPipe)
    - Globe overlay rendered next to the user in the video feed
    
    The processed frame (with all overlays) is published to shared state
    so the GUI service can display it.
    """

    def __init__(self, orchestrator, config: dict = None):
        self.orchestrator = orchestrator
        self.config = config or {}
        
        # State
        self.is_initialized = False
        self.is_running = False
        self.stop_event = threading.Event()
        
        # Sub-systems (lazy-loaded)
        self.camera_manager = None
        self.vision_system = None
        self.biometric_detector = None
        self.hand_controller = None
        self.globe_renderer = None
        
        # Current processed frame
        self.current_frame = None
        self.frame_lock = threading.Lock()
        
        # Globe settings
        self.globe_enabled = False
        self.globe_size = 180  # pixels
        self.globe_rotation = 0.0
        
        # Globe location features
        self._user_lat = None
        self._user_lng = None
        self._user_city = None
        self._highlight_lat = None
        self._highlight_lng = None
        self._highlight_name = None
        self._highlight_time = 0  # when highlight was set
        self._rotation_paused_until = 0  # pause auto-rotation until this time
        self._user_location_fetched = False
        
        # Camera is OFF by default — user clicks Camera button to start
        self.camera_active = False
        
        logger.info("Vision Service created")

    def initialize(self):
        """Initialize all vision sub-systems."""
        logger.info("Initializing vision sub-systems...")
        
        # 1. Camera Manager — created but NOT started (user clicks Camera button)
        try:
            from vision.camera_manager import CameraManager
            from config.settings import config as app_config
            self.camera_manager = CameraManager(app_config)
            # Do NOT call .start() here — camera starts on-demand via start_camera()
            logger.info("  [OK] Camera Manager created (not started — click Camera button)")
        except Exception as e:
            logger.error(f"  [FAIL] Camera Manager: {e}")
        
        # 2. Vision System (face, hands, pose, emotion)
        try:
            from vision.vision_system import MonicaVisionSystem
            self.vision_system = MonicaVisionSystem()
            logger.info("  [OK] Vision System created (lazy-loads on first frame)")
        except Exception as e:
            logger.error(f"  [FAIL] Vision System: {e}")
        
        # 3. Biometric Detector
        try:
            from biometric.biometric_detector import BiometricDetector
            self.biometric_detector = BiometricDetector(owner_name="MJP")
            logger.info("  [OK] Biometric Detector ready")
        except Exception as e:
            logger.warning(f"  [SKIP] Biometric Detector: {e}")
        
        # 4. Hand Controller (fingertip precision for virtual keyboard)
        try:
            from vision.monica_hand_controller import MonicaHandController
            self.hand_controller = MonicaHandController()
            logger.info("  [OK] Hand Controller ready (fingertip tracking)")
        except Exception as e:
            logger.warning(f"  [SKIP] Hand Controller: {e}")
        
        # 5. Globe Renderer (enhanced — NASA texture + live data overlays)
        try:
            from ui.enhanced_globe import get_enhanced_globe
            self.globe_renderer = get_enhanced_globe(size=self.globe_size)
            logger.info("  [OK] Enhanced Globe Renderer ready (texture + live data)")
        except Exception as e:
            logger.warning(f"  [SKIP] Enhanced Globe: {e}")
            # Fallback to old renderer
            try:
                from ui.monica_globe_window import MonicaGlobeWindow
                self.globe_renderer = MonicaGlobeWindow(
                    width=self.globe_size * 2, height=self.globe_size * 2)
                logger.info("  [OK] Globe Renderer ready (fallback)")
            except Exception as e2:
                logger.warning(f"  [SKIP] Globe Renderer: {e2}")
        
        # 6. Universal Object Detector (YOLO - see everything in the room)
        self.object_detector = None
        try:
            from vision.object_detector import get_object_detector
            self.object_detector = get_object_detector()
            logger.info("  [OK] Object Detector ready (YOLO)")
        except Exception as e:
            logger.warning(f"  [SKIP] Object Detector: {e}")
        
        # 7. User Memory - learn about user from what we see
        self.user_memory = None
        try:
            from ai.user_memory import get_user_memory
            self.user_memory = get_user_memory()
            logger.info("  [OK] User Memory connected (learning from vision)")
        except Exception as e:
            logger.warning(f"  [SKIP] User Memory: {e}")
        
        # Counters for throttling expensive operations
        self._frame_count = 0
        self._last_object_detect = 0
        self._last_memory_update = 0
        
        # Cached hand states for smooth drawing between detection frames
        self._cached_hand_states = []
        self._cached_hand_frame_age = 0  # frames since last detection
        
        # Proactive speaking - Monica speaks when she sees problems
        self._last_proactive_speak = 0
        self._proactive_cooldown = 30.0  # seconds between proactive messages
        self._distress_emotions = {'sad', 'angry', 'fear', 'disgust', 'surprise'}
        self._distress_streak = 0  # consecutive distress detections
        self._distress_threshold = 3  # speak after N consecutive detections
        
        self.is_initialized = True
        logger.info("Vision sub-systems initialized")

    def run(self):
        """Main vision processing loop — FAST capture, async heavy processing."""
        if not self.is_initialized:
            self.initialize()
        
        self.is_running = True
        self._processing_busy = False  # guard for bg processing thread
        self._cached_vision_result = None
        self._cached_face_overlay = None  # (x, y, w, h) for face rect
        logger.info("Vision processing loop started")
        
        while not self.stop_event.is_set():
            try:
                t0 = time.time()
                self._fast_capture_loop()
                # Target ~15fps — this loop is FAST (<5ms) so sleep is reliable
                elapsed = time.time() - t0
                sleep_time = max(0.005, 0.066 - elapsed)
                time.sleep(sleep_time)
            except Exception as e:
                logger.debug(f"Vision frame error: {e}")
                time.sleep(0.05)
        
        self.is_running = False

    def start_camera(self):
        """Start the camera (called when user clicks Camera button in GUI)."""
        if self.camera_active:
            return
        if self.camera_manager:
            try:
                self.camera_manager.start()
                self.camera_active = True
                logger.info("Camera started by user")
            except Exception as e:
                logger.error(f"Camera start failed: {e}")
                if self.orchestrator:
                    self.orchestrator.set_shared('camera_error', str(e))
        else:
            logger.error("Camera start failed: CameraManager not initialized")
            if self.orchestrator:
                self.orchestrator.set_shared('camera_error', 'CameraManager not initialized')

    def stop_camera(self):
        """Stop the camera."""
        if not self.camera_active:
            return
        if self.camera_manager:
            try:
                self.camera_manager.stop()
            except Exception:
                pass
            self.camera_active = False
            logger.info("Camera stopped by user")

    def _fast_capture_loop(self):
        """FAST path: capture frame, apply cached overlays, publish. NEVER blocks.
        
        All heavy ML inference (face detection, hand tracking, biometrics)
        runs in _heavy_processing_bg on a separate thread. This method only
        draws cached results onto the live frame, guaranteeing smooth video.
        """
        if not self.camera_manager or not self.camera_active:
            return
        
        frame_bgr = self.camera_manager.get_frame()
        if frame_bgr is None:
            return
        
        self._frame_count += 1
        now = time.time()
        
        # --- Draw cached face rectangle (from bg thread results) ---
        if self._cached_face_overlay:
            x, y, fw, fh = self._cached_face_overlay
            cv2.rectangle(frame_bgr, (x, y), (x + fw, y + fh), (0, 255, 0), 2)
        
        # --- Draw cached biometric overlay ---
        if self.biometric_detector:
            try:
                frame_bgr = self._draw_biometric_overlay(frame_bgr)
            except Exception:
                pass
        
        # --- Draw cached hand fingertips ---
        if self._cached_hand_states and self._cached_hand_frame_age < 20:
            for hs in self._cached_hand_states:
                if hasattr(hs, 'fingertips'):
                    for ft in hs.fingertips:
                        if ft.is_extended:
                            cv2.circle(frame_bgr, (ft.x, ft.y), 12, (0, 255, 0), 2, cv2.LINE_AA)
                            cv2.circle(frame_bgr, (ft.x, ft.y), 6, (0, 255, 255), -1, cv2.LINE_AA)
            self._cached_hand_frame_age += 1
        
        # --- Blit cached globe (cheap) ---
        if self.globe_enabled and hasattr(self, '_cached_globe_img') and self._cached_globe_img is not None:
            try:
                frame_bgr = self._blit_globe(frame_bgr, self._cached_globe_img)
            except Exception:
                pass
        
        # --- Kick off background processing if not already running ---
        if not self._processing_busy:
            self._processing_busy = True
            frame_copy = frame_bgr.copy()
            threading.Thread(
                target=self._heavy_processing_bg,
                args=(frame_copy, now),
                daemon=True
            ).start()
        
        # --- Publish frame to GUI (always, every frame) ---
        if self.orchestrator:
            self.orchestrator.set_shared('vision_frame', frame_bgr)
            try:
                self.orchestrator.set_shared('vision_frame_rgb',
                    cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB))
            except Exception:
                pass
            self.orchestrator.set_shared('vision_frame_id', self._frame_count)
        
        # Send to Spout/OBS if enabled
        if self.camera_manager:
            try:
                self.camera_manager.send_to_spout(frame_bgr)
            except Exception:
                pass

    def _heavy_processing_bg(self, frame_bgr, now):
        """SLOW path: runs ALL heavy ML inference in background thread.
        
        Updates cached results that _fast_capture_loop draws. Takes as long
        as needed without blocking the display. Called at most once at a time.
        """
        try:
            # --- Face detection (Haar cascade) ---
            if self.vision_system:
                try:
                    vision_result = self.vision_system.process_frame(frame_bgr)
                    self._cached_vision_result = vision_result
                    if vision_result and getattr(vision_result, 'face_detected', False):
                        self._cached_face_overlay = getattr(vision_result, 'face_location', None)
                        if self.orchestrator:
                            self.orchestrator.set_shared('vision_result', vision_result)
                    else:
                        self._cached_face_overlay = None
                except Exception as e:
                    logger.debug(f"Vision system error: {e}")
            
            # --- Biometric detection ---
            face_confirmed = (self._cached_vision_result is not None
                              and getattr(self._cached_vision_result, 'face_detected', False))
            if self.biometric_detector and face_confirmed:
                try:
                    self.biometric_detector.process_frame(frame_bgr)
                except Exception:
                    pass
            
            # --- Hand tracking (MediaPipe) ---
            if self.hand_controller:
                try:
                    self.hand_controller.show_landmarks = True
                    _, hand_states = self.hand_controller.process_frame(frame_bgr)
                    if hand_states:
                        self._cached_hand_states = hand_states
                        self._cached_hand_frame_age = 0
                        if self.orchestrator:
                            self.orchestrator.set_shared('hand_states', hand_states)
                except Exception:
                    pass
            
            # --- Globe render ---
            if self.globe_enabled and self.globe_renderer:
                if not self._user_location_fetched:
                    self.fetch_user_location()
                try:
                    result = self._render_globe_only()
                    if result:
                        self._cached_globe_img = result
                except Exception:
                    pass
            
            # --- YOLO (every 20 seconds) ---
            if self.object_detector and now - self._last_object_detect > 20.0:
                self._last_object_detect = now
                try:
                    scene = self.object_detector.detect(frame_bgr)
                    if scene and self.orchestrator:
                        self.orchestrator.set_shared('scene_analysis', scene)
                        self.orchestrator.set_shared('detected_objects',
                            [o.class_name for o in scene.objects])
                except Exception:
                    pass
            
            # --- User memory (every 30 seconds) ---
            if self.user_memory and self.biometric_detector and now - self._last_memory_update > 30.0:
                self._last_memory_update = now
                try:
                    if self.biometric_detector.current_emotion:
                        self.user_memory.record_emotion(
                            self.biometric_detector.current_emotion.emotion)
                    if self.orchestrator:
                        bio_status = self.biometric_detector.get_status()
                        self.orchestrator.set_shared('biometric_status', bio_status)
                    self._check_proactive_speaking()
                except Exception:
                    pass
        
        finally:
            self._processing_busy = False

    def _draw_face_and_hands(self, frame: np.ndarray, vision_result) -> np.ndarray:
        """Draw face bounding box and hand landmarks on the frame."""
        if vision_result is None:
            return frame
        
        # --- Face rectangle ---
        if getattr(vision_result, 'face_detected', False) and getattr(vision_result, 'face_location', None):
            x, y, fw, fh = vision_result.face_location
            # Green rectangle around face
            cv2.rectangle(frame, (x, y), (x + fw, y + fh), (0, 255, 0), 2)
            # Corner accents for sci-fi look
            corner_len = min(20, fw // 4, fh // 4)
            clr = (0, 255, 255)  # cyan
            # Top-left
            cv2.line(frame, (x, y), (x + corner_len, y), clr, 2)
            cv2.line(frame, (x, y), (x, y + corner_len), clr, 2)
            # Top-right
            cv2.line(frame, (x + fw, y), (x + fw - corner_len, y), clr, 2)
            cv2.line(frame, (x + fw, y), (x + fw, y + corner_len), clr, 2)
            # Bottom-left
            cv2.line(frame, (x, y + fh), (x + corner_len, y + fh), clr, 2)
            cv2.line(frame, (x, y + fh), (x, y + fh - corner_len), clr, 2)
            # Bottom-right
            cv2.line(frame, (x + fw, y + fh), (x + fw - corner_len, y + fh), clr, 2)
            cv2.line(frame, (x + fw, y + fh), (x + fw, y + fh - corner_len), clr, 2)
            # Label
            label = "FACE DETECTED"
            if getattr(vision_result, 'emotion', None) and vision_result.emotion != 'neutral':
                label = f"{vision_result.emotion.upper()}"
            cv2.putText(frame, label, (x, y - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        
        # --- Hand landmarks ---
        if getattr(vision_result, 'hand_landmarks', None):
            for hand_lms in vision_result.hand_landmarks:
                try:
                    h, w = frame.shape[:2]
                    points = []
                    for lm in hand_lms.landmark:
                        px, py = int(lm.x * w), int(lm.y * h)
                        points.append((px, py))
                    
                    # Draw connections (skeleton)
                    connections = [
                        (0,1),(1,2),(2,3),(3,4),  # thumb
                        (0,5),(5,6),(6,7),(7,8),  # index
                        (0,9),(9,10),(10,11),(11,12),  # middle
                        (0,13),(13,14),(14,15),(15,16),  # ring
                        (0,17),(17,18),(18,19),(19,20),  # pinky
                        (5,9),(9,13),(13,17),  # palm
                    ]
                    for c in connections:
                        if c[0] < len(points) and c[1] < len(points):
                            cv2.line(frame, points[c[0]], points[c[1]], (0, 200, 0), 1)
                    
                    # Draw fingertip dots (indices 4, 8, 12, 16, 20)
                    tips = [4, 8, 12, 16, 20]
                    for tip_idx in tips:
                        if tip_idx < len(points):
                            px, py = points[tip_idx]
                            cv2.circle(frame, (px, py), 6, (0, 255, 255), -1)
                            cv2.circle(frame, (px, py), 8, (0, 255, 0), 1)
                    
                    # Draw all other joints as small dots
                    for i, pt in enumerate(points):
                        if i not in tips:
                            cv2.circle(frame, pt, 3, (0, 180, 0), -1)
                except Exception:
                    pass
        
        # Fallback: if hand_controller detected hands but no hand_landmarks in vision_result
        elif getattr(vision_result, 'hands_detected', 0) > 0:
            pass  # Hand controller in step 3 will draw its own overlays
        
        return frame

    def _draw_biometric_overlay(self, frame: np.ndarray) -> np.ndarray:
        """Draw ALL biometric data as ONE consolidated overlay panel."""
        if not self.biometric_detector:
            return frame
        
        h, w = frame.shape[:2]
        
        # Collect biometric data
        emotion = self.biometric_detector.current_emotion
        age = self.biometric_detector.current_age
        heartbeat = self.biometric_detector.current_heartbeat
        identity = self.biometric_detector.current_identity
        head_count = self.biometric_detector.current_head_count
        finger_count = self.biometric_detector.current_finger_count
        thermal = self.biometric_detector.current_thermal
        
        # Count lines needed
        lines = ['title']  # BIOMETRICS title
        if identity: lines.append('id')
        if emotion: lines.append('emotion')
        if age: lines.append('age')
        lines.append('heartbeat')
        if head_count: lines.append('heads')
        if finger_count: lines.append('fingers')
        if thermal: lines.append('thermal')
        
        line_h = 20
        panel_w = 270
        panel_h = 28 + len(lines) * line_h
        panel_x = w - panel_w - 10
        panel_y = 10
        
        # Draw semi-transparent panel
        overlay = frame.copy()
        cv2.rectangle(overlay, (panel_x, panel_y), (panel_x + panel_w, panel_y + panel_h),
                      (0, 0, 0), -1)
        frame = cv2.addWeighted(overlay, 0.6, frame, 0.4, 0)
        cv2.rectangle(frame, (panel_x, panel_y), (panel_x + panel_w, panel_y + panel_h),
                      (0, 255, 255), 1)
        
        # Title
        cv2.putText(frame, "BIOMETRICS", (panel_x + 10, panel_y + 18),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
        
        y = panel_y + 36
        font = cv2.FONT_HERSHEY_SIMPLEX
        fs = 0.42
        
        # Identity
        if identity and identity.identified:
            cv2.putText(frame, f"ID: {identity.identity or 'Unknown'}", (panel_x + 10, y), font, fs, (0, 255, 0), 1)
        else:
            cv2.putText(frame, "ID: Scanning...", (panel_x + 10, y), font, fs, (128, 128, 128), 1)
        y += line_h
        
        # Emotion
        if emotion:
            clr = (0, 255, 0) if emotion.confidence > 0.5 else (0, 200, 200)
            cv2.putText(frame, f"Emotion: {emotion.emotion} ({emotion.confidence:.0%})", (panel_x + 10, y), font, fs, clr, 1)
            y += line_h
        
        # Age
        if age:
            cv2.putText(frame, f"Age: ~{age.age} ({age.min_age}-{age.max_age})", (panel_x + 10, y), font, fs, (200, 200, 200), 1)
            y += line_h
        
        # Heartbeat
        if heartbeat and heartbeat.bpm:
            clr = (0, 255, 0) if heartbeat.quality == 'good' else (0, 200, 200)
            cv2.putText(frame, f"Heart: {heartbeat.bpm:.0f} BPM ({heartbeat.quality})", (panel_x + 10, y), font, fs, clr, 1)
        else:
            cv2.putText(frame, "Heart: Measuring...", (panel_x + 10, y), font, fs, (128, 128, 128), 1)
        y += line_h
        
        # Head count
        if head_count:
            cv2.putText(frame, f"Heads: {head_count.count}", (panel_x + 10, y), font, fs, (255, 200, 0), 1)
            y += line_h
        
        # Finger count
        if finger_count:
            cv2.putText(frame, f"Fingers: {finger_count.total_fingers} ({finger_count.gesture})", (panel_x + 10, y), font, fs, (255, 200, 0), 1)
            y += line_h
        
        # Thermal
        if thermal and thermal.estimated_temp_f:
            cv2.putText(frame, f"Temp: {thermal.estimated_temp_f:.1f}F ({thermal.status})", (panel_x + 10, y), font, fs, (200, 200, 255), 1)
            y += line_h
        
        return frame

    def _render_globe_only(self):
        """Render JUST the globe image + mask (called from bg thread)."""
        if not self.globe_renderer or not hasattr(self.globe_renderer, 'render'):
            return None

        # Resize globe renderer if globe_size changed (voice zoom/enlarge)
        if hasattr(self.globe_renderer, 'resize') and self.globe_renderer.size != self.globe_size:
            self.globe_renderer.resize(self.globe_size)

        # Auto-rotate (slow, smooth)
        if time.time() >= self._rotation_paused_until:
            self.globe_rotation += 0.15
            if self.globe_rotation >= 360:
                self.globe_rotation -= 360

        hl_lat = hl_lng = None
        hl_name = ''
        if self._highlight_lat is not None and self._highlight_lng is not None:
            if time.time() - self._highlight_time < 30:
                hl_lat = self._highlight_lat
                hl_lng = self._highlight_lng
                hl_name = self._highlight_name or ''

        try:
            globe_img = self.globe_renderer.render(
                rotation_deg=self.globe_rotation,
                highlight_lat=hl_lat,
                highlight_lng=hl_lng,
                highlight_name=hl_name,
                user_lat=self._user_lat,
                user_lng=self._user_lng,
                user_name=self._user_city or 'You',
                show_earthquakes=getattr(self, '_show_earthquakes', False),
                show_clouds=getattr(self, '_show_clouds', False),
                show_lightning=getattr(self, '_show_lightning', False),
                show_temperature=getattr(self, '_show_temperature', False),
            )
        except Exception as e:
            logger.debug(f"Globe render error: {e}")
            return None

        gs = self.globe_size
        if globe_img is None or globe_img.shape[0] != gs or globe_img.shape[1] != gs:
            return None

        # Pre-compute mask (so _blit_globe is cheap)
        gray = cv2.cvtColor(globe_img, cv2.COLOR_BGR2GRAY)
        _, mask = cv2.threshold(gray, 10, 255, cv2.THRESH_BINARY)
        mask_inv = cv2.bitwise_not(mask)
        fg = cv2.bitwise_and(globe_img, globe_img, mask=mask)
        return {'fg': fg, 'mask_inv': mask_inv, 'gs': gs}

    def _blit_globe(self, frame, globe_data):
        """Cheap blit of pre-rendered globe onto frame (called every frame)."""
        h, w = frame.shape[:2]
        gs = globe_data['gs']
        gx, gy = 10, h - gs - 10
        if gy < 0 or gx < 0 or gy + gs > h or gx + gs > w:
            return frame
        roi = frame[gy:gy + gs, gx:gx + gs]
        if roi.shape[0] != gs or roi.shape[1] != gs:
            return frame
        bg = cv2.bitwise_and(roi, roi, mask=globe_data['mask_inv'])
        frame[gy:gy + gs, gx:gx + gs] = cv2.add(bg, globe_data['fg'])
        return frame

    def fetch_user_location(self):
        """Fetch user's geographic location via free IP geolocation API. Non-blocking."""
        if self._user_location_fetched:
            return
        self._user_location_fetched = True
        
        def _fetch():
            try:
                import urllib.request, json
                req = urllib.request.Request('https://ipapi.co/json/',
                    headers={'User-Agent': 'Monica-AI/1.0'})
                with urllib.request.urlopen(req, timeout=5) as resp:
                    data = json.loads(resp.read().decode())
                    self._user_lat = data.get('latitude')
                    self._user_lng = data.get('longitude')
                    self._user_city = data.get('city', 'You')
                    logger.info(f"User location: {self._user_city} ({self._user_lat}, {self._user_lng})")
            except Exception as e:
                logger.debug(f"Geolocation failed: {e}")
                # Fallback to approximate US location
                self._user_lat = 28.5
                self._user_lng = -81.4
                self._user_city = 'You'
        
        import threading
        threading.Thread(target=_fetch, daemon=True).start()

    def highlight_location(self, lat: float, lng: float, name: str = ''):
        """Highlight a location on the globe with an orange blinking dot.
        Called by AI service when user asks about a place."""
        self._highlight_lat = lat
        self._highlight_lng = lng
        self._highlight_name = name
        self._highlight_time = time.time()
        # Snap globe rotation to center this longitude (pause auto-rotate)
        self.globe_rotation = -lng
        self._rotation_paused_until = time.time() + 30  # Pause auto-rotate for 30s
        logger.info(f"Globe highlighting: {name} ({lat}, {lng})")

    def get_frame(self) -> Optional[np.ndarray]:
        """Get the latest processed frame (BGR)."""
        with self.frame_lock:
            if self.current_frame is not None:
                return self.current_frame.copy()
            return None

    def _check_proactive_speaking(self):
        """
        Check if Monica should proactively speak based on what she sees.
        Triggers when detecting sustained emotional distress (sad, fear, angry).
        """
        if not self.orchestrator or not self.biometric_detector:
            return
        
        now = time.time()
        
        # Check if enough time has passed since last proactive speak
        if now - self._last_proactive_speak < self._proactive_cooldown:
            return
        
        # Check current emotion
        emotion = self.biometric_detector.current_emotion
        if not emotion:
            self._distress_streak = 0
            return
        
        current_emotion = emotion.emotion.lower() if hasattr(emotion, 'emotion') else str(emotion).lower()
        confidence = emotion.confidence if hasattr(emotion, 'confidence') else 0.5
        
        if current_emotion in self._distress_emotions and confidence > 0.4:
            self._distress_streak += 1
        else:
            self._distress_streak = max(0, self._distress_streak - 1)
            return
        
        # Only speak after sustained distress detection
        if self._distress_streak < self._distress_threshold:
            return
        
        # Build proactive message based on detected emotion
        messages = {
            'sad': "Hey, I can see you look a bit down. Want to talk about it? I'm here for you.",
            'angry': "I notice you seem frustrated. Take a breath - want me to help with something?",
            'fear': "You look worried. Everything okay? I'm right here if you need me.",
            'disgust': "Something bothering you? I'm here to help if you want to talk.",
            'surprise': "Whoa, something surprised you! What happened?",
        }
        
        message = messages.get(current_emotion, "I noticed something might be off. How are you doing?")
        
        # Send to AI service so Monica responds naturally
        ai_service = self.orchestrator.get_service('ai')
        if ai_service:
            context_msg = (f"[VISION ALERT: User appears {current_emotion} "
                          f"(confidence: {confidence:.0%}, sustained for {self._distress_streak} checks). "
                          f"Respond with care and empathy. Suggested opening: '{message}']")
            ai_service.ask(context_msg)
            logger.info(f"Proactive speak triggered: {current_emotion} ({confidence:.0%})")
        
        # Also speak directly via TTS for immediate response
        tts_service = self.orchestrator.get_service('tts')
        if tts_service:
            tts_service.speak(message)
        
        self._last_proactive_speak = now
        self._distress_streak = 0

    def stop(self):
        """Stop the vision service."""
        self.stop_event.set()
        self.is_running = False
        
        if self.camera_manager:
            try:
                self.camera_manager.stop()
            except Exception:
                pass
        
        logger.info("Vision Service stopped")
