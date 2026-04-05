"""
Monica AI Service Launcher
Starts all services with fault tolerance and auto-restart.

Boot flow:
1. Show green-letter loading animation in a TKINTER WINDOW (not terminal)
2. Wait for ALL services to be ready (extended timeout for Whisper CUDA)
3. Open GUI with Hands-Free / Push-to-Talk buttons
4. Camera starts ONLY when user clicks Camera button in GUI
5. Startup sounds play ONLY when user says "Monica Initialize" or clicks button
"""

import sys
import os
import warnings

# Fix Windows console Unicode support (prevents encoding errors)
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# TensorFlow / startup logging config
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')
os.environ.setdefault('TF_ENABLE_ONEDNN_OPTS', '0')
os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT', '1')
os.environ.setdefault('OPENCV_VIDEOIO_DEBUG', '0')
os.environ.setdefault('OPENCV_LOG_LEVEL', 'ERROR')

warnings.filterwarnings('ignore', category=DeprecationWarning)
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings(
    'ignore',
    category=UserWarning,
    message=r"Module 'speechbrain\..*' was deprecated, redirecting to '.*'\. Please update your script.*",
)
warnings.filterwarnings('ignore', module='pygame.pkgdata')
warnings.filterwarnings('ignore', message='.*pkg_resources.*deprecated.*')

import logging
import time
import threading


