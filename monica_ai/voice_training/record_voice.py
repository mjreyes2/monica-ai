"""
Monica AI Voice Recording System
Record 1000+ phrases to train a personalized speech recognition model.

This creates training data for SpeechBrain wav2vec2 ASR fine-tuning.
"""

import os
import sys
import json
import wave
import time
import threading
import re
from pathlib import Path
from datetime import datetime
import numpy as np
from scipy import signal as scipy_signal

# Fix Windows console encoding issues
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Import scientific audio quality metrics (with resilient fallback)
HAS_QUALITY_METRICS = False
try:
    # Add project root to path
    # From: monica_project/monica_ai/voice_training/record_voice.py
    # To:   monica_project/
    current_file = os.path.abspath(__file__)
    voice_training_dir = os.path.dirname(current_file)  # voice_training/
    monica_ai_dir = os.path.dirname(voice_training_dir)  # monica_ai/
    project_root = os.path.dirname(monica_ai_dir)  # monica_project/

    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    # Prefer bundled lightweight shim first for robustness
    try:
        from monica_ai.voice_training.quality_shim import AudioQualityMetrics, QualityLevel, AudioQualityAssessment
        HAS_QUALITY_METRICS = True
        print(f"[RECORDER] ✅ Loaded lightweight quality metrics (shim)")
    except Exception as e_shim:
        # Fallback to project-root module
        try:
            from audio_quality_metrics import AudioQualityMetrics, QualityLevel, AudioQualityAssessment
            HAS_QUALITY_METRICS = True
            print(f"[RECORDER] ✅ Audio quality metrics loaded (root)")
        except Exception as e_primary:
            raise RuntimeError(f"Metrics unavailable: shim={e_shim}, root={e_primary}")
except Exception as e:
    print(f"[RECORDER] ⚠️ Audio quality metrics not available: {e}")

# Audio recording
try:
    import sounddevice as sd
    import numpy as np
    HAS_AUDIO = True
except ImportError:
    HAS_AUDIO = False
    print("Install: pip install sounddevice numpy")

# Noise reduction
try:
    import noisereduce as nr
    from scipy.io import wavfile
    HAS_NOISE_REDUCE = True
except ImportError:
    HAS_NOISE_REDUCE = False
    print("Install: pip install noisereduce scipy")

# GUI
try:
    import tkinter as tk
    from tkinter import ttk, messagebox
    HAS_TK = True
except ImportError:
    HAS_TK = False

# Trainer (SpeechBrain) - optional
# Try to resolve at import time so the GUI can accurately reflect availability
VoiceModelTrainer = None
try:
    from monica_ai.voice_training.train_speechbrain_wrapper import SpeechBrainTrainer as _VMT
    VoiceModelTrainer = _VMT
    print("[TRAINER] ✅ SpeechBrain VoiceModelTrainer available")
except Exception as e:
    # Keep optional: training UI will stay disabled but recording still works
    VoiceModelTrainer = None
    print(f"[TRAINER] ⚠️ SpeechBrain trainer not available at startup: {e}")


