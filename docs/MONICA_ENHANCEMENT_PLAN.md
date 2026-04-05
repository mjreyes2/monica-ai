# Monica AI Enhancement Plan: State-of-the-Art Memory, Reasoning, and Speech

## Executive Summary

This document outlines the comprehensive upgrade strategy for Monica AI, transforming her from a basic Excel-based memory system to a state-of-the-art AI with advanced cognitive capabilities.

### Current State
- **Memory**: Basic `ExcelMemoryStore` with simple append/recent queries
- **Reasoning**: None (direct event logging only)
- **Speech**: No TTS or STT capabilities
- **Advanced Modules**: NightWatcher, EmotionFusion, PresenceGauge (already implemented)

### Target State
- **Memory**: Multi-layer semantic memory with vector embeddings (Mem0)
- **Reasoning**: Chain-of-thought, planning, self-reflection
- **Speech**: Real-time TTS/STT with emotion awareness and voice cloning

---

## Phase 1: Memory System Upgrade (HIGH PRIORITY)

### 1.1 Replace ExcelMemoryStore with Mem0-Powered System

**Resources Available:**
- ✅ Full Mem0 library already in `external/mem0/`
- ✅ Comprehensive documentation
- ✅ Multiple integration examples (CrewAI, LlamaIndex, LangChain)

**Implementation Strategy:**

```python
# New file: mem0_memory_store.py

from mem0 import Memory
from typing import List, Dict, Optional
import json

class Mem0MemoryStore:
    """
    Advanced memory store powered by Mem0 with semantic search,
    multi-layer storage, and episodic/procedural memory.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        # Configure Mem0 with Qdrant vector store
        self.config = {
            "vector_store": {
                "provider": "qdrant",
                "config": {
                    "collection_name": "monica_memories",
                    "path": "./data/qdrant_db"  # Local storage
                }
            },
            "llm": {
                "provider": "ollama",  # Free local LLM
                "config": {
                    "model": "llama3.2:latest",
                    "temperature": 0.2
                }
            },
            "embedder": {
                "provider": "sentence-transformers",
                "config": {
                    "model": "all-MiniLM-L6-v2"  # Fast, lightweight
                }
            }
        }
        
        self.memory = Memory.from_config(self.config)
        
    def append(self, speaker: str, event: str, content: str, 
               tags: str = "", extra: str = ""):
        """
        Add memory with semantic indexing (backward compatible).
        """
        # Construct rich message for semantic understanding
        message = {
            "role": speaker.lower(),
            "content": f"[{event}] {content}"
        }
        
        # Parse metadata
        metadata = {
            "event": event,
            "tags": tags.split(",") if tags else [],
            "speaker": speaker
        }
        
        if extra:
            try:
                extra_dict = json.loads(extra)
                metadata.update(extra_dict)
            except:
                metadata["extra"] = extra
        
        # Add to Mem0 (automatically creates embeddings)
        result = self.memory.add(
            [message],
            user_id="monica",
            metadata=metadata
        )
        
        return result
    
    def recent(self, limit: int = 25) -> List[Dict]:
        """
        Get recent memories (backward compatible).
        """
        # Get all memories sorted by recency
        results = self.memory.get_all(user_id="monica")
        
        # Format for compatibility
        formatted = []
        for mem in results[-limit:]:
            formatted.append({
                "timestamp": mem.get("created_at", ""),
                "speaker": mem["metadata"].get("speaker", "unknown"),
                "event": mem["metadata"].get("event", ""),
                "content": mem["memory"],
                "tags": ",".join(mem["metadata"].get("tags", [])),
                "extra": ""
            })
        
        return formatted
    
    def search_semantic(self, query: str, limit: int = 10, 
                       filters: Optional[Dict] = None) -> List[Dict]:
        """
        NEW: Semantic search across all memories.
        
        Examples:
        - "What does Monica like?" → finds preference memories
        - "Emotions detected last week" → temporal + semantic
        - "Face detection errors" → technical event search
        """
        results = self.memory.search(
            query=query,
            user_id="monica",
            filters=filters
        )
        
        return [r["memory"] for r in results[:limit]]
    
    def create_procedural_memory(self, skill: str, context: List[Dict]):
        """
        NEW: Learn procedures from conversation history.
        
        Example: Learn "how to handle low-light scenes" from
        past NightWatcher interactions.
        """
        # Mem0's procedural memory creation
        result = self.memory._create_procedural_memory(
            messages=context,
            metadata={"skill": skill, "type": "procedural"}
        )
        return result
    
    def get_context_for_event(self, event_type: str, limit: int = 5) -> str:
        """
        NEW: Get relevant memories for current event.
        Used by reasoning system to make informed decisions.
        """
        results = self.memory.search(
            query=f"Previous {event_type} events",
            user_id="monica",
            filters={"event": event_type}
        )
        
        context = "\n".join([
            f"- {r['memory']}" for r in results[:limit]
        ])
        
        return context or "No prior context available."
```

