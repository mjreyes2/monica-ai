"""
Monica Advanced Plasma Orb - Separate Window with Green Screen for OBS Overlay
Features:
- Luminous cloud-like plasma orb inspired by Siri/AI orbs
- Lightning effects during materialization
- Electrical crackling sounds
- Wavy blob organic movement
- Particle effects
- Pulsing glow that responds to speaking
"""
import cv2
import numpy as np
import math
import time
import random
import threading
from typing import Tuple, List, Optional, Callable
from enum import Enum

# Green screen color (pure green for chroma key)
GREEN_SCREEN = (0, 255, 0)  # BGR

# Try to import pygame for sound effects
HAS_PYGAME = False
try:
    import pygame
    if not pygame.mixer.get_init():
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
    HAS_PYGAME = True
except:
    pass


class OrbState(Enum):
    HIDDEN = "hidden"
    MATERIALIZING = "materializing"
    VISIBLE = "visible"
    DEMATERIALIZING = "dematerializing"


class LightningBolt:
    """A lightning bolt for the materialization effect."""
    def __init__(self, center: Tuple[int, int], radius: int, inward: bool = True):
        self.center = center
        self.radius = radius
        
        # Start from outside, end at center (or vice versa)
        angle = random.uniform(0, 2 * math.pi)
        
        if inward:
            dist = random.uniform(radius * 1.5, radius * 2.5)
            self.start = (
                int(center[0] + dist * math.cos(angle)),
                int(center[1] + dist * math.sin(angle))
            )
            end_dist = random.uniform(0, radius * 0.3)
            end_angle = random.uniform(0, 2 * math.pi)
            self.end = (
                int(center[0] + end_dist * math.cos(end_angle)),
                int(center[1] + end_dist * math.sin(end_angle))
            )
        else:
            self.start = center
            dist = random.uniform(radius * 0.8, radius * 1.5)
            self.end = (
                int(center[0] + dist * math.cos(angle)),
                int(center[1] + dist * math.sin(angle))
            )
        
        self.segments = self._generate_segments()
        self.birth_time = time.time()
        self.lifetime = random.uniform(0.05, 0.2)
        self.intensity = random.uniform(0.6, 1.0)
        self.color_shift = random.uniform(0, 1)
    
    def _generate_segments(self) -> List[Tuple[Tuple[int, int], Tuple[int, int]]]:
        """Generate jagged lightning path."""
        segments = []
        points = [self.start]
        num_segs = random.randint(5, 12)
        
        for i in range(1, num_segs):
            t = i / num_segs
            base_x = self.start[0] + (self.end[0] - self.start[0]) * t
            base_y = self.start[1] + (self.end[1] - self.start[1]) * t
            offset = 30 * (1 - t * 0.5)
            points.append((
                int(base_x + random.uniform(-offset, offset)),
                int(base_y + random.uniform(-offset, offset))
            ))
        points.append(self.end)
        
        for i in range(len(points) - 1):
            segments.append((points[i], points[i + 1]))
            # Random branches
            if random.random() < 0.35:
                branch_len = random.randint(15, 40)
                angle = random.uniform(0, 2 * math.pi)
                branch_end = (
                    int(points[i][0] + branch_len * math.cos(angle)),
                    int(points[i][1] + branch_len * math.sin(angle))
                )
                segments.append((points[i], branch_end))
        
        return segments
    
    def is_alive(self) -> bool:
        return time.time() - self.birth_time < self.lifetime
    
    def get_alpha(self) -> float:
        age = time.time() - self.birth_time
        return max(0, 1 - age / self.lifetime) * self.intensity


class WavyBlob:
    """Organic wavy blob for cloud-like effect."""
    def __init__(self, center: Tuple[int, int], radius: int, speed: float = 1.0):
        self.center = center
        self.base_radius = radius
        self.speed = speed
        self.phase = random.uniform(0, 2 * math.pi)
        self.num_points = 8
        self.noise_offsets = [random.uniform(0, 100) for _ in range(self.num_points)]
    
    def get_points(self, time_val: float) -> List[Tuple[int, int]]:
        """Get the blob's current shape points."""
        points = []
        for i in range(self.num_points):
            angle = (2 * math.pi * i / self.num_points) + self.phase
            
            # Organic noise-based radius variation
            noise = math.sin(time_val * self.speed + self.noise_offsets[i]) * 0.3
            noise += math.sin(time_val * self.speed * 1.7 + self.noise_offsets[i] * 2) * 0.15
            
            r = self.base_radius * (1 + noise)
            
            x = int(self.center[0] + r * math.cos(angle))
            y = int(self.center[1] + r * math.sin(angle))
            points.append((x, y))
        
        return points


class Particle:
    """Floating particle for the orb."""
    def __init__(self, center: Tuple[int, int], radius: int):
        angle = random.uniform(0, 2 * math.pi)
        dist = random.uniform(0, radius * 0.8)
        self.x = center[0] + dist * math.cos(angle)
        self.y = center[1] + dist * math.sin(angle)
        self.vx = random.uniform(-1, 1)
        self.vy = random.uniform(-2, -0.5)  # Float upward
        self.size = random.uniform(1, 4)
        self.life = random.uniform(1, 3)
        self.birth = time.time()
        self.brightness = random.uniform(0.5, 1.0)
    
    def update(self, dt: float):
        self.x += self.vx * dt * 30
        self.y += self.vy * dt * 30
        self.vx += random.uniform(-0.1, 0.1)
    
    def is_alive(self) -> bool:
        return time.time() - self.birth < self.life
    
    def get_alpha(self) -> float:
        age = time.time() - self.birth
        # Fade in then out
        if age < 0.3:
            return (age / 0.3) * self.brightness
        return max(0, 1 - (age - 0.3) / (self.life - 0.3)) * self.brightness


