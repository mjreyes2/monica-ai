"""
NeMo Text Processing Bridge for Monica AI TTS.

This module provides access to NVIDIA's NeMo Text Processing library
which uses grammar-based finite-state transducers for accurate text normalization.

Since NeMo requires pynini (which only works in conda environments on Windows),
this module uses subprocess to call the conda Python interpreter.

Features:
- Grammar-based text normalization (more accurate than regex)
- Handles numbers, dates, times, currency, ordinals, etc.
- Multi-language support (English, Spanish, German, French, etc.)
- Inverse text normalization (spoken → written)
"""

import subprocess
import sys
import os
import json
from typing import Optional, Dict, List
from pathlib import Path

# Path to conda Python with NeMo installed - search common locations
def _find_conda_python() -> Optional[Path]:
    """Search for conda Python in common Windows locations."""
    candidates = [
        Path(os.path.expanduser("~")) / "miniconda3" / "python.exe",
        Path(os.path.expanduser("~")) / "anaconda3" / "python.exe",
        Path(os.path.expanduser("~")) / "Miniconda3" / "python.exe",
        Path(os.path.expanduser("~")) / "Anaconda3" / "python.exe",
        Path(r"C:\ProgramData\miniconda3\python.exe"),
        Path(r"C:\ProgramData\Anaconda3\python.exe"),
        Path(os.path.expanduser("~")) / "AppData" / "Local" / "miniconda3" / "python.exe",
        Path(os.path.expanduser("~")) / "AppData" / "Local" / "anaconda3" / "python.exe",
    ]
    for p in candidates:
        if p.exists():
            return p
    return None

CONDA_PYTHON = _find_conda_python()


def _verbose_nemo_startup() -> bool:
    return os.environ.get("MONICA_VERBOSE_STARTUP", "0") == "1"

# Cache for normalized text to avoid repeated subprocess calls
_cache: Dict[str, str] = {}
_cache_max_size = 1000