**Dependencies to Install:**
```bash
pip install mem0ai qdrant-client sentence-transformers ollama
```

**Migration Strategy:**
1. Keep `ExcelMemoryStore` for backward compatibility
2. Add `Mem0MemoryStore` as new option
3. Provide migration script to convert Excel → Qdrant
4. Update `MonicaAI` to use new store

**Benefits:**
- ✅ Semantic search: "What makes Monica happy?" instead of scanning rows
- ✅ Automatic memory consolidation (Mem0 deduplicates)
- ✅ Multi-layer: Conversation → Session → User memory
- ✅ Procedural learning: Monica learns from experience
- ✅ Scalable: Handles millions of memories efficiently

---

## Phase 2: Speech Capabilities (HIGH PRIORITY)

### 2.1 Text-to-Speech (TTS) Integration

**Resources Available:**
- ✅ SpeechBrain library in `external/speechbrain/`
- ✅ Whisper in `external/whisper/`
- ✅ PsychoPy TTS support (gTTS)
- ✅ Sound effects library in `external/Free-Sound-Effects-Library/`

**Implementation Options:**

#### Option A: PsychoPy + gTTS (Online, Simple)
```python
from psychopy.sound import AudioClip

# Quick implementation
voice_clip = AudioClip.synthesizeSpeech(
    "Hello! I'm Monica.",
    engine='gtts',
    synthConfig={'lang': 'en', 'tld': 'us', 'slow': False}
)
voice_clip.play()
```

**Pros:** Already in codebase, zero setup  
**Cons:** Online only, generic voice, no emotion control

#### Option B: Coqui TTS (Offline, Voice Cloning)
```python
from TTS.api import TTS

# One-shot voice cloning from reference
tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
tts.tts_with_vc_to_file(
    text="I can speak in any voice!",
    file_path="output.wav",
    speaker_wav="data/voice_reference.wav"
)
```

**Pros:** Voice cloning, emotion control, offline  
**Cons:** Requires ~2GB model download

#### Option C: Piper TTS (Offline, Fast, Lightweight)
```bash
pip install piper-tts
```

```python
from piper import PiperVoice

voice = PiperVoice.load("en_US-lessac-medium")
voice.synthesize("Fast and lightweight!", "output.wav")
```

**Pros:** Fast (real-time), small models (<100MB), offline  
**Cons:** Limited voice variety

**Recommended:** **Piper for real-time + Coqui for voice cloning**

### 2.2 Speech-to-Text (STT) Integration

**Resources Available:**
- ✅ Whisper already in `external/whisper/`
- ✅ SpeechBrain speech enhancement

**Implementation:**

```python
import whisper
import numpy as np

class MonicaSpeechRecognizer:
    def __init__(self):
        # Load Whisper model (base = 150MB, medium = 500MB)
        self.model = whisper.load_model("base")
        
    def transcribe_audio(self, audio_file: str) -> Dict:
        """
        Transcribe audio with timestamps and language detection.
        """
        result = self.model.transcribe(
            audio_file,
            language="en",  # Auto-detect if None
            task="transcribe",
            word_timestamps=True
        )
        
        return {
            "text": result["text"],
            "language": result["language"],
            "segments": result["segments"]  # With timestamps
        }
    
    def transcribe_stream(self, audio_chunk: np.ndarray) -> str:
        """
        Real-time streaming transcription.
        """
        # Convert chunk to WAV
        temp_wav = self._numpy_to_wav(audio_chunk)
        
        result = self.model.transcribe(temp_wav)
        return result["text"]
```

