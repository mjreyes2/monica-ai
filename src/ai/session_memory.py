"""
Monica AI - Session Memory System

Tracks conversation sessions so Monica can:
1. Remember what was discussed last time
2. Notice when it's been a while since the user spoke
3. Recall specific past conversations by topic
4. Build a persistent conversation journal
5. Provide time-aware greetings ("It's been 3 days!")

All data stored locally in: data/user_profile/sessions/
"""

import json
import time
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field, asdict

logger = logging.getLogger("Monica.SessionMemory")


@dataclass
class ConversationEntry:
    """A single message in a conversation."""
    role: str          # 'user' or 'assistant'
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    emotion: str = ""  # Detected emotion at time of message
    topic: str = ""    # Auto-detected topic


@dataclass 
class Session:
    """A conversation session."""
    session_id: str
    started_at: str
    ended_at: str = ""
    duration_minutes: float = 0.0
    messages: List[Dict[str, str]] = field(default_factory=list)
    topics: List[str] = field(default_factory=list)
    summary: str = ""
    user_mood: str = ""
    message_count: int = 0


class SessionMemory:
    """
    Persistent session memory for Monica AI.
    
    Remembers past conversations, tracks time between sessions,
    and provides context for natural, relationship-aware interactions.
    """

    def __init__(self, base_dir: Path = None):
        if base_dir is None:
            try:
                from config.settings import config
                base_dir = Path(str(config.BASE_DIR))
            except Exception:
                base_dir = Path(".")

        self.data_dir = base_dir / "data" / "user_profile" / "sessions"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.sessions_index_file = self.data_dir / "sessions_index.json"
        self.current_session_file = self.data_dir / "current_session.json"

        # State
        self.sessions_index: List[Dict[str, Any]] = []
        self.current_session: Optional[Session] = None
        self._load_index()

        logger.info(f"[SESSION] Memory initialized ({len(self.sessions_index)} past sessions)")

    def _load_index(self):
        """Load sessions index."""
        if self.sessions_index_file.exists():
            try:
                self.sessions_index = json.loads(
                    self.sessions_index_file.read_text(encoding='utf-8')
                )
            except Exception as e:
                logger.warning(f"[SESSION] Failed to load index: {e}")
                self.sessions_index = []

    def _save_index(self):
        """Save sessions index."""
        try:
            self.sessions_index_file.write_text(
                json.dumps(self.sessions_index, indent=2, ensure_ascii=False),
                encoding='utf-8'
            )
        except Exception as e:
            logger.error(f"[SESSION] Failed to save index: {e}")

    def start_session(self) -> Session:
        """Start a new conversation session."""
        # End any existing session first
        if self.current_session:
            self.end_session()

        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_session = Session(
            session_id=session_id,
            started_at=datetime.now().isoformat(),
        )

        logger.info(f"[SESSION] New session started: {session_id}")
        return self.current_session

    def end_session(self):
        """End the current session and save it."""
        if not self.current_session:
            return

        s = self.current_session
        s.ended_at = datetime.now().isoformat()

        # Calculate duration
        try:
            start = datetime.fromisoformat(s.started_at)
            end = datetime.fromisoformat(s.ended_at)
            s.duration_minutes = round((end - start).total_seconds() / 60, 1)
        except Exception:
            s.duration_minutes = 0

        s.message_count = len(s.messages)

        # Auto-generate summary from messages
        if not s.summary:
            s.summary = self._auto_summarize(s)

        # Save session file
        session_file = self.data_dir / f"session_{s.session_id}.json"
        try:
            session_file.write_text(
                json.dumps(asdict(s), indent=2, ensure_ascii=False),
                encoding='utf-8'
            )
        except Exception as e:
            logger.error(f"[SESSION] Failed to save session: {e}")

        # Update index
        self.sessions_index.append({
            'session_id': s.session_id,
            'started_at': s.started_at,
            'ended_at': s.ended_at,
            'duration_minutes': s.duration_minutes,
            'message_count': s.message_count,
            'topics': s.topics[:5],
            'summary': s.summary[:200],
            'user_mood': s.user_mood,
        })

        # Keep last 200 sessions in index
        if len(self.sessions_index) > 200:
            self.sessions_index = self.sessions_index[-200:]

        self._save_index()
        logger.info(f"[SESSION] Session ended: {s.session_id} ({s.message_count} msgs, {s.duration_minutes} min)")

        self.current_session = None

    def add_message(self, role: str, content: str, emotion: str = ""):
        """Add a message to the current session."""
        if not self.current_session:
            self.start_session()

        self.current_session.messages.append({
            'role': role,
            'content': content[:500],  # Truncate for storage
            'timestamp': datetime.now().isoformat(),
            'emotion': emotion,
        })

        # Auto-detect topics from user messages
        if role == 'user':
            topics = self._extract_topics(content)
            for t in topics:
                if t not in self.current_session.topics:
                    self.current_session.topics.append(t)

        # Update mood
        if emotion and role == 'user':
            self.current_session.user_mood = emotion

        # Auto-save every 10 messages
        if len(self.current_session.messages) % 10 == 0:
            self._save_current()

    def _save_current(self):
        """Save current session to disk (periodic backup)."""
        if not self.current_session:
            return
        try:
            self.current_session_file.write_text(
                json.dumps(asdict(self.current_session), indent=2, ensure_ascii=False),
                encoding='utf-8'
            )
        except Exception:
            pass

    # ==================== Recall & Context ====================

    def get_last_session_context(self) -> str:
        """
        Get context about the last session for the AI prompt.
        Includes time gap awareness and conversation recall.
        """
        if not self.sessions_index:
            return "This is the very first conversation with this user. Make a great first impression!"

        last = self.sessions_index[-1]

        # Calculate time since last session
        time_gap_str = ""
        try:
            last_time = datetime.fromisoformat(last['ended_at'])
            now = datetime.now()
            gap = now - last_time

            if gap < timedelta(minutes=5):
                time_gap_str = "You just spoke moments ago."
            elif gap < timedelta(hours=1):
                mins = int(gap.total_seconds() / 60)
                time_gap_str = f"You spoke about {mins} minutes ago."
            elif gap < timedelta(hours=24):
                hours = int(gap.total_seconds() / 3600)
                time_gap_str = f"You last spoke about {hours} hour(s) ago today."
            elif gap < timedelta(days=2):
                time_gap_str = "You spoke yesterday."
            elif gap < timedelta(days=7):
                days = gap.days
                time_gap_str = f"It's been {days} days since you last spoke."
            elif gap < timedelta(days=30):
                weeks = gap.days // 7
                time_gap_str = f"It's been about {weeks} week(s) since your last conversation."
            elif gap < timedelta(days=365):
                months = gap.days // 30
                time_gap_str = f"It's been about {months} month(s) since you last spoke! Welcome back!"
            else:
                time_gap_str = f"It's been a very long time ({gap.days} days) since your last conversation!"
        except Exception:
            pass

        # Build context
        parts = []
        parts.append(f"[SESSION_MEMORY]")

        if time_gap_str:
            parts.append(f"Time since last conversation: {time_gap_str}")

        parts.append(f"Total past sessions: {len(self.sessions_index)}")

        # Last session details
        parts.append(f"\nLast conversation:")
        if last.get('summary'):
            parts.append(f"  Summary: {last['summary']}")
        if last.get('topics'):
            parts.append(f"  Topics discussed: {', '.join(last['topics'][:5])}")
        if last.get('user_mood'):
            parts.append(f"  User's mood was: {last['user_mood']}")
        if last.get('duration_minutes'):
            parts.append(f"  Duration: {last['duration_minutes']} minutes")

        # Recent topics across sessions (last 5)
        all_topics = []
        for s in self.sessions_index[-5:]:
            all_topics.extend(s.get('topics', []))
        if all_topics:
            unique_topics = list(dict.fromkeys(all_topics))[:10]
            parts.append(f"\nRecent topics across sessions: {', '.join(unique_topics)}")

        parts.append("[/SESSION_MEMORY]")
        return "\n".join(parts)

    def recall_topic(self, topic: str) -> List[Dict[str, Any]]:
        """Recall past sessions that discussed a specific topic."""
        matches = []
        topic_lower = topic.lower()
        for s in self.sessions_index:
            session_topics = [t.lower() for t in s.get('topics', [])]
            summary_lower = s.get('summary', '').lower()
            if any(topic_lower in t for t in session_topics) or topic_lower in summary_lower:
                matches.append(s)
        return matches[-5:]  # Last 5 matching sessions

    def get_session_count(self) -> int:
        """Get total number of past sessions."""
        return len(self.sessions_index)

    # ==================== Helpers ====================

    @staticmethod
    def _extract_topics(text: str) -> List[str]:
        """Extract likely topics from user text."""
        topics = []
        text_lower = text.lower()

        # Topic keywords
        topic_keywords = {
            'health': ['health', 'medical', 'doctor', 'sick', 'pain', 'medicine', 'symptom'],
            'work': ['work', 'job', 'career', 'office', 'meeting', 'project', 'boss'],
            'family': ['family', 'mom', 'dad', 'brother', 'sister', 'wife', 'husband', 'kids'],
            'technology': ['computer', 'code', 'programming', 'software', 'app', 'tech'],
            'education': ['school', 'study', 'learn', 'class', 'teacher', 'homework', 'exam'],
            'emotions': ['feel', 'happy', 'sad', 'angry', 'stressed', 'anxious', 'worried'],
            'entertainment': ['movie', 'music', 'game', 'book', 'show', 'watch', 'play'],
            'food': ['eat', 'food', 'cook', 'recipe', 'restaurant', 'hungry', 'meal'],
            'weather': ['weather', 'rain', 'sunny', 'cold', 'hot', 'temperature'],
            'travel': ['travel', 'trip', 'vacation', 'flight', 'hotel', 'visit'],
            'finance': ['money', 'budget', 'save', 'invest', 'bill', 'pay', 'cost'],
            'creative': ['draw', 'paint', 'art', 'create', 'design', 'write', 'story'],
        }

        for topic, keywords in topic_keywords.items():
            if any(kw in text_lower for kw in keywords):
                topics.append(topic)

        return topics[:3]  # Max 3 topics per message

    @staticmethod
    def _auto_summarize(session: Session) -> str:
        """Auto-generate a brief summary of the session."""
        if not session.messages:
            return "Empty session"

        user_msgs = [m['content'] for m in session.messages if m['role'] == 'user']
        if not user_msgs:
            return "No user messages"

        # Use first and last user messages + topics
        summary_parts = []
        if session.topics:
            summary_parts.append(f"Topics: {', '.join(session.topics[:5])}")

        first_msg = user_msgs[0][:100]
        summary_parts.append(f"Started with: '{first_msg}'")

        if len(user_msgs) > 1:
            last_msg = user_msgs[-1][:100]
            summary_parts.append(f"Ended with: '{last_msg}'")

        return ". ".join(summary_parts)


# Singleton
_session_memory = None

def get_session_memory() -> SessionMemory:
    """Get or create the session memory singleton."""
    global _session_memory
    if _session_memory is None:
        _session_memory = SessionMemory()
    return _session_memory
