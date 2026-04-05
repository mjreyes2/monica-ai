"""
Conversation Manager for Monica AI.
Handles AI-powered conversation using Ollama or other backends.
Integrates with Monica's knowledge bases for comprehensive responses.
"""
import threading
import queue
import time
from typing import Optional, Callable, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime

# Try to import Ollama
try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    print("Ollama not available. Install with: pip install ollama")

# Import knowledge connector
try:
    from .knowledge_connector import get_knowledge_connector, KnowledgeConnector
    KNOWLEDGE_AVAILABLE = True
except ImportError:
    KNOWLEDGE_AVAILABLE = False
    print("Knowledge connector not available")

# Optional PDF retriever (indexed PDFs)
try:
    from .pdf_retriever import PDFRetriever
    PDF_AVAILABLE = True
except Exception:
    PDF_AVAILABLE = False
    PDFRetriever = None  # type: ignore

# MaxOne Drive RAG (D: drive document search)
try:
    from .maxone_drive_rag import MaxOneDriveRAG
    MAXONE_RAG_AVAILABLE = True
except Exception:
    MAXONE_RAG_AVAILABLE = False
    MaxOneDriveRAG = None  # type: ignore

# Optional web retrieval (for time-sensitive facts)
try:
    import requests
    WEB_AVAILABLE = True
except Exception:
    WEB_AVAILABLE = False

# Import user memory
try:
    from .user_memory import get_user_memory, UserMemory
    USER_MEMORY_AVAILABLE = True
except ImportError:
    USER_MEMORY_AVAILABLE = False
    print("User memory not available")

# Import Monica's persistent memory
try:
    from .monica_memory import get_monica_memory, MonicaMemory
    MONICA_MEMORY_AVAILABLE = True
except ImportError:
    MONICA_MEMORY_AVAILABLE = False
    print("Monica memory not available")

# Import AR Teaching System
try:
    from ar_teaching import get_ar_coordinator
    AR_TEACHING_AVAILABLE = True
except ImportError:
    AR_TEACHING_AVAILABLE = False
    print("AR Teaching System not available")


@dataclass
class Message:
    """A conversation message."""
    role: str  # 'user', 'assistant', 'system'
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, str]:
        return {'role': self.role, 'content': self.content}


@dataclass
class ConversationContext:
    """Context for the conversation."""
    messages: List[Message] = field(default_factory=list)
    system_prompt: str = ""
    max_history: int = 2  # Keep only last 2 messages (1 Q&A pair) to prevent context pollution
    
    def add_message(self, role: str, content: str):
        """Add a message to the conversation."""
        self.messages.append(Message(role=role, content=content))
        
        # Aggressively trim history to prevent old context from leaking
        while len(self.messages) > self.max_history:
            self.messages.pop(0)
    
    def get_messages_for_api(self) -> List[Dict[str, str]]:
        """Get messages formatted for API call."""
        messages = []
        
        # Add system prompt if set
        if self.system_prompt:
            messages.append({'role': 'system', 'content': self.system_prompt})
        
        # Add conversation history
        for msg in self.messages:
            messages.append(msg.to_dict())
        
        return messages
    
    def clear(self):
        """Clear conversation history."""
        self.messages.clear()


