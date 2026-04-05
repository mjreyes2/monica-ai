"""
native_audio.py — Python wrapper for Rust audio accelerator.

Tries to import the compiled Rust module `monica_audio_accel`.
If not available, provides pure-Python/NumPy fallbacks so the rest
of the codebase works identically (just slower).

Usage:
    from audio.native_audio import audio_accel
    resampled = audio_accel.resample(samples, 44100, 16000)
    energy = audio_accel.rms_energy(samples)
    ring = audio_accel.AudioRingBuffer(capacity=88200)
"""
import numpy as np
import math
import logging
from collections import deque
from typing import Optional

logger = logging.getLogger("Monica.NativeAudio")

# ── Try to load the compiled Rust extension ──
_USE_RUST = False
try:
    import monica_audio_accel as _rust
    _USE_RUST = True
    logger.info("[NativeAudio] Rust audio accelerator loaded (5-20x faster)")
except ImportError:
    _rust = None
    logger.info("[NativeAudio] Rust module not compiled — using Python fallbacks")


# ══════════════════════════════════════════════════════════════
#  Pure-Python fallbacks
# ══════════════════════════════════════════════════════════════

def _py_resample(audio: np.ndarray, source_rate: int, target_rate: int) -> np.ndarray:
    """Linear interpolation resampling (Python fallback)."""
    if source_rate == target_rate:
        return audio.copy()
    ratio = target_rate / source_rate
    output_len = int(math.ceil(len(audio) * ratio))
    indices = np.arange(output_len) / ratio
    idx = indices.astype(int)
    frac = (indices - idx).astype(np.float32)
    idx1 = np.minimum(idx + 1, len(audio) - 1)
    return audio[idx] * (1.0 - frac) + audio[idx1] * frac


def _py_resample_sinc(audio: np.ndarray, source_rate: int,
                       target_rate: int, kernel_size: int = 64) -> np.ndarray:
    """Windowed-sinc resampling (Python fallback — slower but higher quality)."""
    try:
        from scipy.signal import resample as scipy_resample
        output_len = int(math.ceil(len(audio) * target_rate / source_rate))
        return scipy_resample(audio, output_len).astype(np.float32)
    except ImportError:
        return _py_resample(audio, source_rate, target_rate)


def _py_rms_energy(audio: np.ndarray) -> float:
    if len(audio) == 0:
        return 0.0
    return float(np.sqrt(np.mean(audio.astype(np.float64) ** 2)))


def _py_peak_amplitude(audio: np.ndarray) -> float:
    if len(audio) == 0:
        return 0.0
    return float(np.max(np.abs(audio)))


def _py_normalize(audio: np.ndarray, target_db: float = -1.0) -> np.ndarray:
    peak = np.max(np.abs(audio))
    if peak < 1e-10:
        return np.zeros_like(audio)
    target_linear = 10.0 ** (target_db / 20.0)
    gain = target_linear / peak
    return np.clip(audio * gain, -1.0, 1.0).astype(np.float32)


def _py_compress(audio: np.ndarray, threshold_db: float = -20.0,
                  ratio: float = 4.0, attack_ms: float = 5.0,
                  release_ms: float = 50.0, sample_rate: int = 22050) -> np.ndarray:
    threshold = 10.0 ** (threshold_db / 20.0)
    attack_coeff = math.exp(-1.0 / (attack_ms * 0.001 * sample_rate))
    release_coeff = math.exp(-1.0 / (release_ms * 0.001 * sample_rate))

    envelope = 0.0
    output = np.empty_like(audio)
    for i in range(len(audio)):
        abs_s = abs(audio[i])
        if abs_s > envelope:
            envelope = attack_coeff * envelope + (1.0 - attack_coeff) * abs_s
        else:
            envelope = release_coeff * envelope + (1.0 - release_coeff) * abs_s

        if envelope > threshold:
            excess_db = 20.0 * math.log10(max(envelope / threshold, 1e-10))
            compressed_db = excess_db / ratio
            gain = 10.0 ** ((compressed_db - excess_db) / 20.0)
        else:
            gain = 1.0

        output[i] = max(-1.0, min(1.0, audio[i] * gain))
    return output.astype(np.float32)


def _py_mix(a: np.ndarray, b: np.ndarray,
             gain_a: float = 1.0, gain_b: float = 1.0) -> np.ndarray:
    length = max(len(a), len(b))
    out = np.zeros(length, dtype=np.float32)
    out[:len(a)] += a[:length] * gain_a
    out[:len(b)] += b[:length] * gain_b
    return np.clip(out, -1.0, 1.0)


