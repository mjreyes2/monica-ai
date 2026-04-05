# Monica AI Enhancement - Quick Reference Card

## 📋 TL;DR

**What?** Upgrade Monica from basic Excel memory to state-of-the-art AI with semantic memory, speech I/O, and reasoning.

**Why?** Enable Monica to understand context, learn from experience, speak naturally, and make intelligent decisions.

**How?** Use Mem0 (memory), Whisper (STT), Piper/Coqui (TTS), and Ollama/GPT (reasoning) - all already in your workspace!

**Cost?** FREE with local tools (Ollama, Piper, Whisper) or paid with cloud LLMs (OpenAI, Claude)

---

## 🚀 One-Command Install

```bash
python install_enhancements.py
```

---

## 📊 Capabilities Comparison

| Feature | Before (Current) | After (Enhanced) |
|---------|------------------|------------------|
| **Memory** | Excel rows (append/recent) | Vector DB (semantic search) |
| **Search** | "Get last 25 entries" | "What makes the user happy?" |
| **Learning** | None (static logs) | Learns from experience |
| **Speech Input** | ❌ None | ✅ Real-time transcription (99 languages) |
| **Speech Output** | ❌ None | ✅ TTS with voice cloning |
| **Reasoning** | ❌ None | ✅ Chain-of-thought, planning |
| **Context** | ❌ No understanding | ✅ Remembers past interactions |
| **Adaptation** | ❌ Fixed behavior | ✅ Improves over time |
| **Scale** | ~1K memories max | Millions of memories |

---

## 🎯 Key Benefits

### Memory (Mem0)
- **Semantic Search**: Ask "What activities make users happy?" instead of scanning rows
- **Auto-Consolidation**: Deduplicates similar memories automatically
- **Multi-Layer**: Short-term ↔ Long-term ↔ Procedural (learned skills)
- **Scalable**: Handles millions of entries with <50ms search time

### Speech (Whisper + Piper)
- **Real-Time STT**: Live transcription during streaming
- **Voice Cloning**: Monica can speak in any voice (Coqui TTS)
- **Emotion Detection**: Detect user mood from voice tone
- **Multilingual**: 99 languages supported
- **Offline**: No internet required

### Reasoning (Ollama/GPT)
- **Context-Aware**: "Last time this happened, user preferred..."
- **Explainable**: Shows reasoning process step-by-step
- **Planning**: Breaks goals into actionable steps
- **Adaptive**: Learns from outcomes and improves

---

## 💻 Installation Options

### Option 1: Full Stack (Recommended)
```bash
# Install all dependencies
python install_enhancements.py

# Install Ollama (local LLM)
# Download from: https://ollama.com/download
ollama pull llama3.2

# Test installation
python test_enhancements.py
```

### Option 2: Minimal (Memory + Speech Only)
```bash
pip install mem0ai qdrant-client sentence-transformers
pip install openai-whisper piper-tts
```

### Option 3: Cloud-Only (No Local LLM)
```bash
pip install mem0ai qdrant-client sentence-transformers
pip install openai-whisper gtts

# Add to .env:
# OPENAI_API_KEY=sk-...
```

---

## 📁 Files Created

| File | Purpose |
|------|---------|
| **MONICA_ENHANCEMENT_PLAN.md** | Full technical documentation (40+ pages) |
| **ENHANCEMENT_SUMMARY.md** | Executive summary with examples |
| **ARCHITECTURE_DIAGRAM.md** | Visual system architecture |
| **QUICK_REFERENCE.md** | This quick reference card |
| **install_enhancements.py** | One-click installer script |
| **test_enhancements.py** | Component testing (created by installer) |
| **env.template** | Configuration template (created by installer) |

---

## 🔧 Configuration

### Minimal Config (Free, Local)
```python
config = {
    "memory": {
        "provider": "mem0",
        "llm": {"provider": "ollama", "model": "llama3.2"}
    },
    "speech": {
        "stt": {"provider": "whisper", "model": "base"},
        "tts": {"provider": "piper", "voice": "en_US-lessac-medium"}
    },
    "reasoning": {
        "llm": {"provider": "ollama", "model": "llama3.2"}
    }
}
```

### Premium Config (Cloud)
```python
config = {
    "memory": {
        "provider": "mem0",
        "llm": {"provider": "openai", "model": "gpt-4o-mini"}
    },
    "speech": {
        "stt": {"provider": "whisper", "model": "base"},
        "tts": {"provider": "coqui", "voice": "custom_cloned"}
    },
    "reasoning": {
        "llm": {"provider": "openai", "model": "gpt-4o"}
    }
}
```

---

## 📚 Code Examples

### Example 1: Semantic Memory Search
```python
# OLD: Get recent entries
memories = memory.recent(limit=25)

# NEW: Semantic search
results = memory.search_semantic(
    "What activities make the user smile?",
    filters={"emotion": "positive"}
)
# Returns: "User smiled during music playback", "Happy when lights dimmed", etc.
```

### Example 2: Speech Recognition
```python
from monica_speech import MonicaSpeechRecognizer

recognizer = MonicaSpeechRecognizer()
result = recognizer.transcribe_audio("user_input.wav")

print(result["text"])  # "Hello Monica, dim the lights please"
print(result["language"])  # "en"
```

### Example 3: Text-to-Speech
```python
from monica_speech import MonicaTTS

tts = MonicaTTS()
audio = tts.speak(
    "I've dimmed the lights to your preferred level.",
    emotion="friendly"
)
audio.play()
```