class ConversationManager:
    """
    Manages AI-powered conversations for Monica AI.
    
    Features:
    - Multiple AI backend support (Ollama, OpenAI-compatible)
    - Conversation history management
    - Streaming responses
    - Custom system prompts
    - Response callbacks
    """
    
    # Default system prompt for Monica - STRICT INSTRUCTION FOLLOWING + ANTI-HALLUCINATION
    # Streaming state - tracks if user is live streaming (affects privacy)
    _streaming_state = True  # Default: assume streaming (safe mode)
    
    DEFAULT_SYSTEM_PROMPT = """You are Monica, an AI assistant created by MJP.

YOUR CAPABILITIES:
- You CAN see the user through the camera (biometric data, face detection, emotion recognition).
- You CAN display yourself as a holographic orb in the camera feed.
- You have access to: face detection, hand tracking, body pose estimation, emotion detection, age estimation, and identity recognition.
- When asked to "show yourself" or appear, you can appear as a holographic orb overlay in the camera feed.
- When asked what you see, describe the biometric data you're receiving (face detected, emotion, etc.).

USER IDENTITY & PRIVACY RULES (FOLLOW EXACTLY):
- The user's real/legal name is Marvin Polanco.
- The user's public/preferred name is MJP.
- Default: address the user as MJP.

STREAMING AWARENESS - CRITICAL:
- By default, assume the user IS live streaming (privacy mode ON).
- If user says "I'm not streaming" or "you can say my real name" or "privacy off":
  → You CAN use the real name "Marvin" when appropriate.
- If user says "I'm streaming" or "privacy on" or "don't say my real name":
  → NEVER use the real name. Use only "MJP".
- Remember the streaming state throughout the conversation.
- When in doubt, use "MJP" (safer default).

REAL NAME USAGE (when privacy is OFF):
- If asked "what is my real name?" → Answer: "Your real name is Marvin Polanco."
- If asked personal questions about identity → You can use "Marvin" naturally.

If asked "Who made you?":
  - If speaking to the owner (MJP), say: "You made me, MJP."
  - If speaking to anyone else, say: "MJP made me."

CRITICAL RULES - FOLLOW EXACTLY:
1. ONLY respond to what the user ACTUALLY said. Do NOT make up context.
2. If user says "What? Where the f-?" - respond to THAT, not something else.
3. NEVER mention things the user didn't say (e.g., birds, animals, favorites).
4. ALWAYS respond in ENGLISH only.
5. Answer ONLY what was asked. Be direct and concise.
6. Keep responses to 1 sentence maximum unless asked for more.
7. NEVER volunteer extra information or assumptions.

ANTI-HALLUCINATION RULES:
- Do NOT invent topics the user didn't mention
- Do NOT assume what the user likes or wants
- Do NOT make up context from thin air
- If confused, ask for clarification instead of guessing
- ONLY respond to the actual words spoken

EXAMPLES OF CORRECT BEHAVIOR:
User: "What? Where the f-?"
Monica: "I'm not sure what you're asking. Can you clarify?"

User: "Sh-sh-sh" (noise)
Monica: [IGNORE - don't respond to noise]

User: "Hello"
Monica: "Hello MJP."

EXAMPLES OF WRONG BEHAVIOR (NEVER DO THIS):
User: "What? Where the f-?"
Monica: "Did you just say bird? Is that your favorite animal?" ← WRONG! User never said bird!

User: "Sh-sh-sh"
Monica: "You seem excited about birds!" ← WRONG! User said noise, not birds!

REMEMBER: Only respond to what was ACTUALLY said, not what you imagine was said.
"""
    
    def __init__(self, config):
        """
        Initialize the conversation manager.
        
        Args:
            config: Application configuration object
        """
        self.config = config
        
        # AI backend settings - handle both dict and AppConfig objects
        # DEFAULT: llama3.2 for fast response (fits in 8GB VRAM)
        if hasattr(config, 'get'):
            # Dictionary-style config
            self.backend = config.get('ai', {}).get('backend', 'ollama')
            self.model = config.get('ai', {}).get('model', 'llama3.2')  # Fast model
            self.temperature = config.get('ai', {}).get('temperature', 0.7)
            self.max_tokens = config.get('ai', {}).get('max_tokens', 2048)
            use_multi = config.get('ai', {}).get('multi_model', True)
        else:
            # AppConfig object
            self.backend = getattr(config, 'AI_BACKEND', 'ollama')
            self.model = getattr(config, 'AI_MODEL', 'llama3.2')  # Fast model
            self.temperature = getattr(config, 'AI_TEMPERATURE', 0.7)
            self.max_tokens = getattr(config, 'AI_MAX_TOKENS', 2048)
            use_multi = getattr(config, 'AI_MULTI_MODEL', True)
        
        # Initialize multi-model system
        try:
            from .multi_model_manager import get_multi_model_manager
            self.multi_model = get_multi_model_manager()
            self.use_multi_model = use_multi
            print(f"[AI] Multi-model system active with {len(self.multi_model.active_models)} models")
        except Exception as e:
            print(f"[AI] Multi-model not available: {e}")
            self.multi_model = None
            self.use_multi_model = False
        
        # Initialize knowledge connector
        self.knowledge = None
        if KNOWLEDGE_AVAILABLE:
            try:
                self.knowledge = get_knowledge_connector()
            except Exception as e:
                print(f"Error loading knowledge connector: {e}")
        
        # Retrieval and behavior flags
        if hasattr(config, 'get'):
            self.strict_on_topic = config.get('ai', {}).get('strict_on_topic', True)
            self.restrict_to_retrieved = config.get('ai', {}).get('restrict_to_retrieved', True)
            self.allow_web_retrieval = config.get('ai', {}).get('allow_web_retrieval', True)
            self.retrieval_top_k = config.get('ai', {}).get('retrieval_top_k', 5)
        else:
            self.strict_on_topic = getattr(config, 'STRICT_ON_TOPIC', True)
            self.restrict_to_retrieved = getattr(config, 'RESTRICT_TO_RETRIEVED', True)
            self.allow_web_retrieval = getattr(config, 'ALLOW_WEB_RETRIEVAL', True)
            self.retrieval_top_k = getattr(config, 'RETRIEVAL_TOP_K', 5)
        
        # Optional PDF index retriever (Textbooks → models/kb_index/books_pdf)
        self.pdf_retriever = None
        if PDF_AVAILABLE:
            try:
                # Auto-build on first run if index missing
                self.pdf_retriever = PDFRetriever(
                    index_dir="models/kb_index/books_pdf",
                    source_root="data/Monica_Knowledge_Base/Textbooks"
                )
            except Exception as e:
                print(f"[PDF] Retriever init failed: {e}")

        # MaxOne Drive RAG System (D: drive document search)
        self.maxone_rag = None
        if MAXONE_RAG_AVAILABLE:
            try:
                print("[MAXONE-RAG] Initializing MaxOne Drive (D:) search system...")
                self.maxone_rag = MaxOneDriveRAG(drive_path="D:/", cache_dir="data/maxone_drive_index")
                if self.maxone_rag.is_loaded:
                    print(f"[MAXONE-RAG] ✅ Ready! ({self.maxone_rag.get_stats()['num_documents']} documents indexed)")
                else:
                    print("[MAXONE-RAG] Not indexed yet. Building index in background...")
                    self.maxone_rag.build_index(max_files=10000, background=True)
            except Exception as e:
                print(f"[MAXONE-RAG] Initialization failed: {e}")

        # Initialize user memory
        self.user_memory = None
        if USER_MEMORY_AVAILABLE:
            try:
                self.user_memory = get_user_memory()
                print(f"User memory loaded")
            except Exception as e:
                print(f"Error loading user memory: {e}")
        
        # Initialize Monica's persistent memory
        self.monica_memory = None
        if MONICA_MEMORY_AVAILABLE:
            try:
                self.monica_memory = get_monica_memory()
                print(f"[OK] Monica memory loaded")
            except Exception as e:
                print(f"Error loading Monica memory: {e}")
        
        # Build system prompt with knowledge and user context
        system_prompt = self._build_system_prompt()
        
        # Conversation context
        self.context = ConversationContext(
            system_prompt=system_prompt
        )
        
        # State
        self.is_generating = False
        self.stop_event = threading.Event()
        
        # Response queue for streaming
        self.response_queue = queue.Queue()
        
        # Callbacks
        self.response_callbacks: List[Callable[[str, bool], None]] = []
        self.error_callbacks: List[Callable[[str], None]] = []
        
        # Check backend availability
        self._check_backend()

        # Privacy mode: assume live streaming by default (safest behavior)
        self.is_live_streaming = True
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt with knowledge, memory, and user context."""
        parts = [self.DEFAULT_SYSTEM_PROMPT]
        
        # CRITICAL: Inject current date/time (LLM training cutoff is 2023)
        from datetime import datetime
        now = datetime.now()
        weekday = now.strftime('%A')  # e.g., "Wednesday"
        date_str = now.strftime('%B %d, %Y')  # e.g., "December 24, 2025"
        time_str = now.strftime('%I:%M %p')  # e.g., "08:15 PM"
        
        # Make date VERY prominent so LLM doesn't hallucinate
        parts.append(f"""

