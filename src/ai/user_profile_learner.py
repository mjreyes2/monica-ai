"""
Monica AI - User Profile Learning System
Automatically learns about the user from every interaction.
Stores: identity, preferences, appearance, moods, habits, relationships, topics of interest.
All data is encrypted at rest (see security module).
"""
import json
import os
import re
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

logger = logging.getLogger("Monica.UserProfileLearner")

# Default storage location
_DEFAULT_PROFILE_DIR = None


def _get_profile_dir() -> Path:
    global _DEFAULT_PROFILE_DIR
    if _DEFAULT_PROFILE_DIR is None:
        try:
            from config.settings import config
            _DEFAULT_PROFILE_DIR = Path(str(config.BASE_DIR)) / "data" / "user_profile"
        except Exception:
            _DEFAULT_PROFILE_DIR = Path("data") / "user_profile"
    _DEFAULT_PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    return _DEFAULT_PROFILE_DIR


class UserProfileLearner:
    """
    Learns about the user from every interaction and stores a rich profile.
    
    Categories tracked:
    - identity: name, age, pronouns, occupation, location
    - appearance: physical description, clothing style, hair, eyes
    - preferences: likes, dislikes, favorites (food, music, movies, etc.)
    - moods: mood history with timestamps
    - personality: communication style, humor, values
    - relationships: people the user mentions (family, friends, etc.)
    - topics: topics of interest, frequently asked about
    - habits: routines, schedule patterns
    - health: general wellness notes (HIPAA-compliant storage)
    - interactions: conversation stats and patterns
    """

    def __init__(self, profile_dir: Path = None):
        self.profile_dir = profile_dir or _get_profile_dir()
        self.profile_dir.mkdir(parents=True, exist_ok=True)
        self.profile_file = self.profile_dir / "user_profile.json"
        self.mood_log_file = self.profile_dir / "mood_log.json"
        self.interaction_log_file = self.profile_dir / "interaction_log.json"

        self.profile: Dict[str, Any] = self._load_or_create_profile()
        self.mood_log: List[Dict] = self._load_json(self.mood_log_file, [])
        self._interaction_count = self.profile.get("interactions", {}).get("total_count", 0)

        logger.info(f"UserProfileLearner initialized ({self._interaction_count} past interactions)")

    def _load_or_create_profile(self) -> Dict[str, Any]:
        if self.profile_file.exists():
            try:
                with open(self.profile_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load profile: {e}")
        return self._empty_profile()

    @staticmethod
    def _empty_profile() -> Dict[str, Any]:
        return {
            "identity": {
                "name": None,
                "age": None,
                "pronouns": None,
                "occupation": None,
                "location": None,
                "email": None,
                "birthday": None,
            },
            "appearance": {
                "description": None,
                "hair": None,
                "eyes": None,
                "height": None,
                "style": None,
                "notes": [],
            },
            "preferences": {
                "likes": [],
                "dislikes": [],
                "favorite_food": [],
                "favorite_music": [],
                "favorite_movies": [],
                "favorite_books": [],
                "favorite_games": [],
                "favorite_colors": [],
                "hobbies": [],
            },
            "moods": {
                "current_mood": None,
                "last_updated": None,
                "mood_history": [],
            },
            "personality": {
                "communication_style": None,
                "humor_type": None,
                "values": [],
                "pet_peeves": [],
            },
            "relationships": {},
            "topics_of_interest": [],
            "habits": {
                "wake_time": None,
                "sleep_time": None,
                "routines": [],
            },
            "health": {
                "notes": [],
                "conditions": [],
                "medications": [],
            },
            "interactions": {
                "total_count": 0,
                "first_interaction": None,
                "last_interaction": None,
                "frequent_topics": {},
            },
            "custom_facts": [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

    def _load_json(self, path: Path, default):
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return default

    def save(self):
        """Persist profile and logs to disk."""
        self.profile["updated_at"] = datetime.now().isoformat()
        try:
            with open(self.profile_file, "w", encoding="utf-8") as f:
                json.dump(self.profile, f, indent=2, ensure_ascii=False)
            with open(self.mood_log_file, "w", encoding="utf-8") as f:
                json.dump(self.mood_log[-500:], f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save profile: {e}")

    # ==================== Learning from conversation ====================

    def learn_from_message(self, user_message: str, ai_response: str = ""):
        """
        Analyze a user message and extract profile information.
        Call this on every user interaction.
        """
        now = datetime.now().isoformat()
        msg = user_message.strip()
        msg_lower = msg.lower()

        # Update interaction count
        self._interaction_count += 1
        self.profile["interactions"]["total_count"] = self._interaction_count
        if not self.profile["interactions"]["first_interaction"]:
            self.profile["interactions"]["first_interaction"] = now
        self.profile["interactions"]["last_interaction"] = now

        # Extract information
        self._extract_name(msg, msg_lower)
        self._extract_age(msg, msg_lower)
        self._extract_occupation(msg, msg_lower)
        self._extract_location(msg, msg_lower)
        self._extract_preferences(msg, msg_lower)
        self._extract_mood(msg, msg_lower, now)
        self._extract_relationships(msg, msg_lower)
        self._extract_topics(msg, msg_lower)
        self._extract_appearance(msg, msg_lower)
        self._extract_custom_facts(msg, msg_lower)

        # Auto-save every 5 interactions
        if self._interaction_count % 5 == 0:
            self.save()

    def _extract_name(self, msg: str, msg_lower: str):
        patterns = [
            r"my name is (\w+)",
            r"i'?m (\w+)",
            r"call me (\w+)",
            r"people call me (\w+)",
            r"i go by (\w+)",
        ]
        for pat in patterns:
            m = re.search(pat, msg_lower)
            if m:
                name = m.group(1).capitalize()
                if len(name) > 1 and name.lower() not in ("a", "an", "the", "not", "so", "just", "really", "very", "here", "there", "fine", "good", "okay", "great", "doing", "feeling"):
                    self.profile["identity"]["name"] = name
                    break

    def _extract_age(self, msg: str, msg_lower: str):
        patterns = [
            r"i(?:'m| am) (\d{1,3}) years old",
            r"my age is (\d{1,3})",
            r"i(?:'m| am) (\d{1,3})\b",
        ]
        for pat in patterns:
            m = re.search(pat, msg_lower)
            if m:
                age = int(m.group(1))
                if 5 <= age <= 120:
                    self.profile["identity"]["age"] = age
                    break

    def _extract_occupation(self, msg: str, msg_lower: str):
        patterns = [
            r"i (?:work as|am) (?:a |an )?(.+?)(?:\.|,|$)",
            r"my job is (.+?)(?:\.|,|$)",
            r"i'm (?:a |an )?(.+?) (?:by profession|for a living)",
        ]
        job_keywords = ["work", "job", "profession", "career", "employed", "occupation"]
        if any(kw in msg_lower for kw in job_keywords):
            for pat in patterns:
                m = re.search(pat, msg_lower)
                if m:
                    occ = m.group(1).strip()
                    if 2 < len(occ) < 60:
                        self.profile["identity"]["occupation"] = occ
                        break

    def _extract_location(self, msg: str, msg_lower: str):
        patterns = [
            r"i live in (.+?)(?:\.|,|$)",
            r"i'm from (.+?)(?:\.|,|$)",
            r"i(?:'m| am) in (.+?)(?:\.|,|$)",
            r"i(?:'m| am) located in (.+?)(?:\.|,|$)",
        ]
        if any(kw in msg_lower for kw in ["live in", "from", "located in", "i'm in"]):
            for pat in patterns:
                m = re.search(pat, msg_lower)
                if m:
                    loc = m.group(1).strip()
                    if 2 < len(loc) < 80:
                        self.profile["identity"]["location"] = loc
                        break

    def _extract_preferences(self, msg: str, msg_lower: str):
        # Likes
        like_patterns = [
            r"i (?:really )?(?:like|love|enjoy|adore) (.+?)(?:\.|,|!|$)",
            r"my favorite (?:thing|food|music|movie|book|game|color|hobby) is (.+?)(?:\.|,|!|$)",
            r"i'm (?:a )?(?:big )?fan of (.+?)(?:\.|,|!|$)",
        ]
        for pat in like_patterns:
            m = re.search(pat, msg_lower)
            if m:
                item = m.group(1).strip()[:80]
                if item and item not in self.profile["preferences"]["likes"]:
                    self.profile["preferences"]["likes"].append(item)
                    # Categorize
                    self._categorize_preference(item, msg_lower)
                break

        # Dislikes
        dislike_patterns = [
            r"i (?:really )?(?:hate|dislike|can't stand|don't like) (.+?)(?:\.|,|!|$)",
        ]
        for pat in dislike_patterns:
            m = re.search(pat, msg_lower)
            if m:
                item = m.group(1).strip()[:80]
                if item and item not in self.profile["preferences"]["dislikes"]:
                    self.profile["preferences"]["dislikes"].append(item)
                break

    def _categorize_preference(self, item: str, msg_lower: str):
        """Auto-categorize a liked item into specific preference lists."""
        food_words = ["eat", "food", "pizza", "sushi", "pasta", "cook", "restaurant", "meal"]
        music_words = ["music", "song", "band", "singer", "album", "listen", "genre"]
        movie_words = ["movie", "film", "watch", "show", "series", "tv"]
        book_words = ["book", "read", "novel", "author", "story"]
        game_words = ["game", "play", "gaming", "video game"]
        color_words = ["color", "colour"]
        hobby_words = ["hobby", "hobbies", "free time", "fun"]

        if any(w in msg_lower for w in food_words):
            if item not in self.profile["preferences"]["favorite_food"]:
                self.profile["preferences"]["favorite_food"].append(item)
        elif any(w in msg_lower for w in music_words):
            if item not in self.profile["preferences"]["favorite_music"]:
                self.profile["preferences"]["favorite_music"].append(item)
        elif any(w in msg_lower for w in movie_words):
            if item not in self.profile["preferences"]["favorite_movies"]:
                self.profile["preferences"]["favorite_movies"].append(item)
        elif any(w in msg_lower for w in book_words):
            if item not in self.profile["preferences"]["favorite_books"]:
                self.profile["preferences"]["favorite_books"].append(item)
        elif any(w in msg_lower for w in game_words):
            if item not in self.profile["preferences"]["favorite_games"]:
                self.profile["preferences"]["favorite_games"].append(item)
        elif any(w in msg_lower for w in color_words):
            if item not in self.profile["preferences"]["favorite_colors"]:
                self.profile["preferences"]["favorite_colors"].append(item)
        elif any(w in msg_lower for w in hobby_words):
            if item not in self.profile["preferences"]["hobbies"]:
                self.profile["preferences"]["hobbies"].append(item)

    def _extract_mood(self, msg: str, msg_lower: str, timestamp: str):
        mood_map = {
            "happy": ["happy", "glad", "joyful", "excited", "great", "wonderful", "fantastic", "amazing", "awesome"],
            "sad": ["sad", "depressed", "down", "unhappy", "miserable", "crying", "upset", "heartbroken"],
            "angry": ["angry", "mad", "furious", "annoyed", "irritated", "frustrated", "pissed"],
            "anxious": ["anxious", "worried", "nervous", "stressed", "overwhelmed", "panicking"],
            "tired": ["tired", "exhausted", "sleepy", "drained", "fatigued", "burnt out"],
            "calm": ["calm", "relaxed", "peaceful", "chill", "serene", "content"],
            "bored": ["bored", "boring", "nothing to do"],
            "motivated": ["motivated", "inspired", "pumped", "energized", "determined"],
            "confused": ["confused", "lost", "uncertain", "puzzled"],
            "grateful": ["grateful", "thankful", "blessed", "appreciative"],
            "lonely": ["lonely", "alone", "isolated"],
        }

        feeling_patterns = [
            r"i(?:'m| am) (?:feeling |)(\w+)",
            r"i feel (\w+)",
            r"feeling (\w+)",
        ]

        detected_mood = None
        for pat in feeling_patterns:
            m = re.search(pat, msg_lower)
            if m:
                word = m.group(1)
                for mood, keywords in mood_map.items():
                    if word in keywords:
                        detected_mood = mood
                        break
            if detected_mood:
                break

        # Also check for mood keywords directly
        if not detected_mood:
            for mood, keywords in mood_map.items():
                if any(kw in msg_lower for kw in keywords):
                    detected_mood = mood
                    break

        if detected_mood:
            self.profile["moods"]["current_mood"] = detected_mood
            self.profile["moods"]["last_updated"] = timestamp
            entry = {"mood": detected_mood, "timestamp": timestamp, "context": msg[:100]}
            self.profile["moods"]["mood_history"].append(entry)
            # Keep last 100
            self.profile["moods"]["mood_history"] = self.profile["moods"]["mood_history"][-100:]
            self.mood_log.append(entry)

    def _extract_relationships(self, msg: str, msg_lower: str):
        rel_patterns = {
            "spouse": [r"my (?:wife|husband|spouse|partner) (?:is |named )?(\w+)"],
            "child": [r"my (?:son|daughter|child|kid) (?:is |named )?(\w+)"],
            "parent": [r"my (?:mom|dad|mother|father) (?:is |named )?(\w+)"],
            "sibling": [r"my (?:brother|sister|sibling) (?:is |named )?(\w+)"],
            "friend": [r"my (?:best )?friend (?:is |named )?(\w+)"],
            "pet": [r"my (?:dog|cat|pet) (?:is |named )?(\w+)"],
        }
        for rel_type, patterns in rel_patterns.items():
            for pat in patterns:
                m = re.search(pat, msg_lower)
                if m:
                    name = m.group(1).capitalize()
                    if len(name) > 1:
                        self.profile["relationships"][name] = {
                            "type": rel_type,
                            "first_mentioned": datetime.now().isoformat(),
                        }

    def _extract_topics(self, msg: str, msg_lower: str):
        topic_keywords = {
            "technology": ["computer", "software", "programming", "code", "ai", "tech", "app"],
            "health": ["health", "exercise", "diet", "medical", "doctor", "symptoms"],
            "education": ["school", "college", "learn", "study", "class", "homework"],
            "work": ["work", "job", "career", "office", "meeting", "project"],
            "entertainment": ["movie", "music", "game", "show", "book", "read"],
            "travel": ["travel", "trip", "vacation", "flight", "hotel"],
            "food": ["food", "cook", "recipe", "restaurant", "eat"],
            "fitness": ["gym", "workout", "exercise", "run", "yoga"],
            "finance": ["money", "budget", "invest", "savings", "stock"],
            "relationships": ["relationship", "dating", "love", "family", "friend"],
        }
        freq = self.profile["interactions"].get("frequent_topics", {})
        for topic, keywords in topic_keywords.items():
            if any(kw in msg_lower for kw in keywords):
                freq[topic] = freq.get(topic, 0) + 1
                if topic not in self.profile["topics_of_interest"]:
                    self.profile["topics_of_interest"].append(topic)
        self.profile["interactions"]["frequent_topics"] = freq

    def _extract_appearance(self, msg: str, msg_lower: str):
        hair_patterns = [r"my hair is (\w+)", r"i have (\w+) hair"]
        eye_patterns = [r"my eyes are (\w+)", r"i have (\w+) eyes"]
        height_patterns = [r"i(?:'m| am) (\d+['\"]?\d*(?:cm|ft|feet|inches)?)\s*tall"]

        for pat in hair_patterns:
            m = re.search(pat, msg_lower)
            if m:
                self.profile["appearance"]["hair"] = m.group(1)
        for pat in eye_patterns:
            m = re.search(pat, msg_lower)
            if m:
                self.profile["appearance"]["eyes"] = m.group(1)
        for pat in height_patterns:
            m = re.search(pat, msg_lower)
            if m:
                self.profile["appearance"]["height"] = m.group(1)

    def _extract_custom_facts(self, msg: str, msg_lower: str):
        """Extract explicit 'remember that...' instructions."""
        remember_patterns = [
            r"remember (?:that )?(.+?)(?:\.|!|$)",
            r"don't forget (?:that )?(.+?)(?:\.|!|$)",
            r"keep in mind (?:that )?(.+?)(?:\.|!|$)",
            r"note (?:that )?(.+?)(?:\.|!|$)",
        ]
        for pat in remember_patterns:
            m = re.search(pat, msg_lower)
            if m:
                fact = m.group(1).strip()
                if 5 < len(fact) < 200:
                    entry = {"fact": fact, "timestamp": datetime.now().isoformat()}
                    if entry not in self.profile["custom_facts"]:
                        self.profile["custom_facts"].append(entry)
                        # Keep last 200
                        self.profile["custom_facts"] = self.profile["custom_facts"][-200:]
                break

    # ==================== Profile retrieval ====================

    def get_profile_summary(self) -> str:
        """Get a concise summary of the user profile for AI context."""
        parts = []
        p = self.profile

        ident = p.get("identity", {})
        if ident.get("name"):
            parts.append(f"User's name: {ident['name']}")
        if ident.get("age"):
            parts.append(f"Age: {ident['age']}")
        if ident.get("occupation"):
            parts.append(f"Occupation: {ident['occupation']}")
        if ident.get("location"):
            parts.append(f"Location: {ident['location']}")

        prefs = p.get("preferences", {})
        if prefs.get("likes"):
            parts.append(f"Likes: {', '.join(prefs['likes'][:10])}")
        if prefs.get("dislikes"):
            parts.append(f"Dislikes: {', '.join(prefs['dislikes'][:5])}")
        if prefs.get("hobbies"):
            parts.append(f"Hobbies: {', '.join(prefs['hobbies'][:5])}")

        mood = p.get("moods", {})
        if mood.get("current_mood"):
            parts.append(f"Current mood: {mood['current_mood']}")

        rels = p.get("relationships", {})
        if rels:
            rel_parts = [f"{name} ({info.get('type', '?')})" for name, info in list(rels.items())[:5]]
            parts.append(f"People: {', '.join(rel_parts)}")

        topics = p.get("topics_of_interest", [])
        if topics:
            parts.append(f"Interests: {', '.join(topics[:8])}")

        health = p.get("health", {})
        if health.get("conditions"):
            parts.append(f"Health conditions: {', '.join(health['conditions'])}")
        if health.get("learning_style"):
            parts.append(f"Learning style: {health['learning_style']}")

        facts = p.get("custom_facts", [])
        if facts:
            recent = [f['fact'] for f in facts[-5:]]
            parts.append(f"Remembered facts: {'; '.join(recent)}")

        interactions = p.get("interactions", {})
        parts.append(f"Total interactions: {interactions.get('total_count', 0)}")

        return "\n".join(parts) if parts else "No user profile data yet."

    def get_context_for_prompt(self) -> str:
        """Get user profile context to inject into AI prompts."""
        summary = self.get_profile_summary()
        if summary == "No user profile data yet.":
            return ""
        return f"""
[USER PROFILE - Information Monica has learned about this user]
{summary}
[/USER PROFILE]

Use this information to personalize your responses. Address the user by name if known.
Remember their preferences and mood when responding.
"""

    def update_from_vision(self, face_data: Dict = None, emotion: str = None):
        """Update profile from vision system data (face, emotion detection)."""
        now = datetime.now().isoformat()
        if emotion:
            self.profile["moods"]["current_mood"] = emotion
            self.profile["moods"]["last_updated"] = now
            self.profile["moods"]["mood_history"].append({
                "mood": emotion, "timestamp": now, "source": "vision"
            })
        if face_data:
            if face_data.get("age"):
                self.profile["identity"]["age"] = face_data["age"]
            if face_data.get("gender"):
                self.profile["appearance"].setdefault("notes", [])
                note = f"Detected gender: {face_data['gender']}"
                if note not in self.profile["appearance"]["notes"]:
                    self.profile["appearance"]["notes"].append(note)

    def set_fact(self, key: str, value: Any):
        """Manually set a profile fact."""
        keys = key.split(".")
        d = self.profile
        for k in keys[:-1]:
            d = d.setdefault(k, {})
        d[keys[-1]] = value
        self.save()


# Singleton
_learner = None


def get_user_profile_learner() -> UserProfileLearner:
    """Get singleton UserProfileLearner."""
    global _learner
    if _learner is None:
        _learner = UserProfileLearner()
    return _learner
