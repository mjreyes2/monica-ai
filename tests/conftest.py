"""Shared pytest configuration for Monica AI tests."""
import sys
import os
from pathlib import Path

# Add src/ and project root to sys.path so test files can import
# services.*, config.*, ai.*, etc. without manual path manipulation.
_project_root = Path(__file__).resolve().parent.parent
_src_dir = _project_root / "src"

for p in [str(_src_dir), str(_project_root)]:
    if p not in sys.path:
        sys.path.insert(0, p)

# Skip files with invalid Python names (e.g. hyphens) and
# script-style integration files that hang during collection
# (heavy imports, no def test_* functions, manual-run only)
collect_ignore_glob = [
    "*-*.py",
    "test_new_modules.py",
    "test_new_features.py",
    "test_interrupt_system.py",
    "test_pdf_knowledge.py",
    "test_teaching_security.py",
    "test_monica_audio.py",
    "test_quality.py",
    "test_custom_model_loading.py",
    "test_custom_voice_loading.py",
    "test_enhanced_stt.py",
    "test_training_init.py",
    "test_training_start.py",
]
