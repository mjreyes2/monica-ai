"""Comprehensive import smoke test for Monica AI project."""
import sys
import os

# Setup paths
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(project_root, 'src'))
sys.path.insert(0, project_root)

ok = 0
fail = 0
failures = []

modules = [
    # Services layer
    'services.orchestrator',
    'services.stt_service',
    'services.tts_service',
    'services.vision_service',
    'services.ai_service',
    'services.gui_service',
    # Config
    'config.settings',
    # AI modules
    'ai.conversation_manager',
    'ai.multi_model_manager',
    'ai.monica_authentic_personality',
    'ai.monica_education_k12',
    'ai.monica_math_complete',
    'ai.monica_software_skills',
    'ai.monica_counseling_comprehensive',
    'ai.monica_language_teacher',
    'ai.monica_legal_sciences',
    'ai.monica_knowledge_2025',
    'ai.monica_medical_knowledge',
    'ai.monica_intelligence',
    'ai.monica_memory',
    'ai.user_memory',
    'ai.monica_emotion_intelligence',
    'ai.pdf_retriever',
    'ai.maxone_drive_rag',
    # Vision modules
    'vision.camera_manager',
    'vision.vision_system',
    'vision.hand_detector',
    'vision.monica_hand_controller',
    'vision.monica_hand_keyboard',
    'vision.monica_visual_capabilities',
    # Biometric
    'biometric.biometric_detector',
    # UI modules
    'ui.monica_globe_window',
    'ui.monica_realistic_globe',
    'ui.monica_video_enhancer',
    'ui.monica_free_maps',
    'ui.monica_global_webcams',
    # Audio
    'audio.tts_manager',
    'audio.piper_cli',
    'audio.text_normalizer',
    'audio.prosody_enhancer',
    'audio.tts_diagnostics',
    # Core
    'core.monica_services_launcher',
    'core.monica_orb_window',
    'core.monica_ar_hologram_system',
]

print("=" * 60)
print("MONICA AI - COMPREHENSIVE IMPORT SMOKE TEST")
print("=" * 60)

for m in modules:
    try:
        __import__(m)
        ok += 1
        print(f"  [OK] {m}")
    except Exception as e:
        fail += 1
        err_msg = str(e).split('\n')[0][:80]
        print(f"  [FAIL] {m}: {err_msg}")
        failures.append((m, err_msg))

print()
print("=" * 60)
print(f"Results: {ok} passed, {fail} failed out of {ok + fail} modules")
print("=" * 60)

if failures:
    print("\nFailed modules:")
    for m, e in failures:
        print(f"  - {m}: {e}")
else:
    print("\nAll imports passed!")
