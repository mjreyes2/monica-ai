## Monica AI - Intelligence & Learning System Guide

### 🧠 What Makes Monica Intelligent

Monica now has **advanced AI reasoning capabilities** powered by Ollama (local LLM). She can:

1. **Understand Complex Requests** - Parse what you're asking for
2. **Check Her Knowledge** - See if she already knows how to do it
3. **Research When Needed** - Search the web for information
4. **Think Critically** - Apply reasoning to solve problems
5. **Generate Code** - Write Python code to implement solutions
6. **Learn & Remember** - Store knowledge for future use

---

## Your Example: Transparent Background

**You said:**
> "Monica, make my background transparent"

**Monica's Process:**

```
Step 1: Understand Request
  ↓ "User wants transparency, I only know: green, black, blue, red"

Step 2: Check Knowledge
  ↓ "I don't know about transparency yet"

Step 3: Research
  ↓ Searches web for "transparent background Python OpenCV"
  ↓ Finds: RGBA color space, alpha channel, cv2.IMREAD_UNCHANGED

Step 4: Synthesize Solution
  ↓ "I need to use RGBA (4 channels) instead of RGB (3 channels)"
  ↓ "Alpha channel controls transparency: 0=transparent, 255=opaque"

Step 5: Generate Code
  ↓ Creates function to make background transparent

Step 6: Store Learning
  ↓ Saves to knowledge base

Next Time: Monica remembers! No research needed.
```

---

## Setup Instructions

### 1. Install Ollama

**Windows:**
```bash
# Download from https://ollama.com
# Run installer
# After installation, open PowerShell or CMD
```

**Pull the Model:**
```bash
ollama pull llama3.2
```

**Verify:**
```bash
ollama list
# Should show: llama3.2
```

### 2. Install Python Dependencies

```bash
# Required
pip install ollama requests opencv-python numpy

# Optional (for web research)
pip install duckduckgo-search beautifulsoup4
```

### 3. Test Monica's Intelligence

```bash
python test_monica_intelligence.py
```

This will test:
- ✅ Ollama connection
- ✅ Dependencies
- ✅ Basic reasoning
- ✅ Learning new concepts (your transparent background example!)
- ✅ Code generation
- ✅ Memory persistence

---

## How to Use Monica's Intelligence

### Method 1: Direct Intelligence API

```python
from monica_intelligence import MonicaIntelligence

# Create Monica's brain
monica = MonicaIntelligence()

# Ask her to do something she doesn't know
result = monica.think(
    "Make my background transparent",
    context={
        "current_capabilities": ["green", "black", "blue", "red"],
        "programming_language": "python",
        "framework": "opencv"
    }
)

# Check result
if result['success']:
    print("Monica figured it out!")

    # She may have generated code
    if result['code_generated']:
        code = result['code_generated']['code']
        print("Generated code:", code)

        # Execute it
        exec_result = monica.execute_generated_code(code)
        print("Execution result:", exec_result)
```

### Method 2: Natural Language (Coming in Integration)

```python
# Future integration with voice/chat
monica.process_command("Monica, make my background transparent")
# Monica automatically:
# - Thinks about it
# - Researches if needed
# - Generates code
# - Applies it
# - Tells you what she did
```

---

## Critical Thinking Framework

Monica uses an 8-step reasoning process:

### 1. **Understand Request**
- Parse user intent
- Extract key concepts
- Identify technical requirements
- Estimate difficulty

**Example:**
```json
{
  "intent": "make background transparent",
  "concepts": ["transparency", "alpha channel", "RGBA"],
  "technical_requirements": ["opencv", "image processing"],
  "difficulty": "medium"
}
```

### 2. **Check Existing Knowledge**
- Search learned concepts database
- Check code cache
- See if similar problem was solved before

**Example:**
```json
{
  "known": false,
  "similar_concepts": []
}
```

### 3. **Identify Gaps**
- What Monica doesn't know
- What needs to be researched
- What skills are required

### 4. **Research**
- Web search for information
- Find code examples
- Learn best practices

**Sources:**
- DuckDuckGo search
- Technical documentation
- Code repositories
- Tutorials

### 5. **Synthesize Solution**
- Combine research findings
- Propose approach
- Identify steps needed
- Determine if code generation is needed

