#!/usr/bin/env python3
"""
Monica Training Hub GUI

One place to:
- Scan STT recording folders and count new WAV files
- Validate/auto-fix filename conventions for better training quality
- Run STT data prep and STT continued training
- Launch TTS training
- Inspect and decrypt Monica's remembered profile
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import threading
import base64
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText


PROJECT_ROOT = Path(__file__).resolve().parent.parent

WAKE_DIR = PROJECT_ROOT / "data" / "training" / "recordings" / "wake_phrases"
PHRASE_DIR = PROJECT_ROOT / "data" / "training" / "recordings" / "training_phrases"
STATE_FILE = PROJECT_ROOT / "data" / "training" / "datasets" / "stt_combined" / "training_hub_state.json"

PREP_SCRIPT = PROJECT_ROOT / "scripts" / "prepare_all_training_data.py"
CSV_SCRIPT = PROJECT_ROOT / "scripts" / "create_training_csvs.py"
STT_TRAIN_SCRIPT = PROJECT_ROOT / "scripts" / "continue_training.py"
TTS_LAUNCH_SCRIPT = PROJECT_ROOT / "data" / "training" / "monica_tts_training" / "launch_tts_training.py"

WAKE_PATTERN = re.compile(r"^phrase_\d{5}_[a-z0-9_]+\.wav$")
PHRASE_PATTERN = re.compile(r"^\d{4}_[a-z0-9_]+\.wav$")


@dataclass
class InvalidName:
    path: Path
    suggestion: str
    reason: str


class TrainingHubApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Monica STT/TTS Training Hub + Profile Inspector")
        self.root.geometry("1100x750")

        self.state = self._load_state()
        self.invalid: List[InvalidName] = []

        self._build_ui()
        self.refresh_scan()

    def _build_ui(self) -> None:
        # Create notebook (tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # TAB 1: Training Hub
        self.training_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.training_tab, text="Training Hub")
        self._build_training_tab()

        # TAB 2: Profile Inspector
        self.profile_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.profile_tab, text="Profile Inspector")
        self._build_profile_tab()

    def _build_training_tab(self) -> None:
        top = ttk.Frame(self.training_tab, padding=10)
        top.pack(fill=tk.X)

        self.wake_count_var = tk.StringVar(value="Wake folder: 0 files")
        self.phrase_count_var = tk.StringVar(value="Phrase folder: 0 files")
        self.new_count_var = tk.StringVar(value="New since last baseline: 0")

        ttk.Label(top, textvariable=self.wake_count_var).grid(row=0, column=0, sticky=tk.W, padx=5)
        ttk.Label(top, textvariable=self.phrase_count_var).grid(row=0, column=1, sticky=tk.W, padx=5)
        ttk.Label(top, textvariable=self.new_count_var).grid(row=0, column=2, sticky=tk.W, padx=5)

        controls = ttk.Frame(self.training_tab, padding=10)
        controls.pack(fill=tk.X)

        ttk.Button(controls, text="Refresh Scan", command=self.refresh_scan).grid(row=0, column=0, padx=4, pady=4)
        ttk.Button(controls, text="Mark Current As Baseline", command=self.mark_baseline).grid(row=0, column=1, padx=4, pady=4)
        ttk.Button(controls, text="Auto-Rename Invalid Filenames", command=self.auto_rename_invalid).grid(row=0, column=2, padx=4, pady=4)
        ttk.Button(controls, text="Open Recording Folders", command=self.open_recording_folders).grid(row=0, column=3, padx=4, pady=4)

        train_controls = ttk.Frame(self.training_tab, padding=10)
        train_controls.pack(fill=tk.X)

        ttk.Button(train_controls, text="1) Prepare STT Dataset", command=self.prepare_stt).grid(row=0, column=0, padx=4, pady=4)
        ttk.Button(train_controls, text="2) Continue STT Training", command=self.train_stt).grid(row=0, column=1, padx=4, pady=4)
        ttk.Button(train_controls, text="3) Launch TTS Training", command=self.launch_tts).grid(row=0, column=2, padx=4, pady=4)

        # Progress bars for training
        progress_frame = ttk.LabelFrame(self.training_tab, text="Training Progress", padding=10)
        progress_frame.pack(fill=tk.X, padx=10, pady=6)

        stt_frame = ttk.Frame(progress_frame)
        stt_frame.pack(fill=tk.X, pady=5)
        ttk.Label(stt_frame, text="STT Training:", width=15).pack(side=tk.LEFT)
        self.stt_progress = ttk.Progressbar(stt_frame, length=300, mode="determinate", maximum=100)
        self.stt_progress.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.stt_progress_var = tk.StringVar(value="0%")
        ttk.Label(stt_frame, textvariable=self.stt_progress_var, width=8).pack(side=tk.LEFT)

        tts_frame = ttk.Frame(progress_frame)
        tts_frame.pack(fill=tk.X, pady=5)
        ttk.Label(tts_frame, text="TTS Training:", width=15).pack(side=tk.LEFT)
        self.tts_progress = ttk.Progressbar(tts_frame, length=300, mode="determinate", maximum=100)
        self.tts_progress.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.tts_progress_var = tk.StringVar(value="0%")
        ttk.Label(tts_frame, textvariable=self.tts_progress_var, width=8).pack(side=tk.LEFT)

        list_frame = ttk.LabelFrame(self.training_tab, text="Invalid Filename Review", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=False, padx=10, pady=6)

        self.invalid_list = tk.Listbox(list_frame, height=5)
        self.invalid_list.pack(fill=tk.BOTH, expand=True)

        log_frame = ttk.LabelFrame(self.training_tab, text="Run Log", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=6)

        self.log = ScrolledText(log_frame, wrap=tk.WORD, height=10)
        self.log.pack(fill=tk.BOTH, expand=True)

        self._log("Training Hub ready.")
        self._log(f"Python interpreter: {sys.executable}")

    def _build_profile_tab(self) -> None:
        """Build the Profile Inspector tab to show Monica's memories."""
        top = ttk.Frame(self.profile_tab, padding=10)
        top.pack(fill=tk.X)

        ttk.Button(top, text="Refresh Profile", command=self._refresh_profile).pack(side=tk.LEFT, padx=5)
        ttk.Button(top, text="Export Profile (JSON)", command=self._export_profile).pack(side=tk.LEFT, padx=5)
        
        status_frame = ttk.Frame(self.profile_tab, padding=10)
        status_frame.pack(fill=tk.X)
        self.profile_status_var = tk.StringVar(value="Ready to load profile...")
        ttk.Label(status_frame, textvariable=self.profile_status_var, foreground="blue").pack(side=tk.LEFT)

        # Main profile display
        display_frame = ttk.LabelFrame(self.profile_tab, text="Remembered Profile Data", padding=10)
        display_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=6)

        self.profile_text = ScrolledText(display_frame, wrap=tk.WORD, height=20)
        self.profile_text.pack(fill=tk.BOTH, expand=True)

        # Auto-load profile on tab focus
        self._refresh_profile()

    def _decrypt_profile(self) -> Optional[Dict[str, Any]]:
        """Load and decrypt Monica's user profile."""
        profile_file = PROJECT_ROOT / "data" / "user_profile" / "user_profile.json"
        
        if not profile_file.exists():
            self.profile_status_var.set("ERROR: Profile file not found")
            return None

        try:
            data = json.loads(profile_file.read_text(encoding="utf-8"))
            
            # Check if encrypted
            if data.get("encrypted"):
                # Try to decrypt using the encryption manager
                encrypted_data = data.get("data", "")
                try:
                    # Import encryption manager
                    sys.path.insert(0, str(PROJECT_ROOT / "src"))
                    from security.hipaa_compliance import EncryptionManager, AuditLogger
                    
                    audit = AuditLogger(PROJECT_ROOT / "data" / "user_profile")
                    enc_mgr = EncryptionManager(PROJECT_ROOT / "data" / "user_profile", audit)
                    
                    # Decode from base64 and decrypt
                    encrypted_bytes = base64.b64decode(encrypted_data)
                    decrypted = enc_mgr.decrypt(encrypted_bytes)
                    profile = json.loads(decrypted.decode("utf-8"))
                    self.profile_status_var.set("✓ Profile decrypted successfully")
                    return profile
                except Exception as e:
                    self.profile_status_var.set(f"ERROR decrypting: {str(e)[:60]}")
                    return data.get("plaintext_preview")  # Return plaintext preview if available
            else:
                # Not encrypted, return as-is
                self.profile_status_var.set("✓ Profile loaded (not encrypted)")
                return data
                
        except json.JSONDecodeError as e:
            self.profile_status_var.set(f"ERROR: Invalid JSON - {str(e)[:50]}")
            return None
        except Exception as e:
            self.profile_status_var.set(f"ERROR: {str(e)[:60]}")
            return None

    def _refresh_profile(self) -> None:
        """Refresh the profile display."""
        self.profile_text.delete("1.0", tk.END)
        self.profile_text.insert(tk.END, "Loading profile...\n")
        
        profile = self._decrypt_profile()
        
        if not profile:
            self.profile_text.delete("1.0", tk.END)
            self.profile_text.insert(tk.END, "Could not load profile. Check status message above.")
            return

        self.profile_text.delete("1.0", tk.END)

        # Format profile for display
        display_text = "=" * 70 + "\nMONICA'S REMEMBERED PROFILE\n" + "=" * 70 + "\n\n"

        # Personal Identity
        if "name" in profile or "identity" in profile:
            display_text += "PERSONAL IDENTITY\n" + "-" * 70 + "\n"
            identity = profile.get("identity", {})
            display_text += f"Name: {profile.get('name', identity.get('name', 'Unknown'))}\n"
            display_text += f"Age: {identity.get('age', 'Unknown')}\n"
            display_text += f"Location: {identity.get('location', 'Unknown')}\n"
            display_text += f"Occupation: {identity.get('occupation', 'Unknown')}\n"
            display_text += "\n"

        # Mood History
        if "mood_history" in profile or "mood" in profile:
            display_text += "MOOD TRACKING\n" + "-" * 70 + "\n"
            mood_hist = profile.get("mood_history", [])
            if mood_hist:
                # Show last 10 moods
                recent = mood_hist[-10:] if len(mood_hist) > 10 else mood_hist
                for entry in recent:
                    if isinstance(entry, dict):
                        display_text += f"  {entry.get('timestamp', 'N/A')}: {entry.get('emotion', 'Unknown')}\n"
                    else:
                        display_text += f"  {entry}\n"
            display_text += f"Current typical mood: {profile.get('mood', 'Unknown')}\n"
            display_text += "\n"

        # Relationships
        if "relationships" in profile:
            display_text += "RELATIONSHIPS\n" + "-" * 70 + "\n"
            rels = profile.get("relationships", {})
            for rel_type, people in rels.items():
                if people:
                    display_text += f"{rel_type.upper()}:\n"
                    if isinstance(people, dict):
                        for name, info in people.items():
                            display_text += f"  - {name}\n"
                    elif isinstance(people, list):
                        for person in people:
                            display_text += f"  - {person}\n"
            display_text += "\n"

        # Preferences & Goals
        if "preferences" in profile:
            display_text += "PREFERENCES & INTERESTS\n" + "-" * 70 + "\n"
            prefs = profile.get("preferences", {})
            for key, val in prefs.items():
                if isinstance(val, list) and val:
                    display_text += f"{key}: {', '.join(str(v) for v in val[:10])}\n"
                elif val:
                    display_text += f"{key}: {val}\n"
            display_text += "\n"

        # Topics of Interest
        if "topics" in profile:
            display_text += "TOPICS OF INTEREST\n" + "-" * 70 + "\n"
            topics = profile.get("topics", {})
            for topic, count in topics.items():
                display_text += f"  {topic}: {count} mentions\n"
            display_text += "\n"

        # Health & Fitness
        if "health" in profile or "fitness" in profile:
            display_text += "HEALTH & FITNESS\n" + "-" * 70 + "\n"
            health = profile.get("health", {})
            for key, val in health.items():
                display_text += f"  {key}: {val}\n"
            display_text += "\n"

        # Custom Facts
        if "custom_facts" in profile and profile["custom_facts"]:
            display_text += "CUSTOM FACTS (Remember That...)\n" + "-" * 70 + "\n"
            for fact in profile.get("custom_facts", []):
                display_text += f"  • {fact}\n"
            display_text += "\n"

        display_text += "=" * 70 + "\nEOF\n"

        self.profile_text.insert(tk.END, display_text)
        self.profile_text.config(state=tk.NORMAL)  # Allow user to select/copy

    def _export_profile(self) -> None:
        """Export profile to JSON file."""
        profile = self._decrypt_profile()
        if not profile:
            messagebox.showerror("Export Failed", "Could not load or export profile.")
            return

        export_path = PROJECT_ROOT / "data" / "user_profile" / "profile_export.json"
        try:
            export_path.write_text(json.dumps(profile, indent=2, ensure_ascii=False), encoding="utf-8")
            messagebox.showinfo("Export Success", f"Profile exported to:\n{export_path}")
        except Exception as e:
            messagebox.showerror("Export Failed", f"Could not export: {e}")

    def _load_state(self) -> Dict[str, Dict[str, float]]:
        if STATE_FILE.exists():
            try:
                return json.loads(STATE_FILE.read_text(encoding="utf-8"))
            except Exception:
                return {"known": {}}
        return {"known": {}}

    def _save_state(self) -> None:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(self.state, indent=2), encoding="utf-8")

    def _scan_wavs(self) -> List[Path]:
        files: List[Path] = []
        for folder in (WAKE_DIR, PHRASE_DIR):
            if folder.exists():
                files.extend(sorted(folder.glob("*.wav")))
        return files

    def _slug_from_name(self, path: Path) -> str:
        stem = path.stem.lower()
        stem = re.sub(r"[^a-z0-9]+", "_", stem).strip("_")
        return stem or "sample"

    def _next_index(self, folder: Path, prefix_regex: re.Pattern) -> int:
        max_idx = 0
        for p in folder.glob("*.wav"):
            m = prefix_regex.match(p.name)
            if m:
                try:
                    max_idx = max(max_idx, int(m.group(1)))
                except Exception:
                    pass
        return max_idx + 1

    def _collect_invalid(self, files: List[Path]) -> List[InvalidName]:
        out: List[InvalidName] = []

        wake_next = self._next_index(WAKE_DIR, re.compile(r"^phrase_(\d{5})_.*\.wav$"))
        phrase_next = self._next_index(PHRASE_DIR, re.compile(r"^(\d{4})_.*\.wav$"))

        for p in files:
            if p.parent == WAKE_DIR and not WAKE_PATTERN.match(p.name):
                slug = self._slug_from_name(p)
                suggestion = f"phrase_{wake_next:05d}_{slug}.wav"
                out.append(InvalidName(path=p, suggestion=suggestion, reason="wake folder naming mismatch"))
                wake_next += 1
            elif p.parent == PHRASE_DIR and not PHRASE_PATTERN.match(p.name):
                slug = self._slug_from_name(p)
                suggestion = f"{phrase_next:04d}_{slug}.wav"
                out.append(InvalidName(path=p, suggestion=suggestion, reason="phrase folder naming mismatch"))
                phrase_next += 1
        return out

    def _current_known_map(self, files: List[Path]) -> Dict[str, float]:
        known: Dict[str, float] = {}
        for p in files:
            try:
                known[str(p)] = p.stat().st_mtime
            except Exception:
                continue
        return known

    def refresh_scan(self) -> None:
        files = self._scan_wavs()
        wake_count = len(list(WAKE_DIR.glob("*.wav"))) if WAKE_DIR.exists() else 0
        phrase_count = len(list(PHRASE_DIR.glob("*.wav"))) if PHRASE_DIR.exists() else 0

        current = self._current_known_map(files)
        known = self.state.get("known", {})
        new_files = [p for p in files if str(p) not in known or known[str(p)] != current[str(p)]]

        self.invalid = self._collect_invalid(files)
        self.invalid_list.delete(0, tk.END)
        for item in self.invalid:
            self.invalid_list.insert(tk.END, f"{item.path.name} -> {item.suggestion} [{item.reason}]")

        self.wake_count_var.set(f"Wake folder: {wake_count} WAV files")
        self.phrase_count_var.set(f"Phrase folder: {phrase_count} WAV files")
        self.new_count_var.set(f"New since last baseline: {len(new_files)}")

        self._log(f"Scan complete: wake={wake_count}, phrase={phrase_count}, new={len(new_files)}, invalid={len(self.invalid)}")

    def mark_baseline(self) -> None:
        files = self._scan_wavs()
        self.state["known"] = self._current_known_map(files)
        self._save_state()
        self._log("Baseline updated to current files.")
        self.refresh_scan()

    def auto_rename_invalid(self) -> None:
        if not self.invalid:
            messagebox.showinfo("No Rename Needed", "No invalid filenames detected.")
            return

        renamed = 0
        for item in self.invalid:
            target = item.path.with_name(item.suggestion)
            try:
                if target.exists():
                    self._log(f"Skip rename (exists): {target.name}")
                    continue
                item.path.rename(target)
                renamed += 1
                self._log(f"Renamed: {item.path.name} -> {target.name}")
            except Exception as e:
                self._log(f"Rename failed for {item.path.name}: {e}")

        self._log(f"Auto-rename complete: {renamed} files renamed.")
        self.refresh_scan()

    def open_recording_folders(self) -> None:
        for p in (WAKE_DIR, PHRASE_DIR):
            p.mkdir(parents=True, exist_ok=True)
            try:
                import os
                os.startfile(str(p))  # type: ignore[attr-defined]
            except Exception as e:
                self._log(f"Could not open folder {p}: {e}")

    def _run_command_async(self, cmd: List[str], cwd: Path | None = None, progress_var: Optional[tk.StringVar] = None, progress_bar: Optional[ttk.Progressbar] = None) -> None:
        def _worker() -> None:
            self._log("\n>> " + " ".join(cmd))
            try:
                proc = subprocess.Popen(
                    cmd,
                    cwd=str(cwd) if cwd else str(PROJECT_ROOT),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                )
                assert proc.stdout is not None
                for line in proc.stdout:
                    self._log(line.rstrip())
                    
                    # Parse progress from log line
                    if progress_var and progress_bar:
                        self._parse_progress(line, progress_var, progress_bar)
                
                code = proc.wait()
                self._log(f"Command finished with exit code {code}")
                if code == 0 and progress_bar:
                    progress_bar['value'] = 100
                    if progress_var:
                        progress_var.set("100%")
            except Exception as e:
                self._log(f"Command failed: {e}")

        threading.Thread(target=_worker, daemon=True).start()

    def _parse_progress(self, line: str, progress_var: tk.StringVar, progress_bar: ttk.Progressbar) -> None:
        """Extract training progress from output lines."""
        import re
        
        # Pattern 1: Hugging Face Trainer format - "Epoch: 3/50, Step: 150/500"
        match = re.search(r"Epoch\s*:\s*(\d+)/(\d+).*Step\s*:\s*(\d+)/(\d+)", line, re.IGNORECASE)
        if match:
            curr_epoch, total_epochs, curr_step, total_steps = map(int, match.groups())
            # Calculate overall progress
            overall_progress = (curr_epoch / total_epochs) * 100 if total_epochs > 0 else 0
            progress_bar['value'] = overall_progress
            progress_var.set(f"Ep {curr_epoch}/{total_epochs} ({int(overall_progress)}%)")
            self.root.update_idletasks()
            return
        
        # Pattern 2: Simple epoch/step from ongoing training
        match = re.search(r"\[\s*(\d+)/(\d+)\s*\]", line)
        if match:
            curr, total = map(int, match.groups())
            progress = (curr / total) * 100 if total > 0 else 0
            progress_bar['value'] = progress
            progress_var.set(f"{int(progress)}%")
            self.root.update_idletasks()
            return
        
        # Pattern 3: Loss or WER metrics (indicates training is ongoing)
        if any(x in line.lower() for x in ["loss:", "wer:", "eval_loss"]):
            # At least show something is happening
            if progress_bar['value'] < 90:
                progress_bar['value'] += 2
                progress_var.set(f"{int(progress_bar['value'])}%")
                self.root.update_idletasks()

    def prepare_stt(self) -> None:
        self.stt_progress['value'] = 0
        self.stt_progress_var.set("0%")
        self._run_command_async([sys.executable, str(PREP_SCRIPT)], progress_var=self.stt_progress_var, progress_bar=self.stt_progress)
        self._run_command_async([sys.executable, str(CSV_SCRIPT)], progress_var=self.stt_progress_var, progress_bar=self.stt_progress)

    def train_stt(self) -> None:
        self.stt_progress['value'] = 0
        self.stt_progress_var.set("0%")
        self._run_command_async([sys.executable, str(STT_TRAIN_SCRIPT)], progress_var=self.stt_progress_var, progress_bar=self.stt_progress)

    def launch_tts(self) -> None:
        self.tts_progress['value'] = 0
        self.tts_progress_var.set("0%")
        self._run_command_async([sys.executable, str(TTS_LAUNCH_SCRIPT)], cwd=TTS_LAUNCH_SCRIPT.parent, progress_var=self.tts_progress_var, progress_bar=self.tts_progress)

    def _log(self, msg: str) -> None:
        self.log.insert(tk.END, msg + "\n")
        self.log.see(tk.END)


def main() -> None:
    root = tk.Tk()
    app = TrainingHubApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
