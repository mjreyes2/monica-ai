"""Verify all integration points are connected properly."""
import sys
import os

_test_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_test_dir)
sys.path.insert(0, os.path.join(_project_root, 'src'))
sys.path.insert(0, _project_root)

passed = 0
failed = 0

def check(label, condition):
    global passed, failed
    if condition:
        print(f"  [OK] {label}")
        passed += 1
    else:
        print(f"  [FAIL] {label}")
        failed += 1

print("=" * 60)
print("MONICA AI - INTEGRATION VERIFICATION")
print("=" * 60)

# 1. New utility modules
print("\n--- Utility Modules ---")
try:
    from utils.location_services import get_location_services, LocationServices
    ls = get_location_services()
    check("LocationServices import + singleton", isinstance(ls, LocationServices))
except Exception as e:
    check(f"LocationServices import: {e}", False)

try:
    from utils.free_apis import get_free_apis, FreeAPIs
    fa = get_free_apis()
    check("FreeAPIs import + singleton", isinstance(fa, FreeAPIs))
except Exception as e:
    check(f"FreeAPIs import: {e}", False)

try:
    from ui.monica_free_maps import get_free_maps, FreeMapTileSystem
    fm = get_free_maps()
    check("FreeMapTileSystem import + singleton", isinstance(fm, FreeMapTileSystem))
    check("FreeMapTileSystem has ESRI server", "esri_satellite" in fm.TILE_SERVERS)
    check("FreeMapTileSystem cache dir exists", fm.cache_dir.exists())
except Exception as e:
    check(f"FreeMapTileSystem: {e}", False)

# 2. Knowledge connector integration
print("\n--- Knowledge Connector ---")
try:
    from ai.knowledge_connector import KnowledgeConnector
    kc = KnowledgeConnector()
    check("KnowledgeConnector created", kc is not None)
    check("Has _search_location method", hasattr(kc, '_search_location'))
    check("Has _search_free_apis method", hasattr(kc, '_search_free_apis'))
    check("Has _search_satellite method", hasattr(kc, '_search_satellite'))
except Exception as e:
    check(f"KnowledgeConnector: {e}", False)

# 3. Config paths
print("\n--- Config & Data Paths ---")
try:
    from config.settings import config
    base = str(config.BASE_DIR)
    check("BASE_DIR exists", os.path.isdir(base))
    check("data/ exists", os.path.isdir(os.path.join(base, 'data')))
    check("models/ exists", os.path.isdir(os.path.join(base, 'models')))
    check("src/ exists", os.path.isdir(os.path.join(base, 'src')))
    check("monica_ai/ exists", os.path.isdir(os.path.join(base, 'monica_ai')))
    check("config/ exists", os.path.isdir(os.path.join(base, 'config')))

    pvm = getattr(config, 'PERSONAL_VOICE_MODEL_DIR', None)
    check("PERSONAL_VOICE_MODEL_DIR configured", pvm is not None)
    if pvm:
        check("Personal voice model dir exists", os.path.isdir(str(pvm)))

    va = getattr(config, 'VOICE_ADAPTATION_MODEL', None)
    check("VOICE_ADAPTATION_MODEL configured", va is not None)
    if va:
        check("Voice adaptation model file exists", os.path.isfile(str(va)))

    pv = getattr(config, 'PERSONAL_VOCABULARY', None)
    check("PERSONAL_VOCABULARY configured", pv is not None)
    if pv:
        check("Personal vocabulary file exists", os.path.isfile(str(pv)))
except Exception as e:
    check(f"Config: {e}", False)

# 4. OneDrive data access
print("\n--- OneDrive Data Access ---")
try:
    data_training = os.path.join(base, 'data', 'training')
    check("data/training/ exists", os.path.isdir(data_training))

    stt_recs = os.path.join(data_training, 'personal_voice_model', 'stt_training_recordings')
    if os.path.isdir(stt_recs):
        count = len(os.listdir(stt_recs))
        check(f"STT recordings: {count} files", count > 0)
    else:
        check("STT recordings dir", False)

    tts_dir = os.path.join(data_training, 'monica_tts_training')
    check("TTS training dir exists", os.path.isdir(tts_dir))

    mem_adv = os.path.join(base, 'monica_memory_advanced')
    check("monica_memory_advanced/ exists", os.path.isdir(mem_adv))
except Exception as e:
    check(f"OneDrive data: {e}", False)

# 5. Models directory
print("\n--- Models Directory ---")
try:
    models_dir = os.path.join(base, 'models')
    items = os.listdir(models_dir) if os.path.isdir(models_dir) else []
    check(f"models/ has {len(items)} items", len(items) > 0)

    kb_index = os.path.join(models_dir, 'kb_index')
    check("models/kb_index/ exists", os.path.isdir(kb_index))
except Exception as e:
    check(f"Models: {e}", False)

# 6. Globe renderer
print("\n--- Globe Renderer ---")
try:
    from ui.monica_realistic_globe import RealisticGlobeRenderer, GlobeConfig
    gc = GlobeConfig()
    check("GlobeConfig created", gc is not None)
    check("Rotation speed > 0 (west-to-east)", gc.rotation_speed > 0)
    check("Grid enabled", gc.grid_enabled)

    # Check that RealisticGlobeRenderer has NASA download method
    check("Has _download_nasa_blue_marble", hasattr(RealisticGlobeRenderer, '_download_nasa_blue_marble'))
except Exception as e:
    check(f"Globe: {e}", False)

# 7. monica_ai.egg-info
print("\n--- Package Metadata ---")
try:
    egg_info = os.path.join(base, 'monica_ai.egg-info')
    check("monica_ai.egg-info/ exists", os.path.isdir(egg_info))
    pkg_info = os.path.join(egg_info, 'PKG-INFO')
    check("PKG-INFO exists", os.path.isfile(pkg_info))
except Exception as e:
    check(f"egg-info: {e}", False)

# Summary
print()
print("=" * 60)
total = passed + failed
print(f"Results: {passed} passed, {failed} failed out of {total} checks")
print("=" * 60)

if failed > 0:
    print("\nSome checks failed - review above.")
    sys.exit(1)
else:
    print("\nAll integration checks passed!")
