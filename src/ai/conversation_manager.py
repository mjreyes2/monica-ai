"""
Conversation Manager for Monica AI.
Tracks conversation history, context, and user memory.
"""

import time
import json
import logging
from typing import List, Dict, Optional, Any
from pathlib import Path
from dataclasses import dataclass, field

logger = logging.getLogger("Monica.Conversation")


@dataclass
class ConversationTurn:
    """A single turn in the conversation."""
    role: str  # 'user', 'assistant', 'system'
    content: str
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ConversationManager:
    """
    Manages conversation history, context window, and persistence.
    
    Features:
    - Conversation history tracking
    - Context window management for LLM prompts
    - Conversation persistence (save/load)
    - User memory integration
    """

    def __init__(self, max_history: int = 50, persist_path: Optional[str] = None):
        self.max_history = max_history
        self.history: List[ConversationTurn] = []
        self.persist_path = Path(persist_path) if persist_path else None
        self.conversation_id = f"conv_{int(time.time())}"
        
        # Load previous conversation if path exists
        if self.persist_path and self.persist_path.exists():
            self._load()
        
        logger.info(f"ConversationManager ready (max_history={max_history})")

    def add_user_message(self, text: str, **metadata) -> ConversationTurn:
        """Add a user message to history."""
        turn = ConversationTurn(role="user", content=text, metadata=metadata)
        self._add_turn(turn)
        return turn

    def add_assistant_message(self, text: str, **metadata) -> ConversationTurn:
        """Add an assistant message to history."""
        turn = ConversationTurn(role="assistant", content=text, metadata=metadata)
        self._add_turn(turn)
        return turn

    def add_system_message(self, text: str, **metadata) -> ConversationTurn:
        """Add a system message to history."""
        turn = ConversationTurn(role="system", content=text, metadata=metadata)
        self._add_turn(turn)
        return turn

    def _add_turn(self, turn: ConversationTurn):
        """Add a turn and trim history if needed."""
        self.history.append(turn)
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
        
        # Auto-save if persist path is set
        if self.persist_path:
            self._save()

    def get_context_messages(self, max_turns: int = 20) -> List[Dict[str, str]]:
        """
        Get recent conversation as a list of message dicts
        suitable for Ollama/OpenAI chat format.
        """
        recent = self.history[-max_turns:] if len(self.history) > max_turns else self.history
        return [{"role": t.role, "content": t.content} for t in recent]

    def get_last_user_message(self) -> Optional[str]:
        """Get the most recent user message."""
        for turn in reversed(self.history):
            if turn.role == "user":
                return turn.content
        return None

    def get_last_assistant_message(self) -> Optional[str]:
        """Get the most recent assistant message."""
        for turn in reversed(self.history):
            if turn.role == "assistant":
                return turn.content
        return None

    def clear(self):
        """Clear conversation history."""
        self.history.clear()
        self.conversation_id = f"conv_{int(time.time())}"

    def _save(self):
        """Save conversation to disk."""
        if not self.persist_path:
            return
        try:
            self.persist_path.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "conversation_id": self.conversation_id,
                "turns": [
                    {
                        "role": t.role,
                        "content": t.content,
                        "timestamp": t.timestamp,
                        "metadata": t.metadata,
                    }
                    for t in self.history
                ],
            }
            with open(self.persist_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.debug(f"Conversation save error: {e}")

    def _load(self):
        """Load conversation from disk."""
        if not self.persist_path or not self.persist_path.exists():
            return
        try:
            with open(self.persist_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.conversation_id = data.get("conversation_id", self.conversation_id)
            for t in data.get("turns", []):
                self.history.append(
                    ConversationTurn(
                        role=t["role"],
                        content=t["content"],
                        timestamp=t.get("timestamp", 0),
                        metadata=t.get("metadata", {}),
                    )
                )
            logger.info(f"Loaded {len(self.history)} turns from {self.persist_path}")
        except Exception as e:
            logger.debug(f"Conversation load error: {e}")

    def __len__(self):
        return len(self.history)

    def __repr__(self):
        return f"ConversationManager(turns={len(self.history)}, id={self.conversation_id})"