**Example:**
```json
{
  "feasible": true,
  "approach": "Use OpenCV with RGBA color space and alpha channel",
  "steps": [
    "Create RGBA image with 4 channels",
    "Set alpha channel to 0 for transparency",
    "Use cv2.IMREAD_UNCHANGED when loading"
  ],
  "needs_code": true,
  "libraries_needed": ["opencv-python", "numpy"]
}
```

### 6. **Generate Code**
- Write Python code to implement solution
- Include error handling
- Add documentation
- Create usage example

**Example:**
```python
def make_background_transparent(image, background_color=(0, 255, 0)):
    """
    Make specific color transparent in image.

    Args:
        image: Input image (BGR format)
        background_color: Color to make transparent (B, G, R)

    Returns:
        Image with transparency (RGBA format)
    """
    # Create alpha channel
    rgba = cv2.cvtColor(image, cv2.COLOR_BGR2BGRA)

    # Make background color transparent
    mask = np.all(rgba[:, :, :3] == background_color, axis=2)
    rgba[mask, 3] = 0  # Set alpha to 0 (transparent)

    return rgba
```

### 7. **Test & Validate**
- Execute code safely
- Check for errors
- Validate output

### 8. **Store Learning**
- Save concept to knowledge base
- Cache generated code
- Remember for next time

---

## Real-World Examples

### Example 1: Your Use Case

**Request:** "Monica, make my background transparent"

**Monica's Response:**
```
🤔 I don't know how to do that yet. Let me research...

🔍 Researching: transparency, alpha channel, RGBA
📚 Found 5 sources about image transparency in Python
💡 Learning: RGBA has 4 channels, alpha controls transparency

✍️ Generating code...

✅ Done! I created a function to make backgrounds transparent.

💾 I'll remember this for next time!
```

**Generated Code:**
```python
import cv2
import numpy as np

def make_transparent_background(image, bg_color=(0, 255, 0)):
    """Make background color transparent."""
    rgba = cv2.cvtColor(image, cv2.COLOR_BGR2BGRA)
    mask = np.all(rgba[:, :, :3] == bg_color, axis=2)
    rgba[mask, 3] = 0
    return rgba

# Usage
image = cv2.imread('photo.jpg')
transparent = make_transparent_background(image, bg_color=(0, 255, 0))
cv2.imwrite('photo_transparent.png', transparent)
```

### Example 2: Learning Face Detection

**Request:** "Detect faces in my webcam"

**Monica's Process:**
1. Researches face detection
2. Finds Haar Cascades and MediaPipe
3. Generates code using cv2.CascadeClassifier
4. Stores learning about face detection

### Example 3: Creating Custom Filters

**Request:** "Add a vintage sepia filter to my video"

**Monica's Process:**
1. Researches sepia tone algorithms
2. Learns color matrix transformations
3. Generates sepia filter function
4. Integrates with video stream

---

## Knowledge Storage

Monica stores learned knowledge in JSON files:

### Learned Concepts: `data/monica_learned_knowledge.json`

```json
{
  "make background transparent": {
    "learned_at": "2025-12-02T...",
    "understanding": {
      "intent": "create transparency in images",
      "concepts": ["alpha channel", "RGBA", "opencv"],
      "difficulty": "medium"
    },
    "research_summary": {
      "sources_count": 5,
      "key_findings": [
        "RGBA has 4 channels: R, G, B, Alpha",
        "Alpha = 0 is fully transparent",
        "Use cv2.IMREAD_UNCHANGED to preserve alpha"
      ]
    },
    "solution": {
      "feasible": true,
      "approach": "Use RGBA color space with alpha channel",
      "needs_code": true
    }
  }
}
```

### Generated Code: `data/monica_generated_code.json`

```json
{
  "make_transparent_background": {
    "generated_at": "2025-12-02T...",
    "code": "def make_transparent_background(image, bg_color=(0, 255, 0)):\n    ...",
    "usage_example": "transparent = make_transparent_background(img)",
    "tested": true,
    "works": true
  }
}
```

---

## Advanced Usage

### Custom Research Context

```python
monica = MonicaIntelligence()

result = monica.think(
    "Add motion blur to moving objects",
    context={
        "current_capabilities": ["basic filters", "color adjustment"],
        "available_libraries": ["opencv", "numpy", "scipy"],
        "performance_requirement": "real-time 30fps",
        "hardware": "GPU available"
    }
)
```

