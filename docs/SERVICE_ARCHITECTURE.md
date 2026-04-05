# Monica AI - Multi-Process Service Architecture

## Overview

Monica AI now uses a **multi-process service architecture** for maximum stability and fault tolerance. Each major subsystem runs in its own isolated process, communicating via IPC (Inter-Process Communication).

## Benefits

✅ **Crash Isolation**: If one service crashes, others keep running
✅ **Auto-Restart**: Failed services automatically restart
✅ **Health Monitoring**: Continuous service health checks with heartbeats
✅ **GPU Scheduling**: Explicit control over which services use GPU/VRAM
✅ **Easier Debugging**: Isolate problems to specific services
✅ **Resource Management**: Services can be stopped/started independently

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  GUI/Orchestrator                        │
│              (Main Process - Tkinter)                    │
│                                                          │
│  • Coordinates all services                             │
│  • Routes messages via IPC                              │
│  • Health monitoring & auto-restart                     │
│  • User interface                                       │
└─────────────────────────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ STT Service │    │ TTS Service │    │Vision Service│
│  (Process)  │    │  (Process)  │    │  (Process)   │
├─────────────┤    ├─────────────┤    ├─────────────┤
│ • Mic       │    │ • Synthesis │    │ • Camera    │
│   capture   │    │ • Playback  │    │ • OCR       │
│ • SpeechBrain│   │ • MonicaTTS │    │ • Detection │
│ • Wake word │    │ • Queue     │    │ • Biometrics│
└─────────────┘    └─────────────┘    └─────────────┘
        │                  │                  │
        └──────────────────┼──────────────────┘
                           │
                           ▼
                   ┌─────────────┐
                   │ AI Service  │
                   │  (Process)  │
                   ├─────────────┤
                   │ • LLM calls │
                   │ • RAG       │
                   │ • Knowledge │
                   │ • Web tools │
                   └─────────────┘
```

## Services

### 1. STT Service (Speech-to-Text)
**Process**: `stt`
**Responsibilities**:
- Microphone capture
- Speech recognition (SpeechBrain)
- Wake word detection
- Audio level monitoring

**Crash Impact**: Voice input stops, but vision, TTS, and AI continue working

### 2. TTS Service (Text-to-Speech)
**Process**: `tts`
**Responsibilities**:
- Speech synthesis (MonicaTTS)
- Audio playback
- Speech queue management
- Echo cancellation coordination

**Crash Impact**: Voice output stops, but STT, vision, and AI continue working

### 3. Vision Service
**Process**: `vision`
**Responsibilities**:
- Camera capture
- OCR (text recognition)
- Object detection
- Biometric detection (face, emotion, identity)

**Crash Impact**: Visual features stop, but STT, TTS, and AI continue working

### 4. AI Service
**Process**: `ai`
**Responsibilities**:
- LLM inference
- Conversation management
- RAG (Retrieval-Augmented Generation)
- Knowledge retrieval
- Web search/tools

**Crash Impact**: AI responses stop, but STT, TTS, and vision continue working

### 5. GUI/Orchestrator Service
**Process**: Main (GUI runs here)
**Responsibilities**:
- User interface (Tkinter)
- Service coordination
- Message routing
- Health monitoring
- Auto-restart logic

**Crash Impact**: Entire application stops (this is the main process)

## IPC Communication

Services communicate via **multiprocessing.Queue** for simplicity and reliability.

### Message Format

```python
ServiceMessage(
    type='request',        # 'request', 'response', 'event', 'heartbeat', 'error'
    source='stt',          # Service that sent message
    destination='ai',      # Target service or 'orchestrator' or 'broadcast'
    payload={'key': 'value'},  # Actual data
    request_id='uuid',     # Optional for request-response pattern
    timestamp=1234567890.0
)
```

### Message Types

- **request**: Request-response pattern (expects reply)
- **response**: Reply to a request
- **event**: One-way notification
- **heartbeat**: Service health check (automatic)
- **error**: Error notification

### Example: Speech Recognition Flow

```
STT Service → Orchestrator → AI Service → Orchestrator → TTS Service
   │                                                          │
   └─ Transcribes speech                                     └─ Speaks response