**Dependencies:**
```bash
pip install openai-whisper  # Already cloned
```

**Benefits:**
- ✅ Multilingual (99 languages)
- ✅ Offline processing
- ✅ Speaker diarization (who spoke when)
- ✅ Timestamp precision for video sync

### 2.3 Voice Analysis & Emotion Detection

**Using SpeechBrain:**

```python
from speechbrain.pretrained import EncoderClassifier

class VoiceAnalyzer:
    def __init__(self):
        # Speaker recognition
        self.speaker_model = EncoderClassifier.from_hparams(
            source="speechbrain/spkrec-ecapa-voxceleb"
        )
        
        # Emotion recognition
        self.emotion_model = EncoderClassifier.from_hparams(
            source="speechbrain/emotion-recognition-wav2vec2"
        )
    
    def identify_speaker(self, audio_file: str) -> np.ndarray:
        """
        Get speaker embedding (for recognition).
        """
        embedding = self.speaker_model.encode_batch(audio_file)
        return embedding
    
    def detect_emotion(self, audio_file: str) -> Dict:
        """
        Detect emotion from voice.
        """
        prediction = self.emotion_model.classify_file(audio_file)
        
        return {
            "emotion": prediction[3][0],  # Top emotion
            "confidence": prediction[1].exp()[0].tolist()
        }
```

**Benefits:**
- ✅ Speaker identification (who is speaking?)
- ✅ Voice emotion detection (complement video emotion)
- ✅ Voice-based authentication

---

## Phase 3: Reasoning & Thinking Capabilities (MEDIUM PRIORITY)

### 3.1 Reasoning Architecture

**Resources Available:**
- ✅ Mem0 integrates with LangChain, LlamaIndex, CrewAI
- ✅ Multiple LLM providers supported (OpenAI, Anthropic, Ollama, etc.)
- ✅ Reasoning examples in `external/mem0/docs/`

**Architecture:**

```
User Event → Memory Retrieval → Reasoning Chain → Action → Memory Update
     ↓              ↓                   ↓             ↓           ↓
Face Detected → "Who is this?" → Check face_memory → Greet → Log interaction
                     ↓
              Semantic search:
              "Last time this person visited?"
                     ↓
              Context: "Preferred greeting style?"
                     ↓
              Decision: "Use formal vs casual tone"
```

**Implementation:**

```python
from mem0 import Memory
import ollama  # Free local LLM

class MonicaReasoning:
    """
    Reasoning engine with memory-augmented generation.
    """
    
    def __init__(self, memory: Memory):
        self.memory = memory
        self.llm_model = "llama3.2:latest"  # Or GPT-4, Claude, etc.
        
    def reason(self, situation: str, context: Dict) -> Dict:
        """
        Multi-step reasoning with memory retrieval.
        
        Steps:
        1. Understand situation
        2. Retrieve relevant memories
        3. Generate reasoning chain
        4. Decide action
        5. Log decision
        """
        
        # Step 1: Retrieve context from memory
        relevant_memories = self.memory.search(
            query=situation,
            user_id="monica",
            filters=context.get("filters")
        )
        
        memory_context = "\n".join([
            f"- {m['memory']}" for m in relevant_memories
        ])
        
        # Step 2: Construct reasoning prompt
        prompt = f"""You are Monica, an AI with emotional intelligence and long-term memory.

Situation: {situation}

Relevant Memories:
{memory_context}

Current Context: {json.dumps(context, indent=2)}

Think step-by-step:
1. What is happening right now?
2. What do I remember about this situation?
3. What emotions should I consider?
4. What is the best action to take?
5. Why is this the right decision?

Provide your reasoning and final decision."""

        # Step 3: Generate reasoning
        response = ollama.chat(
            model=self.llm_model,
            messages=[{"role": "user", "content": prompt}]
        )
        
        reasoning_text = response["message"]["content"]
        
        # Step 4: Extract decision
        decision = self._parse_decision(reasoning_text)
        
        # Step 5: Log reasoning to memory
        self.memory.add(
            messages=[{
                "role": "assistant",
                "content": f"Reasoning: {reasoning_text}"
            }],
            user_id="monica",
            metadata={
                "type": "reasoning",
                "situation": situation,
                "decision": decision
            }
        )
        
        return {
            "reasoning": reasoning_text,
            "decision": decision,
            "memories_used": len(relevant_memories)
        }
    
    def _parse_decision(self, reasoning: str) -> str:
        """
        Extract final decision from reasoning text.
        """
        # Simple parsing (can be improved with structured output)
        lines = reasoning.split("\n")
        for line in lines:
            if "decision:" in line.lower():
                return line.split(":", 1)[1].strip()
        
        return "No explicit decision found"
    
    def plan_sequence(self, goal: str) -> List[str]:
        """
        Plan a sequence of actions to achieve a goal.
        
        Example: Goal = "Create welcoming atmosphere"
        Output: ["Dim lights", "Play soft music", "Display greeting"]
        """
        prompt = f"""Break down this goal into actionable steps:

Goal: {goal}

Provide 3-5 concrete steps Monica can take."""

        response = ollama.chat(
            model=self.llm_model,
            messages=[{"role": "user", "content": prompt}]
        )
        
        # Parse steps (simple line-based parsing)
        steps = [
            line.strip("- ").strip() 
            for line in response["message"]["content"].split("\n")
            if line.strip().startswith("-") or line.strip()[0].isdigit()
        ]
        
        return steps
```

