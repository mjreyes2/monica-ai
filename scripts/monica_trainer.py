#!/usr/bin/env python3
"""
Monica Trainer — Single Launcher GUI
=====================================
One GUI to manage all STT and TTS training.

Tabs:
  1. STT Training  — scan recordings → prepare dataset → train Wav2Vec2
  2. TTS Training  — verify LJSpeech  → choose method  → train XTTS
  3. Profile       — view Monica's remembered user profile

Safety guarantees:
  - STT and TTS are fully isolated channels.
  - Buttons on one channel are DISABLED while the other is actively training.
  - Each channel has its own scrolled log, progress bar, and status label.
  - No script called by STT can touch TTS model dirs, and vice versa.

Launch:
    python scripts/monica_trainer.py
"""

from __future__ import annotations

import base64
import json
import os
import re
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Any

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinter.scrolledtext import ScrolledText

# ── Project paths ──────────────────────────────────────────────────────────────
PROJECT_ROOT   = Path(__file__).resolve().parent.parent

# STT paths
STT_WAKE_DIR   = PROJECT_ROOT / "data" / "training" / "recordings" / "wake_phrases"
STT_PHRASE_DIR = PROJECT_ROOT / "data" / "training" / "recordings" / "training_phrases"
STT_DATASET    = PROJECT_ROOT / "data" / "training" / "datasets" / "stt_combined"
STT_MODEL_DIR  = PROJECT_ROOT / "models" / "wav2vec2_your_voice"
STT_PREP_SCRIPT  = PROJECT_ROOT / "scripts" / "prepare_all_training_data.py"
STT_CSV_SCRIPT   = PROJECT_ROOT / "scripts" / "create_training_csvs.py"
STT_TRAIN_SCRIPT = PROJECT_ROOT / "scripts" / "continue_training.py"
STT_STATE_FILE   = STT_DATASET / "training_hub_state.json"

# TTS paths
TTS_ROOT       = PROJECT_ROOT / "data" / "training" / "monica_tts_training"
TTS_LJSPEECH   = TTS_ROOT / "datasets" / "LJSpeech-1.1"
TTS_MODEL_DIR  = TTS_ROOT / "models"
TTS_XTTS_SCRIPT      = PROJECT_ROOT / "src" / "models" / "train_xtts_feminine_official.py"
TTS_ACCENT_SCRIPT    = PROJECT_ROOT / "src" / "models" / "train_accent_tune_feminine.py"
TTS_LAUNCH_SCRIPT    = TTS_ROOT / "launch_tts_training.py"

# Profile path
PROFILE_FILE   = PROJECT_ROOT / "data" / "user_profile" / "user_profile.json"

# Filename patterns expected by the STT pipeline
WAKE_PATTERN   = re.compile(r"^phrase_\d{5}_[a-z0-9_]+\.wav$")
PHRASE_PATTERN = re.compile(r"^\d{4}_[a-z0-9_]+\.wav$")

# ── Colour palette ─────────────────────────────────────────────────────────────
C_STT_ACCENT  = "#1a73e8"   # Google-blue  — STT
C_TTS_ACCENT  = "#7c3aed"   # Purple       — TTS
C_OK          = "#16a34a"   # Green
C_WARN        = "#d97706"   # Amber
C_ERR         = "#dc2626"   # Red
C_BG          = "#f8fafc"
C_LOG_BG      = "#111827"
C_LOG_FG      = "#e5e7eb"


@dataclass
class InvalidFile:
    path: Path
    suggestion: str
    reason: str


