"""
Monica AI Named Pipe Server — bridges Python backend to C# WPF frontend.

Creates two named pipes:
    MonicaAIPipe_in  — receives commands FROM the WPF frontend
    MonicaAIPipe_out — sends frames/chat/status TO the WPF frontend

Protocol: JSON lines (newline-delimited JSON).

Usage:
    Launched automatically when MONICA_PIPE_SERVER=1 in .env
    Or: python -m services.pipe_server
"""
import json
import time
import base64
import threading
import logging
import os
from typing import Optional, Any

logger = logging.getLogger("Monica.PipeServer")

# Windows named pipes
HAS_WIN32 = False
try:
    import win32pipe
    import win32file
    import pywintypes
    HAS_WIN32 = True
except ImportError:
    logger.info("[PipeServer] pywin32 not installed — pipe server disabled")
    logger.info("[PipeServer] Install with: pip install pywin32")

try:
    import cv2
    import numpy as np
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

PIPE_NAME_IN = r"\\.\pipe\MonicaAIPipe_in"
PIPE_NAME_OUT = r"\\.\pipe\MonicaAIPipe_out"
BUFFER_SIZE = 1024 * 1024  # 1MB buffer for JPEG frames


class MonicaPipeServer:
    """
    Named pipe server for C# WPF frontend communication.
    
    Runs two pipe threads:
      - Output pipe: streams video frames, chat messages, status to WPF
      - Input pipe: receives commands, chat input from WPF
    """

    def __init__(self):
        self.orchestrator = None
        self.is_running = False
        self._pipe_out_handle = None
        self._pipe_in_handle = None
        self._client_connected = False
        self._stop_event = threading.Event()

        # Frame streaming
        self._last_frame_time = 0.0
        self._frame_interval = 1.0 / 30  # 30fps target
        self._jpeg_quality = 65

        # Queued messages to send
        self._send_queue: list = []
        self._send_lock = threading.Lock()

        logger.info("[PipeServer] Created (waiting for WPF client)")

    def set_orchestrator(self, orchestrator):
        self.orchestrator = orchestrator

    def start(self):
        """Start the pipe server in background threads."""
        if not HAS_WIN32:
            logger.warning("[PipeServer] pywin32 not available — cannot start pipe server")
            return

        self.is_running = True
        self._stop_event.clear()

        threading.Thread(target=self._output_pipe_thread, daemon=True,
                         name="PipeServer-Out").start()
        threading.Thread(target=self._input_pipe_thread, daemon=True,
                         name="PipeServer-In").start()

        logger.info("[PipeServer] Pipe server started — waiting for WPF client connection")

    def stop(self):
        self.is_running = False
        self._stop_event.set()
        self._client_connected = False

        # Close pipe handles
        for handle in [self._pipe_out_handle, self._pipe_in_handle]:
            if handle:
                try:
                    win32file.CloseHandle(handle)
                except Exception:
                    pass

        logger.info("[PipeServer] Stopped")

    # ── Output pipe: send data TO WPF ──

    def _output_pipe_thread(self):
        """Create output named pipe and stream data to WPF client."""
        while self.is_running and not self._stop_event.is_set():
            try:
                # Create pipe (server side)
                self._pipe_out_handle = win32pipe.CreateNamedPipe(
                    PIPE_NAME_OUT,
                    win32pipe.PIPE_ACCESS_OUTBOUND,
                    win32pipe.PIPE_TYPE_BYTE | win32pipe.PIPE_READMODE_BYTE | win32pipe.PIPE_WAIT,
                    1,  # max instances
                    BUFFER_SIZE,
                    BUFFER_SIZE,
                    0,  # default timeout
                    None  # security attributes
                )

                logger.info("[PipeServer] Output pipe created, waiting for WPF client...")

                # Block until client connects
                win32pipe.ConnectNamedPipe(self._pipe_out_handle, None)
                self._client_connected = True
                logger.info("[PipeServer] WPF client connected (output pipe)")

                # Stream loop
                while self.is_running and not self._stop_event.is_set():
                    try:
                        # Send video frame
                        self._send_frame()

                        # Send queued messages (chat, status)
                        self._flush_queue()

                        # Send status update every second
                        self._send_status()

                        time.sleep(0.016)  # ~60Hz check rate

                    except pywintypes.error as e:
                        if e.args[0] == 232:  # ERROR_NO_DATA (pipe closed)
                            break
                        raise

            except pywintypes.error as e:
                logger.debug(f"[PipeServer] Output pipe error: {e}")
            except Exception as e:
                logger.debug(f"[PipeServer] Output pipe error: {e}")
            finally:
                self._client_connected = False
                if self._pipe_out_handle:
                    try:
                        win32pipe.DisconnectNamedPipe(self._pipe_out_handle)
                        win32file.CloseHandle(self._pipe_out_handle)
                    except Exception:
                        pass
                    self._pipe_out_handle = None

                if self.is_running:
                    logger.info("[PipeServer] WPF client disconnected, waiting for reconnect...")
                    time.sleep(1.0)

    def _send_frame(self):
        """Send current video frame as base64 JPEG."""
        if not self.orchestrator or not self._client_connected:
            return

        now = time.time()
        if now - self._last_frame_time < self._frame_interval:
            return

        frame = self.orchestrator.get_shared('vision_frame')
        if frame is None or not HAS_CV2:
            return

        self._last_frame_time = now

        try:
            _, jpeg = cv2.imencode('.jpg', frame,
                                    [cv2.IMWRITE_JPEG_QUALITY, self._jpeg_quality])
            b64 = base64.b64encode(jpeg.tobytes()).decode('ascii')

            msg = json.dumps({"type": "frame", "data": b64}) + "\n"
            win32file.WriteFile(self._pipe_out_handle, msg.encode('utf-8'))
        except Exception:
            pass

    def _send_status(self):
        """Send system status update."""
        if not self.orchestrator or not self._client_connected:
            return

        # Only send once per second
        now = time.time()
        if not hasattr(self, '_last_status_time'):
            self._last_status_time = 0.0
        if now - self._last_status_time < 1.0:
            return
        self._last_status_time = now

        status = {"type": "status", "services": {}}

        for name in ['stt', 'tts', 'ai', 'vision']:
            svc = self.orchestrator.get_service(name)
            status["services"][name] = "active" if svc else "offline"

        vr = self.orchestrator.get_shared('vision_result')
        if vr:
            status["emotion"] = getattr(vr, 'emotion', '')

        status["mic_energy"] = self.orchestrator.get_shared('mic_energy', 0.0)

        try:
            msg = json.dumps(status) + "\n"
            win32file.WriteFile(self._pipe_out_handle, msg.encode('utf-8'))
        except Exception:
            pass

    def _flush_queue(self):
        """Send queued messages to WPF client."""
        if not self._client_connected:
            return

        with self._send_lock:
            queue = self._send_queue.copy()
            self._send_queue.clear()

        for msg_dict in queue:
            try:
                msg = json.dumps(msg_dict) + "\n"
                win32file.WriteFile(self._pipe_out_handle, msg.encode('utf-8'))
            except Exception:
                break

    # ── Input pipe: receive commands FROM WPF ──

    def _input_pipe_thread(self):
        """Create input named pipe and receive commands from WPF client."""
        while self.is_running and not self._stop_event.is_set():
            try:
                self._pipe_in_handle = win32pipe.CreateNamedPipe(
                    PIPE_NAME_IN,
                    win32pipe.PIPE_ACCESS_INBOUND,
                    win32pipe.PIPE_TYPE_BYTE | win32pipe.PIPE_READMODE_BYTE | win32pipe.PIPE_WAIT,
                    1,
                    BUFFER_SIZE,
                    BUFFER_SIZE,
                    0,
                    None
                )

                logger.info("[PipeServer] Input pipe created, waiting for WPF client...")
                win32pipe.ConnectNamedPipe(self._pipe_in_handle, None)
                logger.info("[PipeServer] WPF client connected (input pipe)")

                buffer = ""
                while self.is_running and not self._stop_event.is_set():
                    try:
                        hr, data = win32file.ReadFile(self._pipe_in_handle, 65536)
                        if hr != 0:
                            break
                        buffer += data.decode('utf-8')

                        # Process complete JSON lines
                        while "\n" in buffer:
                            line, buffer = buffer.split("\n", 1)
                            line = line.strip()
                            if line:
                                try:
                                    msg = json.loads(line)
                                    self._handle_command(msg)
                                except json.JSONDecodeError:
                                    pass

                    except pywintypes.error as e:
                        if e.args[0] in (109, 232):  # Broken pipe / no data
                            break
                        raise

            except pywintypes.error:
                pass
            except Exception as e:
                logger.debug(f"[PipeServer] Input pipe error: {e}")
            finally:
                if self._pipe_in_handle:
                    try:
                        win32pipe.DisconnectNamedPipe(self._pipe_in_handle)
                        win32file.CloseHandle(self._pipe_in_handle)
                    except Exception:
                        pass
                    self._pipe_in_handle = None

                if self.is_running:
                    time.sleep(1.0)

    def _handle_command(self, msg: dict):
        """Process a command received from the WPF frontend."""
        msg_type = msg.get('type', '')

        if msg_type == 'command':
            cmd = msg.get('command', '')
            self._dispatch_command(cmd, msg)

        elif msg_type == 'chat':
            text = msg.get('text', '').strip()
            if text and self.orchestrator:
                # Forward to AI service
                ai = self.orchestrator.get_service('ai')
                if ai:
                    ai.ask(text)

                # Echo user message to pipe output
                self.push_chat("user", text)

    def _dispatch_command(self, cmd: str, msg: dict):
        """Dispatch a control command."""
        if not self.orchestrator:
            return

        if cmd == 'camera_on':
            vision = self.orchestrator.get_service('vision')
            if vision:
                vision.start_camera()

        elif cmd == 'camera_off':
            vision = self.orchestrator.get_service('vision')
            if vision:
                vision.stop_camera()

        elif cmd == 'toggle_globe':
            vision = self.orchestrator.get_service('vision')
            if vision:
                vision.globe_enabled = not vision.globe_enabled

        elif cmd == 'initialize':
            ai = self.orchestrator.get_service('ai')
            if ai:
                ai.initialize_conversation()

        elif cmd == 'stop_speaking':
            tts = self.orchestrator.get_service('tts')
            if tts:
                tts.stop_speaking()

        elif cmd == 'set_stt_mode':
            mode = msg.get('mode', 'hands_free')
            stt = self.orchestrator.get_service('stt')
            if stt:
                if mode == 'off':
                    stt.pause()
                else:
                    stt.resume()

        elif cmd == 'toggle_spout':
            vision = self.orchestrator.get_service('vision')
            if vision and hasattr(vision, 'camera_manager'):
                cm = vision.camera_manager
                if cm:
                    cm.spout_enabled = not getattr(cm, 'spout_enabled', False)

    # ── Public API for Python backend ──

    def push_chat(self, role: str, text: str):
        """Queue a chat message to send to WPF client."""
        with self._send_lock:
            self._send_queue.append({
                "type": "chat",
                "role": role,
                "text": text,
            })

    @property
    def client_connected(self) -> bool:
        return self._client_connected


# Singleton
_pipe_server: Optional[MonicaPipeServer] = None


def get_pipe_server() -> MonicaPipeServer:
    global _pipe_server
    if _pipe_server is None:
        _pipe_server = MonicaPipeServer()
    return _pipe_server