### 3.2 Integration with Advanced Modules

**Example: Memory-Aware NightWatcher**

```python
class MemoryAwareNightWatcher(NightWatcher):
    """
    Enhanced NightWatcher that learns from past low-light experiences.
    """
    
    def __init__(self, memory: Memory, reasoning: MonicaReasoning):
        super().__init__()
        self.memory = memory
        self.reasoning = reasoning
        
    def process_low_light(self, frame, light_level: float):
        """
        Process low-light scene with learned strategies.
        """
        # Get past experiences
        context = self.reasoning.reason(
            situation=f"Low light detected (level: {light_level})",
            context={
                "filters": {"event": "low_light_processing"},
                "light_level": light_level
            }
        )
        
        # Apply learned strategy
        if "increase_gain" in context["decision"]:
            enhanced = self.enhance_with_gain(frame)
        elif "use_infrared" in context["decision"]:
            enhanced = self.switch_to_infrared(frame)
        else:
            enhanced = super().process_low_light(frame, light_level)
        
        # Log result for future learning
        self.memory.add(
            messages=[{
                "role": "system",
                "content": f"Low light processing successful with strategy: {context['decision']}"
            }],
            user_id="monica",
            metadata={
                "event": "low_light_processing",
                "light_level": light_level,
                "strategy": context["decision"]
            }
        )
        
        return enhanced
```

**Benefits:**
- ✅ Learns from mistakes (procedural memory)
- ✅ Adapts strategies based on success rate
- ✅ Explains decisions (transparency)
- ✅ Plans multi-step actions

### 3.3 LLM Provider Options

**Free/Local Options (No API Keys):**
1. **Ollama** (Recommended)
   - Models: Llama 3.2, Mistral, Phi-3
   - Setup: `ollama pull llama3.2`
   - Speed: Fast on CPU

2. **LM Studio**
   - Already supported in Mem0
   - GUI for model management
   - Runs locally

**Paid Options (Best Quality):**
1. **OpenAI GPT-4o** - Best reasoning
2. **Anthropic Claude 3.5 Sonnet** - Long context
3. **Groq** - Fastest inference

**Configuration:**
```python
# For Ollama (Free)
config = {
    "llm": {
        "provider": "ollama",
        "config": {
            "model": "llama3.2:latest"
        }
    }
}

# For OpenAI (if API key available)
config = {
    "llm": {
        "provider": "openai",
        "config": {
            "model": "gpt-4o-mini",
            "api_key": os.getenv("OPENAI_API_KEY")
        }
    }
}
```

---

## Implementation Roadmap

### Week 1-2: Memory System
- [x] Install Mem0 dependencies
- [ ] Create `Mem0MemoryStore` class
- [ ] Write Excel → Qdrant migration script
- [ ] Update `MonicaAI` to use new memory
- [ ] Test backward compatibility

### Week 3-4: Speech Integration
- [ ] Install Whisper + Piper TTS
- [ ] Create `MonicaSpeechRecognizer` class
- [ ] Create `MonicaTTS` class
- [ ] Add voice emotion detection (SpeechBrain)
- [ ] Test real-time transcription