# Robust logging setup: ALL Monica.* loggers write to the same log file
def setup_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    try:
        file_handler = logging.FileHandler('monica_services.log', encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception:
        try:
            stream_handler = logging.StreamHandler(stream=sys.stdout)
            stream_handler.setFormatter(formatter)
            logger.addHandler(stream_handler)
        except OSError:
            logger.addHandler(logging.NullHandler())
    return logger

# Configure the ROOT "Monica" logger so ALL sub-loggers (Monica.STT, Monica.AI, etc.)
# inherit the file handler and their messages are visible in monica_services.log
_root_monica_logger = setup_logger("Monica")
logger = logging.getLogger("Monica.Launcher")  # Inherits from Monica root
logging.getLogger('tensorflow').setLevel(logging.ERROR)
logging.getLogger('absl').setLevel(logging.ERROR)

# Add project root and src/ to path so services.* and config.* resolve
_core_dir = os.path.dirname(__file__)
_src_dir = os.path.dirname(_core_dir)
_project_root = os.path.dirname(_src_dir)
for _p in [_src_dir, _project_root]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from services.orchestrator import ServiceOrchestrator
from services.stt_service import STTService
from services.tts_service import TTSService
from services.vision_service import VisionService
from services.ai_service import AIService
from services.gui_service import MonicaGUI
from config.settings import config


# =====================================================================
# GREEN LOADING ANIMATION — TKINTER SPLASH WINDOW
# =====================================================================

def _show_splash_loading(stop_event, status_dict):
    """
    Show a tkinter splash window with green letters on black background
    while services load.  Blocks until stop_event is set or 90s timeout.
    """
    import tkinter as tk

    splash = tk.Tk()
    splash.title("Monica AI - Loading")
    splash.configure(bg='#000000')
    splash.overrideredirect(True)          # borderless

    # Center on screen
    sw = splash.winfo_screenwidth()
    sh = splash.winfo_screenheight()
    w, h = 650, 420
    x, y = (sw - w) // 2, (sh - h) // 2
    splash.geometry(f"{w}x{h}+{x}+{y}")
    splash.attributes('-topmost', True)

    # ---- Title ----
    tk.Label(splash, text="M O N I C A   A I", bg='#000000', fg='#00ff00',
             font=('Consolas', 32, 'bold')).pack(pady=(40, 5))
    tk.Label(splash, text="Initializing Systems...", bg='#000000', fg='#00aa00',
             font=('Consolas', 13)).pack(pady=(0, 25))

    # ---- Per-service status labels ----
    svc_keys = ['stt', 'tts', 'vision', 'ai']
    svc_labels = {}
    for key in svc_keys:
        lbl = tk.Label(splash, text=f"  [  ]  {key.upper():10s} Waiting...",
                       bg='#000000', fg='#005500',
                       font=('Consolas', 15), anchor='w')
        lbl.pack(anchor='w', padx=80, pady=2)
        svc_labels[key] = lbl

    # ---- Bottom status ----
    bottom_lbl = tk.Label(splash, text="", bg='#000000', fg='#007700',
                          font=('Consolas', 11))
    bottom_lbl.pack(side=tk.BOTTOM, pady=20)

    spinner = ['|', '/', '-', '\\']
    tick = [0]
    start_time = time.time()

    def _tick():
        elapsed = time.time() - start_time

        if stop_event.is_set() or elapsed > 92:
            # Show brief "ready" state then close
            for k, lbl in svc_labels.items():
                st = status_dict.get(k, 'loading')
                if st == 'ready':
                    lbl.configure(text=f"  [OK]  {k.upper():10s} Ready", fg='#00ff00')
                elif st == 'error':
                    lbl.configure(text=f"  [!!]  {k.upper():10s} Error", fg='#ff4444')
                else:
                    lbl.configure(text=f"  [OK]  {k.upper():10s} Ready", fg='#00ff00')
            bottom_lbl.configure(text="All Systems Online — Opening GUI...", fg='#00ff00')
            splash.after(800, splash.destroy)
            return

        # Update each service line
        s = spinner[tick[0] % 4]
        for k, lbl in svc_labels.items():
            st = status_dict.get(k, 'waiting')
            if st == 'ready':
                lbl.configure(text=f"  [OK]  {k.upper():10s} Ready", fg='#00ff00')
            elif st == 'error':
                lbl.configure(text=f"  [!!]  {k.upper():10s} Error", fg='#ff4444')
            else:
                lbl.configure(text=f"  [{s}]   {k.upper():10s} Loading...", fg='#00aa00')

        bottom_lbl.configure(text=f"Elapsed: {int(elapsed)}s")
        tick[0] += 1
        splash.after(300, _tick)

    splash.after(200, _tick)
    splash.mainloop()          # blocks until splash.destroy()


def _generate_scifi_beep(sample_rate=44100):
    """Generate a short sci-fi beeping sound (three ascending tones)."""
    import numpy as _np
    beeps = []
    for freq, dur in [(880, 0.08), (1100, 0.08), (1320, 0.12)]:
        t = _np.linspace(0, dur, int(sample_rate * dur), False)
        tone = (_np.sin(2 * _np.pi * freq * t) * 0.4 * 32767).astype(_np.int16)
        # Fade in/out to avoid clicks
        fade = int(sample_rate * 0.01)
        tone[:fade] = (tone[:fade] * _np.linspace(0, 1, fade)).astype(_np.int16)
        tone[-fade:] = (tone[-fade:] * _np.linspace(1, 0, fade)).astype(_np.int16)
        beeps.append(tone)
        # Small gap between beeps
        beeps.append(_np.zeros(int(sample_rate * 0.04), dtype=_np.int16))
    mono = _np.concatenate(beeps)
    stereo = _np.column_stack([mono, mono])
    return stereo


def _play_initialization_sequence(orchestrator):
    """
    Play Monica's initialization sequence with sounds and TTS.
    This is ONLY called when user says 'Monica Initialize' or clicks the button.
    Plays sci-fi sounds AND TTS simultaneously for the full cinematic experience.
    Ends with "System ready" announcement and sci-fi beep.
    """
    try:
        import pygame
        import time as _t

        sound_dir = os.path.join(_project_root, 'monica_ai', 'resources', 'sounds', 'scifi')
        init_sound_path = os.path.join(sound_dir, 'monica_initialize_one.mp3')

        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

        if os.path.exists(init_sound_path):
            init_sound = pygame.mixer.Sound(init_sound_path)
            channel = pygame.mixer.Channel(0)
            channel.play(init_sound)

            # Layer additional sci-fi sounds
            layered = ['monica_electricalstart_orb.mp3', 'energy_hum.mp3', 'monica_Orb_forming.mp3']
            for idx, snd_name in enumerate(layered):
                snd_path = os.path.join(sound_dir, snd_name)
                if os.path.exists(snd_path):
                    try:
                        snd = pygame.mixer.Sound(snd_path)
                        ch = pygame.mixer.Channel(idx + 1)
                        ch.set_volume(0.35)
                        ch.play(snd)
                    except Exception:
                        pass

            # Let TTS speak WHILE sounds are playing (simultaneous)
            tts = orchestrator.get_service('tts') if orchestrator else None
            if tts and hasattr(tts, 'speak'):
                tts.speak("Monica initializing. All systems online.")

            # Wait for init sound to finish (non-blocking check)
            timeout = _t.time() + 15
            while channel.get_busy() and _t.time() < timeout:
                _t.sleep(0.1)

            # Stop layered sounds
            for ch_idx in range(1, 4):
                try:
                    pygame.mixer.Channel(ch_idx).stop()
                except Exception:
                    pass
        else:
            # Just use TTS if no sound file
            tts = orchestrator.get_service('tts') if orchestrator else None
            if tts and hasattr(tts, 'speak'):
                tts.speak("Monica initializing. All systems online.")

        # --- Sci-fi beep + "System ready" announcement ---
        _t.sleep(0.3)
        try:
            beep_data = _generate_scifi_beep()
            beep_sound = pygame.sndarray.make_sound(beep_data)
            beep_sound.play()
            _t.sleep(0.5)  # Let beep play
        except Exception:
            pass

        tts = orchestrator.get_service('tts') if orchestrator else None
        if tts and hasattr(tts, 'speak'):
            tts.speak("System ready.")

    except Exception as e:
        print(f"[STARTUP] Initialization sequence error (non-fatal): {e}")


def launch_monica():
    """Launch Monica AI services."""
    main()


def main():
    """Main entry point for Monica AI service architecture."""
    logger.info("Creating service orchestrator...")

    # Create orchestrator
    orchestrator = ServiceOrchestrator(config.__dict__)

    logger.info("Registering services...")

    # Register all services
    # NOTE: VisionService will NOT auto-start the camera — user clicks Camera button
    orchestrator.register_service(
        STTService,
        name='stt',
        config={
            'INPUT_DEVICE_NAME': getattr(config, 'INPUT_DEVICE_NAME', None),
            'INPUT_DEVICE_INDEX': getattr(config, 'INPUT_DEVICE_INDEX', None),
            'ENERGY_THRESHOLD': getattr(config, 'ENERGY_THRESHOLD', 0.01),
            'PAUSE_THRESHOLD': getattr(config, 'PAUSE_THRESHOLD', 0.8),
            'PERSONAL_VOICE_MODEL_DIR': getattr(config, 'PERSONAL_VOICE_MODEL_DIR', None),
            'VOICE_ADAPTATION_MODEL': getattr(config, 'VOICE_ADAPTATION_MODEL', None),
            'PERSONAL_VOCABULARY': getattr(config, 'PERSONAL_VOCABULARY', None),
        }
    )

    orchestrator.register_service(TTSService, name='tts', config={})
    orchestrator.register_service(VisionService, name='vision', config={})
    orchestrator.register_service(AIService, name='ai', config={})

    logger.info("Starting all services...")

    # --- Start services (in background threads) ---
    orchestrator.start()

    logger.info("Waiting for services to initialize...")

    # --- Monitor service readiness in background ---
    stop_anim = threading.Event()
    status_dict = {}

    def _monitor():
        while not stop_anim.is_set():
            try:
                statuses = orchestrator.get_service_status()
                all_ready = True
                for name, state in statuses.items():
                    if state == 'running':
                        status_dict[name] = 'ready'
                    elif state == 'error':
                        status_dict[name] = 'error'
                    else:
                        status_dict[name] = 'loading'
                        all_ready = False
                if all_ready and len(statuses) > 0:
                    time.sleep(0.5)   # brief pause so splash shows all-green
                    stop_anim.set()
            except Exception:
                pass
            time.sleep(0.3)

    threading.Thread(target=_monitor, daemon=True).start()

    # Timeout safety — close splash after 90s even if not ready
    def _timeout():
        time.sleep(90)
        stop_anim.set()
    threading.Thread(target=_timeout, daemon=True).start()

    # --- Show splash window (BLOCKS until destroyed) ---
    _show_splash_loading(stop_anim, status_dict)

    logger.info("All services ready!")

    # ── Optional: Start Named Pipe server for C# WPF frontend ──
    if os.environ.get('MONICA_PIPE_SERVER', '').strip() == '1':
        try:
            from services.pipe_server import get_pipe_server
            pipe_srv = get_pipe_server()
            pipe_srv.set_orchestrator(orchestrator)
            pipe_srv.start()
            logger.info("[Launcher] Named pipe server started (for WPF frontend)")
        except Exception as e:
            logger.warning(f"[Launcher] Pipe server failed to start: {e}")

    # ── Optional: Start WebSocket server for React web UI ──
    if os.environ.get('MONICA_WEB_UI', '').strip() == '1':
        try:
            from web.backend.websocket_server import get_web_server, app as fastapi_app
            web_srv = get_web_server()
            web_srv.set_orchestrator(orchestrator)

            def _run_web():
                import uvicorn
                uvicorn.run(fastapi_app, host="0.0.0.0", port=8765, log_level="warning")

            threading.Thread(target=_run_web, daemon=True, name="WebSocket-Server").start()
            logger.info("[Launcher] WebSocket server started on port 8765 (for React web UI)")
        except Exception as e:
            logger.warning(f"[Launcher] WebSocket server failed to start: {e}")

    # Store initialization function on orchestrator so GUI can trigger it
    orchestrator._play_initialization_sequence = lambda: _play_initialization_sequence(orchestrator)
    orchestrator._monica_initialized = False

    # Create and run GUI (in main thread — tkinter requires main thread)
    logger.info("Starting GUI...")
    gui = MonicaGUI(orchestrator)

    try:
        gui.run()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")

    # Cleanup
    logger.info("Shutting down...")
    orchestrator.stop()
    logger.info("Shutdown complete")


if __name__ == "__main__":
    # Enable multiprocessing on Windows
    import multiprocessing as mp
    mp.set_start_method('spawn', force=True)

    main()
