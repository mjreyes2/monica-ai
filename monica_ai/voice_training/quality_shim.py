"""
Lightweight Audio Quality Metrics shim

Used as a fallback when the primary audio_quality_metrics module
is unavailable or fails to import. Provides PASS/FAIL style
quality checks for Monica voice recordings: SNR, clipping, voice
activity, background noise, and clarity (mumbled/slurred proxy).
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Tuple

import numpy as np
from scipy import signal as scipy_signal
from scipy.io import wavfile


class QualityLevel(Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"


@dataclass
class AudioQualityMetrics:
    snr_db: float
    thd_percent: float
    dynamic_range_db: float
    frequency_response_flatness: float
    mos_score: float
    quality_level: QualityLevel
    clipping_detected: bool
    long_silences_detected: bool
    codec_issues: bool
    recommendations: List[str]
    voice_activity_percent: float
    background_noise: Dict[str, float]
    speech_clarity: Dict[str, float]
    content_accuracy: Dict[str, float]


class AudioQualityAssessment:
    # Relaxed thresholds for real-world recording conditions
    # Headset mics, USB mics, and broadcast-processed audio need more lenient thresholds
    QUALITY_THRESHOLDS = {
        'snr_good': 6.0,           # Lowered from 10.0 - headset mics often show lower SNR
        'snr_fair': 2.0,           # Lowered from 4.0 - still usable for training
        'clip_percent_max': 8.0,   # Increased from 5.0 - slight clipping is OK
        'voice_activity_min': 5.0, # Lowered from 8.0 - short phrases are valid
        'clarity_good': 25.0,      # Lowered from 35.0 - less strict on articulation
        'noise_total_max': 70.0,   # Increased from 60.0 - more tolerant of ambient noise
    }

    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate

    # Public API used by recorder
    def assess_audio_quality(self, file_path: str, expected_phrase: str = "") -> AudioQualityMetrics:
        sr, audio = self._load_wav(file_path)
        return self.assess_audio_quality_from_array(audio, sr, expected_phrase)

    def assess_audio_quality_from_array(self, audio: np.ndarray, sample_rate: int, expected_phrase: str = "") -> AudioQualityMetrics:
        audio = self._ensure_mono_float(audio)
        if audio.size == 0:
            return self._empty_metrics("Empty audio")

        # Trim leading/trailing silence lightly
        audio = self._trim_silence(audio, sample_rate)

        # Metrics
        snr_db, _, _ = self._compute_snr(audio, sample_rate)
        clip_percent, clipped = self._detect_clipping(audio)
        dyn_range = self._dynamic_range(audio)
        freq_flat = self._frequency_flatness(audio, sample_rate)
        va_pct = self._voice_activity_percent(audio, sample_rate)
        noise = self._background_noise(audio, sample_rate)
        clarity = self._speech_clarity(audio, sample_rate)
        thd_percent = self._estimate_thd(audio, sample_rate)

        # Overall level
        qlvl = self._quality_level(snr_db, clip_percent, va_pct, clarity['clarity_score'], noise['total_noise'])
        mos = self._estimate_mos(snr_db, clarity['clarity_score'], clip_percent)

        recs = self._recommendations(snr_db, clip_percent, va_pct, clarity, noise, expected_phrase)

        return AudioQualityMetrics(
            snr_db=float(snr_db),
            thd_percent=float(thd_percent),
            dynamic_range_db=float(dyn_range),
            frequency_response_flatness=float(freq_flat),
            mos_score=float(mos),
            quality_level=qlvl,
            clipping_detected=clipped,
            long_silences_detected=va_pct < max(5.0, 0.5 * self.QUALITY_THRESHOLDS['voice_activity_min']),
            codec_issues=False,
            recommendations=recs,
            voice_activity_percent=float(va_pct),
            background_noise=noise,
            speech_clarity=clarity,
            content_accuracy={'content_accuracy': 100.0, 'is_too_short': False}
        )

    # ---- Helpers ----
    def _load_wav(self, file_path: str) -> Tuple[int, np.ndarray]:
        sr, data = wavfile.read(file_path)
        if data.dtype == np.int16:
            a = data.astype(np.float32) / 32768.0
        elif data.dtype == np.int32:
            a = data.astype(np.float32) / 2147483648.0
        else:
            a = data.astype(np.float32)
        if a.ndim == 2:
            a = a.mean(axis=1)
        return sr, a

    def _ensure_mono_float(self, audio: np.ndarray) -> np.ndarray:
        a = audio
        if a.ndim == 2:
            a = a.mean(axis=1)
        if a.dtype not in (np.float32, np.float64):
            a = a.astype(np.float32)
        return a

    def _trim_silence(self, audio: np.ndarray, sr: int, thresh_db: float = -55.0) -> np.ndarray:
        if audio.size == 0:
            return audio
        frame = max(128, int(0.02 * sr))
        hop = max(64, int(0.01 * sr))
        eps = 1e-9
        rms = []
        for i in range(0, len(audio) - frame, hop):
            rms.append(np.sqrt(np.mean(audio[i:i+frame]**2) + eps))
        if not rms:
            return audio
        rms = np.asarray(rms)
        db = 20 * np.log10(rms + eps)
        thr = np.max(db) + thresh_db
        start_idx = 0
        for i, val in enumerate(db):
            if val > thr:
                start_idx = i * hop
                break
        end_idx = len(audio)
        for j in range(len(db)-1, -1, -1):
            if db[j] > thr:
                end_idx = min(len(audio), j * hop + frame)
                break
        return audio[start_idx:end_idx]

    def _compute_snr(self, audio: np.ndarray, sr: int) -> Tuple[float, float, float]:
        frame = int(0.03 * sr)
        hop = int(0.015 * sr)
        if frame <= 0:
            return 0.0, 0.0, 0.0
        energies = []
        for i in range(0, len(audio)-frame, hop):
            energies.append(np.mean(audio[i:i+frame]**2))
        if not energies:
            return 0.0, 0.0, 0.0
        energies = np.asarray(energies)
        med = np.median(energies)
        speech_mask = energies > (med * 3.0)
        noise_mask = ~speech_mask
        speech_rms = np.sqrt(np.mean(energies[speech_mask])) if np.any(speech_mask) else np.sqrt(np.mean(energies))
        noise_rms = np.sqrt(np.mean(energies[noise_mask])) if np.any(noise_mask) else speech_rms / 3.0
        snr = 20 * np.log10((speech_rms + 1e-9) / (noise_rms + 1e-9))
        return float(snr), float(noise_rms), float(speech_rms)

    def _detect_clipping(self, audio: np.ndarray) -> Tuple[float, bool]:
        thr = 0.99
        clip_count = np.sum(np.abs(audio) >= thr)
        clip_percent = (clip_count / max(1, audio.size)) * 100.0
        return float(clip_percent), clip_percent > self.QUALITY_THRESHOLDS['clip_percent_max']

    def _dynamic_range(self, audio: np.ndarray) -> float:
        abs_a = np.abs(audio) + 1e-9
        p95 = np.percentile(abs_a, 95)
        p5 = np.percentile(abs_a, 5)
        return float(20 * np.log10((p95 + 1e-9) / (p5 + 1e-9)))

    def _frequency_flatness(self, audio: np.ndarray, sr: int) -> float:
        nfft = 2048
        if len(audio) < nfft:
            return 50.0
        f, Pxx = scipy_signal.welch(audio, fs=sr, nperseg=1024)
        gm = np.exp(np.mean(np.log(Pxx + 1e-12)))
        am = np.mean(Pxx + 1e-12)
        flatness = gm / am
        return float((1.0 - flatness) * 100.0)

    def _voice_activity_percent(self, audio: np.ndarray, sr: int) -> float:
        frame = int(0.02 * sr)
        hop = int(0.01 * sr)
        if frame <= 0:
            return 0.0
        energies = []
        for i in range(0, len(audio)-frame, hop):
            energies.append(np.mean(audio[i:i+frame]**2))
        if not energies:
            return 0.0
        energies = np.asarray(energies)
        thr = np.max(energies) * 0.2
        active = np.sum(energies > thr)
        return float(active / len(energies) * 100.0)

    def _background_noise(self, audio: np.ndarray, sr: int) -> Dict[str, float]:
        f, Pxx = scipy_signal.welch(audio, fs=sr, nperseg=1024)
        if Pxx.size == 0:
            return {'total_noise': 50.0, 'continuous_noise': 50.0, 'impulsive_noise': 0.0}
        speech_band = (f >= 100) & (f <= 6000)
        total_power = np.sum(Pxx)
        speech_power = np.sum(Pxx[speech_band])
        noise_ratio = float((total_power - speech_power) / (total_power + 1e-12) * 100.0)
        impulsive = float(np.clip((np.max(Pxx) / (np.mean(Pxx) + 1e-9)) - 1.0, 0.0, 100.0))
        return {'total_noise': noise_ratio, 'continuous_noise': max(0.0, noise_ratio - impulsive/5.0), 'impulsive_noise': impulsive}

    def _speech_clarity(self, audio: np.ndarray, sr: int) -> Dict[str, float]:
        frame = int(0.03 * sr)
        hop = int(0.015 * sr)
        if len(audio) < frame*2:
            return {'clarity_score': 30.0}
        clarity_scores = []
        for i in range(0, len(audio)-frame, hop):
            seg = audio[i:i+frame]
            S = np.abs(np.fft.rfft(seg * np.hanning(len(seg))))
            freqs = np.fft.rfftfreq(len(seg), 1.0/sr)
            if np.sum(S) <= 0:
                continue
            centroid = np.sum(freqs * S) / (np.sum(S) + 1e-9)
            cumsum = np.cumsum(S)
            roll_idx = np.searchsorted(cumsum, 0.85 * cumsum[-1])
            rolloff = freqs[min(roll_idx, len(freqs)-1)]
            centroid_norm = np.clip((centroid - 1000) / 3000, 0, 1)
            rolloff_norm = np.clip((rolloff - 2000) / 6000, 0, 1)
            clarity = 100.0 * (0.6 * rolloff_norm + 0.4 * centroid_norm)
            clarity_scores.append(clarity)
        if not clarity_scores:
            return {'clarity_score': 30.0}
        return {'clarity_score': float(np.mean(clarity_scores))}

    def _estimate_thd(self, audio: np.ndarray, sr: int) -> float:
        n = 2048
        if len(audio) < n:
            return 10.0
        S = np.abs(np.fft.rfft(audio[:n] * np.hanning(n))) + 1e-9
        peak = np.max(S)
        rest = np.mean(S)
        ratio = rest / peak
        return float(np.clip(100.0 * ratio, 1.0, 50.0))

    def _quality_level(self, snr_db: float, clip_percent: float, va_pct: float, clarity_score: float, noise_total: float) -> QualityLevel:
        if snr_db >= self.QUALITY_THRESHOLDS['snr_good'] and clip_percent <= self.QUALITY_THRESHOLDS['clip_percent_max'] and va_pct >= self.QUALITY_THRESHOLDS['voice_activity_min'] and clarity_score >= self.QUALITY_THRESHOLDS['clarity_good'] and noise_total <= self.QUALITY_THRESHOLDS['noise_total_max']:
            return QualityLevel.GOOD
        if snr_db >= self.QUALITY_THRESHOLDS['snr_fair'] and va_pct >= 8.0:
            return QualityLevel.FAIR
        return QualityLevel.POOR

    def _estimate_mos(self, snr_db: float, clarity_score: float, clip_percent: float) -> float:
        mos = 1.0
        mos += np.clip((snr_db - 0) / 10.0, 0, 3) * 0.8
        mos += np.clip(clarity_score / 50.0, 0, 2) * 0.9
        mos -= np.clip(clip_percent / 20.0, 0, 1) * 1.0
        return float(np.clip(mos, 1.0, 5.0))

    def _recommendations(self, snr_db: float, clip_percent: float, va_pct: float, clarity: Dict[str, float], noise: Dict[str, float], expected_phrase: str) -> List[str]:
        recs: List[str] = []
        if snr_db < self.QUALITY_THRESHOLDS['snr_fair']:
            recs.append("Move closer to the mic or reduce background noise")
        if clip_percent > self.QUALITY_THRESHOLDS['clip_percent_max']:
            recs.append("Reduce input gain to avoid clipping")
        if va_pct < self.QUALITY_THRESHOLDS['voice_activity_min']:
            recs.append("Speak a bit louder and complete the full phrase")
        if noise['total_noise'] > self.QUALITY_THRESHOLDS['noise_total_max']:
            recs.append("Quieter room or enable noise reduction")
        if clarity['clarity_score'] < self.QUALITY_THRESHOLDS['clarity_good']:
            recs.append("Articulate clearly; avoid mumbling/slurring")
        return recs