class MonicaOrbWindow:
    """
    Advanced plasma orb window with cloud-like effects, lightning, and sounds.
    Green screen background for OBS chroma key.
    Enhanced with plasma textures from PlasmaOrb repository.
    """
    
    MATERIALIZE_PHRASES = [
        "Uploading consciousness...",
        "Optimizing geometry...",
    ]
    
    def __init__(self, width: int = 1920, height: int = 1080):
        self.width = width
        self.height = height
        self.center = (width // 2, height // 2)
        
        # Orb properties
        self.orb_radius = 180
        self.state = OrbState.HIDDEN
        self.visibility = 0.0
        self.materialize_duration = 6.0  # 6 seconds for full formation
        self.materialize_start = 0
        
        # Animation
        self.time_val = 0
        self.pulse_phase = 0
        self.color_phase = 0
        
        # Speaking animation
        self.is_speaking = False
        self.speak_intensity = 0.0
        self.tts_callback = None
        
        # Materialization phrases
        self.materialization_phrases = [
            "Uploading consciousness...",
            "Establishing neural pathways...",
            "Synchronizing quantum states...",
            "Calibrating sensory inputs...",
            "Initialization complete."
        ]
        self.phrase_index = 0
        self.last_phrase_time = 0
        
        # Lightning effects
        self.lightning_bolts: List[LightningBolt] = []
        self.last_zap_time = 0
        
        # Particles
        self.particles: List[Particle] = []
        
        # Color palette (purple/blue/pink plasma)
        self.base_colors = [
            (180, 100, 255),  # Purple
            (255, 100, 200),  # Pink
            (100, 150, 255),  # Blue
            (200, 150, 255),  # Light purple
        ]
        
        # Plasma textures (loaded from external images if available)
        self.plasma_textures = []
        self._load_plasma_textures()
        
        # Sound effects
        self._init_sounds()
        
        # Background ambient sound channels
        self.ambient_channels = []
        self.ambient_active = False
        
        # Window control
        self.running = False
        self.thread = None
        self.visible = False
        
        # Wavy blobs for cloud effect
        self.blobs = []
        for i in range(3):
            speed = 0.5 + i * 0.3
            self.blobs.append(WavyBlob(self.center, self.orb_radius, speed))
        
        # Glow rotation for swirling effect
        self.glow_rotation = 0
        
        # Current phrase display
        self.current_phrase = ""
        
        print("[MonicaOrb] Advanced Plasma Orb initialized (green screen mode)")
    
    def _load_plasma_textures(self):
        """Load plasma orb textures from PlasmaOrb repository."""
        import os
        texture_dir = os.path.join(os.path.dirname(__file__), '..', 'ui', 'PlasmaOrb_ref')
        texture_files = ['plasma.png', 'plasma1.png', 'plasma2.png', 'plasma3.png', 'plasma4.png']
        
        for tex_file in texture_files:
            tex_path = os.path.join(texture_dir, tex_file)
            if os.path.exists(tex_path):
                try:
                    # Load and resize texture to fit orb
                    tex = cv2.imread(tex_path, cv2.IMREAD_UNCHANGED)
                    if tex is not None:
                        # Resize to orb size
                        orb_size = self.orb_radius * 3
                        tex = cv2.resize(tex, (orb_size, orb_size))
                        
                        # Create circular mask
                        mask = np.zeros((orb_size, orb_size), dtype=np.uint8)
                        cv2.circle(mask, (orb_size // 2, orb_size // 2), orb_size // 2 - 5, 255, -1)
                        
                        # Apply mask to make circular
                        if tex.shape[2] == 4:  # Has alpha
                            tex[:, :, 3] = cv2.bitwise_and(tex[:, :, 3], mask)
                        else:
                            # Add alpha channel
                            tex = cv2.cvtColor(tex, cv2.COLOR_BGR2BGRA)
                            tex[:, :, 3] = mask
                        
                        self.plasma_textures.append(tex)
                        print(f"[MonicaOrb] Loaded plasma texture: {tex_file}")
                except Exception as e:
                    print(f"[MonicaOrb] Could not load {tex_file}: {e}")
        
        if not self.plasma_textures:
            print("[MonicaOrb] No plasma textures found, using procedural effects only")
    
    def _load_formation_sounds(self):
        """Load ALL sound files from disk - formation, ambient, research, error, dematerialization."""
        try:
            import os
            sound_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'monica_ai', 'resources', 'sounds', 'scifi')
            
            # Complete sound library
            sound_files = {
                # Initialization
                'initialize': 'monica_initialize_one.mp3',
                
                # Pre-materialization (electrical sparks)
                'electrical_start': 'monica_electricalstart_orb.mp3',
                'electrical_current': 'electrical-current-2-307466.mp3',
                
                # Energy buildup
                'energy_hum': 'energy_hum.mp3',  # PROMINENT - bright pulsation
                'forming_1': 'monica_Orb_forming.mp3',
                'forming_2': 'monica_Orb_forming_two.mp3',
                
                # Formation completion
                'pulsating_1': 'monicaOrb_pulsating.mp3',
                'pulsating_2': 'monicaOrb_pulsatingtwo.mp3',
                'pulsating_3': 'monicaOrb_pulsatingthree.mp3',
                'low_rumble': 'low_rumble.mp3',
                
                # Background ambient (loops)
                'ambient_pulsating': 'monicaOrb_pulsating.mp3',
                'ambient_rumble': 'low_rumble.mp3',
                
                # Research & errors
                'research': 'monica_doing_research.mp3',
                'research_2': 'monica_doing_researchtwo.mp3',
                'error': 'monica_didnot_understand.mp3',
                
                # Dematerialization
                'power_down': 'power_down.mp3'
            }
            
            for key, filename in sound_files.items():
                path = os.path.join(sound_dir, filename)
                if os.path.exists(path):
                    self.sounds[key] = pygame.mixer.Sound(path)
                    print(f"[MonicaOrb] Loaded {key}: {filename}")
                else:
                    print(f"[MonicaOrb] WARNING: Missing sound file: {filename}")
            
            self.formation_sounds_loaded = True
            print("[MonicaOrb] Complete sound library loaded")
            
        except Exception as e:
            print(f"[MonicaOrb] Formation sounds loading error: {e}")
    
    def _init_sounds(self):
        """Initialize electrical/lightning sound effects."""
        self.sounds = {}
        self.sound_channels = []
        self.formation_sounds_loaded = False
        
        if not HAS_PYGAME:
            return
        
        try:
            # Create electrical crackling sounds
            sample_rate = 44100
            
            # Short crackle
            duration = 0.15
            samples = int(sample_rate * duration)
            noise = np.random.uniform(-0.4, 0.4, samples).astype(np.float32)
            envelope = np.exp(-np.linspace(0, 8, samples))
            noise *= envelope
            # Add some frequency variation
            t = np.linspace(0, duration, samples)
            noise *= (1 + 0.5 * np.sin(2 * np.pi * 200 * t))
            noise_int = (noise * 32767).astype(np.int16)
            stereo = np.column_stack((noise_int, noise_int))
            self.sounds['crackle'] = pygame.sndarray.make_sound(stereo)
            self.sounds['crackle'].set_volume(0.25)
            
            # TERMINATOR-STYLE ELECTRICAL HUM - Loud and dramatic
            duration = 1.5
            samples = int(sample_rate * duration)
            t = np.linspace(0, duration, samples)
            # Combine multiple frequencies for INTENSE electrical sound
            hum = np.sin(2 * np.pi * 60 * t) * 0.5  # Louder base
            hum += np.sin(2 * np.pi * 120 * t) * 0.4
            hum += np.sin(2 * np.pi * 180 * t) * 0.3
            hum += np.sin(2 * np.pi * 240 * t) * 0.2
            hum += np.sin(2 * np.pi * 50 * t) * 0.3  # Low rumble
            # Add electrical crackling noise
            hum += np.random.uniform(-0.3, 0.3, samples)
            # Pulsing effect
            hum *= (1 + 0.3 * np.sin(2 * np.pi * 8 * t))
            envelope = np.ones(samples)
            envelope[:int(samples*0.1)] = np.linspace(0, 1, int(samples*0.1))
            envelope[-int(samples*0.2):] = np.linspace(1, 0, int(samples*0.2))
            hum *= envelope
            hum = np.clip(hum, -1, 1)
            hum_int = (hum * 32767).astype(np.int16)
            stereo = np.column_stack((hum_int, hum_int))
            self.sounds['hum'] = pygame.sndarray.make_sound(stereo)
            self.sounds['hum'].set_volume(0.6)  # LOUDER
            
            # Load formation sound files
            self._load_formation_sounds()
            
            # TERMINATOR-STYLE PLASMA FORMATION - Building electrical storm
            duration = 4.0  # Longer for dramatic effect
            samples = int(sample_rate * duration)
            t = np.linspace(0, duration, samples)
            # Rising intensity electrical sound
            intensity = (t / duration) ** 1.5  # Builds up
            # Multiple frequency layers
            plasma = np.sin(2 * np.pi * 80 * t) * 0.4 * intensity
            plasma += np.sin(2 * np.pi * 160 * t) * 0.3 * intensity
            plasma += np.sin(2 * np.pi * 320 * t) * 0.2 * intensity
            # Electrical crackling that intensifies
            crackle = np.random.uniform(-0.5, 0.5, samples) * intensity
            plasma += crackle
            # Deep rumble
            plasma += np.sin(2 * np.pi * 30 * t) * 0.5 * intensity
            # High-pitched electrical whine that rises
            freq_rise = 200 + 800 * (t / duration) ** 2
            plasma += np.sin(2 * np.pi * freq_rise * t) * 0.3 * intensity
            # Envelope - builds up then sustains
            envelope = np.minimum(1.0, t / (duration * 0.3))
            plasma *= envelope
            plasma = np.clip(plasma, -1, 1)
            plasma_int = (plasma * 32767).astype(np.int16)
            stereo = np.column_stack((plasma_int, plasma_int))
            self.sounds['whoosh'] = pygame.sndarray.make_sound(stereo)
            self.sounds['whoosh'].set_volume(0.8)  # LOUD
            
            # LOUD ELECTRICAL ZAP for lightning strikes
            duration = 0.3
            samples = int(sample_rate * duration)
            t = np.linspace(0, duration, samples)
            zap = np.random.uniform(-1, 1, samples)
            zap *= np.exp(-t * 10)  # Quick decay
            zap += np.sin(2 * np.pi * 1000 * t) * 0.5 * np.exp(-t * 8)
            zap += np.sin(2 * np.pi * 2000 * t) * 0.3 * np.exp(-t * 12)
            zap = np.clip(zap, -1, 1)
            zap_int = (zap * 32767).astype(np.int16)
            stereo = np.column_stack((zap_int, zap_int))
            self.sounds['zap'] = pygame.sndarray.make_sound(stereo)
            self.sounds['zap'].set_volume(0.7)
            
            print("[MonicaOrb] Sound effects loaded")
        except Exception as e:
            print(f"[MonicaOrb] Could not create sounds: {e}")
    
    def _play_sound(self, sound_name: str, volume: float = 1.0):
        """Play a sound effect with optional volume control."""
        if HAS_PYGAME and sound_name in self.sounds:
            try:
                sound = self.sounds[sound_name]
                sound.set_volume(volume)
                sound.play()
            except Exception as e:
                print(f"[MonicaOrb] Sound play error ({sound_name}): {e}")
    
    def _start_ambient_sounds(self):
        """Start background ambient sounds (pulsating + low rumble) - low volume to not overpower voice."""
        if not HAS_PYGAME:
            return
        
        try:
            self.ambient_active = True
            
            # Play ambient pulsating (loop, low volume)
            if 'ambient_pulsating' in self.sounds:
                channel = self.sounds['ambient_pulsating'].play(loops=-1)  # Loop forever
                if channel:
                    channel.set_volume(0.15)  # 15% volume - don't overpower voice
                    self.ambient_channels.append(channel)
                    print("[MonicaOrb] Background pulsating started (15% volume)")
            
            # Play ambient rumble (loop, low volume)
            if 'ambient_rumble' in self.sounds:
                channel = self.sounds['ambient_rumble'].play(loops=-1)  # Loop forever
                if channel:
                    channel.set_volume(0.10)  # 10% volume - subtle background
                    self.ambient_channels.append(channel)
                    print("[MonicaOrb] Background rumble started (10% volume)")
            
        except Exception as e:
            print(f"[MonicaOrb] Ambient sounds error: {e}")
    
    def _stop_ambient_sounds(self):
        """Stop all background ambient sounds."""
        try:
            self.ambient_active = False
            for channel in self.ambient_channels:
                if channel:
                    channel.stop()
            self.ambient_channels.clear()
            print("[MonicaOrb] Background ambient sounds stopped")
        except Exception as e:
            print(f"[MonicaOrb] Stop ambient error: {e}")
    
    def play_research_sound(self):
        """Play research sound when Monica is searching/researching."""
        import random
        sound = 'research' if random.random() < 0.5 else 'research_2'
        self._play_sound(sound, volume=0.6)
        print("[MonicaOrb] Research sound played")
    
    def play_error_sound(self):
        """Play error sound when Monica doesn't understand."""
        self._play_sound('error', volume=0.7)
        print("[MonicaOrb] Error sound played")
    
    def set_tts_callback(self, callback: Callable[[str], None]):
        """Set callback for speaking materialization phrases."""
        self.tts_callback = callback
    
    def show_window_only(self):
        """Just make the window visible without sounds - for GUI button click.
        Shows the orb visually but without the sound sequence."""
        if self.state == OrbState.HIDDEN:
            self.state = OrbState.MATERIALIZING
            self.materialize_start = time.time()
            self.visibility = 0.0
            self._spawn_initial_lightning()
        self.visible = True
        
        # Bring window to front using Windows API for reliable focus
        try:
            import ctypes
            # Find the OpenCV window and bring it to front
            hwnd = ctypes.windll.user32.FindWindowW(None, "Monica Orb")
            if hwnd:
                ctypes.windll.user32.SetForegroundWindow(hwnd)
                ctypes.windll.user32.BringWindowToTop(hwnd)
                ctypes.windll.user32.ShowWindow(hwnd, 9)  # SW_RESTORE
                print(f"[MonicaOrb] Window brought to front (hwnd={hwnd})")
        except Exception as e:
            print(f"[MonicaOrb] Could not bring window to front: {e}")
        
        # Also try OpenCV method
        try:
            cv2.setWindowProperty("Monica Orb", cv2.WND_PROP_TOPMOST, 1)
            cv2.setWindowProperty("Monica Orb", cv2.WND_PROP_TOPMOST, 0)  # Reset so it's not always on top
        except:
            pass
        
        print("[MonicaOrb] Window opened (silent mode - say 'Monica show yourself' for full effect)")
    
    def show(self, with_sounds: bool = True):
        """Start materialization - Monica appears with COMPLETE MULTI-PHASE formation sequence.
        
        Args:
            with_sounds: If True, play full sound sequence. If False, just show visually.
        """
        if self.state == OrbState.HIDDEN:
            self.state = OrbState.MATERIALIZING
            self.materialize_start = time.time()
            self.phrase_index = 0
            self.last_phrase_time = 0
            self.visibility = 0.0
            self.last_zap_time = 0
            self._spawn_initial_lightning()
            
            if not with_sounds:
                print("[MonicaOrb] Materializing (silent mode)")
                return
            
            import threading
            
            # ===== PHASE 1: PRE-MATERIALIZATION - Electrical sparks (0-2 seconds) =====
            self._play_sound('electrical_start')  # 0s - Electrical sparks start
            threading.Timer(0.5, lambda: self._play_sound('electrical_current')).start()  # 0.5s - Electrical current (with visible electricity)
            
            # ===== PHASE 2: ENERGY BUILDUP (2-4 seconds) =====
            threading.Timer(2.0, lambda: self._play_sound('energy_hum')).start()  # 2s - PROMINENT energy hum (bright pulsation)
            threading.Timer(2.5, lambda: self._play_sound('forming_1')).start()  # 2.5s - Orb forming sound 1
            threading.Timer(3.0, lambda: self._play_sound('forming_2')).start()  # 3s - Orb forming sound 2
            
            # ===== PHASE 3: FORMATION COMPLETION (4-6 seconds) =====
            threading.Timer(4.0, lambda: self._play_sound('pulsating_1')).start()  # 4s - Pulsating 1
            threading.Timer(4.5, lambda: self._play_sound('pulsating_2')).start()  # 4.5s - Pulsating 2
            threading.Timer(5.0, lambda: self._play_sound('pulsating_3')).start()  # 5s - Pulsating 3
            threading.Timer(5.5, lambda: self._play_sound('low_rumble')).start()  # 5.5s - Low rumble when orb is done forming
            
            # ===== PHASE 4: START BACKGROUND AMBIENT (after 6 seconds) =====
            threading.Timer(6.0, lambda: self._start_ambient_sounds()).start()  # 6s - Start continuous background loops
            
            print("[MonicaOrb] [?] COMPLETE FORMATION SEQUENCE STARTED")
            print("[MonicaOrb] Phase 1: Electrical sparks (0-2s)")
            print("[MonicaOrb] Phase 2: Energy buildup (2-4s)")
            print("[MonicaOrb] Phase 3: Formation completion (4-6s)")
            print("[MonicaOrb] Phase 4: Background ambient active (6s+)")
    
    def hide(self):
        """Start dematerialization - Monica disappears with complete sound sequence."""
        if self.state == OrbState.VISIBLE:
            self.state = OrbState.DEMATERIALIZING
            self.materialize_start = time.time()
            self._spawn_initial_lightning()
            
            # Stop background ambient sounds
            self._stop_ambient_sounds()
            
            import threading
            
            # ===== DEMATERIALIZATION SEQUENCE (3-4 seconds) =====
            self._play_sound('electrical_current')  # 0s - Electrical discharge
            threading.Timer(0.5, lambda: self._play_sound('electrical_start')).start()  # 0.5s - Electrical sparks (reversed)
            threading.Timer(2.5, lambda: self._play_sound('power_down')).start()  # 2.5s - Power down (towards end)
            
            print("[MonicaOrb] [?] DEMATERIALIZATION SEQUENCE STARTED")
            print("[MonicaOrb] Electrical discharge → Sparks → Power down")
    
    def set_speaking(self, speaking: bool, intensity: float = 0.5):
        """Set speaking state for pulsing animation."""
        self.is_speaking = speaking
        self.speak_intensity = intensity if speaking else 0.0
    
    def _spawn_initial_lightning(self):
        """Spawn initial lightning bolts."""
        for _ in range(12):
            self.lightning_bolts.append(
                LightningBolt(self.center, self.orb_radius, inward=True)
            )
    
    def _spawn_particles(self, count: int = 3):
        """Spawn floating particles."""
        for _ in range(count):
            self.particles.append(Particle(self.center, self.orb_radius))
    
    def _update(self, dt: float):
        """Update animation state."""
        self.time_val += dt
        self.color_phase += dt * 0.5
        self.pulse_phase += dt * 3.0
        self.glow_rotation += dt * 30  # Degrees per second
        
        # Update state transitions
        if self.state == OrbState.MATERIALIZING:
            elapsed = time.time() - self.materialize_start
            self.visibility = min(1.0, elapsed / self.materialize_duration)
            
            # Spawn lightning during materialization (more at start, DRAMATIC)
            lightning_chance = 0.6 * (1 - self.visibility * 0.5)  # More lightning
            if random.random() < lightning_chance:
                # Spawn multiple bolts for dramatic effect
                num_bolts = random.randint(1, 3)
                for _ in range(num_bolts):
                    self.lightning_bolts.append(
                        LightningBolt(self.center, self.orb_radius, inward=True)
                    )
                # Play ZAP sound with each lightning burst (not too often)
                current_time = time.time()
                if current_time - getattr(self, 'last_zap_time', 0) > 0.15:
                    self._play_sound('zap')
                    self.last_zap_time = current_time
                elif random.random() < 0.4:
                    self._play_sound('crackle')
            
            # Spawn particles
            if random.random() < 0.3:
                self._spawn_particles(2)
            
            # Speak phrases
            phrase_interval = self.materialize_duration / len(self.MATERIALIZE_PHRASES)
            if elapsed - self.last_phrase_time > phrase_interval and self.phrase_index < len(self.MATERIALIZE_PHRASES):
                self.current_phrase = self.MATERIALIZE_PHRASES[self.phrase_index]
                if self.tts_callback:
                    self.tts_callback(self.current_phrase)
                self.phrase_index += 1
                self.last_phrase_time = elapsed
            
            if self.visibility >= 1.0:
                self.state = OrbState.VISIBLE
                self.current_phrase = ""
                print("[MonicaOrb] Fully materialized")
        
        elif self.state == OrbState.DEMATERIALIZING:
            elapsed = time.time() - self.materialize_start
            self.visibility = max(0.0, 1.0 - elapsed / (self.materialize_duration * 0.4))
            
            # Spawn lightning during dematerialization
            if random.random() < 0.5 * self.visibility:
                self.lightning_bolts.append(
                    LightningBolt(self.center, self.orb_radius, inward=False)
                )
            
            if self.visibility <= 0.0:
                self.state = OrbState.HIDDEN
                self.particles.clear()
                self.lightning_bolts.clear()
                print("[MonicaOrb] Hidden")
        
        elif self.state == OrbState.VISIBLE:
            # Ambient lightning occasionally
            if random.random() < 0.02:
                self.lightning_bolts.append(
                    LightningBolt(self.center, self.orb_radius, inward=random.random() < 0.5)
                )
            
            # Ambient particles
            if random.random() < 0.15:
                self._spawn_particles(1)
        
        # Update lightning
        self.lightning_bolts = [b for b in self.lightning_bolts if b.is_alive()]
        
        # Update particles
        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if p.is_alive()]
    
    def _get_current_color(self) -> Tuple[int, int, int]:
        """Get interpolated color based on phase."""
        idx = int(self.color_phase) % len(self.base_colors)
        next_idx = (idx + 1) % len(self.base_colors)
        blend = self.color_phase % 1.0
        
        c1 = self.base_colors[idx]
        c2 = self.base_colors[next_idx]
        
        return tuple(int(c1[i] * (1 - blend) + c2[i] * blend) for i in range(3))
    
    def _render(self) -> np.ndarray:
        """Render the orb frame."""
        # Green screen background
        frame = np.full((self.height, self.width, 3), GREEN_SCREEN, dtype=np.uint8)
        
        if self.state == OrbState.HIDDEN:
            return frame
        
        alpha = self.visibility
        orb_color = self._get_current_color()
        
        # Pulse effect
        pulse = 1.0 + 0.1 * math.sin(self.pulse_phase)
        if self.is_speaking:
            pulse += 0.15 * self.speak_intensity * math.sin(self.pulse_phase * 4)
        
        current_radius = int(self.orb_radius * pulse * alpha)
        
        if current_radius < 5:
            # Just draw lightning during early materialization
            self._draw_lightning(frame, alpha)
            return frame
        
        # === OUTER GLOW LAYERS (SUPER LUMINOUS effect) ===
        # More layers, bigger glow, brighter colors
        for i in range(10, 0, -1):
            glow_radius = current_radius + i * 30  # Bigger spread
            glow_alpha = 0.25 * (11 - i) / 10 * alpha  # Brighter
            glow_color = tuple(int(min(255, c * glow_alpha * 1.5)) for c in orb_color)
            cv2.circle(frame, self.center, glow_radius, glow_color, 5, cv2.LINE_AA)
        
        # Extra bright inner glow
        for i in range(4, 0, -1):
            inner_glow_radius = current_radius + i * 15
            inner_alpha = 0.4 * (5 - i) / 4 * alpha
            inner_color = tuple(int(min(255, c * inner_alpha * 2)) for c in orb_color)
            cv2.circle(frame, self.center, inner_glow_radius, inner_color, 8, cv2.LINE_AA)
        
        # === PLASMA TEXTURE OVERLAY (from PlasmaOrb repository) ===
        if self.plasma_textures and alpha > 0.3:
            try:
                # Cycle through textures based on time
                tex_idx = int(self.time_val * 0.5) % len(self.plasma_textures)
                next_tex_idx = (tex_idx + 1) % len(self.plasma_textures)
                blend_factor = (self.time_val * 0.5) % 1.0
                
                tex = self.plasma_textures[tex_idx]
                next_tex = self.plasma_textures[next_tex_idx]
                
                # Scale texture to current orb size
                tex_size = int(current_radius * 2.2)
                if tex_size > 20:
                    tex_scaled = cv2.resize(tex, (tex_size, tex_size))
                    next_tex_scaled = cv2.resize(next_tex, (tex_size, tex_size))
                    
                    # Blend between textures for smooth transition
                    tex_blended = cv2.addWeighted(tex_scaled, 1 - blend_factor, next_tex_scaled, blend_factor, 0)
                    
                    # Rotate texture for swirling plasma effect
                    rotation_angle = self.glow_rotation * 0.3
                    M = cv2.getRotationMatrix2D((tex_size // 2, tex_size // 2), rotation_angle, 1.0)
                    tex_rotated = cv2.warpAffine(tex_blended, M, (tex_size, tex_size), 
                                                  borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
                    
                    # Calculate ROI bounds
                    x1 = max(0, self.center[0] - tex_size // 2)
                    y1 = max(0, self.center[1] - tex_size // 2)
                    x2 = min(self.width, x1 + tex_size)
                    y2 = min(self.height, y1 + tex_size)
                    
                    # Texture region to use
                    tx1 = max(0, -(self.center[0] - tex_size // 2))
                    ty1 = max(0, -(self.center[1] - tex_size // 2))
                    tx2 = tx1 + (x2 - x1)
                    ty2 = ty1 + (y2 - y1)
                    
                    if x2 > x1 and y2 > y1 and tex_rotated.shape[2] == 4:
                        # Get alpha channel and apply visibility
                        tex_alpha = tex_rotated[ty1:ty2, tx1:tx2, 3:4].astype(np.float32) / 255.0 * alpha * 0.6
                        
                        # Get RGB channels
                        tex_rgb = tex_rotated[ty1:ty2, tx1:tx2, :3].astype(np.float32)
                        
                        # Get frame region
                        frame_region = frame[y1:y2, x1:x2].astype(np.float32)
                        
                        # Create mask for non-green-screen pixels
                        not_green = ~np.all(frame[y1:y2, x1:x2] == GREEN_SCREEN, axis=2, keepdims=True)
                        
                        # Blend only where not green screen
                        blended = frame_region * (1 - tex_alpha) + tex_rgb * tex_alpha
                        frame[y1:y2, x1:x2] = np.where(not_green, blended, frame_region).astype(np.uint8)
            except Exception as e:
                pass  # Silently fail if texture rendering has issues
        
        # === WAVY BLOB CLOUD LAYERS ===
        for blob_idx, blob in enumerate(self.blobs):
            points = blob.get_points(self.time_val)
            if len(points) > 2:
                pts = np.array(points, np.int32)
                
                # Different opacity for each blob layer
                blob_alpha = [0.4, 0.6, 0.3][blob_idx] * alpha
                blob_color = tuple(int(c * blob_alpha) for c in orb_color)
                
                # Fill the blob shape
                overlay = frame.copy()
                cv2.fillPoly(overlay, [pts], blob_color, cv2.LINE_AA)
                
                # Blend with frame (avoid green screen areas)
                mask = np.all(frame == GREEN_SCREEN, axis=2)
                frame = cv2.addWeighted(frame, 0.7, overlay, 0.3, 0)
                frame[mask] = GREEN_SCREEN
        
        # === CORE GRADIENT (dense center) ===
        for r in range(current_radius, 0, -4):
            ratio = r / current_radius
            # Brighter in center (dense), dimmer at edges
            intensity = 0.3 + 0.7 * (1 - ratio) ** 1.5
            
            # Add pulsing variation
            pulse_var = 1 + 0.1 * math.sin(self.pulse_phase * 2 + r * 0.05)
            
            layer_color = tuple(int(min(255, c * intensity * pulse_var * alpha)) for c in orb_color)
            cv2.circle(frame, self.center, r, layer_color, 2, cv2.LINE_AA)
        
        # === BRIGHT CORE ===
        core_radius = int(current_radius * 0.25)
        # White-ish bright core
        core_color = tuple(int(min(255, c * 1.3 * alpha)) for c in orb_color)
        cv2.circle(frame, self.center, core_radius, core_color, -1, cv2.LINE_AA)
        cv2.circle(frame, self.center, int(core_radius * 0.5), (255, 255, 255), -1, cv2.LINE_AA)
        
        # === ROTATING GLOW EFFECT ===
        num_glows = 3
        for i in range(num_glows):
            angle = math.radians(self.glow_rotation + i * 120)
            glow_dist = current_radius * 0.6
            glow_x = int(self.center[0] + glow_dist * math.cos(angle))
            glow_y = int(self.center[1] + glow_dist * math.sin(angle))
            
            glow_size = int(current_radius * 0.4)
            glow_color = tuple(int(c * 0.5 * alpha) for c in orb_color)
            cv2.circle(frame, (glow_x, glow_y), glow_size, glow_color, -1, cv2.LINE_AA)
        
        # === PARTICLES ===
        for p in self.particles:
            p_alpha = p.get_alpha() * alpha
            p_color = tuple(int(min(255, c * p_alpha * 1.2)) for c in orb_color)
            cv2.circle(frame, (int(p.x), int(p.y)), int(p.size), p_color, -1, cv2.LINE_AA)
        
        # === LIGHTNING ===
        self._draw_lightning(frame, alpha)
        
        # === MATERIALIZATION PHRASE ===
        if self.current_phrase:
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.5
            thickness = 1
            text_size = cv2.getTextSize(self.current_phrase, font, font_scale, thickness)[0]
            text_x = (self.width - text_size[0]) // 2
            text_y = self.height - 40
            
            # Text with glow
            cv2.putText(frame, self.current_phrase, (text_x + 1, text_y + 1),
                       font, font_scale, (0, 0, 0), thickness + 1, cv2.LINE_AA)
            cv2.putText(frame, self.current_phrase, (text_x, text_y),
                       font, font_scale, (255, 255, 255), thickness, cv2.LINE_AA)
        
        return frame
    
    def _draw_lightning(self, frame: np.ndarray, alpha: float):
        """Draw SUPER BRIGHT lightning bolts on the frame."""
        for bolt in self.lightning_bolts:
            bolt_alpha = bolt.get_alpha() * alpha
            
            # Lightning colors - BIGGER, BRIGHTER, MORE LUMINOUS
            for seg_start, seg_end in bolt.segments:
                # Layer 1: Outer glow (very wide, dim) - ELECTRIC BLUE
                outer_glow = (
                    int(255 * bolt_alpha * 0.4),  # Blue
                    int(200 * bolt_alpha * 0.4),  # Green
                    int(100 * bolt_alpha * 0.4)   # Red
                )
                cv2.line(frame, seg_start, seg_end, outer_glow, 15, cv2.LINE_AA)
                
                # Layer 2: Mid glow (wide, brighter) - CYAN
                mid_glow = (
                    int(255 * bolt_alpha * 0.7),
                    int(255 * bolt_alpha * 0.6),
                    int(150 * bolt_alpha * 0.5)
                )
                cv2.line(frame, seg_start, seg_end, mid_glow, 9, cv2.LINE_AA)
                
                # Layer 3: Inner glow (medium) - BRIGHT CYAN
                inner_glow = (
                    int(255 * bolt_alpha),
                    int(255 * bolt_alpha * 0.9),
                    int(200 * bolt_alpha * 0.7)
                )
                cv2.line(frame, seg_start, seg_end, inner_glow, 5, cv2.LINE_AA)
                
                # Layer 4: Core glow - WHITE/CYAN
                core_glow = (
                    int(255 * bolt_alpha),
                    int(255 * bolt_alpha),
                    int(255 * bolt_alpha)
                )
                cv2.line(frame, seg_start, seg_end, core_glow, 3, cv2.LINE_AA)
                
                # Layer 5: Bright white core
                cv2.line(frame, seg_start, seg_end, (255, 255, 255), 1, cv2.LINE_AA)
    
    def _run_loop(self):
        """Main render loop."""
        cv2.namedWindow("Monica Orb", cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO)
        cv2.resizeWindow("Monica Orb", self.width, self.height)
        
        # CRITICAL: Make window always on top and move to front
        try:
            cv2.setWindowProperty("Monica Orb", cv2.WND_PROP_TOPMOST, 1)
        except:
            pass  # Older OpenCV versions may not support this
        
        # Bring window to front using Windows API
        try:
            import ctypes
            hwnd = ctypes.windll.user32.FindWindowW(None, "Monica Orb")
            if hwnd:
                ctypes.windll.user32.SetForegroundWindow(hwnd)
                ctypes.windll.user32.BringWindowToTop(hwnd)
                ctypes.windll.user32.ShowWindow(hwnd, 9)  # SW_RESTORE
        except:
            pass
        
        # Move window to primary monitor, centered
        try:
            import tkinter as tk
            root = tk.Tk()
            screen_width = root.winfo_screenwidth()
            screen_height = root.winfo_screenheight()
            root.destroy()
            
            # Center the window
            x = (screen_width - self.width) // 2
            y = (screen_height - self.height) // 2
            cv2.moveWindow("Monica Orb", x, y)
        except:
            # Fallback: move to top-left
            cv2.moveWindow("Monica Orb", 100, 100)
        
        last_time = time.time()
        
        while self.running:
            current_time = time.time()
            dt = current_time - last_time
            last_time = current_time
            
            self._update(dt)
            frame = self._render()
            
            cv2.imshow("Monica Orb", frame)
            
            key = cv2.waitKey(16) & 0xFF  # ~60 FPS
            if key == ord('q'):
                break
            elif key == ord('s'):  # Show
                self.show()
            elif key == ord('h'):  # Hide
                self.hide()
            elif key == ord('t'):  # Toggle speaking
                self.set_speaking(not self.is_speaking, 0.7)
        
        cv2.destroyWindow("Monica Orb")
    
    def start(self):
        """Start the orb window in a separate thread."""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._run_loop, daemon=True)
            self.thread.start()
            print("[MonicaOrb] Window started (Press 's' to show, 'h' to hide, 't' to toggle speaking, 'q' to quit)")
    
    def stop(self):
        """Stop the orb window and clean up properly."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
        # IMPORTANT: Destroy window to prevent duplicates
        try:
            cv2.destroyWindow("Monica Orb")
        except:
            pass
        print("[MonicaOrb] Window stopped and cleaned up")
    
    def cleanup(self):
        """Force cleanup of all resources."""
        self.running = False
        try:
            cv2.destroyWindow("Monica Orb")
        except:
            pass
        # Stop any playing sounds
        if HAS_PYGAME:
            try:
                pygame.mixer.stop()
            except:
                pass


# Singleton instance
_orb_window: Optional[MonicaOrbWindow] = None


def get_orb_window() -> MonicaOrbWindow:
    """Get singleton orb window instance. Cleans up old instance if exists."""
    global _orb_window
    if _orb_window is not None:
        # Clean up existing window if not running
        if not _orb_window.running:
            _orb_window.cleanup()
            _orb_window = None
    if _orb_window is None:
        _orb_window = MonicaOrbWindow()
    return _orb_window


def cleanup_orb_window():
    """Force cleanup of orb window singleton."""
    global _orb_window
    if _orb_window is not None:
        _orb_window.cleanup()
        _orb_window = None


if __name__ == "__main__":
    """Run orb window standalone when executed directly."""
    print("[MonicaOrb] Running standalone...")
    orb = get_orb_window()
    orb.start()
    
    try:
        # Keep running until window is closed
        while orb.running:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("[MonicaOrb] Interrupted by user")
    finally:
        orb.stop()
        print("[MonicaOrb] Stopped")


# Test mode
if __name__ == "__main__":
    print("Monica Advanced Plasma Orb - Green Screen Mode")
    print("Press 's' to show (with lightning), 'h' to hide, 't' to toggle speaking, 'q' to quit")
    
    orb = MonicaOrbWindow(500, 500)
    orb.running = True
    orb._run_loop()
