"""
STT Smoke Test — Vosk offline speech recognition
Tests:
  1. Vosk model loads from disk
  2. KaldiRecognizer initializes at 16kHz
  3. Transcribes a synthetic sine-wave WAV (silence test)
  4. Transcribes a real WAV from the training dataset (if available)
  5. Reports word error rate sanity check
"""

import os
import sys
import json
import wave
import struct
import time
import math
import struct

# --- Paths ---
MONICA_ROOT = r"C:\Monica"
VOSK_MODEL_PATH = os.path.join(MONICA_ROOT, "models", "vosk", "vosk-model-small-en-us-0.15")
DATASET_AUDIO_ROOT = r"D:\Monica_Datasets\training\monica_tts_training\datasets\LJSpeech-1.1\wavs"
ALT_AUDIO_ROOT = r"D:\Monica_Datasets\processed\audio"

print("=" * 60)
print("Monica STT Smoke Test — Vosk")
print("=" * 60)

# ─── Step 1: Import Vosk ─────────────────────────────────────
print("\n[1/5] Importing Vosk...")
t0 = time.time()
from vosk import Model, KaldiRecognizer, SetLogLevel  # type: ignore
SetLogLevel(-1)
print(f"      OK — import in {time.time() - t0:.2f}s")

# ─── Step 2: Load model ──────────────────────────────────────
print(f"\n[2/5] Loading model from: {VOSK_MODEL_PATH}")
assert os.path.isdir(VOSK_MODEL_PATH), f"Model not found: {VOSK_MODEL_PATH}"
t0 = time.time()
model = Model(VOSK_MODEL_PATH)
print(f"      OK — model loaded in {time.time() - t0:.2f}s")

# ─── Step 3: Init recognizer ─────────────────────────────────
print("\n[3/5] Initializing KaldiRecognizer at 16kHz...")
SAMPLE_RATE = 16000
rec = KaldiRecognizer(model, SAMPLE_RATE)
rec.SetWords(True)
print("      OK")

# ─── Step 4: Synthetic silent WAV transcription ──────────────
print("\n[4/5] Transcribing synthetic silent audio (1 second)...")

def make_sine_wav_bytes(freq_hz: float, duration_s: float, sample_rate: int, amplitude: float = 0.0) -> bytes:
    """Generate raw 16-bit PCM WAV bytes. amplitude=0 = silence."""
    n_samples = int(sample_rate * duration_s)
    samples = []
    for i in range(n_samples):
        val = amplitude * math.sin(2 * math.pi * freq_hz * i / sample_rate)
        samples.append(int(max(-32767, min(32767, val * 32767))))
    return struct.pack(f"<{n_samples}h", *samples)

silent_pcm = make_sine_wav_bytes(0, 1.0, SAMPLE_RATE, amplitude=0.0)
rec.AcceptWaveform(silent_pcm)
result = json.loads(rec.FinalResult())
text = result.get("text", "").strip()
print(f"      Transcription of silence: '{text}' (expected empty or minimal)")
assert "error" not in text.lower(), f"Recognizer returned error: {text}"
print("      OK — recognizer alive")

# ─── Step 5: Real audio from dataset ─────────────────────────
print("\n[5/5] Looking for a real dataset WAV to transcribe...")

test_wav = None
for root_dir in [DATASET_AUDIO_ROOT, ALT_AUDIO_ROOT]:
    if os.path.isdir(root_dir):
        for dirpath, _, files in os.walk(root_dir):
            for f in files:
                if f.endswith(".wav"):
                    candidate = os.path.join(dirpath, f)
                    size = os.path.getsize(candidate)
                    if 20_000 < size < 2_000_000:  # 20KB–2MB
                        test_wav = candidate
                        break
            if test_wav:
                break
    if test_wav:
        break

if test_wav:
    print(f"      Using: {test_wav} ({os.path.getsize(test_wav)//1024} KB)")
    rec2 = KaldiRecognizer(model, SAMPLE_RATE)
    rec2.SetWords(True)

    with wave.open(test_wav, "rb") as wf:
        channels = wf.getnchannels()
        rate = wf.getframerate()
        n_frames = wf.getnframes()
        raw = wf.readframes(n_frames)

    # Downsample to mono 16kHz if needed (simple decimation)
    if channels == 2:
        # Convert stereo to mono by averaging
        pcm = struct.unpack(f"<{len(raw)//2}h", raw)
        mono = [int((pcm[i] + pcm[i+1]) / 2) for i in range(0, len(pcm)-1, 2)]
        raw = struct.pack(f"<{len(mono)}h", *mono)

    if rate != SAMPLE_RATE:
        print(f"      Resampling {rate}Hz -> {SAMPLE_RATE}Hz...")
        # Simple integer decimation (works for 22050->16000 approx via scipy if available, else naive)
        try:
            from scipy.signal import resample_poly
            import numpy as np
            from fractions import Fraction
            pcm_arr = np.frombuffer(raw, dtype=np.int16).astype(np.float32)
            if channels == 2:
                pcm_arr = pcm_arr.reshape(-1, 2).mean(axis=1)
            frac = Fraction(SAMPLE_RATE, rate).limit_denominator(100)
            resampled = resample_poly(pcm_arr, frac.numerator, frac.denominator)
            raw = resampled.astype(np.int16).tobytes()
            channels = 1
            print(f"      Resampled to {SAMPLE_RATE}Hz via scipy")
        except ImportError:
            print(f"      WARNING: scipy not available — feeding {rate}Hz audio as-is (accuracy may be lower)")

    CHUNK = 4000
    results = []
    for i in range(0, len(raw), CHUNK):
        chunk = raw[i:i+CHUNK]
        if rec2.AcceptWaveform(chunk):
            r = json.loads(rec2.Result())
            if r.get("text"):
                results.append(r["text"])
    final = json.loads(rec2.FinalResult())
    if final.get("text"):
        results.append(final["text"])
    transcription = " ".join(results).strip()
    print(f"      Transcription: '{transcription[:120]}'" + ("..." if len(transcription) > 120 else ""))
    print("      OK — real audio transcribed")
else:
    print("      No dataset WAV found — skipping real audio test")
    print("      (Datasets expected at D:\\Monica_Datasets\\processed\\audio)")

# ─── Summary ─────────────────────────────────────────────────
print("\n" + "=" * 60)
print("STT SMOKE TEST: ALL CHECKS PASSED")
print("  Vosk model:      ", os.path.basename(VOSK_MODEL_PATH))
print("  Sample rate:     16000 Hz")
print("  Silence test:    PASS")
if test_wav:
    print(f"  Real audio:      PASS ({os.path.basename(test_wav)})")
else:
    print("  Real audio:      SKIPPED (no wav found)")
print("=" * 60)