class NeMoNormalizer:
    """
    Text normalizer using NVIDIA NeMo Text Processing.
    
    Uses subprocess to call conda Python where pynini is available.
    Provides caching to minimize subprocess overhead.
    """
    
    SUPPORTED_LANGUAGES = ['en', 'es', 'de', 'fr', 'ru', 'vi', 'ar', 'zh']
    
    def __init__(self, language: str = 'en', input_case: str = 'cased'):
        """
        Initialize the NeMo normalizer.
        
        Args:
            language: Language code ('en', 'es', 'de', 'fr', etc.)
            input_case: 'cased' or 'lower_cased'
        """
        self.language = language
        self.input_case = input_case
        self._available = None
    
    def is_available(self) -> bool:
        """Check if NeMo Text Processing is available."""
        if self._available is None:
            self._available = self._check_availability()
        return self._available
    
    def _check_availability(self) -> bool:
        """Check if conda Python and NeMo are available."""
        if CONDA_PYTHON is None or not CONDA_PYTHON.exists():
            return False
        
        try:
            result = subprocess.run(
                [str(CONDA_PYTHON), "-c", "import nemo_text_processing; print('ok')"],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0 and 'ok' in result.stdout:
                if _verbose_nemo_startup():
                    print("[NEMO] NeMo Text Processing available")
                return True
            else:
                if _verbose_nemo_startup():
                    print("[NEMO] NeMo import failed:", result.stderr[:200])
                return False
        except Exception as e:
            if _verbose_nemo_startup():
                print(f"[NEMO] Availability check failed: {e}")
            return False
    
    def normalize(self, text: str) -> str:
        """
        Normalize text using NeMo Text Processing.
        
        Converts:
        - Numbers: "25" → "twenty five"
        - Currency: "$5.99" → "five dollars and ninety nine cents"
        - Dates: "December 7th, 2025" → "december seventh, twenty twenty five"
        - Times: "3:30 PM" → "three thirty p m"
        - Ordinals: "1st" → "first"
        
        Args:
            text: Raw text to normalize
            
        Returns:
            Normalized text suitable for TTS
        """
        if not text or not text.strip():
            return text
        
        # Check cache first
        cache_key = f"{self.language}:{self.input_case}:{text}"
        if cache_key in _cache:
            return _cache[cache_key]
        
        # Check availability
        if not self.is_available():
            return text  # Return unchanged if NeMo not available
        
        try:
            # Call NeMo via subprocess
            normalized = self._call_nemo(text)
            
            # Cache the result
            if len(_cache) >= _cache_max_size:
                # Remove oldest entries (simple FIFO)
                keys_to_remove = list(_cache.keys())[:_cache_max_size // 2]
                for key in keys_to_remove:
                    del _cache[key]
            _cache[cache_key] = normalized
            
            return normalized
            
        except Exception as e:
            print(f"[NEMO] Normalization error: {e}")
            return text
    
    def _call_nemo(self, text: str) -> str:
        """Call NeMo normalizer via subprocess."""
        # Escape the text for command line
        escaped_text = text.replace('\\', '\\\\').replace('"', '\\"').replace("'", "\\'")
        
        script = (
            "import sys\n"
            "sys.stdout.reconfigure(encoding='utf-8')\n"
            "from nemo_text_processing.text_normalization.normalize import Normalizer\n"
            f"n = Normalizer(input_case='{self.input_case}', lang='{self.language}')\n"
            f'result = n.normalize("{escaped_text}")\n'
            "print(result)\n"
        )
        
        result = subprocess.run(
            [str(CONDA_PYTHON), "-c", script],
            capture_output=True,
            text=True,
            timeout=5,  # Reduced from 30s to 5s - NeMo should be fast
            encoding='utf-8',
            errors='replace'
        )
        
        if result.returncode == 0:
            # Get the last line (the actual result)
            lines = result.stdout.strip().split('\n')
            return lines[-1] if lines else text
        else:
            print(f"[NEMO] Subprocess error: {result.stderr[:200]}")
            return text
    
    def normalize_batch(self, texts: List[str]) -> List[str]:
        """
        Normalize multiple texts in a single subprocess call.
        
        More efficient for batch processing.
        
        Args:
            texts: List of texts to normalize
            
        Returns:
            List of normalized texts
        """
        if not texts:
            return texts
        
        if not self.is_available():
            return texts
        
        try:
            # Prepare batch script
            texts_json = json.dumps(texts)
            escaped_json = texts_json.replace("'", "\\'")
            
            script = (
                "import sys\n"
                "import json\n"
                "sys.stdout.reconfigure(encoding='utf-8')\n"
                "from nemo_text_processing.text_normalization.normalize import Normalizer\n"
                f"n = Normalizer(input_case='{self.input_case}', lang='{self.language}')\n"
                f"texts = json.loads('{escaped_json}')\n"
                "results = [n.normalize(t) for t in texts]\n"
                "print(json.dumps(results))\n"
            )
            
            result = subprocess.run(
                [str(CONDA_PYTHON), "-c", script],
                capture_output=True,
                text=True,
                timeout=60,
                encoding='utf-8',
                errors='replace'
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                return json.loads(lines[-1])
            else:
                return texts
                
        except Exception as e:
            print(f"[NEMO] Batch normalization error: {e}")
            return texts


# Singleton instance
_normalizer: Optional[NeMoNormalizer] = None


def get_nemo_normalizer(language: str = 'en') -> NeMoNormalizer:
    """Get or create the NeMo normalizer."""
    global _normalizer
    if _normalizer is None or _normalizer.language != language:
        _normalizer = NeMoNormalizer(language=language)
    return _normalizer


def nemo_normalize(text: str, language: str = 'en') -> str:
    """
    Convenience function to normalize text using NeMo.
    
    Args:
        text: Text to normalize
        language: Language code
        
    Returns:
        Normalized text
    """
    return get_nemo_normalizer(language).normalize(text)


def is_nemo_available() -> bool:
    """Check if NeMo Text Processing is available."""
    return get_nemo_normalizer().is_available()


# Test function
def test_nemo_normalizer():
    """Test the NeMo normalizer."""
    print("=" * 60)
    print("NEMO TEXT PROCESSING TEST")
    print("=" * 60)
    
    normalizer = NeMoNormalizer()
    
    if not normalizer.is_available():
        print("NeMo Text Processing is NOT available")
        return
    
    test_cases = [
        "I have $5.99 and 25 apples",
        "The meeting is on December 7th, 2025 at 3:30 PM",
        "Call me at 555-123-4567",
        "She finished 1st in the race",
        "The temperature is 72°F",
        "I need 2.5 kg of flour",
    ]
    
    for text in test_cases:
        normalized = normalizer.normalize(text)
        print(f"\nOriginal:   {text}")
        print(f"Normalized: {normalized}")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    test_nemo_normalizer()