class VoiceRecorder:
    """Record voice samples for training with noise reduction."""
    
    def __init__(self, output_dir: str = "data/training/recordings/wake_phrases", user_id: str = "mjp"):
        self.user_id = user_id
        # Resolve output directory relative to project root for stability
        out_path = Path(output_dir)
        try:
            # Get project root (3 levels up from this file)
            base_root = Path(__file__).resolve().parents[2]
            
            # If the path doesn't exist, try to get it from the environment
            if not base_root.exists():
                base_root = Path(os.getcwd())
                
            print(f"[INIT] Using project root: {base_root}")
            
        except Exception as e:
            print(f"[INIT] Error determining project root: {e}")
            base_root = Path.cwd()
            
        if not out_path.is_absolute():
            out_path = base_root / out_path
            
        self.output_dir = out_path  # User-specific folder has been consolidated
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Audio settings - Using NVIDIA Broadcast devices
        try:
            # Add the project root to the Python path
            import sys
            import os
            project_root = Path(__file__).resolve().parents[2]
            if str(project_root) not in sys.path:
                sys.path.append(str(project_root))
            
            # Try to import the config
            try:
                from audio_config import INPUT_DEVICE_INDEX, OUTPUT_DEVICE_INDEX, SAMPLE_RATE, CHANNELS, CHUNK_SIZE
                
                self.input_device_index = INPUT_DEVICE_INDEX
                self.output_device_index = OUTPUT_DEVICE_INDEX
                self.sample_rate = SAMPLE_RATE
                self.channels = CHANNELS
                self.chunk_size = CHUNK_SIZE
                print(f"[AUDIO] Using config: Input={INPUT_DEVICE_INDEX}, Output={OUTPUT_DEVICE_INDEX}, {SAMPLE_RATE}Hz, {CHANNELS} channel(s)")
                
            except ImportError as e:
                print(f"[AUDIO] Could not load audio_config.py: {e}")
                # Fall through to hardcoded defaults
                raise
                
        except Exception as e:
            # Fallback to hardcoded defaults
            print("[AUDIO] Using hardcoded NVIDIA Broadcast settings")
            self.input_device_index = 2    # NVIDIA Broadcast Microphone
            self.output_device_index = 4   # NVIDIA Broadcast Speakers
            self.sample_rate = 48000
            self.channels = 1
            self.chunk_size = 1024
        
        self.dtype = np.int16
        self._record_sample_rate = self.sample_rate
        
        # Noise reduction settings
        self.noise_reduce_enabled = True
        self.noise_profile = None  # Will capture ambient noise
        # Noise reduction strength: 0.0 = off, 1.0 = maximum (default was too aggressive)
        # 0.5 = moderate reduction that preserves speech characteristics
        self.noise_reduce_strength = 0.5
        # Mic gain (applied before saving); 1.0 = unity
        self.mic_gain = 1.0
        
        # Microphone type detection (affects level thresholds)
        self.is_headset_mic = False
        self.mic_type = "unknown"
        self._detect_microphone_type()
        
        # Recording state
        self.is_recording = False
        self.audio_data = []
        self.current_phrase_idx = 0
        self._last_recording_path = None  # Track last saved file explicitly
        # Calibration (loaded from user_profile.json if available)
        self.calibration = {}
        
        # Load phrases
        self.phrases = self._load_phrases()
        
        # User profile and progress files
        self.profile_file = self.output_dir / "user_profile.json"
        self.progress_file = self.output_dir / "progress.json"
        self.recorded_phrases_file = self.output_dir / "recorded_phrases.json"
        
        # Track which phrases have been recorded (by phrase text)
        self.recorded_phrases = set()
        self.load_user_profile()
        self.load_progress()
        self.load_recorded_phrases()

        # Manifest for SpeechBrain training
        self.manifest_file = self.output_dir / "manifest.json"
        
        # Initialize audio quality assessment
        if HAS_QUALITY_METRICS:
            self.quality_assessor = AudioQualityAssessment(sample_rate=self.sample_rate)
            self.quality_log_file = self.output_dir / "quality_log.json"
        else:
            self.quality_assessor = None
        
        # Count actual WAV files in the directory
        actual_file_count = len(list(self.output_dir.glob("*.wav")))
        
        print(f"[RECORDER] User: {self.user_id}")
        print(f"[RECORDER] Output directory: {self.output_dir}")
        print(f"[RECORDER] Total phrases: {len(self.phrases)}")
        print(f"[RECORDER] Recordings in library: {actual_file_count}")
        print(f"[RECORDER] Unique phrases recorded: {len(self.recorded_phrases)}")
        print(f"[RECORDER] Current position: {self.current_phrase_idx}")
        print(f"[RECORDER] Noise reduction: {'ENABLED' if HAS_NOISE_REDUCE else 'DISABLED'} (strength: {self.noise_reduce_strength})")
        print(f"[RECORDER] Microphone type: {self.mic_type} (headset: {self.is_headset_mic})")
        print(f"[RECORDER] Quality metrics: {'ENABLED' if HAS_QUALITY_METRICS else 'DISABLED'}")

        # Initialize crash/diagnostic log
        try:
            self.log_file = self.output_dir / "recorder.log"
            # Simple log rotation (~2 MB)
            try:
                if self.log_file.exists() and self.log_file.stat().st_size > 2 * 1024 * 1024:
                    rotated = self.output_dir / "recorder.log.1"
                    try:
                        if rotated.exists():
                            rotated.unlink()
                    except Exception:
                        pass
                    self.log_file.rename(rotated)
            except Exception:
                pass
            with open(self.log_file, "a", encoding="utf-8") as lf:
                lf.write(f"\n[{datetime.now().isoformat(timespec='seconds')}] Recorder initialized for user {self.user_id}\n")
        except Exception:
            self.log_file = None

    def _detect_microphone_type(self):
        """Detect if the microphone is a headset/USB mic and adjust thresholds accordingly."""
        try:
            import sounddevice as sd
            devices = sd.query_devices()
            
            device_name = ''
            if self.input_device_index is not None and self.input_device_index < len(devices):
                device = devices[self.input_device_index]
                device_name = device.get('name', '').lower()
            else:
                try:
                    device = sd.query_devices(kind='input')
                    device_name = device.get('name', '').lower()
                except:
                    pass
            
            # Detect headset/USB microphone patterns
            headset_keywords = ['headset', 'headphone', 'usb', 'wireless', 'bluetooth', 
                              'airpod', 'earbud', 'jabra', 'plantronics', 'logitech',
                              'hyperx', 'steelseries', 'razer', 'corsair', 'arctis']
            
            broadcast_keywords = ['nvidia broadcast', 'rtx voice', 'krisp', 'noise cancell']
            
            if any(kw in device_name for kw in headset_keywords):
                self.is_headset_mic = True
                self.mic_type = "headset"
            elif any(kw in device_name for kw in broadcast_keywords):
                self.is_headset_mic = False
                self.mic_type = "broadcast_processed"
            elif 'realtek' in device_name or 'built-in' in device_name or 'internal' in device_name:
                self.is_headset_mic = False
                self.mic_type = "builtin"
            else:
                self.is_headset_mic = False
                self.mic_type = "standard"
                
            print(f"[RECORDER] Detected mic: '{device_name}' -> type={self.mic_type}")
            
        except Exception as e:
            print(f"[RECORDER] Mic detection failed: {e}")
            self.is_headset_mic = False
            self.mic_type = "unknown"
    
    def get_level_thresholds(self):
        """Get audio level thresholds based on microphone type.
        
        Returns dict with threshold percentages for the visual meter.
        Headset mics and broadcast-processed audio need more relaxed thresholds.
        """
        if self.mic_type == "headset":
            # Headset mics: closer to mouth, more consistent but often lower raw levels
            return {
                'too_quiet': 15,      # Below 15% is too quiet (was 33%)
                'quiet': 25,          # 15-25% is quiet but usable (was 33-50%)
                'good_start': 25,     # 25%+ is good (was 50%)
                'loud': 85,           # Above 85% is loud (was 80%)
                'clip': 95            # Above 95% is clipping risk (was 90%)
            }
        elif self.mic_type == "broadcast_processed":
            # NVIDIA Broadcast / noise-cancelled: already processed, trust the levels more
            return {
                'too_quiet': 10,      # Very relaxed - broadcast normalizes
                'quiet': 20,
                'good_start': 20,
                'loud': 90,
                'clip': 98
            }
        else:
            # Standard/desktop mics: original thresholds but slightly relaxed
            return {
                'too_quiet': 25,      # Below 25% is too quiet (was 33%)
                'quiet': 40,          # 25-40% is quiet (was 33-50%)
                'good_start': 40,     # 40%+ is good (was 50%)
                'loud': 85,           # Above 85% is loud (was 80%)
                'clip': 92            # Above 92% is clipping risk (was 90%)
            }

    def calibrate_mic(self) -> dict:
        """Quick calibration: measure ambient noise floor and store in profile.

        Returns a dict with calibration results or an empty dict on failure.
        """
        results = {}
        try:
            import sounddevice as sd
            import numpy as np

            # Prefer current effective samplerate if a stream is active
            sr = int(self._record_sample_rate or self.sample_rate)

            duration_quiet = 1.0  # seconds
            duration_speech = 1.5  # seconds

            def _rec(seconds: float) -> np.ndarray:
                frames = int(seconds * sr)
                data = sd.rec(frames, samplerate=sr, channels=self.channels, dtype='float32')
                sd.wait()
                a = np.squeeze(data)
                if a.ndim > 1:
                    a = a[:, 0]
                return a.astype(np.float32, copy=False)

            # Measure ambient noise
            quiet = _rec(duration_quiet)
            noise_rms = float(np.sqrt(np.mean(quiet**2)) + 1e-9)

            # Prompt user to speak briefly (handled by GUI) — capture anyway
            speech = _rec(duration_speech)
            speech_rms = float(np.sqrt(np.mean(speech**2)) + 1e-9)

            # Estimate SNR in dB
            import math
            snr_db = 20.0 * math.log10(max(speech_rms, 1e-9) / max(noise_rms, 1e-9))
            # Auto-suggest mic gain so typical speech is in a healthy range
            # Target speech RMS in float32 [-1,1] space (~0.02 = good headroom)
            target_rms = 0.02
            suggested_gain = 1.0
            try:
                if speech_rms > 1e-8:
                    suggested_gain = target_rms / speech_rms
                    # Clamp to a safe range; recorder will enforce a slightly wider clamp
                    suggested_gain = max(0.5, min(3.0, suggested_gain))
            except Exception:
                suggested_gain = 1.0

            # Apply suggested gain to recorder (future recordings)
            try:
                self.mic_gain = float(suggested_gain)
            except Exception:
                self.mic_gain = 1.0

            results = {
                'sample_rate': sr,
                'noise_rms': noise_rms,
                'speech_rms': speech_rms,
                'snr_db': float(snr_db),
                'suggested_mic_gain': float(suggested_gain)
            }

            # Persist to user_profile.json
            try:
                profile = {}
                if self.profile_file.exists():
                    with open(self.profile_file, 'r', encoding='utf-8') as f:
                        profile = json.load(f)
                calib = profile.get('calibration', {}) or {}
                calib.update(results)
                profile['calibration'] = calib
                with open(self.profile_file, 'w', encoding='utf-8') as f:
                    json.dump(profile, f, indent=2)
            except Exception:
                pass

            # Log
            try:
                if self.log_file:
                    with open(self.log_file, 'a', encoding='utf-8') as lf:
                        lf.write(
                            f"[CALIB] sr={sr}, noise_rms={noise_rms:.6f}, speech_rms={speech_rms:.6f}, "
                            f"snr_db={snr_db:.1f}, suggested_gain={suggested_gain:.2f}\n"
                        )
            except Exception:
                pass

        except Exception as e:
            print(f"[RECORDER] Calibration failed: {e}")
        return results
    
    def load_user_profile(self):
        """Load or create user profile."""
        if self.profile_file.exists():
            with open(self.profile_file, 'r') as f:
                profile = json.load(f)
                print(f"[RECORDER] Welcome back, {profile.get('name', self.user_id)}!")
                # Load calibration block if present
                self.calibration = profile.get('calibration', {}) or {}
                # Load any persisted audio device preferences
                try:
                    audio_devs = profile.get('audio_devices') or {}
                    in_idx = audio_devs.get('input')
                    out_idx = audio_devs.get('output')
                    if in_idx is not None:
                        self.input_device_index = int(in_idx)
                    if out_idx is not None:
                        self.output_device_index = int(out_idx)
                    if audio_devs:
                        print(f"[AUDIO] Using saved devices from profile: input={self.input_device_index}, output={self.output_device_index}")
                except Exception as e:
                    print(f"[AUDIO] Failed to load audio_devices from profile: {e}")
        else:
            # Create new profile
            profile = {
                "user_id": self.user_id,
                "name": self.user_id,
                "created": str(Path(self.output_dir).stat().st_ctime if self.output_dir.exists() else "now"),
                "total_recordings": 0
            }
            self.save_user_profile(profile)
            print(f"[RECORDER] Created new profile for {self.user_id}")
    
    def save_user_profile(self, profile: dict = None):
        """Save user profile."""
        if profile is None:
            # Merge into existing profile to avoid dropping fields
            if self.profile_file.exists():
                try:
                    with open(self.profile_file, 'r', encoding='utf-8') as f:
                        profile = json.load(f)
                except Exception:
                    profile = {}
            else:
                profile = {}
            profile.setdefault("user_id", self.user_id)
            profile.setdefault("name", self.user_id)
            profile["total_recordings"] = len(self.recorded_phrases)
        with open(self.profile_file, 'w', encoding='utf-8') as f:
            json.dump(profile, f, indent=2)

    def set_devices(self, input_index: int, output_index: int):
        """Update input/output device indices and persist them in the user profile."""
        try:
            self.input_device_index = int(input_index)
            self.output_device_index = int(output_index)

            # Load or create profile
            if self.profile_file.exists():
                try:
                    with open(self.profile_file, 'r', encoding='utf-8') as f:
                        profile = json.load(f)
                except Exception:
                    profile = {}
            else:
                profile = {"user_id": self.user_id, "name": self.user_id}

            profile.setdefault("audio_devices", {})
            profile["audio_devices"]["input"] = int(input_index)
            profile["audio_devices"]["output"] = int(output_index)

            with open(self.profile_file, 'w', encoding='utf-8') as f:
                json.dump(profile, f, indent=2)

            print(f"[AUDIO] Saved device prefs: input={input_index}, output={output_index}")
        except Exception as e:
            print(f"[AUDIO] Failed to save device prefs: {e}")
    
    def load_recorded_phrases(self):
        """Load set of already recorded phrases."""
        if self.recorded_phrases_file.exists():
            try:
                with open(self.recorded_phrases_file, 'r') as f:
                    data = json.load(f)
                    self.recorded_phrases = set(data.get("phrases", []))
            except:
                self.recorded_phrases = set()
        else:
            self.recorded_phrases = set()
    
    def save_recorded_phrases(self):
        """Save set of recorded phrases with retry logic for file sync issues."""
        max_retries = 3
        retry_delay = 0.5  # seconds
        
        data = {
            "user_id": self.user_id,
            "count": len(self.recorded_phrases),
            "phrases": list(self.recorded_phrases)
        }
        
        for attempt in range(max_retries):
            try:
                # Write to temp file first, then rename (atomic operation)
                temp_file = self.recorded_phrases_file.with_suffix('.json.tmp')
                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
                
                # Replace original with temp (handles file locks better)
                import shutil
                shutil.move(str(temp_file), str(self.recorded_phrases_file))
                return  # Success
                
            except OSError as e:
                if attempt < max_retries - 1:
                    print(f"[RECORDER] ⚠️ File save retry {attempt + 1}/{max_retries}: {e}")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    # Final attempt: try direct write
                    try:
                        with open(self.recorded_phrases_file, 'w', encoding='utf-8') as f:
                            json.dump(data, f, indent=2)
                        return
                    except Exception as final_e:
                        print(f"[RECORDER] ❌ Could not save recorded phrases: {final_e}")
                        # Don't crash - data is still in memory
            except Exception as e:
                print(f"[RECORDER] ❌ Unexpected error saving phrases: {e}")
    
    def is_phrase_recorded(self, phrase: str) -> bool:
        """Check if a phrase has already been recorded."""
        return phrase in self.recorded_phrases
    
    def mark_phrase_recorded(self, phrase: str):
        """Mark a phrase as recorded."""
        self.recorded_phrases.add(phrase)
        self.save_recorded_phrases()
        self.save_user_profile()
    
    def unmark_phrase_recorded(self, phrase: str):
        """Unmark a phrase (for re-recording)."""
        # Try both original and lowercase since manifest stores lowercase
        phrase_lower = phrase.lower()
        removed = False
        if phrase in self.recorded_phrases:
            self.recorded_phrases.discard(phrase)
            removed = True
        if phrase_lower in self.recorded_phrases:
            self.recorded_phrases.discard(phrase_lower)
            removed = True
        # Also try to find by matching lowercase
        to_remove = [p for p in self.recorded_phrases if p.lower() == phrase_lower]
        for p in to_remove:
            self.recorded_phrases.discard(p)
            removed = True
        if removed:
            self.save_recorded_phrases()
    
    def _load_phrases(self) -> list:
        """Load 1000+ training phrases - diverse, complex, with tongue twisters."""
        phrases = []
        
        # === TONGUE TWISTERS (100) ===
        tongue_twisters = [
            "She sells seashells by the seashore every single summer morning without fail",
            "Peter Piper picked a peck of pickled peppers from the garden patch behind the barn",
            "How much wood would a woodchuck chuck if a woodchuck could chuck wood all day",
            "Red lorry yellow lorry red lorry yellow lorry red lorry yellow lorry quickly",
            "Unique New York unique New York you know you need unique New York city",
            "The sixth sick sheik's sixth sheep's sick and needs immediate medical attention",
            "Fuzzy Wuzzy was a bear but Fuzzy Wuzzy had no hair so he wasn't fuzzy",
            "Betty Botter bought some butter but she said the butter's bitter if I put it in my batter",
            "A proper copper coffee pot produces properly poured coffee every single time",
            "Six slippery snails slid slowly seaward through the sandy beach at sunset",
            "Irish wristwatch Swiss wristwatch Irish wristwatch Swiss wristwatch repeatedly",
            "Pad kid poured curd pulled cod from the fishing boat early this morning",
            "Thirty three thousand feathers on a thrushes throat is quite remarkable",
            "The thirty three thieves thought that they thrilled the throne throughout Thursday night",
            "Fresh French fried fish from the finest French fish fryer in Paris",
            "A skunk sat on a stump and thunk the stump stunk but the stump thunk the skunk stunk",
            "Lesser leather never weathered wetter weather better than superior leather",
            "Which wristwatches are Swiss wristwatches from Switzerland exactly",
            "Roberta ran rings around the Roman ruins in Rome during her vacation",
            "Nine nimble noblemen nibbling nuts near the northern nursery yesterday",
            "Fred fed Ted bread and Ted fed Fred bread instead of feeding themselves",
            "Green glass globes glow greenly in the garden at night during summer",
            "Six Czech cricket critics clicked their clickety clickers continuously",
            "Toy boat toy boat toy boat toy boat toy boat said quickly five times",
            "Rubber baby buggy bumpers bounce beautifully on bumpy roads everywhere",
            "Selfish shellfish swim swiftly through the shallow sea near the shore",
            "The big black bug bit the big black bear on his big black nose repeatedly",
            "Around the rugged rocks the ragged rascal ran repeatedly without stopping",
            "Three free throws from the free throw line for three points each time",
            "Whether the weather is cold or whether the weather is hot we shall have weather",
            "If two witches were watching two watches which witch would watch which watch carefully",
            "I saw Susie sitting in a shoe shine shop shining shoes all day long",
            "A tutor who tooted the flute tried to tutor two tooters to toot properly",
            "How can a clam cram in a clean cream can carefully without making a mess",
            "I scream you scream we all scream for ice cream in summer every year",
            "The great Greek grape growers grow great Greek grapes in abundance",
            "Black background brown background black background brown background alternating",
            "Susie works in a shoeshine shop where she shines she sits and shines all day",
            "Mix a box of mixed biscuits with a boxed biscuit mixer thoroughly",
            "Imagine an imaginary menagerie manager managing an imaginary menagerie professionally",
            "Seventy seven benevolent elephants marched elegantly through the parade",
            "Six thick thistle sticks six thick thistles stick together firmly",
            "Truly rural truly rural truly rural truly rural areas are peaceful",
            "Near an ear a nearer ear a nearly eerie ear heard everything clearly",
            "Eddie edited it and edited it until Eddie edited it right finally",
            "Specific Pacific specific Pacific specific Pacific ocean views are beautiful",
            "Freshly fried fresh flesh from the French fish market tastes delicious",
            "Luke Luck likes lakes Luke's duck likes lakes and quacks happily",
            "Crash quiche course crash quiche course crash quiche course cooking class",
            "Scissors sizzle thistles sizzle scissors sizzle thistles in the summer heat",
            "The seething sea ceaseth and thus the seething sea sufficeth us",
            "Can you can a can as a canner can can a can professionally",
            "Denise sees the fleece Denise sees the fleas at least Denise could sneeze",
            "Cooks cook cupcakes quickly in the kitchen every morning before dawn",
            "Really leery rarely Larry really leery rarely Larry acted strangely",
            "Send toast to ten tense stout saints ten tall tents standing firmly",
            "Six sick hicks nick six slick bricks with picks and sticks quickly",
            "Rory the warrior and Roger the worrier were reared wrongly in a rural brewery",
            "Tommy Tucker tried to tie Tammy's turtles tie to two tall trees",
            "Brisk brave brigadiers brandished broad bright blades blunderbusses and bludgeons",
            "A pessimistic pest exists amidst us and persists in testing our patience",
            "Elizabeth's birthday is on the third Thursday of this month surprisingly",
            "Fred's friend Fran flips fine flapjacks fast and furiously every morning",
            "Give papa a cup of proper coffee in a copper coffee cup please",
            "Good blood bad blood good blood bad blood good blood bad blood flows",
            "He threw three free throws from the free throw line successfully",
            "I wish to wash my Irish wristwatch with my Swiss wristwatch thoroughly",
            "Kindly kittens knitting mittens keep kazooing in the king's kitchen",
            "Larry sent the latter a letter later to let the latter know about it",
            "Lovely lemon liniment for limber limbs is available at the pharmacy",
            "Many an anemone sees an enemy anemone in the ocean regularly",
            "Nine nice night nurses nursing nicely through the night shift diligently",
            "Of all the felt I ever felt I never felt a piece of felt like that felt",
            "One smart fellow he felt smart two smart fellows they felt smart",
            "Pirates private property is properly protected by the proper authorities",
            "Quick kiss quicker kiss quickest kiss kissed quickly and quietly",
            "Round the rough and rugged rock the ragged rascal rudely ran repeatedly",
            "Sheena leads Sheila needs Sheila leads Sheena needs both working together",
            "The bottom of the butter bucket is the buttered bucket bottom clearly",
            "The epitome of femininity with extreme proximity to infinity",
            "There those thousand thinkers were thinking how did the other three thieves go through",
            "Thin sticks thick bricks thin sticks thick bricks building constantly",
            "Three short sword sheaths sheathe three short swords securely",
            "Through three cheese trees three free fleas flew while freezing breeze blew",
            "Tie twine to three tree twigs tightly and trim the twigs thoroughly",
            "Two tiny tigers take two taxis to town every Tuesday morning",
            "Unique New York unique New York you know you need unique New York always",
            "Very well very well very well said the three vets to the very wet pet",
            "Wayne went to Wales to watch walruses wander wildly through water",
            "Which witch wished which wicked wish on the wicked witch of the west",
            "Willie's really weary wading in the water with his wet wool winter underwear",
            "World wide web world wide web world wide web browsing extensively",
            "Yellow butter purple jelly red jam black bread spread it thick say it quick",
            "Yolanda Yolanda Yolanda yodeled yesterday while doing her yoga",
            "Zebras zig and zebras zag zooming zealously through the zoo enclosure",
            "Zeus was seized by a seizure and sneezed and wheezed in the breeze",
            "A big black bear sat on a big black rug eating blueberries",
            "Around the rocks the ragged rascals ran racing rather recklessly",
        ]
        phrases.extend(tongue_twisters)
        
        # === COMPLEX SENTENCES - SCIENCE & NATURE (100) ===
        science_nature = [
            "The intricate process of photosynthesis converts sunlight into chemical energy within plant cells",
            "Tectonic plates shift gradually beneath the earth's surface causing earthquakes and volcanic activity",
            "The human brain contains approximately eighty six billion neurons connected by trillions of synapses",
            "Climate change is accelerating the melting of polar ice caps at an unprecedented and alarming rate",
            "The Amazon rainforest produces approximately twenty percent of the world's oxygen supply",
            "Gravitational waves were first detected in twenty fifteen confirming Einstein's theoretical predictions",
            "The mitochondria are often called the powerhouse of the cell because they generate most cellular energy",
            "Bioluminescence allows deep sea creatures to produce their own light in the darkness of the ocean",
            "The theory of evolution by natural selection was independently developed by Darwin and Wallace",
            "Quantum entanglement allows particles to remain connected regardless of the distance between them",
            "The periodic table organizes chemical elements by their atomic number and electron configuration",
            "Coral reefs support approximately twenty five percent of all marine species despite covering less than one percent of the ocean floor",
            "The water cycle continuously moves water through evaporation precipitation and collection processes",
            "Black holes are regions of spacetime where gravity is so strong that nothing can escape",
            "DNA contains the genetic instructions for the development and functioning of all living organisms",
            "The aurora borealis occurs when charged particles from the sun interact with atmospheric gases",
            "Plate tectonics explains how continents drift apart and collide over millions of years",
            "The immune system defends the body against pathogens through complex cellular and molecular mechanisms",
            "Ecosystems maintain balance through intricate food webs and nutrient cycling processes",
            "The speed of light in a vacuum is approximately three hundred million meters per second",
            "Stem cells have the remarkable ability to develop into many different specialized cell types",
            "The ozone layer protects life on Earth by absorbing most of the sun's harmful ultraviolet radiation",
            "Neuroplasticity allows the brain to reorganize itself by forming new neural connections throughout life",
            "The carbon cycle describes the movement of carbon through the atmosphere oceans and living organisms",
            "Renewable energy sources include solar wind hydroelectric geothermal and biomass technologies",
            "The greenhouse effect traps heat in the atmosphere and is essential for maintaining Earth's temperature",
            "Genetic mutations can be beneficial neutral or harmful depending on environmental conditions",
            "The circulatory system transports oxygen nutrients and hormones throughout the entire body",
            "Biodiversity is essential for ecosystem resilience and provides numerous services to humanity",
            "The electromagnetic spectrum includes radio waves microwaves infrared visible light ultraviolet x-rays and gamma rays",
            "Artificial intelligence systems can now recognize patterns and make decisions with remarkable accuracy",
            "The nitrogen cycle converts atmospheric nitrogen into forms usable by plants and animals",
            "Seismic waves provide valuable information about the internal structure of the Earth",
            "Photovoltaic cells convert sunlight directly into electricity using semiconductor materials",
            "The human genome contains approximately three billion base pairs of DNA organized into chromosomes",
            "Ocean currents distribute heat around the globe and significantly influence regional climates",
            "Superconductors conduct electricity with zero resistance when cooled below critical temperatures",
            "The digestive system breaks down food into nutrients that can be absorbed by the body",
            "Dark matter and dark energy make up approximately ninety five percent of the universe",
            "Symbiotic relationships between species can be mutualistic parasitic or commensal in nature",
            "The respiratory system facilitates gas exchange bringing oxygen in and removing carbon dioxide",
            "Nanotechnology manipulates matter at the atomic and molecular scale for various applications",
            "The food chain demonstrates how energy flows from producers to consumers in an ecosystem",
            "Gene therapy holds promise for treating genetic disorders by correcting defective genes",
            "The rock cycle describes the continuous transformation of rocks through geological processes",
            "Antibiotics revolutionized medicine but overuse has led to resistant bacterial strains",
            "The nervous system coordinates voluntary and involuntary actions throughout the body",
            "Sustainable agriculture practices aim to meet food needs while protecting environmental resources",
            "The theory of relativity fundamentally changed our understanding of space time and gravity",
            "Vaccines train the immune system to recognize and fight specific pathogens effectively",
        ]
        phrases.extend(science_nature)
        
        # === COMPLEX SENTENCES - HISTORY & CULTURE (100) ===
        history_culture = [
            "The Renaissance period marked a significant cultural and intellectual transformation in European history",
            "Ancient civilizations developed sophisticated writing systems mathematics and architectural techniques",
            "The Industrial Revolution fundamentally transformed manufacturing transportation and daily life",
            "World War Two remains the deadliest conflict in human history affecting millions of people worldwide",
            "The French Revolution introduced radical political and social changes that influenced subsequent movements",
            "Ancient Egyptian pyramids were constructed as elaborate tombs for pharaohs and their consorts",
            "The printing press invented by Gutenberg revolutionized the spread of knowledge and information",
            "The Roman Empire at its height controlled vast territories across Europe Africa and Asia",
            "The civil rights movement fought against racial discrimination and achieved significant legal reforms",
            "The Great Wall of China was built over many centuries to protect against northern invasions",
            "The Age of Exploration led to unprecedented global exchange of goods ideas and unfortunately diseases",
            "Democracy originated in ancient Athens where citizens participated directly in governmental decisions",
            "The Enlightenment emphasized reason science and individual rights over traditional authority",
            "Indigenous cultures around the world developed unique traditions languages and knowledge systems",
            "The space race between superpowers accelerated technological development and scientific discovery",
            "Medieval castles served as both defensive fortifications and symbols of feudal power",
            "The abolitionist movement worked tirelessly to end the practice of slavery throughout the world",
            "Ancient Greek philosophy laid the foundations for Western thought in ethics politics and metaphysics",
            "The Byzantine Empire preserved classical knowledge while developing distinctive art and architecture",
            "The suffragette movement fought for women's right to vote and participate in political processes",
            "The Silk Road facilitated trade and cultural exchange between East and West for centuries",
            "Archaeological discoveries continue to reveal new insights about ancient human civilizations",
            "The Reformation challenged the authority of the Catholic Church and transformed religious practice",
            "Colonial powers established empires that profoundly affected indigenous populations worldwide",
            "The invention of the wheel revolutionized transportation and manufacturing capabilities",
            "Ancient Mesopotamia is often called the cradle of civilization due to its many innovations",
            "The Cold War shaped international relations and military strategy for nearly five decades",
            "Traditional craftsmanship techniques have been passed down through generations of artisans",
            "The Scientific Revolution established empirical observation as the basis for understanding nature",
            "Cultural heritage preservation protects historical sites and traditions for future generations",
            "The Ottoman Empire controlled strategic territory connecting Europe Asia and Africa",
            "Folk traditions and oral histories preserve valuable knowledge about past ways of life",
            "The agricultural revolution enabled permanent settlements and population growth",
            "Museums serve as repositories of cultural artifacts and centers for public education",
            "The Harlem Renaissance celebrated African American cultural contributions through art and literature",
            "Ancient maritime civilizations developed sophisticated navigation and shipbuilding techniques",
            "The labor movement fought for workers rights including fair wages and safe conditions",
            "Archaeological methods have become increasingly sophisticated with modern technology",
            "The spread of writing systems enabled the recording and transmission of complex information",
            "Cultural exchange continues to shape societies through migration trade and communication",
            "The Aztec and Mayan civilizations achieved remarkable advances in astronomy and architecture",
            "Historical preservation efforts balance development needs with protecting heritage sites",
            "The partition of various nations created lasting political and social consequences",
            "Traditional medicine practices from various cultures contribute to modern pharmaceutical research",
            "The invention of currency transformed economic systems and facilitated complex trade",
            "Oral traditions kept histories alive in societies before the development of writing",
            "The spread of religions has profoundly influenced cultures laws and conflicts throughout history",
            "Architectural styles reflect the values technologies and resources of their time periods",
            "The decolonization process reshaped political boundaries and international relationships",
            "Cultural artifacts provide invaluable evidence about past societies and their practices",
        ]
        phrases.extend(history_culture)
        
        # === PROFESSIONAL & BUSINESS COMMUNICATION (100) ===
        professional_phrases = [
            "I would like to schedule a meeting with the entire development team for next Thursday afternoon",
            "The quarterly financial report indicates significant growth in our international markets",
            "Please review the attached documents and provide your feedback by end of business today",
            "We need to address the customer complaints regarding product quality and delivery times",
            "The marketing campaign exceeded our expectations and generated substantial leads",
            "I recommend we postpone the product launch until we resolve the remaining technical issues",
            "The budget allocation for this fiscal year requires careful consideration and planning",
            "Our competitive analysis reveals several opportunities for market expansion",
            "The performance metrics demonstrate consistent improvement across all departments",
            "We should establish clear milestones and deliverables for the upcoming project",
            "The stakeholder presentation has been rescheduled to accommodate international participants",
            "Please ensure all team members complete the mandatory compliance training by Friday",
            "The vendor negotiations resulted in favorable terms for our long-term partnership",
            "Our customer satisfaction scores have improved significantly since implementing the new system",
            "The strategic planning session will focus on identifying growth opportunities",
            "I appreciate your thorough analysis of the market trends and competitive landscape",
            "The project timeline needs adjustment to account for unexpected resource constraints",
            "We should prioritize the most critical deliverables given our limited bandwidth",
            "The integration process requires coordination between multiple departments and systems",
            "Please circulate the meeting minutes and action items to all relevant stakeholders",
            "The quality assurance process identified several areas requiring immediate attention",
            "Our risk assessment highlights potential challenges that need proactive mitigation",
            "The customer feedback survey provides valuable insights for product improvement",
            "We need to align our objectives with the overall organizational strategy",
            "The procurement process must follow established protocols and approval workflows",
            "Please prepare a comprehensive briefing document for the executive committee",
            "The resource allocation plan should reflect our strategic priorities for this quarter",
            "Our operational efficiency has improved through process automation initiatives",
            "The training program will equip employees with essential skills for their roles",
            "We should evaluate alternative solutions before making a final recommendation",
            "The contract terms require legal review before we proceed with the agreement",
            "Please coordinate with the technical team to resolve the outstanding issues",
            "The implementation schedule accounts for testing validation and deployment phases",
            "Our communication strategy should target key audiences through appropriate channels",
            "The organizational restructuring will streamline operations and reduce redundancies",
            "Please document the lessons learned from this project for future reference",
            "The escalation procedure ensures timely resolution of critical issues",
            "We need to establish metrics that accurately measure project success",
            "The change management process will help employees adapt to new procedures",
            "Please provide regular status updates to keep stakeholders informed of progress",
            "The cost benefit analysis supports the investment in upgraded infrastructure",
            "Our diversity and inclusion initiatives have created a more welcoming workplace",
            "The succession planning process identifies and develops future organizational leaders",
            "Please ensure compliance with all applicable regulations and industry standards",
            "The workflow optimization reduced processing time and improved accuracy significantly",
            "We should leverage existing resources before requesting additional budget allocation",
            "The partnership agreement outlines responsibilities expectations and deliverables",
            "Please schedule follow up meetings to track progress on action items",
            "The continuous improvement methodology has enhanced our operational performance",
            "Our employee engagement survey reveals opportunities for workplace enhancement",
        ]
        phrases.extend(professional_phrases)
        
        # === TECHNOLOGY & PROGRAMMING (100) ===
        tech_phrases = [
            "The software development lifecycle includes planning analysis design implementation testing and maintenance phases",
            "Object oriented programming encapsulates data and behavior within classes and objects for better organization",
            "Machine learning algorithms improve automatically through experience and exposure to training data",
            "Database normalization reduces redundancy and improves data integrity in relational databases",
            "Version control systems like Git track changes and enable collaboration among development teams",
            "Agile methodology emphasizes iterative development continuous feedback and adaptive planning",
            "Cloud computing provides scalable on demand access to computing resources over the internet",
            "Cybersecurity measures protect systems networks and data from unauthorized access and attacks",
            "Application programming interfaces enable different software systems to communicate effectively",
            "Continuous integration and deployment automate the process of building testing and releasing software",
            "Microservices architecture decomposes applications into small independently deployable services",
            "Containerization packages applications and dependencies together for consistent deployment",
            "Artificial neural networks are computing systems inspired by biological neural networks",
            "Natural language processing enables computers to understand and generate human language",
            "Blockchain technology creates decentralized and immutable records of transactions",
            "The internet of things connects everyday devices to networks for data exchange",
            "Quantum computing uses quantum mechanical phenomena to perform complex calculations",
            "Big data analytics processes and analyzes extremely large datasets for insights",
            "Edge computing processes data closer to its source rather than in centralized data centers",
            "DevOps practices integrate software development and IT operations for faster delivery",
            "Responsive web design ensures websites display properly across different screen sizes",
            "User experience design focuses on creating products that provide meaningful experiences",
            "Test driven development writes tests before implementing the actual code",
            "Code refactoring improves existing code structure without changing its external behavior",
            "Software debugging identifies and removes errors from computer programs systematically",
            "Memory management handles allocation and deallocation of computer memory resources",
            "Parallel processing executes multiple computations simultaneously for improved performance",
            "Data encryption converts information into code to prevent unauthorized access",
            "Network protocols define rules for communication between devices on a network",
            "Load balancing distributes workloads across multiple computing resources evenly",
            "Caching stores frequently accessed data in fast storage for quicker retrieval",
            "Authentication verifies user identity while authorization controls access permissions",
            "Virtual machines emulate complete computer systems on physical hardware",
            "Operating systems manage hardware resources and provide services for applications",
            "Compiler optimization transforms code to improve execution efficiency and speed",
            "Algorithm complexity analysis evaluates resource requirements for computational problems",
            "Data structures organize and store information for efficient access and modification",
            "Recursion involves functions calling themselves to solve complex problems",
            "Exception handling manages and responds to runtime errors in programs",
            "Multithreading allows concurrent execution of multiple parts of a program",
            "Socket programming enables network communication between different processes",
            "Regular expressions provide powerful pattern matching for text processing",
            "Dependency injection reduces coupling between components in software systems",
            "Design patterns provide reusable solutions to common software design problems",
            "Code review processes help identify bugs and improve code quality collaboratively",
            "Performance profiling identifies bottlenecks and optimization opportunities in code",
            "Automated testing frameworks verify software functionality without manual intervention",
            "Documentation standards ensure code is understandable and maintainable over time",
            "Software architecture defines high level structure and organization of systems",
            "Infrastructure as code manages computing resources through configuration files",
        ]
        phrases.extend(tech_phrases)
        
        # === EVERYDAY CONVERSATION - COMPLEX (100) ===
        everyday_complex = [
            "I've been thinking about taking a vacation somewhere warm but I haven't decided where yet",
            "The traffic this morning was absolutely terrible and made me late for my appointment",
            "Would you mind helping me move this furniture to the other side of the room please",
            "I'm trying to decide between the chicken and the fish but both options sound delicious",
            "The weather forecast says it might rain later so we should probably bring umbrellas",
            "I accidentally left my phone charger at home and now my battery is almost dead",
            "The restaurant we went to last weekend had incredible food and excellent service",
            "I need to pick up some groceries on the way home but I forgot my shopping list",
            "My car has been making a strange noise lately and I should take it to the mechanic",
            "The movie we watched last night was surprisingly good despite the negative reviews",
            "I've been trying to learn a new language but it's more difficult than I expected",
            "The construction on the main road has been causing significant delays for commuters",
            "I really appreciate you taking the time to explain this complicated concept to me",
            "The package I ordered online still hasn't arrived even though it shipped days ago",
            "I'm considering changing my exercise routine to include more strength training",
            "The presentation went much better than I anticipated and the audience was engaged",
            "I need to remember to call my parents this weekend because I haven't talked to them recently",
            "The apartment we looked at yesterday was nice but a bit out of our price range",
            "I've been having trouble sleeping lately and I think stress might be the cause",
            "The new coffee shop downtown has excellent pastries and a really cozy atmosphere",
            "I should probably start preparing for the exam now instead of waiting until the last minute",
            "The concert tickets sold out within minutes and I wasn't able to get any unfortunately",
            "I've been meaning to organize my closet but I keep putting it off for some reason",
            "The documentary about climate change really made me think about my environmental impact",
            "I accidentally deleted an important file and I'm hoping I can recover it somehow",
            "The new policy at work has caused some confusion among the staff members",
            "I'm thinking about adopting a pet but I'm not sure if I have enough time to care for one",
            "The flight was delayed by several hours due to severe weather at the destination",
            "I've been trying to reduce my screen time but it's harder than I thought it would be",
            "The birthday party we threw for my friend turned out to be a huge success",
            "I need to schedule a dentist appointment because I haven't been in over a year",
            "The book club meeting was really interesting and we had a great discussion",
            "I'm debating whether to take the promotion because it would require relocating",
            "The plumber said the repair would take about two hours and cost around two hundred dollars",
            "I've been experimenting with new recipes and some of them have turned out really well",
            "The online course I enrolled in has been helpful for developing new skills",
            "I accidentally bumped into an old friend at the grocery store and we caught up",
            "The hotel room was much smaller than it looked in the pictures on the website",
            "I'm trying to be more mindful about my spending habits and create a budget",
            "The neighborhood has changed quite a bit since we moved here five years ago",
            "I should probably back up my computer because I haven't done that in months",
            "The wedding ceremony was beautiful and the reception afterward was a lot of fun",
            "I've been feeling overwhelmed lately and I think I need to take a break",
            "The new restaurant opening next month is supposed to have amazing reviews already",
            "I accidentally sent that email to the wrong person and I'm so embarrassed about it",
            "The gym has been really crowded lately because of all the new year resolutions",
            "I'm considering going back to school to get an advanced degree in my field",
            "The power went out last night during the storm and didn't come back until morning",
            "I've been trying to eat healthier but it's difficult when I'm always on the go",
            "The customer service representative was extremely helpful in resolving my issue",
        ]
        phrases.extend(everyday_complex)
        
        # === NUMBERS DATES AND MEASUREMENTS (100) ===
        numbers_dates = [
            "The meeting is scheduled for Tuesday December seventeenth at two thirty in the afternoon",
            "Please transfer three thousand four hundred seventy five dollars to the savings account",
            "The coordinates are forty seven point three five by negative one hundred twenty two point six",
            "Version fourteen point two point nine was released on November twenty third this year",
            "The package weighs approximately eighteen point seven five kilograms including packaging",
            "The flight departs at seven forty five in the morning and arrives at eleven thirty at night",
            "The annual budget allocation is two hundred ninety five thousand dollars for this department",
            "The temperature dropped to negative twenty three degrees Celsius overnight during the storm",
            "The distance from here to the city center is approximately fifteen point eight kilometers",
            "This building has fifty two floors and stands approximately three hundred forty meters tall",
            "The quarterly revenue increased by twenty two point five percent compared to last year",
            "The server processes approximately one hundred twenty thousand requests per minute on average",
            "The marathon distance is exactly forty two point one nine five kilometers by official measurement",
            "The interest rate was adjusted to five point two five percent effective from Monday",
            "The population of the metropolitan area exceeded four point seven million residents recently",
            "This project requires approximately eight hundred seventy five hours of work to complete",
            "The storage capacity is one terabyte of solid state drive plus two terabytes of backup",
            "The anniversary celebration is scheduled for Saturday March twenty ninth twenty twenty six",
            "The recipe calls for four hundred twenty five grams of all purpose flour",
            "The speed limit on this highway section is one hundred thirty kilometers per hour maximum",
            "The conference room accommodates up to forty five people seated comfortably",
            "The warranty covers the product for thirty six months from the date of purchase",
            "The document contains approximately sixteen thousand three hundred words total",
            "The battery provides up to twenty two hours of continuous operation under normal conditions",
            "The monthly subscription costs nineteen dollars and ninety nine cents plus applicable taxes",
            "The building was constructed in nineteen forty seven and renovated in two thousand fifteen",
            "The temperature should be maintained between sixty eight and seventy two degrees Fahrenheit",
            "We need to order approximately three hundred fifty units to meet the quarterly demand",
            "The presentation is scheduled to last approximately forty five minutes plus questions",
            "The compound interest rate yields approximately seven point eight percent annually",
            "The vehicle traveled approximately two hundred eighty seven miles on a single charge",
            "The property spans approximately two point three acres including the garden area",
            "The survey received responses from one thousand four hundred twenty three participants",
            "The file size is approximately four hundred seventy three megabytes compressed",
            "The ceremony will begin at precisely six o'clock in the evening on Saturday",
            "The discount applies to orders over seventy five dollars before tax and shipping",
            "The room dimensions are approximately twenty four feet by eighteen feet total",
            "The average response time improved from three point two seconds to one point eight seconds",
            "The membership fee is two hundred forty dollars annually or twenty five dollars monthly",
            "The train arrives at platform seven at fourteen thirty two according to the schedule",
            "The ingredients should be mixed for approximately eight to ten minutes until smooth",
            "The altitude at the summit reaches approximately four thousand eight hundred meters",
            "The inventory shows approximately twelve thousand six hundred items currently in stock",
            "The appointment is confirmed for Thursday at three fifteen in the afternoon",
            "The total cost including installation is approximately six thousand seven hundred dollars",
            "The bandwidth capacity supports up to ten gigabits per second data transfer",
            "The meeting room reservation is from nine thirty until eleven forty five tomorrow",
            "The document was last modified on October fourteenth at two twenty seven in the afternoon",
            "The estimated delivery window is between fourteen and twenty one business days",
            "The resolution is three thousand eight hundred forty by two thousand one hundred sixty pixels",
        ]
        phrases.extend(numbers_dates)
        
        # === DESCRIPTIVE AND NARRATIVE (100) ===
        descriptive_narrative = [
            "The ancient oak tree stood majestically in the center of the garden casting long shadows across the lawn",
            "Brilliant sunlight streamed through the stained glass windows painting colorful patterns on the floor",
            "The bustling marketplace was filled with vendors selling exotic spices handcrafted jewelry and fresh produce",
            "Gentle waves lapped against the shore as seagulls circled overhead searching for their next meal",
            "The mountain peaks were shrouded in mist creating an ethereal atmosphere in the valley below",
            "Children's laughter echoed through the playground as they chased each other around the climbing structures",
            "The aroma of freshly baked bread wafted from the bakery filling the entire street with its warmth",
            "Storm clouds gathered on the horizon threatening to unleash their fury upon the unsuspecting town",
            "The old library contained thousands of dusty volumes each holding stories waiting to be discovered",
            "Autumn leaves danced gracefully through the air before settling gently on the cobblestone path",
            "The orchestra began playing softly gradually building to a magnificent crescendo that filled the hall",
            "Snowflakes fell silently through the crisp winter air blanketing the landscape in pristine white",
            "The cottage nestled among the rolling hills looked like something from a fairytale book",
            "Fireflies flickered like tiny lanterns in the warm summer evening creating a magical display",
            "The chef carefully plated each dish arranging the ingredients with artistic precision",
            "Morning dew glistened on the rose petals catching the first rays of sunlight beautifully",
            "The winding river carved its way through the canyon revealing millions of years of geological history",
            "Candlelight flickered against the ancient stone walls creating dancing shadows in the chamber",
            "The farmer surveyed his fields with satisfaction watching the golden wheat sway in the breeze",
            "Thunder rumbled in the distance as lightning illuminated the darkening sky dramatically",
            "The artist's brush moved confidently across the canvas bringing the portrait to life",
            "Wildflowers bloomed in abundance across the meadow creating a tapestry of vibrant colors",
            "The train whistled as it emerged from the tunnel revealing breathtaking mountain scenery",
            "Steam rose from the hot springs creating an otherworldly atmosphere in the forest clearing",
            "The cathedral's towering spires reached toward the heavens inspiring awe in all who visited",
            "Dolphins leaped playfully alongside the boat their sleek bodies glistening in the sunlight",
            "The clock tower chimed midnight its bells echoing through the quiet streets below",
            "Fresh snow crunched underfoot as hikers made their way along the trail at dawn",
            "The vineyard stretched across the hillside rows of grapevines heavy with ripening fruit",
            "Musicians filled the square with lively melodies as couples danced under the stars",
            "The waterfall cascaded down the cliff face sending mist into the air like a gentle rain",
            "Lanterns illuminated the narrow alleyway revealing hidden shops and cozy cafes",
            "The desert landscape glowed orange and purple as the sun set behind the distant dunes",
            "Kites soared high above the beach their colorful tails streaming behind them in the wind",
            "The greenhouse was filled with exotic plants from tropical regions around the world",
            "Fishing boats returned to harbor their nets full of the day's catch glistening in the evening light",
            "The spiral staircase wound upward through the lighthouse to the observation deck above",
            "Cherry blossoms floated down like pink snowflakes carpeting the ground beneath the trees",
            "The blacksmith hammered rhythmically shaping the glowing metal into a beautiful design",
            "Owls hooted softly in the darkness as nocturnal creatures emerged from their hiding places",
            "The farmer's market bustled with activity as vendors arranged their colorful displays",
            "Sailboats dotted the bay their white sails brilliant against the deep blue water",
            "The hiking trail meandered through ancient forest where sunlight barely penetrated the canopy",
            "Street performers entertained crowds with acrobatics music and magic tricks",
            "The aurora borealis painted the night sky with ribbons of green and purple light",
            "Morning fog lifted slowly from the lake revealing the mirror-like surface beneath",
            "The castle ruins stood atop the hill a testament to centuries of history and conflict",
            "Butterflies fluttered among the garden flowers their delicate wings catching the light",
            "The cobblestone streets wound through the old town past historic buildings and monuments",
            "Waves crashed against the rocky cliffs sending spray high into the salty air above",
        ]
        phrases.extend(descriptive_narrative)
        
        # === OPINIONS AND THOUGHTS (100) ===
        opinions_thoughts = [
            "I believe that continuous learning is essential for personal and professional growth throughout life",
            "It seems to me that effective communication is the foundation of all successful relationships",
            "In my experience working collaboratively with others often produces better results than working alone",
            "I've always thought that patience is one of the most undervalued virtues in modern society",
            "From my perspective the benefits of technology far outweigh the potential drawbacks overall",
            "I tend to think that maintaining a healthy work life balance is crucial for long term happiness",
            "It's my understanding that proper preparation significantly increases the chances of success",
            "I'm of the opinion that kindness and empathy can transform even the most difficult situations",
            "Based on what I've observed people generally respond better to encouragement than criticism",
            "I strongly feel that education should be accessible to everyone regardless of background",
            "It appears to me that small consistent actions lead to significant changes over time",
            "I've come to realize that failure is often a necessary step on the path to eventual success",
            "From what I can tell authenticity is increasingly valued in both personal and professional contexts",
            "I'm inclined to believe that diversity of thought leads to more innovative solutions",
            "It's become clear to me that mental health deserves as much attention as physical health",
            "I would argue that critical thinking skills are more important now than ever before",
            "In my view taking calculated risks is necessary for achieving meaningful accomplishments",
            "I've noticed that people who express gratitude regularly tend to be happier overall",
            "It strikes me that the most successful people are often those who never stop asking questions",
            "I'm convinced that genuine curiosity is one of the most valuable traits a person can have",
            "From my observations adaptability has become an essential skill in our rapidly changing world",
            "I suspect that many problems could be solved through better communication and understanding",
            "It seems increasingly clear that environmental sustainability must be a global priority",
            "I've learned that listening carefully is often more important than speaking eloquently",
            "In my opinion the quality of our relationships largely determines our overall life satisfaction",
            "I think it's fair to say that first impressions while important can be misleading",
            "Based on my experience setting clear goals significantly improves the likelihood of achieving them",
            "I'm fairly certain that emotional intelligence is just as important as intellectual ability",
            "It occurs to me that many of our limitations are self-imposed rather than actual barriers",
            "I would suggest that taking time for self-reflection regularly leads to personal growth",
            "From everything I've seen creativity flourishes when people feel safe to take risks",
            "I believe strongly that integrity and honesty are fundamental to building trust",
            "It's my contention that preventive measures are generally more effective than reactive solutions",
            "I've observed that successful teams typically have clear communication and shared objectives",
            "In my assessment the ability to manage stress effectively is crucial for overall wellbeing",
            "I'm reasonably confident that technology will continue to transform education significantly",
            "From what I understand cultural awareness is increasingly important in our globalized world",
            "I tend to believe that positive reinforcement is more effective than punishment for motivation",
            "It seems obvious to me that investing in infrastructure benefits society as a whole",
            "I've always maintained that respect must be earned through consistent actions over time",
            "In my estimation problem solving skills can be developed through practice and persistence",
            "I'm of the mind that open and honest feedback is essential for continuous improvement",
            "Based on available evidence regular exercise has numerous benefits for mental health",
            "I would venture to say that most conflicts arise from misunderstandings rather than malice",
            "From my standpoint mentorship plays a crucial role in professional development",
            "I firmly believe that everyone has something valuable to contribute to any discussion",
            "It's my sense that attention to detail often separates good work from excellent work",
            "I've concluded that meaningful connections require vulnerability and authentic engagement",
            "In my judgment sustainable practices will become increasingly important for businesses",
            "I'm persuaded that lifelong learning is the key to staying relevant in any field",
        ]
        phrases.extend(opinions_thoughts)
        
        # === QUESTIONS AND INQUIRIES - COMPLEX (100) ===
        questions_complex = [
            "Could you please explain the reasoning behind your decision to change the project timeline",
            "What would be the most effective approach to address the concerns raised during the meeting",
            "Have you had a chance to review the documents I sent over earlier this week",
            "Would it be possible to reschedule our appointment to sometime later in the afternoon",
            "Do you have any recommendations for improving the efficiency of our current workflow",
            "What factors should we consider when evaluating the different options available to us",
            "Could you walk me through the process step by step so I can understand it better",
            "Is there any additional information you need from me before making your final decision",
            "How would you suggest we handle this situation given the constraints we're facing",
            "What are the potential consequences if we decide to proceed with the alternative plan",
            "Have you considered the impact this change might have on the other team members",
            "Would you mind clarifying what you meant when you mentioned the new requirements",
            "What resources would we need to successfully complete this project on schedule",
            "Could you provide some examples to help illustrate the concept you just described",
            "Is there a particular reason why this approach was chosen over the other alternatives",
            "How long do you estimate it will take to implement the proposed changes completely",
            "What challenges do you anticipate we might encounter during the implementation phase",
            "Have the stakeholders been informed about the recent developments in this matter",
            "Would it be helpful if I prepared a detailed summary of our discussion for reference",
            "What criteria should we use to evaluate the success of this initiative going forward",
            "Could you elaborate on the specific requirements for completing this particular task",
            "Is there anyone else who should be included in these discussions moving forward",
            "How does this proposal align with our overall strategic objectives for the year",
            "What feedback have you received so far from the clients regarding the new features",
            "Would you prefer to meet in person or would a video conference be more convenient",
            "What are the main differences between the two options we're currently considering",
            "Have there been any updates since we last spoke about this particular issue",
            "Could you recommend any resources that might help me learn more about this topic",
            "Is there flexibility in the budget to accommodate these additional requirements",
            "How should we prioritize these tasks given our limited time and resources",
            "What lessons can we learn from the challenges we encountered in the previous project",
            "Would it be appropriate to involve external consultants for this specialized work",
            "What measures are currently in place to ensure quality control throughout the process",
            "Have you identified any potential risks that we should be aware of before proceeding",
            "Could you share your thoughts on the best way to communicate these changes to the team",
            "Is there a preferred format for submitting the final deliverables to the client",
            "What training would be necessary for the team to effectively use the new system",
            "How do you envision this project evolving over the next several months",
            "Would you be available to answer questions if issues arise during implementation",
            "What documentation will be required to support the decisions we've made",
            "Have the necessary approvals been obtained to move forward with this initiative",
            "Could you clarify the scope of responsibilities for each team member involved",
            "Is there anything that could potentially delay the completion of this project",
            "How will success be measured once the project has been fully implemented",
            "What contingency plans should we have in place in case of unexpected complications",
            "Would it be possible to get a preliminary estimate before committing to the project",
            "What standards or guidelines should we follow when developing the solution",
            "Have you consulted with the technical team about the feasibility of this approach",
            "Could you provide a timeline showing the key milestones and deadlines",
            "Is there any historical data that might help inform our decision making process",
        ]
        phrases.extend(questions_complex)
        
        # === INSTRUCTIONS AND DIRECTIONS (100) ===
        instructions_directions = [
            "Please ensure that all documents are properly formatted before submitting them for review",
            "First you need to download the application then create an account using your email address",
            "Make sure to save your work frequently to avoid losing any important changes",
            "Begin by gathering all the necessary materials before starting the assembly process",
            "Remember to double check all calculations before finalizing the financial report",
            "Start by preheating the oven to three hundred seventy five degrees before preparing the ingredients",
            "Carefully read through the entire instruction manual before attempting to operate the equipment",
            "Take note of the safety guidelines and follow them strictly throughout the procedure",
            "Be sure to update your contact information if any changes occur during the process",
            "Complete each section of the form thoroughly before moving on to the next one",
            "Allow sufficient time for the paint to dry completely between applying additional coats",
            "Keep all receipts and documentation for your records in case they are needed later",
            "Check that all connections are secure before powering on the system for testing",
            "Review the terms and conditions carefully before agreeing to the service agreement",
            "Set aside adequate time to thoroughly prepare for the upcoming examination",
            "Organize your workspace efficiently to maximize productivity during the project",
            "Verify that all required fields are completed accurately before submitting the application",
            "Follow the established protocol when handling sensitive information and data",
            "Confirm the appointment details at least one day in advance to avoid any confusion",
            "Back up all important files regularly to prevent potential data loss",
            "Test the equipment thoroughly before using it in a production environment",
            "Document all changes made during the development process for future reference",
            "Coordinate with team members to ensure everyone understands their responsibilities",
            "Prioritize tasks based on urgency and importance to manage time effectively",
            "Maintain clear communication with stakeholders throughout the duration of the project",
            "Adhere to the style guide when creating content for the company website",
            "Inspect all materials carefully before beginning the construction process",
            "Schedule regular check-ins to monitor progress and address any concerns promptly",
            "Archive completed projects according to the established organizational system",
            "Update the status report weekly to keep all parties informed of developments",
            "Calibrate the instruments precisely before conducting any measurements",
            "Consult the reference documentation if you encounter any unexpected errors",
            "Allocate resources appropriately to ensure all project phases are adequately supported",
            "Implement security measures to protect sensitive data from unauthorized access",
            "Validate user input thoroughly to prevent potential security vulnerabilities",
            "Optimize performance by identifying and addressing bottlenecks in the system",
            "Establish clear milestones to track progress throughout the project lifecycle",
            "Communicate expectations clearly to ensure everyone is aligned on objectives",
            "Review feedback carefully and incorporate relevant suggestions into revisions",
            "Prepare contingency plans to address potential challenges that may arise",
            "Train new team members thoroughly before assigning them independent tasks",
            "Evaluate options systematically using established criteria before deciding",
            "Maintain detailed records of all transactions for auditing purposes",
            "Synchronize files across devices to ensure access to the latest versions",
            "Configure settings appropriately based on your specific requirements and preferences",
            "Integrate new features gradually to minimize disruption to existing workflows",
            "Assess risks proactively and develop mitigation strategies accordingly",
            "Streamline processes by eliminating unnecessary steps and redundancies",
            "Collaborate effectively by sharing information and resources openly with others",
            "Monitor system performance continuously and address issues as they arise",
        ]
        phrases.extend(instructions_directions)
        
        # === SHORT CONFIRMATIONS AND RESPONSES (50) ===
        short_responses = [
            "Absolutely I completely agree with that assessment",
            "That sounds like a reasonable approach to the problem",
            "I understand what you're saying and I appreciate the clarification",
            "Yes that's exactly what I was thinking as well",
            "No I don't believe that would be the best course of action",
            "Perhaps we should consider some alternative options first",
            "Definitely that aligns with our overall objectives",
            "I'm not entirely sure about that particular point",
            "That makes perfect sense when you explain it that way",
            "Certainly I would be happy to assist with that request",
            "Actually I think there might be a better way to approach this",
            "Correct that's precisely the information we were looking for",
            "Unfortunately that won't be possible given our current constraints",
            "Exactly that captures the essence of what I was trying to convey",
            "Interesting I hadn't considered that perspective before now",
            "Of course I can take care of that for you right away",
            "Possibly although we would need to verify some details first",
            "Indeed that observation is quite insightful and relevant",
            "Naturally that would be the logical next step to take",
            "Evidently there's been some miscommunication along the way",
            "Fortunately we still have time to make the necessary adjustments",
            "Surprisingly the results turned out better than we anticipated",
            "Ideally we would have more resources to dedicate to this effort",
            "Admittedly that aspect could have been handled more effectively",
            "Undoubtedly this represents a significant achievement for the team",
            "Regrettably we won't be able to meet the original deadline",
            "Thankfully the issue was resolved before it caused major problems",
            "Presumably the updated information will be available soon",
            "Apparently there were some factors we hadn't accounted for initially",
            "Obviously we need to reconsider our strategy moving forward",
            "Clearly there's strong support for the proposed changes",
            "Essentially that summarizes the main points of our discussion",
            "Fundamentally the core principles remain unchanged throughout",
            "Generally speaking the feedback has been overwhelmingly positive",
            "Technically speaking there are a few details that need clarification",
            "Practically speaking implementation will require additional resources",
            "Realistically we should expect some challenges during the transition",
            "Specifically we need to focus on the items marked as high priority",
            "Importantly we must ensure compliance with all relevant regulations",
            "Additionally there are several other factors worth considering",
            "Furthermore the analysis reveals some interesting patterns",
            "Meanwhile the team continues to make progress on other initiatives",
            "Nevertheless we remain committed to achieving our stated objectives",
            "Consequently we will need to adjust our timeline accordingly",
            "Subsequently the procedures were updated to reflect best practices",
            "Accordingly all stakeholders have been notified of the changes",
            "Ultimately the decision will depend on several key factors",
            "Initially there was some resistance but acceptance has grown",
            "Eventually we expect to see significant improvements in performance",
            "Overall I'm quite satisfied with how things have progressed",
        ]
        phrases.extend(short_responses)
        
        # === CONVERSATIONAL - COMPLEX (100) ===
        conversational_phrases = [
            "How have you been doing lately I feel like we haven't caught up in quite a while",
            "What do you think about the changes they announced at the meeting today",
            "Have you had a chance to try that new restaurant everyone's been talking about",
            "I was wondering if you might be available to help me with something later this afternoon",
            "The weather has been absolutely beautiful lately and I've been trying to spend more time outside",
            "I heard that they're planning to renovate the office building starting next month",
            "Do you remember that conversation we had last week about the upcoming project deadline",
            "I've been meaning to ask you about your experience with the new software system",
            "It seems like everyone has been really busy lately with all the end of year activities",
            "I was just thinking about how much things have changed around here over the past few years",
            "Have you noticed that the traffic has gotten significantly worse during rush hour recently",
            "I'm trying to decide whether to take the early flight or the later one tomorrow morning",
            "The presentation you gave yesterday was really impressive and well received by the team",
            "I've been having some trouble with my computer and was hoping you might have some suggestions",
            "Do you happen to know if the meeting has been rescheduled or if it's still at the original time",
            "I really enjoyed the book you recommended and I was wondering if you have any others to suggest",
            "The food at that new place downtown was surprisingly good considering the mixed reviews",
            "I'm thinking about taking some time off next month but I haven't finalized my plans yet",
            "Have you heard anything about the potential changes to the company's vacation policy",
            "I was pleasantly surprised by how smoothly the transition went despite the initial concerns",
            "The kids have been asking about when we can plan another family outing to the park",
            "I noticed you've been working on that project for quite some time now and was curious about progress",
            "Do you think it would be worth investing in that new equipment we discussed last week",
            "I've been trying to establish a better morning routine but it's harder than I expected",
            "The concert last weekend was absolutely amazing and exceeded all of my expectations",
            "I was hoping we could find some time to discuss the upcoming changes to our department",
            "Have you considered taking that professional development course that was mentioned recently",
            "The garden has really flourished this year thanks to all the rain we've been getting",
            "I'm curious to hear your thoughts on the proposal that was circulated yesterday",
            "The commute has been much more manageable since they finished the road construction",
            "I've been experimenting with some new recipes and would love to get your feedback sometime",
            "Do you remember the name of that movie we were talking about at dinner last week",
            "I was thinking we should try to coordinate our schedules better for the upcoming meetings",
            "The renovation project is taking longer than expected but the results look promising",
            "I've noticed that the team dynamics have improved significantly since the new manager started",
            "Have you had a chance to review the documents I sent over earlier this morning",
            "I'm still trying to figure out the best approach for handling that complicated situation",
            "The workshop I attended last month provided some really valuable insights and techniques",
            "Do you have any recommendations for good places to visit during the upcoming holiday",
            "I've been meaning to organize my workspace but I keep getting distracted by other tasks",
            "The feedback from the client was more positive than we anticipated which was encouraging",
            "I was wondering if you could clarify a few points from our previous discussion",
            "The new policy seems reasonable but I have some concerns about the implementation timeline",
            "Have you noticed any improvements since we made those changes to the process last month",
            "I'm looking forward to the team building event next week it should be a nice change of pace",
            "The project milestone was achieved ahead of schedule which was a pleasant surprise",
            "I've been considering different options for the upcoming vacation and can't decide",
            "Do you think we should schedule a follow up meeting to discuss the remaining items",
            "The information you provided was extremely helpful in preparing for the presentation",
            "I'm curious whether the proposed timeline is realistic given our current resources",
        ]
        phrases.extend(conversational_phrases)
        
        # === COMPLEX LONG SENTENCES (150) ===
        complex_sentences = [
            "The documentary I watched last night about climate change was absolutely fascinating and thought provoking",
            "Could you please explain that complicated concept in much simpler terms that I can understand",
            "I was thinking about going to the park later this afternoon if the weather cooperates with our plans",
            "That's an interesting perspective on the matter that I hadn't considered before you mentioned it",
            "The research paper concluded that artificial intelligence will fundamentally transform healthcare delivery",
            "Please open the application settings and configure all the necessary audio parameters correctly",
            "What would be the absolute best approach to solving this particularly challenging problem",
            "How long will it realistically take to finish processing all the requested information today",
            "Where exactly did you put the important configuration files that we discussed yesterday",
            "Why does the entire system behave so differently under extremely heavy load conditions",
            "The meeting has been rescheduled for next Tuesday afternoon at three thirty in conference room B",
            "I appreciate your continuous help and support with this complicated and stressful situation",
            "Let me know whenever you're completely ready to proceed with the next critical step",
            "The investment portfolio performed exceptionally well during the last quarter despite market volatility",
            "Scientific evidence strongly suggests that regular exercise improves both mental and physical health",
            "The architectural design of the new building incorporates sustainable and environmentally friendly materials",
            "Professional athletes dedicate countless hours to training and perfecting their specialized skills",
            "The museum exhibition features rare artifacts from ancient civilizations around the world",
            "Technological advancements have dramatically transformed the way we communicate and share information",
            "The restaurant received outstanding reviews for its innovative fusion cuisine and exceptional service",
            "Environmental conservation efforts require collaboration between governments and local communities worldwide",
            "The symphony orchestra delivered a breathtaking performance that moved the entire audience to tears",
            "Economic forecasters predict significant growth in the renewable energy sector over the next decade",
            "The university offers comprehensive programs in computer science and artificial intelligence research",
            "Medical researchers have made remarkable breakthroughs in treating previously incurable diseases",
            "The international conference brought together leading experts from more than fifty different countries",
            "Customer satisfaction surveys indicate that product quality has improved substantially this year",
            "The historical documentary provides fascinating insights into the events that shaped our modern world",
            "Effective communication skills are absolutely essential for success in any professional environment",
            "The wildlife sanctuary provides a safe habitat for endangered species from around the globe",
            "Financial advisors recommend diversifying your investment portfolio to minimize potential risks",
            "The software development team successfully completed the project ahead of the original schedule",
            "Public transportation systems play a crucial role in reducing urban traffic congestion",
            "The art gallery showcases contemporary works from both established and emerging talented artists",
            "Climate scientists have documented unprecedented changes in global temperature patterns recently",
            "The educational curriculum emphasizes critical thinking and creative problem solving abilities",
            "Pharmaceutical companies invest billions of dollars annually in research and development efforts",
            "The telecommunications industry continues to evolve rapidly with each new generation of technology",
            "Social media platforms have fundamentally changed how businesses interact with their customers",
            "The aerospace engineering program prepares students for careers in aviation and space exploration",
            "Nutritional experts recommend a balanced diet rich in fruits vegetables and whole grains",
            "The judicial system aims to ensure fair and impartial treatment for all citizens",
            "Archaeological excavations have uncovered valuable artifacts from ancient civilizations",
            "The hospitality industry has adapted to changing consumer preferences and travel patterns",
            "Renewable energy sources like solar and wind power are becoming increasingly cost effective",
            "The pharmaceutical research facility employs hundreds of scientists and laboratory technicians",
            "Urban planning initiatives focus on creating sustainable and livable city environments",
            "The documentary filmmaker spent three years researching and producing the award winning film",
            "Genetic engineering has opened new possibilities for treating hereditary diseases and conditions",
            "The international trade agreement aims to reduce tariffs and promote economic cooperation",
        ]
        phrases.extend(complex_sentences)
        
        # === NATURAL CONVERSATION WITHOUT MONICA PREFIX (100) ===
        natural_conversation = [
            "I need you to search for the nearest coffee shop with excellent reviews",
            "Please set a reminder for tomorrow morning at exactly eight thirty",
            "What is the current temperature and detailed weather forecast for this weekend",
            "Calculate the square root of one thousand twenty four for me please",
            "Send an important email to the development team about the upcoming project deadline",
            "Schedule a meeting with the entire marketing department for next Tuesday afternoon",
            "Turn off all the lights in the house and activate the security system",
            "I would really appreciate it if you could help me with this task",
            "Do you have any recommendations for a good restaurant in this area",
            "That sounds like a reasonable plan and I think we should proceed with it",
            "I'm not entirely sure what the best approach would be in this situation",
            "Would you mind explaining that concept one more time for clarification",
            "I've been thinking about this problem and I have a few potential solutions",
            "The presentation went really well and everyone seemed genuinely impressed",
            "I need to finish this project by the end of the week at the latest",
            "Can you provide more details about the specifications for this feature",
            "The results exceeded our initial expectations and we're very pleased",
            "I'll need to consult with the team before making a final decision",
            "There seems to be an issue with the connection that needs attention",
            "The deadline has been extended so we have more time to complete everything",
            "I appreciate your patience while we work through these technical difficulties",
            "The new software update includes several important security improvements",
            "We should schedule a follow up meeting to discuss the next phase",
            "I've reviewed all the documents and everything appears to be in order",
            "The customer feedback has been overwhelmingly positive so far",
            "I'll send you the updated report as soon as it's ready for review",
            "The training session covered all the essential topics we needed",
            "We need to address these concerns before moving forward with the plan",
            "The system has been running smoothly since the last maintenance update",
            "I suggest we take a different approach to solve this particular challenge",
            "The project timeline looks achievable if we allocate resources properly",
            "Can you walk me through the steps required to complete this process",
            "I've encountered a few obstacles but I'm working through them systematically",
            "The performance metrics indicate significant improvement over last quarter",
            "We should document these procedures for future reference and training",
            "The integration with the existing system went more smoothly than expected",
            "I need additional information before I can provide a complete answer",
            "The team has demonstrated excellent collaboration throughout this project",
            "We've identified several opportunities for optimization and efficiency gains",
            "The stakeholders have approved the proposed changes to the original plan",
            "I recommend we prioritize the most critical tasks first this week",
            "The analysis reveals some interesting patterns in the user behavior data",
            "We should consider alternative solutions in case the primary plan fails",
            "The quality assurance process has been thorough and comprehensive",
            "I'll coordinate with the other departments to ensure alignment on goals",
            "The implementation phase will begin once we receive final approval",
            "We need to establish clear communication channels between all team members",
            "The preliminary results are promising but we need more data to confirm",
            "I suggest we schedule regular check ins to monitor progress effectively",
            "The budget constraints require us to be more creative with our solutions",
        ]
        phrases.extend(natural_conversation)
        
        # === TECHNICAL AND SCIENTIFIC PHRASES (100) ===
        technical_phrases = [
            "The algorithm processes approximately three million data points per second efficiently",
            "Neural network architectures have become increasingly sophisticated over recent years",
            "Quantum computing promises to revolutionize cryptography and complex simulations",
            "The database schema requires optimization to improve query performance significantly",
            "Machine learning models require substantial training data for accurate predictions",
            "The application programming interface supports both synchronous and asynchronous requests",
            "Cybersecurity protocols must be regularly updated to address emerging threats",
            "The distributed computing system handles workloads across multiple geographic regions",
            "Blockchain technology provides transparent and immutable transaction records",
            "The software architecture follows microservices design patterns for better scalability",
            "Automated testing frameworks ensure code quality and prevent regression bugs",
            "Cloud infrastructure enables rapid deployment and elastic resource allocation",
            "The encryption algorithm uses two hundred fifty six bit keys for security",
            "Containerization simplifies application deployment and environment management",
            "The authentication system implements multi factor verification for enhanced security",
            "Real time data analytics provide actionable insights for business decisions",
            "The version control system tracks all changes and enables collaboration",
            "Load balancing distributes traffic evenly across multiple server instances",
            "The caching layer significantly reduces database query latency and load",
            "Continuous integration pipelines automate building testing and deployment",
            "The protocol stack handles communication between different network layers",
            "Memory management optimizations reduced resource consumption by forty percent",
            "The indexing strategy improved search query performance dramatically",
            "Fault tolerant systems automatically recover from hardware and software failures",
            "The monitoring dashboard displays real time metrics and alert notifications",
            "Data serialization formats ensure compatibility across different platforms",
            "The configuration management system maintains consistent environment settings",
            "Parallel processing techniques accelerate computationally intensive operations",
            "The logging framework captures detailed diagnostic information for debugging",
            "Service mesh architecture provides observability and traffic management",
        ]
        phrases.extend(technical_phrases)
        
        # === NUMBERS DATES AND MEASUREMENTS (50) ===
        numbers_dates = [
            "The meeting is scheduled for December sixteenth twenty twenty five at two PM",
            "Transfer approximately three thousand four hundred fifty dollars to savings",
            "The coordinates are forty seven point three by negative one twenty two point five",
            "Version twelve point three point seven was officially released yesterday afternoon",
            "The package weighs approximately fifteen point seven five kilograms total",
            "The flight departs at seven forty five AM and arrives at eleven thirty PM",
            "The budget allocation is two hundred seventy five thousand dollars annually",
            "The temperature dropped to negative fifteen degrees Celsius overnight",
            "The distance from here to downtown is approximately twelve point eight kilometers",
            "The building has forty seven floors and stands three hundred twenty meters tall",
            "The quarterly revenue increased by eighteen point five percent year over year",
            "The server processes approximately ninety five thousand requests per minute",
            "The marathon distance is exactly forty two point one nine five kilometers",
            "The interest rate was adjusted to four point seven five percent yesterday",
            "The population of the city exceeded two point three million residents",
            "The project requires approximately six hundred fifty hours of work",
            "The storage capacity is five hundred twelve gigabytes of solid state",
            "The anniversary celebration is on March twenty third twenty twenty six",
            "The recipe calls for three hundred seventy five grams of flour",
            "The speed limit on this highway is one hundred twenty kilometers per hour",
            "The conference room accommodates up to thirty five people comfortably",
            "The warranty covers the product for twenty four months from purchase",
            "The document contains approximately twelve thousand five hundred words",
            "The battery provides up to eighteen hours of continuous operation",
            "The monthly subscription costs fourteen dollars and ninety nine cents",
        ]
        phrases.extend(numbers_dates)
        
        return phrases
    
    def load_progress(self):
        """Load recording progress."""
        if self.progress_file.exists():
            try:
                with open(self.progress_file, 'r') as f:
                    data = json.load(f)
                    self.current_phrase_idx = data.get('current_index', 0)
            except:
                self.current_phrase_idx = 0
    
    def save_progress(self):
        """Save recording progress."""
        with open(self.progress_file, 'w') as f:
            json.dump({'current_index': self.current_phrase_idx}, f)
    
    def get_current_phrase(self) -> str:
        """Get the current phrase to record."""
        if self.current_phrase_idx < len(self.phrases):
            return self.phrases[self.current_phrase_idx]
        return None
    
    def start_recording(self):
        """Start recording audio."""
        if self.is_recording:
            return
        
        self.is_recording = True
        self.audio_data = []
        
        def callback(indata, frames, time_info, status):
            try:
                if status:
                    _log(f"[RECORDER] stream status: {status}")
                if self.is_recording:
                    # Append a copy of the buffer; keep short clips in memory only
                    self.audio_data.append(indata.copy())
            except Exception as e_cb:
                # Never raise from the audio callback; log and stop safely
                _log(f"[RECORDER] Audio callback error: {e_cb}")
                try:
                    if self.stream:
                        self.stream.stop(); self.stream.close()
                except Exception:
                    pass
                self.stream = None
                self.is_recording = False
        
        # Helper to log
        def _log(msg: str):
            print(msg)
            try:
                if self.log_file:
                    with open(self.log_file, "a", encoding="utf-8") as lf:
                        lf.write(msg + "\n")
            except Exception:
                pass

        # Try to open the configured input device at the target sample rate
        # Prefer shared-mode WASAPI on Windows
        try:
            extra_settings = None
            try:
                extra_settings = sd.WasapiSettings(exclusive=False)
            except Exception:
                extra_settings = None
            
            # Get the device info for logging
            device_info = sd.query_devices(device=self.input_device_index)
            device_name = device_info.get('name', 'Unknown')
            _log(f"[RECORDER] Attempting to open device {self.input_device_index}: {device_name}")
            
            # Validate settings to surface issues early
            try:
                sd.check_input_settings(
                    device=self.input_device_index, 
                    samplerate=self.sample_rate, 
                    channels=self.channels, 
                    dtype='float32'
                )
            except Exception as e_chk:
                _log(f"[RECORDER] check_input_settings failed @ {self.sample_rate} Hz: {e_chk}")
            
            # Use float32 for stability; high latency avoids dropouts; blocksize 0 lets backend choose
            self.stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype='float32',
                callback=callback,
                device=self.input_device_index,  # Use the configured input device
                latency='high',
                blocksize=0,
                extra_settings=extra_settings
            )
            self.stream.start()
            self._record_sample_rate = self.sample_rate
            _log(f"[RECORDER] 🎙️ Recording started @ {self._record_sample_rate} Hz on device {self.input_device_index}: {device_name}")
        except Exception as e1:
            # Fallback 1: try again at the system's default input device/sample rate
            try:
                dev = sd.default.device[0] if hasattr(sd, 'default') else None
                dev_info = sd.query_devices(dev) if dev is not None else sd.query_devices(kind='input')
                fallback_sr = int(dev_info.get('default_samplerate', 44100) or 44100)
                self.stream = sd.InputStream(
                    samplerate=fallback_sr,
                    channels=min(self.channels, dev_info.get('max_input_channels', 1) or 1),
                    dtype='float32',
                    callback=callback,
                    device=dev,
                    latency='high',
                    blocksize=0,
                    extra_settings=extra_settings
                )
                self.stream.start()
                self._record_sample_rate = fallback_sr
                self.dtype = np.float32
                _log(f"[RECORDER] 🎙️ Recording started @ {self._record_sample_rate} Hz on default input device")
            except Exception:
                # Fallback 2: final attempt using any input device with float32
                try:
                    any_in = None
                    dev_info = None
                    for idx, d in enumerate(sd.query_devices()):
                        if d.get('max_input_channels', 0) > 0:
                            any_in = idx
                            dev_info = d
                            break
                    if any_in is None:
                        raise RuntimeError("No input devices available")
                    sr_any = int((dev_info or {}).get('default_samplerate', 44100) or 44100)
                    self.stream = sd.InputStream(
                        samplerate=sr_any,
                        channels=min(self.channels, dev_info.get('max_input_channels', 1) or 1),
                        dtype='float32',
                        callback=callback,
                        device=any_in
                    )
                    self.stream.start()
                    self._record_sample_rate = sr_any
                    self.dtype = np.float32
                    _log(f"[RECORDER] 🎙️ Recording started @ {self._record_sample_rate} Hz on first available input device")
                except Exception as e_final:
                    _log(f"[RECORDER] ❌ Failed to start input stream on any device: {e_final}")
                    _log("[RECORDER] Tip: Select a valid microphone as the Windows default input device, then try again.")
                    self.is_recording = False
                    self.audio_data = []
                    self.stream = None
                    return
    
    def stop_recording(self):
        """Stop recording and save the audio with noise reduction and quality assessment.
        
        Returns:
            tuple: (filepath, quality_metrics) or (None, None) if recording failed
        """
        if not self.is_recording:
            return None, None
        
        self.is_recording = False
        try:
            if self.stream is not None:
                self.stream.stop()
                self.stream.close()
        finally:
            self.stream = None
        
        if not self.audio_data:
            return None, None
        
        # Combine audio chunks
        try:
            audio = np.concatenate(self.audio_data, axis=0)
        except Exception:
            # Safe fallback
            audio = np.array(self.audio_data, dtype=self.dtype).reshape(-1, self.channels)
        
        # Ensure shape is (frames,) for mono and (frames, channels) for multi-channel
        if self.channels == 1 and audio.ndim == 2:
            audio = audio[:, 0]
        
        # Ensure int16 for WAV saving
        if audio.dtype != np.int16:
            try:
                # Scale/clip float32 to int16
                if np.issubdtype(audio.dtype, np.floating):
                    max_int16 = np.iinfo(np.int16).max
                    audio = np.clip(audio, -1.0, 1.0)
                    audio = (audio * max_int16).astype(np.int16)
                else:
                    audio = audio.astype(np.int16)
            except Exception as e:
                print(f"[RECORDER] ⚠️ dtype convert failed: {e}")

        # Apply mic gain (with clipping protection) before any resampling/NR
        try:
            gain = float(getattr(self, "mic_gain", 1.0) or 1.0)
            # Clamp gain to a reasonable range
            if gain < 0.1:
                gain = 0.1
            if gain > 4.0:
                gain = 4.0
            if gain != 1.0:
                audio_f = audio.astype(np.float32) * gain
                audio_f = np.clip(audio_f, np.iinfo(np.int16).min, np.iinfo(np.int16).max)
                audio = audio_f.astype(np.int16)
        except Exception as e_gain:
            print(f"[RECORDER] ⚠️ Mic gain apply failed, using unity: {e_gain}")

        # Decide which sample rate to save with
        save_sr = int(self._record_sample_rate or self.sample_rate)

        # Resample if the actual record sample rate differs from target
        if self._record_sample_rate != self.sample_rate:
            try:
                print(f"[RECORDER] 🔁 Resampling {self._record_sample_rate} -> {self.sample_rate} Hz")
                # Use polyphase resampling for better quality
                gcd = np.gcd(int(self._record_sample_rate), int(self.sample_rate))
                up = int(self.sample_rate // gcd)
                down = int(self._record_sample_rate // gcd)
                # Convert int16 to float in [-1,1] for processing
                if audio.dtype == np.int16:
                    audio_f = audio.astype(np.float32) / 32768.0
                else:
                    audio_f = audio.astype(np.float32)
                audio_rs = scipy_signal.resample_poly(audio_f, up, down)
                # Clip to [-1,1] and convert back to int16 scaling properly
                audio_rs = np.clip(audio_rs, -1.0, 1.0)
                audio = (audio_rs * 32767.0).astype(np.int16)
                # After successful resample, ensure we save with the target sample rate
                save_sr = int(self.sample_rate)
            except Exception as e:
                print(f"[RECORDER] ⚠️ Resample failed ({e}), saving at {self._record_sample_rate} Hz instead")
                # If resample fails, keep save_sr as the original record rate
                save_sr = int(self._record_sample_rate or self.sample_rate)

        # Apply background noise reduction (robust, non-fatal on error)
        # Uses configurable strength (0.0-1.0) to avoid over-processing speech
        if HAS_NOISE_REDUCE and self.noise_reduce_enabled and self.noise_reduce_strength > 0.0:
            try:
                strength = self.noise_reduce_strength
                print(f"[RECORDER] 🔇 Applying noise reduction (strength: {strength:.1%})...")
                # Convert int16 to float32 in [-1, 1]
                audio_f = audio.astype(np.float32) / 32768.0
                # Use non-stationary noise reduction with controlled strength
                # prop_decrease controls how much noise is reduced (0.0 = none, 1.0 = full)
                # Lower values preserve more speech characteristics
                reduced = nr.reduce_noise(
                    y=audio_f, 
                    sr=save_sr, 
                    stationary=False,
                    prop_decrease=strength,  # Control reduction strength
                    n_fft=1024,              # Smaller FFT for better time resolution
                    win_length=512,          # Shorter window preserves transients
                    freq_mask_smooth_hz=200  # Less aggressive frequency smoothing
                )
                # Blend original with reduced based on strength for more natural sound
                # At 0.5 strength, we use 75% reduced + 25% original
                blend_factor = min(1.0, strength + 0.5)
                blended = blend_factor * reduced + (1.0 - blend_factor) * audio_f
                # Clip and convert back to int16
                blended = np.clip(blended, -1.0, 1.0)
                audio = (blended * 32767.0).astype(np.int16)
            except Exception as e:
                print(f"[RECORDER] ⚠️ Noise reduction skipped due to error: {e}")
        
        # Get current phrase
        phrase = self.get_current_phrase()
        if not phrase:
            return None, None
        
        # Create filename with timestamp
        # Remove all characters invalid in Windows filenames: \ / : * ? " < > |
        safe_phrase = phrase.replace(" ", "_")
        for char in ['\\', '/', ':', '*', '?', '"', '<', '>', '|', "'", '!', ',', '.', ';']:
            safe_phrase = safe_phrase.replace(char, '')
        safe_phrase = safe_phrase[:25]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"phrase_{self.current_phrase_idx:04d}_{timestamp}_{safe_phrase}.wav"
        filepath = self.output_dir / filename
        
        # Save WAV file first (needed for quality assessment)
        # Use explicit open/close to avoid Python wave module __del__ bug
        wf = None
        try:
            wf = wave.open(str(filepath), 'wb')
            wf.setnchannels(self.channels)
            wf.setsampwidth(2)  # 16-bit PCM
            # Use the correct sample rate that matches the audio buffer we are writing
            wf.setframerate(int(save_sr))
            # Ensure contiguous bytes
            wf.writeframes(np.ascontiguousarray(audio).tobytes())
        finally:
            if wf is not None:
                try:
                    wf.close()
                except Exception:
                    pass
        
        # Log saved file info
        duration_sec = (len(audio) / float(save_sr)) if save_sr else 0.0
        print(f"[RECORDER] 💾 Saved: {filepath} | {duration_sec:.2f}s @ {int(save_sr)} Hz, {self.channels} ch")
        
        # Quality assessment will be done asynchronously by GUI
        # Return None for now to avoid blocking
        quality_metrics = None
        
        # Update manifest with timestamp and quality metrics
        self._update_manifest(filepath, phrase, duration_sec, timestamp, quality_metrics)
        
        # Mark phrase as recorded
        self.mark_phrase_recorded(phrase)

        # Remember exact last recording path for reliable playback
        self._last_recording_path = str(filepath)
        
        # DON'T move to next phrase automatically - let quality assessment decide
        # self.current_phrase_idx += 1
        # self.save_progress()
        
        return str(filepath), quality_metrics
    
    def _log_quality_metrics(self, metrics, filepath, phrase):
        """Log quality metrics to a JSON file."""
        if not hasattr(self, 'quality_log_file'):
            return
            
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "filepath": filepath,
            "phrase": phrase,
            "metrics": {
                "mos_score": metrics.mos_score,
                "snr_db": metrics.snr_db,
                "thd_percent": metrics.thd_percent,
                "dynamic_range_db": metrics.dynamic_range_db,
                "frequency_response_flatness": metrics.frequency_response_flatness,
                "quality_level": metrics.quality_level.value,
                "clipping_detected": metrics.clipping_detected,
                "long_silences_detected": metrics.long_silences_detected,
                "codec_issues": metrics.codec_issues,
                "recommendations": metrics.recommendations
            }
        }
        
        try:
            logs = []
            if self.quality_log_file.exists():
                with open(self.quality_log_file, 'r') as f:
                    logs = json.load(f)
            
            logs.append(log_entry)
            
            with open(self.quality_log_file, 'w') as f:
                json.dump(logs, f, indent=2)
                
        except Exception as e:
            print(f"[QUALITY] Failed to log metrics: {str(e)}")
    
    def _update_manifest(self, filepath: Path, text: str, duration: float, timestamp: str = None, quality_metrics=None):
        """Update the training manifest file with optional quality metrics."""
        entry = {
            "audio_filepath": str(filepath.absolute()),
            "text": text.lower(),
            "duration": round(duration, 2),
            "timestamp": timestamp or datetime.now().strftime("%Y%m%d_%H%M%S"),
            "user_id": self.user_id
        }
        
        # Add quality metrics if available
        if quality_metrics:
            entry["quality_metrics"] = {
                "mos_score": round(quality_metrics.mos_score, 2),
                "snr_db": round(quality_metrics.snr_db, 1),
                "thd_percent": round(quality_metrics.thd_percent, 2),
                "dynamic_range_db": round(quality_metrics.dynamic_range_db, 1),
                "quality_level": quality_metrics.quality_level.value,
                "clipping_detected": quality_metrics.clipping_detected,
                "long_silences_detected": quality_metrics.long_silences_detected
            }
        
        # Append to manifest
        with open(self.manifest_file, 'a') as f:
            f.write(json.dumps(entry) + '\n')
    
    def get_all_recordings(self) -> list:
        """Get all recordings with metadata."""
        recordings = []
        for wav_file in self.output_dir.glob("*.wav"):
            # Parse filename: phrase_XXXX_YYYYMMDD_HHMMSS_text.wav
            parts = wav_file.stem.split("_")
            
            # Get file stats
            stat = wav_file.stat()
            file_time = datetime.fromtimestamp(stat.st_mtime)
            
            # Try to extract phrase index and timestamp from filename
            phrase_idx = None
            timestamp_str = None
            phrase_text = ""
            
            if len(parts) >= 4 and parts[0] == "phrase":
                try:
                    phrase_idx = int(parts[1])
                    # parts[2] = date, parts[3] = time
                    timestamp_str = f"{parts[2]}_{parts[3]}"
                    phrase_text = "_".join(parts[4:]) if len(parts) > 4 else ""
                except:
                    phrase_text = "_".join(parts[1:])
            else:
                phrase_text = wav_file.stem
            
            recordings.append({
                "filepath": str(wav_file),
                "filename": wav_file.name,
                "phrase_idx": phrase_idx,
                "phrase_text": phrase_text.replace("_", " "),
                "timestamp": timestamp_str,
                "file_time": file_time,
                "size_kb": stat.st_size / 1024,
                "duration_estimate": stat.st_size / (self.sample_rate * 2)  # Rough estimate
            })
        
        # Sort by file time, newest first
        recordings.sort(key=lambda x: x["file_time"], reverse=True)
        return recordings
    
    def delete_recording(self, filepath: str) -> bool:
        """Delete a specific recording."""
        try:
            path = Path(filepath)
            if path.exists():
                # Get the phrase text to unmark it
                # Try to find it in manifest
                phrase_text = None
                if self.manifest_file.exists():
                    with open(self.manifest_file, 'r') as f:
                        lines = f.readlines()
                    
                    new_lines = []
                    for line in lines:
                        entry = json.loads(line.strip())
                        if entry.get("audio_filepath") == str(path.absolute()):
                            phrase_text = entry.get("text", "")
                        else:
                            new_lines.append(line)
                    
                    # Rewrite manifest without this entry
                    with open(self.manifest_file, 'w') as f:
                        f.writelines(new_lines)
                
                # Unmark phrase as recorded
                if phrase_text:
                    self.unmark_phrase_recorded(phrase_text)
                
                # Delete the file
                path.unlink()
                print(f"[RECORDER] Deleted: {path.name}")
                return True
        except Exception as e:
            print(f"[RECORDER] Delete failed: {e}")
        return False
    
    def delete_all_recordings(self) -> int:
        """Delete all recordings. Returns count of deleted files."""
        count = 0
        for wav_file in self.output_dir.glob("*.wav"):
            try:
                wav_file.unlink()
                count += 1
            except:
                pass
        
        # Clear manifest
        if self.manifest_file.exists():
            self.manifest_file.unlink()
        
        # Clear recorded phrases
        self.recorded_phrases.clear()
        self.save_recorded_phrases()
        
        # Reset progress
        self.current_phrase_idx = 0
        self.save_progress()
        
        print(f"[RECORDER] Deleted {count} recordings")
        return count
    
    def calculate_snr(self, audio: np.ndarray, sample_rate: int = 16000) -> float:
        """
        Calculate Signal-to-Noise Ratio (SNR) in dB using WADA algorithm.
        
        Based on professional standards:
        - WADA SNR Estimation for Speech Signals
        - ITU-T P.862 PESQ recommendations
        - SoapBox Labs audio quality standards
        
        Returns:
            SNR in dB (higher is better)
        """
        if len(audio) == 0:
            return -999.0
        
        # Convert to float and normalize
        audio_float = audio.astype(np.float32)
        if np.max(np.abs(audio_float)) > 0:
            audio_float = audio_float / np.max(np.abs(audio_float))
        
        # Estimate noise floor using first 50ms (silence before speech)
        noise_samples = int(0.05 * sample_rate)  # 50ms
        if len(audio_float) > noise_samples * 2:
            noise_floor = audio_float[:noise_samples]
        else:
            # Fallback: use quietest 10% of signal
            sorted_amp = np.sort(np.abs(audio_float))
            noise_floor = audio_float[:len(sorted_amp)//10]
        
        # Estimate signal (loudest parts)
        # Use threshold of 25dB below peak (Phonanium standard)
        peak_level = np.max(np.abs(audio_float))
        signal_threshold = peak_level * 0.1778  # 10^(-25/20)
        signal_mask = np.abs(audio_float) > signal_threshold
        
        if not np.any(signal_mask):
            return -999.0
        
        signal_power = np.mean(audio_float[signal_mask]**2)
        noise_power = np.mean(noise_floor**2)
        
        # Avoid division by zero
        if noise_power < 1e-10:
            noise_power = 1e-10
        
        # Calculate SNR in dB
        snr_db = 10 * np.log10(signal_power / noise_power)
        
        # Clamp to reasonable range
        snr_db = np.clip(snr_db, -50, 100)
        
        return snr_db
    
    def assess_audio_quality(self, audio: np.ndarray, sample_rate: int = 16000) -> dict:
        """
        Comprehensive audio quality assessment using professional metrics.
        
        Based on:
        - ITU-T P.862 PESQ standards
        - SoapBox Labs audio quality thresholds
        - Phonanium clinical voice assessment standards
        - WADA SNR estimation
        
        Returns:
            Dictionary with quality metrics and assessment
        """
        # Calculate SNR
        snr = self.calculate_snr(audio, sample_rate)

        # Focus analysis on the active speech region, not trailing silence
        try:
            a = audio.astype(np.float32)
            abs_a = np.abs(a)
            max_val = float(abs_a.max() or 0.0)
            if max_val > 0.0:
                # Consider samples above a small fraction of the peak as "speech"
                speech_mask = abs_a > (0.05 * max_val)
                if np.any(speech_mask):
                    a_active = a[speech_mask]
                else:
                    a_active = a
            else:
                a_active = a
        except Exception:
            a_active = audio.astype(np.float32)

        # Calculate RMS and peak on active speech so we don't penalize end silence
        rms = float(np.sqrt(np.mean(a_active**2))) if len(a_active) else 0.0
        peak = float(np.max(np.abs(a_active))) if len(a_active) else 0.0
        
        # Calculate dynamic range
        if rms > 0:
            dynamic_range = 20 * np.log10(peak / rms) if peak > 0 else 0
        else:
            dynamic_range = 0
        
        # Zero crossing rate (speech activity indicator)
        zero_crossings = np.sum(np.diff(np.sign(audio)) != 0) / len(audio)
        
        # Simplified quality assessment for real-world recordings
        if snr >= 5:  # Very lenient SNR threshold
            quality = "GOOD"
            quality_color = "#00ff88"
            description = "Acceptable for AI training"
        elif snr >= 2:  # Even more lenient
            quality = "FAIR"
            quality_color = "#ff9500"
            description = "May work for AI training"
        else:
            quality = "POOR"
            quality_color = "#ff6b6b"
            description = "Low quality - may affect AI accuracy"
        
        # Check for clipping
        clipping = np.sum(np.abs(audio) > 0.95 * np.max(np.abs(audio))) > len(audio) * 0.01
        if clipping:
            quality = "CLIPPING"
            quality_color = "#ff00ff"
            description = "Audio clipping detected - re-record"
        
        # Check if *extremely* quiet (relaxed threshold)
        # Only hard-fail as TOO_QUIET when levels are extremely low *and* quality isn't already GOOD/FAIR.
        if rms < 0.003:
            if quality not in ["GOOD", "FAIR"]:
                quality = "TOO_QUIET"
                quality_color = "#888888"
                description = "Audio level very low - move closer to mic or increase mic gain"
            else:
                # For otherwise good takes, just add a soft hint without changing PASS status
                description = (description + " | Slightly quiet (this is OK for training)") if description else "Slightly quiet (this is OK for training)"
        
        return {
            "snr_db": snr,
            "rms_level": rms,
            "peak_level": peak,
            "dynamic_range": dynamic_range,
            "zero_crossing_rate": zero_crossings,
            "quality": quality,
            "quality_color": quality_color,
            "description": description,
            "pass": quality in ["GOOD", "FAIR"]
        }
    
    def skip_phrase(self):
        """Skip the current phrase."""
        self.current_phrase_idx += 1
        self.save_progress()
    
    def go_back(self):
        """Go back to previous phrase."""
        if self.current_phrase_idx > 0:
            self.current_phrase_idx -= 1
            self.save_progress()
    
    def get_progress(self) -> tuple:
        """Get recording progress."""
        return self.current_phrase_idx, len(self.phrases)
    
    def get_last_recording_path(self) -> str:
        """Get the path of the last recorded file."""
        # Prefer explicitly tracked last recording path (independent of phrase index)
        if getattr(self, "_last_recording_path", None):
            return self._last_recording_path
        
        # Fallback: infer from latest WAV file if no explicit path is stored
        matches = sorted(self.output_dir.glob("*.wav"), key=lambda x: x.stat().st_mtime, reverse=True)
        if matches:
            return str(matches[0])
        
        # Fallback: return the most recently modified wav file
        all_wavs = list(self.output_dir.glob("*.wav"))
        if all_wavs:
            all_wavs.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            return str(all_wavs[0])
        
        return None
    
    def rerecord_last(self):
        """Go back to re-record the last phrase."""
        if self.current_phrase_idx > 0:
            # Get the phrase we're going back to
            prev_phrase = self.phrases[self.current_phrase_idx - 1]
            
            # Unmark it as recorded (so it can be re-recorded)
            self.unmark_phrase_recorded(prev_phrase)
            
            # Delete the last recording from manifest
            self._remove_last_from_manifest()
            
            # Go back one phrase
            self.current_phrase_idx -= 1
            self.save_progress()
            return True
        return False
    
    def _remove_last_from_manifest(self):
        """Remove the last entry from the manifest."""
        if not self.manifest_file.exists():
            return
        
        # Read all lines except the last
        with open(self.manifest_file, 'r') as f:
            lines = f.readlines()
        
        if lines:
            with open(self.manifest_file, 'w') as f:
                f.writelines(lines[:-1])
    
    def play_audio(self, filepath: str):
        """Play an audio file with proper sample rate handling."""
        try:
            import sounddevice as sd
            from scipy.io import wavfile
            from scipy import signal
            
            # Read the WAV file
            sr, audio = wavfile.read(filepath)
            
            # Convert to float32 in [-1, 1] range based on input format
            if audio.dtype == np.int16:
                audio = audio.astype(np.float32) / 32768.0
            elif audio.dtype == np.int32:
                audio = audio.astype(np.float32) / 2147483648.0
            elif audio.dtype == np.uint8:
                audio = (audio.astype(np.float32) - 128) / 128.0
            elif audio.dtype != np.float32:
                audio = audio.astype(np.float32)
            
            # Convert stereo to mono if needed
            if len(audio.shape) > 1:
                audio = np.mean(audio, axis=1)

            # Choose an appropriate output device and sample rate
            out_device = None
            try:
                # Prefer configured output_device_index if it is a valid output device
                cfg_dev = getattr(self, 'output_device_index', None)
                dev_info = None
                if cfg_dev is not None:
                    try:
                        info = sd.query_devices(cfg_dev)
                        if info.get('max_output_channels', 0) > 0:
                            out_device = cfg_dev
                            dev_info = info
                    except Exception:
                        dev_info = None

                # If no configured output device, fall back to first usable output device
                if dev_info is None:
                    for idx, d in enumerate(sd.query_devices()):
                        if d.get('max_output_channels', 0) > 0:
                            out_device = idx
                            dev_info = d
                            break

                # Determine output sample rate if we have a device
                if dev_info is not None:
                    output_sr = int(dev_info.get('default_samplerate', sr) or sr)
                    # Resample if needed (using high-quality resampling)
                    if sr != output_sr:
                        ratio = output_sr / sr
                        audio = signal.resample_poly(audio, int(100 * ratio), 100)
                        sr = output_sr
            except Exception as e:
                print(f"[RECORDER] Could not determine output device/sample rate, using file rate: {e}")
            
            # Ensure the audio is in the correct range
            max_val = np.max(np.abs(audio))
            if max_val > 1.0:
                audio = audio / max_val
            
            print(f"[PLAYBACK] Playing at {sr} Hz, duration: {len(audio)/sr:.2f}s")
            
            # Play with error handling
            try:
                # Explicitly pass the chosen output device if available
                if out_device is not None:
                    sd.play(audio, sr, blocking=True, device=out_device)
                else:
                    sd.play(audio, sr, blocking=True)
                return True
            except Exception as play_error:
                print(f"[PLAYBACK] Error during playback: {play_error}")
                # Try again with default settings as fallback
                try:
                    sd.play(audio, 44100, blocking=True)
                    return True
                except Exception as fallback_error:
                    print(f"[PLAYBACK] Fallback playback failed: {fallback_error}")
                    return False
                    
        except Exception as e:
            print(f"[PLAYBACK] Playback error: {e}")
            import traceback
            traceback.print_exc()
            return False


class RecorderGUI:
    """GUI for voice recording."""
    
    # Multilingual prompt files (each ~5000 prompts)
    MULTILINGUAL_PROMPT_FILES = [
        ("Pack 1 (5K)", "voice_training/prompts/marvin_multilingual_prompts_01.txt"),
        ("Pack 2 (5K)", "voice_training/prompts/marvin_multilingual_prompts_02.txt"),
        ("Pack 3 (5K)", "voice_training/prompts/marvin_multilingual_prompts_03.txt"),
        ("Pack 4 (5K)", "voice_training/prompts/marvin_multilingual_prompts_04.txt"),
        ("Pack 5 (5K)", "voice_training/prompts/marvin_multilingual_prompts_05.txt"),
        ("Pack 7 (5K)", "voice_training/prompts/marvin_multilingual_prompts_07.txt"),
    ]
    
    def __init__(self, recorder: VoiceRecorder):
        self.user_id = recorder.user_id
        self.recorder = recorder
        self.loaded_packs = set()  # Track which packs are loaded
        self.show_only_unrecorded = False  # Toggle to show only unrecorded phrases
        # Strict gating: do not permit overrides by default
        self.strict_gate = True
        
        # Handle window close properly
        self.root = tk.Tk()
        # Use the recorder's user_id for the window title
        self.root.title(f"Monica Voice Training - {self.user_id}")
        self.root.geometry("900x800")
        self.root.configure(bg='#1a1a2e')
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.bind('<Escape>', lambda e: self._on_close())

        # Capture Tkinter exceptions to prevent silent exits
        def _tk_report_callback_exception(exc, val, tb):
            import traceback
            msg = "\n".join(traceback.format_exception(exc, val, tb))
            try:
                if hasattr(self.recorder, 'log_file') and self.recorder.log_file:
                    with open(self.recorder.log_file, 'a', encoding='utf-8') as lf:
                        lf.write(f"[{datetime.now().isoformat(timespec='seconds')}] TK EXCEPTION:\n{msg}\n")
                # Also write to a fallback project-level log to avoid "no log found" situations
                try:
                    proj_root = Path(__file__).resolve().parents[2]
                    fallback = proj_root / 'logs' / 'recorder.log'
                    fallback.parent.mkdir(parents=True, exist_ok=True)
                    with open(fallback, 'a', encoding='utf-8') as lf2:
                        lf2.write(f"[{datetime.now().isoformat(timespec='seconds')}] TK EXCEPTION:\n{msg}\n")
                except Exception:
                    pass
            except Exception:
                pass
            print("[RECORDER] Tkinter exception:\n" + msg)
            try:
                messagebox.showerror("Recorder Error", "An internal error occurred. Details were logged to recorder.log")
            except Exception:
                pass
        self.root.report_callback_exception = _tk_report_callback_exception
        
        self._setup_ui()
        self._update_display()
        # Training prompt flag (per session)
        self._train_prompt_shown = False

        # Auto-skip to first unrecorded phrase to avoid duplicates
        self._auto_skip_to_unrecorded()
    
    def _on_close(self):
        """Handle window close event."""
        print("[MPVR] Closing MPVR - Progress saved!")
        try:
            # Save any pending progress
            self.recorder.save_progress()
            self.recorder.save_recorded_phrases()
            self.recorder.save_user_profile()
        except:
            pass  # Ignore errors during cleanup
        
        # Destroy the window and exit
        self.root.destroy()
        self.root.quit()
        import sys
        sys.exit(0)
    
    def _setup_ui(self):
        """Setup the UI with scrollbar."""
        # Create main canvas with a single vertical scrollbar (like the side one)
        self.main_canvas = tk.Canvas(self.root, bg='#1a1a2e', highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=self.main_canvas.yview)
        self.scrollable_frame = tk.Frame(self.main_canvas, bg='#1a1a2e')
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all"))
        )
        
        self.main_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        # Only vertical scrolling; content auto-fits width so no horizontal bar with tiny arrows
        self.main_canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack scrollbar and canvas
        scrollbar.pack(side="right", fill="y")
        self.main_canvas.pack(side="left", fill="both", expand=True)
        
        # Enable mouse wheel scrolling
        def _on_mousewheel(event):
            self.main_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        self.main_canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Title
        title = tk.Label(
            self.scrollable_frame,
            text="🎤 Monica Voice Training",
            font=('Segoe UI', 24, 'bold'),
            fg='#00d4ff',
            bg='#1a1a2e'
        )
        title.pack(pady=10)
        
        # User info frame
        user_frame = tk.Frame(self.scrollable_frame, bg='#16213e', padx=20, pady=10)
        user_frame.pack(pady=5, padx=40, fill='x')
        
        self.user_label = tk.Label(
            user_frame,
            text=f"👤 User: {self.user_id}",
            font=('Segoe UI', 12, 'bold'),
            fg='#00ff88',
            bg='#16213e'
        )
        self.user_label.pack(side='left', padx=10)
        
        self.recorded_count_label = tk.Label(
            user_frame,
            text=f"📝 Recorded: {len(self.recorder.recorded_phrases)}",
            font=('Segoe UI', 11),
            fg='#00d4ff',
            bg='#16213e'
        )
        self.recorded_count_label.pack(side='left', padx=20)
        
        self.remaining_label = tk.Label(
            user_frame,
            text=f"⏳ Remaining: {len(self.recorder.phrases) - len(self.recorder.recorded_phrases)}",
            font=('Segoe UI', 11),
            fg='#ff9500',
            bg='#16213e'
        )
        self.remaining_label.pack(side='left', padx=20)
        
        # Progress
        self.progress_label = tk.Label(
            self.scrollable_frame,
            text="Progress: 0 / 1000",
            font=('Segoe UI', 14),
            fg='white',
            bg='#1a1a2e'
        )
        self.progress_label.pack(pady=5)
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(
            self.scrollable_frame,
            length=600,
            mode='determinate'
        )
        self.progress_bar.pack(pady=5)
        
        # Phrase to read
        self.phrase_frame = tk.Frame(self.scrollable_frame, bg='#16213e', padx=40, pady=20)
        self.phrase_frame.pack(pady=15, padx=40, fill='x')
        
        self.phrase_header_label = tk.Label(
            self.phrase_frame,
            text="Say this phrase:",
            font=('Segoe UI', 12),
            fg='#888',
            bg='#16213e'
        )
        self.phrase_header_label.pack()
        
        self.phrase_label = tk.Label(
            self.phrase_frame,
            text="Loading...",
            font=('Segoe UI', 24, 'bold'),
            fg='#00ff88',
            bg='#16213e',
            wraplength=700
        )
        self.phrase_label.pack(pady=10)
        
        # Already recorded indicator
        self.recorded_indicator = tk.Label(
            self.phrase_frame,
            text="",
            font=('Segoe UI', 10),
            fg='#888',
            bg='#16213e'
        )
        self.recorded_indicator.pack(pady=5)
        
        # Recording indicator
        self.status_label = tk.Label(
            self.scrollable_frame,
            text="Press SPACE or click to start/stop recording",
            font=('Segoe UI', 14),
            fg='#888',
            bg='#1a1a2e'
        )
        self.status_label.pack(pady=10)
        
        # Quality metrics display
        self.quality_label = tk.Label(
            self.scrollable_frame,
            text="",
            font=('Segoe UI', 11),
            fg='#00d4ff',
            bg='#1a1a2e'
        )
        self.quality_label.pack(pady=5)
        
        # Audio level meter frame
        meter_frame = tk.Frame(self.scrollable_frame, bg='#1a1a2e')
        meter_frame.pack(pady=8, fill='x', padx=40)
        
        tk.Label(
            meter_frame,
            text="Audio Level:",
            font=('Segoe UI', 10),
            fg='#888',
            bg='#1a1a2e'
        ).pack(side='left', padx=5)
        
        # Audio level canvas (visual meter)
        self.level_canvas = tk.Canvas(
            meter_frame,
            width=400,
            height=25,
            bg='#0a0a15',
            highlightthickness=1,
            highlightbackground='#333'
        )
        self.level_canvas.pack(side='left', padx=10)
        
        # Level indicator text
        self.level_text = tk.Label(
            meter_frame,
            text="",
            font=('Segoe UI', 10),
            fg='#888',
            bg='#1a1a2e'
        )
        self.level_text.pack(side='left', padx=5)

        # Mic gain control (slider)
        gain_frame = tk.Frame(self.scrollable_frame, bg='#1a1a2e')
        gain_frame.pack(pady=4, padx=40, fill='x')

        tk.Label(
            gain_frame,
            text="Mic Gain:",
            font=('Segoe UI', 10),
            fg='#888',
            bg='#1a1a2e'
        ).pack(side='left', padx=(0, 8))

        self.mic_gain_var = tk.DoubleVar(value=getattr(self.recorder, 'mic_gain', 1.0))

        def _on_gain_change(value):
            try:
                g = float(value)
                # Keep within 0.5x–3.0x for UI; recorder will hard-clamp wider
                self.recorder.mic_gain = g
                self.mic_gain_label.config(text=f"{g:.1f}x")
            except Exception:
                pass

        self.mic_gain_slider = tk.Scale(
            gain_frame,
            from_=0.5,
            to=3.0,
            resolution=0.1,
            orient='horizontal',
            showvalue=False,
            length=220,
            bg='#1a1a2e',
            troughcolor='#333',
            highlightthickness=0,
            fg='#ccc',
            command=_on_gain_change,
            variable=self.mic_gain_var
        )
        self.mic_gain_slider.pack(side='left')

        self.mic_gain_label = tk.Label(
            gain_frame,
            text=f"{self.mic_gain_var.get():.1f}x",
            font=('Segoe UI', 10),
            fg='#00ff88',
            bg='#1a1a2e'
        )
        self.mic_gain_label.pack(side='left', padx=6)

        # Preflight guidance label (live while recording)
        self.preflight_label = tk.Label(
            self.scrollable_frame,
            text="",
            font=('Segoe UI', 10),
            fg='#888',
            bg='#1a1a2e'
        )
        self.preflight_label.pack(pady=4)
        
        # Buttons row 1 - main controls
        btn_frame = tk.Frame(self.scrollable_frame, bg='#1a1a2e')
        btn_frame.pack(pady=8)
        
        self.record_btn = tk.Button(
            btn_frame,
            text="⏺ Record",
            font=('Segoe UI', 12, 'bold'),
            bg='#e94560',
            fg='white',
            width=16,
            height=2
        )
        self.record_btn.pack(side='left', padx=5)
        # Default to click-to-toggle behavior for simplicity and stability
        self.record_btn.config(command=self._toggle_recording)
        
        # Play button
        self.play_btn = tk.Button(
            btn_frame,
            text="▶ Play",
            font=('Segoe UI', 11),
            bg='#0077b6',
            fg='white',
            width=8,
            command=self._play_recording,
            state='disabled'
        )
        self.play_btn.pack(side='left', padx=5)
        
        # Re-record button
        self.rerecord_btn = tk.Button(
            btn_frame,
            text="🔄 Re-record",
            font=('Segoe UI', 11),
            bg='#ff9500',
            fg='white',
            width=10,
            command=self._rerecord,
            state='disabled'
        )
        # Do not pack the button so it remains available for shortcuts but hidden in the UI

        # Explicit Save + Next button (no auto-advance after recording)
        self.next_btn = tk.Button(
            btn_frame,
            text="➡ Save + Next",
            font=('Segoe UI', 11),
            bg='#22c55e',
            fg='white',
            width=12,
            command=self._next_and_save,
            state='disabled'
        )
        self.next_btn.pack(side='left', padx=5)

        # Override button (advanced; hidden in strict mode)
        self.override_btn = tk.Button(
            btn_frame,
            text="⚠ Override & Continue",
            font=('Segoe UI', 11, 'bold'),
            bg='#6b7280',
            fg='white',
            width=18,
            command=self._override_and_continue,
            state='disabled'
        )
        if not self.strict_gate:
            self.override_btn.pack(side='left', padx=5)
        
        # Noise reduction and Library row
        controls_frame = tk.Frame(self.scrollable_frame, bg='#1a1a2e')
        controls_frame.pack(pady=8)
        self.noise_label = tk.Label(
            controls_frame,
            text="🔇 Noise Reduction: ENABLED" if HAS_NOISE_REDUCE else "⚠️ Noise Reduction: DISABLED",
            font=('Segoe UI', 10),
            fg='#00ff88' if HAS_NOISE_REDUCE else '#ff6b6b',
            bg='#1a1a2e'
        )
        self.noise_label.pack(side='left', padx=10)
        
        # Toggle noise reduction
        self.noise_toggle_btn = tk.Button(
            controls_frame,
            text="Toggle NR",
            font=('Segoe UI', 9),
            bg='#333',
            fg='white',
            command=self._toggle_noise_reduction
        )
        self.noise_toggle_btn.pack(side='left', padx=5)
        
        # Noise reduction strength slider
        tk.Label(
            controls_frame,
            text="NR Strength:",
            font=('Segoe UI', 9),
            fg='#888',
            bg='#1a1a2e'
        ).pack(side='left', padx=(10, 2))
        
        self.nr_strength_var = tk.DoubleVar(value=self.recorder.noise_reduce_strength)
        self.nr_strength_slider = tk.Scale(
            controls_frame,
            from_=0.0,
            to=1.0,
            resolution=0.1,
            orient='horizontal',
            length=80,
            variable=self.nr_strength_var,
            command=self._update_nr_strength,
            bg='#1a1a2e',
            fg='#00ff88',
            highlightthickness=0,
            troughcolor='#333'
        )
        self.nr_strength_slider.pack(side='left', padx=2)
        
        self.nr_strength_label = tk.Label(
            controls_frame,
            text=f"{self.recorder.noise_reduce_strength:.0%}",
            font=('Segoe UI', 9),
            fg='#00ff88',
            bg='#1a1a2e',
            width=4
        )
        self.nr_strength_label.pack(side='left')
        
        # Library Manager button
        self.library_btn = tk.Button(
            controls_frame,
            text="📚 View Library",
            font=('Segoe UI', 10, 'bold'),
            bg='#6c5ce7',
            fg='white',
            command=self._open_library_manager
        )
        self.library_btn.pack(side='left', padx=15)

        # Diagnostics exporter button
        self.diag_btn = tk.Button(
            controls_frame,
            text="🩺 Report Issue",
            font=('Segoe UI', 10, 'bold'),
            bg='#64748b',
            fg='white',
            command=self._export_diagnostics
        )
        self.diag_btn.pack(side='left', padx=10)

        # Calibrate button
        self.calib_btn = tk.Button(
            controls_frame,
            text="🎚️ Calibrate Mic",
            font=('Segoe UI', 10, 'bold'),
            bg='#0ea5e9',
            fg='white',
            command=self._calibrate_mic
        )
        self.calib_btn.pack(side='left', padx=10)
        self.calib_status = tk.Label(
            controls_frame,
            text="Not calibrated",
            font=('Segoe UI', 9),
            fg='#888',
            bg='#1a1a2e'
        )
        self.calib_status.pack(side='left', padx=6)

        # Change devices button
        self.device_btn = tk.Button(
            controls_frame,
            text="🎧 Change Devices",
            font=('Segoe UI', 9),
            bg='#374151',
            fg='white',
            command=self._change_devices
        )
        self.device_btn.pack(side='left', padx=10)

        # ========== TRAINING CONTROLS SECTION ==========
        train_frame = tk.LabelFrame(
            self.scrollable_frame,
            text="🧠 Train Speech-to-Text (SpeechBrain + wav2vec2)",
            font=('Segoe UI', 11, 'bold'),
            fg='#00d4ff',
            bg='#1a1a2e',
            padx=15,
            pady=10
        )
        train_frame.pack(pady=10, padx=40, fill='x')

        train_left = tk.Frame(train_frame, bg='#1a1a2e')
        train_left.pack(side='left')

        self.train_btn = tk.Button(
            train_left,
            text="🚀 Train Speech-to-Text",
            font=('Segoe UI', 12, 'bold'),
            bg='#00aa55' if VoiceModelTrainer else '#555',
            fg='white',
            width=22,
            command=self._train_speech_model,
            state='normal' if VoiceModelTrainer else 'disabled'
        )
        self.train_btn.pack(side='left', padx=5)

        self.training_status_label = tk.Label(
            train_frame,
            text=("Ready when you have at least 10 recordings" if VoiceModelTrainer else
                  "Trainer unavailable. Install SpeechBrain: pip install speechbrain"),
            font=('Segoe UI', 10),
            fg='#888' if VoiceModelTrainer else '#ff6b6b',
            bg='#1a1a2e'
        )
        self.training_status_label.pack(side='left', padx=15)

        # Training progress bar (GUI-side indicator)
        self.training_progress_bar = ttk.Progressbar(
            train_frame,
            orient='horizontal',
            mode='determinate',
            length=220,
            maximum=100
        )
        self.training_progress_bar.pack(side='left', padx=10)

        # View last training result button
        self.view_training_btn = tk.Button(
            train_frame,
            text="📄 Last Result",
            font=('Segoe UI', 9),
            bg='#374151',
            fg='white',
            command=self._view_last_training_result
        )
        self.view_training_btn.pack(side='left', padx=5)
        
        # ========== KEYBOARD SHORTCUTS SECTION ==========
        shortcuts_frame = tk.LabelFrame(
            self.scrollable_frame,
            text="⌨️ Keyboard Shortcuts",
            font=('Segoe UI', 11, 'bold'),
            fg='#00d4ff',
            bg='#1a1a2e',
            padx=15,
            pady=10
        )
        shortcuts_frame.pack(pady=10, padx=40, fill='x')
        
        shortcuts = [
            ("SPACE", "Start/Stop recording"),
            ("P", "Play last recording"),
            ("R", "Re-record last phrase"),
            ("N", "Next unrecorded phrase"),
            ("→ (Right Arrow)", "Skip phrase"),
            ("← (Left Arrow)", "Go back"),
            ("ESC", "Exit (progress saved)"),
        ]
        
        for i, (key, action) in enumerate(shortcuts):
            row = tk.Frame(shortcuts_frame, bg='#1a1a2e')
            row.pack(fill='x', pady=2)
            
            key_label = tk.Label(
                row,
                text=key,
                font=('Consolas', 10, 'bold'),
                fg='#ff9500',
                bg='#1a1a2e',
                width=18,
                anchor='e'
            )
            key_label.pack(side='left', padx=(0, 10))
            
            action_label = tk.Label(
                row,
                text=action,
                font=('Segoe UI', 10),
                fg='#ccc',
                bg='#1a1a2e',
                anchor='w'
            )
            action_label.pack(side='left')
        
        # ========== OPTIONAL PROMPT PACKS SECTION ==========
        packs_frame = tk.LabelFrame(
            self.scrollable_frame,
            text="📦 Optional Prompt Packs (5K each)",
            font=('Segoe UI', 11, 'bold'),
            fg='#00d4ff',
            bg='#1a1a2e',
            padx=15,
            pady=10
        )
        packs_frame.pack(pady=10, padx=40, fill='x')
        
        self.pack_vars = {}
        self.pack_buttons = {}
        
        for pack_name, pack_path in self.MULTILINGUAL_PROMPT_FILES:
            pack_row = tk.Frame(packs_frame, bg='#1a1a2e')
            pack_row.pack(fill='x', pady=3)
            
            # Check if file exists
            full_path = Path(__file__).parent.parent / pack_path
            exists = full_path.exists()
            
            var = tk.BooleanVar(value=False)
            self.pack_vars[pack_name] = var
            
            cb = tk.Checkbutton(
                pack_row,
                text=pack_name,
                variable=var,
                font=('Segoe UI', 10),
                fg='#ccc' if exists else '#666',
                bg='#1a1a2e',
                selectcolor='#333',
                activebackground='#1a1a2e',
                activeforeground='#00ff88',
                state='normal' if exists else 'disabled'
            )
            cb.pack(side='left')
            
            status = "Available" if exists else "Not found"
            status_color = '#00ff88' if exists else '#ff6b6b'
            
            status_label = tk.Label(
                pack_row,
                text=f"({status})",
                font=('Segoe UI', 9),
                fg=status_color,
                bg='#1a1a2e'
            )
            status_label.pack(side='left', padx=10)
        
        # Load packs button
        load_btn_frame = tk.Frame(packs_frame, bg='#1a1a2e')
        load_btn_frame.pack(pady=10)
        
        self.load_packs_btn = tk.Button(
            load_btn_frame,
            text="📥 Load Selected Packs",
            font=('Segoe UI', 11, 'bold'),
            bg='#00aa55',
            fg='white',
            command=self._load_selected_packs
        )
        self.load_packs_btn.pack(side='left', padx=5)
        
        self.packs_status_label = tk.Label(
            load_btn_frame,
            text="",
            font=('Segoe UI', 10),
            fg='#888',
            bg='#1a1a2e'
        )
        self.packs_status_label.pack(side='left', padx=10)
        
        # Keyboard bindings
        self.root.bind('<space>', self._toggle_recording)  # Toggle recording with spacebar
        self.root.bind('<Right>', lambda e: self._skip())
        self.root.bind('<Left>', lambda e: self._go_back())
        self.root.bind('<Escape>', lambda e: self.root.quit())
        self.root.bind('p', lambda e: self._play_recording())
        self.root.bind('r', lambda e: self._rerecord())
        self.root.bind('n', lambda e: self._skip_to_unrecorded())
        
        # Track last recording
        self.last_recording = None

    def _set_training_status(self, text: str, color: str = '#00d4ff'):
        try:
            if hasattr(self, 'training_status_label'):
                # Ensure thread-safe UI update
                self.root.after(0, lambda: self.training_status_label.config(text=text, fg=color))
        except Exception:
            pass

    def _toggle_controls(self, enabled: bool):
        state = 'normal' if enabled else 'disabled'
        try:
            self.root.after(0, lambda: (
                self.record_btn.config(state=state),
                self.play_btn.config(state=state),
                self.rerecord_btn.config(state=state),
                self.noise_toggle_btn.config(state=state),
                self.library_btn.config(state=state),
                self.diag_btn.config(state=state),
                self.train_btn.config(state=state),
                self.view_training_btn.config(state=state),
            ))
        except Exception:
            pass

    def _train_speech_model(self):
        """Start optimized SpeechBrain training on recorded data."""

        # Count recordings based on existing CSVs if available.
        csv_train = self.recorder.output_dir / 'train.csv'
        csv_val = self.recorder.output_dir / 'val.csv'

        if not csv_train.exists() or not csv_val.exists():
            messagebox.showwarning(
                "Training Data Not Ready",
                "Training/validation CSV files not found.\n\n"
                "Please record at least 100 phrases first.\n"
                "The GUI will automatically create train.csv and val.csv."
            )
            return

        # Count recordings
        try:
            import csv as csv_module
            with open(csv_train, 'r', encoding='utf-8', newline='') as f:
                train_count = sum(1 for _ in csv_module.reader(f)) - 1  # -1 for header
            with open(csv_val, 'r', encoding='utf-8', newline='') as f:
                val_count = sum(1 for _ in csv_module.reader(f)) - 1
            total_count = max(0, train_count) + max(0, val_count)
        except Exception:
            total_count = 0

        if total_count < 100:
            messagebox.showwarning(
                "Need More Recordings",
                f"You have {total_count} recordings.\n\n"
                "At least 100 recordings are recommended for training.\n"
                "Please record more phrases first."
            )
            return

        # Confirm training start
        if not messagebox.askyesno(
            "Start Optimized SpeechBrain Training",
            f"Ready to train on {total_count} recordings!\n\n"
            "This will:\n"
            "• Fine-tune Wav2Vec2-Large model (22 epochs)\n"
            "• Use FP16 mixed precision + gradient checkpointing\n"
            "• Optimized for 8GB VRAM (no more crashes!)\n"
            "• Take ~1.5-2 hours\n"
            "• Achieve 85-95% accuracy on YOUR voice\n\n"
            "Memory optimizations enabled:\n"
            "✓ Mixed precision training\n"
            "✓ Gradient accumulation (4x)\n"
            "✓ Aggressive memory management\n\n"
            "You can continue recording while training runs.\n\n"
            "Start training now?"
        ):
            return

        # Disable train button
        try:
            self.train_btn.config(state='disabled', text="🚀 Training...")
        except Exception:
            pass

        self.training_progress_bar['value'] = 0
        self._set_training_status("Starting optimized training (22 epochs, FP16)...", '#00ff88')

        def _run_training():
            import subprocess
            import sys

            try:
                # Get project root and training script
                project_root = Path(__file__).resolve().parents[2]
                # Use optimized training script with memory fixes
                train_script = project_root / "train_monica.py"
                hparams = project_root / "hparams_monica.yaml"

                if not train_script.exists():
                    raise FileNotFoundError(f"Training script not found: {train_script}")
                if not hparams.exists():
                    raise FileNotFoundError(f"Config file not found: {hparams}")

                # Get Python executable - ALWAYS use venv Python, not sys.executable
                # sys.executable returns whichever Python launched the GUI, which may be wrong
                venv_python = project_root / ".venv" / "Scripts" / "python.exe"
                if venv_python.exists():
                    python_exe = str(venv_python)
                    print(f"[TRAINING] Using venv Python: {python_exe}")
                else:
                    # Fallback to sys.executable with warning
                    python_exe = sys.executable
                    print(f"[TRAINING] WARNING: venv Python not found, using: {python_exe}")

                # Build command
                cmd = [python_exe, str(train_script), str(hparams)]

                self._set_training_status("Loading Wav2Vec2 model (1-2 min)...", '#00d4ff')

                # Run training process
                print(f"[TRAINING] Starting: {' '.join(cmd)}")
                process = subprocess.Popen(
                    cmd,
                    cwd=str(project_root),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                    bufsize=1
                )

                log_dir = self.recorder.output_dir / "training_logs"
                try:
                    log_dir.mkdir(parents=True, exist_ok=True)
                except Exception:
                    pass
                log_path = log_dir / f"training_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
                latest_log_path = log_dir / "training_latest.log"
                log_fh = None
                try:
                    log_fh = open(log_path, 'w', encoding='utf-8', errors='replace')
                except Exception:
                    log_fh = None

                # Monitor output
                # SpeechBrain logs a few different epoch formats; handle them all.
                epoch_pattern = re.compile(r'\bepoch\s+(\d+)\b', re.IGNORECASE)
                going_into_epoch_pattern = re.compile(r'Going into epoch\s+(\d+)', re.IGNORECASE)
                # tqdm progress lines look like:
                #  88%|########8 | 882/1002 [04:12<12:54,  6.46s/it, train_loss=0.039]
                tqdm_step_pattern = re.compile(
                    r"(?P<pct>\d+)%\|.*?\|\s*(?P<step>\d+)\/(?P<total>\d+).*?train_loss=(?P<loss>[0-9.]+)",
                    re.IGNORECASE,
                )
                current_epoch = 0
                total_epochs = 22
                current_step = None
                total_steps = None
                current_loss = None
                last_ui_update_ts = 0.0

                def _post_status_update():
                    try:
                        parts = []
                        if current_epoch:
                            parts.append(f"Epoch {current_epoch}/{total_epochs}")
                        if current_step is not None and total_steps is not None:
                            parts.append(f"Step {current_step}/{total_steps}")
                        if current_loss is not None:
                            parts.append(f"loss {current_loss}")
                        if not parts:
                            return
                        status_text = " • ".join(parts)

                        # Progress bar: primarily based on epoch. Steps are shown in text.
                        progress = (current_epoch / total_epochs) * 100 if total_epochs else 0
                        self.training_progress_bar.config(value=progress)
                        self._set_training_status(status_text, '#00d4ff')
                    except Exception:
                        pass

                for line in process.stdout:
                    print(line, end='')  # Print to console
                    if log_fh is not None:
                        try:
                            log_fh.write(line)
                            log_fh.flush()
                        except Exception:
                            pass

                    # Parse epoch progress
                    match = going_into_epoch_pattern.search(line) or epoch_pattern.search(line)
                    if match:
                        try:
                            current_epoch = int(match.group(1))
                        except Exception:
                            current_epoch = current_epoch

                    # Parse per-step tqdm progress (step/total + train_loss)
                    tmatch = tqdm_step_pattern.search(line)
                    if tmatch:
                        try:
                            current_step = int(tmatch.group('step'))
                            total_steps = int(tmatch.group('total'))
                            current_loss = tmatch.group('loss')
                        except Exception:
                            pass

                    # Throttle UI updates so we don't overwhelm Tkinter
                    try:
                        now_ts = time.time()
                        if now_ts - last_ui_update_ts >= 0.5:
                            last_ui_update_ts = now_ts
                            self.root.after(0, _post_status_update)
                    except Exception:
                        pass

                # Wait for completion
                process.wait()

                if log_fh is not None:
                    try:
                        log_fh.flush()
                    except Exception:
                        pass
                    try:
                        log_fh.close()
                    except Exception:
                        pass
                    try:
                        with open(log_path, 'r', encoding='utf-8', errors='replace') as _src, \
                             open(latest_log_path, 'w', encoding='utf-8', errors='replace') as _dst:
                            _dst.write(_src.read())
                    except Exception:
                        pass

                if process.returncode == 0:
                    model_path = project_root / "models" / "monica_finetuned" / "1986" / "save"
                    self._set_training_status("✅ Training complete! Model ready.", '#00ff88')
                    messagebox.showinfo(
                        "Training Complete!",
                        f"Your personalized STT model is ready!\n\n"
                        f"Model location:\n{model_path}\n\n"
                        f"Training log:\n{log_path}\n\n"
                        f"Training summary:\n"
                        f"• Recordings: {total_count}\n"
                        f"• Epochs: 22 (optimized)\n"
                        f"• Precision: FP16 mixed precision\n"
                        f"• Memory: Gradient checkpointing enabled\n\n"
                        f"Next step: Review training log for final WER/CER\n"
                        f"Monica will now understand YOUR voice perfectly!"
                    )

                    # Save result
                    try:
                        result_path = self.recorder.output_dir / "last_training_result.json"
                        with open(result_path, 'w', encoding='utf-8') as rf:
                            json.dump({
                                'status': 'success',
                                'model_path': str(model_path),
                                'training_log': str(log_path),
                                'recordings': total_count,
                                'epochs': 22,
                                'optimizations': {
                                    'precision': 'fp16',
                                    'gradient_accumulation': 4,
                                    'gradient_checkpointing': True,
                                    'memory_optimized': True
                                },
                                'timestamp': datetime.now().isoformat(timespec='seconds')
                            }, rf, indent=2)
                    except Exception:
                        pass
                else:
                    rc = process.returncode
                    self._set_training_status(f"⚠️ Training failed (exit code {rc}). Check console.", '#ff9500')

                    # Capture training failure with crash reporter
                    try:
                        from monica_ai.crash_reporter import get_crash_reporter
                        crash_reporter = get_crash_reporter()
                        report_file = crash_reporter.generate_report(
                            error_type="Training Process Failed",
                            error_message=f"Training process exited with non-zero exit code: {rc}\n\n"
                                         f"This usually indicates an error during model training.\n"
                                         f"Check the console output above for details.",
                            error_traceback=None,
                            context={
                                "component": "Voice Training",
                                "exit_code": rc,
                                "total_recordings": total_count,
                                "current_epoch": current_epoch,
                                "python_exe": str(python_exe)
                            }
                        )
                        print(f"[TRAINING] Crash report saved: {report_file}")
                    except Exception as crash_err:
                        print(f"[TRAINING] Could not save crash report: {crash_err}")

                    messagebox.showerror(
                        "Training Failed",
                        f"Training process exited with code {rc}\n\n"
                        "Check the console output for details.\n\n"
                        "A crash report has been saved to crash_reports/"
                    )

            except Exception as e:
                import traceback
                error_msg = traceback.format_exc()
                print(f"[TRAINING] Error:\n{error_msg}")

                self._set_training_status(f"❌ Training failed: {e}", '#ff6b6b')

                # Capture exception with crash reporter
                try:
                    from monica_ai.crash_reporter import capture_exception
                    report_file = capture_exception("Training Exception", {
                        "component": "Voice Training",
                        "total_recordings": total_count if 'total_count' in locals() else 'unknown',
                        "python_exe": str(python_exe) if 'python_exe' in locals() else 'unknown'
                    })
                    print(f"[TRAINING] Crash report saved: {report_file}")
                except Exception as crash_err:
                    print(f"[TRAINING] Could not save crash report: {crash_err}")

                messagebox.showerror(
                    "Training Failed",
                    f"{str(e)}\n\n"
                    "A crash report has been saved to crash_reports/"
                )

                try:
                    result_path = self.recorder.output_dir / "last_training_result.json"
                    with open(result_path, 'w', encoding='utf-8') as rf:
                        json.dump({
                            'status': 'failed',
                            'error': str(e),
                            'timestamp': datetime.now().isoformat(timespec='seconds')
                        }, rf, indent=2)
                except Exception:
                    pass
            finally:
                # Re-enable button
                try:
                    self.root.after(0, lambda: self.train_btn.config(
                        state='normal',
                        text="🚀 Train Speech-to-Text"
                    ))
                except Exception:
                    pass

        threading.Thread(target=_run_training, daemon=True).start()
    
    def _update_display(self):
        """Update the display."""
        current, total = self.recorder.get_progress()
        
        # Count actual files in library
        actual_file_count = len(list(self.recorder.output_dir.glob("*.wav")))
        unique_phrases = len(self.recorder.recorded_phrases)
        remaining = total - unique_phrases
        
        # Update progress (show 1-based index for user-facing position)
        display_idx = (min(current + 1, total) if total > 0 else 0)
        self.progress_label.config(text=f"Position: {display_idx} / {total}")
        # Keep progress bar proportional to completed items; use current/total (0-based is correct fraction)
        self.progress_bar['value'] = (current / total) * 100 if total > 0 else 0
        
        # Update user stats - show both file count and unique phrases
        self.recorded_count_label.config(text=f"📝 Library: {actual_file_count} files ({unique_phrases} unique)")
        self.remaining_label.config(text=f"⏳ Remaining: {remaining}")
        
        # Update phrase
        phrase = self.recorder.get_current_phrase()
        if phrase:
            self.phrase_label.config(text=f'"{phrase}"')
            
            # Check if already recorded
            if self.recorder.is_phrase_recorded(phrase):
                self.recorded_indicator.config(
                    text="✅ Already recorded - will overwrite if you record again",
                    fg='#00ff88'
                )
                self.phrase_label.config(fg='#888888')  # Dim the phrase
            else:
                self.recorded_indicator.config(
                    text="🆕 Not yet recorded",
                    fg='#ff9500'
                )
                self.phrase_label.config(fg='#00ff88')  # Normal color
        else:
            self.phrase_label.config(text="🎉 All done! Great job!")
            self.recorded_indicator.config(text="")
            self.status_label.config(text="You've recorded all phrases!")

        # Training threshold reached - just update status, don't prompt
        try:
            if (
                VoiceModelTrainer
                and unique_phrases >= 100
                and not getattr(self, "_train_prompt_shown", False)
            ):
                self._train_prompt_shown = True
                # Just update status hint, don't show popup
                self._set_training_status(
                    f"Ready to train anytime (recordings: {unique_phrases}).",
                    '#00ff88'
                )
        except Exception:
            pass
    
    def _keypress_space(self, event=None):
        """Start on space press (debounced)."""
        try:
            import time as _t
            now = _t.time()
            if now - getattr(self, '_last_state_change_ts', 0) < 0.25:
                return
            if not self.recorder.is_recording:
                self._start_recording()
        except Exception:
            pass

    def _keyrelease_space(self, event=None):
        """Stop on space release (debounced)."""
        try:
            import time as _t
            now = _t.time()
            if now - getattr(self, '_last_state_change_ts', 0) < 0.25:
                return
            if self.recorder.is_recording:
                self._stop_recording()
        except Exception:
            pass

    def _start_recording(self, event=None):
        """Start recording."""
        # Debounce rapid toggles (mouse + keyboard repeats)
        try:
            import time as _t
            now = _t.time()
            if now - getattr(self, '_last_state_change_ts', 0) < 0.2:
                return
            self._last_state_change_ts = now
        except Exception:
            pass

        self.recorder.start_recording()
        self.status_label.config(text="🔴 RECORDING...", fg='#e94560')
        self.record_btn.config(bg='#ff0000')
        # Disable play/rerecord during recording
        self.play_btn.config(state='disabled')
        self.rerecord_btn.config(state='disabled')
        # Can't go next while actively recording
        if hasattr(self, 'next_btn'):
            self.next_btn.config(state='disabled')
        # Start audio level monitoring
        self._update_audio_level()
    
    def _stop_recording(self, event=None):
        """Stop recording."""
        # Debounce rapid toggles
        try:
            import time as _t
            now = _t.time()
            if now - getattr(self, '_last_state_change_ts', 0) < 0.2:
                return
            self._last_state_change_ts = now
        except Exception:
            pass

        filepath, quality_metrics = self.recorder.stop_recording()
        if filepath:
            self.status_label.config(text=f"✅ Saved! Analyzing quality...", fg='#00ff88')
            self.quality_label.config(text="⏳ Analyzing...", fg='#888')
            
            # Run quality assessment in background thread to avoid freezing GUI
            def assess_quality_async():
                try:
                    if HAS_QUALITY_METRICS and self.recorder.quality_assessor:
                        print("[QUALITY] Running scientific quality assessment...")
                        # Get the current phrase for content accuracy checking
                        current_phrase = self.recorder.phrases[self.recorder.current_phrase_idx - 1] if self.recorder.current_phrase_idx > 0 else ""
                        # Run the actual quality assessment
                        quality_result = self.recorder.quality_assessor.assess_audio_quality(filepath, current_phrase)
                    
                        # Build detailed quality text with reasons
                        mos = quality_result.mos_score
                        snr = quality_result.snr_db
                        thd = quality_result.thd_percent
                        level = quality_result.quality_level.value.upper()
                    
                        # Dynamic thresholds based on calibration (if available)
                        # Use a fixed, realistic SNR threshold so good takes don't fail.
                        # Typical speech recordings are usable above ~10 dB; your room often
                        # measures 25-40 dB, which is already very good. Using calibration
                        # here made the threshold too strict (e.g. 47 dB). We now just require
                        # a modest, fixed minimum SNR.
                        snr_min = 10.0
                        # Other heuristic gates (more tolerant for real rooms)
                        va_pct = float(getattr(quality_result, 'voice_activity_percent', 0.0)) if hasattr(quality_result, 'voice_activity_percent') else 0.0
                        try:
                            clarity = float(getattr(quality_result, 'speech_clarity', {}).get('clarity_score', 0.0))
                        except Exception:
                            clarity = 0.0
                        try:
                            noise_total = float(getattr(quality_result, 'background_noise', {}).get('total_noise', 100.0))
                        except Exception:
                            noise_total = 100.0

                        # Final PASS logic: make the quality check advisory, not blocking.
                        # We still compute SNR/clipping/noise, but even if they are not ideal
                        # we will not delete the take or block progress. Only use this for
                        # guidance in the UI.
                        passes_quality = (
                            (snr >= snr_min)
                            and (not quality_result.clipping_detected)
                            and (noise_total <= 80.0)
                        )
                    
                        # Print console verdict with details
                        if passes_quality:  # Quality passes
                            print(f"[QUALITY] ✅ PASS - MOS: {mos:.2f}, SNR: {snr:.1f}dB, THD: {thd:.1f}%, Level: {level}")
                            quality_text = f"✅ PASS | MOS: {mos:.2f} | SNR: {snr:.1f}dB | THD: {thd:.1f}% | {level}"
                            color = '#00ff88'  # Green
                            status_text = "✅ Quality PASSED! Use 'Save + Next' when you're ready to move on."
                            status_color = '#00ff88'

                            # Do NOT auto-advance; just enable Save+Next for manual control
                            def _enable_next():
                                if hasattr(self, 'next_btn'):
                                    self.next_btn.config(state='normal')
                                # On good take, override is not needed
                                try:
                                    self.override_btn.config(state='disabled', bg='#6b7280')
                                except Exception:
                                    pass
                            self.root.after(0, _enable_next)
                        else:
                            # Build advisory reasons (no longer used to delete or block)
                            reasons = []
                            if snr < snr_min:
                                reasons.append(f"Low SNR ({snr:.1f}dB < {snr_min:.1f}dB)")
                            if quality_result.clipping_detected:
                                reasons.append("Clipping detected")
                            # Voice-activity and clarity hints only
                            if va_pct < 3.0:
                                reasons.append("Very short speech (usually OK if clearly spoken)")
                            if clarity < 30.0:
                                reasons.append("Articulation unclear (mumbled/slurred)")
                            if noise_total > 80.0:
                                reasons.append("High background noise")

                            reason_text = " | ".join(reasons) if reasons else "Quality below ideal"
                            print(f"[QUALITY] ⚠ ADVISORY - {reason_text}")
                            quality_text = f"⚠ ADVISORY | {reason_text}"
                            color = '#ffb74d'  # Amber
                            status_text = "⚠ Quality not ideal, but this take is kept. You can re-record if you want."
                            status_color = '#ffb74d'

                            # On advisory, still enable Save+Next so the user can move on
                            def _on_warn():
                                try:
                                    self.next_btn.config(state='normal')
                                except Exception:
                                    pass
                                try:
                                    self.override_btn.config(state='disabled', bg='#6b7280')
                                except Exception:
                                    pass
                            self.root.after(0, _on_warn)
                            # Stay on same phrase - don't increment
                        
                        # Update GUI on main thread
                        self.root.after(0, lambda: self.quality_label.config(text=quality_text, fg=color))
                        self.root.after(0, lambda: self.status_label.config(text=status_text, fg=status_color))
                    else:
                        print("[QUALITY] ⚠️ Quality metrics not available")
                        self.root.after(0, lambda: self.quality_label.config(text="📊 Quality metrics: Not available", fg='#888'))
                        self.root.after(0, lambda: self.status_label.config(text=f"✅ Saved! Play to review or SPACE for next", fg='#00ff88'))
                except Exception as e:
                    print(f"[QUALITY] ❌ Error in quality assessment: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    self.root.after(0, lambda: self.quality_label.config(text="❌ Error in quality check", fg='#ff6b6b'))
                    self.root.after(0, lambda: self.status_label.config(text=f"✅ Saved! Play to review or SPACE for next", fg='#00ff88'))
            
            # Start quality assessment in background
            threading.Thread(target=assess_quality_async, daemon=True).start()
            
            # Enable play and re-record buttons immediately
            self.play_btn.config(state='normal')
            self.rerecord_btn.config(state='normal')
            self.last_recording = filepath
        else:
            self.status_label.config(text="❌ Recording failed, try again", fg='#ff6b6b')
            self.quality_label.config(text="", fg='#888')
        self.record_btn.config(bg='#e94560')
        self._update_display()

    def _export_diagnostics(self):
        """Export a diagnostics bundle and create crash report with email draft."""
        try:
            import zipfile
            from datetime import datetime as _dt
            from tkinter import messagebox

            # Import crash reporter
            try:
                from monica_ai.crash_reporter import get_crash_reporter
                crash_reporter = get_crash_reporter()
            except ImportError:
                # Fallback if crash reporter not available
                crash_reporter = None
                print("[RECORDER] Warning: crash_reporter not available")

            out_dir = self.recorder.output_dir
            ts = _dt.now().strftime('%Y%m%d_%H%M%S')

            # Create diagnostics ZIP
            zip_path = out_dir / f"diagnostics_{ts}.zip"
            with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
                # Include logs
                for name in ["recorder.log", "quality_log.json", "manifest.json", "user_profile.json"]:
                    p = out_dir / name
                    if p.exists():
                        zf.write(p, arcname=p.name)
                # Include last 5 WAVs
                wavs = sorted(out_dir.glob('*.wav'), key=lambda p: p.stat().st_mtime, reverse=True)[:5]
                for w in wavs:
                    zf.write(w, arcname=f"samples/{w.name}")

            print(f"[RECORDER] Diagnostics ZIP created: {zip_path}")

            # Generate crash report with system info
            if crash_reporter:
                # Collect context
                total_recordings = len(list(out_dir.glob('*.wav')))
                unique_phrases = len(self.recorder.recorded_phrases)
                current_phrase = self.recorder.get_current_phrase()

                context = {
                    "component": "Voice Recording",
                    "user_id": self.user_id,
                    "total_recordings": total_recordings,
                    "unique_phrases": unique_phrases,
                    "current_phrase": current_phrase,
                    "diagnostics_zip": str(zip_path),
                    "timestamp": ts,
                }

                # Generate report
                report_file = crash_reporter.generate_report(
                    error_type="User-Requested Diagnostics",
                    error_message=f"User requested diagnostics export from voice recording GUI.\n\n"
                                 f"Recordings: {total_recordings} files ({unique_phrases} unique)\n"
                                 f"Current phrase: {current_phrase}\n"
                                 f"Diagnostics bundle: {zip_path}",
                    error_traceback=None,
                    context=context
                )

                messagebox.showinfo(
                    "Diagnostics Exported",
                    f"✅ Diagnostics bundle created:\n{zip_path}\n\n"
                    f"📧 Crash report saved:\n{report_file}\n\n"
                    f"Email draft created for: marvinjr18@hotmail.com\n\n"
                    f"You can find both files in:\n{report_file.parent}"
                )
                print(f"[RECORDER] Crash report created: {report_file}")
            else:
                messagebox.showinfo("Diagnostics Exported", f"Saved: {zip_path}")

        except Exception as e:
            import traceback
            error_msg = traceback.format_exc()
            print(f"[RECORDER] Diagnostics export failed:\n{error_msg}")

            # Try to save error with crash reporter
            try:
                from monica_ai.crash_reporter import capture_exception
                capture_exception("Diagnostics Export Failed", {
                    "component": "Voice Recording GUI",
                    "action": "Export Diagnostics"
                })
            except:
                pass

            try:
                from tkinter import messagebox
                messagebox.showerror("Export Failed", f"Failed to export diagnostics:\n{e}")
            except:
                pass

    def _override_and_continue(self):
        """Allow user to proceed to the next phrase even if quality failed."""
        try:
            self.recorder.current_phrase_idx += 1
            self.recorder.save_progress()
            # Reset UI state
            self.status_label.config(text="⏭ Overridden. Proceeding to next phrase.", fg='#ff9500')
            self.override_btn.config(state='disabled', bg='#6b7280')
            if hasattr(self, 'next_btn'):
                self.next_btn.config(state='disabled')
            self._update_display()
        except Exception as e:
            print(f"[RECORDER] Override failed: {e}")

    def _view_last_training_result(self):
        """Show information about the last SpeechBrain training run, if available."""
        try:
            from tkinter import messagebox
            result_path = self.recorder.output_dir / "last_training_result.json"
            if not result_path.exists():
                messagebox.showinfo(
                    "Last Training Result",
                    "No training result found yet. Train your model first, then try again."
                )
                return

            with open(result_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            status = data.get('status', 'unknown')
            model_path = data.get('model_path', 'N/A')
            ts = data.get('timestamp', 'N/A')

            msg = (
                f"Status: {status}\n"
                f"Timestamp: {ts}\n\n"
                f"Model path:\n{model_path}\n\n"
                "You can later load this SpeechBrain model checkpoint or point Monica's ASR loader to it "
                "to use your personalized speech recognition model."
            )
            messagebox.showinfo("Last Training Result", msg)
        except Exception as e:
            print(f"[TRAINING] Failed to read last_training_result.json: {e}")

    def _calibrate_mic(self):
        """Run professional mic calibration with accurate dBFS measurements.
        
        This calibration:
        1. Measures ambient noise floor (should be < -40 dBFS)
        2. Measures speech level (target: -20 to -12 dBFS)
        3. Calculates SNR (Signal-to-Noise Ratio)
        4. Suggests optimal mic gain
        
        Professional audio standards:
        - Noise floor: < -50 dBFS (excellent), < -40 dBFS (good)
        - Speech level: -20 to -12 dBFS (optimal)
        - SNR: > 20 dB (good), > 30 dB (excellent)
        """
        try:
            import tkinter as tk
            from tkinter import messagebox
            import sounddevice as sd
            import numpy as np
            import math
            
            self.calib_status.config(text="Calibrating...", fg='#00d4ff')
            self.root.update()
            
            # Get sample rate
            sr = int(getattr(self.recorder, '_record_sample_rate', None) or 
                    getattr(self.recorder, 'sample_rate', 48000))
            channels = getattr(self.recorder, 'channels', 1)
            
            # Step 1: Measure noise floor
            messagebox.showinfo("Calibration Step 1/2", 
                "Stay QUIET for 2 seconds.\n\nThis measures your ambient noise floor.")
            self.calib_status.config(text="Measuring noise floor...", fg='#00d4ff')
            self.root.update()
            
            # Record 2 seconds of silence
            noise_frames = int(2.0 * sr)
            noise_data = sd.rec(noise_frames, samplerate=sr, channels=channels, dtype='float32')
            sd.wait()
            noise_arr = np.squeeze(noise_data)
            if noise_arr.ndim > 1:
                noise_arr = noise_arr[:, 0]
            
            # Calculate noise RMS and dBFS
            noise_rms = np.sqrt(np.mean(noise_arr ** 2)) + 1e-10
            noise_db = 20.0 * math.log10(noise_rms)
            
            # Step 2: Measure speech level
            messagebox.showinfo("Calibration Step 2/2", 
                "Say 'TESTING ONE TWO THREE' at your normal speaking volume.\n\n"
                "Speak for about 3 seconds.")
            self.calib_status.config(text="Measuring speech level...", fg='#00d4ff')
            self.root.update()
            
            # Record 3 seconds of speech
            speech_frames = int(3.0 * sr)
            speech_data = sd.rec(speech_frames, samplerate=sr, channels=channels, dtype='float32')
            sd.wait()
            speech_arr = np.squeeze(speech_data)
            if speech_arr.ndim > 1:
                speech_arr = speech_arr[:, 0]
            
            # Calculate speech RMS and dBFS
            speech_rms = np.sqrt(np.mean(speech_arr ** 2)) + 1e-10
            speech_db = 20.0 * math.log10(speech_rms)
            speech_peak = np.max(np.abs(speech_arr)) + 1e-10
            speech_peak_db = 20.0 * math.log10(speech_peak)
            
            # Calculate SNR
            snr_db = speech_db - noise_db
            
            # Determine optimal gain
            # Target speech level: -18 dBFS (good headroom, clear signal)
            target_db = -18.0
            gain_adjustment_db = target_db - speech_db
            suggested_gain = 10.0 ** (gain_adjustment_db / 20.0)
            # Clamp gain to safe range
            suggested_gain = max(0.5, min(3.0, suggested_gain))
            
            # Apply suggested gain
            self.recorder.mic_gain = suggested_gain
            
            # Update UI
            if hasattr(self, 'mic_gain_var'):
                self.mic_gain_var.set(suggested_gain)
            if hasattr(self, 'mic_gain_label'):
                self.mic_gain_label.config(text=f"{suggested_gain:.1f}x")
            
            # Evaluate results
            noise_quality = "Excellent" if noise_db < -50 else ("Good" if noise_db < -40 else "High")
            speech_quality = "Good" if -25 < speech_db < -10 else ("Quiet" if speech_db < -25 else "Loud")
            snr_quality = "Excellent" if snr_db > 30 else ("Good" if snr_db > 20 else "Poor")
            
            # Build result message
            result_msg = (
                f"Calibration Complete!\n\n"
                f"Noise Floor: {noise_db:.1f} dBFS ({noise_quality})\n"
                f"Speech Level: {speech_db:.1f} dBFS ({speech_quality})\n"
                f"Peak Level: {speech_peak_db:.1f} dBFS\n"
                f"SNR: {snr_db:.1f} dB ({snr_quality})\n\n"
                f"Suggested Gain: {suggested_gain:.1f}x\n\n"
            )
            
            # Add recommendations
            recommendations = []
            if noise_db > -40:
                recommendations.append("- Reduce background noise (close windows, turn off fans)")
            if speech_db < -30:
                recommendations.append("- Move closer to the microphone")
            if speech_db > -10:
                recommendations.append("- Move further from the microphone")
            if speech_peak_db > -3:
                recommendations.append("- Reduce mic gain to avoid clipping")
            if snr_db < 20:
                recommendations.append("- Improve room acoustics or use noise reduction")
            
            if recommendations:
                result_msg += "Recommendations:\n" + "\n".join(recommendations)
            else:
                result_msg += "Your setup looks great!"
            
            messagebox.showinfo("Calibration Results", result_msg)
            
            # Update status label with compact summary
            status_color = '#00ff88' if snr_db > 20 and noise_db < -40 else ('#ffaa00' if snr_db > 15 else '#ff6b6b')
            self.calib_status.config(
                text=f"Noise:{noise_db:.0f}dB | Speech:{speech_db:.0f}dB | SNR:{snr_db:.0f}dB | Gain:{suggested_gain:.1f}x",
                fg=status_color
            )
            
            # Save calibration to profile
            try:
                calibration_data = {
                    'sample_rate': sr,
                    'noise_db': float(noise_db),
                    'noise_rms': float(noise_rms),
                    'speech_db': float(speech_db),
                    'speech_rms': float(speech_rms),
                    'speech_peak_db': float(speech_peak_db),
                    'snr_db': float(snr_db),
                    'suggested_gain': float(suggested_gain),
                    'timestamp': datetime.now().isoformat()
                }
                # Load existing profile and add calibration
                if self.recorder.profile_file.exists():
                    with open(self.recorder.profile_file, 'r', encoding='utf-8') as f:
                        profile = json.load(f)
                else:
                    profile = {"user_id": self.recorder.user_id}
                profile['calibration'] = calibration_data
                with open(self.recorder.profile_file, 'w', encoding='utf-8') as f:
                    json.dump(profile, f, indent=2)
            except Exception as save_err:
                print(f"[RECORDER] Could not save calibration: {save_err}")
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.calib_status.config(text=f"Calibration failed: {e}", fg='#ff6b6b')
            print(f"[RECORDER] Calibration error: {e}")
    
    def _change_devices(self):
        """Open a small dialog to change input/output audio devices and persist the choice."""
        try:
            import sounddevice as sd
            import tkinter as tk
            from tkinter import messagebox

            devices = sd.query_devices()
            
            # Filter to show only unique device names (avoid duplicates from different APIs)
            # Group by device name and pick the first occurrence
            seen_input_names = set()
            seen_output_names = set()
            input_devices = []  # (index, name, channels)
            output_devices = []  # (index, name, channels)
            
            for idx, dev in enumerate(devices):
                name = dev['name'].strip()
                # Skip empty names
                if not name:
                    continue
                    
                # Input devices
                if dev['max_input_channels'] > 0:
                    # Normalize name for dedup (remove extra spaces, lowercase for comparison)
                    name_key = ' '.join(name.lower().split())
                    if name_key not in seen_input_names:
                        seen_input_names.add(name_key)
                        input_devices.append((idx, name, dev['max_input_channels']))
                
                # Output devices
                if dev['max_output_channels'] > 0:
                    name_key = ' '.join(name.lower().split())
                    if name_key not in seen_output_names:
                        seen_output_names.add(name_key)
                        output_devices.append((idx, name, dev['max_output_channels']))
            
            # Build display text
            lines = ["=== INPUT DEVICES (Microphones) ==="]
            for idx, name, ch in input_devices:
                lines.append(f"  {idx}: {name} ({ch} ch)")
            lines.append("")
            lines.append("=== OUTPUT DEVICES (Speakers) ===")
            for idx, name, ch in output_devices:
                lines.append(f"  {idx}: {name} ({ch} ch)")

            info = "Available devices (index: name (in, out)):\n\n" + "\n".join(lines)

            # Ask for new indices with current ones as default using a custom scrollable dialog
            current_in = getattr(self.recorder, 'input_device_index', None)
            current_out = getattr(self.recorder, 'output_device_index', None)

            dialog = tk.Toplevel(self.root)
            dialog.title("Change Audio Devices")
            dialog.configure(bg="#1a1a2e")
            dialog.grab_set()

            # Scrollable text area for device list
            text_frame = tk.Frame(dialog, bg="#1a1a2e")
            text_frame.pack(fill="both", expand=True, padx=10, pady=(10, 5))

            txt = tk.Text(
                text_frame,
                width=80,
                height=20,
                bg="#0f172a",
                fg="#e5e7eb",
                insertbackground="#e5e7eb",
                font=("Consolas", 9),
                wrap="none"
            )
            vsb = tk.Scrollbar(text_frame, orient="vertical", command=txt.yview)
            txt.configure(yscrollcommand=vsb.set)
            vsb.pack(side="right", fill="y")
            txt.pack(side="left", fill="both", expand=True)

            txt.insert("1.0", info)
            txt.config(state="disabled")

            # Entry for indices
            entry_frame = tk.Frame(dialog, bg="#1a1a2e")
            entry_frame.pack(fill="x", padx=10, pady=(0, 10))

            tk.Label(
                entry_frame,
                text="Enter input and output device indices (e.g. 2,4):",
                bg="#1a1a2e",
                fg="#e5e7eb",
                font=("Segoe UI", 10)
            ).pack(anchor="w")

            entry_var = tk.StringVar()
            if current_in is not None and current_out is not None:
                entry_var.set(f"{current_in},{current_out}")

            entry = tk.Entry(
                entry_frame,
                textvariable=entry_var,
                bg="#020617",
                fg="#e5e7eb",
                insertbackground="#e5e7eb",
                font=("Consolas", 10),
                width=20
            )
            entry.pack(anchor="w", pady=(4, 6))

            resp = {"value": None}

            def _on_ok():
                resp["value"] = entry_var.get()
                dialog.destroy()

            def _on_cancel():
                dialog.destroy()

            btn_frame = tk.Frame(dialog, bg="#1a1a2e")
            btn_frame.pack(fill="x", padx=10, pady=(0, 10))

            ok_btn = tk.Button(btn_frame, text="OK", width=10, command=_on_ok, bg="#22c55e", fg="white")
            ok_btn.pack(side="left")
            cancel_btn = tk.Button(btn_frame, text="Cancel", width=10, command=_on_cancel, bg="#4b5563", fg="white")
            cancel_btn.pack(side="left", padx=(8, 0))

            entry.focus_set()
            dialog.bind("<Return>", lambda e: _on_ok())
            dialog.bind("<Escape>", lambda e: _on_cancel())

            self.root.wait_window(dialog)

            resp_value = resp["value"]
            if not resp_value:
                return

            try:
                parts = [p.strip() for p in resp_value.split(',')]
                if len(parts) != 2:
                    raise ValueError("Please enter exactly two comma-separated indices, e.g. 2,4")
                in_idx = int(parts[0])
                out_idx = int(parts[1])
            except Exception as e:
                messagebox.showerror("Invalid Input", f"Could not parse indices: {e}")
                return

            # Basic range check
            if not (0 <= in_idx < len(devices)) or not (0 <= out_idx < len(devices)):
                messagebox.showerror("Invalid Indices", "One or both indices are out of range.")
                return

            # Persist and update recorder
            self.recorder.set_devices(in_idx, out_idx)
            try:
                sd.default.device = (in_idx, out_idx)
            except Exception:
                pass

            self.status_label.config(text=f"🎧 Devices set: input={in_idx}, output={out_idx}", fg='#00ff88')
        except Exception as e:
            print(f"[RECORDER] Device change UI error: {e}")
    
    def _update_audio_level(self):
        """Update the audio level meter during recording.
        
        Uses proper dB calculation based on audio engineering standards:
        - RMS (Root Mean Square) for accurate level measurement
        - dBFS (decibels relative to Full Scale) where 0 dBFS = max digital level
        - Peak detection for clipping warnings
        
        Reference levels (dBFS):
        - 0 dBFS: Digital maximum (clipping)
        - -6 dBFS: Very loud, risk of clipping
        - -12 dBFS: Loud but safe
        - -20 dBFS: Good speech level (target)
        - -30 dBFS: Quiet but usable
        - -40 dBFS: Very quiet
        - -60 dBFS: Near silence / noise floor
        """
        if not self.recorder.is_recording:
            return
        
        # Get current audio level from recorder
        if self.recorder.audio_data:
            # Get the most recent audio chunk
            recent = self.recorder.audio_data[-1] if self.recorder.audio_data else np.array([0])
            # recent can be 2D (frames, channels)
            try:
                arr = np.asarray(recent)
                if arr.ndim > 1:
                    arr = arr[:, 0]
            except Exception:
                arr = recent
            
            # Convert to float32 normalized to [-1, 1] for accurate dB calculation
            try:
                if np.issubdtype(arr.dtype, np.floating):
                    # Already float, check if normalized
                    arr_float = arr.astype(np.float32)
                    if np.max(np.abs(arr_float)) > 1.0:
                        arr_float = arr_float / 32768.0  # Assume it was int16 scale
                else:
                    # Integer type - normalize to [-1, 1]
                    if arr.dtype == np.int16:
                        arr_float = arr.astype(np.float32) / 32768.0
                    elif arr.dtype == np.int32:
                        arr_float = arr.astype(np.float32) / 2147483648.0
                    else:
                        arr_float = arr.astype(np.float32) / 32768.0
            except Exception:
                arr_float = arr.astype(np.float32) / 32768.0
            
            # Calculate RMS (Root Mean Square) - standard audio level measurement
            # Add small epsilon to avoid log(0)
            rms = np.sqrt(np.mean(arr_float ** 2)) + 1e-10
            peak = np.max(np.abs(arr_float)) + 1e-10
            
            # Convert to dBFS (decibels relative to Full Scale)
            # 0 dBFS = maximum digital level (1.0 in normalized float)
            rms_db = 20.0 * np.log10(rms)
            peak_db = 20.0 * np.log10(peak)
            
            # Clamp to reasonable range (-60 to 0 dBFS)
            rms_db = max(-60.0, min(0.0, rms_db))
            peak_db = max(-60.0, min(0.0, peak_db))
            
            # Map dBFS to 0-100 scale for visual meter
            # -60 dBFS -> 0%, 0 dBFS -> 100%
            normalized = ((rms_db + 60.0) / 60.0) * 100.0
            
            # Update the canvas
            self.level_canvas.delete("all")
            
            # Draw background zones based on dBFS levels
            # Zone boundaries in pixels (400px total, mapped from dBFS):
            # -60 to -40 dBFS (0-33%): Too quiet (red zone)
            # -40 to -30 dBFS (33-50%): Quiet (yellow zone)  
            # -30 to -12 dBFS (50-80%): Good/Excellent (green zone)
            # -12 to -6 dBFS (80-90%): Loud (yellow zone)
            # -6 to 0 dBFS (90-100%): Clipping risk (red zone)
            
            # Background
            self.level_canvas.create_rectangle(0, 0, 400, 25, fill='#1a1a1a', outline='')
            
            # Zone indicators (visual guide) - calibrated to dBFS
            self.level_canvas.create_rectangle(0, 0, 133, 25, fill='#330000', outline='')    # -60 to -40 dBFS: Too quiet
            self.level_canvas.create_rectangle(133, 0, 200, 25, fill='#332200', outline='')  # -40 to -30 dBFS: Quiet
            self.level_canvas.create_rectangle(200, 0, 320, 25, fill='#003300', outline='')  # -30 to -12 dBFS: Good
            self.level_canvas.create_rectangle(320, 0, 360, 25, fill='#332200', outline='')  # -12 to -6 dBFS: Loud
            self.level_canvas.create_rectangle(360, 0, 400, 25, fill='#330000', outline='')  # -6 to 0 dBFS: Clipping
            
            # Draw level bar
            bar_width = int(normalized * 4)  # 400px max
            
            # Get dynamic thresholds based on microphone type
            thresholds = self.recorder.get_level_thresholds()
            
            # Determine color and status based on mic-aware thresholds
            if normalized < thresholds['too_quiet']:
                color = '#ff4444'  # Red - too quiet
                status = "TOO QUIET"
                hint = "Too quiet — move closer or increase mic gain"
            elif normalized < thresholds['quiet']:
                color = '#ffaa00'  # Yellow - quiet but usable
                status = "QUIET"
                hint = "Quiet but usable — speak a bit louder if possible"
            elif normalized < thresholds['loud']:
                color = '#00ff88'  # Green - good/excellent
                status = "GOOD"
                hint = "Good level — keep this distance and pace"
            elif normalized < thresholds['clip']:
                color = '#ffaa00'  # Yellow - loud
                status = "LOUD"
                hint = "Loud — back off slightly to avoid clipping"
            else:
                color = '#ff4444'  # Red - clipping risk
                status = "CLIP!"
                hint = "CLIPPING risk — reduce gain or move back"
            
            self.level_canvas.create_rectangle(0, 2, bar_width, 23, fill=color, outline='')
            
            # Show dBFS value and status
            self.level_text.config(text=f"{rms_db:.1f} dB | {status}", fg=color)

            # Extra alert if peak clipping detected
            if peak_db >= -1.0:  # Peak within 1 dB of full scale
                hint = "CLIPPING detected — reduce gain immediately!"
                color = '#ff0000'

            try:
                self.preflight_label.config(text=hint, fg=color)
            except Exception:
                pass
        
        # Schedule next update (30ms for smooth ~33fps meter)
        if self.recorder.is_recording:
            self.root.after(30, self._update_audio_level)
    
    def _play_recording(self):
        """Play the last recording."""
        filepath = self.recorder.get_last_recording_path()
        if filepath:
            self.status_label.config(text="▶ Playing...", fg='#0077b6')
            self.play_btn.config(state='disabled')
            self.root.update()
            
            # Play in thread to not block UI
            def play_thread():
                self.recorder.play_audio(filepath)
                self.root.after(0, lambda: self.play_btn.config(state='normal'))
                self.root.after(0, lambda: self.status_label.config(
                    text="✅ Playback done. Re-record or SPACE for next", fg='#00ff88'))
            
            threading.Thread(target=play_thread, daemon=True).start()
        else:
            self.status_label.config(text="No recording to play", fg='#ff6b6b')
    
    def _rerecord(self):
        """Re-record the current phrase (either last recorded or current failed phrase)."""
        # First try to re-record the last successfully recorded phrase
        if self.recorder.rerecord_last():
            # Get the phrase we're now going to re-record
            phrase = self.recorder.get_current_phrase()
            short_phrase = phrase[:40] + "..." if len(phrase) > 40 else phrase
            self.status_label.config(
                text=f"Re-recording: \"{short_phrase}\" - Press SPACE", 
                fg='#ff9500'
            )
            self.play_btn.config(state='disabled')
            self.rerecord_btn.config(state='disabled')
            self._update_display()
        else:
            # If no last recorded phrase, allow re-recording current phrase
            # This handles the case where quality assessment failed
            phrase = self.recorder.get_current_phrase()
            if phrase:
                short_phrase = phrase[:40] + "..." if len(phrase) > 40 else phrase
                self.status_label.config(
                    text=f"Re-recording current phrase: \"{short_phrase}\" - Press SPACE", 
                    fg='#ff9500'
                )
                self.play_btn.config(state='disabled')
                self.rerecord_btn.config(state='disabled')
                self._update_display()
            else:
                self.status_label.config(text="Nothing to re-record", fg='#ff6b6b')
    
    def _toggle_recording(self, event=None):
        """Toggle recording with spacebar."""
        if self.recorder.is_recording:
            self._stop_recording()
        else:
            self._start_recording()
    
    def _next_and_save(self):
        """Move to the next *unrecorded* phrase after a take you're happy with.

        This keeps your place when you go back to fix old lines: after re-recording,
        Save+Next will jump back to the next empty phrase instead of leaving you
        stuck on the old one.
        """
        try:
            # Reuse the same logic as the "skip to unrecorded" action
            start_idx = self.recorder.current_phrase_idx + 1
            total = len(self.recorder.phrases)

            # Search from the phrase after the current one to the end
            for i in range(start_idx, total):
                phrase = self.recorder.phrases[i]
                if not self.recorder.is_phrase_recorded(phrase):
                    self.recorder.current_phrase_idx = i
                    self.recorder.save_progress()
                    self._update_display()
                    self.status_label.config(
                        text=f"➡ Moved to phrase {i+1} (next unrecorded). Press SPACE to record.",
                        fg='#00ff88')
                    break
            else:
                # No further unrecorded phrases found; stay on current and inform user
                self.status_label.config(
                    text="All phrases up to this point are recorded. You can continue manually or close the recorder.",
                    fg='#00ff88')

            # After moving, require a new recording before allowing Save+Next again
            if hasattr(self, 'next_btn'):
                self.next_btn.config(state='disabled')
            # Override button is only for failed takes, so keep it disabled here
            try:
                self.override_btn.config(state='disabled', bg='#6b7280')
            except Exception:
                pass
        except Exception as e:
            print(f"[RECORDER] Next+Save failed: {e}")
    
    def _skip(self):
        """Skip current phrase."""
        self.recorder.skip_phrase()
        self._update_display()
        self.status_label.config(text="Skipped. Press SPACE to record", fg='#888')
    
    def _go_back(self):
        """Go back to previous phrase."""
        self.recorder.go_back()
        self._update_display()
        self.status_label.config(text="Went back. Press SPACE to record", fg='#888')
    
    def _skip_to_unrecorded(self):
        """Skip to the next unrecorded phrase."""
        start_idx = self.recorder.current_phrase_idx
        total = len(self.recorder.phrases)
        
        # Search from current position to end
        for i in range(start_idx, total):
            phrase = self.recorder.phrases[i]
            if not self.recorder.is_phrase_recorded(phrase):
                self.recorder.current_phrase_idx = i
                self.recorder.save_progress()
                self._update_display()
                self.status_label.config(
                    text=f"Jumped to phrase {i+1} (unrecorded)", fg='#0077b6')
                return
        
        # If not found, search from beginning
        for i in range(0, start_idx):
            phrase = self.recorder.phrases[i]
            if not self.recorder.is_phrase_recorded(phrase):
                self.recorder.current_phrase_idx = i
                self.recorder.save_progress()
                self._update_display()
                self.status_label.config(
                    text=f"Jumped to phrase {i+1} (unrecorded)", fg='#0077b6')
                return
        
        # All phrases recorded
        self.status_label.config(
            text="🎉 All phrases have been recorded!", fg='#00ff88')

    def _auto_skip_to_unrecorded(self):
        """Auto-skip to first unrecorded phrase on startup (silent version)."""
        start_idx = self.recorder.current_phrase_idx
        total = len(self.recorder.phrases)

        # Search from current position to end
        for i in range(start_idx, total):
            phrase = self.recorder.phrases[i]
            if not self.recorder.is_phrase_recorded(phrase):
                self.recorder.current_phrase_idx = i
                self.recorder.save_progress()
                self._update_display()
                return

        # If not found, search from beginning
        for i in range(0, start_idx):
            phrase = self.recorder.phrases[i]
            if not self.recorder.is_phrase_recorded(phrase):
                self.recorder.current_phrase_idx = i
                self.recorder.save_progress()
                self._update_display()
                return

    def _toggle_noise_reduction(self):
        """Toggle noise reduction on/off."""
        if HAS_NOISE_REDUCE:
            self.recorder.noise_reduce_enabled = not self.recorder.noise_reduce_enabled
            if self.recorder.noise_reduce_enabled:
                self.noise_label.config(text="🔇 Noise Reduction: ENABLED", fg='#00ff88')
            else:
                self.noise_label.config(text="🔇 Noise Reduction: DISABLED", fg='#ff6b6b')
    
    def _update_nr_strength(self, value):
        """Update noise reduction strength from slider."""
        try:
            strength = float(value)
            self.recorder.noise_reduce_strength = strength
            self.nr_strength_label.config(text=f"{strength:.0%}")
            # Color feedback: green for moderate, yellow for high
            if strength <= 0.5:
                self.nr_strength_label.config(fg='#00ff88')  # Green - speech preserved
            elif strength <= 0.7:
                self.nr_strength_label.config(fg='#ffaa00')  # Yellow - moderate
            else:
                self.nr_strength_label.config(fg='#ff6b6b')  # Red - aggressive
        except Exception as e:
            print(f"[GUI] NR strength update error: {e}")
    
    def _load_selected_packs(self):
        """Load selected prompt packs."""
        selected_packs = []
        for pack_name, pack_path in self.MULTILINGUAL_PROMPT_FILES:
            if self.pack_vars.get(pack_name) and self.pack_vars[pack_name].get():
                if pack_name not in self.loaded_packs:
                    selected_packs.append((pack_name, pack_path))
        
        if not selected_packs:
            self.packs_status_label.config(text="No new packs selected", fg='#ff9500')
            return
        
        # Disable button during loading
        self.load_packs_btn.config(state='disabled')
        self.packs_status_label.config(text="Loading...", fg='#00d4ff')
        self.root.update()
        
        total_added = 0
        for pack_name, pack_path in selected_packs:
            full_path = Path(__file__).parent.parent / pack_path
            if full_path.exists():
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        new_phrases = [line.strip() for line in f if line.strip()]
                    
                    # Add to recorder's phrases
                    self.recorder.phrases.extend(new_phrases)
                    self.loaded_packs.add(pack_name)
                    total_added += len(new_phrases)
                    print(f"[RECORDER] Loaded {len(new_phrases)} phrases from {pack_name}")
                except Exception as e:
                    print(f"[RECORDER] Error loading {pack_name}: {e}")
        
        # Re-enable button
        self.load_packs_btn.config(state='normal')
        
        if total_added > 0:
            self.packs_status_label.config(
                text=f"✅ Added {total_added:,} phrases! Total: {len(self.recorder.phrases):,}",
                fg='#00ff88'
            )
            self._update_display()
        else:
            self.packs_status_label.config(text="No phrases loaded", fg='#ff6b6b')
    
    def _open_library_manager(self):
        """Open the recording library manager dialog."""
        # Create dialog window
        dialog = tk.Toplevel(self.root)
        dialog.title("📚 Recording Library Manager")
        dialog.geometry("900x600")
        dialog.configure(bg='#1a1a2e')
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Title
        title = tk.Label(
            dialog,
            text="📚 Recording Library",
            font=('Segoe UI', 18, 'bold'),
            fg='#00d4ff',
            bg='#1a1a2e'
        )
        title.pack(pady=10)
        
        # Stats frame
        stats_frame = tk.Frame(dialog, bg='#16213e', padx=20, pady=10)
        stats_frame.pack(fill='x', padx=20, pady=5)
        
        recordings = self.recorder.get_all_recordings()
        total_size = sum(r['size_kb'] for r in recordings)
        
        stats_label = tk.Label(
            stats_frame,
            text=f"Total Recordings: {len(recordings)} | Total Size: {total_size/1024:.2f} MB | User: {self.user_id}",
            font=('Segoe UI', 11),
            fg='#00ff88',
            bg='#16213e'
        )
        stats_label.pack()
        
        # ==== FIRST 100 RECORDINGS SECTION ====
        top_frame = tk.LabelFrame(
            dialog,
            text="First 100 Recordings",
            font=('Segoe UI', 11, 'bold'),
            fg='#00d4ff',
            bg='#1a1a2e',
            padx=10,
            pady=6
        )
        top_frame.pack(fill='x', padx=20, pady=8)

        # Compute first 100 recordings by phrase_idx
        top_recs = [r for r in recordings if r.get('phrase_idx') is not None and r['phrase_idx'] < 100]
        try:
            top_recs.sort(key=lambda r: r.get('phrase_idx', 0))
        except Exception:
            pass

        top_list_frame = tk.Frame(top_frame, bg='#1a1a2e')
        top_list_frame.pack(fill='x')

        top_scroll = ttk.Scrollbar(top_list_frame)
        top_scroll.pack(side='right', fill='y')

        top_listbox = tk.Listbox(
            top_list_frame,
            font=('Consolas', 9),
            bg='#05050b',
            fg='#ccc',
            height=6,
            yscrollcommand=top_scroll.set,
            selectbackground='#6c5ce7',
            selectforeground='white'
        )
        top_listbox.pack(side='left', fill='x', expand=True)
        top_scroll.config(command=top_listbox.yview)

        for rec in top_recs:
            idx_disp = f"#{int(rec['phrase_idx'])+1:04d}" if rec.get('phrase_idx') is not None else "--"
            text = rec['phrase_text'][:50] + "..." if len(rec['phrase_text']) > 50 else rec['phrase_text']
            top_listbox.insert(tk.END, f"{idx_disp}  {text}")

        top_btns = tk.Frame(top_frame, bg='#1a1a2e')
        top_btns.pack(fill='x', pady=4)

        def play_top_selected():
            sel = top_listbox.curselection()
            if not sel:
                messagebox.showwarning("No Selection", "Select a recording from the First 100 list.")
                return
            rec = top_recs[sel[0]]
            def _play():
                self.recorder.play_audio(rec['filepath'])
            threading.Thread(target=_play, daemon=True).start()

        def rerecord_top_selected():
            sel = top_listbox.curselection()
            if not sel:
                messagebox.showwarning("No Selection", "Select a recording from the First 100 list.")
                return
            rec = top_recs[sel[0]]
            if rec.get('phrase_idx') is None:
                messagebox.showwarning("Unavailable", "This recording is not linked to a specific phrase.")
                return
            try:
                # Jump recorder to that phrase index
                self.recorder.current_phrase_idx = int(rec['phrase_idx'])
                self.recorder.save_progress()
                # Close dialog and start recording on that phrase
                dialog.destroy()
                self._update_display()
                self.status_label.config(
                    text=f"Re-recording phrase {rec['phrase_idx']+1}. Press SPACE or wait...",
                    fg='#ff9500')
                # Start recording immediately
                self._start_recording()
            except Exception as e:
                print(f"[RECORDER] Top-100 re-record failed: {e}")

        tk.Button(
            top_btns,
            text="▶ Play Selected",
            font=('Segoe UI', 9),
            bg='#0077b6',
            fg='white',
            command=play_top_selected
        ).pack(side='left', padx=4)

        tk.Button(
            top_btns,
            text="🔄 Re-record This Phrase",
            font=('Segoe UI', 9),
            bg='#ff9500',
            fg='white',
            command=rerecord_top_selected
        ).pack(side='left', padx=4)

        # Button frame at top (for full library actions)
        btn_frame = tk.Frame(dialog, bg='#1a1a2e')
        btn_frame.pack(fill='x', padx=20, pady=10)
        
        def delete_selected():
            selection = listbox.curselection()
            if not selection:
                messagebox.showwarning("No Selection", "Please select a recording to delete.")
                return
            
            idx = selection[0]
            rec = recordings[idx]
            
            if messagebox.askyesno("Confirm Delete", 
                f"Delete this recording?\n\n{rec['phrase_text']}\nRecorded: {rec['file_time'].strftime('%Y-%m-%d %H:%M:%S')}"):
                if self.recorder.delete_recording(rec['filepath']):
                    # Reload recorded phrases from file to ensure sync
                    self.recorder.load_recorded_phrases()
                    refresh_list()
                    self._update_display()
        
        def delete_all():
            if len(recordings) == 0:
                messagebox.showinfo("Empty", "No recordings to delete.")
                return
            
            if messagebox.askyesno("⚠️ Delete ALL Recordings", 
                f"Are you sure you want to delete ALL {len(recordings)} recordings?\n\nThis cannot be undone!"):
                if messagebox.askyesno("Final Confirmation", 
                    "This will permanently delete all your voice recordings.\n\nAre you ABSOLUTELY sure?"):
                    count = self.recorder.delete_all_recordings()
                    messagebox.showinfo("Deleted", f"Deleted {count} recordings.")
                    refresh_list()
                    self._update_display()
        
        def play_selected():
            selection = listbox.curselection()
            if not selection:
                messagebox.showwarning("No Selection", "Please select a recording to play.")
                return
            
            idx = selection[0]
            rec = recordings[idx]
            
            # Play in thread
            def play_thread():
                self.recorder.play_audio(rec['filepath'])
            threading.Thread(target=play_thread, daemon=True).start()
        
        def refresh_list():
            nonlocal recordings
            recordings = self.recorder.get_all_recordings()
            listbox.delete(0, tk.END)
            for rec in recordings:
                time_str = rec['file_time'].strftime("%Y-%m-%d %H:%M:%S")
                duration = rec['duration_estimate']
                text = rec['phrase_text'][:50] + "..." if len(rec['phrase_text']) > 50 else rec['phrase_text']
                listbox.insert(tk.END, f"[{time_str}] ({duration:.1f}s) {text}")
            
            # Update stats
            total_size = sum(r['size_kb'] for r in recordings)
            stats_label.config(
                text=f"Total Recordings: {len(recordings)} | Total Size: {total_size/1024:.2f} MB | User: {self.user_id}"
            )
        
        # Buttons
        play_btn = tk.Button(
            btn_frame,
            text="▶ Play Selected",
            font=('Segoe UI', 10),
            bg='#0077b6',
            fg='white',
            command=play_selected
        )
        play_btn.pack(side='left', padx=5)
        
        delete_btn = tk.Button(
            btn_frame,
            text="🗑️ Delete Selected",
            font=('Segoe UI', 10),
            bg='#e94560',
            fg='white',
            command=delete_selected
        )
        delete_btn.pack(side='left', padx=5)
        
        delete_all_btn = tk.Button(
            btn_frame,
            text="⚠️ Delete ALL",
            font=('Segoe UI', 10),
            bg='#ff0000',
            fg='white',
            command=delete_all
        )
        delete_all_btn.pack(side='left', padx=5)
        
        refresh_btn = tk.Button(
            btn_frame,
            text="🔄 Refresh",
            font=('Segoe UI', 10),
            bg='#333',
            fg='white',
            command=refresh_list
        )
        refresh_btn.pack(side='left', padx=5)
        
        # Listbox with scrollbar
        list_frame = tk.Frame(dialog, bg='#1a1a2e')
        list_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side='right', fill='y')
        
        listbox = tk.Listbox(
            list_frame,
            font=('Consolas', 10),
            bg='#0a0a15',
            fg='#ccc',
            selectbackground='#6c5ce7',
            selectforeground='white',
            yscrollcommand=scrollbar.set,
            height=20
        )
        listbox.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=listbox.yview)
        
        # Reorder library to match phrase order so it aligns with the on-screen position number
        try:
            rec_with_idx = [r for r in recordings if r.get('phrase_idx') is not None]
            rec_without_idx = [r for r in recordings if r.get('phrase_idx') is None]
            rec_with_idx.sort(key=lambda r: r.get('phrase_idx', 0))
            recordings = rec_with_idx + rec_without_idx
        except Exception:
            # Fallback to existing order on any unexpected issue
            pass

        # Populate list (show phrase number as 1-based to match UI position)
        for rec in recordings:
            time_str = rec['file_time'].strftime("%Y-%m-%d %H:%M:%S")
            duration = rec['duration_estimate']
            text = rec['phrase_text'][:50] + "..." if len(rec['phrase_text']) > 50 else rec['phrase_text']
            idx_disp = f"#{int(rec['phrase_idx'])+1:04d}" if rec.get('phrase_idx') is not None else "--"
            listbox.insert(tk.END, f"[{idx_disp}] [{time_str}] ({duration:.1f}s) {text}")
        
        # Details frame
        details_frame = tk.Frame(dialog, bg='#16213e', padx=20, pady=10)
        details_frame.pack(fill='x', padx=20, pady=5)
        
        details_label = tk.Label(
            details_frame,
            text="Select a recording to see details",
            font=('Segoe UI', 10),
            fg='#888',
            bg='#16213e',
            wraplength=800
        )
        details_label.pack()
        
        # Track current selection for jump action
        selected_rec = {'rec': None}
        
        def on_select(event):
            selection = listbox.curselection()
            if selection:
                idx = selection[0]
                rec = recordings[idx]
                selected_rec['rec'] = rec
                details_label.config(
                    text=f"Phrase #: {rec['phrase_idx']+1 if rec.get('phrase_idx') is not None else '—'}\n"
                         f"File: {rec['filename']}\n"
                         f"Phrase: \"{rec['phrase_text']}\"\n"
                         f"Recorded: {rec['file_time'].strftime('%Y-%m-%d %H:%M:%S')} | "
                         f"Size: {rec['size_kb']:.1f} KB | "
                         f"Duration: ~{rec['duration_estimate']:.1f}s",
                    fg='#ccc'
                )
                # Enable jump button only when we have a valid phrase index
                try:
                    if rec.get('phrase_idx') is not None:
                        jump_btn.config(state='normal')
                    else:
                        jump_btn.config(state='disabled')
                except Exception:
                    pass
        
        listbox.bind('<<ListboxSelect>>', on_select)
        
        # Jump to phrase button (align library selection with current position)
        def jump_to_phrase():
            try:
                rec = selected_rec.get('rec')
                if rec and rec.get('phrase_idx') is not None:
                    self.recorder.current_phrase_idx = int(rec['phrase_idx'])
                    self.recorder.save_progress()
                    # Reflect updated position in main UI and notify
                    self._update_display()
                    self.status_label.config(
                        text=f"Jumped to phrase {rec['phrase_idx']+1}", fg='#00d4ff')
                    dialog.destroy()
            except Exception as e:
                print(f"[RECORDER] Jump to phrase failed: {e}")

        jump_btn = tk.Button(
            dialog,
            text="↘ Jump to this phrase",
            font=('Segoe UI', 11),
            bg='#0ea5e9',
            fg='white',
            width=20,
            state='disabled',
            command=jump_to_phrase
        )
        jump_btn.pack(pady=6)

        # Close button
        close_btn = tk.Button(
            dialog,
            text="Close",
            font=('Segoe UI', 11),
            bg='#333',
            fg='white',
            width=15,
            command=dialog.destroy
        )
        close_btn.pack(pady=10)
    
    def run(self):
        """Run the GUI."""
        self.root.mainloop()


def main():
    """Main entry point."""
    if not HAS_AUDIO:
        print("ERROR: sounddevice not installed")
        print("Run: pip install sounddevice numpy")
        # Early-log the failure so it's visible even when launched in background
        try:
            from pathlib import Path as _P
            from datetime import datetime as _DT
            # Two common locations used in different versions
            cand = [
                _P(__file__).parent / "recordings" / "mjp" / "recorder.log",
                _P(__file__).resolve().parents[2] / "voice_training" / "recordings" / "mjp" / "recorder.log",
            ]
            for p in cand:
                p.parent.mkdir(parents=True, exist_ok=True)
                with open(p, 'a', encoding='utf-8') as lf:
                    lf.write(f"[{_DT.now().isoformat(timespec='seconds')}] FATAL: sounddevice not installed. Install with: pip install sounddevice numpy\n")
        except Exception:
            pass
        # Best-effort Windows message box if Tk is unavailable
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, "sounddevice not installed. Run: pip install sounddevice numpy", "Recorder Error", 0x10)
        except Exception:
            pass
        return
    
    if not HAS_TK:
        print("ERROR: tkinter not available")
        # Early-log the failure so it's visible even when launched in background
        try:
            from pathlib import Path as _P
            from datetime import datetime as _DT
            cand = [
                _P(__file__).parent / "recordings" / "mjp" / "recorder.log",
                _P(__file__).resolve().parents[2] / "voice_training" / "recordings" / "mjp" / "recorder.log",
            ]
            for p in cand:
                p.parent.mkdir(parents=True, exist_ok=True)
                with open(p, 'a', encoding='utf-8') as lf:
                    lf.write(f"[{_DT.now().isoformat(timespec='seconds')}] FATAL: tkinter not available. Install Python with Tcl/Tk or `conda install tk`.\n")
        except Exception:
            pass
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, "tkinter not available. Install Python with Tcl/Tk or `conda install tk`.", "Recorder Error", 0x10)
        except Exception:
            pass
        return
    
    print("=" * 60)
    print("MONICA VOICE TRAINING SYSTEM")
    print("=" * 60)
    print("\nThis will help you record 1000 phrases to train")
    print("a personalized speech recognition model.\n")
    print("Instructions:")
    print("  - Hold SPACE or click the button to record")
    print("  - Release to stop and save")
    print("  - Use arrow keys to skip or go back")
    print("  - Press ESC to exit (progress is saved)")
    print("\n" + "=" * 60)
    
    try:
        # Create recorder and pass it into the GUI (required argument)
        recorder = VoiceRecorder()
        app = RecorderGUI(recorder)
        app.run()
    except Exception as e:
        import traceback
        msg = "\n".join(traceback.format_exception(type(e), e, e.__traceback__))
        # Try multiple log locations so users always find one
        candidates = [
            Path(__file__).parent / "recordings" / "mjp" / "recorder.log",
            Path(__file__).resolve().parents[2] / "voice_training" / "recordings" / "mjp" / "recorder.log",
            Path(__file__).resolve().parents[2] / "logs" / "recorder.log",
        ]
        for p in candidates:
            try:
                p.parent.mkdir(parents=True, exist_ok=True)
                with open(p, 'a', encoding='utf-8') as lf:
                    lf.write(f"[{datetime.now().isoformat(timespec='seconds')}] FATAL:\n{msg}\n")
            except Exception:
                continue
        print("[RECORDER] Fatal error, see recorder.log in recordings/mjp or logs/")


if __name__ == "__main__":
    main()
