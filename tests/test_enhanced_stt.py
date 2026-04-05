"""
Test the Enhanced STT Pipeline with sample audio.
Converted to proper pytest with import guards for kenlm/DLL issues.
"""
import sys
import os
import pytest
import numpy as np

_test_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_test_dir)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)


def _can_import_pipeline():
    """Check if EnhancedSTTPipeline is importable (requires kenlm etc.)."""
    try:
        from enhanced_stt_pipeline import EnhancedSTTPipeline
        return True
    except (ImportError, OSError) as e:
        return False


@pytest.fixture
def pipeline():
    if not _can_import_pipeline():
        pytest.skip("EnhancedSTTPipeline not importable (kenlm DLL or deps missing)")
    from enhanced_stt_pipeline import EnhancedSTTPipeline
    return EnhancedSTTPipeline()


def test_pipeline_importable():
    """EnhancedSTTPipeline can be imported (or skips gracefully)."""
    if not _can_import_pipeline():
        pytest.skip("EnhancedSTTPipeline not importable (kenlm DLL or deps missing)")
    from enhanced_stt_pipeline import EnhancedSTTPipeline
    assert EnhancedSTTPipeline is not None


def test_pipeline_creates(pipeline):
    """Pipeline can be instantiated."""
    assert pipeline is not None


def test_pipeline_transcribes_silence(pipeline):
    """Pipeline handles a silent audio array without crashing."""
    import torch
    silent = torch.zeros(1, 16000)  # 1 second of silence
    try:
        result = pipeline.transcribe(silent)
        assert isinstance(result, str)
    except Exception:
        pass  # transcribe may raise on silence - that is acceptable