# ── Utility: threaded subprocess runner ───────────────────────────────────────
class ChannelRunner:
    """Runs a subprocess in a background thread and pipes output to a ScrolledText log."""

    def __init__(
        self,
        log: ScrolledText,
        progress_bar: ttk.Progressbar,
        progress_label: tk.StringVar,
        status_label: tk.StringVar,
        on_start,
        on_finish,
    ):
        self.log = log
        self.progress_bar = progress_bar
        self.progress_label = progress_label
        self.status_label = status_label
        self.on_start = on_start
        self.on_finish = on_finish
        self._proc: Optional[subprocess.Popen] = None
        self.running = False

    def run(self, cmd: List[str], cwd: Optional[Path] = None, label: str = "") -> None:
        if self.running:
            self._log("⚠ Already running — wait for current task to finish.")
            return
        self.running = True
        self.on_start()
        self._reset_progress()
        self.status_label.set(f"⏳ {label}")
        threading.Thread(target=self._worker, args=(cmd, cwd, label), daemon=True).start()

    def run_sequence(self, steps: List[tuple], cwd: Optional[Path] = None) -> None:
        """Run multiple commands sequentially, stopping on error."""
        if self.running:
            self._log("⚠ Already running — wait for current task to finish.")
            return
        self.running = True
        self.on_start()
        self._reset_progress()
        threading.Thread(target=self._sequence_worker, args=(steps, cwd), daemon=True).start()

    def _sequence_worker(self, steps: List[tuple], cwd: Optional[Path]) -> None:
        total = len(steps)
        for idx, (cmd, label) in enumerate(steps):
            self.status_label.set(f"⏳ Step {idx+1}/{total}: {label}")
            self._log(f"\n{'='*60}\n[STEP {idx+1}/{total}] {label}\n{'='*60}")
            ok = self._run_one(cmd, cwd)
            if not ok:
                self.status_label.set(f"❌ Failed at: {label}")
                self._log(f"\n❌ STEP FAILED: {label}\nStopping sequence.")
                self.running = False
                self.on_finish(success=False)
                return
        self.status_label.set("✅ All steps complete")
        self._log("\n✅ All steps completed successfully.")
        self.progress_bar["value"] = 100
        self.progress_label.set("100%")
        self.running = False
        self.on_finish(success=True)

    def _worker(self, cmd: List[str], cwd: Optional[Path], label: str) -> None:
        ok = self._run_one(cmd, cwd)
        if ok:
            self.status_label.set(f"✅ Done: {label}")
            self._log(f"\n✅ {label} — complete.")
            self.progress_bar["value"] = 100
            self.progress_label.set("100%")
        else:
            self.status_label.set(f"❌ Failed: {label}")
        self.running = False
        self.on_finish(success=ok)

    def _run_one(self, cmd: List[str], cwd: Optional[Path]) -> bool:
        self._log(">> " + " ".join(str(c) for c in cmd))
        try:
            self._proc = subprocess.Popen(
                cmd,
                cwd=str(cwd or PROJECT_ROOT),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            assert self._proc.stdout
            for line in self._proc.stdout:
                stripped = line.rstrip()
                self._log(stripped)
                self._parse_progress(stripped)
            code = self._proc.wait()
            self._log(f"[exit {code}]")
            return code == 0
        except Exception as e:
            self._log(f"[ERROR] {e}")
            return False

    def kill(self) -> None:
        if self._proc and self._proc.poll() is None:
            self._proc.terminate()
            self._log("⚠ Process terminated by user.")
        self.running = False

    def _reset_progress(self) -> None:
        self.progress_bar["value"] = 0
        self.progress_label.set("0%")

    def _parse_progress(self, line: str) -> None:
        # HuggingFace Trainer: "{'loss': 0.42, 'epoch': 3.5}"  or "Epoch: 3/50"
        m = re.search(r"epoch[\"']?\s*[:]\s*([\d.]+)[/,]?\s*(\d*)", line, re.I)
        if m:
            curr = float(m.group(1))
            total_str = m.group(2)
            if total_str and int(total_str) > 0:
                pct = min(100, int((curr / int(total_str)) * 100))
                self.progress_bar["value"] = pct
                self.progress_label.set(f"{pct}%")
                return

        # Generic [n/total]
        m = re.search(r"\[(\d+)/(\d+)\]", line)
        if m:
            curr, total = int(m.group(1)), int(m.group(2))
            if total > 0:
                pct = min(100, int(curr / total * 100))
                self.progress_bar["value"] = pct
                self.progress_label.set(f"{pct}%")
                return

        # Nudge bar forward on any training heartbeat
        if any(k in line.lower() for k in ("loss:", "wer:", "cer:", "step:", "eval_")):
            cur = self.progress_bar["value"]
            if cur < 95:
                self.progress_bar["value"] = cur + 1
                self.progress_label.set(f"{int(cur + 1)}%")

    def _log(self, msg: str) -> None:
        try:
            self.log.insert(tk.END, msg + "\n")
            self.log.see(tk.END)
        except Exception:
            pass


# ── Main Application ───────────────────────────────────────────────────────────
class MonicaTrainer:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Monica Trainer")
        self.root.geometry("1150x820")
        self.root.configure(bg=C_BG)

        self._stt_state: Dict = self._load_stt_state()
        self._invalid_files: List[InvalidFile] = []

        self._build_ui()

        # Auto-scan on startup
        self.root.after(300, self._stt_scan)
        self.root.after(400, self._tts_check)

    # ── Layout ─────────────────────────────────────────────────────────────────
    def _build_ui(self) -> None:
        # Top banner
        banner = tk.Frame(self.root, bg=C_LOG_BG, height=48)
        banner.pack(fill=tk.X)
        tk.Label(
            banner, text="🤖  Monica Trainer", font=("Segoe UI", 16, "bold"),
            bg=C_LOG_BG, fg="white"
        ).pack(side=tk.LEFT, padx=16, pady=8)
        self._global_status = tk.StringVar(value="Ready")
        tk.Label(
            banner, textvariable=self._global_status,
            font=("Segoe UI", 10), bg=C_LOG_BG, fg="#9ca3af"
        ).pack(side=tk.RIGHT, padx=16, pady=8)

        self.nb = ttk.Notebook(self.root)
        self.nb.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        self._build_stt_tab()
        self._build_tts_tab()
        self._build_profile_tab()

    # ── STT Tab ────────────────────────────────────────────────────────────────
    def _build_stt_tab(self) -> None:
        frame = ttk.Frame(self.nb)
        self.nb.add(frame, text="🎙  STT Training")

        # Header
        hdr = tk.Frame(frame, bg=C_STT_ACCENT)
        hdr.pack(fill=tk.X)
        tk.Label(
            hdr, text="Speech-to-Text Training Channel",
            font=("Segoe UI", 11, "bold"), bg=C_STT_ACCENT, fg="white", pady=6
        ).pack(side=tk.LEFT, padx=10)
        self._stt_status_var = tk.StringVar(value="Idle")
        tk.Label(
            hdr, textvariable=self._stt_status_var,
            font=("Segoe UI", 9), bg=C_STT_ACCENT, fg="#bfdbfe", pady=6
        ).pack(side=tk.RIGHT, padx=10)

        # Stats row
        stats = ttk.LabelFrame(frame, text="Recording Folders", padding=8)
        stats.pack(fill=tk.X, padx=8, pady=4)
        self._wake_var   = tk.StringVar(value="Wake phrases: –")
        self._phrase_var = tk.StringVar(value="Training phrases: –")
        self._new_var    = tk.StringVar(value="New since baseline: –")
        for var in (self._wake_var, self._phrase_var, self._new_var):
            tk.Label(stats, textvariable=var, font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=12)

        ttk.Button(stats, text="🔄 Refresh", command=self._stt_scan).pack(side=tk.RIGHT, padx=4)
        ttk.Button(stats, text="📁 Open Folders", command=self._stt_open_folders).pack(side=tk.RIGHT, padx=4)
        ttk.Button(stats, text="📌 Mark Baseline", command=self._stt_mark_baseline).pack(side=tk.RIGHT, padx=4)

        # Invalid files
        inv_frame = ttk.LabelFrame(frame, text="⚠ Files With Non-Standard Names (must fix before training)", padding=6)
        inv_frame.pack(fill=tk.X, padx=8, pady=2)
        self._invalid_list = tk.Listbox(inv_frame, height=4, font=("Consolas", 8))
        self._invalid_list.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        ttk.Button(inv_frame, text="Auto-Rename All", command=self._stt_auto_rename).pack(side=tk.RIGHT, padx=4, pady=4)

        # Action buttons
        actions = ttk.LabelFrame(frame, text="Training Actions — run in order", padding=8)
        actions.pack(fill=tk.X, padx=8, pady=4)

        self._stt_btn_prep  = ttk.Button(actions, text="1️⃣  Prepare Dataset",      command=self._stt_prepare)
        self._stt_btn_csv   = ttk.Button(actions, text="2️⃣  Build CSV Manifests",  command=self._stt_csvs)
        self._stt_btn_train = ttk.Button(actions, text="3️⃣  Continue STT Training", command=self._stt_train)
        self._stt_btn_all   = ttk.Button(actions, text="🚀 Run Full Pipeline (1→2→3)", command=self._stt_full_pipeline)
        self._stt_btn_stop  = ttk.Button(actions, text="⛔ Stop", command=self._stt_stop, state=tk.DISABLED)

        for col, btn in enumerate([
            self._stt_btn_prep, self._stt_btn_csv,
            self._stt_btn_train, self._stt_btn_all, self._stt_btn_stop
        ]):
            btn.grid(row=0, column=col, padx=5, pady=4)

        # Progress
        prog_frame = ttk.Frame(frame)
        prog_frame.pack(fill=tk.X, padx=8, pady=2)
        tk.Label(prog_frame, text="Progress:", font=("Segoe UI", 9)).pack(side=tk.LEFT)
        self._stt_pbar = ttk.Progressbar(prog_frame, length=400, mode="determinate", maximum=100)
        self._stt_pbar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6)
        self._stt_pbar_var = tk.StringVar(value="0%")
        tk.Label(prog_frame, textvariable=self._stt_pbar_var, width=6, font=("Segoe UI", 9)).pack(side=tk.LEFT)

        # Log
        log_frame = ttk.LabelFrame(frame, text="STT Log", padding=4)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
        self._stt_log = ScrolledText(log_frame, wrap=tk.WORD, bg=C_LOG_BG, fg=C_LOG_FG,
                                     font=("Consolas", 8), height=12)
        self._stt_log.pack(fill=tk.BOTH, expand=True)

        # Wire up runner
        self._stt_runner = ChannelRunner(
            log=self._stt_log,
            progress_bar=self._stt_pbar,
            progress_label=self._stt_pbar_var,
            status_label=self._stt_status_var,
            on_start=self._on_stt_start,
            on_finish=self._on_stt_finish,
        )
        self._stt_log_msg("STT channel ready.")
        self._stt_log_msg(f"Python: {sys.executable}")
        self._stt_log_msg(f"Project root: {PROJECT_ROOT}")

    # ── TTS Tab ────────────────────────────────────────────────────────────────
    def _build_tts_tab(self) -> None:
        frame = ttk.Frame(self.nb)
        self.nb.add(frame, text="🔊  TTS Training")

        # Header
        hdr = tk.Frame(frame, bg=C_TTS_ACCENT)
        hdr.pack(fill=tk.X)
        tk.Label(
            hdr, text="Text-to-Speech Training Channel",
            font=("Segoe UI", 11, "bold"), bg=C_TTS_ACCENT, fg="white", pady=6
        ).pack(side=tk.LEFT, padx=10)
        self._tts_status_var = tk.StringVar(value="Idle")
        tk.Label(
            hdr, textvariable=self._tts_status_var,
            font=("Segoe UI", 9), bg=C_TTS_ACCENT, fg="#e9d5ff", pady=6
        ).pack(side=tk.RIGHT, padx=10)

        # Dataset status
        ds_frame = ttk.LabelFrame(frame, text="Dataset Status", padding=8)
        ds_frame.pack(fill=tk.X, padx=8, pady=4)
        self._tts_ljs_var = tk.StringVar(value="LJSpeech: checking…")
        tk.Label(ds_frame, textvariable=self._tts_ljs_var, font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=8)
        ttk.Button(ds_frame, text="🔄 Check", command=self._tts_check).pack(side=tk.RIGHT, padx=4)
        ttk.Button(ds_frame, text="📁 Open TTS Folder", command=self._tts_open_folder).pack(side=tk.RIGHT, padx=4)

        # Method selector
        method_frame = ttk.LabelFrame(frame, text="Training Method", padding=8)
        method_frame.pack(fill=tk.X, padx=8, pady=4)
        self._tts_method = tk.StringVar(value="xtts_official")
        methods = [
            ("XTTS v2 Official  (best quality, ~4–8 h)",   "xtts_official"),
            ("AccentTune  (faster, ~30–60 min)",            "accent_tune"),
            ("launch_tts_training.py  (project default)",   "launch_script"),
        ]
        for label, val in methods:
            ttk.Radiobutton(
                method_frame, text=label, variable=self._tts_method, value=val
            ).pack(anchor=tk.W, padx=8, pady=2)

        # Action buttons
        actions = ttk.LabelFrame(frame, text="Training Actions", padding=8)
        actions.pack(fill=tk.X, padx=8, pady=4)

        self._tts_btn_train = ttk.Button(actions, text="🚀 Start TTS Training", command=self._tts_train)
        self._tts_btn_stop  = ttk.Button(actions, text="⛔ Stop",              command=self._tts_stop, state=tk.DISABLED)

        self._tts_btn_train.grid(row=0, column=0, padx=6, pady=4)
        self._tts_btn_stop.grid(row=0, column=1, padx=6, pady=4)

        # ⚠ Isolation notice
        notice = tk.Label(
            actions,
            text="⚠  TTS training only reads/writes TTS model directories and is isolated from STT.",
            font=("Segoe UI", 8), fg=C_WARN
        )
        notice.grid(row=0, column=2, padx=10)

        # Progress
        prog_frame = ttk.Frame(frame)
        prog_frame.pack(fill=tk.X, padx=8, pady=2)
        tk.Label(prog_frame, text="Progress:", font=("Segoe UI", 9)).pack(side=tk.LEFT)
        self._tts_pbar = ttk.Progressbar(prog_frame, length=400, mode="determinate", maximum=100)
        self._tts_pbar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6)
        self._tts_pbar_var = tk.StringVar(value="0%")
        tk.Label(prog_frame, textvariable=self._tts_pbar_var, width=6, font=("Segoe UI", 9)).pack(side=tk.LEFT)

        # Log
        log_frame = ttk.LabelFrame(frame, text="TTS Log", padding=4)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
        self._tts_log = ScrolledText(log_frame, wrap=tk.WORD, bg=C_LOG_BG, fg=C_LOG_FG,
                                     font=("Consolas", 8), height=14)
        self._tts_log.pack(fill=tk.BOTH, expand=True)

        # Wire up runner
        self._tts_runner = ChannelRunner(
            log=self._tts_log,
            progress_bar=self._tts_pbar,
            progress_label=self._tts_pbar_var,
            status_label=self._tts_status_var,
            on_start=self._on_tts_start,
            on_finish=self._on_tts_finish,
        )
        self._tts_log_msg("TTS channel ready.")
        self._tts_log_msg(f"TTS training root: {TTS_ROOT}")

    # ── Profile Tab ────────────────────────────────────────────────────────────
    def _build_profile_tab(self) -> None:
        frame = ttk.Frame(self.nb)
        self.nb.add(frame, text="👤  Profile")

        ctrl = ttk.Frame(frame, padding=8)
        ctrl.pack(fill=tk.X)
        ttk.Button(ctrl, text="🔄 Refresh", command=self._profile_refresh).pack(side=tk.LEFT, padx=4)
        ttk.Button(ctrl, text="💾 Export JSON", command=self._profile_export).pack(side=tk.LEFT, padx=4)
        self._profile_status = tk.StringVar(value="Click Refresh to load.")
        tk.Label(ctrl, textvariable=self._profile_status, font=("Segoe UI", 9), fg="blue").pack(side=tk.LEFT, padx=10)

        pf = ttk.LabelFrame(frame, text="Monica's Remembered Profile", padding=6)
        pf.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
        self._profile_text = ScrolledText(pf, wrap=tk.WORD, font=("Consolas", 9), height=25)
        self._profile_text.pack(fill=tk.BOTH, expand=True)

    # ── STT Actions ───────────────────────────────────────────────────────────
    def _stt_scan(self) -> None:
        wake_wavs   = list(STT_WAKE_DIR.glob("*.wav"))   if STT_WAKE_DIR.exists()   else []
        phrase_wavs = list(STT_PHRASE_DIR.glob("*.wav")) if STT_PHRASE_DIR.exists() else []
        all_wavs    = wake_wavs + phrase_wavs

        known = self._stt_state.get("known", {})
        new_files = [p for p in all_wavs
                     if str(p) not in known or known[str(p)] != p.stat().st_mtime]

        self._invalid_files = self._collect_invalid(wake_wavs, phrase_wavs)
        self._invalid_list.delete(0, tk.END)
        for item in self._invalid_files:
            self._invalid_list.insert(tk.END,
                f"{item.path.name}  →  {item.suggestion}   [{item.reason}]")

        self._wake_var.set(f"Wake phrases: {len(wake_wavs)} WAV files")
        self._phrase_var.set(f"Training phrases: {len(phrase_wavs)} WAV files")
        self._new_var.set(f"New since baseline: {len(new_files)}")
        self._stt_log_msg(
            f"Scan: wake={len(wake_wavs)}, phrases={len(phrase_wavs)}, "
            f"new={len(new_files)}, invalid={len(self._invalid_files)}"
        )

    def _stt_mark_baseline(self) -> None:
        wake_wavs   = list(STT_WAKE_DIR.glob("*.wav"))   if STT_WAKE_DIR.exists()   else []
        phrase_wavs = list(STT_PHRASE_DIR.glob("*.wav")) if STT_PHRASE_DIR.exists() else []
        known: Dict[str, float] = {}
        for p in wake_wavs + phrase_wavs:
            try:
                known[str(p)] = p.stat().st_mtime
            except Exception:
                pass
        self._stt_state["known"] = known
        self._save_stt_state()
        self._stt_log_msg("✅ Baseline updated.")
        self._stt_scan()

    def _stt_auto_rename(self) -> None:
        if not self._invalid_files:
            messagebox.showinfo("Nothing to rename", "All filenames look correct.")
            return
        renamed = 0
        for item in self._invalid_files:
            target = item.path.with_name(item.suggestion)
            try:
                if target.exists():
                    self._stt_log_msg(f"Skip (exists): {target.name}")
                    continue
                item.path.rename(target)
                renamed += 1
                self._stt_log_msg(f"Renamed: {item.path.name} → {target.name}")
            except Exception as e:
                self._stt_log_msg(f"Rename failed for {item.path.name}: {e}")
        self._stt_log_msg(f"Auto-rename done: {renamed} files renamed.")
        self._stt_scan()

    def _stt_open_folders(self) -> None:
        for p in (STT_WAKE_DIR, STT_PHRASE_DIR):
            p.mkdir(parents=True, exist_ok=True)
            try:
                os.startfile(str(p))
            except Exception as e:
                self._stt_log_msg(f"Cannot open {p}: {e}")

    def _stt_prepare(self) -> None:
        if not STT_PREP_SCRIPT.exists():
            messagebox.showerror("Missing Script", f"Not found:\n{STT_PREP_SCRIPT}")
            return
        self._stt_runner.run(
            [sys.executable, str(STT_PREP_SCRIPT)],
            label="Prepare STT Dataset"
        )

    def _stt_csvs(self) -> None:
        if not STT_CSV_SCRIPT.exists():
            messagebox.showerror("Missing Script", f"Not found:\n{STT_CSV_SCRIPT}")
            return
        self._stt_runner.run(
            [sys.executable, str(STT_CSV_SCRIPT)],
            label="Build CSV Manifests"
        )

    def _stt_train(self) -> None:
        if not STT_TRAIN_SCRIPT.exists():
            messagebox.showerror("Missing Script", f"Not found:\n{STT_TRAIN_SCRIPT}")
            return
        if not STT_MODEL_DIR.exists():
            if not messagebox.askyesno(
                "No Checkpoint Found",
                f"No existing model found at:\n{STT_MODEL_DIR}\n\n"
                "You should run steps 1 and 2 first.\n\nContinue anyway?"
            ):
                return
        self._stt_runner.run(
            [sys.executable, str(STT_TRAIN_SCRIPT)],
            label="Continue STT Training"
        )

    def _stt_full_pipeline(self) -> None:
        missing = [s for s in (STT_PREP_SCRIPT, STT_CSV_SCRIPT, STT_TRAIN_SCRIPT) if not s.exists()]
        if missing:
            messagebox.showerror("Missing Scripts", "Cannot find:\n" + "\n".join(str(m) for m in missing))
            return
        self._stt_runner.run_sequence([
            ([sys.executable, str(STT_PREP_SCRIPT)],  "Prepare STT Dataset"),
            ([sys.executable, str(STT_CSV_SCRIPT)],   "Build CSV Manifests"),
            ([sys.executable, str(STT_TRAIN_SCRIPT)], "Continue STT Training"),
        ])

    def _stt_stop(self) -> None:
        self._stt_runner.kill()
        self._stt_status_var.set("⛔ Stopped by user")

    # ── TTS Actions ───────────────────────────────────────────────────────────
    def _tts_check(self) -> None:
        ljs_wavs = TTS_LJSPEECH / "wavs"
        if ljs_wavs.exists():
            n = len(list(ljs_wavs.glob("*.wav")))
            self._tts_ljs_var.set(f"✅ LJSpeech found — {n:,} WAV files at {TTS_LJSPEECH}")
            self._tts_log_msg(f"LJSpeech OK: {n:,} files")
        else:
            self._tts_ljs_var.set(f"❌ LJSpeech NOT found — expected at {TTS_LJSPEECH}")
            self._tts_log_msg(f"WARNING: LJSpeech not found at {TTS_LJSPEECH}")

    def _tts_open_folder(self) -> None:
        TTS_ROOT.mkdir(parents=True, exist_ok=True)
        try:
            os.startfile(str(TTS_ROOT))
        except Exception as e:
            self._tts_log_msg(f"Cannot open folder: {e}")

    def _tts_train(self) -> None:
        method = self._tts_method.get()

        if method == "xtts_official":
            script = TTS_XTTS_SCRIPT
        elif method == "accent_tune":
            script = TTS_ACCENT_SCRIPT
        else:
            script = TTS_LAUNCH_SCRIPT

        if not script.exists():
            messagebox.showerror(
                "Missing Script",
                f"Training script not found:\n{script}\n\n"
                "Please verify your project structure."
            )
            return

        # Final confirmation — prevent accidents
        method_names = {
            "xtts_official": "XTTS v2 Official",
            "accent_tune":   "AccentTune (fast)",
            "launch_script": "launch_tts_training.py",
        }
        if not messagebox.askyesno(
            "Confirm TTS Training",
            f"You are about to start TTS training.\n\n"
            f"Method: {method_names[method]}\n"
            f"Script: {script.name}\n\n"
            f"This will NOT affect your STT model.\n\n"
            f"Start now?"
        ):
            return

        cwd = script.parent if method == "launch_script" else None
        self._tts_runner.run(
            [sys.executable, str(script)],
            cwd=cwd,
            label=f"TTS Training ({method_names[method]})"
        )

    def _tts_stop(self) -> None:
        self._tts_runner.kill()
        self._tts_status_var.set("⛔ Stopped by user")

    # ── Channel lock / unlock ─────────────────────────────────────────────────
    def _on_stt_start(self) -> None:
        """Disable STT action buttons; also disable TTS to prevent cross-training."""
        for btn in (self._stt_btn_prep, self._stt_btn_csv,
                    self._stt_btn_train, self._stt_btn_all):
            btn.config(state=tk.DISABLED)
        self._stt_btn_stop.config(state=tk.NORMAL)
        # Lock TTS while STT is active
        self._tts_btn_train.config(state=tk.DISABLED)
        self._global_status.set("🎙 STT training in progress…")

    def _on_stt_finish(self, success: bool) -> None:
        for btn in (self._stt_btn_prep, self._stt_btn_csv,
                    self._stt_btn_train, self._stt_btn_all):
            btn.config(state=tk.NORMAL)
        self._stt_btn_stop.config(state=tk.DISABLED)
        # Unlock TTS (unless TTS is already running)
        if not self._tts_runner.running:
            self._tts_btn_train.config(state=tk.NORMAL)
        self._global_status.set("✅ STT done" if success else "❌ STT failed — check log")

    def _on_tts_start(self) -> None:
        """Disable TTS action buttons; also disable STT to prevent cross-training."""
        self._tts_btn_train.config(state=tk.DISABLED)
        self._tts_btn_stop.config(state=tk.NORMAL)
        # Lock STT while TTS is active
        for btn in (self._stt_btn_prep, self._stt_btn_csv,
                    self._stt_btn_train, self._stt_btn_all):
            btn.config(state=tk.DISABLED)
        self._global_status.set("🔊 TTS training in progress…")

    def _on_tts_finish(self, success: bool) -> None:
        self._tts_btn_train.config(state=tk.NORMAL)
        self._tts_btn_stop.config(state=tk.DISABLED)
        # Unlock STT (unless STT is already running)
        if not self._stt_runner.running:
            for btn in (self._stt_btn_prep, self._stt_btn_csv,
                        self._stt_btn_train, self._stt_btn_all):
                btn.config(state=tk.NORMAL)
        self._global_status.set("✅ TTS done" if success else "❌ TTS failed — check log")

    # ── Profile ───────────────────────────────────────────────────────────────
    def _profile_refresh(self) -> None:
        self._profile_text.delete("1.0", tk.END)
        if not PROFILE_FILE.exists():
            self._profile_status.set("Profile file not found.")
            self._profile_text.insert(tk.END, f"Expected at:\n{PROFILE_FILE}")
            return
        try:
            data = json.loads(PROFILE_FILE.read_text(encoding="utf-8"))
            if data.get("encrypted"):
                try:
                    sys.path.insert(0, str(PROJECT_ROOT / "src"))
                    from security.hipaa_compliance import EncryptionManager, AuditLogger
                    audit = AuditLogger(PROFILE_FILE.parent)
                    enc   = EncryptionManager(PROFILE_FILE.parent, audit)
                    raw   = enc.decrypt(base64.b64decode(data.get("data", "")))
                    data  = json.loads(raw.decode("utf-8"))
                    self._profile_status.set("✅ Decrypted successfully")
                except Exception as e:
                    self._profile_status.set(f"Decrypt error: {e}")
            else:
                self._profile_status.set("✅ Loaded (not encrypted)")
            self._profile_text.insert(tk.END, json.dumps(data, indent=2, ensure_ascii=False))
        except Exception as e:
            self._profile_status.set(f"Error: {e}")
            self._profile_text.insert(tk.END, str(e))

    def _profile_export(self) -> None:
        path = PROFILE_FILE.parent / "profile_export.json"
        try:
            data = json.loads(PROFILE_FILE.read_text(encoding="utf-8"))
            path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
            messagebox.showinfo("Exported", f"Profile exported to:\n{path}")
        except Exception as e:
            messagebox.showerror("Export Failed", str(e))

    # ── STT filename validation helpers ───────────────────────────────────────
    def _collect_invalid(self, wake_wavs: List[Path], phrase_wavs: List[Path]) -> List[InvalidFile]:
        out: List[InvalidFile] = []

        def next_idx(folder: Path, pat: re.Pattern) -> int:
            mx = 0
            for p in folder.glob("*.wav"):
                m = pat.match(p.name)
                if m:
                    try: mx = max(mx, int(m.group(1)))
                    except Exception: pass
            return mx + 1

        wi = next_idx(STT_WAKE_DIR,   re.compile(r"^phrase_(\d{5})_.*\.wav$"))
        pi = next_idx(STT_PHRASE_DIR, re.compile(r"^(\d{4})_.*\.wav$"))

        def slug(p: Path) -> str:
            s = re.sub(r"[^a-z0-9]+", "_", p.stem.lower()).strip("_")
            return s or "sample"

        for p in wake_wavs:
            if not WAKE_PATTERN.match(p.name):
                out.append(InvalidFile(p, f"phrase_{wi:05d}_{slug(p)}.wav", "wake naming"))
                wi += 1
        for p in phrase_wavs:
            if not PHRASE_PATTERN.match(p.name):
                out.append(InvalidFile(p, f"{pi:04d}_{slug(p)}.wav", "phrase naming"))
                pi += 1
        return out

    # ── STT state persistence ─────────────────────────────────────────────────
    def _load_stt_state(self) -> Dict:
        if STT_STATE_FILE.exists():
            try:
                return json.loads(STT_STATE_FILE.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {"known": {}}

    def _save_stt_state(self) -> None:
        STT_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STT_STATE_FILE.write_text(json.dumps(self._stt_state, indent=2), encoding="utf-8")

    # ── Log helpers ───────────────────────────────────────────────────────────
    def _stt_log_msg(self, msg: str) -> None:
        try:
            self._stt_log.insert(tk.END, msg + "\n")
            self._stt_log.see(tk.END)
        except Exception:
            pass

    def _tts_log_msg(self, msg: str) -> None:
        try:
            self._tts_log.insert(tk.END, msg + "\n")
            self._tts_log.see(tk.END)
        except Exception:
            pass


# ── Entry point ────────────────────────────────────────────────────────────────
def main() -> None:
    if sys.platform == "win32":
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
        os.system("chcp 65001 >nul 2>&1")

    root = tk.Tk()

    # DPI awareness on Windows
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

    app = MonicaTrainer(root)
    root.mainloop()


if __name__ == "__main__":
    main()
