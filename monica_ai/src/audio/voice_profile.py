"""
Voice Profile System for Monica AI.
Learns and remembers the user's voice characteristics to improve recognition.
"""
import json
import numpy as np
from pathlib import Path
from typing import Optional, Dict, List
from dataclasses import dataclass, asdict
import time


@dataclass
class VoiceProfile:
    """User's voice profile for better recognition."""
    user_name: str = "MJP"
    
    # Audio characteristics (learned over time)
    avg_energy: float = 0.01  # Average speaking energy
    min_energy: float = 0.005  # Minimum energy when speaking
    max_energy: float = 0.1  # Maximum energy when speaking
    
    # Speech patterns
    avg_phrase_duration: float = 2.0  # Average phrase length in seconds
    avg_pause_duration: float = 0.5  # Average pause between phrases
    
    # Recognition statistics
    total_phrases: int = 0
    successful_recognitions: int = 0
    
    # Timestamps
    created_at: float = 0.0
    last_updated: float = 0.0
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'VoiceProfile':
        return cls(**data)


class VoiceProfileManager:
    """Manages voice profiles for improved recognition."""
    
    def __init__(self, profile_path: Optional[Path] = None):
        """Initialize the voice profile manager."""
        if profile_path is None:
            profile_path = Path(__file__).parent.parent.parent / "voice_profile.json"
        
        self.profile_path = profile_path
        self.profile = self._load_profile()
        
        # Running statistics for learning
        self.energy_samples: List[float] = []
        self.phrase_durations: List[float] = []
        self.last_update_time = time.time()
        
        print(f"Voice profile loaded for: {self.profile.user_name}")
    
    def _load_profile(self) -> VoiceProfile:
        """Load voice profile from disk."""
        if self.profile_path.exists():
            try:
                with open(self.profile_path, 'r') as f:
                    data = json.load(f)
                    return VoiceProfile.from_dict(data)
            except Exception as e:
                print(f"Error loading voice profile: {e}")
        
        # Create new profile
        profile = VoiceProfile()
        profile.created_at = time.time()
        profile.last_updated = time.time()
        return profile
    
    def save_profile(self):
        """Save voice profile to disk."""
        try:
            self.profile.last_updated = time.time()
            with open(self.profile_path, 'w') as f:
                json.dump(self.profile.to_dict(), f, indent=2)
        except Exception as e:
            print(f"Error saving voice profile: {e}")
    
    def update_from_audio(self, energy: float, duration: float, was_successful: bool = True):
        """Update profile based on recognized speech."""
        # Track energy samples
        self.energy_samples.append(energy)
        if len(self.energy_samples) > 100:
            self.energy_samples.pop(0)
        
        # Track phrase durations
        if duration > 0.3:  # Only track meaningful phrases
            self.phrase_durations.append(duration)
            if len(self.phrase_durations) > 50:
                self.phrase_durations.pop(0)
        
        # Update statistics
        self.profile.total_phrases += 1
        if was_successful:
            self.profile.successful_recognitions += 1
        
        # Update averages periodically
        if time.time() - self.last_update_time > 30:  # Every 30 seconds
            self._update_averages()
            self.last_update_time = time.time()
    
    def _update_averages(self):
        """Update average values from collected samples."""
        if self.energy_samples:
            self.profile.avg_energy = np.mean(self.energy_samples)
            self.profile.min_energy = np.percentile(self.energy_samples, 10)
            self.profile.max_energy = np.percentile(self.energy_samples, 90)
        
        if self.phrase_durations:
            self.profile.avg_phrase_duration = np.mean(self.phrase_durations)
        
        # Save updated profile
        self.save_profile()
        print(f"[VOICE PROFILE] Updated - avg_energy: {self.profile.avg_energy:.4f}, "
              f"phrases: {self.profile.total_phrases}")
    
    def get_recommended_threshold(self) -> float:
        """Get recommended energy threshold based on learned profile."""
        # Use 50% of minimum speaking energy as threshold
        # This helps distinguish speech from background noise
        if self.profile.min_energy > 0:
            return self.profile.min_energy * 0.5
        return 0.005  # Default
    
    def is_likely_user_speech(self, energy: float) -> bool:
        """Check if audio energy is consistent with user's voice."""
        # If we have learned the user's voice, check if energy is in expected range
        if self.profile.total_phrases > 10:
            # Allow some margin (50% below min to 150% above max)
            min_threshold = self.profile.min_energy * 0.5
            max_threshold = self.profile.max_energy * 1.5
            return min_threshold <= energy <= max_threshold
        
        # Not enough data yet, accept all
        return True
    
    def get_stats(self) -> Dict:
        """Get profile statistics."""
        return {
            "user": self.profile.user_name,
            "total_phrases": self.profile.total_phrases,
            "success_rate": (self.profile.successful_recognitions / max(1, self.profile.total_phrases)) * 100,
            "avg_energy": self.profile.avg_energy,
            "energy_range": (self.profile.min_energy, self.profile.max_energy),
        }


# Global instance
_voice_profile_manager: Optional[VoiceProfileManager] = None


def get_voice_profile() -> VoiceProfileManager:
    """Get the global voice profile manager."""
    global _voice_profile_manager
    if _voice_profile_manager is None:
        _voice_profile_manager = VoiceProfileManager()
    return _voice_profile_manager
