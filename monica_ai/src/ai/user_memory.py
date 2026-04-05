"""
User Memory System for Monica AI.
Remembers users, their preferences, and conversation history.
"""
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict


@dataclass
class UserProfile:
    """User profile with preferences and history."""
    user_id: str
    name: str = ""
    nickname: str = ""
    voice_signature: str = ""  # For future voice recognition
    first_seen: str = field(default_factory=lambda: datetime.now().isoformat())
    last_seen: str = field(default_factory=lambda: datetime.now().isoformat())
    interaction_count: int = 0
    preferences: Dict[str, Any] = field(default_factory=dict)
    facts: List[str] = field(default_factory=list)  # Things Monica learned about user
    topics_discussed: List[str] = field(default_factory=list)
    
    # Visual/emotional patterns
    common_emotions: Dict[str, int] = field(default_factory=dict)  # Emotion frequency
    typical_mood: str = ""  # Overall mood pattern
    body_language_notes: List[str] = field(default_factory=list)
    appearance_notes: List[str] = field(default_factory=list)  # Hair color, glasses, etc.
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'UserProfile':
        return cls(**data)


class UserMemory:
    """
    Manages user recognition and memory.
    
    Features:
    - Remember user names and preferences
    - Track conversation topics
    - Store facts about users
    - Personalize greetings
    """
    
    def __init__(self, data_dir: Path = None):
        """Initialize user memory."""
        if data_dir is None:
            data_dir = Path(__file__).parent.parent.parent / "data"
        
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.users_file = self.data_dir / "users.json"
        self.users: Dict[str, UserProfile] = {}
        self.current_user: Optional[UserProfile] = None
        
        # Load existing users
        self._load_users()
        
        # Set default user (primary user)
        self._set_default_user()
    
    def _load_users(self):
        """Load users from file."""
        if self.users_file.exists():
            try:
                with open(self.users_file, 'r') as f:
                    data = json.load(f)
                    for user_id, user_data in data.items():
                        self.users[user_id] = UserProfile.from_dict(user_data)
                print(f"Loaded {len(self.users)} user profiles")
            except Exception as e:
                print(f"Error loading users: {e}")
    
    def _save_users(self):
        """Save users to file."""
        try:
            data = {uid: user.to_dict() for uid, user in self.users.items()}
            with open(self.users_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving users: {e}")
    
    def _set_default_user(self):
        """Set or create the default/primary user."""
        default_id = "primary_user"
        
        if default_id not in self.users:
            # Create default user
            self.users[default_id] = UserProfile(
                user_id=default_id,
                name="",  # Will be learned
                nickname="",
            )
            self._save_users()
        
        self.current_user = self.users[default_id]
    
    def get_current_user(self) -> Optional[UserProfile]:
        """Get the current user."""
        return self.current_user
    
    def set_user_name(self, name: str):
        """Set the current user's name."""
        if self.current_user:
            self.current_user.name = name
            self._save_users()
            print(f"User name set to: {name}")
    
    def set_user_nickname(self, nickname: str):
        """Set a nickname for the current user."""
        if self.current_user:
            self.current_user.nickname = nickname
            self._save_users()
    
    def add_user_fact(self, fact: str):
        """Add a fact about the current user."""
        if self.current_user and fact not in self.current_user.facts:
            self.current_user.facts.append(fact)
            # Keep only last 50 facts
            if len(self.current_user.facts) > 50:
                self.current_user.facts = self.current_user.facts[-50:]
            self._save_users()
    
    def add_topic(self, topic: str):
        """Add a discussed topic."""
        if self.current_user and topic not in self.current_user.topics_discussed:
            self.current_user.topics_discussed.append(topic)
            # Keep only last 100 topics
            if len(self.current_user.topics_discussed) > 100:
                self.current_user.topics_discussed = self.current_user.topics_discussed[-100:]
            self._save_users()
    
    def record_interaction(self):
        """Record an interaction with the current user."""
        if self.current_user:
            self.current_user.interaction_count += 1
            self.current_user.last_seen = datetime.now().isoformat()
            self._save_users()
    
    def is_known_user(self) -> bool:
        """Check if we know the current user's name."""
        return bool(self.current_user and self.current_user.name)
    
    def get_greeting_context(self) -> str:
        """Get context for personalized greeting."""
        if not self.current_user:
            return "This is a new user. Introduce yourself warmly."
        
        user = self.current_user
        
        if not user.name:
            if user.interaction_count == 0:
                return """This is a brand new user you've never met. 
Give a warm, elegant introduction of yourself. 
Ask for their name so you can remember them."""
            else:
                return f"""You've talked to this user {user.interaction_count} times but don't know their name yet.
Don't introduce yourself again - they know you.
You might want to ask their name if appropriate."""
        
        # Known user
        name = user.nickname or user.name
        facts_str = "\n".join(f"- {f}" for f in user.facts[-5:]) if user.facts else "None yet"
        
        return f"""This is {name}, a user you know well!
You've had {user.interaction_count} conversations together.
Last seen: {user.last_seen}

Things you know about {name}:
{facts_str}

DO NOT introduce yourself - {name} knows you well.
Greet them warmly by name like an old friend."""
    
    def extract_name_from_message(self, message: str) -> Optional[str]:
        """Try to extract user's name from a message."""
        message_lower = message.lower()
        
        # Common patterns
        patterns = [
            "my name is ",
            "i'm ",
            "i am ",
            "call me ",
            "name's ",
            "this is ",
        ]
        
        for pattern in patterns:
            if pattern in message_lower:
                # Get the word after the pattern
                idx = message_lower.find(pattern) + len(pattern)
                remaining = message[idx:].strip()
                # Get first word (the name)
                name = remaining.split()[0] if remaining.split() else None
                if name:
                    # Clean up punctuation
                    name = name.strip('.,!?')
                    if len(name) > 1 and name[0].isupper():
                        return name
        
        return None
    
    def process_message_for_memory(self, message: str) -> Optional[str]:
        """
        Process a message to extract and store information.
        Returns a confirmation message if something was remembered.
        """
        message_lower = message.lower()
        confirmation = None
        
        # Try to extract name
        name = self.extract_name_from_message(message)
        if name and not self.current_user.name:
            self.set_user_name(name)
            print(f"Learned user's name: {name}")
        
        # Check for "remember" commands
        remember_patterns = [
            "remember that ", "remember this ", "remember i ", "remember my ",
            "don't forget ", "keep in mind ", "note that ", "save this ",
            "remember:", "remember -", "memorize "
        ]
        
        for pattern in remember_patterns:
            if pattern in message_lower:
                idx = message_lower.find(pattern) + len(pattern)
                fact = message[idx:].strip()
                if fact and len(fact) > 3:
                    self.add_user_fact(fact)
                    confirmation = f"I'll remember: {fact}"
                    print(f"[MEMORY] Stored fact: {fact}")
                break
        
        # Check for preference settings - only explicit user preferences
        # Removed "always" and "never" as they match too many things
        preference_patterns = {
            "i prefer ": "preference",
            "i like ": "likes",
            "i don't like ": "dislikes", 
            "i hate ": "dislikes",
            "i love ": "loves",
            "my favorite ": "favorites",
            "i always ": "habits",
            "i never ": "avoids",
            "call me ": "nickname",
            "please remember to ": "behavior_request",
            "i want you to always ": "behavior_request",
        }
        
        for pattern, pref_type in preference_patterns.items():
            if pattern in message_lower:
                idx = message_lower.find(pattern) + len(pattern)
                value = message[idx:].strip().rstrip('.,!?')
                if value and len(value) > 2:
                    if pref_type == "nickname":
                        self.set_user_nickname(value.split()[0])
                        confirmation = f"I'll call you {value.split()[0]} from now on!"
                    else:
                        # Store as preference
                        if pref_type not in self.current_user.preferences:
                            self.current_user.preferences[pref_type] = []
                        if value not in self.current_user.preferences[pref_type]:
                            self.current_user.preferences[pref_type].append(value)
                            self._save_users()
                            confirmation = f"Noted! I'll remember that."
                            print(f"[MEMORY] Stored preference ({pref_type}): {value}")
                break
        
        # Record interaction
        self.record_interaction()
        
        return confirmation
    
    def record_emotion(self, emotion: str):
        """Record an observed emotion to track patterns."""
        if not self.current_user or not emotion:
            return
        
        # Initialize if needed
        if not hasattr(self.current_user, 'common_emotions') or self.current_user.common_emotions is None:
            self.current_user.common_emotions = {}
        
        # Increment emotion count
        if emotion not in self.current_user.common_emotions:
            self.current_user.common_emotions[emotion] = 0
        self.current_user.common_emotions[emotion] += 1
        
        # Update typical mood (most common emotion)
        if self.current_user.common_emotions:
            self.current_user.typical_mood = max(
                self.current_user.common_emotions,
                key=self.current_user.common_emotions.get
            )
        
        self._save_users()
    
    def add_appearance_note(self, note: str):
        """Add a note about user's appearance."""
        if self.current_user and note:
            if not hasattr(self.current_user, 'appearance_notes') or self.current_user.appearance_notes is None:
                self.current_user.appearance_notes = []
            if note not in self.current_user.appearance_notes:
                self.current_user.appearance_notes.append(note)
                self._save_users()
    
    def add_body_language_note(self, note: str):
        """Add a note about user's body language patterns."""
        if self.current_user and note:
            if not hasattr(self.current_user, 'body_language_notes') or self.current_user.body_language_notes is None:
                self.current_user.body_language_notes = []
            if note not in self.current_user.body_language_notes:
                self.current_user.body_language_notes.append(note)
                # Keep only last 20 notes
                self.current_user.body_language_notes = self.current_user.body_language_notes[-20:]
                self._save_users()
    
    def get_user_context(self) -> str:
        """Get full user context for AI system prompt."""
        if not self.current_user:
            return ""
        
        user = self.current_user
        context_parts = []
        
        # ALWAYS use nickname (MJP) - never expose real name to AI
        if user.nickname:
            context_parts.append(f"User's name: {user.nickname}")
            context_parts.append(f"IMPORTANT: Always call the user '{user.nickname}', never use any other name.")
        
        # Add facts
        if user.facts:
            context_parts.append("Things you know about this user:")
            for fact in user.facts[-10:]:  # Last 10 facts
                context_parts.append(f"  - {fact}")
        
        # Add preferences
        if user.preferences:
            context_parts.append("User preferences:")
            for pref_type, values in user.preferences.items():
                if values:
                    context_parts.append(f"  - {pref_type}: {', '.join(values[-5:])}")
        
        # Add emotional patterns
        if hasattr(user, 'typical_mood') and user.typical_mood:
            context_parts.append(f"User's typical mood: {user.typical_mood}")
        
        if hasattr(user, 'common_emotions') and user.common_emotions:
            top_emotions = sorted(user.common_emotions.items(), key=lambda x: x[1], reverse=True)[:3]
            if top_emotions:
                emotions_str = ", ".join([f"{e[0]} ({e[1]}x)" for e in top_emotions])
                context_parts.append(f"Common emotions observed: {emotions_str}")
        
        # Add appearance notes
        if hasattr(user, 'appearance_notes') and user.appearance_notes:
            context_parts.append(f"Appearance: {', '.join(user.appearance_notes[-3:])}")
        
        return "\n".join(context_parts)


# Singleton instance
_user_memory = None

def get_user_memory() -> UserMemory:
    """Get the singleton user memory instance."""
    global _user_memory
    if _user_memory is None:
        _user_memory = UserMemory()
    return _user_memory
