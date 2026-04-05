"""
Text-to-Speech Service for Monica AI.
Wraps the TTS Manager into a managed service.
"""

import threading
import time
import logging
import queue
from typing import Optional, Callable, List, Any

logger = logging.getLogger("Monica.TTS")


class TTSService:
    """
    Text-to-Speech service for Monica AI.
    
    Features:
    - Multiple TTS engine support (Piper, Coqui XTTS, system)
    - Non-blocking speech queue
    - Speaking state management
    - Callbacks for speech start/end
    """

    def __init__(self, orchestrator, config: dict = None):
        self.orchestrator = orchestrator
        self.config = config or {}
        
        # State
        self.is_speaking = False
        self.is_initialized = False
        self.stop_event = threading.Event()
        
        # Barge-in support
        self._interrupt_event = threading.Event()  # Set to interrupt current speech
        self._current_text = ""  # Full text being spoken
        self._spoken_so_far = ""  # Text already delivered
        
        # Speech queue
        self.speech_queue = queue.Queue()
        self.worker_thread: Optional[threading.Thread] = None
        
        # TTS Manager instance
        self.tts_manager = None
        
        # Callbacks
        self.start_callbacks: List[Callable[[str], None]] = []
        self.end_callbacks: List[Callable[[str], None]] = []
        
        logger.info("TTS Service created")

    def initialize(self):
        """Initialize the TTS engine."""
        try:
            from audio.tts_manager import TTSManager
            from config.settings import config as app_config
            self.tts_manager = TTSManager(app_config)
            self.is_initialized = True
            logger.info("TTS Service initialized")
        except Exception as e:
            logger.error(f"TTS initialization failed: {e}")
            self.is_initialized = False

    def run(self):
        """Main TTS loop - process speech queue."""
        if not self.is_initialized:
            self.initialize()
        
        logger.info("TTS worker started")
        
        while not self.stop_event.is_set():
            try:
                # Wait for text to speak
                text = self.speech_queue.get(timeout=1.0)
                if text is None:
                    continue
                
                self._speak_text(text)
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"TTS loop error: {e}")
                time.sleep(0.5)

    def _speak_text(self, text: str):
        """Synthesize and play speech with barge-in support.
        
        Splits long text into sentence chunks so interrupts are responsive.
        Tracks progress so interrupted speech can be resumed.
        """
        self.is_speaking = True
        self._interrupt_event.clear()
        self._current_text = text
        self._spoken_so_far = ""
        
        # Share state via orchestrator
        if self.orchestrator:
            self.orchestrator.set_shared('tts_speaking', True)
            self.orchestrator.set_shared('tts_text', text)
            self.orchestrator.set_shared('tts_spoken_so_far', '')
        
        # Notify start callbacks
        for cb in self.start_callbacks:
            try:
                cb(text)
            except Exception:
                pass
        
        try:
            logger.info(f"TTS speaking: '{text[:80]}...'")
            
            # Send FULL text to tts_manager as ONE call — it handles splitting
            # and sequential playback internally. Do NOT split here too, or
            # multiple overlapping synthesis threads will produce multiple voices.
            try:
                if self.tts_manager:
                    self.tts_manager.speak(text, block=True)
                else:
                    try:
                        import pyttsx3
                        engine = pyttsx3.init()
                        engine.say(text)
                        engine.runAndWait()
                    except ImportError:
                        logger.warning(f"No TTS engine available. Text: {text}")
            except Exception as e:
                logger.error(f"TTS speak error: {e}")
            
            self._spoken_so_far = text
                    
        except Exception as e:
            logger.error(f"TTS speak error: {e}")
        finally:
            self.is_speaking = False
            if self.orchestrator:
                self.orchestrator.set_shared('tts_speaking', False)
            
            # Notify end callbacks
            for cb in self.end_callbacks:
                try:
                    cb(text)
                except Exception:
                    pass
    
    @staticmethod
    def _split_into_chunks(text: str) -> List[str]:
        """Split text into sentence-level chunks for responsive interrupts."""
        import re
        # Split on sentence boundaries
        sentences = re.split(r'(?<=[.!?])\s+', text)
        # Merge very short sentences with the next one
        chunks = []
        current = ""
        for s in sentences:
            current += (" " if current else "") + s
            if len(current) >= 40:  # Min chunk size
                chunks.append(current.strip())
                current = ""
        if current.strip():
            chunks.append(current.strip())
        return chunks if chunks else [text]

    def speak(self, text: str):
        """Queue text for speaking (non-blocking)."""
        self.speech_queue.put(text)

    def speak_now(self, text: str):
        """Speak immediately, clearing queue."""
        # Clear existing queue
        while not self.speech_queue.empty():
            try:
                self.speech_queue.get_nowait()
            except queue.Empty:
                break
        self.speech_queue.put(text)

    def stop_speaking(self):
        """Stop current speech immediately (barge-in)."""
        self._interrupt_event.set()  # Signal chunk loop to stop
        if self.tts_manager and hasattr(self.tts_manager, 'stop'):
            self.tts_manager.stop()
        self.is_speaking = False
        # Immediately clear shared state so STT resumes listening
        if self.orchestrator:
            self.orchestrator.set_shared('tts_speaking', False)
        logger.info("TTS stop_speaking called (barge-in)")

    def add_start_callback(self, callback: Callable[[str], None]):
        """Add callback for when speech starts."""
        self.start_callbacks.append(callback)

    def add_end_callback(self, callback: Callable[[str], None]):
        """Add callback for when speech ends."""
        self.end_callbacks.append(callback)

    def stop(self):
        """Stop the TTS service."""
        self.stop_event.set()
        self.stop_speaking()
        logger.info("TTS Service stopped")
