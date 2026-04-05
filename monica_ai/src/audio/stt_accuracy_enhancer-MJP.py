"""
STT Accuracy Enhancer for Monica AI
Fixes: Background noise, speaking speed variations, vocabulary gaps, accent drift
"""
import numpy as np
import torch

# Try to import torchaudio with fallback
try:
    import torchaudio
    TORCHAUDIO_AVAILABLE = True
except Exception as e:
    print(f"[STT-ENHANCER] torchaudio import failed: {e}")
    TORCHAUDIO_AVAILABLE = False
    torchaudio = None

from pathlib import Path
from typing import Optional, Dict, List, Tuple
import json
import time
from collections import deque
import re

try:
    import noisereduce as nr
    HAS_NOISEREDUCE = True
except ImportError:
    HAS_NOISEREDUCE = False
    print("[STT-ENHANCER] Warning: noisereduce not available - install with: pip install noisereduce")


class STTAccuracyEnhancer:
    """
    Comprehensive STT accuracy enhancement system.
    Addresses all 4 major accuracy issues.
    """
    
    def __init__(self, sample_rate: int = 16000, model_dir: Path = None):
        """
        Initialize STT accuracy enhancer.
        
        Args:
            sample_rate: Audio sample rate (default 16000 for ASR)
            model_dir: Path to model directory for vocabulary/profile storage
        """
        self.sample_rate = sample_rate
        
        # Model directory for storing profiles
        if model_dir is None:
            model_dir = Path(__file__).resolve().parents[2] / "personal_voice_model"
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        # ============================================================
        # FIX 1: BACKGROUND NOISE HANDLING
        # ============================================================
        self.noise_profile = None
        self.noise_reduction_enabled = True
        self.adaptive_noise_floor = 0.001
        self.noise_history = deque(maxlen=100)
        
        # ============================================================
        # FIX 2: SPEAKING SPEED NORMALIZATION
        # ============================================================
        self.target_speaking_rate = 150  # words per minute (average)
        self.speed_normalization_enabled = True
        self._speed_norm_disabled_notice_shown = False
        self.speed_history = deque(maxlen=50)
        self.user_avg_speed = None
        
        # ============================================================
        # FIX 3: DYNAMIC VOCABULARY EXPANSION
        # ============================================================
        self.vocabulary_file = self.model_dir / "dynamic_vocabulary.json"
        self.custom_vocabulary = self._load_vocabulary()
        self.vocabulary_corrections = self._load_corrections()
        self.new_words_buffer = []
        
        # ============================================================
        # FIX 4: ACCENT DRIFT ADAPTATION
        # ============================================================
        self.accent_profile_file = self.model_dir / "accent_profile.json"
        self.accent_profile = self._load_accent_profile()
        self.phoneme_corrections = {}
        self.accent_drift_threshold = 0.15  # 15% change triggers retraining suggestion
        
        print("[STT-ENHANCER] Initialized with all 4 accuracy fixes")
        print(f"[STT-ENHANCER] Vocabulary: {len(self.custom_vocabulary)} words")
        print(f"[STT-ENHANCER] Noise reduction: {'Enabled' if HAS_NOISEREDUCE else 'Disabled (install noisereduce)'}")
    
    # ============================================================
    # FIX 1: BACKGROUND NOISE HANDLING
    # ============================================================
    
    def reduce_background_noise(self, audio: np.ndarray) -> np.ndarray:
        """
        Advanced noise reduction using spectral subtraction and adaptive filtering.
        
        Args:
            audio: Input audio array (float32, mono)
            
        Returns:
            Noise-reduced audio
        """
        if not HAS_NOISEREDUCE:
            # Fallback: Simple noise gate
            return self._simple_noise_gate(audio)
        
        try:
            # Adaptive noise reduction
            # Use learned noise profile if available
            if self.noise_profile is not None:
                reduced = nr.reduce_noise(
                    y=audio,
                    sr=self.sample_rate,
                    stationary=True,
                    prop_decrease=1.0
                )
            else:
                # Standard noise reduction
                reduced = nr.reduce_noise(
                    y=audio,
                    sr=self.sample_rate,
                    stationary=False
                )
            
            # Update noise floor estimate
            self._update_noise_floor(audio, reduced)
            
            return reduced
            
        except Exception as e:
            print(f"[STT-ENHANCER] Noise reduction failed: {e}")
            return audio
    
    def _simple_noise_gate(self, audio: np.ndarray, threshold_db: float = -40) -> np.ndarray:
        """Simple noise gate fallback when noisereduce unavailable."""
        # Convert threshold to linear
        threshold = 10 ** (threshold_db / 20)
        
        # Calculate energy
        energy = np.abs(audio)
        
        # Apply gate with smooth transitions
        gate = np.where(energy > threshold, 1.0, 0.1)
        
        return audio * gate
    
    def _update_noise_floor(self, original: np.ndarray, reduced: np.ndarray):
        """Update adaptive noise floor based on reduction results."""
        # Estimate noise as difference between original and reduced
        noise_estimate = np.abs(original - reduced)
        noise_level = np.mean(noise_estimate)
        
        self.noise_history.append(noise_level)
        
        if len(self.noise_history) >= 10:
            self.adaptive_noise_floor = np.median(list(self.noise_history))
    
    def calibrate_noise_profile(self, ambient_audio: np.ndarray):
        """
        Calibrate noise profile from ambient audio sample.
        
        Args:
            ambient_audio: 2-3 seconds of ambient noise (no speech)
        """
        if not HAS_NOISEREDUCE:
            print("[STT-ENHANCER] Noise profile calibration requires noisereduce")
            return
        
        # Store noise profile for stationary noise reduction
        self.noise_profile = ambient_audio
        print(f"[STT-ENHANCER] Noise profile calibrated ({len(ambient_audio)/self.sample_rate:.1f}s sample)")
    
    # ============================================================
    # FIX 2: SPEAKING SPEED NORMALIZATION
    # ============================================================
    
    def normalize_speaking_speed(self, audio: torch.Tensor, estimated_wpm: Optional[float] = None) -> torch.Tensor:
        """
        Normalize speaking speed to improve recognition of fast/slow speech.
        
        Args:
            audio: Input audio tensor [samples] or [1, samples]
            estimated_wpm: Estimated words per minute (optional)
            
        Returns:
            Speed-normalized audio tensor
        """
        if not self.speed_normalization_enabled:
            return audio
        
        # Ensure 1D tensor
        if audio.dim() == 2:
            audio = audio.squeeze(0)
        
        # Estimate speaking rate if not provided
        if estimated_wpm is None:
            estimated_wpm = self._estimate_speaking_rate(audio)
        
        # Calculate speed adjustment factor
        if self.user_avg_speed is not None:
            target_speed = self.user_avg_speed
        else:
            target_speed = self.target_speaking_rate
        
        speed_ratio = estimated_wpm / target_speed if estimated_wpm > 0 else 1.0
        
        # Only adjust if significantly different (>10%)
        if abs(speed_ratio - 1.0) < 0.1:
            return audio
        
        # Clamp speed adjustment to reasonable range
        speed_ratio = np.clip(speed_ratio, 0.7, 1.5)
        
        try:
            # Time-stretch audio to normalize speed
            # speed_ratio > 1.0 = slow down (speaker is too fast)
            # speed_ratio < 1.0 = speed up (speaker is too slow)
            effects = [
                ["tempo", str(1.0 / speed_ratio)],  # Inverse because tempo is playback speed
                ["rate", str(self.sample_rate)]
            ]
            
            normalized, _ = torchaudio.sox_effects.apply_effects_tensor(
                audio.unsqueeze(0),
                self.sample_rate,
                effects
            )
            
            # Update speed history
            self.speed_history.append(estimated_wpm)
            if len(self.speed_history) >= 20:
                self.user_avg_speed = np.median(list(self.speed_history))
            
            return normalized.squeeze(0)
            
        except Exception as e:
            msg = str(e)
            if ("sox" in msg.lower() and "windows" in msg.lower()) or ("sox extension" in msg.lower()):
                self.speed_normalization_enabled = False
                if not self._speed_norm_disabled_notice_shown:
                    print(f"[STT-ENHANCER] Speed normalization disabled on Windows: {e}")
                    self._speed_norm_disabled_notice_shown = True
            else:
                print(f"[STT-ENHANCER] Speed normalization failed: {e}")
            return audio
    
    def _estimate_speaking_rate(self, audio: torch.Tensor) -> float:
        """
        Estimate speaking rate (words per minute) from audio.
        Uses syllable detection as proxy.
        """
        # Convert to numpy
        audio_np = audio.numpy() if isinstance(audio, torch.Tensor) else audio
        
        # Detect syllables using energy peaks
        # Apply bandpass filter for speech
        from scipy import signal
        nyquist = self.sample_rate / 2
        b, a = signal.butter(4, [300/nyquist, 3000/nyquist], btype='band')
        filtered = signal.filtfilt(b, a, audio_np)
        
        # Calculate energy envelope
        energy = np.abs(filtered)
        kernel_size = int(self.sample_rate * 0.02)
        if kernel_size < 3:
            kernel_size = 3
        if kernel_size % 2 == 0:
            kernel_size += 1
        envelope = signal.medfilt(energy, kernel_size=kernel_size)
        
        # Find peaks (syllables)
        threshold = np.mean(envelope) * 1.5
        peaks, _ = signal.find_peaks(envelope, height=threshold, distance=int(self.sample_rate * 0.15))
        
        # Estimate WPM (assume ~1.5 syllables per word)
        duration_minutes = len(audio_np) / self.sample_rate / 60
        if duration_minutes > 0:
            syllables_per_minute = len(peaks) / duration_minutes
            wpm = syllables_per_minute / 1.5
            return max(50, min(250, wpm))  # Clamp to reasonable range
        
        return self.target_speaking_rate
    
    # ============================================================
    # FIX 3: DYNAMIC VOCABULARY EXPANSION
    # ============================================================
    
    def add_to_vocabulary(self, word: str, phonetic: Optional[str] = None):
        """
        Add new word to dynamic vocabulary.
        
        Args:
            word: Word to add
            phonetic: Optional phonetic spelling
        """
        word_lower = word.lower().strip()
        
        if word_lower and word_lower not in self.custom_vocabulary:
            self.custom_vocabulary[word_lower] = {
                "added": time.strftime("%Y-%m-%d %H:%M:%S"),
                "phonetic": phonetic,
                "frequency": 1
            }
            self.new_words_buffer.append(word_lower)
            
            # Auto-save every 10 new words
            if len(self.new_words_buffer) >= 10:
                self._save_vocabulary()
                self.new_words_buffer.clear()
            
            print(f"[STT-ENHANCER] Added to vocabulary: '{word_lower}'")
    
    def correct_with_vocabulary(self, text: str) -> str:
        """
        Apply vocabulary-based corrections to transcription.
        
        Args:
            text: Raw transcription
            
        Returns:
            Corrected transcription
        """
        if not text:
            return text
        
        words = text.split()
        corrected_words = []
        
        for word in words:
            word_lower = word.lower()
            
            # Check direct corrections
            if word_lower in self.vocabulary_corrections:
                corrected_words.append(self.vocabulary_corrections[word_lower])
            # Check if in custom vocabulary
            elif word_lower in self.custom_vocabulary:
                # Update frequency
                self.custom_vocabulary[word_lower]["frequency"] += 1
                corrected_words.append(word)
            else:
                # Try fuzzy matching
                best_match = self._fuzzy_match_vocabulary(word_lower)
                if best_match:
                    corrected_words.append(best_match)
                else:
                    corrected_words.append(word)
        
        corrected = ' '.join(corrected_words)
        
        if corrected.lower() != text.lower():
            print(f"[STT-ENHANCER] Corrected: '{text}' → '{corrected}'")
        
        return corrected
    
    def _fuzzy_match_vocabulary(self, word: str, threshold: float = 0.8) -> Optional[str]:
        """Fuzzy match word against vocabulary."""
        if len(word) < 3:
            return None
        
        best_match = None
        best_score = 0
        
        for vocab_word in self.custom_vocabulary.keys():
            if abs(len(vocab_word) - len(word)) > 2:
                continue
            
            # Simple character-based similarity
            matches = sum(1 for a, b in zip(word, vocab_word) if a == b)
            score = matches / max(len(word), len(vocab_word))
            
            # Bonus for same start
            if word[:2] == vocab_word[:2]:
                score += 0.2
            
            if score > best_score and score >= threshold:
                best_score = score
                best_match = vocab_word
        
        return best_match
    
    def _load_vocabulary(self) -> Dict:
        """Load custom vocabulary from file."""
        if self.vocabulary_file.exists():
            try:
                with open(self.vocabulary_file, 'r', encoding='utf-8') as f:
                    vocab = json.load(f)
                print(f"[STT-ENHANCER] Loaded {len(vocab)} custom vocabulary words")
                return vocab
            except Exception as e:
                print(f"[STT-ENHANCER] Error loading vocabulary: {e}")
        
        # Default vocabulary
        return {
            "monica": {"added": "default", "frequency": 1000},
            "initialize": {"added": "default", "frequency": 500},
            "mjp": {"added": "default", "frequency": 500},
            "marvin": {"added": "default", "frequency": 100},
            "polanco": {"added": "default", "frequency": 100},
        }
    
    def _load_corrections(self) -> Dict:
        """Load common misrecognition corrections."""
        return {
            # Monica variations
            'mahanika': 'monica', 'mamanika': 'monica', 'monika': 'monica',
            'monique': 'monica', 'monic': 'monica', 'manica': 'monica',
            'onica': 'monica', 'mmonica': 'monica',
            
            # Initialize variations
            'in it': 'initialize', 'innit': 'initialize', 'initial': 'initialize',
            'initiate': 'initialize', 'init': 'initialize',
            
            # Historical figures - Christopher Columbus
            'crispicolontis': 'christopher columbus', 'crispicalontes': 'christopher columbus',
            'christofercolumbus': 'christopher columbus', 'cristofercolumbus': 'christopher columbus',
            'christopercolumbus': 'christopher columbus', 'kristofercolumbus': 'christopher columbus',
            'crisopher': 'christopher', 'cristopher': 'christopher', 'kristopher': 'christopher',
            'colombus': 'columbus', 'columus': 'columbus', 'columbis': 'columbus',
            
            # Common proper nouns
            'america': 'america', 'amercia': 'america', 'amerca': 'america',
            'psychology': 'psychology', 'psycology': 'psychology', 'sychology': 'psychology',
            'psychological': 'psychological', 'psycological': 'psychological', 'sychological': 'psychological',
            'psycho': 'psychological',  # Common mishearing of "psychological"
            'syco': 'psychological', 'sicko': 'psychological', 'siko': 'psychological',
            'counseling': 'counseling', 'councing': 'counseling', 'counceling': 'counseling',
            'counselling': 'counseling', 'counsling': 'counseling',
            
            # Common contractions
            'dont': "don't", 'cant': "can't", 'wont': "won't",
            'im': "i'm", 'youre': "you're", 'theyre': "they're",
            
            # REMOVED problematic number corrections that break normal sentences:
            # 'won': 'one', 'too': 'two', 'for': 'four', 'ate': 'eight'
            # These were changing "tell me about psychology" incorrectly
            
            # Date/time
            'dateof': 'date of', 'dateofbirth': 'date of birth',
            'mytyoerth': 'my date of birth', 'mydateaverg': 'my date of birth',
        }
    
    def _save_vocabulary(self):
        """Save vocabulary to file."""
        try:
            with open(self.vocabulary_file, 'w', encoding='utf-8') as f:
                json.dump(self.custom_vocabulary, f, indent=2, ensure_ascii=False)
            print(f"[STT-ENHANCER] Saved {len(self.custom_vocabulary)} vocabulary words")
        except Exception as e:
            print(f"[STT-ENHANCER] Error saving vocabulary: {e}")
    
    # ============================================================
    # FIX 4: ACCENT DRIFT ADAPTATION
    # ============================================================
    
    def detect_accent_drift(self, recent_transcriptions: List[Tuple[str, str]]) -> Dict:
        """
        Detect if accent has drifted from training data.
        
        Args:
            recent_transcriptions: List of (expected, actual) transcription pairs
            
        Returns:
            Drift analysis with recommendations
        """
        if len(recent_transcriptions) < 20:
            return {"drift_detected": False, "message": "Insufficient data"}
        
        # Calculate error rate
        total_words = 0
        error_words = 0
        error_patterns = {}
        
        for expected, actual in recent_transcriptions:
            exp_words = expected.lower().split()
            act_words = actual.lower().split()
            
            total_words += len(exp_words)
            
            # Simple word-level comparison
            for i, (exp, act) in enumerate(zip(exp_words, act_words)):
                if exp != act:
                    error_words += 1
                    # Track error pattern
                    pattern = f"{exp}→{act}"
                    error_patterns[pattern] = error_patterns.get(pattern, 0) + 1
        
        error_rate = error_words / total_words if total_words > 0 else 0
        
        # Check against baseline
        baseline_error = self.accent_profile.get("baseline_error_rate", 0.05)
        drift_amount = error_rate - baseline_error
        
        drift_detected = drift_amount > self.accent_drift_threshold
        
        analysis = {
            "drift_detected": drift_detected,
            "current_error_rate": round(error_rate, 3),
            "baseline_error_rate": round(baseline_error, 3),
            "drift_amount": round(drift_amount, 3),
            "total_samples": len(recent_transcriptions),
            "common_errors": sorted(error_patterns.items(), key=lambda x: x[1], reverse=True)[:10],
            "recommendation": ""
        }
        
        if drift_detected:
            analysis["recommendation"] = (
                f"Accent drift detected! Error rate increased by {drift_amount*100:.1f}%. "
                f"Recommend recording 100-200 new samples and retraining model."
            )
            print(f"[STT-ENHANCER] ⚠️ {analysis['recommendation']}")
        else:
            analysis["recommendation"] = "Accent profile stable. No retraining needed."
        
        # Update accent profile
        self.accent_profile["last_check"] = time.strftime("%Y-%m-%d %H:%M:%S")
        self.accent_profile["recent_error_rate"] = error_rate
        self._save_accent_profile()
        
        return analysis
    
    def _load_accent_profile(self) -> Dict:
        """Load accent profile from file."""
        if self.accent_profile_file.exists():
            try:
                with open(self.accent_profile_file, 'r', encoding='utf-8') as f:
                    profile = json.load(f)
                print(f"[STT-ENHANCER] Loaded accent profile (baseline WER: {profile.get('baseline_error_rate', 0)*100:.1f}%)")
                return profile
            except Exception as e:
                print(f"[STT-ENHANCER] Error loading accent profile: {e}")
        
        # Default profile
        return {
            "baseline_error_rate": 0.05,  # 5% WER baseline
            "created": time.strftime("%Y-%m-%d %H:%M:%S"),
            "last_check": None,
            "recent_error_rate": 0.05
        }
    
    def _save_accent_profile(self):
        """Save accent profile to file."""
        try:
            with open(self.accent_profile_file, 'w', encoding='utf-8') as f:
                json.dump(self.accent_profile, f, indent=2)
        except Exception as e:
            print(f"[STT-ENHANCER] Error saving accent profile: {e}")
    
    # ============================================================
    # INTEGRATED PROCESSING PIPELINE
    # ============================================================
    
    def enhance_audio_for_stt(self, audio: np.ndarray) -> np.ndarray:
        """
        Complete audio enhancement pipeline for STT.
        Applies all fixes in optimal order.
        
        Args:
            audio: Raw audio input (numpy array, float32, mono)
            
        Returns:
            Enhanced audio ready for STT
        """
        # Fix 1: Reduce background noise
        if self.noise_reduction_enabled:
            audio = self.reduce_background_noise(audio)
        
        # Fix 2: Normalize speaking speed (requires torch tensor)
        if self.speed_normalization_enabled:
            audio_tensor = torch.from_numpy(audio).float()
            audio_tensor = self.normalize_speaking_speed(audio_tensor)
            audio = audio_tensor.numpy()
        
        return audio
    
    def enhance_transcription(self, raw_transcription: str) -> str:
        """
        Post-process transcription with vocabulary corrections.
        
        Args:
            raw_transcription: Raw STT output
            
        Returns:
            Enhanced transcription
        """
        # Fix incorrectly SPLIT words first (e.g., "syc ology" -> "psychology")
        merged = self._fix_split_words(raw_transcription)
        
        # Fix word segmentation (split joined words)
        segmented = self._fix_word_segmentation(merged)
        
        # Fix 3: Apply vocabulary corrections
        corrected = self.correct_with_vocabulary(segmented)
        
        return corrected
    
    def _fix_split_words(self, text: str) -> str:
        """
        Fix words that are incorrectly split by CTC decoding.
        E.g., "syc ology" -> "psychology", "psy chology" -> "psychology"
        """
        if not text:
            return text
        
        # Common words that get incorrectly split by CTC
        split_word_fixes = {
            # Psychology variations
            'syc ology': 'psychology',
            'psy chology': 'psychology',
            'psych ology': 'psychology',
            'psycho logy': 'psychology',
            'psychol ogy': 'psychology',
            'sych ology': 'psychology',
            'sy chology': 'psychology',
            'p sychology': 'psychology',
            'ps ychology': 'psychology',
            # Initialize variations
            'initial ize': 'initialize',
            'initia lize': 'initialize',
            'init ialize': 'initialize',
            'in itialize': 'initialize',
            'ini tialize': 'initialize',
            # Monica variations
            'mon ica': 'monica',
            'moni ca': 'monica',
            'mo nica': 'monica',
            # Christopher variations
            'chris topher': 'christopher',
            'christo pher': 'christopher',
            'christ opher': 'christopher',
            # Columbus variations
            'colum bus': 'columbus',
            'col umbus': 'columbus',
            'colu mbus': 'columbus',
            # Common words
            'to day': 'today',
            'to morrow': 'tomorrow',
            'yester day': 'yesterday',
            'some thing': 'something',
            'any thing': 'anything',
            'every thing': 'everything',
            'no thing': 'nothing',
            'some one': 'someone',
            'any one': 'anyone',
            'every one': 'everyone',
            'no one': 'no one',  # This one is actually correct
            'be cause': 'because',
            'al though': 'although',
            'how ever': 'however',
            'there fore': 'therefore',
            'mean while': 'meanwhile',
            'under stand': 'understand',
            'with out': 'without',
            'in to': 'into',
            'on to': 'onto',
            # Technical terms
            'com puter': 'computer',
            'pro gram': 'program',
            'soft ware': 'software',
            'hard ware': 'hardware',
            'inter net': 'internet',
            'web site': 'website',
            # More psychology-related
            'clin ical': 'clinical',
            'clini cal': 'clinical',
            'thera py': 'therapy',
            'ther apy': 'therapy',
            'coun seling': 'counseling',
            'counsel ing': 'counseling',
        }
        
        result = text.lower()
        
        for wrong, right in split_word_fixes.items():
            if wrong in result:
                result = result.replace(wrong, right)
                print(f"[STT-ENHANCER] Merged split word: '{wrong}' → '{right}'")
        
        return result

    def _fix_word_segmentation(self, text: str) -> str:
        """
        Fix words that are joined together without spaces.
        Uses a dictionary of common words to find split points.
        """
        if not text:
            return text
        
        # Common words to look for when splitting (ordered by priority)
        common_words = [
            'monica', 'initialize', 'what', 'who', 'when', 'where', 'why', 'how',
            'today', 'yesterday', 'tomorrow', 'about', 'the', 'you', 'your',
            'created', 'tell', 'show', 'help', 'can', 'could', 'would', 'should',
            'is', 'are', 'was', 'were', 'have', 'has', 'had', 'do', 'does', 'did',
            'say', 'said', 'mean', 'meant', 'talk', 'let', 'lets', 'clinical',
            'psychology', 'that', 'this', 'with', 'from', 'into', 'onto',
            'me', 'my', 'mine', 'him', 'his', 'her', 'hers', 'them', 'their',
            'yourself', 'myself', 'herself', 'himself', 'ourselves',
            'one', 'two', 'three', 'four', 'five', 'last', 'first', 'next',
            'statement', 'question', 'answer', 'used', 'which', 'meant',
        ]
        
        # Phrase corrections for common misrecognitions
        phrase_fixes = {
            'clinigasyclosy': 'clinical psychology',
            'clinicalclicity': 'clinical psychology', 
            'clicty': 'psychology',
            'cycllicity': 'psychology',
            'cyclicity': 'psychology',
            'onica': 'monica',
            # Date/time related fixes
            'sdate': "s date",
            'todaysdate': "today's date",
            'todaydate': "today date",
            'whattoday': 'what today',
            "what today sdate": "what is today's date",
            "what today date": "what is today's date",
            "whats today": "what is today",
            "whats the date": "what is the date",
            "whats the time": "what is the time",
            "whatistoday": "what is today",
            "whatistodaysdate": "what is today's date",
            # Common word joining fixes
            'whocreated': 'who created',
            'createdyou': 'created you',
            'talkabout': 'talk about',
            'tellme': 'tell me',
            'showme': 'show me',
            'helpme': 'help me',
            'doyou': 'do you',
            'areyou': 'are you',
            'canyou': 'can you',
            'wouldyou': 'would you',
            'couldyou': 'could you',
            'whatdo': 'what do',
            'whatdoes': 'what does',
            'whatdid': 'what did',
            'whatwas': 'what was',
            'whatis': 'what is',
            'whowas': 'who was',
            'whois': 'who is',
            'howdo': 'how do',
            'howdoes': 'how does',
            'howcan': 'how can',
            'letme': 'let me',
            'letstalk': 'lets talk',
            'letstalkabout': 'lets talk about',
            'noyou': 'no you',
            'yousaid': 'you said',
            'yoused': 'you said',
            'youdid': 'you did',
            'youwere': 'you were',
            'imeant': 'i meant',
            'whatimeant': 'what i meant',
            'laststatement': 'last statement',
            'fourstatements': 'four statements',
            'inour': 'in our',
            'infour': 'in four',
            # Birth/date related fixes (user reported issues)
            'mydateofearth': 'my date of birth',
            'dateofearth': 'date of birth',
            'dateofbirth': 'date of birth',
            'mydateofbirth': 'my date of birth',
            'ismy': 'is my',
            'whatismy': 'what is my',
            'iwasborn': 'i was born',
            'wheniwasborn': 'when i was born',
            'tdateof': 'the date of',
            'noimean': 'no i mean',
            'noi': 'no i',
            # Witches/exist fixes
            'dowhichesexist': 'do witches exist',
            'whichesexist': 'witches exist',
            'dowitchesexist': 'do witches exist',
            'witchesexist': 'witches exist',
            # More common joins
            'imean': 'i mean',
            'youmean': 'you mean',
            'whatdoyoumean': 'what do you mean',
            'thatmeans': 'that means',
            'thismeans': 'this means',
        }
        
        result = text.lower()
        
        # Apply phrase fixes first
        for wrong, right in phrase_fixes.items():
            if wrong in result:
                result = result.replace(wrong, right)
                print(f"[STT-ENHANCER] Segmentation fix: '{wrong}' → '{right}'")
        
        # Now try to split remaining joined words
        words = result.split()
        fixed_words = []
        
        for word in words:
            if len(word) <= 6:  # Short words probably ok
                fixed_words.append(word)
                continue
            
            # Try to find split points
            split_found = False
            for common in common_words:
                if len(common) < 3:
                    continue
                # Check if word starts with common word
                if word.startswith(common) and len(word) > len(common) + 1:
                    remainder = word[len(common):]
                    if len(remainder) >= 2:
                        fixed_words.append(common)
                        fixed_words.append(remainder)
                        print(f"[STT-ENHANCER] Split: '{word}' → '{common} {remainder}'")
                        split_found = True
                        break
                # Check if word ends with common word
                if word.endswith(common) and len(word) > len(common) + 1:
                    prefix = word[:-len(common)]
                    if len(prefix) >= 2:
                        fixed_words.append(prefix)
                        fixed_words.append(common)
                        print(f"[STT-ENHANCER] Split: '{word}' → '{prefix} {common}'")
                        split_found = True
                        break
            
            if not split_found:
                fixed_words.append(word)
        
        return ' '.join(fixed_words)


# Global instance
_stt_enhancer = None

def get_stt_enhancer(sample_rate: int = 16000, model_dir: Path = None):
    """Get or create STT accuracy enhancer."""
    global _stt_enhancer
    if _stt_enhancer is None:
        _stt_enhancer = STTAccuracyEnhancer(sample_rate, model_dir)
        print("[STT-ENHANCER] Global instance created")
    return _stt_enhancer
