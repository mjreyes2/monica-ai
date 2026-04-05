"""Full connectivity audit for Monica AI - checks all modules, paths, engines, databases."""
import sys
import os

_script_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.join(_script_dir, '..')
sys.path.insert(0, os.path.join(_project_root, 'src'))
sys.path.insert(0, _project_root)
os.chdir(_project_root)

results = {"ok": 0, "fail": 0, "warn": 0}

def check(label, condition, detail=""):
    if condition:
        results["ok"] += 1
        print(f"  [OK] {label}" + (f" - {detail}" if detail else ""))
    else:
        results["fail"] += 1
        print(f"  [FAIL] {label}" + (f" - {detail}" if detail else ""))

def warn(label, detail=""):
    results["warn"] += 1
    print(f"  [WARN] {label}" + (f" - {detail}" if detail else ""))

print("=" * 60)
print("MONICA AI - FULL CONNECTIVITY AUDIT")
print("=" * 60)

# 1. GPU / CUDA
print("\n--- GPU / CUDA ---")
try:
    import torch
    check("PyTorch installed", True, torch.__version__)
    check("CUDA available", torch.cuda.is_available())
    if torch.cuda.is_available():
        check("GPU detected", True, torch.cuda.get_device_name(0))
except Exception as e:
    check("PyTorch", False, str(e))

# 2. NumPy
print("\n--- NumPy ---")
try:
    import numpy as np
    v = np.__version__
    is_ok = int(v.split('.')[0]) < 2
    check("NumPy compatible", is_ok, f"v{v} ({'<2 OK' if is_ok else '>=2 INCOMPATIBLE'})")
except Exception as e:
    check("NumPy", False, str(e))

# 3. SpeechBrain / STT
print("\n--- STT Engines ---")
try:
    import speechbrain
    check("SpeechBrain", True)
except Exception as e:
    check("SpeechBrain", False, str(e))

try:
    import whisper
    check("Whisper", True)
except ImportError:
    warn("Whisper not installed (optional fallback)")

try:
    import speech_recognition
    check("speech_recognition", True)
except ImportError:
    warn("speech_recognition not installed")

# 4. TTS Engines
print("\n--- TTS Engines ---")
from pathlib import Path

piper_exe = Path(r"C:\Users\Marvi\AppData\Local\Temp\piper\piper\piper.exe")
check("Piper executable", piper_exe.exists(), str(piper_exe))

from config.settings import config
from audio.tts_manager import TTSManager
tm = TTSManager(config)
vp = tm._get_voice_model_path("en_US-amy-medium")
check("TTS initialized", tm.is_initialized, f"engine={tm.engine}")
check("Voice model en_US-amy-medium", vp is not None and vp.exists())

try:
    import pyttsx3
    check("pyttsx3 (system TTS fallback)", True)
except ImportError:
    check("pyttsx3", False)

# 5. Sound Files
print("\n--- Sound Files ---")
snd_dir = Path("monica_ai/resources/sounds/scifi")
snd_files = list(snd_dir.glob("*.mp3")) if snd_dir.exists() else []
check("Scifi sounds directory", snd_dir.exists(), f"{len(snd_files)} mp3 files")
check("monica_initialize_one.mp3", (snd_dir / "monica_initialize_one.mp3").exists())
check("energy_hum.mp3", (snd_dir / "energy_hum.mp3").exists())

# 6. Databases
print("\n--- Databases ---")
for db in ["data/monica_conversations.db", "data/monica_memory.db"]:
    check(db, os.path.exists(db), f"{os.path.getsize(db)//1024}KB" if os.path.exists(db) else "")

ki = "data/knowledge_index/chunks.json"
check("Knowledge index", os.path.exists(ki), f"{os.path.getsize(ki)//1024}KB" if os.path.exists(ki) else "")

# 7. PDF Backend
print("\n--- PDF / Knowledge ---")
try:
    import fitz
    check("PyMuPDF (PDF extraction)", True, f"v{fitz.version[0]}")
except ImportError:
    check("PyMuPDF", False, "pip install PyMuPDF")

try:
    import pytesseract
    check("pytesseract (OCR for scanned PDFs)", True)
except ImportError:
    warn("pytesseract not installed (OCR fallback disabled)")

kb_dir = Path("data/Monica_Knowledge_Base")
if kb_dir.exists():
    pdf_count = len(list(kb_dir.rglob("*.pdf")))
    check("Knowledge Base PDFs", pdf_count > 0, f"{pdf_count} PDFs")