```

1. **STT** captures audio, transcribes: "What's the weather?"
2. **STT** sends event to **Orchestrator**: `{event: 'transcription', text: '...'}`
3. **Orchestrator** routes to **AI**: `{action: 'chat', message: '...'}`
4. **AI** processes and sends response: `{event: 'ai_response', response: '...'}`
5. **Orchestrator** routes to **TTS**: `{action: 'speak', text: '...'}`
6. **TTS** synthesizes and plays audio

## Fault Tolerance

### Health Monitoring

Each service sends a **heartbeat** every 5 seconds. The orchestrator monitors:
- Process alive/dead status
- Heartbeat timeout (15 seconds)
- Crash notifications

### Auto-Restart

When a service crashes:
1. Orchestrator detects crash
2. Logs error with traceback
3. Attempts restart (max 5 times in 60 seconds)
4. Other services continue running normally

### Restart Limits

To prevent infinite restart loops:
- Max 5 restarts per 60-second window
- After limit reached, service stays stopped
- Manual restart still possible

## Usage

### Start Monica with Service Architecture

```bash
python monica_services_launcher.py
```

### Test Resilience

```bash
python test_service_resilience.py
```

This runs automated tests that intentionally crash services to verify auto-restart works.

### Monitor Service Status

The GUI shows real-time service status:
- 🟢 **RUNNING**: Service healthy
- 🔴 **STOPPED**: Service not running
- 🟡 **ERROR**: Service has issues
- 🟠 **CRASHED**: Service crashed (will auto-restart)

## API Reference

### Orchestrator

```python
from monica_services.orchestrator import ServiceOrchestrator

# Create orchestrator
orchestrator = ServiceOrchestrator(config)

# Register services
orchestrator.register_service(STTService, 'stt', config)
orchestrator.register_service(TTSService, 'tts', config)

# Start all services
orchestrator.start()

# Send message to service
orchestrator.send_message(
    destination='ai',
    message_type='request',
    payload={'action': 'chat', 'message': 'Hello'}
)

# Get service status
status = orchestrator.get_service_status('stt')
all_status = orchestrator.get_all_status()

# Manually restart a service
orchestrator.restart_service('vision')

# Stop all services
orchestrator.stop()
```

### Creating Custom Services

```python
from monica_services.base_service import BaseService

class MyService(BaseService):
    def initialize(self):
        """Called once at startup"""
        self.logger.info("Initializing...")
        # Load models, open connections, etc.

    def process(self):
        """Called repeatedly in main loop - keep fast!"""
        # Do work here
        time.sleep(0.01)

    def cleanup(self):
        """Called once at shutdown"""
        self.logger.info("Cleaning up...")
        # Close connections, save state, etc.

    def handle_request(self, payload):
        """Handle request from another service"""
        action = payload.get('action')
        if action == 'do_something':
            return {'status': 'success', 'result': 42}
        return None

    def handle_event(self, payload):
        """Handle event from another service"""
        event = payload.get('event')
        if event == 'something_happened':
            # React to event
            pass
```

## File Structure

```
monica_project/
├── monica_services/
│   ├── __init__.py
│   ├── base_service.py       # Base service framework
│   ├── orchestrator.py        # Service orchestrator
│   ├── stt_service.py         # STT service
│   ├── tts_service.py         # TTS service
│   ├── vision_service.py      # Vision service
│   ├── ai_service.py          # AI service
│   └── gui_service.py         # GUI coordinator
├── monica_services_launcher.py  # Main launcher
├── test_service_resilience.py   # Resilience tests
└── SERVICE_ARCHITECTURE.md      # This file
```

## Performance Considerations

### GPU Memory

Each service can use GPU independently. Configure which services use GPU:

```python
# In service config
config = {
    'use_gpu': True,       # Enable GPU for this service
    'gpu_device': 0,       # Which GPU to use
    'max_gpu_memory': 2048 # Max GPU memory (MB)
}
```

### Message Queue Sizing

Queues have maximum sizes to prevent memory issues:
- Inbox: 1000 messages
- Outbox: 1000 messages

If a queue fills up, oldest messages are dropped.

### Process Startup

Services start in **staggered** fashion (0.2s delay between each) to avoid resource contention during initialization.

## Troubleshooting

### Service Won't Start

Check logs:
```bash
tail -f monica_services.log
```

Common issues:
- Missing dependencies
- Port already in use
- GPU memory full

### Service Keeps Crashing

1. Check service log for error
2. Verify dependencies installed
3. Check resource usage (RAM, GPU)
4. Reduce restart limit if crash loop

### Messages Not Routing

1. Verify both services are running
2. Check destination name is correct
3. Look for "Inbox full" warnings in logs
4. Verify message handler registered

## Migration from Old Architecture

To migrate existing Monica code:

1. **Keep imports the same** - services import from `monica_ai.src.*`
2. **Services are self-contained** - each has its own process space
3. **Communication via messages** - use `send_to_service()` instead of direct calls
4. **Async by default** - services don't block each other

### Before (Monolithic)

```python
# Direct call - blocks entire app
result = self.ai_manager.get_response(text)
self.tts_manager.speak(result)
```

### After (Service-Based)

```python
# Send message - non-blocking
self.send_to_service('ai', {
    'action': 'chat',
    'message': text
})

# AI service sends result to TTS automatically
# GUI receives event when done
```

## Future Enhancements

- [ ] Add service metrics (CPU, memory, GPU usage)
- [ ] Web dashboard for monitoring
- [ ] Remote service support (run services on different machines)
- [ ] gRPC for faster IPC (optional upgrade from queues)
- [ ] Docker containers for services
- [ ] Kubernetes deployment support

## License

Same as Monica AI main project.
