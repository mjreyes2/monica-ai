"""
Monica Study Assistant
Helps users study by:
- Reading screen content (OCR)
- Following along as user reads aloud
- Checking pronunciation
- Answering questions about the material
- Providing explanations and context

Author: Monica AI
Date: December 2025
"""

import cv2
import numpy as np
import threading
import time
import re
from typing import Optional, Dict, List, Tuple, Any
from dataclasses import dataclass, field
from pathlib import Path
from difflib import SequenceMatcher
import mss
import mss.tools

# OCR Libraries - try multiple options
HAS_TESSERACT = False
HAS_EASYOCR = False
HAS_WINDOWS_OCR = False

# Try Windows OCR first (built-in, no install needed)
try:
    import asyncio
    import ctypes
    # Check if Windows OCR is available
    HAS_WINDOWS_OCR = True
    print("[OK] Windows OCR available")
except Exception as e:
    print(f"[WARNING] Windows OCR not available: {e}")

# EasyOCR - LAZY LOAD (it's very heavy, loads neural networks)
# Will be imported on first use instead of at startup
HAS_EASYOCR = True  # Assume available, will check on first use
_easyocr_module = None

# Try Tesseract (direct subprocess call - avoids numpy issues)
TESSERACT_PATH = None
tesseract_paths = [
    r'C:\Program Files\Tesseract-OCR\tesseract.exe',
    r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
]

for path in tesseract_paths:
    if Path(path).exists():
        TESSERACT_PATH = path
        HAS_TESSERACT = True
        print(f"[OK] Tesseract OCR found at {path}")
        break

if not HAS_TESSERACT:
    import shutil
    tesseract_path = shutil.which('tesseract')
    if tesseract_path:
        TESSERACT_PATH = tesseract_path
        HAS_TESSERACT = True
        print("[OK] Tesseract OCR found in PATH")

# For pronunciation comparison
HAS_JELLYFISH = False
try:
    import jellyfish
    HAS_JELLYFISH = True
    print("[OK] Jellyfish loaded for phonetic comparison")
except ImportError:
    pass


@dataclass
class ScreenRegion:
    """Represents a region of the screen."""
    x: int
    y: int
    width: int
    height: int
    name: str = "Screen"


@dataclass
class ReadingSession:
    """Tracks a reading/study session."""
    start_time: float = field(default_factory=time.time)
    screen_text: str = ""
    words_read: List[str] = field(default_factory=list)
    current_position: int = 0
    mispronounced_words: List[Tuple[str, str]] = field(default_factory=list)  # (expected, spoken)
    questions_asked: List[str] = field(default_factory=list)
    topics_covered: List[str] = field(default_factory=list)
    