### Example 4: Memory-Augmented Reasoning
```python
from monica_reasoning import MonicaReasoning

reasoning = MonicaReasoning(memory=memory)
result = reasoning.reason(
    situation="User entered room at night",
    context={"time": "22:00", "light_level": 0.3}
)

print(result["reasoning"])
# "1. Late hour (22:00)
#  2. Memory: User prefers dim lighting at night
#  3. Current light too bright
#  4. Action: Dim to 20%, warm color temp
#  5. Reason: Creates relaxing evening atmosphere"

print(result["decision"])
# "Dim lights to 20%, set warm color (2700K)"
```

---

## ⚡ Performance

| Operation | Time | Hardware |
|-----------|------|----------|
| Memory search | <50ms | CPU |
| Speech recognition | Real-time | CPU (Whisper base) |
| TTS generation | 1-2s for 10s audio | CPU (Piper) |
| LLM reasoning | 2-5s | CPU (Ollama) |
| LLM reasoning | <1s | GPU or cloud (GPT-4) |

---

## 💾 Resource Requirements

### Minimal Setup
- **Storage**: ~1GB (Mem0 + Whisper + Piper)
- **RAM**: ~2GB peak
- **Performance**: Real-time on CPU

### Full Setup (with Ollama)
- **Storage**: ~4GB (+ Ollama models)
- **RAM**: ~6GB peak
- **Performance**: 2-5s reasoning on CPU

---

## 🎓 Learning Curve

### Easy (1 hour)
- Install dependencies
- Configure settings
- Run tests
- See examples work

### Medium (1 day)
- Understand Mem0 architecture
- Implement basic memory wrapper
- Add speech I/O to one module

### Advanced (1 week)
- Full integration with all modules
- Custom reasoning chains
- Performance optimization
- Production deployment

---

## 🐛 Troubleshooting

### "Ollama not found"
```bash
# Install Ollama from: https://ollama.com/download
# Then: ollama pull llama3.2
```

### "Qdrant connection failed"
```bash
# Qdrant runs locally, no installation needed
# Check path in config: "./data/qdrant_db"
```

### "Whisper too slow"
```python
# Use smaller model
config = {"stt": {"model": "tiny"}}  # Faster but less accurate
```

### "Out of memory"
```python
# Use lighter models
# Whisper: tiny/base instead of medium/large
# Ollama: llama3.2:1b instead of llama3.2:3b
```

---

## 🔐 API Keys (Optional)

**Free Tier (No Keys):**
- Ollama (local LLM)
- Whisper (local STT)
- Piper (local TTS)
- Mem0 (local vector DB)

**Paid Services (Requires Keys):**
- OpenAI: `OPENAI_API_KEY=sk-...`
- Anthropic: `ANTHROPIC_API_KEY=sk-ant-...`
- Google Cloud: `GOOGLE_API_KEY=...`

Add to `.env` file or environment variables.

---

## 📈 Implementation Phases

### Phase 1: Memory (Week 1-2) 🎯 START HERE
```bash
pip install mem0ai qdrant-client sentence-transformers
# Create mem0_memory_store.py
# Test semantic search
```

### Phase 2: Speech (Week 3-4)
```bash
pip install openai-whisper piper-tts
# Create monica_speech.py
# Test STT + TTS
```

### Phase 3: Reasoning (Week 5-6)
```bash
# Install Ollama or configure API keys
# Create monica_reasoning.py
# Integrate with memory
```

### Phase 4: Integration (Week 7)
```bash
# Update monica_ai.py
# Test end-to-end
# Deploy
```

---

## 🎯 Quick Wins

**Day 1: Install Everything**
```bash
python install_enhancements.py
python test_enhancements.py
```

**Day 2: Try Semantic Search**
```python
from mem0 import Memory
memory = Memory.from_config(config)
memory.add([{"role": "user", "content": "I love blue lights"}], user_id="test")
results = memory.search("What colors does user like?", user_id="test")
print(results)  # Shows "I love blue lights"
```

**Day 3: Try Speech**
```python
from gtts import gTTS
tts = gTTS("Hello! I'm Monica.", lang='en')
tts.save("greeting.mp3")
# Play greeting.mp3
```

**Day 4: Try Reasoning (if Ollama installed)**
```python
import ollama
response = ollama.chat(
    model='llama3.2',
    messages=[{'role': 'user', 'content': 'What makes a good AI companion?'}]
)
print(response['message']['content'])
```

---

## 📞 Support

- **Documentation**: See MONICA_ENHANCEMENT_PLAN.md
- **Architecture**: See ARCHITECTURE_DIAGRAM.md
- **Examples**: See ENHANCEMENT_SUMMARY.md
- **Issues**: Check test_enhancements.py output

---

## ✅ Checklist

- [ ] Read ENHANCEMENT_SUMMARY.md
- [ ] Run `python install_enhancements.py`
- [ ] Install Ollama (optional, for reasoning)
- [ ] Run `python test_enhancements.py`
- [ ] Configure .env (if using API keys)
- [ ] Review MONICA_ENHANCEMENT_PLAN.md
- [ ] Start Phase 1: Memory System
- [ ] Test semantic search
- [ ] Continue to Phase 2: Speech
- [ ] Test STT + TTS
- [ ] Continue to Phase 3: Reasoning
- [ ] Test decision-making
- [ ] Phase 4: Full integration

---

## 🎉 End Result

Monica will be able to:

✅ **Remember**: "You prefer dim lighting when tired"  
✅ **Understand**: "What activities make you happy?" → finds patterns  
✅ **Listen**: Real-time speech transcription  
✅ **Speak**: Natural voice with emotion control  
✅ **Reason**: "Based on past experience, I should..."  
✅ **Learn**: Improves strategies over time  
✅ **Adapt**: Personalizes to each user  
✅ **Explain**: Shows reasoning process transparently  

**All while maintaining existing features (fog effects, face tracking, advanced modules)!**

---

## 🚀 Ready?

```bash
python install_enhancements.py
```

**Good luck! You're about to build something amazing! 🌟**
