"""
Sound Manager for AR/Holographic Teaching System
Handles sci-fi sound effects playback with queue management
"""

import os
import threading
import queue
from pathlib import Path
from typing import Optional, Dict
import pygame

class SoundManager:
    """
    Manages sci-fi sound effects for AR/Holographic teaching mode.
    
    Features:
    - Sound queue (prevents overlapping)
    - Volume control
    - Preloading for fast playback
    - Thread-safe operation
    """
    
    def __init__(self, sounds_dir: Optional[Path] = None):
        """
        Initialize sound manager.
        
        Args:
            sounds_dir: Directory containing sound files (default: resources/sounds/scifi)
        """
        # Initialize pygame mixer
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        
        # Set default sounds directory
        if sounds_dir is None:
            project_root = Path(__file__).parent.parent.parent
            sounds_dir = project_root / "resources" / "sounds" / "scifi"
        
        self.sounds_dir = Path(sounds_dir)
        self.sounds_dir.mkdir(parents=True, exist_ok=True)
        
        # Sound cache (preloaded sounds)
        self.sounds: Dict[str, pygame.mixer.Sound] = {}
        
        # Playback queue
        self.queue = queue.Queue()
        self.playing = False
        self.volume = 0.7  # Default volume (0.0 to 1.0)
        
        # Playback thread
        self.playback_thread = threading.Thread(target=self._playback_loop, daemon=True)
        self.playback_thread.start()
        
        # Load available sounds
        self._load_sounds()
        
        print(f"[SoundManager] Initialized with {len(self.sounds)} sounds")
    
    def _load_sounds(self):
        """Load all available sound files from sounds directory."""
        if not self.sounds_dir.exists():
            print(f"[SoundManager] Sounds directory not found: {self.sounds_dir}")
            return
        
        # Load all .wav and .mp3 files
        for sound_file in self.sounds_dir.glob("*.wav"):
            try:
                sound_name = sound_file.stem  # Filename without extension
                sound = pygame.mixer.Sound(str(sound_file))
                sound.set_volume(self.volume)
                self.sounds[sound_name] = sound
                print(f"[SoundManager] Loaded: {sound_name}")
            except Exception as e:
                print(f"[SoundManager] Failed to load {sound_file.name}: {e}")
        
        for sound_file in self.sounds_dir.glob("*.mp3"):
            try:
                sound_name = sound_file.stem
                sound = pygame.mixer.Sound(str(sound_file))
                sound.set_volume(self.volume)
                self.sounds[sound_name] = sound
                print(f"[SoundManager] Loaded: {sound_name}")
            except Exception as e:
                print(f"[SoundManager] Failed to load {sound_file.name}: {e}")
    
    def _playback_loop(self):
        """Background thread for sequential sound playback."""
        while True:
            try:
                # Get next sound from queue (blocking)
                sound_name = self.queue.get()
                
                if sound_name is None:  # Shutdown signal
                    break
                
                # Play sound
                if sound_name in self.sounds:
                    self.playing = True
                    sound = self.sounds[sound_name]
                    channel = sound.play()
                    
                    # Wait for sound to finish
                    if channel:
                        while channel.get_busy():
                            pygame.time.wait(10)
                    
                    self.playing = False
                else:
                    print(f"[SoundManager] Sound not found: {sound_name}")
                
                self.queue.task_done()
                
            except Exception as e:
                print(f"[SoundManager] Playback error: {e}")
                self.playing = False
    
    def play(self, sound_name: str, immediate: bool = False):
        """
        Play a sound effect.
        
        Args:
            sound_name: Name of sound file (without extension)
            immediate: If True, play immediately (interrupt current sound)
        """
        if sound_name not in self.sounds:
            print(f"[SoundManager] Sound not found: {sound_name}")
            return
        
        if immediate:
            # Stop current sound and clear queue
            pygame.mixer.stop()
            while not self.queue.empty():
                try:
                    self.queue.get_nowait()
                except queue.Empty:
                    break
            self.playing = False
        
        # Add to queue
        self.queue.put(sound_name)
    
    def stop(self):
        """Stop all sounds and clear queue."""
        pygame.mixer.stop()
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
            except queue.Empty:
                break
        self.playing = False
    
    def set_volume(self, volume: float):
        """
        Set volume for all sounds.
        
        Args:
            volume: Volume level (0.0 to 1.0)
        """
        self.volume = max(0.0, min(1.0, volume))
        for sound in self.sounds.values():
            sound.set_volume(self.volume)
    
    def is_playing(self) -> bool:
        """Check if a sound is currently playing."""
        return self.playing
    
    def get_available_sounds(self) -> list:
        """Get list of available sound names."""
        return list(self.sounds.keys())
    
    def shutdown(self):
        """Shutdown sound manager and cleanup resources."""
        self.stop()
        self.queue.put(None)  # Signal playback thread to stop
        self.playback_thread.join(timeout=1.0)
        pygame.mixer.quit()


# Global sound manager instance
_sound_manager: Optional[SoundManager] = None

def get_sound_manager() -> SoundManager:
    """Get global sound manager instance (singleton)."""
    global _sound_manager
    if _sound_manager is None:
        _sound_manager = SoundManager()
    return _sound_manager
