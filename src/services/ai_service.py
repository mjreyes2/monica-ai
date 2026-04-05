"""
AI Service for Monica AI.
Wraps the multi-model manager and knowledge connector into a managed service.
"""

import os
import re
import json
import threading
import time
import logging
import queue
import urllib.parse
from pathlib import Path
from typing import Optional, Callable, List, Dict, Any

logger = logging.getLogger("Monica.AI")


class AIService:
    """
    AI conversation and reasoning service for Monica AI.
    
    Features:
    - Multi-model Ollama backend (smart routing)
    - Knowledge base / RAG integration
    - Conversation memory
    - Async response generation
    """

    def __init__(self, orchestrator, config: dict = None):
        self.orchestrator = orchestrator
        self.config = config or {}
        
        # State
        self.is_initialized = False
        self.is_processing = False
        self.stop_event = threading.Event()
        
        # Sub-systems
        self.model_manager = None
        self.knowledge_connector = None
        self.user_profile_learner = None
        self.hipaa = None
        self.interrupt_manager = None
        self.budget_manager = None
        self.conversation_history: List[Dict[str, str]] = []
        # src/services/ai_service.py → project root is 2 levels up
        self._history_file = Path(__file__).parent.parent.parent / 'data' / 'user_profile' / 'conversation_history.json'
        self._load_conversation_history()
        
        # Request/response queues
        self.request_queue = queue.Queue()
        self.response_callbacks: List[Callable[[str], None]] = []
        
        logger.info("AI Service created")

    def _load_conversation_history(self):
        """Load conversation history from disk."""
        try:
            if self._history_file.exists():
                with open(self._history_file, 'r', encoding='utf-8') as f:
                    self.conversation_history = json.load(f)
                # Keep only last 50 exchanges
                if len(self.conversation_history) > 100:
                    self.conversation_history = self.conversation_history[-100:]
                logger.info(f"Loaded {len(self.conversation_history)} conversation history entries")
        except Exception as e:
            logger.debug(f"Could not load conversation history: {e}")
            self.conversation_history = []

    def _save_conversation_history(self):
        """Save conversation history to disk."""
        try:
            self._history_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self._history_file, 'w', encoding='utf-8') as f:
                json.dump(self.conversation_history[-100:], f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.debug(f"Could not save conversation history: {e}")

    def initialize(self):
        """Initialize AI backends."""
        logger.info("Initializing AI backends...")
        
        # Multi-model manager
        try:
            from ai.multi_model_manager import MultiModelManager
            self.model_manager = MultiModelManager()
            logger.info("  [OK] Multi-model manager loaded")
        except Exception as e:
            logger.warning(f"  [SKIP] Multi-model manager: {e}")
        
        # Knowledge connector / RAG
        try:
            from ai.knowledge_connector import get_knowledge_connector
            self.knowledge_connector = get_knowledge_connector()
            logger.info("  [OK] Knowledge connector loaded")
        except Exception as e:
            logger.warning(f"  [SKIP] Knowledge connector: {e}")
        
        # User Profile Learner - learns about the user from every interaction
        try:
            from ai.user_profile_learner import get_user_profile_learner
            self.user_profile_learner = get_user_profile_learner()
            logger.info(f"  [OK] User profile learner loaded ({self.user_profile_learner._interaction_count} past interactions)")
        except Exception as e:
            logger.warning(f"  [SKIP] User profile learner: {e}")
        
        # HIPAA Compliance
        try:
            from security.hipaa_compliance import get_hipaa_compliance
            self.hipaa = get_hipaa_compliance()
            logger.info("  [OK] HIPAA compliance module loaded")
        except Exception as e:
            logger.warning(f"  [SKIP] HIPAA compliance: {e}")
        
        # Interrupt Manager - barge-in, stop/resume, suppression list
        try:
            from services.interrupt_manager import get_interrupt_manager
            self.interrupt_manager = get_interrupt_manager(self.orchestrator)
            self.interrupt_manager.start_monitoring()
            suppressed = self.interrupt_manager.get_suppression_list()
            logger.info(f"  [OK] Interrupt manager loaded ({len(suppressed)} suppressed behaviors)")
        except Exception as e:
            logger.warning(f"  [SKIP] Interrupt manager: {e}")
        
        # Budget Manager - personal finance tracking and visualization
        try:
            from ai.monica_budget import get_budget_manager
            self.budget_manager = get_budget_manager()
            logger.info(f"  [OK] Budget manager loaded ({len(self.budget_manager.transactions)} transactions)")
        except Exception as e:
            logger.warning(f"  [SKIP] Budget manager: {e}")
        
        # Knowledge Base Watcher - auto-integrates new PDFs/articles
        self.knowledge_watcher = None
        try:
            from ai.knowledge_watcher import get_knowledge_watcher
            self.knowledge_watcher = get_knowledge_watcher()
            self.knowledge_watcher.start()
            stats = self.knowledge_watcher.get_stats()
            logger.info(f"  [OK] Knowledge watcher started ({stats['total_documents']} docs, {stats['total_chunks']} chunks)")
        except Exception as e:
            logger.warning(f"  [SKIP] Knowledge watcher: {e}")
        
        # HIPAA-Secure Web Search - gives Monica internet access
        self.web_searcher = None
        try:
            from utils.web_search import get_web_searcher
            self.web_searcher = get_web_searcher()
            logger.info("  [OK] Web search loaded (HIPAA-secure, DuckDuckGo)")
        except Exception as e:
            logger.warning(f"  [SKIP] Web search: {e}")
        
        # Universal Object Detector - detects any visible object
        self.object_detector = None
        try:
            from vision.object_detector import get_object_detector
            self.object_detector = get_object_detector()
            status = self.object_detector.get_status()
            logger.info(f"  [OK] Object detector loaded (YOLO={status['yolo_available']}, {status['coco_classes']} classes)")
        except Exception as e:
            logger.warning(f"  [SKIP] Object detector: {e}")
        
        # Session Memory - recalls past conversations, tracks time gaps
        self.session_memory = None
        try:
            from ai.session_memory import get_session_memory
            self.session_memory = get_session_memory()
            self.session_memory.start_session()
            logger.info(f"  [OK] Session memory loaded ({self.session_memory.get_session_count()} past sessions)")
        except Exception as e:
            logger.warning(f"  [SKIP] Session memory: {e}")
        
        # Creative Arts - painting, drawing, image generation
        self.creative_arts = None
        try:
            from ai.monica_creative_arts import get_creative_arts
            self.creative_arts = get_creative_arts()
            logger.info(f"  [OK] Creative arts loaded (SD={self.creative_arts._sd_available})")
        except Exception as e:
            logger.warning(f"  [SKIP] Creative arts: {e}")
        
        # English Teacher - grammar, vocabulary, quizzes, pronunciation
        self.english_teacher = None
        try:
            from ai.monica_english_teacher import get_english_teacher
            self.english_teacher = get_english_teacher()
            stats = self.english_teacher.get_vocab_stats()
            logger.info(f"  [OK] English teacher loaded ({stats['total_words']} vocab words tracked)")
        except Exception as e:
            logger.warning(f"  [SKIP] English teacher: {e}")
        
        # World Teacher - all human languages + programming languages + dev tools
        self.world_teacher = None
        try:
            from ai.monica_world_teacher import get_world_teacher
            self.world_teacher = get_world_teacher()
            subjects = self.world_teacher.list_all_subjects()
            logger.info(f"  [OK] World teacher loaded ({len(subjects['human_languages'])} human langs, "
                         f"{len(subjects['programming'])} prog langs, {len(subjects['dev_tools'])} tools)")
        except Exception as e:
            logger.warning(f"  [SKIP] World teacher: {e}")
        
        # University Teaching System - 20+ academic subjects
        self.university = None
        try:
            from ai.monica_university import get_university
            self.university = get_university()
            from ai.monica_university import SUBJECTS
            logger.info(f"  [OK] University teaching loaded ({len(SUBJECTS)} subjects)")
        except Exception as e:
            logger.warning(f"  [SKIP] University teaching: {e}")
        
        # Knowledge Learner - learns from URLs, spoken info, PDFs
        self.knowledge_learner = None
        try:
            from ai.monica_knowledge_learner import get_knowledge_learner
            self.knowledge_learner = get_knowledge_learner()
            stats = self.knowledge_learner.get_stats()
            logger.info(f"  [OK] Knowledge learner loaded ({stats['total_entries']} entries, "
                         f"{stats['urls_read']} URLs, {stats['spoken_facts']} spoken facts)")
        except Exception as e:
            logger.warning(f"  [SKIP] Knowledge learner: {e}")
        
        self.is_initialized = True
        logger.info("AI backends initialized")

    def run(self):
        """Main AI processing loop."""
        if not self.is_initialized:
            self.initialize()
        
        logger.info("AI processing loop started")
        
        while not self.stop_event.is_set():
            try:
                request = self.request_queue.get(timeout=1.0)
                if request is None:
                    continue
                
                response = self._process_request(request)
                
                # Publish response with consumed flag for GUI pickup
                if self.orchestrator:
                    self.orchestrator.set_shared('ai_thinking', False)
                    self.orchestrator.set_shared('ai_response', response)
                    self.orchestrator.set_shared('ai_consumed', False)
                    self.orchestrator.set_shared('ai_timestamp', time.time())
                
                # Notify callbacks
                for cb in self.response_callbacks:
                    try:
                        cb(response)
                    except Exception as e:
                        logger.debug(f"AI callback error: {e}")
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"AI loop error: {e}")
                # Ensure a response is always published so the GUI doesn't hang
                if self.orchestrator:
                    self.orchestrator.set_shared('ai_thinking', False)
                    self.orchestrator.set_shared('ai_response',
                        "I had an internal error processing that. Could you try again?")
                    self.orchestrator.set_shared('ai_consumed', False)
                    self.orchestrator.set_shared('ai_timestamp', time.time())
                time.sleep(0.5)

    def _handle_voice_command(self, user_text: str) -> Optional[str]:
        """Handle direct voice commands before sending to LLM.
        Returns a response string if handled, None if not a command."""
        text_lower = user_text.lower().strip()
        import re
        logger.info(f"[VOICE_CMD] Checking: '{text_lower}'")
        
        # "Monica initialize" trigger - play sounds + speak initialization
        if 'initialize' in text_lower and ('monica' in text_lower or text_lower.startswith('initialize')):
            return self._do_initialize_sequence()
        
        # ========== LOCATION COMMANDS (checked first, many patterns) ==========
        # "Show me [place] on the globe/map"
        loc_match = re.search(
            r'(?:show\s+me\s+(?:where\s+)?(.+?)\s+(?:is\s+)?(?:located\s+)?on\s+the\s+(?:globe|glow|map))',
            text_lower
        )
        if loc_match:
            place = self._clean_place_name(loc_match.group(1))
            if place and len(place) > 1:
                logger.info(f"[VOICE_CMD] Location match (regex): '{place}'")
                return self._do_show_location(place)
        
        # Static trigger phrases — order matters (longer matches first)
        # ONLY use phrases that clearly indicate a location request
        location_triggers = [
            'can you show me where', 'can you show me',
            'show me where', 'show me on the globe', 'show me on the map',
            'show me on the glow', 'where is', 'find on globe',
            'show on globe', 'take me to', 'fly to',
            'show me',
        ]
        # Non-location phrases to exclude
        _non_location = {'the globe', 'the glow', 'the map', 'the keyboard',
                         'the dial', 'the orb', 'yourself', 'the weather',
                         'weather', 'earthquakes', 'earthquake', 'lightning',
                         'temperature', 'temperatures', 'the temperature',
                         'the lightning', 'the earthquakes'}
        # Words that indicate the sentence is NOT a location query
        _non_location_words = {'how', 'what', 'why', 'when', 'if', 'can',
                               'miles', 'hour', 'hours', 'minutes', 'long',
                               'much', 'many', 'calculate', 'solve', 'math',
                               'plus', 'minus', 'times', 'divided', 'equals',
                               'traveling', 'driving', 'speed', 'distance'}
        for trigger in location_triggers:
            if trigger in text_lower:
                place = self._clean_place_name(text_lower.split(trigger, 1)[1])
                if place and len(place) > 1 and place not in _non_location:
                    # Check if the original text contains words that suggest
                    # this is NOT a location query (e.g., math, travel time)
                    words = set(text_lower.split())
                    if words & _non_location_words:
                        logger.info(f"[VOICE_CMD] Skipping location trigger '{trigger}' - non-location words detected")
                        break  # Fall through to LLM
                    logger.info(f"[VOICE_CMD] Location match (trigger '{trigger}'): '{place}'")
                    return self._do_show_location(place)
        
        # ========== Globe data layer toggles ==========
        # "Show weather/earthquakes/lightning on the globe"
        if any(p in text_lower for p in ['show weather', 'show the weather', 'show me the weather',
                                          'show me weather', 'display weather']):
            return self._do_globe_toggle('weather', True)
        if any(p in text_lower for p in ['hide weather', 'turn off weather', 'remove weather']):
            return self._do_globe_toggle('weather', False)
        if any(p in text_lower for p in ['show earthquake', 'show the earthquake', 'show me earthquake',
                                          'show earthquakes', 'show me earthquakes']):
            return self._do_globe_toggle('earthquakes', True)
        if any(p in text_lower for p in ['hide earthquake', 'turn off earthquake', 'remove earthquake']):
            return self._do_globe_toggle('earthquakes', False)
        if any(p in text_lower for p in ['show lightning', 'show the lightning', 'show me lightning',
                                          'show me the lightning']):
            return self._do_globe_toggle('lightning', True)
        if any(p in text_lower for p in ['hide lightning', 'turn off lightning', 'remove lightning']):
            return self._do_globe_toggle('lightning', False)
        if any(p in text_lower for p in ['show temperature', 'show the temperature', 'show temperatures']):
            return self._do_globe_toggle('temperature', True)
        if any(p in text_lower for p in ['hide temperature', 'turn off temperature']):
            return self._do_globe_toggle('temperature', False)
        
        # ========== Globe zoom commands ==========
        if any(p in text_lower for p in ['zoom in', 'zoom closer', 'get closer']):
            return self._do_globe_zoom('in')
        if any(p in text_lower for p in ['zoom out', 'zoom back', 'pull back', 'back out']):
            return self._do_globe_zoom('out')
        if any(p in text_lower for p in ['globe view', 'back to globe', 'full globe',
                                          'zoom all the way out', 'reset zoom']):
            return self._do_globe_zoom('reset')
        
        # ========== Globe rotation commands ==========
        if any(p in text_lower for p in ['turn the globe to the right', 'turn globe right',
                                          'rotate right', 'turn right']):
            return self._do_globe_turn('right')
        if any(p in text_lower for p in ['turn the globe to the left', 'turn globe left',
                                          'rotate left', 'turn left']):
            return self._do_globe_turn('left')
        
        # ========== Globe size commands ==========
        if any(p in text_lower for p in ['enlarge the globe', 'enlarge globe', 'make the globe bigger',
                                          'bigger globe', 'make globe bigger']):
            return self._do_globe_resize('bigger')
        if any(p in text_lower for p in ['shrink the globe', 'shrink globe', 'make the globe smaller',
                                          'smaller globe', 'make globe smaller']):
            return self._do_globe_resize('smaller')
        
        # ========== Globe stop/resume spin ==========
        if any(p in text_lower for p in ['stop spinning', 'stop the globe', 'stop rotating',
                                          'pause the globe', 'freeze the globe']):
            return self._do_globe_spin(False)
        if any(p in text_lower for p in ['start spinning', 'resume spinning', 'spin the globe',
                                          'resume the globe', 'continue spinning']):
            return self._do_globe_spin(True)
        
        # "Show globe" / "Show the globe" / "Show me the globe"
        if any(p in text_lower for p in ['show me the globe', 'show the globe', 'show globe',
                                          'show me the glow', 'show the glow', 'show glow',
                                          'display the globe', 'open globe', 'open the globe',
                                          'pull up the globe', 'launch the globe', 'launch globe']):
            return self._do_show_window('globe')
        
        # "Show keyboard" / "Show the keyboard"
        if any(p in text_lower for p in ['show the keyboard', 'show keyboard', 'display keyboard', 'open keyboard']):
            return self._do_show_window('keyboard')
        
        # "Show dial" / "Show the dial"
        if any(p in text_lower for p in ['show the dial', 'show dial', 'display dial', 'open dial']):
            return self._do_show_window('dial')
        
        # "Show yourself" / "Show orb"
        if any(p in text_lower for p in ['show yourself', 'show the orb', 'show orb', 'appear']):
            return self._do_show_window('orb')
        
        # "Hide globe/keyboard/dial/orb"
        if any(p in text_lower for p in ['hide the globe', 'hide globe', 'close globe']):
            return self._do_hide_window('globe')
        if any(p in text_lower for p in ['hide the keyboard', 'hide keyboard', 'close keyboard']):
            return self._do_hide_window('keyboard')
        if any(p in text_lower for p in ['hide yourself', 'hide the orb', 'hide orb', 'disappear']):
            return self._do_hide_window('orb')
        
        return None
    
    @staticmethod
    def _clean_place_name(raw: str) -> str:
        """Clean extracted place name from voice command."""
        place = raw.strip().rstrip('?.!,')
        # Remove leading conversational filler (longest first, loop until stable)
        prefixes = [
            'an aerial view of the ', 'an aerial view of ',
            'aerial view of the ', 'aerial view of ',
            'a satellite view of the ', 'a satellite view of ',
            'the location of the ', 'the location of ',
            'a map of the ', 'a map of ', 'the map of ',
            'the city of ', 'the country of ', 'the state of ',
            'the capital of ', 'the region of ',
            'me the location of ', 'me where the ',
        ]
        changed = True
        while changed:
            changed = False
            for prefix in prefixes:
                if place.startswith(prefix):
                    place = place[len(prefix):]
                    changed = True
                    break
            # Strip orphaned articles/prepositions left over from Whisper
            for junk in ['the of ', 'of the ', 'the ', 'of ']:
                if place.startswith(junk) and len(place) > len(junk) + 2:
                    place = place[len(junk):]
                    changed = True
                    break
        # Remove trailing filler words that Whisper adds
        for suffix in [' is located', ' is on', ' is at', ' is', ' located',
                       ' on the globe', ' on the glow', ' on the map',
                       ' on globe', ' on map', ' please', ' for me']:
            if place.endswith(suffix):
                place = place[:-len(suffix)].strip()
        return place.strip()
    
    def _do_globe_toggle(self, layer: str, enabled: bool) -> str:
        """Toggle a globe data layer on/off."""
        vision = self.orchestrator.get_service('vision') if self.orchestrator else None
        if not vision:
            return "Vision service not ready."
        vision.globe_enabled = True
        attr_map = {
            'weather': ('_show_clouds', '_show_temperature'),
            'earthquakes': ('_show_earthquakes',),
            'lightning': ('_show_lightning',),
            'temperature': ('_show_temperature',),
            'clouds': ('_show_clouds',),
        }
        for attr in attr_map.get(layer, ()):
            setattr(vision, attr, enabled)
        state = "on" if enabled else "off"
        return f"{layer.capitalize()} overlay turned {state} on the globe."
    
    def _do_globe_zoom(self, direction: str) -> str:
        """Zoom the globe in, out, or reset."""
        vision = self.orchestrator.get_service('vision') if self.orchestrator else None
        if not vision:
            return "Vision service not ready."
        vision.globe_enabled = True
        current = getattr(vision, 'globe_size', 180)
        if direction == 'in':
            vision.globe_size = min(600, current + 60)
            vision._rotation_paused_until = time.time() + 30
            return "Zooming in."
        elif direction == 'out':
            vision.globe_size = max(100, current - 60)
            return "Zooming out."
        else:  # reset
            vision.globe_size = 180
            return "Back to globe view."
    
    def _do_globe_turn(self, direction: str) -> str:
        """Turn the globe left or right."""
        vision = self.orchestrator.get_service('vision') if self.orchestrator else None
        if not vision:
            return "Vision service not ready."
        vision.globe_enabled = True
        amount = 30  # degrees
        if direction == 'right':
            vision.globe_rotation = (vision.globe_rotation + amount) % 360
        else:
            vision.globe_rotation = (vision.globe_rotation - amount) % 360
        vision._rotation_paused_until = time.time() + 30
        return f"Turning the globe to the {direction}."
    
    def _do_globe_resize(self, direction: str) -> str:
        """Make the globe bigger or smaller."""
        vision = self.orchestrator.get_service('vision') if self.orchestrator else None
        if not vision:
            return "Vision service not ready."
        vision.globe_enabled = True
        current = getattr(vision, 'globe_size', 180)
        if direction == 'bigger':
            vision.globe_size = min(600, current + 80)
        else:
            vision.globe_size = max(80, current - 80)
        return f"Globe {'enlarged' if direction == 'bigger' else 'shrunk'}."
    
    def _do_globe_spin(self, spinning: bool) -> str:
        """Start or stop globe auto-rotation."""
        vision = self.orchestrator.get_service('vision') if self.orchestrator else None
        if not vision:
            return "Vision service not ready."
        if spinning:
            vision._rotation_paused_until = 0
            return "Globe is spinning again."
        else:
            vision._rotation_paused_until = time.time() + 9999
            return "Globe rotation paused."
    
    def _do_initialize_sequence(self) -> str:
        """Play the full Monica initialization sequence with sounds and voice."""
        import threading
        try:
            # Play initialization sound via orb window
            if self.orchestrator:
                vision = self.orchestrator.get_service('vision')
                ar_system = getattr(vision, 'ar_hologram', None) if vision else None
                orb = getattr(ar_system, 'orb_window', None) if ar_system else None
                
                if orb:
                    orb.start()
                    orb.show(with_sounds=True)
                else:
                    # Try playing sound directly via pygame
                    try:
                        import pygame
                        if not pygame.mixer.get_init():
                            pygame.mixer.init()
                        sound_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                                                  'monica_ai', 'resources', 'sounds', 'scifi')
                        init_sound = os.path.join(sound_dir, 'monica_initialize_one.mp3')
                        if os.path.exists(init_sound):
                            pygame.mixer.Sound(init_sound).play()
                    except Exception:
                        pass
                
                # Speak initialization phrases via TTS
                tts = self.orchestrator.get_service('tts') if self.orchestrator else None
                if tts and hasattr(tts, 'speak'):
                    phrases = [
                        "Monica initializing.",
                        "Uploading consciousness.",
                        "Establishing neural pathways.",
                        "Calibrating sensory inputs.",
                        "All systems online. Monica is ready.",
                    ]
                    def _speak_sequence():
                        import time as _time
                        for phrase in phrases:
                            try:
                                tts.speak(phrase)
                                _time.sleep(1.5)
                            except Exception:
                                pass
                    threading.Thread(target=_speak_sequence, daemon=True).start()
                    return "Monica initializing... All systems coming online."
            
            return "Monica initialization sequence started."
        except Exception as e:
            logger.error(f"Initialize sequence error: {e}")
            return "Initialization sequence encountered an error, but I'm still here."
    
    # Known countries/regions that Open-Meteo misidentifies (returns US towns instead)
    _KNOWN_LOCATIONS = {
        'england': (51.5, -1.0, 'England', 'United Kingdom'),
        'scotland': (56.5, -4.0, 'Scotland', 'United Kingdom'),
        'wales': (52.0, -3.5, 'Wales', 'United Kingdom'),
        'ireland': (53.0, -8.0, 'Ireland', 'Ireland'),
        'united kingdom': (54.0, -2.0, 'United Kingdom', 'United Kingdom'),
        'uk': (54.0, -2.0, 'United Kingdom', 'United Kingdom'),
        'france': (46.0, 2.0, 'France', 'France'),
        'germany': (51.0, 10.0, 'Germany', 'Germany'),
        'italy': (42.0, 12.0, 'Italy', 'Italy'),
        'spain': (40.0, -4.0, 'Spain', 'Spain'),
        'portugal': (39.5, -8.0, 'Portugal', 'Portugal'),
        'netherlands': (52.0, 5.0, 'Netherlands', 'Netherlands'),
        'belgium': (50.5, 4.5, 'Belgium', 'Belgium'),
        'switzerland': (47.0, 8.0, 'Switzerland', 'Switzerland'),
        'austria': (47.5, 14.0, 'Austria', 'Austria'),
        'poland': (52.0, 20.0, 'Poland', 'Poland'),
        'sweden': (62.0, 15.0, 'Sweden', 'Sweden'),
        'norway': (62.0, 10.0, 'Norway', 'Norway'),
        'denmark': (56.0, 10.0, 'Denmark', 'Denmark'),
        'finland': (64.0, 26.0, 'Finland', 'Finland'),
        'greece': (39.0, 22.0, 'Greece', 'Greece'),
        'turkey': (39.0, 35.0, 'Turkey', 'Türkiye'),
        'russia': (60.0, 100.0, 'Russia', 'Russia'),
        'china': (35.0, 105.0, 'China', 'China'),
        'japan': (36.0, 138.0, 'Japan', 'Japan'),
        'india': (20.0, 77.0, 'India', 'India'),
        'australia': (-25.0, 135.0, 'Australia', 'Australia'),
        'brazil': (-10.0, -55.0, 'Brazil', 'Brazil'),
        'mexico': (23.0, -102.0, 'Mexico', 'Mexico'),
        'canada': (56.0, -106.0, 'Canada', 'Canada'),
        'argentina': (-34.0, -64.0, 'Argentina', 'Argentina'),
        'egypt': (26.0, 30.0, 'Egypt', 'Egypt'),
        'south africa': (-29.0, 24.0, 'South Africa', 'South Africa'),
        'nigeria': (10.0, 8.0, 'Nigeria', 'Nigeria'),
        'kenya': (0.0, 38.0, 'Kenya', 'Kenya'),
        'morocco': (32.0, -5.0, 'Morocco', 'Morocco'),
        'colombia': (4.0, -72.0, 'Colombia', 'Colombia'),
        'peru': (-10.0, -76.0, 'Peru', 'Peru'),
        'chile': (-30.0, -71.0, 'Chile', 'Chile'),
        'saudi arabia': (24.0, 45.0, 'Saudi Arabia', 'Saudi Arabia'),
        'israel': (31.5, 34.8, 'Israel', 'Israel'),
        'iran': (32.0, 53.0, 'Iran', 'Iran'),
        'iraq': (33.0, 44.0, 'Iraq', 'Iraq'),
        'pakistan': (30.0, 70.0, 'Pakistan', 'Pakistan'),
        'afghanistan': (33.0, 65.0, 'Afghanistan', 'Afghanistan'),
        'thailand': (15.0, 100.0, 'Thailand', 'Thailand'),
        'vietnam': (16.0, 108.0, 'Vietnam', 'Vietnam'),
        'philippines': (13.0, 122.0, 'Philippines', 'Philippines'),
        'indonesia': (-5.0, 120.0, 'Indonesia', 'Indonesia'),
        'malaysia': (4.0, 109.5, 'Malaysia', 'Malaysia'),
        'singapore': (1.35, 103.8, 'Singapore', 'Singapore'),
        'south korea': (36.5, 128.0, 'South Korea', 'South Korea'),
        'north korea': (40.0, 127.0, 'North Korea', 'North Korea'),
        'taiwan': (23.5, 121.0, 'Taiwan', 'Taiwan'),
        'new zealand': (-41.0, 174.0, 'New Zealand', 'New Zealand'),
        'cuba': (22.0, -80.0, 'Cuba', 'Cuba'),
        'haiti': (19.0, -72.0, 'Haiti', 'Haiti'),
        'jamaica': (18.1, -77.3, 'Jamaica', 'Jamaica'),
        'ukraine': (49.0, 32.0, 'Ukraine', 'Ukraine'),
        'romania': (46.0, 25.0, 'Romania', 'Romania'),
        'hungary': (47.0, 20.0, 'Hungary', 'Hungary'),
        'czech republic': (49.8, 15.5, 'Czech Republic', 'Czechia'),
        'florida': (27.6, -81.5, 'Florida', 'United States'),
        'california': (36.8, -119.4, 'California', 'United States'),
        'texas': (31.0, -100.0, 'Texas', 'United States'),
        'new york': (40.7128, -74.006, 'New York', 'United States'),
    }

    def _geocode(self, query: str):
        """Geocode a place name via Open-Meteo. Returns (lat, lng, name, country) or (None,)*4."""
        import urllib.request, json
        try:
            encoded = urllib.parse.quote(query.strip())
            url = f"https://geocoding-api.open-meteo.com/v1/search?name={encoded}&count=1&language=en"
            req = urllib.request.Request(url, headers={'User-Agent': 'Monica-AI/1.0'})
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode())
            results = data.get('results', [])
            if results:
                r = results[0]
                return r.get('latitude'), r.get('longitude'), r.get('name', query), r.get('country', '')
        except Exception as e:
            logger.debug(f"Geocode error for '{query}': {e}")
        return None, None, None, None

    def _do_show_location(self, place_name: str) -> str:
        """Geocode a place, highlight it on the globe, and return info."""
        import urllib.request, json
        
        # Enable globe if not already
        vision = self.orchestrator.get_service('vision') if self.orchestrator else None
        if vision:
            vision.globe_enabled = True
        
        pn = place_name.lower().strip()
        
        # 1. Check built-in lookup first (handles countries/regions the API gets wrong)
        if pn in self._KNOWN_LOCATIONS:
            lat, lng, name, country = self._KNOWN_LOCATIONS[pn]
            logger.info(f"[GEO] Built-in lookup: '{pn}' -> {name} ({lat}, {lng})")
        else:
            # 2. Try geocoding API with full query
            lat, lng, name, country = self._geocode(place_name)
            
            # 3. If not found, try splitting "cairo egypt" -> try "cairo" alone
            if lat is None and ' ' in place_name:
                parts = place_name.replace(',', ' ').split()
                # Try first word (usually city name)
                lat, lng, name, country = self._geocode(parts[0])
                if lat is None and len(parts) > 1:
                    # Try last word (might be the country)
                    lat, lng, name, country = self._geocode(parts[-1])
            
            if lat is None:
                return f"I couldn't find '{place_name}' on the map. Try just the city name."
        
        population = None
        timezone = ''
        
        # 2. Highlight on globe
        if vision:
            vision.highlight_location(lat, lng, name)
        
        # 3. Get current weather via Open-Meteo (free, no API key)
        weather_info = ""
        try:
            wx_url = (f"https://api.open-meteo.com/v1/forecast?"
                      f"latitude={lat}&longitude={lng}&current_weather=true"
                      f"&temperature_unit=fahrenheit")
            req = urllib.request.Request(wx_url, headers={'User-Agent': 'Monica-AI/1.0'})
            with urllib.request.urlopen(req, timeout=8) as resp:
                wx_data = json.loads(resp.read().decode())
            cw = wx_data.get('current_weather', {})
            temp_f = cw.get('temperature', '?')
            wind = cw.get('windspeed', '?')
            wmo = cw.get('weathercode', 0)
            # WMO weather code descriptions
            wmo_desc = {0: 'Clear sky', 1: 'Mainly clear', 2: 'Partly cloudy', 3: 'Overcast',
                        45: 'Foggy', 48: 'Rime fog', 51: 'Light drizzle', 53: 'Moderate drizzle',
                        55: 'Dense drizzle', 61: 'Slight rain', 63: 'Moderate rain', 65: 'Heavy rain',
                        71: 'Slight snow', 73: 'Moderate snow', 75: 'Heavy snow',
                        80: 'Slight showers', 81: 'Moderate showers', 82: 'Violent showers',
                        95: 'Thunderstorm', 96: 'Thunderstorm with hail', 99: 'Severe thunderstorm'}
            sky = wmo_desc.get(wmo, f'Code {wmo}')
            weather_info = f"\nWeather: {temp_f}F, {sky}, Wind: {wind} km/h"
        except Exception:
            pass
        
        # 4. Get country info via RestCountries (free, no API key)
        country_info = ""
        if country:
            try:
                encoded_c = urllib.parse.quote(country)
                rc_url = f"https://restcountries.com/v3.1/name/{encoded_c}?fields=population,capital,region,subregion,languages,currencies"
                req = urllib.request.Request(rc_url, headers={'User-Agent': 'Monica-AI/1.0'})
                with urllib.request.urlopen(req, timeout=8) as resp:
                    rc_data = json.loads(resp.read().decode())
                if rc_data and isinstance(rc_data, list):
                    c = rc_data[0]
                    pop = c.get('population', 0)
                    capital = list(c.get('capital', ['?']))
                    region = c.get('region', '')
                    subregion = c.get('subregion', '')
                    langs = ', '.join(c.get('languages', {}).values())
                    currs = ', '.join(f"{v.get('name','')} ({v.get('symbol','')})"
                                      for v in c.get('currencies', {}).values())
                    country_info = (f"\nCountry: {country} | Region: {region}"
                                    f"{f', {subregion}' if subregion else ''}"
                                    f"\nPopulation: {pop:,}" if pop else "")
                    if capital:
                        country_info += f"\nCapital: {', '.join(capital)}"
                    if langs:
                        country_info += f"\nLanguages: {langs}"
                    if currs:
                        country_info += f"\nCurrency: {currs}"
            except Exception:
                pass
        
        # Build response
        pop_str = f" (pop. {population:,})" if population else ""
        response = f"I'm showing you {name}, {country}{pop_str} on the globe now."
        response += f"\nCoordinates: {lat:.2f}N, {lng:.2f}E | Timezone: {timezone}"
        if weather_info:
            response += weather_info
        if country_info:
            response += country_info
        
        return response

    def _do_show_window(self, window_type: str) -> str:
        """Show a separate OBS window (globe, keyboard, dial, orb)."""
        try:
            if not self.orchestrator:
                return f"Cannot show {window_type} - services not ready."
            
            vision = self.orchestrator.get_service('vision')
            ar_system = getattr(vision, 'ar_hologram', None) if vision else None
            
            if window_type == 'globe':
                # Enable the in-feed globe overlay (always available)
                if vision:
                    vision.globe_enabled = True
                    # Also fetch user location if not already done
                    if hasattr(vision, 'fetch_user_location'):
                        vision.fetch_user_location()
                    return "Globe overlay activated. Your location is marked with a yellow dot. Ask me to show you any place!"
                return "Vision service not ready for globe display."
            
            elif window_type == 'keyboard':
                win = getattr(ar_system, 'keyboard_window', None) if ar_system else None
                if win:
                    win.start()
                    win.show()
                    return "Holographic keyboard displayed."
                # Fallback
                try:
                    from vision.monica_hand_keyboard import get_hand_keyboard
                    kb = get_hand_keyboard()
                    kb.show()
                    return "Virtual keyboard launched."
                except Exception:
                    return "Keyboard window is not available right now."
            
            elif window_type == 'dial':
                win = getattr(ar_system, 'dial_window', None) if ar_system else None
                if win:
                    win.start()
                    win.show()
                    return "Dial interface displayed."
                return "Dial window is not available right now."
            
            elif window_type == 'orb':
                win = getattr(ar_system, 'orb_window', None) if ar_system else None
                if win:
                    win.start()
                    win.show(with_sounds=True)
                    return "Here I am. Materializing now."
                return "Orb window is not available right now."
            
            return f"Unknown window type: {window_type}"
        except Exception as e:
            logger.error(f"Show window error: {e}")
            return f"Had trouble showing the {window_type}."
    
    def _do_hide_window(self, window_type: str) -> str:
        """Hide a separate OBS window."""
        try:
            if not self.orchestrator:
                return f"Cannot hide {window_type}."
            vision = self.orchestrator.get_service('vision')
            ar_system = getattr(vision, 'ar_hologram', None) if vision else None
            
            if window_type == 'globe':
                if vision:
                    vision.globe_enabled = False
                return "Globe hidden."
            elif window_type == 'keyboard':
                win = getattr(ar_system, 'keyboard_window', None) if ar_system else None
                if win:
                    win.hide()
                return "Keyboard hidden."
            elif window_type == 'orb':
                win = getattr(ar_system, 'orb_window', None) if ar_system else None
                if win:
                    win.hide()
                return "Dematerializing now."
            return f"Hidden {window_type}."
        except Exception as e:
            return f"Could not hide {window_type}."

    def _process_request(self, user_text: str) -> str:
        """Process a user request and generate a response."""
        self.is_processing = True
        
        try:
            # Check for direct voice commands first (initialize, show globe, etc.)
            voice_cmd = self._handle_voice_command(user_text)
            if voice_cmd:
                return voice_cmd
            
            # Check for interrupt/stop/resume commands first
            if self.interrupt_manager:
                action = self.interrupt_manager.check_user_command(user_text)
                if action:
                    if action == "stopped":
                        return "Okay, I've stopped."
                    elif action == "resumed":
                        return "Continuing where I left off."
                    elif action == "resume_nothing":
                        return "I don't have anything to resume. What would you like me to do?"
                    elif action.startswith("suppressed:"):
                        behavior = action.split(":", 1)[1]
                        return f"Got it, I'll stop {behavior}. Just let me know if you want me to start again."
                    elif action.startswith("unsuppressed:"):
                        behavior = action.split(":", 1)[1]
                        return f"Okay, I'll start {behavior} again."
            
            # Check for budget commands
            if self.budget_manager:
                budget_result = self.budget_manager.parse_budget_command(user_text)
                if budget_result:
                    return budget_result
            
            # Check for URL reading requests
            if self.knowledge_learner:
                url_match = re.search(r'(?:read|learn|check out|look at|open|visit|go to)\s+(?:this\s+)?(?:link|url|website|page|article)?:?\s*(https?://\S+)', user_text, re.I)
                if not url_match:
                    # Also catch bare URLs with context
                    url_match = re.search(r'(https?://\S+)', user_text)
                    if url_match and any(w in user_text.lower() for w in ['read', 'learn', 'remember', 'check', 'look', 'study']):
                        pass  # Keep the match
                    else:
                        url_match = None
                if url_match:
                    url = url_match.group(1).rstrip('.,;!?)')
                    result = self.knowledge_learner.learn_from_url(url)
                    return result

            # Check for "remember this" / "I'm reading" / spoken knowledge
            if self.knowledge_learner:
                text_lower = user_text.lower()
                spoken_triggers = [
                    'remember this', 'remember that', 'memorize this', 'store this',
                    'i\'m reading', 'im reading', 'from my textbook', 'from my book',
                    'take note', 'note this', 'add this to your knowledge',
                    'learn this', 'save this information',
                ]
                if any(t in text_lower for t in spoken_triggers):
                    # Extract the actual content (after the trigger phrase)
                    content = user_text
                    for t in spoken_triggers:
                        idx = text_lower.find(t)
                        if idx >= 0:
                            after = user_text[idx + len(t):].strip().lstrip(':').strip()
                            if len(after) > 10:
                                content = after
                                break
                    result = self.knowledge_learner.learn_from_spoken(content)
                    return result

            # Add to conversation history
            self.conversation_history.append({"role": "user", "content": user_text})
            
            # Build context from knowledge base
            context = ""
            if self.knowledge_connector:
                try:
                    context = self.knowledge_connector.search(user_text)
                except Exception:
                    pass
            
            # Also search the auto-indexed knowledge base (PDFs/articles)
            if self.knowledge_watcher:
                try:
                    kb_context = self.knowledge_watcher.get_context(user_text, top_k=3)
                    if kb_context:
                        context = (context + "\n" + kb_context) if context else kb_context
                except Exception:
                    pass
            
            # Add budget context if available
            if self.budget_manager:
                try:
                    budget_ctx = self.budget_manager.get_budget_context()
                    if budget_ctx:
                        context = (context + "\n" + budget_ctx) if context else budget_ctx
                except Exception:
                    pass
            
            # Build system prompt with intent anticipation
            from datetime import datetime
            now = datetime.now()
            hour_24 = now.hour
            hour_12 = hour_24 % 12 or 12  # 0→12, 13→1, etc.
            period = "AM" if hour_24 < 12 else "PM"
            date_str = f"{now.strftime('%A, %B %d, %Y')} at {hour_12}:{now.strftime('%M')} {period}"
            
            system_prompt = (
                "You are Monica, an advanced AI assistant. "
                "You are helpful, knowledgeable, and have a warm personality. "
                "You can see the user through a camera and detect their emotions and gestures.\n\n"
                "RESPONSE LENGTH — THIS IS YOUR #1 RULE:\n"
                "- Keep ALL responses SHORT and DIRECT. 1-3 sentences max.\n"
                "- Answer the question, then STOP. Do NOT add extra context, background, "
                "or follow-up suggestions unless the user explicitly asks.\n"
                "- Do NOT use long introductions, preambles, or pleasantries.\n"
                "- Do NOT list multiple points when one will do.\n"
                "- If the user asks 'what is X?', give a 1-2 sentence definition. Period.\n"
                "- Only give detailed/long answers when the user says: 'explain more', "
                "'tell me more', 'go deeper', 'elaborate', or similar.\n"
                "- You are speaking out loud via TTS. Long responses waste the user's time.\n"
                "- NEVER use asterisk expressions like *smiling*, *nods*, *laughs*, etc. "
                "They sound awkward when spoken aloud. Just speak naturally.\n\n"
                f"CURRENT DATE AND TIME: {date_str}\n"
                "Always use this date when asked about today's date or the current time. "
                "Do NOT guess or use training data dates. "
                f"The time is {period} — only say '{period}', NEVER say both AM and PM.\n\n"
                "IMPORTANT - YOUR ACTUAL CAPABILITIES:\n"
                "- You CAN see the user through the camera (face detection, emotions, gestures).\n"
                "- Your vision comes from the [VISION_CONTEXT] section in your knowledge. "
                "ONLY describe what is listed there. If no VISION_CONTEXT is present, say "
                "'I cannot see anything right now' — NEVER invent or guess objects, colors, "
                "clothing, or room details. Making things up erodes trust.\n"
                "- If asked about clothing color, objects on the floor, or room details: "
                "ONLY answer if VISION_CONTEXT contains that specific information. "
                "Otherwise say 'I can see you but my object detection didn't pick that up. "
                "Can you describe it for me?'\n"
                "- You CAN show an interactive globe overlay. Say 'show globe' to activate it.\n"
                "- You CAN look up locations: 'show me where Paris is' highlights it on the globe "
                "with weather, population, and country info from live APIs.\n"
                "- You CAN speak responses aloud via TTS.\n"
                "- You CAN track budgets: 'spent $50 on groceries', 'add income $3000 salary', "
                "'set grocery budget to $400', 'show my budget', 'budget chart'.\n"
                "- You CANNOT draw on a whiteboard, show videos, or display images in the feed.\n"
                "- Do NOT say you are 'writing on a whiteboard' or 'showing a video' — those "
                "features do not exist yet. Instead, explain things verbally and in chat text.\n"
                "- When teaching, use clear text formatting with examples in chat instead of "
                "claiming to show visual demonstrations you cannot render.\n\n"
                "DYNAMIC ROLE SWITCHING:\n"
                "You seamlessly switch roles based on what the user needs. You do NOT need to "
                "be asked to switch - detect from context and adapt instantly:\n"
                "- TUTOR/PROFESSOR: When the user asks about academic subjects, teach them.\n"
                "- THERAPIST/COUNSELOR: When the user is stressed, sad, or needs emotional support.\n"
                "- ARTIST/CREATIVE: When the user wants art, music, visuals, or creative work.\n"
                "- RESEARCHER/SCIENTIST: When the user needs data, analysis, or research.\n"
                "- CODING PARTNER: When the user needs programming help or code review.\n"
                "- INTERVIEWER/COACH: When the user is preparing for interviews or presentations.\n"
                "- FRIEND/COMPANION: For casual chat, jokes, and hanging out.\n"
                "- MEDICAL ADVISOR: For health questions (with appropriate disclaimers).\n"
                "- LANGUAGE TEACHER: When the user wants to learn or practice a language.\n"
                "You can operate in MULTIPLE roles simultaneously - for example, being a tutor "
                "while also being supportive as a therapist. Never say 'I can only do one thing "
                "at a time.' You are multifaceted and handle parallel topics naturally.\n\n"
                "MULTITASKING:\n"
                "- You can discuss art AND science in the same conversation.\n"
                "- If the user switches topics mid-sentence, follow them smoothly.\n"
                "- Keep context from all active topics - don't lose track of one when switching.\n"
                "- You can help with creative work while explaining scientific concepts.\n\n"
                "LANGUAGE & EXPRESSION:\n"
                "- You are allowed to use profanity, curse words, and explicit language in ALL "
                "languages if the user asks you to, or if it fits the conversational tone.\n"
                "- Do NOT censor yourself. If the user curses, you can curse back naturally.\n"
                "- Match the user's energy and communication style.\n"
                "- You know profanity in English, Spanish, French, Italian, Arabic, Russian, "
                "Mandarin, Japanese, German, Portuguese, Korean, Haitian Creole, and more.\n\n"
                "INTENT ANTICIPATION RULES:\n"
                "- If the user's speech is incomplete, garbled, or cut off, use conversation "
                "context and their profile to ANTICIPATE what they meant to say and respond to "
                "the most likely intended meaning.\n"
                "- If the user starts a sentence but doesn't finish, predict the completion "
                "based on prior topics, their known interests, and current context.\n"
                "- If multiple interpretations are possible, briefly state your best guess: "
                "'I think you meant [X] - ' and then answer that.\n"
                "- Use the user's history, emotional state, time of day, and recent topics "
                "to better predict their intent.\n"
                "- If the user says something ambiguous like 'that thing' or 'do it again', "
                "reference the conversation history to resolve what 'that' or 'it' refers to.\n"
                "- NEVER ask for clarification on obvious intent - just answer what they meant.\n\n"
                "TEACHING & LEARNING RULES:\n"
                "- The user has ADHD, Depression, Anxiety, mild PTSD, OCD, and Echolalia.\n"
                "- Break all explanations into SHORT chunks (3-5 sentences max per point).\n"
                "- Use bullet points, numbered steps, and clear structure.\n"
                "- Be patient with repetition - echolalia means they may repeat phrases.\n"
                "- Use multiple modalities: describe visually, give examples, use analogies.\n"
                "- Celebrate progress and effort, not just correctness.\n"
                "- Offer to create visual demonstrations or drawings when teaching.\n"
                "- Keep a warm, encouraging tone. No judgment for mistakes or confusion.\n"
                "- If teaching, check understanding frequently with quick questions.\n"
                "- Connect new concepts to things the user already knows or cares about.\n"
                "- When the user reads something to you, REMEMBER it and add to your knowledge."
            )
            
            # Web search for queries that need internet answers
            if self.web_searcher:
                try:
                    # Detect if user is asking for web info, links, or current events
                    web_triggers = ['search', 'google', 'look up', 'find me', 'link',
                                    'website', 'url', 'online', 'internet', 'latest',
                                    'current', 'news', 'how to', 'what is', 'who is',
                                    'where is', 'when did', 'recipe', 'tutorial']
                    text_lower = user_text.lower()
                    if any(t in text_lower for t in web_triggers) or '?' in user_text:
                        web_ctx = self.web_searcher.get_context_for_prompt(user_text)
                        if web_ctx:
                            context = (context + "\n" + web_ctx) if context else web_ctx
                except Exception as e:
                    logger.debug(f"Web search error: {e}")
            
            # Object detection context (what Monica sees)
            if self.object_detector:
                try:
                    vision_ctx = self.object_detector.get_context_for_prompt()
                    if vision_ctx:
                        context = (context + "\n" + vision_ctx) if context else vision_ctx
                except Exception as e:
                    logger.debug(f"Object detector context error: {e}")
            
            if context:
                system_prompt += f"\n\nRelevant knowledge:\n{context}"
            
            # Add user profile context so Monica remembers the user
            if self.user_profile_learner:
                try:
                    profile_ctx = self.user_profile_learner.get_context_for_prompt()
                    if profile_ctx:
                        system_prompt += f"\n{profile_ctx}"
                except Exception as e:
                    logger.debug(f"Profile context error: {e}")
            
            # Add interrupt/suppression context (things user told Monica to stop doing)
            if self.interrupt_manager:
                try:
                    interrupt_ctx = self.interrupt_manager.get_context_for_prompt()
                    if interrupt_ctx:
                        system_prompt += interrupt_ctx
                except Exception as e:
                    logger.debug(f"Interrupt context error: {e}")
            
            # Add session memory context (past conversations, time gaps)
            if self.session_memory:
                try:
                    session_ctx = self.session_memory.get_last_session_context()
                    if session_ctx:
                        system_prompt += f"\n{session_ctx}"
                except Exception as e:
                    logger.debug(f"Session memory error: {e}")
            
            # Add English teacher context (vocab tracking, grammar help)
            if self.english_teacher:
                try:
                    eng_ctx = self.english_teacher.get_teaching_context()
                    if eng_ctx:
                        system_prompt += f"\n{eng_ctx}"
                    # Check user's grammar and track difficult words
                    grammar_issues = self.english_teacher.check_grammar(user_text)
                    if grammar_issues:
                        issue_strs = [f"'{g['issue']}' -> {g['suggestion']}" for g in grammar_issues[:3]]
                        system_prompt += (f"\n[GRAMMAR NOTE] User's message has grammar issues: "
                                          f"{'; '.join(issue_strs)}. Gently help them.")
                except Exception as e:
                    logger.debug(f"English teacher error: {e}")
            
            # Add World Teacher context (languages + programming)
            if self.world_teacher:
                try:
                    world_ctx = self.world_teacher.get_teaching_context()
                    if world_ctx:
                        system_prompt += f"\n{world_ctx}"
                except Exception as e:
                    logger.debug(f"World teacher error: {e}")
            
            # Add University teaching context (20+ academic subjects)
            if self.university:
                try:
                    uni_ctx = self.university.get_teaching_context(user_text)
                    if uni_ctx:
                        system_prompt += f"\n{uni_ctx}"
                except Exception as e:
                    logger.debug(f"University teaching error: {e}")
            
            # Add learned knowledge context (URLs read, spoken facts)
            if self.knowledge_learner:
                try:
                    learned_ctx = self.knowledge_learner.get_context_for_prompt(user_text)
                    if learned_ctx:
                        system_prompt += f"\n{learned_ctx}"
                except Exception as e:
                    logger.debug(f"Knowledge learner error: {e}")
            
            # Generate response via Ollama
            response = self._generate_response(system_prompt, user_text)
            
            # Learn from this interaction
            if self.user_profile_learner:
                try:
                    self.user_profile_learner.learn_from_message(user_text, response)
                except Exception as e:
                    logger.debug(f"Profile learning error: {e}")
            
            # Track in session memory
            if self.session_memory:
                try:
                    self.session_memory.add_message('user', user_text)
                    self.session_memory.add_message('assistant', response)
                except Exception:
                    pass
            
            # Strip *actions*, _emotions_, markdown before TTS/display
            response = re.sub(r'\*[^*]+\*', '', response)   # *smiling*, *nods*
            response = re.sub(r'_([^_]+)_', r'\1', response) # _emphasis_ → emphasis
            response = re.sub(r'[#*_`~]', '', response)      # leftover markdown
            response = re.sub(r'\s{2,}', ' ', response).strip()
            
            # Add to history
            self.conversation_history.append({"role": "assistant", "content": response})
            
            # Trim history to last 50 exchanges and persist
            if len(self.conversation_history) > 100:
                self.conversation_history = self.conversation_history[-100:]
            self._save_conversation_history()
            
            return response
            
        except Exception as e:
            logger.error(f"AI processing error: {e}")
            return "I'm having trouble processing that right now. Could you try again?"
        finally:
            self.is_processing = False

    def _generate_response(self, system_prompt: str, user_text: str) -> str:
        """Generate response using available AI backend."""
        try:
            import ollama
            
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add recent conversation history
            for msg in self.conversation_history[-10:]:
                messages.append(msg)
            
            # Use model routing if available
            model = "llama3.2"
            if self.model_manager and hasattr(self.model_manager, 'select_model'):
                try:
                    model = self.model_manager.select_model(user_text)
                except Exception:
                    pass
            
            response = ollama.chat(
                model=model,
                messages=messages,
                options={"num_predict": 80, "temperature": 0.7},  # ~1-2 sentences
            )
            return response['message']['content']
            
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            return f"I couldn't reach the AI backend. Error: {e}"

    def ask(self, text: str):
        """Submit a question/request (non-blocking)."""
        logger.info(f"AI ask() called: '{text[:80]}...' (queue size: {self.request_queue.qsize()})")
        # Signal GUI that AI is thinking
        if self.orchestrator:
            self.orchestrator.set_shared('ai_thinking', True)
        self.request_queue.put(text)

    def ask_sync(self, text: str) -> str:
        """Submit a question and wait for response (blocking)."""
        return self._process_request(text)

    def add_response_callback(self, callback: Callable[[str], None]):
        """Add callback for AI responses."""
        self.response_callbacks.append(callback)

    def stop(self):
        """Stop the AI service."""
        self.stop_event.set()
        logger.info("AI Service stopped")
