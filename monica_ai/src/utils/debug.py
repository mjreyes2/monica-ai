"""
Debug utilities for Monica AI.
"""
import sys
import platform
from datetime import datetime
from typing import Dict, Any


def generate_debug_report(app=None) -> str:
    """
    Generate a comprehensive debug report.
    
    Args:
        app: Optional MonicaAI application instance
        
    Returns:
        Debug report as string
    """
    lines = []
    lines.append("=" * 60)
    lines.append("MONICA AI DEBUG REPORT")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 60)
    lines.append("")
    
    # System Information
    lines.append("SYSTEM INFORMATION:")
    lines.append(f"  Platform: {platform.system()} {platform.release()}")
    lines.append(f"  Python: {sys.version}")
    lines.append(f"  Architecture: {platform.machine()}")
    lines.append("")
    
    # Check dependencies
    lines.append("DEPENDENCIES:")
    
    dependencies = [
        ('numpy', 'numpy'),
        ('opencv', 'cv2'),
        ('PIL', 'PIL'),
        ('torch', 'torch'),
        ('whisper', 'whisper'),
        ('pyaudio', 'pyaudio'),
        ('sounddevice', 'sounddevice'),
        ('piper', 'piper'),
        ('ollama', 'ollama'),
        ('SpoutGL', 'SpoutGL'),
    ]
    
    for name, module in dependencies:
        try:
            m = __import__(module)
            version = getattr(m, '__version__', 'installed')
            lines.append(f"  [*] {name}: {version}")
        except ImportError:
            lines.append(f"  [*] {name}: NOT INSTALLED")
    
    lines.append("")
    
    # GPU Information
    lines.append("GPU INFORMATION:")
    try:
        import torch
        if torch.cuda.is_available():
            lines.append(f"  CUDA Available: Yes")
            lines.append(f"  CUDA Version: {torch.version.cuda}")
            lines.append(f"  GPU: {torch.cuda.get_device_name(0)}")
            lines.append(f"  GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
        else:
            lines.append(f"  CUDA Available: No")
    except ImportError:
        lines.append(f"  PyTorch not installed")
    lines.append("")
    
    # Application state
    if app:
        lines.append("APPLICATION STATE:")
        
        # Camera
        if hasattr(app, 'camera') and app.camera:
            lines.append(f"  Camera running: {app.camera.is_running}")
            lines.append(f"  Camera FPS: {app.camera.get_fps():.1f}")
            lines.append(f"  Spout enabled: {app.camera.is_spout_enabled()}")
        
        # Audio
        if hasattr(app, 'audio') and app.audio:
            lines.append(f"  Audio input active: {app.audio.is_input_active}")
            lines.append(f"  Speech recognition: {app.audio.is_listening}")
            lines.append(f"  Wake word active: {app.audio.is_wake_word_active}")
        
        # TTS
        if hasattr(app, 'tts') and app.tts:
            lines.append(f"  TTS initialized: {app.tts.is_initialized}")
            lines.append(f"  TTS engine: {app.tts.engine_type}")
            lines.append(f"  Current voice: {app.tts.current_voice}")
        
        # AI
        if hasattr(app, 'conversation') and app.conversation:
            lines.append(f"  AI backend: {app.conversation.backend}")
            lines.append(f"  AI model: {app.conversation.model}")
        
        lines.append("")
        
        # Configuration
        if hasattr(app, 'config'):
            lines.append("CONFIGURATION:")
            config = app.config
            lines.append(f"  Camera: {config.CAMERA_WIDTH}x{config.CAMERA_HEIGHT} @ {config.TARGET_FPS}fps")
            lines.append(f"  Audio: {config.SAMPLE_RATE}Hz, {config.CHANNELS}ch")
            lines.append(f"  Whisper model: {config.WHISPER_MODEL_SIZE}")
            lines.append(f"  STT language: {config.STT_LANGUAGE}")
            lines.append(f"  Wake word: {config.WAKE_WORD}")
            lines.append(f"  AI model: {config.AI_MODEL}")
            lines.append("")
    
    # Available devices
    lines.append("AVAILABLE DEVICES:")
    
    # Cameras
    try:
        import cv2
        lines.append("  Cameras:")
        for i in range(5):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                lines.append(f"    {i}: {w}x{h}")
                cap.release()
    except Exception as e:
        lines.append(f"  Cameras: Error - {e}")
    
    # Audio devices
    try:
        import pyaudio
        p = pyaudio.PyAudio()
        
        lines.append("  Audio Input:")
        for i in range(p.get_device_count()):
            info = p.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:
                lines.append(f"    {i}: {info['name']}")
        
        lines.append("  Audio Output:")
        for i in range(p.get_device_count()):
            info = p.get_device_info_by_index(i)
            if info['maxOutputChannels'] > 0:
                lines.append(f"    {i}: {info['name']}")
        
        p.terminate()
    except Exception as e:
        lines.append(f"  Audio: Error - {e}")
    
    lines.append("")
    lines.append("=" * 60)
    
    return "\n".join(lines)


def check_system_requirements() -> Dict[str, Any]:
    """
    Check if system meets requirements for Monica AI.
    
    Returns:
        Dictionary with requirement status
    """
    results = {
        'passed': True,
        'warnings': [],
        'errors': []
    }
    
    # Check Python version
    if sys.version_info < (3, 8):
        results['errors'].append(f"Python 3.8+ required, found {sys.version}")
        results['passed'] = False
    
    # Check required packages
    required = ['numpy', 'cv2', 'PIL']
    for pkg in required:
        try:
            __import__(pkg)
        except ImportError:
            results['errors'].append(f"Required package not installed: {pkg}")
            results['passed'] = False
    
    # Check optional packages
    optional = [
        ('torch', 'GPU acceleration'),
        ('whisper', 'Speech recognition'),
        ('piper', 'Text-to-speech'),
        ('ollama', 'AI conversation'),
    ]
    
    for pkg, feature in optional:
        try:
            __import__(pkg)
        except ImportError:
            results['warnings'].append(f"{pkg} not installed - {feature} will be limited")
    
    # Check GPU
    try:
        import torch
        if not torch.cuda.is_available():
            results['warnings'].append("CUDA not available - using CPU (slower)")
    except ImportError:
        pass
    
    return results
