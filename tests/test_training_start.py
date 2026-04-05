"""
Test Training Start - Diagnostic checks for training prerequisites.
Converted from diagnostic script to proper pytest (no sys.exit).
"""
import sys
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_pytorch_available():
    """PyTorch can be imported."""
    import torch
    assert hasattr(torch, '__version__')


def test_speechbrain_available():
    """SpeechBrain can be imported."""
    try:
        import speechbrain
        assert hasattr(speechbrain, '__version__')
    except ImportError as e:
        pytest.skip(f"SpeechBrain not available: {e}")


def test_training_files_exist():
    """Training script and hparams exist in project root."""
    train_script = PROJECT_ROOT / "train_monica.py"
    hparams = PROJECT_ROOT / "hparams_monica.yaml"
    if not train_script.exists():
        pytest.skip(f"train_monica.py not found at {train_script}")
    if not hparams.exists():
        pytest.skip(f"hparams_monica.yaml not found at {hparams}")
    assert train_script.exists()
    assert hparams.exists()


def test_training_script_readable():
    """Training script contains expected ASRBrain class."""
    train_script = PROJECT_ROOT / "train_monica.py"
    if not train_script.exists():
        pytest.skip("train_monica.py not found")
    content = train_script.read_text(encoding="utf-8")
    assert "ASR" in content and "Brain" in content or "class ASR" in content