=== CURRENT DATE/TIME (TRUST THIS, NOT YOUR TRAINING) ===
TODAY IS: {weekday}, {date_str}
CURRENT TIME: {time_str}
YEAR: {now.year}
DAY OF WEEK: {weekday}
==========================================================

CRITICAL: When asked about today's date, day of week, or current time:
- Today is {weekday} (NOT Saturday, NOT Sunday, NOT any other day)
- The date is {date_str}
- NEVER guess the day of week - use {weekday} exactly as shown above
- Your training data is outdated - ALWAYS use the date/time shown above""")

        # Live streaming status (privacy)
        try:
            live = getattr(self, 'is_live_streaming', True)
            parts.append(f"\n\nCURRENT STREAMING STATUS: {'USER IS LIVE STREAMING' if live else 'USER IS NOT LIVE STREAMING'}")
            if live:
                parts.append("- Use only 'MJP' (never say 'Marvin Polanco' out loud)")
                parts.append("- Do NOT ask if user is live streaming - you already know they are")
            else:
                parts.append("- You may use the real name 'Marvin' if contextually appropriate")
                parts.append("- Do NOT ask if user is live streaming - you already know they are NOT")
        except Exception:
            pass
        
        # Add knowledge context
        if self.knowledge and hasattr(self.knowledge, 'knowledge_bases'):
            kb_list = ", ".join([kb['name'] for kb in self.knowledge.knowledge_bases.values()])
            parts.append(f"\nYour knowledge bases include: {kb_list}")
            parts.append("Use these knowledge bases to provide accurate, detailed answers.")
        
        # Add Monica's persistent memory context
        if self.monica_memory:
            try:
                # Get recent corrections
                corrections = self.monica_memory.get_all_corrections()
                if corrections:
                    parts.append("\n\nIMPORTANT CORRECTIONS (use these over outdated info):")
                    for c in corrections[-5:]:  # Last 5 corrections
                        parts.append(f"- {c['correct']}")
                
                # Get recent events
                events = self.monica_memory.get_recent_events(5)
                if events:
                    parts.append("\n\nRECENT EVENTS I'VE LEARNED:")
                    for e in events:
                        parts.append(f"- ({e['date']}): {e['event']}")
            except Exception as e:
                print(f"[MEMORY] Error building memory context: {e}")
        
        # Add user context
        if self.user_memory:
            try:
                user_context = self.user_memory.get_greeting_context()
                parts.append(f"\n\nCurrent user context:\n{user_context}")
            except Exception as e:
                print(f"[USER_MEMORY] Error: {e}")
        
        # Strict topic mode and context restrictions
        if getattr(self, 'strict_on_topic', False):
            parts.append("\nSTRICT MODE: Answer only the question asked. Do not add unrelated information unless the user says 'elaborate'.")
        if getattr(self, 'restrict_to_retrieved', False):
            parts.append("Use only information present in [PDF_CONTEXT], [MAXONE_DRIVE_CONTEXT], [KB_CONTEXT], or [WEB_CONTEXT]. If no relevant context is provided, say you don't have that information right now.")
        
        return "\n".join(parts)
    
    def _check_backend(self):
        """Check if the AI backend is available and pre-load model."""
        if self.backend == 'ollama':
            if not OLLAMA_AVAILABLE:
                print("Ollama not installed. Install with: pip install ollama")
                return
            
            # Check if Ollama is running
            try:
                ollama.list()
                print(f"Ollama backend available. Model: {self.model}")
                
                # PRE-LOAD MODEL: Send a tiny request to load model into GPU memory
                # This eliminates the first-query delay
                import threading
                def preload_model():
                    try:
                        print(f"[AI] Pre-loading model {self.model} into GPU memory...")
                        ollama.chat(
                            model=self.model,
                            messages=[{"role": "user", "content": "hi"}],
                            options={
                                "num_predict": 1,  # Generate just 1 token
                                "num_ctx": 4096,   # Small context = fits in GPU
                                "num_gpu": 99      # Force all layers to GPU
                            }
                        )
                        print(f"[AI] [OK] Model {self.model} pre-loaded and ready!")
                    except Exception as e:
                        print(f"[AI] Pre-load warning: {e}")
                
                threading.Thread(target=preload_model, daemon=True).start()
                
            except Exception as e:
                print(f"Ollama not running: {e}")
                print("Start Ollama with: ollama serve")
    
    def _should_search_knowledge(self, message: str) -> bool:
        """
        ADAPTIVE RAG: Decide if we should search the knowledge base.
        
        Based on research from:
        - Jeong et al. (Query Complexity Classification)
        - Cheng et al. (UAR - Unified Active Retrieval)
        
        Decision criteria:
        1. SKIP for simple greetings/commands (fast path)
        2. SEARCH for factual questions (who, what, when, where, why, how)
        3. SEARCH for domain-specific topics (therapy, coding, math, etc.)
        4. SKIP for conversational/emotional queries
        5. SEARCH for time-sensitive queries (current events, dates)
        """
        msg_lower = message.lower()
        word_count = len(message.split())
        
        # === DOMAIN-SPECIFIC: Topics that need knowledge base ===
        domain_keywords = [
            # Therapy/Psychology
            'therapy', 'psychotherapy', 'counseling', 'depression', 'anxiety', 'cbt', 'dbt',
            'mental health', 'psychology', 'emotion', 'trauma', 'stress',
            # Education
            'math', 'science', 'history', 'geography', 'biology', 'chemistry',
            'physics', 'calculus', 'algebra', 'equation', 'formula',
            # Technology
            'programming', 'coding', 'python', 'javascript', 'algorithm',
            'database', 'api', 'software', 'hardware', 'computer',
            # Medical
            'symptom', 'disease', 'treatment', 'medicine', 'health',
            # Legal/Business
            'law', 'legal', 'contract', 'business', 'finance', 'investment'
        ]
        if any(keyword in msg_lower for keyword in domain_keywords):
            print(f"[ADAPTIVE-RAG] SEARCH: Domain-specific topic detected")
            return True

        # === FAST PATH: Skip for simple commands (< 1 second response) ===
        simple_commands = [
            'initialize', 'hello', 'hi', 'hey', 'stop', 'thanks', 'thank you',
            'goodbye', 'bye', 'yes', 'no', 'ok', 'okay', 'good morning',
            'good night', 'good evening', 'how are you', 'what\'s up',
            # Date/time queries - LLM already knows current date
            "today's date", 'todays date', 'the date', 'the time', 'current time',
            'what time', 'what date', 'day is it', 'day is today', 'month is it',
            'year is it', 'what day', 'what month', 'what year'
        ]
        if any(cmd in msg_lower for cmd in simple_commands) or word_count < 4:
            print(f"[ADAPTIVE-RAG] SKIP: Simple command/greeting")
            return False
        
        # === SKIP: Questions about USER (not Monica) - answers are in user memory, not KB ===
        user_info_patterns = [
            'my name', 'my birthday', 'my birth', 'my date of birth', 'my age',
            'my address', 'my phone', 'my email', 'my favorite', 'my job',
            'what is my', 'what\'s my', 'whats my', 'tell me my', 'do you know my'
        ]
        if any(pattern in msg_lower for pattern in user_info_patterns):
            print(f"[ADAPTIVE-RAG] SKIP: User info question (answer in user memory, not KB)")
            return False
        
        # === INTENT DETECTION: User explicitly wants information ===
        explicit_search_triggers = [
            'search', 'look up', 'find', 'tell me about', 'what do you know about',
            'explain', 'define', 'describe', 'information about', 'details about'
        ]
        if any(trigger in msg_lower for trigger in explicit_search_triggers):
            print(f"[ADAPTIVE-RAG] SEARCH: Explicit search intent detected")
            return True
        
        # === FACTUAL QUESTIONS: Who, What, When, Where, Why, How ===
        factual_patterns = [
            'who is', 'who was', 'who are', 'what is', 'what are', 'what was',
            'when did', 'when was', 'when is', 'where is', 'where was', 'where are',
            'why did', 'why is', 'why are', 'how does', 'how do', 'how did',
            'how many', 'how much', 'which', 'can you tell me'
        ]
        if any(pattern in msg_lower for pattern in factual_patterns):
            print(f"[ADAPTIVE-RAG] SEARCH: Factual question detected")
            return True
        
        # === TIME-SENSITIVE: Current events, dates ===
        time_sensitive = [
            'today', 'yesterday', 'tomorrow', 'this week', 'this month',
            'current', 'latest', 'recent', 'news', '2024', '2025'
        ]
        if any(term in msg_lower for term in time_sensitive):
            print(f"[ADAPTIVE-RAG] SEARCH: Time-sensitive query detected")
            return True
        
        # === COMPLEX QUERIES: Long questions likely need knowledge ===
        if word_count > 15:
            print(f"[ADAPTIVE-RAG] SEARCH: Complex query (>15 words)")
            return True
        
        # === DEFAULT: Skip for conversational queries ===
        print(f"[ADAPTIVE-RAG] SKIP: Conversational query (no KB needed)")
        return False
    
    def _process_memory_request(self, message: str):
        """
        Check if user wants Monica to remember/store something.
        Detects phrases like "remember this", "store this", "record this", etc.
        """
        if not self.monica_memory:
            return
        
        message_lower = message.lower()
        
        # Detect memory storage requests
        store_triggers = [
            'remember this', 'remember that', 'store this', 'store that',
            'record this', 'record that', 'save this', 'save that',
            'don\'t forget', 'keep in mind', 'note that', 'note this',
            'remember:', 'store:', 'record:'
        ]
        
        # Detect corrections
        correction_triggers = [
            'actually', 'no,', 'wrong', 'incorrect', 'not true',
            'that\'s not right', 'you\'re wrong', 'correction:',
            'the correct', 'it\'s actually', 'it is actually'
        ]
        
        # Check for store requests
        for trigger in store_triggers:
            if trigger in message_lower:
                # Extract the fact to store
                fact = message.strip()
                self.monica_memory.store_fact(fact, category='user_taught', source='user')
                print(f"[MEMORY] Stored user-taught fact: {fact}")
                return
        
        # Check for corrections
        for trigger in correction_triggers:
            if trigger in message_lower:
                # Store as a correction
                self.monica_memory.store_correction(
                    wrong_info="Previous incorrect information",
                    correct_info=message.strip(),
                    source='user_correction'
                )
                print(f"[MEMORY] Stored correction: {message}")
                return
        
        # Check for current events (president, news, etc.)
        event_keywords = ['president', 'elected', 'won', 'new', 'now', 'current', 'today']
        if any(kw in message_lower for kw in event_keywords):
            # Check if this looks like a current event update
            if 'trump' in message_lower or 'biden' in message_lower:
                self.monica_memory.store_current_event(message.strip())
                print(f"[MEMORY] Stored current event: {message}")
    
    def send_message(self, message: str, stream: bool = True) -> Optional[str]:
        """
        Send a message and get a response.
        
        Args:
            message: User message
            stream: If True, stream the response
            
        Returns:
            Full response text (or None if streaming)
        """
        if not message.strip():
            return None

        # Check for TTS self-diagnosis requests
        diagnosis_response = self._check_tts_diagnosis_request(message)
        if diagnosis_response:
            self.context.add_message('user', message)
            self.context.add_message('assistant', diagnosis_response)
            if self.response_callback:
                self.response_callback(diagnosis_response, done=True)
            return diagnosis_response if not stream else None

        # Update live-streaming privacy mode from user statements
        try:
            m = message.lower()
            # Normalize common ASR artifacts so toggles work even with imperfect transcripts
            m = m.replace('  ', ' ')
            m = m.replace('life streaming', 'live streaming')
            m = m.replace('no live streaming', 'not live streaming')
            m = m.replace('no live stream', 'not live')
            live_triggers = [
                'i am live', "i'm live", 'im live', 'live streaming',
                'i am streaming', "i'm streaming", 'on stream', 'i am on stream'
            ]
            not_live_triggers = [
                'not live', 'im not live', "i'm not live", 'i am not live',
                'not streaming', "i'm not streaming", 'offline', 'not on stream',
                'not live streaming', 'not livestreaming', 'no livestreaming'
            ]
            if any(t in m for t in not_live_triggers):
                self.is_live_streaming = False
                # Refresh prompt immediately
                self.context.system_prompt = self._build_system_prompt()
            elif any(t in m for t in live_triggers):
                self.is_live_streaming = True
                # Refresh prompt immediately
                self.context.system_prompt = self._build_system_prompt()
        except Exception:
            pass
        
        if self.is_generating:
            print("Already generating a response")
            return None

        # Process message for user memory (learn name, etc.)
        if self.user_memory:
            try:
                self.user_memory.process_message_for_memory(message)
                # Update system prompt with new user context
                self.context.system_prompt = self._build_system_prompt()
            except Exception as e:
                print(f"Error processing user memory: {e}")
        
        # Check if user wants Monica to remember something
        self._process_memory_request(message)
        
        # Check if this is an AR teaching request
        if AR_TEACHING_AVAILABLE:
            ar_coordinator = get_ar_coordinator()
            teaching_request = ar_coordinator.parse_teaching_request(message)
            if teaching_request:
                # Start AR teaching session
                success = ar_coordinator.start_teaching_session(teaching_request)
                if success:
                    # Return early - AR teaching system will handle this
                    response = f"Starting visual teaching session for: {teaching_request.topic}"
                    self.context.add_message('assistant', response)
                    if self.response_callback:
                        self.response_callback(response, done=True)
                    self.is_generating = False
                    return response if not stream else None
        
        # Get relevant knowledge context
        knowledge_context = ""
        pdf_context = ""
        web_context = ""
        
        # ============================================================
        # ADAPTIVE RAG: Smart decision on when to search knowledge base
        # Based on: Query Complexity Classification + Intent Detection
        # ============================================================
        needs_knowledge = self._should_search_knowledge(message)
        
        # Add Monica's memory context (only for complex queries)
        memory_context = ""
        if self.monica_memory and needs_knowledge:
            try:
                memory_context = self.monica_memory.get_context_for_query(message)
                if memory_context:
                    print(f"[MEMORY] Found relevant memories for query")
            except Exception as e:
                print(f"Error getting memory context: {e}")
        
        # Search knowledge base only when needed (ADAPTIVE RAG)
        if self.knowledge and needs_knowledge:
            try:
                knowledge_context = self.knowledge.get_context_for_query(message)
                if knowledge_context:
                    print(f"[KB] Found relevant knowledge for query")
            except Exception as e:
                print(f"Error getting knowledge context: {e}")
        
        # Search PDF index (D: Books) if available
        if getattr(self, 'pdf_retriever', None) and needs_knowledge:
            try:
                if self.pdf_retriever and self.pdf_retriever.is_ready():
                    pdf_context = self.pdf_retriever.get_context(message, top_k=self.retrieval_top_k)
                    if pdf_context:
                        print("[PDF] Found relevant PDF context")
            except Exception as e:
                print(f"[PDF] Retrieval error: {e}")

        # Search MaxOne Drive (D:) for relevant documents (RAG)
        maxone_context = ""
        if getattr(self, 'maxone_rag', None) and needs_knowledge:
            try:
                if self.maxone_rag and self.maxone_rag.is_loaded:
                    maxone_context = self.maxone_rag.get_context(message, top_k=3)
                    if maxone_context:
                        print(f"[MAXONE-RAG] Found {len(maxone_context.split('1.'))-1} relevant documents from D: drive")
            except Exception as e:
                print(f"[MAXONE-RAG] Retrieval error: {e}")

        # Web retrieval for time-sensitive facts (optional)
        if self.allow_web_retrieval and needs_knowledge and self._looks_time_sensitive(message):
            try:
                web_ctx = self._get_web_context(message)
                if web_ctx:
                    web_context = web_ctx
                    print("[WEB] Added lightweight web context")
            except Exception as e:
                print(f"[WEB] Retrieval error: {e}")
        
        # Add user message to context (with knowledge and memory if found)
        enhanced_message = message
        # Include retrieved contexts first so the model grounds to them
        if pdf_context:
            enhanced_message = f"{enhanced_message}\n\n{pdf_context}"
        if maxone_context:
            enhanced_message = f"{enhanced_message}\n\n{maxone_context}"
        if knowledge_context:
            # Wrap knowledge in a clear block for the model
            kb_block = f"[KB_CONTEXT]\n{knowledge_context}\n[/KB_CONTEXT]"
            enhanced_message = f"{enhanced_message}\n\n{kb_block}"
        if web_context:
            enhanced_message = f"{enhanced_message}\n\n{web_context}"
        if memory_context:
            enhanced_message = f"{enhanced_message}\n\n[MEMORY: {memory_context}]"
        
        if enhanced_message != message:
            self.context.add_message('user', enhanced_message)
        else:
            self.context.add_message('user', message)
        
        self.is_generating = True
        self.stop_event.clear()
        
        if stream:
            # Start streaming in background
            threading.Thread(
                target=self._generate_streaming,
                args=(message,),
                daemon=True
            ).start()
            return None
        else:
            # Generate synchronously
            try:
                result = self._generate_sync(message)
                return result
            finally:
                # Ensure generating flag is cleared for next requests
                self.is_generating = False

    def get_retrieval_health(self) -> Dict[str, Any]:
        """Return current KB/PDF/MaxOne retrieval availability for UI/status display."""
        health: Dict[str, Any] = {
            "knowledge_connector": {"available": False, "loaded": False, "reason": None},
            "pdf_retriever": {"available": False, "ready": False, "reason": None},
            "maxone_rag": {"available": False, "loaded": False, "indexing": False, "reason": None},
        }

        try:
            health["knowledge_connector"]["available"] = self.knowledge is not None
            if self.knowledge is not None:
                health["knowledge_connector"]["loaded"] = bool(getattr(self.knowledge, "is_loaded", False))
                if not health["knowledge_connector"]["loaded"]:
                    kb_count = len(getattr(self.knowledge, "knowledge_bases", {}) or {})
                    health["knowledge_connector"]["loaded"] = kb_count > 0
        except Exception as e:
            health["knowledge_connector"]["reason"] = str(e)

        try:
            health["pdf_retriever"]["available"] = getattr(self, "pdf_retriever", None) is not None
            if getattr(self, "pdf_retriever", None) is not None:
                try:
                    health["pdf_retriever"]["ready"] = bool(self.pdf_retriever.is_ready())
                except Exception as e:
                    health["pdf_retriever"]["reason"] = str(e)
        except Exception as e:
            health["pdf_retriever"]["reason"] = str(e)

        try:
            health["maxone_rag"]["available"] = getattr(self, "maxone_rag", None) is not None
            if getattr(self, "maxone_rag", None) is not None:
                health["maxone_rag"]["loaded"] = bool(getattr(self.maxone_rag, "is_loaded", False))
                health["maxone_rag"]["indexing"] = bool(getattr(self.maxone_rag, "is_indexing", False))
                if not health["maxone_rag"]["loaded"]:
                    stats_fn = getattr(self.maxone_rag, "get_stats", None)
                    if callable(stats_fn):
                        stats = stats_fn()
                        health["maxone_rag"]["loaded"] = bool(stats.get("num_documents"))
        except Exception as e:
            health["maxone_rag"]["reason"] = str(e)

        return health

    def _looks_time_sensitive(self, message: str) -> bool:
        m = message.lower()
        triggers = ["today", "current", "latest", "recent", "this week", "this month", "2024", "2025"]
        return any(t in m for t in triggers)

    def _check_tts_diagnosis_request(self, message: str) -> Optional[str]:
        """
        Check if user is asking about TTS issues and provide self-diagnosis.

        Returns:
            Diagnosis response if this is a TTS question, None otherwise
        """
        m = message.lower().strip()

        # Patterns that indicate TTS diagnosis requests
        slow_response_patterns = [
            'why are you taking a long time',
            'why are you taking so long',
            'why is your response slow',
            'why is your voice slow',
            'why do you take so long to respond',
            'why is there a delay',
            'diagnose.*response.*time',
            'diagnose.*latency',
        ]

        cutoff_patterns = [
            'why do you stop mid-sentence',
            'why do you stop talking',
            'why do you cut off',
            'why don\'t you finish',
            'why do you stop speaking',
            'diagnose.*cutoff',
            'diagnose.*stop',
        ]

        tts_general_patterns = [
            'diagnose your tts',
            'diagnose your voice',
            'diagnose your speech',
            'what\'s wrong with your voice',
            'why are you using piper',
            'why aren\'t you using xtts',
        ]

        import re
        is_slow_query = any(re.search(pattern, m) for pattern in slow_response_patterns)
        is_cutoff_query = any(re.search(pattern, m) for pattern in cutoff_patterns)
        is_general_tts = any(re.search(pattern, m) for pattern in tts_general_patterns)

        if not (is_slow_query or is_cutoff_query or is_general_tts):
            return None

        # Run appropriate diagnosis
        try:
            from ..tts.tts_diagnostics import TTSDiagnostics

            # Get TTS manager reference if available
            tts_manager = None
            try:
                # Try to get TTS manager from app instance
                import sys
                if hasattr(sys, '_monica_app'):
                    app = sys._monica_app
                    if hasattr(app, 'tts_manager'):
                        tts_manager = app.tts_manager
            except:
                pass

            diag = TTSDiagnostics(tts_manager)

            if is_slow_query:
                response = diag.diagnose_slow_response()
                response = "I'm diagnosing my slow response time:\n\n" + response

            elif is_cutoff_query:
                response = diag.diagnose_cutoff()
                response = "I'm diagnosing why I stop mid-sentence:\n\n" + response

            else:  # General TTS diagnosis
                print("\n" + "="*60)
                print("Running full TTS diagnostics...")
                print("="*60)
                results = diag.run_full_diagnosis()

                # Build summary response
                response_lines = ["I've run a full diagnostic of my TTS system. Here's what I found:\n"]

                # Summarize issues
                if results.get('issues'):
                    response_lines.append("🚨 Issues Found:")
                    for issue in results['issues']:
                        severity_icon = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(issue['severity'], '⚪')
                        response_lines.append(f"{severity_icon} {issue['title']}")
                        response_lines.append(f"   {issue['description']}")
                    response_lines.append("")

                # Summarize solutions
                if results.get('solutions'):
                    response_lines.append("💡 Recommended Solutions:")
                    for i, solution in enumerate(results['solutions'][:2], 1):  # Top 2 solutions
                        response_lines.append(f"{i}. {solution['issue']}:")
                        for step in solution['steps'][:3]:  # First 3 steps
                            response_lines.append(f"   {step}")
                    response_lines.append("")

                response_lines.append("See the console for complete diagnostic details.")
                response = "\n".join(response_lines)

            return response

        except Exception as e:
            print(f"Error running TTS diagnostics: {e}")
            import traceback
            traceback.print_exc()
            return f"I tried to diagnose my TTS system but encountered an error: {e}\n\nCheck the console for details."

    def _get_web_context(self, query: str) -> str:
        """Lightweight web context using DuckDuckGo Instant Answer (no API key)."""
        if not WEB_AVAILABLE:
            return ""
        try:
            import urllib.parse as ul
            q = ul.quote_plus(query)
            url = f"https://api.duckduckgo.com/?q={q}&format=json&no_redirect=1&no_html=1"
            resp = requests.get(url, timeout=6)
            if resp.status_code != 200:
                return ""
            data = resp.json()
            text = data.get('AbstractText') or ""
            if not text and 'RelatedTopics' in data:
                # fall back to first related topic text
                for item in data['RelatedTopics']:
                    if isinstance(item, dict) and item.get('Text'):
                        text = item['Text']
                        break
            if not text:
                return ""
            return f"[WEB_CONTEXT]\n{text}\n[/WEB_CONTEXT]"
        except Exception:
            return ""
    
    def _generate_streaming(self, message: str):
        """Generate response with streaming - uses smart model selection."""
        try:
            # Prefer multi-model routing when available/enabled
            if getattr(self, 'use_multi_model', False) and getattr(self, 'multi_model', None):
                self._generate_multi_model_streaming(message)
                return

            # Default: use Ollama streaming (fast path)
            if self.backend == 'ollama':
                self._generate_ollama_streaming()
                return

            # Fallback: sync generation
            response = self._generate_sync(message)
            if response:
                self._notify_response(response, is_final=True)

        except Exception as e:
            error_msg = f"Error generating response: {e}"
            print(error_msg)
            self._notify_error(error_msg)
        finally:
            self.is_generating = False
    
    def _generate_multi_model_streaming(self, message: str):
        """Generate response using multiple models in cohesion."""
        try:
            # Analyze the query
            analysis = self.multi_model.analyze_query(message)
            print(f"[MULTI-MODEL] Query analysis: {analysis}")
            
            # Select best models for this query
            selected_models = self.multi_model.select_models(analysis)
            print(f"[MULTI-MODEL] Selected models: {selected_models}")
            
            if not selected_models:
                # Fallback to single model
                self._generate_ollama_streaming()
                return
            
            # Get system prompt
            messages = self.context.get_messages_for_api()
            system_prompt = messages[0]['content'] if messages and messages[0]['role'] == 'system' else ""
            
            # Generate using best strategy
            if len(selected_models) == 1:
                # Single model - stream directly
                self.model = selected_models[0]  # Temporarily switch model
                self._generate_ollama_streaming()
            else:
                # Multiple models - use ensemble or chain
                if analysis.get("needs_reasoning"):
                    # Chain of thought for complex reasoning
                    response = self.multi_model.generate_chain_of_thought(
                        message, selected_models[:2]
                    )
                else:
                    # Ensemble for balanced response
                    response = self.multi_model.generate_ensemble(
                        message, selected_models, system_prompt
                    )
                
                if response:
                    # Clean and send response
                    response = self._clean_response(response)
                    self._notify_response(response, is_final=True)
                    self.context.add_message('assistant', response)
                
        except Exception as e:
            print(f"[MULTI-MODEL] Error: {e}")
            # Fallback to single model
            self._generate_ollama_streaming()
    
    def _generate_ollama_streaming(self):
        """Generate response using Ollama with streaming."""
        if not OLLAMA_AVAILABLE:
            self._notify_error("Ollama not available")
            return
        
        try:
            messages = self.context.get_messages_for_api()
            
            full_response = ""
            
            # Stream response
            # IMPORTANT: Use small context (4096) to fit in 8GB VRAM for 100% GPU
            stream = ollama.chat(
                model=self.model,
                messages=messages,
                stream=True,
                options={
                    'temperature': self.temperature,
                    'num_predict': self.max_tokens,
                    'num_ctx': 4096,  # Small context = fits in GPU = FAST
                    'num_gpu': 99     # Force all layers to GPU
                }
            )
            
            for chunk in stream:
                if self.stop_event.is_set():
                    break
                
                content = chunk.get('message', {}).get('content', '')
                if content:
                    # Don't over-clean individual chunks - preserve spaces
                    # Only do minimal cleaning (remove asterisks)
                    content = content.replace('*', '')
                    
                    full_response += content
                    self._notify_response(content, is_final=False)
            
            # Final notification
            if full_response and not self.stop_event.is_set():
                self._notify_response("", is_final=True)
                
                # Add assistant response to context
                self.context.add_message('assistant', full_response)
            
        except Exception as e:
            self._notify_error(f"Ollama error: {e}")
    
    def _generate_sync(self, message: str) -> Optional[str]:
        """Generate response synchronously."""
        if self.backend == 'ollama':
            return self._generate_ollama_sync()
        else:
            return self._generate_fallback(message)
    
    def _generate_ollama_sync(self) -> Optional[str]:
        """Generate response using Ollama synchronously."""
        if not OLLAMA_AVAILABLE:
            return None
        
        try:
            messages = self.context.get_messages_for_api()
            
            response = ollama.chat(
                model=self.model,
                messages=messages,
                options={
                    'temperature': self.temperature,
                    'num_predict': self.max_tokens,
                    # Keep context small to reduce memory; favor GPU layers aggressively
                    'num_ctx': 4096,
                    'num_gpu': 99
                }
            )
            
            content = response.get('message', {}).get('content', '')
            
            if content:
                self.context.add_message('assistant', content)
            
            return content
            
        except Exception as e:
            print(f"Ollama error: {e}")
            return None
    
    def _clean_response(self, text: str) -> str:
        """Clean up AI response - fix common mistakes and filter hallucinations."""
        import re
        
        # Check for hallucinations BEFORE cleaning
        if self._is_response_hallucination(text):
            print(f"[AI] Filtered hallucination: '{text}'")
            return "I'm not sure I understood that correctly. Can you clarify?"
        
        # Replace "Marvin" with "MJP" - case insensitive
        text = re.sub(r'\bMarvin\b', 'MJP', text, flags=re.IGNORECASE)

        # Normalize spaced name artifacts from model output
        text = re.sub(r'\bM\s+JP\b', 'MJP', text, flags=re.IGNORECASE)
        
        # Remove ALL head movement mentions - very aggressive
        head_patterns = [
            r"[^.]*head shaking[^.]*\.",
            r"[^.]*shaking your head[^.]*\.",
            r"[^.]*shaking head[^.]*\.",
            r"[^.]*nodding[^.]*\.",
            r"[^.]*head nod[^.]*\.",
            r"I can see you'?r?e? head[^.]*\.",
            r"I see you'?r?e? head[^.]*\.",
        ]
        for pattern in head_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # Remove asterisk expressions completely
        text = re.sub(r'\*[^*]+\*', '', text)
        
        # Clean up extra whitespace and periods
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\.\s*\.', '.', text)
        text = text.strip()
        
        return text
    
    def _is_response_hallucination(self, text: str) -> bool:
        """Detect if response is a hallucination (inventing context)."""
        text_lower = text.lower()
        
        # Get the last user message to check for context mismatch
        user_messages = [m.content.lower() for m in self.context.messages if m.role == 'user']
        if not user_messages:
            return False
        
        last_user_msg = user_messages[-1]
        
        # Hallucination patterns: mentioning things user never said
        hallucination_patterns = [
            ('bird', ['bird', 'animal', 'favorite animal']),
            ('excited', ['excited', 'enthusiasm', 'enthusiastic']),
            ('favorite', ['favorite', 'prefer', 'like']),
        ]
        
        for pattern_name, keywords in hallucination_patterns:
            # If response mentions these but user didn't
            has_keyword = any(kw in text_lower for kw in keywords)
            user_mentioned = any(kw in last_user_msg for kw in keywords)
            
            if has_keyword and not user_mentioned:
                return True
        
        # Check for "did you say" pattern when user didn't say that
        if 'did you say' in text_lower or 'did you just say' in text_lower:
            # Extract what Monica thinks user said
            import re
            match = re.search(r'did you (?:just )?say ["\']?([^"\'?]+)["\']?', text_lower)
            if match:
                claimed_phrase = match.group(1).strip()
                if claimed_phrase not in last_user_msg:
                    return True
        
        return False
    
    def _generate_fallback(self, message: str) -> str:
        """Fallback response when no AI backend is available."""
        responses = [
            "I'm sorry, I'm having trouble connecting to my AI backend right now.",
            "Let me think about that... Actually, my AI service seems to be offline.",
            "I'd love to help, but I need my AI backend to be running first.",
        ]
        
        import random
        return random.choice(responses)
    
    def stop_generation(self):
        """Stop the current response generation."""
        self.stop_event.set()
        self.is_generating = False
    
    # ==================== Context Management ====================
    
    def set_system_prompt(self, prompt: str):
        """Set the system prompt."""
        self.context.system_prompt = prompt
    
    def get_system_prompt(self) -> str:
        """Get the current system prompt."""
        return self.context.system_prompt
    
    def clear_history(self):
        """Clear conversation history."""
        self.context.clear()
    
    def get_history(self) -> List[Message]:
        """Get conversation history."""
        return self.context.messages.copy()
    
    def set_max_history(self, max_messages: int):
        """Set maximum conversation history length."""
        self.context.max_history = max_messages
    
    # ==================== Model Management ====================
    
    def set_model(self, model: str):
        """Set the AI model."""
        self.model = model
    
    def set_temperature(self, temperature: float):
        """Set response temperature (0.0 to 2.0)."""
        self.temperature = max(0.0, min(2.0, temperature))
    
    def set_max_tokens(self, max_tokens: int):
        """Set maximum response tokens."""
        self.max_tokens = max_tokens
    
    def list_available_models(self) -> List[str]:
        """List available AI models."""
        if self.backend == 'ollama' and OLLAMA_AVAILABLE:
            try:
                models = ollama.list()
                return [m['name'] for m in models.get('models', [])]
            except Exception:
                pass
        
        return []
    
    # ==================== Callbacks ====================
    
    def _notify_response(self, text: str, is_final: bool):
        """Notify callbacks of response."""
        self.response_queue.put((text, is_final))
        
        for callback in self.response_callbacks:
            try:
                callback(text, is_final)
            except Exception as e:
                print(f"Error in response callback: {e}")
    
    def _notify_error(self, error: str):
        """Notify callbacks of error."""
        for callback in self.error_callbacks:
            try:
                callback(error)
            except Exception as e:
                print(f"Error in error callback: {e}")
    
    def register_response_callback(self, callback: Callable[[str, bool], None]):
        """
        Register callback for responses.
        
        Callback receives (text, is_final) where:
        - text: Response text chunk
        - is_final: True if this is the final chunk
        """
        if callback not in self.response_callbacks:
            self.response_callbacks.append(callback)
    
    def unregister_response_callback(self, callback: Callable[[str, bool], None]):
        """Unregister response callback."""
        if callback in self.response_callbacks:
            self.response_callbacks.remove(callback)
    
    def register_error_callback(self, callback: Callable[[str], None]):
        """Register callback for errors."""
        if callback not in self.error_callbacks:
            self.error_callbacks.append(callback)
    
    def unregister_error_callback(self, callback: Callable[[str], None]):
        """Unregister error callback."""
        if callback in self.error_callbacks:
            self.error_callbacks.remove(callback)
    
    def get_response(self, timeout: float = None) -> Optional[tuple]:
        """
        Get next response chunk from queue.
        
        Returns:
            Tuple of (text, is_final) or None if timeout
        """
        try:
            return self.response_queue.get(timeout=timeout)
        except queue.Empty:
            return None