### Code Execution Control

```python
# Safe mode (default) - blocks dangerous operations
exec_result = monica.execute_generated_code(code, safe_mode=True)

# Unsafe mode - use carefully
exec_result = monica.execute_generated_code(code, safe_mode=False)

# Check result
if exec_result['success']:
    print("Code ran successfully!")
    print("Namespace:", exec_result['namespace'])
else:
    print("Error:", exec_result['error'])
```

### Manual Learning

```python
# Teach Monica something directly
monica.learned_concepts["custom_concept"] = {
    "learned_at": datetime.now().isoformat(),
    "understanding": {...},
    "solution": {...}
}
monica._save_knowledge()
```

---

## Integration with Monica's Systems

### With Voice System

```python
from monica_intelligence import MonicaIntelligence
from monica_voice_complete import VoiceSystem

intelligence = MonicaIntelligence()
voice = VoiceSystem()

# User speaks
user_input = voice.listen()

# Monica thinks about it
result = intelligence.think(user_input)

# Monica responds
if result['success']:
    response = "I figured it out! " + result['solution']['approach']
else:
    response = "I'm still learning about that. Let me research more."

voice.speak(response)
```

### With Avatar System

```python
from monica_intelligence import MonicaIntelligence
from monica_avatar_integration import MonicaAvatarController

intelligence = MonicaIntelligence()
avatar = MonicaAvatarController()

# While thinking, show thinking expression
avatar.set_expression('thinking')

result = intelligence.think("complex request")

# After figuring it out, show happy expression
if result['success']:
    avatar.set_expression('smile')
    avatar.perform_gesture('explain')
```

---

## Troubleshooting

### Ollama Not Connecting

**Problem:** `Ollama not available` error

**Solution:**
```bash
# Check if Ollama is running
# Open a new terminal
ollama serve

# In another terminal, test
ollama run llama3.2 "Hello"
```

### Model Not Found

**Problem:** `llama3.2 model not found`

**Solution:**
```bash
ollama pull llama3.2
```

### Slow Response Times

**Problem:** Monica takes too long to think

**Solutions:**
1. Use smaller model: `ollama pull llama3.2:1b`
2. Reduce research depth
3. Use GPU acceleration
4. Cache more aggressively

### Import Errors

**Problem:** `ModuleNotFoundError: No module named 'duckduckgo_search'`

**Solution:**
```bash
pip install duckduckgo-search
```

This is optional - Monica will still work without web search, just with reduced research capability.

---

## Performance Tips

### 1. First Request Is Slow
- Monica needs to research and learn
- Subsequent requests are fast (she remembers!)

### 2. Optimize Model Choice
```bash
# Faster, less accurate
ollama pull llama3.2:1b

# Balanced (recommended)
ollama pull llama3.2

# Slower, more accurate
ollama pull llama3.2:70b
```

### 3. Pre-load Common Knowledge
Teach Monica common tasks in advance so she doesn't need to research every time.

---

## Security Considerations

### Safe Mode (Default)
- Blocks: file system operations, subprocess calls, imports
- Allows: safe calculations, data transformations
- Best for: automated execution

### Unsafe Mode
- Allows: everything
- Use only: when you review code first
- Never: run untrusted code

### Code Review
Always review generated code before executing in production:
```python
result = monica.think("request")
if result['code_generated']:
    print("Review this code:")
    print(result['code_generated']['code'])

    # Manual approval
    if input("Execute? (yes/no): ") == "yes":
        monica.execute_generated_code(result['code_generated']['code'])
```

---

## What's Next

Monica's intelligence system is **production-ready** for:
- ✅ Learning new concepts
- ✅ Generating code solutions
- ✅ Remembering what she learns
- ✅ Critical thinking and problem-solving

**To use it:**
1. Make sure Ollama is running
2. Run the test: `python test_monica_intelligence.py`
3. Try your transparent background example!

**Future enhancements:**
- Voice command integration
- Visual feedback during thinking
- Multi-step complex tasks
- Collaborative problem-solving

---

**Ready to see Monica learn?**

```bash
python test_monica_intelligence.py
```

Watch her research, learn, and solve the transparent background problem! 🚀
