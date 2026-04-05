# Monica AI - Quick Reference Card

## 🚀 Quick Start

```powershell
# Test everything
python test_monica_complete.py

# Run complete system
python monica_ai_complete.py
```

## 📞 Your SMS Number
**813-426-6783** (receives alerts, FREE with Textbelt)

---

## 💬 Ask Monica

### Legal Questions
```python
monica.ask_monica("user_id", "What is Florida's homestead exemption?")
monica.ask_monica("user_id", "What are federal bankruptcy laws?")
```

### Science Questions
```python
monica.ask_monica("user_id", "How do neurons communicate?")
monica.ask_monica("user_id", "What causes schizophrenia?")
monica.ask_monica("user_id", "Explain organic chemistry")
```

### Education Questions
```python
monica.ask_monica("user_id", "What are the best CS universities?")
monica.ask_monica("user_id", "MIT admission requirements?")
```

---

## 🌐 Internet Search

```python
# Search and display hologram
results = monica.search_internet("user_id", "Python programming", display_hologram=True)

# Results structure
{
    "results": [{"title": "...", "url": "...", "snippet": "..."}],
    "hologram": {"position": {"x": 0, "y": 0, "z": -2.0}, "scale": 1.0}
}
```

---

## ✨ Hologram Control (Hand Gestures)

| Gesture | Action |
|---------|--------|
| Pinch & drag | Move hologram |
| Two-hand spread | Scale larger |
| Two-hand pinch | Scale smaller |
| Swipe left/right | Move to side |
| Push away | Move back |
| Pull toward | Move closer |
| Palm up | Show hologram |
| Palm down | Hide hologram |

```python
# Process gesture
gesture = {"gesture_type": "two_hand_spread", "scale_factor": 1.5}
monica.process_hand_gesture(gesture)
```

---

## 🔒 Security

### Check Authorization
```python
if monica.check_security("user_id", "action"):
    # User authorized
    pass
```

### View Security Status
```python
summary = monica.get_security_summary()
# {
#     "total_accesses": 42,
#     "unauthorized_attempts": 0,
#     "total_alerts_sent": 3,
#     "last_access": "2025-12-02T10:30:00"
# }
```

### Encrypt/Decrypt
```python
encrypted = monica.security.encrypt_data("sensitive")
decrypted = monica.security.decrypt_data(encrypted)
```

---

## 📱 SMS Alerts

### Monica Sends You Message
```python
monica.send_sms_to_owner("Hey! I learned something cool!")
# You receive: "💬 Monica says: Hey! I learned something cool!"
```

### Automatic Alerts
- **Unauthorized access** → SMS to 813-426-6783
- **Someone accesses Monica** → SMS notification
- **System changes** → SMS notification

### Alert Types
```python
# Manual alerts
monica.sms_alerts.alert_unauthorized_access("user_id", "action")
monica.sms_alerts.alert_monica_access("user_id")
monica.sms_alerts.alert_system_change("change description")
```

---

## 📚 Feed Monica Knowledge

```python
# PDF
monica.learn_from_file("user_id", "textbook.pdf")

# Audio
monica.learn_from_file("user_id", "lecture.mp3")

# Video
monica.learn_from_file("user_id", "tutorial.mp4")
```

---

## 🎭 Personality

### Set Accent
```python
monica.set_personality("user_id", accent="brooklyn")
# Options: new_york, brooklyn, italian_american, chicago, southern,
#          western, latin, british, australian, irish, scottish, 
#          indian, african
```

### Set Humor Style
```python
monica.set_personality("user_id", humor_style="ghetto")
# Options: ghetto, witty, sarcastic, dry, observational
```

### Get Joke
```python
joke = monica.get_joke("user_id", topic="physics")
```

### Translate
```python
result = monica.translate("user_id", "Hello", "english", "spanish")
# {"translation": "Hola", "source_lang": "english", "target_lang": "spanish"}
```

### Teach
```python
lesson = monica.teach_me("user_id", "algorithms", level="beginner")
# Levels: beginner, intermediate, advanced
```

---

## 📊 Knowledge Domains

### Legal (50+ jurisdictions)
- All 50 US states
- Federal law
- Criminal, Civil, Family, Business, Estate, Regulatory

### Sciences (5 domains)
- Biology
- Chemistry  
- Neurobiology
- Bacteriology
- Schizophrenia