class ScreenReader:
    """
    Captures and reads text from the screen using OCR.
    """
    
    def __init__(self):
        self.sct = mss.mss()
        self.easyocr_reader = None
        self.last_capture = None
        self.last_text = ""
        self.capture_lock = threading.Lock()
        
        # Initialize EasyOCR (lazy load - it's heavy)
        self._easyocr_initialized = False
        
    def _init_easyocr(self):
        """Lazy initialize EasyOCR - only when actually needed."""
        global _easyocr_module, HAS_EASYOCR
        
        if not self._easyocr_initialized and HAS_EASYOCR:
            try:
                # Lazy import - only load when needed
                if _easyocr_module is None:
                    print("[STUDY] Loading EasyOCR (first use)...")
                    import easyocr as _easyocr_module
                
                self.easyocr_reader = _easyocr_module.Reader(['en'], gpu=True)
                self._easyocr_initialized = True
                print("[STUDY] EasyOCR initialized with GPU")
            except Exception as e:
                try:
                    if _easyocr_module is None:
                        import easyocr as _easyocr_module
                    self.easyocr_reader = _easyocr_module.Reader(['en'], gpu=False)
                    self._easyocr_initialized = True
                    print("[STUDY] EasyOCR initialized (CPU mode)")
                except Exception as e2:
                    print(f"[STUDY] EasyOCR not available: {e2}")
                    HAS_EASYOCR = False
    
    def capture_screen(self, region: ScreenRegion = None) -> np.ndarray:
        """Capture the screen or a specific region."""
        with self.capture_lock:
            if region:
                monitor = {
                    "left": region.x,
                    "top": region.y,
                    "width": region.width,
                    "height": region.height
                }
            else:
                # Capture primary monitor
                monitor = self.sct.monitors[1]
            
            screenshot = self.sct.grab(monitor)
            frame = np.array(screenshot)
            # Convert BGRA to BGR
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            self.last_capture = frame
            return frame
    
    def capture_active_window(self) -> Tuple[np.ndarray, str]:
        """Capture the currently active window."""
        try:
            import win32gui
            import win32ui
            import win32con
            import win32api
            
            # Get active window
            hwnd = win32gui.GetForegroundWindow()
            window_title = win32gui.GetWindowText(hwnd)
            
            # Get window dimensions
            left, top, right, bottom = win32gui.GetWindowRect(hwnd)
            width = right - left
            height = bottom - top
            
            # Capture using mss (more reliable)
            region = ScreenRegion(left, top, width, height, window_title)
            frame = self.capture_screen(region)
            
            return frame, window_title
            
        except ImportError:
            print("[STUDY] win32gui not available, capturing full screen")
            return self.capture_screen(), "Full Screen"
        except Exception as e:
            print(f"[STUDY] Window capture error: {e}")
            return self.capture_screen(), "Full Screen"
    
    def read_text_from_image(self, image: np.ndarray, use_easyocr: bool = True) -> str:
        """
        Extract text from an image using OCR.
        
        Args:
            image: BGR image
            use_easyocr: Use EasyOCR if available
        """
        if image is None:
            return ""
        
        # Preprocess image for better OCR
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Increase contrast
        gray = cv2.convertScaleAbs(gray, alpha=1.5, beta=0)
        
        text = ""
        
        # Try EasyOCR first
        if HAS_EASYOCR and use_easyocr:
            self._init_easyocr()
            if self.easyocr_reader:
                try:
                    results = self.easyocr_reader.readtext(gray, detail=0, paragraph=True)
                    text = " ".join(results) if results else ""
                    if text:
                        print(f"[STUDY] EasyOCR found {len(text)} chars")
                except Exception as e:
                    print(f"[STUDY] EasyOCR error: {e}")
        
        # Fallback to Tesseract if available (using subprocess to avoid numpy issues)
        if not text and HAS_TESSERACT and TESSERACT_PATH:
            try:
                import subprocess
                import tempfile
                
                # Save image to temp file
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                    tmp_path = tmp.name
                    cv2.imwrite(tmp_path, gray)
                
                # Run tesseract with UTF-8 encoding
                result = subprocess.run(
                    [TESSERACT_PATH, tmp_path, 'stdout', '-l', 'eng', '--psm', '6'],
                    capture_output=True,
                    timeout=30,
                    encoding='utf-8',
                    errors='ignore'
                )
                
                text = result.stdout.strip() if result.stdout else ""
                
                # Cleanup temp file
                try:
                    Path(tmp_path).unlink()
                except:
                    pass
                
                if text:
                    print(f"[STUDY] Tesseract found {len(text)} chars")
            except subprocess.TimeoutExpired:
                print("[STUDY] Tesseract timeout")
            except Exception as e:
                print(f"[STUDY] Tesseract error: {e}")
        
        # If no OCR worked, try to save image for manual inspection
        if not text:
            # Save screenshot for user to see what was captured
            try:
                timestamp = int(time.time())
                debug_path = Path(__file__).parent.parent.parent / "data" / f"screen_capture_{timestamp}.png"
                debug_path.parent.mkdir(exist_ok=True)
                cv2.imwrite(str(debug_path), image)
                print(f"[STUDY] Screen saved to: {debug_path}")
                return f"[Screen captured but OCR unavailable. Screenshot saved. To enable OCR, install Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki]"
            except Exception as e:
                print(f"[STUDY] Could not save screenshot: {e}")
                return "[OCR not available - please install Tesseract OCR]"
        
        self.last_text = text.strip()
        return self.last_text
    
    def get_text_regions(self, image: np.ndarray) -> List[Dict]:
        """Get text regions with bounding boxes."""
        if not HAS_TESSERACT:
            return []
        
        try:
            try:
                import pytesseract
            except Exception:
                return []

            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            data = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DICT)
            
            regions = []
            for i, text in enumerate(data['text']):
                if text.strip():
                    regions.append({
                        'text': text,
                        'x': data['left'][i],
                        'y': data['top'][i],
                        'width': data['width'][i],
                        'height': data['height'][i],
                        'confidence': data['conf'][i]
                    })
            return regions
        except Exception as e:
            print(f"[STUDY] Text regions error: {e}")
            return []


# Import the enhanced pronunciation assessor
try:
    from .pronunciation_assessor import get_pronunciation_assessor, PronunciationAssessor
    HAS_PRONUNCIATION_ASSESSOR = True
except ImportError:
    HAS_PRONUNCIATION_ASSESSOR = False


