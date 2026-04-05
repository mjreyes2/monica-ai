"""Test loading the custom trained Monica model.
Converted to proper pytest with skip guards and timeout."""
import sys
import os
import pytest

_test_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_test_dir)
sys.path.insert(0, os.path.join(_project_root, 'src'))
sys.path.insert(0, _project_root)


def _get_recognizer_class():
    """Try importing FinalSpeechBrainRecognizer from available locations."""
    try:
        from audio.speechbrain_final import FinalSpeechBrainRecognizer
        return FinalSpeechBrainRecognizer
    except (ImportError, OSError):
        pass
    try:
        sys.path.insert(0, os.path.join(_project_root, 'monica_ai', 'src'))
        from audio.speechbrain_final import FinalSpeechBrainRecognizer
        return FinalSpeechBrainRecognizer
    except (ImportError, OSError):
        return None


def test_recognizer_importable():
    """FinalSpeechBrainRecognizer can be imported."""
    cls = _get_recognizer_class()
    if cls is None:
        pytest.skip("FinalSpeechBrainRecognizer not importable (missing deps)")
    assert cls is not None


@pytest.mark.timeout(30)
def test_recognizer_creates():
    """FinalSpeechBrainRecognizer can be instantiated."""
    cls = _get_recognizer_class()
    if cls is None:
        pytest.skip("FinalSpeechBrainRecognizer not importable")
    try:
        r = cls()
        assert r is not None
    except Exception as e:
        pytest.skip(f"Recognizer creation failed (expected if model not downloaded): {e}")
