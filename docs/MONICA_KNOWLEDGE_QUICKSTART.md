# Monica AI - Quick Reference Card (Free Version)

## 🎯 What Monica Can Do Now

✅ **Tell jokes** (ghetto, witty, sarcastic, observational)  
✅ **Speak with accents** (Brooklyn, Southern, Italian, Chicago, 13+ more)  
✅ **Translate all languages** (99+ languages, written & verbal)  
✅ **Teach anything** (Physics to Psychology to Programming)  
✅ **Learn from files** (PDFs, audio, video, text)  
✅ **Remember people** (faces, preferences, conversation history)  
✅ **Provide therapy** (CBT, EMDR, trauma-informed care)  
✅ **Expert discussions** (All sciences, math, humanities, coding)  

---

## 💻 Installation (5 Minutes)

```bash
# 1. Install Ollama (Free Local LLM)
# Download: https://ollama.com/download
ollama pull llama3.2

# 2. Install Python packages
python install_enhancements.py

# 3. Test Monica
python demo_monica_knowledge.py
```

---

## 🎭 Quick Examples

### Tell a Joke
```python
from monica_knowledge_system import MonicaExpert, MonicaKnowledgeBase

knowledge = MonicaKnowledgeBase()
monica = MonicaExpert(knowledge)

monica.set_humor_style("ghetto")
joke = monica.tell_joke("physics")
print(joke)
```

### Change Accent
```python
monica.set_accent("brooklyn")  # Now speaks with Brooklyn accent
monica.set_accent("southern")  # Y'all ready for this?
monica.set_accent("italian_american")  # Fuhget about it!
```

### Translate Languages
```python
result = monica.translate(
    "Hello, how are you?",
    "english",
    "spanish"
)
print(result["translation"])  # "Hola, ¿cómo estás?"
```

### Teach Something
```python
lesson = monica.teach(
    subject="quantum physics",
    level="beginner",
    person_id="user1"  # Personalizes to user
)
print(lesson)
```

### Learn from Files
```python
# PDF
knowledge.learn_from_pdf("quantum_physics_textbook.pdf")

# Audio (any language!)
knowledge.learn_from_audio("lecture.mp3")

# Video
knowledge.learn_from_video("tutorial.mp4")

# Text
with open("ebook.txt") as f:
    knowledge.learn_from_text(f.read(), "Philosophy Book", "philosophy")
```

### Remember People
```python
# Store info
knowledge.remember_person("john", {
    "name": "John",
    "preferences": {"accent": "southern", "humor_style": "witty"},
    "topics": ["quantum physics", "programming"]
})

# Recall info
person = knowledge.recall_person("john")
print(f"I remember {person['name']}!")
```

### Get Therapy Support
```python
response = monica.get_trauma_informed_response(
    user_state="anxious, triggered",
    context="Flashback from past trauma"
)
print(response)  # Compassionate, professional support
```

---

## 📚 Monica's Expertise

### Sciences
- **Physics**: Classical, Quantum, Cosmology, Astrophysics
- **Mathematics**: Algebra, Calculus, Geometry, Statistics (all levels)
- **Computer Science**: Algorithms, AI, ML, Programming
- **Quantum Physics**: Entanglement, superposition, quantum mechanics
- **Cosmology**: Universe, black holes, dark matter

### Psychology & Therapy
- **CBT** (Cognitive Behavioral Therapy)
- **EMDR** (Eye Movement Desensitization)
- **Gestalt**, **Realism**, **Solution-Focused**
- **Psychoanalysis** (all schools)
- **Trauma-Informed Care**
- **NCMHCE** knowledge

### Programming (All Languages)
Python, JavaScript, Java, C, C++, Rust, Go, SQL, HTML, CSS, React, Node.js, TensorFlow, PyTorch

### Life Skills
Driving, GPS, Communication, Presentation, Assertiveness, Journaling, Critical Thinking, Abstract Thinking

### Humanities
Philosophy, World Religions, World Cultures, Spirituality, Human Sexuality, Reading, Writing

---

## 🗣️ Available Accents

1. New York - "caw-fee" (coffee)
2. Brooklyn - "hee-ya" (here)
3. Italian American - "fuhget about it"
4. Chicago - "da bears"
5. Southern - "y'all"
6. Western - "howdy pardner"
7. Latin - Spanish-influenced English
8. British, Australian, Irish, Scottish, Indian, African (13+ total)

---

## 😂 Humor Styles

- **ghetto**: Street humor, urban comedy
- **witty**: Quick, clever wordplay
- **sarcastic**: Dry, ironic humor
- **observational**: Daily life comedy
- **puns**: Wordplay jokes

---

## 🌍 Languages (99+)

English, Spanish, French, German, Italian, Portuguese, Russian, Chinese, Japanese, Korean, Arabic, Hindi, Dutch, Swedish, Polish, Turkish, Vietnamese, Thai, and 80+ more!

---

## 🧠 Trauma Knowledge

