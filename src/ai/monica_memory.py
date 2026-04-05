"""
Monica Memory System
Allows Monica to store and recall information that users teach her.
Persistent storage using JSON file.
"""

import json
import os
from datetime import datetime
from typing import Optional, List, Dict, Any

class MonicaMemory:
    """
    Persistent memory system for Monica AI.
    Stores facts, corrections, and learned information.
    """
    
    def __init__(self, memory_file: str = None):
        if memory_file is None:
            # Store in monica_ai directory
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            memory_file = os.path.join(base_dir, 'monica_memories.json')
        
        self.memory_file = memory_file
        self.memories: Dict[str, Any] = {
            'facts': [],           # General facts Monica learns
            'corrections': [],     # Corrections to her knowledge
            'user_preferences': {},# User preferences
            'important_dates': [], # Important dates to remember
            'people': {},          # Information about people
            'current_events': [],  # Current events/news
        }
        self._load_memories()
        print(f"[OK] Monica Memory System initialized ({len(self.memories['facts'])} facts, {len(self.memories['corrections'])} corrections)")
    
    def _load_memories(self):
        """Load memories from file."""
        try:
            if os.path.exists(self.memory_file):
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    # Merge with default structure
                    for key in self.memories:
                        if key in loaded:
                            self.memories[key] = loaded[key]
        except Exception as e:
            print(f"[MEMORY] Error loading memories: {e}")
    
    def _save_memories(self):
        """Save memories to file."""
        try:
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(self.memories, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[MEMORY] Error saving memories: {e}")
    
    def store_fact(self, fact: str, category: str = 'general', source: str = 'user') -> bool:
        """Store a new fact."""
        try:
            memory_entry = {
                'fact': fact,
                'category': category,
                'source': source,
                'timestamp': datetime.now().isoformat(),
            }
            self.memories['facts'].append(memory_entry)
            self._save_memories()
            print(f"[MEMORY] Stored fact: {fact}")
            return True
        except Exception as e:
            print(f"[MEMORY] Error storing fact: {e}")
            return False
    
    def store_correction(self, wrong_info: str, correct_info: str, source: str = 'user') -> bool:
        """Store a correction to Monica's knowledge."""
        try:
            correction_entry = {
                'wrong': wrong_info,
                'correct': correct_info,
                'source': source,
                'timestamp': datetime.now().isoformat(),
            }
            self.memories['corrections'].append(correction_entry)
            self._save_memories()
            print(f"[MEMORY] Stored correction: {wrong_info} -> {correct_info}")
            return True
        except Exception as e:
            print(f"[MEMORY] Error storing correction: {e}")
            return False
    
    def store_current_event(self, event: str, date: str = None) -> bool:
        """Store a current event."""
        try:
            if date is None:
                date = datetime.now().strftime('%Y-%m-%d')
            event_entry = {
                'event': event,
                'date': date,
                'timestamp': datetime.now().isoformat(),
            }
            self.memories['current_events'].append(event_entry)
            self._save_memories()
            print(f"[MEMORY] Stored current event: {event}")
            return True
        except Exception as e:
            print(f"[MEMORY] Error storing event: {e}")
            return False
    
    def store_person_info(self, name: str, info: str) -> bool:
        """Store information about a person."""
        try:
            if name not in self.memories['people']:
                self.memories['people'][name] = []
            self.memories['people'][name].append({
                'info': info,
                'timestamp': datetime.now().isoformat(),
            })
            self._save_memories()
            print(f"[MEMORY] Stored info about {name}: {info}")
            return True
        except Exception as e:
            print(f"[MEMORY] Error storing person info: {e}")
            return False
    
    def search_memories(self, query: str) -> List[str]:
        """Search all memories for relevant information."""
        results = []
        query_lower = query.lower()
        
        # Search facts
        for fact in self.memories['facts']:
            if query_lower in fact['fact'].lower():
                results.append(f"Fact: {fact['fact']}")
        
        # Search corrections
        for correction in self.memories['corrections']:
            if query_lower in correction['correct'].lower() or query_lower in correction['wrong'].lower():
                results.append(f"Correction: {correction['correct']} (not {correction['wrong']})")
        
        # Search current events
        for event in self.memories['current_events']:
            if query_lower in event['event'].lower():
                results.append(f"Event ({event['date']}): {event['event']}")
        
        # Search people
        for name, info_list in self.memories['people'].items():
            if query_lower in name.lower():
                for info in info_list:
                    results.append(f"About {name}: {info['info']}")
        
        return results
    
    def get_context_for_query(self, query: str) -> str:
        """Get relevant memory context for a query."""
        results = self.search_memories(query)
        if results:
            return "Based on what I've learned: " + "; ".join(results[:5])
        return ""
    
    def get_all_corrections(self) -> List[Dict]:
        """Get all stored corrections."""
        return self.memories['corrections']
    
    def get_recent_events(self, limit: int = 10) -> List[Dict]:
        """Get recent current events."""
        return self.memories['current_events'][-limit:]


# Singleton instance
_memory_instance = None

def get_monica_memory() -> MonicaMemory:
    """Get the singleton MonicaMemory instance."""
    global _memory_instance
    if _memory_instance is None:
        _memory_instance = MonicaMemory()
    return _memory_instance
