# Monica AI — Multi-Language Native Modules

Monica AI uses **4 languages** alongside Python for maximum performance:

| Language | Purpose | Speedup | Location |
|----------|---------|---------|----------|
| **C++ (pybind11)** | Vision hot-path: frame compositing, skeleton drawing, globe rendering | 10-50x | `native/cpp/` |
| **Rust (PyO3)** | Audio pipeline: resampling, ring buffer, compression, mixing | 5-20x | `native/rust/` |
| **TypeScript/React** | Web-based UI with WebSocket video streaming and WebGL globe | Smoother UI | `web/` |
| **C# (WPF)** | GPU-accelerated native Windows UI via named pipes | Native perf | `native/csharp/` |

All native modules have **Python fallbacks** — Monica works without compiling any of them.

---

## 1. C++ Vision Accelerator

### Prerequisites
- Visual Studio 2022 (or Build Tools) with C++ workload
- Python 3.10+ with `pybind11` installed

### Build
```powershell
cd native/cpp
pip install pybind11
python setup.py build_ext --inplace
# Copy the .pyd file to the project root or site-packages
copy build\lib.*\monica_vision_accel*.pyd ..\..\
```

### CMake alternative
```powershell
cd native/cpp
mkdir build && cd build
cmake .. -G "Visual Studio 17 2022"
cmake --build . --config Release
```

### Functions provided
- `composite_overlay(base, overlay, x, y)` — Alpha-blend BGRA overlay onto BGR frame
- `fast_resize(src, dst_h, dst_w)` — Bilinear resize
- `swap_channels(frame)` — BGR↔RGB in-place (no copy)
- `draw_hand_skeleton(frame, landmarks, ...)` — Full 21-landmark hand skeleton in one call
- `globe_project(lat, lng, ...)` — Lat/lng to screen coordinates
- `render_globe(texture, dst, ...)` — Textured globe rendering
- `draw_globe_dot(frame, lat, lng, ...)` — Pulsating dot on globe

---

## 2. Rust Audio Accelerator

### Prerequisites
- [Rust toolchain](https://rustup.rs/) (stable)
- Python 3.10+ with `maturin` installed

### Build
```powershell
cd native/rust
pip install maturin
maturin develop --release
# This installs monica_audio_accel directly into your Python environment
```

### Functions provided
- `resample(audio, source_rate, target_rate)` — Linear interpolation resampling
- `resample_sinc(audio, source_rate, target_rate)` — Windowed-sinc (high quality)
- `rms_energy(audio)` — RMS energy calculation
- `peak_amplitude(audio)` — Peak amplitude
- `normalize(audio, target_db)` — Normalize to target level
- `compress(audio, threshold_db, ratio, ...)` — Dynamic range compression
- `mix(a, b, gain_a, gain_b)` — Mix two audio buffers
- `pcm16_to_float(audio)` / `float_to_pcm16(audio)` — Format conversion
- `AudioRingBuffer(capacity)` — Thread-safe ring buffer for TTS playback

---

## 3. TypeScript/React Web UI

### Prerequisites
- [Node.js 18+](https://nodejs.org/) with npm
- Python with `fastapi` and `uvicorn` installed

### Setup
```powershell
# Frontend
cd web/frontend
npm install
npm run dev          # Development server on http://localhost:3000

# Backend (WebSocket server)
pip install fastapi uvicorn
cd web/backend
uvicorn websocket_server:app --host 0.0.0.0 --port 8765
```

### Production build
```powershell
cd web/frontend
npm run build        # Outputs to web/frontend/dist/
# FastAPI automatically serves the built frontend
```

### Features
- Live video streaming via WebSocket (JPEG frames)
- Real-time chat with auto-scroll
- Service status indicators
- Mic level visualization
- Camera/Globe/Voice toggle controls
- Dark sci-fi theme matching Monica's aesthetic

---

## 4. C# WPF Frontend

### Prerequisites
- [.NET 8 SDK](https://dotnet.microsoft.com/download/dotnet/8.0)
- Visual Studio 2022 (optional, for XAML designer)

### Build & Run
```powershell
cd native/csharp
dotnet build
dotnet run --project MonicaWPF
```

### Connection
The WPF frontend communicates with Python via **named pipes**:
- `MonicaAIPipe_in` — WPF sends commands to Python
- `MonicaAIPipe_out` — Python sends frames/chat/status to WPF

To enable the pipe server in Monica, set in `.env`:
```
MONICA_PIPE_SERVER=1
```

### Features
- GPU-accelerated video display via `WriteableBitmap`
- Dark theme matching Monica's visual identity
- Full chat interface with history
- Service status monitoring
- Camera, Globe, Voice, Spout controls

---

## Python Fallback Wrappers

Even without compiling any native module, Monica works via pure-Python fallbacks:

```python
# Vision (auto-detects C++ module)
from vision.native_accel import accel
accel.draw_hand_skeleton(frame, landmarks)  # Uses C++ if compiled, else cv2

# Audio (auto-detects Rust module)
from audio.native_audio import audio_accel
resampled = audio_accel.resample(samples, 44100, 16000)  # Uses Rust if compiled, else NumPy
```

Check which backend is active:
```python
print(f"Vision: {'C++' if accel.is_native else 'Python'}")
print(f"Audio: {'Rust' if audio_accel.is_native else 'Python'}")
```