### Other (14+ domains)
- Education (colleges/universities)
- Psychology & Therapy
- Computer Science
- Programming
- Mathematics
- Physics
- Philosophy
- World Religions
- Life Skills
- Social Engineering Protection

---

## 🛡️ PII Protection

```python
# Detect PII
detected = monica.maskwise.detect_pii("SSN is 123-45-6789")
# [{"type": "ssn", "value": "123-45-6789", "start": 7, "end": 18}]

# Anonymize
text = "My SSN is 123-45-6789"
anonymized = monica.maskwise.anonymize_text(text)
# "My SSN is [SSN-REDACTED]"
```

---

## 📁 Key Files

| File | Purpose |
|------|---------|
| `monica_ai_complete.py` | Complete integration |
| `monica_legal_sciences.py` | Legal & sciences |
| `monica_internet_hologram.py` | Search & hologram |
| `monica_security_sms.py` | Security & SMS |
| `test_monica_complete.py` | Test all modules |
| `MONICA_COMPLETE_GUIDE.md` | Full documentation |
| `MONICA_COMPLETE_SUMMARY.md` | Implementation summary |

---

## 💰 Cost

**$0.00** - Everything is FREE!

- ✅ Ollama (local LLM)
- ✅ DuckDuckGo search
- ✅ Textbelt SMS (1/day)
- ✅ MaskWise PII protection
- ✅ All Python packages

---

## 🔐 Security Features

✅ **Encryption** - Fernet (AES-128)  
✅ **Access Logging** - Every interaction logged  
✅ **Rate Limiting** - 100 requests/hour  
✅ **Intrusion Detection** - Pattern analysis  
✅ **PII Protection** - Auto-redaction  
✅ **SMS Alerts** - Real-time notifications  
✅ **Session Tokens** - 24-hour expiration  

---

## 📱 SMS Setup

### Default (FREE)
- **Service**: Textbelt
- **Limit**: 1 SMS/day
- **Cost**: $0.00
- **Status**: ✅ Ready

### Upgrade (Optional)
1. Sign up at [twilio.com](https://www.twilio.com/try-twilio)
2. Get 50 free SMS
3. Update credentials in `monica_security_sms.py`
4. Enable: `monica.sms_alerts.use_twilio = True`

---

## 🎯 Quick Examples

### Example 1: Complete Session
```python
from monica_ai_complete import MonicaAIComplete

monica = MonicaAIComplete()
user = "user_123"

# Set personality
monica.set_personality(user, accent="brooklyn", humor_style="ghetto")

# Ask question
answer = monica.ask_monica(user, "What is quantum entanglement?")

# Search internet
results = monica.search_internet(user, "quantum physics books", True)

# Get joke
joke = monica.get_joke(user, "physics")

# Monica texts you
monica.send_sms_to_owner("Just learned about quantum physics!")

# Check security
summary = monica.get_security_summary()
```

### Example 2: Learn & Teach
```python
# Feed knowledge
monica.learn_from_file(user, "quantum_physics.pdf")
monica.learn_from_file(user, "lecture.mp3")

# Teach you
lesson = monica.teach_me(user, "quantum_mechanics", "beginner")
```

### Example 3: Hologram Control
```python
# Display search results as hologram
results = monica.search_internet(user, "universities", True)

# Scale larger with hands
monica.process_hand_gesture({"gesture_type": "two_hand_spread", "scale_factor": 1.5})

# Move to the right
monica.process_hand_gesture({"gesture_type": "swipe_right"})

# Hide
monica.hologram.hide_hologram()
```

---

## 📖 Documentation

- **Complete Guide**: `MONICA_COMPLETE_GUIDE.md`
- **Summary**: `MONICA_COMPLETE_SUMMARY.md`
- **Knowledge System**: `KNOWLEDGE_SYSTEM_GUIDE.md`
- **Integration**: `integration_example.py`

---

## ✅ Status

All systems: **READY** ✅

- ✅ Legal knowledge
- ✅ Sciences knowledge
- ✅ Education knowledge
- ✅ Social engineering protection
- ✅ Internet search
- ✅ Hologram display
- ✅ Security (encryption, logging)
- ✅ SMS alerts (813-426-6783)
- ✅ PII protection
- ✅ Complete integration

**Test passed**: `python test_monica_complete.py` ✅

---

**Monica AI is now complete and ready to use!** 🎉