### Brain Effects
- Amygdala hijack
- Hippocampus damage
- Prefrontal cortex regulation

### Techniques
- Grounding (5-4-3-2-1)
- Breathing exercises
- DBT skills
- Mindfulness
- Safe communication

---

## 💰 Cost

**100% FREE** using:
- Ollama (local LLM)
- Whisper (speech recognition)
- Piper/gTTS (text-to-speech)
- Mem0 + Qdrant (memory)

**No API keys required!**

---

## 🎓 Teaching Levels

- **elementary**: Basic introduction
- **beginner**: Getting started
- **intermediate**: Building on basics
- **advanced**: Deep expertise
- **expert**: Professional-level

---

## 📖 File Types Monica Learns From

- **PDF**: Textbooks, papers, documents
- **Audio**: MP3, WAV, M4A (lectures, podcasts)
- **Video**: MP4, AVI, MKV (tutorials)
- **Text**: TXT, EPUB, DOCX (ebooks, articles)

---

## 🚀 Quick Start

```python
# Import
from monica_knowledge_system import MonicaExpert, MonicaKnowledgeBase

# Initialize
knowledge = MonicaKnowledgeBase()
monica = MonicaExpert(knowledge)

# Set personality
monica.set_accent("brooklyn")
monica.set_humor_style("ghetto")

# Use Monica
joke = monica.tell_joke("physics")
lesson = monica.teach("quantum physics", "beginner")
translation = monica.translate("Hello", "english", "spanish")

# Learn
knowledge.learn_from_pdf("textbook.pdf")
knowledge.learn_from_audio("lecture.mp3")

# Remember
knowledge.remember_person("user1", {"name": "John", "topics": ["physics"]})
```

---

## 📋 Complete Integration Example

```python
from monica_knowledge_system import MonicaExpert, MonicaKnowledgeBase

# Setup Monica
knowledge = MonicaKnowledgeBase()
monica = MonicaExpert(knowledge)

# Meet new person
knowledge.remember_person("sarah", {
    "name": "Sarah",
    "preferences": {"accent": "brooklyn", "humor_style": "ghetto"},
    "note": "Wants to learn computer science for CS degree"
})

# Set personality for Sarah
monica.set_accent("brooklyn")
monica.set_humor_style("ghetto")

# Tell joke
joke = monica.tell_joke("programming")
print(f"Monica: {joke}")

# Teach
lesson = monica.teach("algorithms", "beginner", person_id="sarah")
print(f"\nLesson:\n{lesson}")

# Discuss topic
response = monica.discuss(
    "computer science",
    "How do hash tables work?",
    person_id="sarah"
)
print(f"\nMonica explains:\n{response}")

# Learn from file (for Sarah's studies)
result = knowledge.learn_from_pdf("data_structures_textbook.pdf")
print(f"\nLearned: {result}")

# Translate for Sarah
translation = monica.translate(
    "¿Cómo funcionan las tablas hash?",
    "spanish",
    "english"
)
print(f"\nTranslated: {translation['translation']}")

# Remember this session
person = knowledge.recall_person("sarah")
print(f"\nSarah's progress:")
print(f"  Interactions: {person['interactions']}")
print(f"  Topics: {', '.join(person['conversation_topics'])}")
```

---

## 🛠️ Dependencies

### Required
```bash
pip install mem0ai qdrant-client sentence-transformers  # Memory
pip install openai-whisper  # Speech recognition
pip install PyPDF2 python-docx ebooklib beautifulsoup4  # File learning
```

### Optional
```bash
pip install moviepy  # Video processing
# ffmpeg for video: https://ffmpeg.org/download.html
```

---

## 📚 Documentation

- **KNOWLEDGE_SYSTEM_GUIDE.md** - Complete guide with all examples
- **MONICA_ENHANCEMENT_PLAN.md** - Overall enhancement plan
- **demo_monica_knowledge.py** - Interactive demo

---

## 💡 Pro Tips

1. **Feed Monica knowledge early**: More files = smarter responses
2. **Use consistent person IDs**: Track users across sessions
3. **Combine accents + humor**: Create unique personalities
4. **Start teaching at beginner**: Progress as user learns
5. **Provide context**: Use person_id for personalized responses
6. **Learn from diverse sources**: PDFs, audio, video all add value

---

## 🎉 What This Gives You

A **state-of-the-art AI companion** that:

✅ Makes you laugh (any style)  
✅ Speaks your language (99+ languages)  
✅ Teaches you anything (CS degree? Check!)  
✅ Remembers you forever  
✅ Provides trauma-informed support  
✅ Gets smarter every day (learns from files)  
✅ Has personality (accents + humor)  

**All for FREE!** 🌟

---

## 🚀 Ready?

```bash
# 1. Install Ollama
# Download: https://ollama.com/download
ollama pull llama3.2

# 2. Run demo
python demo_monica_knowledge.py

# 3. Start building!
```

**Monica is ready to be the most knowledgeable, funny, multilingual, trauma-informed AI ever created!** 🎊