def _py_pcm16_to_float(audio: np.ndarray) -> np.ndarray:
    return audio.astype(np.float32) / 32768.0


def _py_float_to_pcm16(audio: np.ndarray) -> np.ndarray:
    return np.clip(audio * 32767.0, -32768, 32767).astype(np.int16)


class _PyAudioRingBuffer:
    """Pure-Python ring buffer fallback."""
    def __init__(self, capacity: int = 88200):
        self._buf = deque(maxlen=capacity)
        self.capacity = capacity

    def push(self, audio: np.ndarray) -> int:
        n = 0
        for s in audio.flat:
            self._buf.append(float(s))
            n += 1
        return n

    def pull(self, count: int) -> np.ndarray:
        n = min(count, len(self._buf))
        out = np.array([self._buf.popleft() for _ in range(n)], dtype=np.float32)
        return out

    def available(self) -> int:
        return len(self._buf)

    def clear(self):
        self._buf.clear()

    def is_empty(self) -> bool:
        return len(self._buf) == 0

    def __len__(self):
        return len(self._buf)

    def __repr__(self):
        return f"PyAudioRingBuffer(capacity={self.capacity}, available={len(self._buf)})"


# ══════════════════════════════════════════════════════════════
#  Unified API
# ══════════════════════════════════════════════════════════════

class _AudioAccelerator:
    """Unified audio accelerator API with automatic Rust/Python dispatch."""

    @property
    def is_native(self) -> bool:
        return _USE_RUST

    def resample(self, audio: np.ndarray, source_rate: int, target_rate: int) -> np.ndarray:
        if _USE_RUST:
            return np.asarray(_rust.resample(audio.astype(np.float32), source_rate, target_rate))
        return _py_resample(audio.astype(np.float32), source_rate, target_rate)

    def resample_sinc(self, audio: np.ndarray, source_rate: int,
                       target_rate: int, kernel_size: int = 64) -> np.ndarray:
        if _USE_RUST:
            return np.asarray(_rust.resample_sinc(
                audio.astype(np.float32), source_rate, target_rate, kernel_size))
        return _py_resample_sinc(audio.astype(np.float32), source_rate, target_rate, kernel_size)

    def rms_energy(self, audio: np.ndarray) -> float:
        if _USE_RUST:
            return _rust.rms_energy(audio.astype(np.float32))
        return _py_rms_energy(audio)

    def peak_amplitude(self, audio: np.ndarray) -> float:
        if _USE_RUST:
            return _rust.peak_amplitude(audio.astype(np.float32))
        return _py_peak_amplitude(audio)

    def normalize(self, audio: np.ndarray, target_db: float = -1.0) -> np.ndarray:
        if _USE_RUST:
            return np.asarray(_rust.normalize(audio.astype(np.float32), target_db))
        return _py_normalize(audio, target_db)

    def compress(self, audio: np.ndarray, threshold_db: float = -20.0,
                  ratio: float = 4.0, attack_ms: float = 5.0,
                  release_ms: float = 50.0, sample_rate: int = 22050) -> np.ndarray:
        if _USE_RUST:
            return np.asarray(_rust.compress(
                audio.astype(np.float32), threshold_db, ratio,
                attack_ms, release_ms, sample_rate))
        return _py_compress(audio, threshold_db, ratio, attack_ms, release_ms, sample_rate)

    def mix(self, a: np.ndarray, b: np.ndarray,
             gain_a: float = 1.0, gain_b: float = 1.0) -> np.ndarray:
        if _USE_RUST:
            return np.asarray(_rust.mix(
                a.astype(np.float32), b.astype(np.float32), gain_a, gain_b))
        return _py_mix(a, b, gain_a, gain_b)

    def pcm16_to_float(self, audio: np.ndarray) -> np.ndarray:
        if _USE_RUST:
            return np.asarray(_rust.pcm16_to_float(audio.astype(np.int16)))
        return _py_pcm16_to_float(audio)

    def float_to_pcm16(self, audio: np.ndarray) -> np.ndarray:
        if _USE_RUST:
            return np.asarray(_rust.float_to_pcm16(audio.astype(np.float32)))
        return _py_float_to_pcm16(audio)

    def AudioRingBuffer(self, capacity: int = 88200):
        if _USE_RUST:
            return _rust.AudioRingBuffer(capacity)
        return _PyAudioRingBuffer(capacity)


# Singleton
audio_accel = _AudioAccelerator()
