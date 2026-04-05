# Monica Quick Start Guide

## How to Talk to Monica

1. **Start Monica**: Run `.\.venv\Scripts\python.exe monica_interface.py`
2. **Press Enter** when prompted
3. **Look for the window**: "Monica Interface (Flame Spark + You)"
4. **See Monica**: She appears as a bright orange/yellow flame spark on a black background
5. **Talk to Monica**: Press SPACEBAR, then speak clearly into your microphone
6. **Wait**: You'll see "🎤 LISTENING..." on screen while she listens
7. **She responds**: Monica's flame will pulse when she speaks back

## Controls

- **SPACE**: Activate voice input (hold and speak)
- **Q**: Quit Monica
- **V**: Toggle whether Monica can see you
- **D**: Toggle object detection

## Troubleshooting

### Can't see Monica?
- Look for a bright flame spark on black background
- The window title is "Monica Interface (Flame Spark + You)"
- Make sure the window isn't minimized

### Monica can't hear you?
- Check your microphone is plugged in
- Grant microphone permissions to Python
- Make sure you have internet (uses Google Speech Recognition)
- Speak clearly and loudly after pressing SPACE
- Wait for "🎤 LISTENING..." to appear

### No response?
- Monica needs internet for speech recognition
- Say "Monica" to get her attention first
- Try: "Monica, hello" or "Monica, help me"

## SMS Feature

SMS is available but not demonstrated automatically (free API allows 1 message/day).
To send SMS: `monica.communication.send_sms("Your message here")`

## What to Say

- "Monica, hello" - Get her attention
- "Monica, help me" - General assistance
- "Write a report" - Create a document
- "What do you see?" - Object detection
- "Start therapy" - Begin EMDR session