class PronunciationChecker:
    """
    Checks pronunciation by comparing spoken words to expected text.
    Uses the enhanced PronunciationAssessor when available.
    """
    
    def __init__(self):
        self.phoneme_cache = {}
        self.assessor = None
        if HAS_PRONUNCIATION_ASSESSOR:
            try:
                self.assessor = get_pronunciation_assessor()
                print("[STUDY] Enhanced pronunciation assessor connected")
            except Exception as e:
                print(f"[STUDY] Pronunciation assessor error: {e}")
        
    def get_phonemes(self, word: str) -> str:
        """Get phonetic representation of a word."""
        word = word.lower().strip()
        
        if word in self.phoneme_cache:
            return self.phoneme_cache[word]
        
        # Use assessor if available
        if self.assessor:
            phonemes = self.assessor.get_phonemes(word)
        else:
            phonemes = self._basic_phonetic(word)
        
        self.phoneme_cache[word] = phonemes
        return phonemes
    
    def _basic_phonetic(self, word: str) -> str:
        """Basic phonetic approximation."""
        # Simple syllable breakdown
        vowels = 'aeiou'
        syllables = []
        current = ""
        
        for i, char in enumerate(word.lower()):
            current += char
            if char in vowels and i < len(word) - 1:
                if word[i+1] not in vowels:
                    syllables.append(current)
                    current = ""
        
        if current:
            syllables.append(current)
        
        return "-".join(syllables) if syllables else word
    
    def compare_pronunciation(self, expected: str, spoken: str) -> Tuple[float, str]:
        """
        Compare expected word with what was spoken.
        
        Returns:
            Tuple of (similarity_score, feedback)
        """
        expected = expected.lower().strip()
        spoken = spoken.lower().strip()
        
        # Direct match
        if expected == spoken:
            return 1.0, "Perfect!"
        
        # Use enhanced assessor if available
        if self.assessor:
            result = self.assessor.assess_pronunciation(expected, spoken)
            return result.score, result.feedback
        
        # Fallback: Use phonetic comparison if available
        if HAS_JELLYFISH:
            # Soundex comparison (phonetic)
            expected_soundex = jellyfish.soundex(expected)
            spoken_soundex = jellyfish.soundex(spoken)
            
            if expected_soundex == spoken_soundex:
                return 0.9, "Good pronunciation! The sounds are correct."
            
            # Metaphone comparison (more accurate phonetic)
            expected_meta = jellyfish.metaphone(expected)
            spoken_meta = jellyfish.metaphone(spoken)
            
            if expected_meta == spoken_meta:
                return 0.85, "Close! The pronunciation sounds similar."
        
        # Sequence matching
        ratio = SequenceMatcher(None, expected, spoken).ratio()
        
        if ratio > 0.8:
            return ratio, f"Almost! You said '{spoken}', the word is '{expected}'."
        elif ratio > 0.5:
            return ratio, f"Try again. The word is '{expected}'. You said '{spoken}'."
        else:
            return ratio, f"Let me help. The word '{expected}' is pronounced: {self._get_pronunciation_guide(expected)}"
    
    def _get_pronunciation_guide(self, word: str) -> str:
        """Get a pronunciation guide for a word."""
        # Simple syllable breakdown
        vowels = 'aeiou'
        syllables = []
        current = ""
        
        for i, char in enumerate(word.lower()):
            current += char
            if char in vowels and i < len(word) - 1:
                if word[i+1] not in vowels:
                    syllables.append(current)
                    current = ""
        
        if current:
            syllables.append(current)
        
        return "-".join(syllables) if syllables else word