### Week 5-6: Reasoning System
- [ ] Install Ollama (or choose LLM provider)
- [ ] Create `MonicaReasoning` class
- [ ] Integrate with existing modules
- [ ] Add planning capabilities
- [ ] Test memory-augmented reasoning

### Week 7: Integration & Testing
- [ ] Integrate all components into `MonicaAI`
- [ ] Create configuration system
- [ ] Write comprehensive tests
- [ ] Update documentation
- [ ] Performance optimization

---

## Configuration File Structure

**New file: `monica_enhanced_config.json`**

```json
{
  "memory": {
    "provider": "mem0",
    "backend": {
      "vector_store": "qdrant",
      "path": "./data/qdrant_db"
    },
    "embedder": {
      "model": "all-MiniLM-L6-v2"
    },
    "llm": {
      "provider": "ollama",
      "model": "llama3.2:latest"
    }
  },
  "speech": {
    "tts": {
      "provider": "piper",
      "voice": "en_US-lessac-medium",
      "speed": 1.0
    },
    "stt": {
      "provider": "whisper",
      "model": "base",
      "language": "en"
    },
    "voice_analysis": {
      "emotion_detection": true,
      "speaker_recognition": true
    }
  },
  "reasoning": {
    "enabled": true,
    "llm": {
      "provider": "ollama",
      "model": "llama3.2:latest",
      "temperature": 0.2
    },
    "memory_context_limit": 10,
    "thinking_mode": "chain-of-thought"
  },
  "advanced_modules": {
    "night_watcher": true,
    "emotion_fusion": true,
    "presence_gauge": true
  }
}
```

---

## Estimated Resource Requirements

### Storage
- Mem0 + Qdrant DB: ~500MB (grows with memories)
- Whisper base model: 150MB
- Piper TTS voices: 50-100MB each
- Ollama Llama 3.2: 2GB
- **Total: ~3-4GB**

### RAM
- Mem0: ~500MB
- Whisper: ~1GB during transcription
- Ollama: ~4GB during inference
- **Peak: ~6GB**

### Performance
- Memory search: <50ms (Qdrant vector search)
- TTS generation: ~1-2s for 10 seconds of speech
- STT transcription: Real-time (Whisper base)
- LLM reasoning: 2-5s per response (Ollama on CPU)

---

## Benefits Summary

### Memory (Mem0)
- ✅ **Semantic understanding**: "What makes users happy?" instead of keyword search
- ✅ **Automatic consolidation**: No duplicate memories
- ✅ **Multi-layer storage**: Short-term, long-term, procedural
- ✅ **Scalable**: Handles millions of entries
- ✅ **Learning**: Improves over time

### Speech (Whisper + Piper/Coqui)
- ✅ **Real-time STT**: Live transcription during streaming
- ✅ **Voice cloning**: Monica can speak in any voice
- ✅ **Emotion detection**: Detect user mood from voice
- ✅ **Multilingual**: 99 languages supported
- ✅ **Offline**: No internet required

### Reasoning (Ollama + Mem0)
- ✅ **Context-aware**: Uses past experiences to decide
- ✅ **Explainable**: Shows reasoning process
- ✅ **Planning**: Multi-step action sequences
- ✅ **Adaptive**: Learns from outcomes
- ✅ **Free**: Runs locally on Ollama

---

## Next Steps

1. **Immediate**: Install Mem0 dependencies
   ```bash
   pip install mem0ai qdrant-client sentence-transformers
   ```

2. **Setup Ollama** (for reasoning):
   ```bash
   # Windows
   winget install Ollama.Ollama
   ollama pull llama3.2
   ```

3. **Install Speech Tools**:
   ```bash
   pip install openai-whisper piper-tts
   ```

4. **Begin Implementation**: Start with Phase 1 (Memory System)

---

## Questions to Answer

1. **LLM Choice**: Ollama (free, local) or OpenAI/Claude (best quality, requires API key)?
2. **TTS Choice**: Piper (fast, simple) or Coqui (voice cloning, more complex)?
3. **Deployment**: Desktop app or also enable remote access?
4. **Privacy**: Keep all processing local or allow cloud LLMs?

---

**Ready to proceed with implementation?**
