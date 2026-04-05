"""
Speech Enhancement Module for Monica AI
Improves both speech recognition (STT) and text-to-speech (TTS)
"""
import numpy as np
import re
from typing import Optional, Tuple
import scipy.signal
import noisereduce as nr

class SpeechEnhancer:
    """Enhance speech recognition and synthesis quality."""
    
    def __init__(self, sample_rate: int = 16000):
        """Initialize speech enhancer."""
        self.sample_rate = sample_rate
        
    def preprocess_audio_for_recognition(self, audio_data: np.ndarray) -> np.ndarray:
        """
        Preprocess audio before sending to Whisper for better recognition.
        """
        # 1. Noise reduction
        audio_data = self._reduce_noise(audio_data)
        
        # 2. Normalize volume
        audio_data = self._normalize_audio(audio_data)
        
        # 3. Apply bandpass filter (human speech range: 80-8000 Hz)
        audio_data = self._apply_bandpass_filter(audio_data)
        
        # 4. Remove silence and trim
        audio_data = self._trim_silence(audio_data)
        
        # 5. Apply pre-emphasis to boost high frequencies
        audio_data = self._pre_emphasis(audio_data)
        
        return audio_data
    
    def _reduce_noise(self, audio_data: np.ndarray) -> np.ndarray:
        """Reduce background noise using spectral gating."""
        try:
            # Use noisereduce library if available
            return nr.reduce_noise(y=audio_data, sr=self.sample_rate)
        except:
            # Fallback to simple noise gate
            threshold = np.percentile(np.abs(audio_data), 10)
            audio_data[np.abs(audio_data) < threshold] *= 0.1
            return audio_data
    
    def _normalize_audio(self, audio_data: np.ndarray) -> np.ndarray:
        """Normalize audio to optimal volume level."""
        # Find peak
        peak = np.max(np.abs(audio_data))
        if peak > 0:
            # Normalize to 70% of max to avoid clipping
            audio_data = audio_data * (0.7 / peak)
        return audio_data
    
    def _apply_bandpass_filter(self, audio: np.ndarray) -> np.ndarray:
        """Apply bandpass filter to focus on speech frequencies."""
        from scipy import signal
        
        # Human speech is typically 80-8000 Hz
        # But need to normalize for Nyquist frequency
        nyquist = self.sample_rate / 2
        lowcut = 80 / nyquist
        highcut = min(8000, nyquist * 0.99) / nyquist  # Ensure < 1
        
        # Validate frequencies
        if lowcut >= 1 or highcut >= 1 or lowcut <= 0 or highcut <= 0:
            print(f"[ENHANCER] Invalid filter frequencies, skipping bandpass")
            return audio
        
        # Create butterworth bandpass filter
        try:
            sos = signal.butter(
                4,  # 4th order filter
                [lowcut, highcut],
                btype='band',
                output='sos'
            )
        except Exception as e:
            print(f"[ENHANCER] Filter creation failed: {e}")
            return audio
        
        # Apply filter
        return signal.sosfilt(sos, audio)
    
    def _trim_silence(self, audio_data: np.ndarray, threshold: float = 0.01) -> np.ndarray:
        """Remove silence from beginning and end."""
        # Find first non-silent sample
        energy = np.abs(audio_data)
        indices = np.where(energy > threshold)[0]
        
        if len(indices) > 0:
            return audio_data[indices[0]:indices[-1] + 1]
        return audio_data
    
    def _pre_emphasis(self, audio_data: np.ndarray, coefficient: float = 0.97) -> np.ndarray:
        """Apply pre-emphasis filter to boost high frequencies."""
        return np.append(audio_data[0], audio_data[1:] - coefficient * audio_data[:-1])
    
    def create_whisper_prompt(self, context: str = "") -> str:
        """
        Create an optimized initial prompt for Whisper to improve accuracy.
        Research shows specific prompts help with:
        - Common names and words
        - Technical vocabulary
        - Consistent capitalization
        """
        # Base vocabulary that helps Whisper
        base_prompt = "Monica, MJP, AI, assistant, hello, yes, no, please, thank you"
        
        # Add context-specific words
        if context:
            # Extract likely important words from context
            important_words = self._extract_important_words(context)
            if important_words:
                base_prompt += ", " + ", ".join(important_words)
        
        return base_prompt
    
    def _extract_important_words(self, text: str) -> list:
        """Extract important words from context for prompt."""
        # Focus on proper nouns and technical terms
        words = []
        
        # Find capitalized words (likely names/proper nouns)
        capitalized = re.findall(r'\b[A-Z][a-z]+\b', text)
        words.extend(capitalized[:5])  # Limit to 5
        
        # Common technical terms in conversation
        tech_terms = ["computer", "program", "code", "python", "javascript", "database"]
        for term in tech_terms:
            if term in text.lower():
                words.append(term)
        
        return list(set(words))[:10]  # Unique words, max 10

class TTSTextProcessor:
    """Process text for better TTS output."""
    
    @staticmethod
    def fix_text_for_speech(text: str) -> str:
        """
        Minimal text processing for TTS - avoid breaking word spacing.
        """
        # Only do essential cleanup
        text = text.strip()
        
        # Remove multiple spaces
        text = re.sub(r'\s+', ' ', text)
        
        # Ensure space after sentence endings
        text = re.sub(r'([.!?])([A-Za-z])', r'\1 \2', text)
        
        # Clean up
        text = text.strip()
        
        print(f"[TTS PROCESSOR] Text: '{text}'")
        
        return text
    
    @staticmethod
    def add_speech_markers(text: str) -> str:
        """
        Add SSML-like markers for better speech rhythm.
        """
        # Add brief pauses
        text = text.replace(', ', ', <pause> ')
        text = text.replace('. ', '. <pause> ')
        text = text.replace('? ', '? <pause> ')
        text = text.replace('! ', '! <pause> ')
        
        return text

# Global instance
_speech_enhancer = None

def get_speech_enhancer(sample_rate: int = 16000):
    """Get or create speech enhancer."""
    global _speech_enhancer
    if _speech_enhancer is None:
        _speech_enhancer = SpeechEnhancer(sample_rate)
    return _speech_enhancer