else:
    check("Knowledge Base directory", False)

# 8. Web Search
print("\n--- Web / APIs ---")
try:
    from utils.web_search import get_web_searcher
    check("HIPAA Web Search", True)
except Exception as e:
    check("Web Search", False, str(e))

try:
    from utils.free_apis import get_free_apis
    check("Free APIs (weather, wiki, etc)", True)
except Exception as e:
    warn(f"Free APIs: {e}")

# 9. Ollama AI Backend
try:
    import requests
    r = requests.get("http://localhost:11434/api/tags", timeout=3)
    models = [m["name"] for m in r.json().get("models", [])]
    check("Ollama running", True, f"models: {models}")
except Exception as e:
    check("Ollama", False, str(e))

# 10. Animations
print("\n--- Animations ---")
anims = {
    "Fog": "src/ui/CSS_FOG_ANIMATION/index.html",
    "Clouds": "src/ui/clouds-animation-code/haven-animation.html",
    "Star Field": "animations/starfield.html",
    "Aurora": "animations/aurora.html",
}
for name, path in anims.items():
    check(f"Animation: {name}", os.path.exists(path))

# 11. PlasmaOrb
print("\n--- Visual Effects ---")
ptex = Path("src/ui/PlasmaOrb_ref")
ptex_count = len(list(ptex.glob("*.png"))) if ptex.exists() else 0
check("Plasma textures", ptex_count >= 5, f"{ptex_count} png files")

check("monica.ico", os.path.exists("monica.ico"))
check("Launch_Monica.bat", os.path.exists("Launch_Monica.bat"))
check("Launch_Monica.lnk", os.path.exists("Launch_Monica.lnk"))

# 12. Voice Model / Training
print("\n--- Voice Models / Training ---")
vm = Path("monica_ai/personal_voice_model")
if vm.exists():
    vm_files = list(vm.glob("*"))
    check("Personal voice model dir", True, f"{len(vm_files)} files")
else:
    warn("Personal voice model directory missing")

train = Path("data/training")
if train.exists():
    check("Training data dir", True)
else:
    check("Training data dir", False)

# 13. Camera
print("\n--- Camera / Vision ---")
try:
    from vision.camera_manager import CameraManager
    check("CameraManager importable", True)
except Exception as e:
    check("CameraManager", False, str(e))

try:
    from vision.vision_system import MonicaVisionSystem
    check("VisionSystem importable", True)
except Exception as e:
    check("VisionSystem", False, str(e))

try:
    from core.monica_orb_window import MonicaOrbWindow
    check("MonicaOrbWindow importable", True)
except Exception as e:
    check("MonicaOrbWindow", False, str(e))

try:
    from core.monica_ar_hologram_system import MonicaARHologramSystem
    check("MonicaARHologramSystem importable", True)
except Exception as e:
    check("MonicaARHologramSystem", False, str(e))

# 14. AI Modules
print("\n--- AI Modules ---")
ai_modules = [
    "ai.conversation_manager", "ai.multi_model_manager",
    "ai.monica_authentic_personality", "ai.monica_english_teacher",
    "ai.monica_world_teacher", "ai.monica_emotion_intelligence",
    "ai.monica_memory", "ai.user_memory", "ai.session_memory",
    "ai.user_profile_learner", "ai.knowledge_watcher",
    "ai.knowledge_base_manager", "ai.pdf_retriever",
]
for mod in ai_modules:
    try:
        __import__(mod)
        check(mod, True)
    except Exception as e:
        check(mod, False, str(e))

# 15. Security
print("\n--- Security ---")
try:
    from security.auth_manager import get_auth_manager
    check("Auth Manager", True)
except Exception as e:
    check("Auth Manager", False, str(e))

try:
    from security.hipaa_compliance import get_hipaa_compliance
    check("HIPAA Compliance", True)
except Exception as e:
    check("HIPAA Compliance", False, str(e))

# Summary
print("\n" + "=" * 60)
print(f"AUDIT RESULTS: {results['ok']} OK, {results['fail']} FAIL, {results['warn']} WARN")
if results["fail"] == 0:
    print("ALL CRITICAL CHECKS PASSED!")
else:
    print(f"*** {results['fail']} CRITICAL FAILURES NEED ATTENTION ***")
print("=" * 60)