class StudyAssistant:
    """
    Main study assistant that coordinates screen reading, 
    pronunciation checking, grammar checking, and Q&A.
    """
    
    def __init__(self, ai_manager=None, tts_manager=None):
        self.screen_reader = ScreenReader()
        self.pronunciation_checker = PronunciationChecker()
        self.ai_manager = ai_manager
        self.tts_manager = tts_manager
        
        # Grammar checker with challenge memory
        self.grammar_checker = None
        try:
            from .grammar_checker import get_grammar_checker
            self.grammar_checker = get_grammar_checker()
            print("[STUDY] Grammar checker connected")
        except Exception as e:
            print(f"[STUDY] Grammar checker not available: {e}")
        
        # Literature library (70,000+ free ebooks)
        self.literature_library = None
        try:
            from .literature_library import get_literature_library
            self.literature_library = get_literature_library()
            print(f"[STUDY] Literature library connected ({self.literature_library.get_total_books()} curated books)")
        except Exception as e:
            print(f"[STUDY] Literature library not available: {e}")
        
        # Writing assistant (Grammarly-like features)
        self.writing_assistant = None
        try:
            from .writing_assistant import get_writing_assistant
            self.writing_assistant = get_writing_assistant(ai_manager)
            print("[STUDY] Writing assistant connected")
        except Exception as e:
            print(f"[STUDY] Writing assistant not available: {e}")
        
        # Adobe Creative Suite trainer
        self.adobe_trainer = None
        try:
            from .adobe_trainer import get_adobe_trainer
            self.adobe_trainer = get_adobe_trainer(ai_manager, self.screen_reader)
            print("[STUDY] Adobe trainer connected")
        except Exception as e:
            print(f"[STUDY] Adobe trainer not available: {e}")
        
        # Ebook reader (Maxone Drive D:, OneDrive, etc.)
        self.ebook_reader = None
        try:
            from .ebook_reader import get_ebook_reader
            self.ebook_reader = get_ebook_reader(["D:/", "D:/ebooks", "D:/Books"])
            print(f"[STUDY] Ebook reader connected ({self.ebook_reader.get_stats()['total_books']} books)")
        except Exception as e:
            print(f"[STUDY] Ebook reader not available: {e}")
        
        # Roleplay & Communication Skills Trainer
        self.roleplay_trainer = None
        try:
            from .roleplay_trainer import get_roleplay_trainer
            self.roleplay_trainer = get_roleplay_trainer(ai_manager, tts_manager)
            print("[STUDY] Roleplay trainer connected")
        except Exception as e:
            print(f"[STUDY] Roleplay trainer not available: {e}")
        
        # Current session
        self.session: Optional[ReadingSession] = None
        self.is_active = False
        
        # Screen monitoring
        self.monitor_thread: Optional[threading.Thread] = None
        self.monitor_interval = 2.0  # seconds between screen captures
        
        # Reading tracking
        self.current_text = ""
        self.text_words = []
        self.reading_position = 0
        
        # Study context for AI
        self.study_context = ""
        self.subject = ""
        
        print("[STUDY] Study Assistant initialized")
    
    def start_session(self, subject: str = "General") -> str:
        """Start a new study session."""
        self.session = ReadingSession()
        self.is_active = True
        self.subject = subject
        
        # Start screen monitoring
        self._start_monitoring()
        
        return f"Study session started! I'm now watching your screen and ready to help you study {subject}. Read aloud and I'll follow along."
    
    def end_session(self) -> str:
        """End the current study session."""
        self.is_active = False
        self._stop_monitoring()
        
        if self.session:
            duration = time.time() - self.session.start_time
            minutes = int(duration / 60)
            
            summary = f"Study session ended. Duration: {minutes} minutes. "
            if self.session.words_read:
                summary += f"Words read: {len(self.session.words_read)}. "
            if self.session.mispronounced_words:
                summary += f"Words to practice: {len(self.session.mispronounced_words)}. "
            
            self.session = None
            return summary
        
        return "Study session ended."
    
    def _start_monitoring(self):
        """Start background screen monitoring."""
        if self.monitor_thread and self.monitor_thread.is_alive():
            return
        
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        print("[STUDY] Screen monitoring started")
    
    def _stop_monitoring(self):
        """Stop background screen monitoring."""
        self.is_active = False
        print("[STUDY] Screen monitoring stopped")
    
    def _monitor_loop(self):
        """Background loop to monitor screen content."""
        while self.is_active:
            try:
                # Capture active window
                frame, window_title = self.screen_reader.capture_active_window()
                
                # Read text from screen
                text = self.screen_reader.read_text_from_image(frame)
                
                if text and text != self.current_text:
                    self.current_text = text
                    self.text_words = self._tokenize_text(text)
                    self.study_context = f"Window: {window_title}\n\nContent:\n{text[:2000]}"
                    
                    if self.session:
                        self.session.screen_text = text
                    
                    print(f"[STUDY] Screen updated: {len(self.text_words)} words detected")
                
            except Exception as e:
                print(f"[STUDY] Monitor error: {e}")
            
            time.sleep(self.monitor_interval)
    
    def _tokenize_text(self, text: str) -> List[str]:
        """Tokenize text into words."""
        # Remove special characters but keep apostrophes
        text = re.sub(r"[^\w\s'-]", " ", text)
        words = text.split()
        return [w.strip() for w in words if w.strip()]
    
    def capture_and_read_screen(self) -> str:
        """Capture current screen and read all text."""
        frame, window_title = self.screen_reader.capture_active_window()
        text = self.screen_reader.read_text_from_image(frame)
        
        self.current_text = text
        self.text_words = self._tokenize_text(text)
        self.study_context = f"Window: {window_title}\n\nContent:\n{text[:2000]}"
        
        if text:
            return f"I can see your screen ({window_title}). I found {len(self.text_words)} words. What would you like help with?"
        else:
            return "I couldn't read any text from your screen. Make sure the text is visible and clear."
    
    def process_spoken_text(self, spoken: str) -> Optional[str]:
        """
        Process what the user said - check grammar, pronunciation, and questions.
        
        Returns response if action needed, None otherwise.
        """
        if not self.is_active or not self.session:
            return None
        
        spoken_lower = spoken.lower().strip()
        
        # Check if it's a question
        question_starters = ['what', 'why', 'how', 'when', 'where', 'who', 'which', 
                           'can you', 'could you', 'please explain', 'help me',
                           'what does', 'what is', 'define', 'meaning of']
        
        is_question = any(spoken_lower.startswith(q) for q in question_starters) or '?' in spoken
        
        if is_question:
            self.session.questions_asked.append(spoken)
            return self._answer_question(spoken)
        
        # Check grammar first (for all spoken text)
        grammar_feedback = ""
        if self.grammar_checker and len(spoken.split()) >= 3:  # Only check sentences with 3+ words
            grammar_feedback = self.check_grammar(spoken)
        
        # Check if user is reading - compare with screen text
        reading_feedback = self._check_reading(spoken)
        
        # Combine feedback
        if grammar_feedback and reading_feedback:
            return f"{reading_feedback}\n\nAlso, {grammar_feedback}"
        elif grammar_feedback:
            return grammar_feedback
        elif reading_feedback:
            return reading_feedback
        
        return None
    
    def _check_reading(self, spoken: str) -> Optional[str]:
        """Check if user is reading from screen and verify pronunciation."""
        if not self.text_words:
            return None
        
        spoken_words = self._tokenize_text(spoken)
        
        # Find matching sequence in screen text
        best_match_start = -1
        best_match_score = 0
        
        for i in range(len(self.text_words) - len(spoken_words) + 1):
            screen_segment = self.text_words[i:i + len(spoken_words)]
            
            # Calculate match score
            matches = sum(1 for s, t in zip(spoken_words, screen_segment) 
                         if s.lower() == t.lower())
            score = matches / len(spoken_words) if spoken_words else 0
            
            if score > best_match_score:
                best_match_score = score
                best_match_start = i
        
        # If good match found, check pronunciation
        if best_match_score > 0.5 and best_match_start >= 0:
            screen_segment = self.text_words[best_match_start:best_match_start + len(spoken_words)]
            
            # Check each word
            mispronounced = []
            for spoken_word, expected_word in zip(spoken_words, screen_segment):
                score, feedback = self.pronunciation_checker.compare_pronunciation(
                    expected_word, spoken_word
                )
                
                if score < 0.8:
                    mispronounced.append((expected_word, spoken_word, feedback))
                    if self.session:
                        self.session.mispronounced_words.append((expected_word, spoken_word))
            
            # Update reading position
            self.reading_position = best_match_start + len(spoken_words)
            if self.session:
                self.session.words_read.extend(spoken_words)
            
            # Return feedback if mispronunciations found
            if mispronounced:
                word, spoken, feedback = mispronounced[0]  # Focus on first error
                return feedback
        
        return None
    
    def _answer_question(self, question: str) -> str:
        """Answer a question about the study material."""
        if not self.ai_manager:
            return "I don't have access to the AI system to answer questions."
        
        # Build context-aware prompt
        prompt = f"""You are Monica, a helpful study assistant. The user is studying and has a question.

CURRENT SCREEN CONTENT:
{self.study_context[:3000] if self.study_context else "No screen content available."}

SUBJECT: {self.subject}

USER'S QUESTION: {question}

Please provide a clear, educational answer. If the question relates to the screen content, reference it specifically. Keep your answer concise but thorough."""

        try:
            response = self.ai_manager.get_response(prompt)
            return response
        except Exception as e:
            print(f"[STUDY] AI error: {e}")
            return "I'm having trouble accessing my knowledge base. Could you rephrase your question?"
    
    def explain_word(self, word: str) -> str:
        """Explain a word's meaning and pronunciation."""
        pronunciation = self.pronunciation_checker._get_pronunciation_guide(word)
        
        if self.ai_manager:
            prompt = f"""Define the word "{word}" in a simple, educational way. Include:
1. Definition (1-2 sentences)
2. Example sentence
3. Any related words

Keep it brief and clear for a student."""
            
            try:
                definition = self.ai_manager.get_response(prompt)
                return f"'{word}' (pronounced: {pronunciation})\n\n{definition}"
            except:
                pass
        
        return f"'{word}' is pronounced: {pronunciation}. Ask me to define it if you need the meaning."
    
    def get_pronunciation(self, word: str) -> str:
        """Get pronunciation guide for a word."""
        guide = self.pronunciation_checker._get_pronunciation_guide(word)
        
        # Speak it if TTS available
        if self.tts_manager:
            self.tts_manager.speak(word, block=False)
            return f"The word '{word}' is pronounced: {guide}. Listen to how I say it."
        
        return f"The word '{word}' is pronounced: {guide}"
    
    def summarize_screen(self) -> str:
        """Summarize what's currently on screen."""
        if not self.current_text:
            self.capture_and_read_screen()
        
        if not self.current_text:
            return "I can't see any text on your screen right now."
        
        if self.ai_manager:
            prompt = f"""Summarize this text in 2-3 sentences for a student:

{self.current_text[:2000]}

Focus on the main points and key concepts."""
            
            try:
                return self.ai_manager.get_response(prompt)
            except:
                pass
        
        # Fallback: first few sentences
        sentences = self.current_text.split('.')[:3]
        return "Main points: " + '. '.join(sentences)
    
    def quiz_me(self) -> str:
        """Generate a quiz question based on screen content."""
        if not self.current_text:
            return "I need to see some study material first. Make sure text is visible on your screen."
        
        if self.ai_manager:
            prompt = f"""Based on this study material, create ONE quiz question to test understanding:

{self.current_text[:2000]}

Format:
Question: [your question]
Answer: [brief answer]"""
            
            try:
                return self.ai_manager.get_response(prompt)
            except:
                pass
        
        return "I can see your material but need my AI system to generate questions."
    
    def check_grammar(self, text: str) -> str:
        """Check grammar and return feedback with challenge tracking."""
        if not self.grammar_checker:
            return "Grammar checker not available."
        
        errors, response = self.grammar_checker.check_and_respond(text)
        
        if not errors:
            return ""  # No errors found
        
        return response
    
    def get_grammar_challenges(self) -> str:
        """Get summary of user's grammar challenges."""
        if not self.grammar_checker:
            return "Grammar checker not available."
        
        summary = self.grammar_checker.get_challenges_summary()
        
        if 'message' in summary:
            result = summary['message']
            
            # Add top challenges
            if 'top_challenges' in summary and summary['top_challenges']:
                result += "\n\nYour top challenges:"
                for i, challenge in enumerate(summary['top_challenges'][:3], 1):
                    result += f"\n{i}. {challenge['rule']} ({challenge['count']} times)"
                    if challenge['example']:
                        result += f" - Example: '{challenge['example']}'"
            
            return result
        
        return "No grammar challenges tracked yet."
    
    def get_practice_suggestions(self) -> str:
        """Get grammar practice suggestions based on challenges."""
        if not self.grammar_checker:
            return "Grammar checker not available."
        
        suggestions = self.grammar_checker.get_practice_suggestions()
        
        if suggestions:
            return "Practice these:\n" + "\n".join(suggestions)
        
        return "No specific practice suggestions yet. Keep talking and I'll track your patterns!"
    
    # ==================== LITERATURE LIBRARY ====================
    
    def get_reading_passage(self, category: str = 'classic_novels') -> str:
        """Get a random reading passage from classical literature."""
        if not self.literature_library:
            return "Literature library not available."
        
        passage = self.literature_library.get_random_passage(category)
        
        return f"[*] From '{passage['book']}' by {passage['author']}:\n\n{passage['passage']}"
    
    def search_books(self, query: str) -> str:
        """Search for books in the literature library."""
        if not self.literature_library:
            return "Literature library not available."
        
        books = self.literature_library.search_books(query, max_results=5)
        
        if not books:
            return f"No books found for '{query}'."
        
        result = f"[*] Found {len(books)} books:\n"
        for i, book in enumerate(books, 1):
            result += f"\n{i}. {book.title} by {', '.join(book.authors)}"
        
        return result
    
    def get_literature_categories(self) -> str:
        """Get available literature categories."""
        if not self.literature_library:
            return "Literature library not available."
        
        categories = self.literature_library.get_all_categories()
        counts = {cat: self.literature_library.get_category_count(cat) for cat in categories}
        
        result = f"[*] Literature Library ({self.literature_library.get_total_books()} curated books):\n"
        for cat, count in counts.items():
            result += f"\n• {cat.replace('_', ' ').title()}: {count} books"
        
        return result
    
    # ==================== WRITING ASSISTANT ====================
    
    def improve_writing(self, text: str, tone: str = 'professional') -> str:
        """Improve writing with Grammarly-like suggestions."""
        if not self.writing_assistant:
            return "Writing assistant not available."
        
        result = self.writing_assistant.check_and_improve(text)
        
        response = f"[*] Writing Analysis:\n"
        response += f"• Words: {result['word_count']}\n"
        response += f"• Current tone: {result['current_tone']}\n"
        response += f"• Readability: {result['readability']:.0f}/100\n"
        
        if result['suggestions']:
            response += f"\n[Note] Suggestions:\n"
            for s in result['suggestions'][:3]:
                response += f"• {s['reason']}\n"
        
        response += f"\n[Sparkle] Improved ({tone}) version:\n{result['versions'].get(tone, text)}"
        
        return response
    
    def rewrite_in_tone(self, text: str, tone: str) -> str:
        """Rewrite text in a specific tone."""
        if not self.writing_assistant:
            return "Writing assistant not available."
        
        rewritten = self.writing_assistant.rewrite_in_tone(text, tone)
        return f"[Sparkle] {tone.title()} version:\n{rewritten}"
    
    def get_alternative_phrasings(self, text: str) -> str:
        """Get alternative ways to phrase text."""
        if not self.writing_assistant:
            return "Writing assistant not available."
        
        alternatives = self.writing_assistant.get_alternative_phrasings(text)
        
        if not alternatives:
            return "Could not generate alternatives."
        
        result = "[Idea] Alternative phrasings:\n"
        for i, alt in enumerate(alternatives, 1):
            result += f"\n{i}. {alt}"
        
        return result
    
    def improve_email(self, text: str, tone: str = 'professional') -> str:
        """Improve an email with proper structure and tone."""
        if not self.writing_assistant:
            return "Writing assistant not available."
        
        improved = self.writing_assistant.improve_email(text, tone)
        return f"[*] Improved email ({tone}):\n\n{improved}"
    
    def get_writing_tones(self) -> str:
        """Get available writing tones."""
        if not self.writing_assistant:
            return "Writing assistant not available."
        
        tones = self.writing_assistant.get_available_tones()
        return "Available tones: " + ", ".join(tones)
    
    # ==================== ADOBE CREATIVE SUITE ====================
    
    def get_adobe_products(self) -> str:
        """Get list of supported Adobe products."""
        if not self.adobe_trainer:
            return "Adobe trainer not available."
        
        products = self.adobe_trainer.get_products()
        return "I can help you with: " + ", ".join([p.replace('_', ' ').title() for p in products])
    
    def start_adobe_tutorial(self, product: str, task: str) -> str:
        """Start an Adobe tutorial."""
        if not self.adobe_trainer:
            return "Adobe trainer not available."
        
        return self.adobe_trainer.start_tutorial(product, task)
    
    def adobe_next_step(self) -> str:
        """Get next step in Adobe tutorial."""
        if not self.adobe_trainer:
            return "Adobe trainer not available."
        
        return self.adobe_trainer.next_step()
    
    def adobe_previous_step(self) -> str:
        """Go back to previous step."""
        if not self.adobe_trainer:
            return "Adobe trainer not available."
        
        return self.adobe_trainer.previous_step()
    
    def adobe_repeat_step(self) -> str:
        """Repeat current step."""
        if not self.adobe_trainer:
            return "Adobe trainer not available."
        
        return self.adobe_trainer.repeat_step()
    
    def get_adobe_shortcuts(self, product: str) -> str:
        """Get shortcuts for an Adobe product."""
        if not self.adobe_trainer:
            return "Adobe trainer not available."
        
        shortcuts = self.adobe_trainer.get_shortcuts(product)
        if not shortcuts:
            return f"No shortcuts found for {product}."
        
        result = f"⌨[*] {product.title()} Shortcuts:\n"
        for action, shortcut in list(shortcuts.items())[:15]:
            result += f"• {action.replace('_', ' ').title()}: {shortcut}\n"
        
        return result
    
    def ask_adobe_help(self, question: str) -> str:
        """Ask for help with Adobe products."""
        if not self.adobe_trainer:
            return "Adobe trainer not available."
        
        return self.adobe_trainer.ask_guidance(question)
    
    # ==================== EBOOK READER (MAXONE DRIVE) ====================
    
    def scan_ebooks(self) -> str:
        """Scan for ebooks on connected drives."""
        if not self.ebook_reader:
            return "Ebook reader not available."
        
        count = self.ebook_reader.scan_libraries()
        stats = self.ebook_reader.get_stats()
        
        return f"[*] Found {count} new ebooks!\nTotal: {stats['total_books']} books ({stats['total_size_mb']:.1f} MB)"
    
    def list_ebooks(self, search_term: str = None) -> str:
        """List available ebooks."""
        if not self.ebook_reader:
            return "Ebook reader not available."
        
        books = self.ebook_reader.list_ebooks(search_term=search_term)
        
        if not books:
            return "No ebooks found. Try scanning your library first."
        
        result = f"[*] Found {len(books)} ebooks:\n"
        for book in books[:10]:
            result += f"• {book.title} ({book.format}, {book.size_mb:.1f} MB)\n"
        
        if len(books) > 10:
            result += f"...and {len(books) - 10} more"
        
        return result
    
    def search_ebooks(self, query: str) -> str:
        """Search through ebooks for information."""
        if not self.ebook_reader:
            return "Ebook reader not available."
        
        results = self.ebook_reader.search_ebooks(query)
        
        if not results:
            return f"No results found for '{query}' in your ebook library."
        
        response = f"[Search] Found {len(results)} results for '{query}':\n\n"
        for result in results[:5]:
            response += f"[*] {result.book_title}:\n{result.context}\n\n"
        
        return response
    
    def find_answer_in_ebooks(self, question: str) -> str:
        """Find an answer to a question using ebook content."""
        if not self.ebook_reader:
            return "Ebook reader not available."
        
        return self.ebook_reader.find_answer(question, self.ai_manager)
    
    def get_ebook_summary(self, book_title: str) -> str:
        """Get a summary of an ebook."""
        if not self.ebook_reader:
            return "Ebook reader not available."
        
        # Find the book
        books = self.ebook_reader.list_ebooks(search_term=book_title)
        
        if not books:
            return f"Could not find a book matching '{book_title}'."
        
        book = books[0]
        return self.ebook_reader.get_book_summary(str(book.path), self.ai_manager)
    
    def get_ebook_stats(self) -> str:
        """Get ebook library statistics."""
        if not self.ebook_reader:
            return "Ebook reader not available."
        
        stats = self.ebook_reader.get_stats()
        
        result = f"[*] Ebook Library Stats:\n"
        result += f"• Total books: {stats['total_books']}\n"
        result += f"• Total size: {stats['total_size_mb']:.1f} MB\n"
        result += f"• Formats: {', '.join(f'{k}: {v}' for k, v in stats['formats'].items())}\n"
        result += f"• Library paths: {', '.join(stats['library_paths'][:3])}"
        
        return result
    
    # ==================== ROLEPLAY & COMMUNICATION SKILLS ====================
    
    def get_roleplay_scenarios(self, category: str = None) -> str:
        """Get available roleplay scenarios."""
        if not self.roleplay_trainer:
            return "Roleplay trainer not available."
        
        from .roleplay_trainer import ScenarioCategory
        
        cat = None
        if category:
            try:
                cat = ScenarioCategory(category.lower())
            except:
                pass
        
        scenarios = self.roleplay_trainer.get_scenarios(cat)
        
        result = "[*] Available Roleplay Scenarios:\n\n"
        for s in scenarios[:10]:
            result += f"• **{s.title}** ({s.category.value})\n  {s.description[:60]}...\n\n"
        
        return result
    
    def start_roleplay(self, scenario_id: str = None, category: str = None) -> str:
        """Start a roleplay scenario."""
        if not self.roleplay_trainer:
            return "Roleplay trainer not available."
        
        # If no specific scenario, pick one from category or random
        if not scenario_id:
            scenarios = self.roleplay_trainer.get_scenarios()
            if category:
                from .roleplay_trainer import ScenarioCategory
                try:
                    cat = ScenarioCategory(category.lower())
                    scenarios = [s for s in scenarios if s.category == cat]
                except:
                    pass
            
            if scenarios:
                import random
                scenario_id = random.choice(scenarios).id
            else:
                return "No scenarios available."
        
        return self.roleplay_trainer.start_scenario(scenario_id)
    
    def roleplay_respond(self, response: str) -> str:
        """Respond in the current roleplay."""
        if not self.roleplay_trainer:
            return "Roleplay trainer not available."
        
        return self.roleplay_trainer.respond(response)
    
    def end_roleplay(self) -> str:
        """End the current roleplay and get feedback."""
        if not self.roleplay_trainer:
            return "Roleplay trainer not available."
        
        return self.roleplay_trainer.end_scenario()
    
    def get_technique_info(self, technique: str) -> str:
        """Get information about a communication technique."""
        if not self.roleplay_trainer:
            return "Roleplay trainer not available."
        
        return self.roleplay_trainer.get_technique_info(technique)
    
    def quick_roleplay_practice(self, technique: str) -> str:
        """Start quick practice for a specific technique."""
        if not self.roleplay_trainer:
            return "Roleplay trainer not available."
        
        return self.roleplay_trainer.quick_practice(technique)


# Singleton instance
_study_assistant = None

def get_study_assistant(ai_manager=None, tts_manager=None) -> StudyAssistant:
    """Get or create the study assistant singleton."""
    global _study_assistant
    if _study_assistant is None:
        _study_assistant = StudyAssistant(ai_manager, tts_manager)
    elif ai_manager:
        _study_assistant.ai_manager = ai_manager
    elif tts_manager:
        _study_assistant.tts_manager = tts_manager
    return _study_assistant


# Test
if __name__ == "__main__":
    print("Testing Study Assistant...")
    
    assistant = get_study_assistant()
    
    # Test screen capture
    print("\n1. Capturing screen...")
    result = assistant.capture_and_read_screen()
    print(f"Result: {result}")
    
    # Test pronunciation
    print("\n2. Testing pronunciation...")
    checker = PronunciationChecker()
    score, feedback = checker.compare_pronunciation("necessary", "nessesary")
    print(f"Score: {score}, Feedback: {feedback}")
    
    print("\nStudy Assistant ready!")
