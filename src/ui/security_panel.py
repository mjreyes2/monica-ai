"""
Monica AI - Security & HIPAA Compliance Panel (GUI)

Provides tkinter UI components for:
- Login/Authentication dialog
- Audit log viewer
- HIPAA compliance report viewer
- Access control settings
- Encryption status display
- Session management
- Desktop teaching lesson launcher
"""
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger("Monica.SecurityPanel")

try:
    import tkinter as tk
    from tkinter import ttk, scrolledtext, messagebox
    HAS_TK = True
except ImportError:
    HAS_TK = False


class LoginDialog:
    """Modal login dialog for Monica AI."""

    def __init__(self, parent: tk.Tk, auth_manager):
        self.parent = parent
        self.auth = auth_manager
        self.result = False
        self.dialog = None

    def show(self) -> bool:
        """Show login dialog. Returns True if authenticated."""
        if not HAS_TK:
            return True

        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Monica AI - Login")
        self.dialog.geometry("400x350")
        self.dialog.configure(bg="#0a0a2e")
        self.dialog.resizable(False, False)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()

        # Center on screen
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() - 400) // 2
        y = (self.dialog.winfo_screenheight() - 350) // 2
        self.dialog.geometry(f"400x350+{x}+{y}")

        # Title
        tk.Label(self.dialog, text="Monica AI",
                 bg="#0a0a2e", fg="#00d4ff", font=("Segoe UI", 18, "bold")).pack(pady=(25, 5))
        tk.Label(self.dialog, text="Secure Login",
                 bg="#0a0a2e", fg="#888888", font=("Segoe UI", 10)).pack(pady=(0, 20))

        if not self.auth.is_setup():
            self._build_setup_form()
        else:
            self._build_login_form()

        self.dialog.protocol("WM_DELETE_WINDOW", self._on_cancel)
        self.parent.wait_window(self.dialog)
        return self.result

    def _build_login_form(self):
        frame = tk.Frame(self.dialog, bg="#0a0a2e")
        frame.pack(padx=40, fill=tk.X)

        tk.Label(frame, text="Password:", bg="#0a0a2e", fg="#e0e0e0",
                 font=("Segoe UI", 10)).pack(anchor=tk.W, pady=(0, 3))
        self.pw_entry = tk.Entry(frame, show="●", bg="#16213e", fg="#e0e0e0",
                                 insertbackground="#00d4ff", font=("Segoe UI", 12),
                                 relief=tk.FLAT)
        self.pw_entry.pack(fill=tk.X, ipady=6)
        self.pw_entry.focus_set()
        self.pw_entry.bind("<Return>", lambda e: self._do_login())

        self.msg_label = tk.Label(self.dialog, text="", bg="#0a0a2e", fg="#ff4444",
                                  font=("Segoe UI", 9))
        self.msg_label.pack(pady=(8, 0))

        tk.Button(self.dialog, text="Login", bg="#16213e", fg="#00ff88",
                  activebackground="#1a1a4e", font=("Segoe UI", 11, "bold"),
                  relief=tk.FLAT, width=20, command=self._do_login).pack(pady=(15, 5))

        tk.Button(self.dialog, text="Cancel", bg="#3e1616", fg="#ff6666",
                  activebackground="#4e1a1a", font=("Segoe UI", 10),
                  relief=tk.FLAT, width=20, command=self._on_cancel).pack()

    def _build_setup_form(self):
        tk.Label(self.dialog, text="First time? Set up your password:",
                 bg="#0a0a2e", fg="#ffcc00", font=("Segoe UI", 10)).pack(pady=(0, 10))

        frame = tk.Frame(self.dialog, bg="#0a0a2e")
        frame.pack(padx=40, fill=tk.X)

        tk.Label(frame, text="New Password (min 8 chars):", bg="#0a0a2e", fg="#e0e0e0",
                 font=("Segoe UI", 10)).pack(anchor=tk.W, pady=(0, 2))
        self.pw_entry = tk.Entry(frame, show="●", bg="#16213e", fg="#e0e0e0",
                                 insertbackground="#00d4ff", font=("Segoe UI", 11),
                                 relief=tk.FLAT)
        self.pw_entry.pack(fill=tk.X, ipady=5)
        self.pw_entry.focus_set()

        tk.Label(frame, text="Confirm Password:", bg="#0a0a2e", fg="#e0e0e0",
                 font=("Segoe UI", 10)).pack(anchor=tk.W, pady=(8, 2))
        self.pw_confirm = tk.Entry(frame, show="●", bg="#16213e", fg="#e0e0e0",
                                   insertbackground="#00d4ff", font=("Segoe UI", 11),
                                   relief=tk.FLAT)
        self.pw_confirm.pack(fill=tk.X, ipady=5)
        self.pw_confirm.bind("<Return>", lambda e: self._do_setup())

        self.msg_label = tk.Label(self.dialog, text="", bg="#0a0a2e", fg="#ff4444",
                                  font=("Segoe UI", 9))
        self.msg_label.pack(pady=(5, 0))

        tk.Button(self.dialog, text="Set Password & Login", bg="#16213e", fg="#00ff88",
                  activebackground="#1a1a4e", font=("Segoe UI", 11, "bold"),
                  relief=tk.FLAT, width=25, command=self._do_setup).pack(pady=(10, 0))

    def _do_login(self):
        pw = self.pw_entry.get()
        ok, msg = self.auth.login(pw)
        if ok:
            self.result = True
            self.dialog.destroy()
        else:
            self.msg_label.config(text=msg)
            self.pw_entry.delete(0, tk.END)

    def _do_setup(self):
        pw = self.pw_entry.get()
        confirm = self.pw_confirm.get()
        ok, msg = self.auth.setup_password(pw, confirm)
        if ok:
            ok2, msg2 = self.auth.login(pw)
            if ok2:
                self.result = True
                self.dialog.destroy()
            else:
                self.msg_label.config(text=msg2)
        else:
            self.msg_label.config(text=msg)

    def _on_cancel(self):
        self.result = False
        self.dialog.destroy()


class SecurityPanel:
    """
    HIPAA Compliance & Security panel for the Monica AI GUI.
    Adds buttons for audit log viewing, compliance reports, etc.
    """

    def __init__(self, parent_frame: tk.Frame, root: tk.Tk):
        self.parent = parent_frame
        self.root = root
        self._hipaa = None
        self._auth = None
        self._teacher = None
        self._build_panel()

    def _get_hipaa(self):
        if self._hipaa is None:
            try:
                from security.hipaa_compliance import get_hipaa_compliance
                self._hipaa = get_hipaa_compliance()
            except Exception:
                pass
        return self._hipaa

    def _get_auth(self):
        if self._auth is None:
            try:
                from security.auth_manager import get_auth_manager
                self._auth = get_auth_manager()
            except Exception:
                pass
        return self._auth

    def _get_teacher(self):
        if self._teacher is None:
            try:
                from ui.desktop_teaching_overlay import get_desktop_teacher
                self._teacher = get_desktop_teacher()
                self._teacher.set_root(self.root)
            except Exception:
                pass
        return self._teacher

    def _build_panel(self):
        """Build the security panel buttons."""
        # Security Section Header
        tk.Label(self.parent, text="Security & HIPAA",
                 bg="#1a1a2e", fg="#00d4ff", font=("Segoe UI", 10, "bold")).pack(
            anchor=tk.W, padx=5, pady=(8, 3))

        btn_frame = tk.Frame(self.parent, bg="#1a1a2e")
        btn_frame.pack(fill=tk.X, padx=5)

        btn_style = {"bg": "#16213e", "fg": "#e0e0e0", "activebackground": "#1a1a4e",
                     "activeforeground": "#00d4ff", "relief": tk.FLAT,
                     "font": ("Segoe UI", 9), "width": 18, "anchor": tk.W}

        tk.Button(btn_frame, text="View Audit Log", command=self._show_audit_log,
                  **btn_style).pack(fill=tk.X, pady=1)
        tk.Button(btn_frame, text="Compliance Report", command=self._show_compliance_report,
                  **btn_style).pack(fill=tk.X, pady=1)
        tk.Button(btn_frame, text=" Change Password", command=self._show_change_password,
                  **btn_style).pack(fill=tk.X, pady=1)
        tk.Button(btn_frame, text="Encrypt Data Now", command=self._encrypt_sensitive_data,
                  **btn_style).pack(fill=tk.X, pady=1)
        tk.Button(btn_frame, text="Logout", command=self._do_logout,
                  **{**btn_style, "fg": "#ff6666"}).pack(fill=tk.X, pady=1)

        # Teaching Section
        tk.Label(self.parent, text="Teaching & Lessons",
                 bg="#1a1a2e", fg="#00d4ff", font=("Segoe UI", 10, "bold")).pack(
            anchor=tk.W, padx=5, pady=(10, 3))

        teach_frame = tk.Frame(self.parent, bg="#1a1a2e")
        teach_frame.pack(fill=tk.X, padx=5)

        tk.Button(teach_frame, text=" Python Basics", **btn_style,
                  command=lambda: self._start_lesson("python_basics")).pack(fill=tk.X, pady=1)
        tk.Button(teach_frame, text="Programming 101", **btn_style,
                  command=lambda: self._start_lesson("programming")).pack(fill=tk.X, pady=1)
        tk.Button(teach_frame, text=" Computer Science", **btn_style,
                  command=lambda: self._start_lesson("computer_science")).pack(fill=tk.X, pady=1)
        tk.Button(teach_frame, text=" Web Development", **btn_style,
                  command=lambda: self._start_lesson("web_development")).pack(fill=tk.X, pady=1)
        tk.Button(teach_frame, text=" Windows Tips", **btn_style,
                  command=lambda: self._start_lesson("windows_basics")).pack(fill=tk.X, pady=1)

    def _show_audit_log(self):
        """Open audit log viewer window."""
        hipaa = self._get_hipaa()
        if not hipaa:
            messagebox.showwarning("Not Available", "HIPAA module not loaded.")
            return

        win = tk.Toplevel(self.root)
        win.title("Monica AI - HIPAA Audit Log")
        win.geometry("750x500")
        win.configure(bg="#0a0a2e")
        win.attributes("-topmost", True)

        tk.Label(win, text="HIPAA Audit Log", bg="#0a0a2e", fg="#00d4ff",
                 font=("Segoe UI", 14, "bold")).pack(pady=(10, 5))
        tk.Label(win, text="All access to protected data is logged here",
                 bg="#0a0a2e", fg="#888888", font=("Segoe UI", 9)).pack()

        log_text = scrolledtext.ScrolledText(win, bg="#0f0f23", fg="#e0e0e0",
                                              font=("Consolas", 9), wrap=tk.WORD,
                                              state=tk.NORMAL)
        log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Load logs
        entries = hipaa.audit.get_recent_logs(200)
        if entries:
            for entry in entries:
                if "DENIED" in entry or "FAILED" in entry or "LOCKOUT" in entry:
                    log_text.insert(tk.END, entry + "\n", "error")
                elif "SUCCESS" in entry:
                    log_text.insert(tk.END, entry + "\n", "success")
                else:
                    log_text.insert(tk.END, entry + "\n")
            log_text.tag_configure("error", foreground="#ff4444")
            log_text.tag_configure("success", foreground="#00ff88")
        else:
            log_text.insert(tk.END, "No audit log entries yet.\n")

        log_text.configure(state=tk.DISABLED)
        log_text.see(tk.END)

        btn_frame = tk.Frame(win, bg="#0a0a2e")
        btn_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        tk.Button(btn_frame, text="Refresh", bg="#16213e", fg="#00d4ff",
                  relief=tk.FLAT, font=("Segoe UI", 10),
                  command=lambda: self._refresh_audit_log(log_text, hipaa)).pack(side=tk.LEFT)
        tk.Label(btn_frame, text=f"  {len(entries)} entries", bg="#0a0a2e", fg="#888888",
                 font=("Segoe UI", 9)).pack(side=tk.LEFT)

    def _refresh_audit_log(self, text_widget, hipaa):
        text_widget.configure(state=tk.NORMAL)
        text_widget.delete("1.0", tk.END)
        entries = hipaa.audit.get_recent_logs(200)
        for entry in entries:
            if "DENIED" in entry or "FAILED" in entry:
                text_widget.insert(tk.END, entry + "\n", "error")
            elif "SUCCESS" in entry:
                text_widget.insert(tk.END, entry + "\n", "success")
            else:
                text_widget.insert(tk.END, entry + "\n")
        text_widget.configure(state=tk.DISABLED)
        text_widget.see(tk.END)

    def _show_compliance_report(self):
        """Show HIPAA compliance report window."""
        hipaa = self._get_hipaa()
        if not hipaa:
            messagebox.showwarning("Not Available", "HIPAA module not loaded.")
            return

        report = hipaa.get_compliance_report()

        win = tk.Toplevel(self.root)
        win.title("Monica AI - HIPAA Compliance Report")
        win.geometry("600x550")
        win.configure(bg="#0a0a2e")
        win.attributes("-topmost", True)

        tk.Label(win, text="HIPAA Compliance Report", bg="#0a0a2e", fg="#00d4ff",
                 font=("Segoe UI", 14, "bold")).pack(pady=(10, 5))
        tk.Label(win, text=f"Generated: {report.get('timestamp', '')}",
                 bg="#0a0a2e", fg="#888888", font=("Segoe UI", 9)).pack()

        content = tk.Frame(win, bg="#0f0f23", bd=1, relief=tk.SOLID)
        content.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

        items = [
            ("Encryption Method", report.get("encryption_method", "Unknown"),
             "#00ff88" if report.get("encryption_available") else "#ff4444"),
            ("Encryption Available", "YES" if report.get("encryption_available") else "NO - INSTALL cryptography",
             "#00ff88" if report.get("encryption_available") else "#ff4444"),
            ("Audit Logging", "ACTIVE" if report.get("audit_logging") else "INACTIVE",
             "#00ff88" if report.get("audit_logging") else "#ff4444"),
            ("Integrity Checking", "ACTIVE" if report.get("integrity_checking") else "INACTIVE",
             "#00ff88"),
            ("Master Key", "PRESENT" if report.get("master_key_exists") else "MISSING",
             "#00ff88" if report.get("master_key_exists") else "#ff4444"),
            ("Audit Log Entries", str(report.get("audit_log_entries", 0)), "#e0e0e0"),
        ]

        for i, (label, value, color) in enumerate(items):
            row = tk.Frame(content, bg="#0f0f23")
            row.pack(fill=tk.X, padx=10, pady=3)
            tk.Label(row, text=f"{label}:", bg="#0f0f23", fg="#aaaaaa",
                     font=("Segoe UI", 10), width=22, anchor=tk.W).pack(side=tk.LEFT)
            tk.Label(row, text=value, bg="#0f0f23", fg=color,
                     font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)

        # Protected directories
        tk.Label(content, text="\nProtected Directories:", bg="#0f0f23", fg="#00d4ff",
                 font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, padx=10)
        for d in report.get("protected_directories", []):
            status = "[OK]" if d.get("exists") else "[X]"
            path = Path(d.get("path", "")).name
            files = d.get("file_count", 0)
            tk.Label(content, text=f"  {status} {path} ({files} files)",
                     bg="#0f0f23", fg="#e0e0e0", font=("Consolas", 9)).pack(anchor=tk.W, padx=10)

        # Recommendations
        tk.Label(content, text="\nRecommendations:", bg="#0f0f23", fg="#ffcc00",
                 font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, padx=10)
        for rec in report.get("recommendations", []):
            color = "#ff4444" if "CRITICAL" in rec else "#ffcc00" if "WARNING" in rec else "#aaaaaa"
            tk.Label(content, text=f"  - {rec}", bg="#0f0f23", fg=color,
                     font=("Segoe UI", 9), wraplength=520, justify=tk.LEFT).pack(
                anchor=tk.W, padx=10)

    def _show_change_password(self):
        """Show change password dialog."""
        auth = self._get_auth()
        if not auth:
            messagebox.showwarning("Not Available", "Auth module not loaded.")
            return
        if not auth.is_authenticated():
            messagebox.showwarning("Not Logged In", "You must be logged in to change your password.")
            return

        win = tk.Toplevel(self.root)
        win.title("Change Password")
        win.geometry("380x300")
        win.configure(bg="#0a0a2e")
        win.attributes("-topmost", True)
        win.resizable(False, False)

        tk.Label(win, text=" Change Password", bg="#0a0a2e", fg="#00d4ff",
                 font=("Segoe UI", 13, "bold")).pack(pady=(15, 10))

        form = tk.Frame(win, bg="#0a0a2e")
        form.pack(padx=30, fill=tk.X)

        entries = {}
        for label_text, key in [("Current Password:", "old"), ("New Password:", "new"),
                                 ("Confirm New:", "confirm")]:
            tk.Label(form, text=label_text, bg="#0a0a2e", fg="#e0e0e0",
                     font=("Segoe UI", 10)).pack(anchor=tk.W, pady=(5, 1))
            e = tk.Entry(form, show="●", bg="#16213e", fg="#e0e0e0",
                         insertbackground="#00d4ff", font=("Segoe UI", 11), relief=tk.FLAT)
            e.pack(fill=tk.X, ipady=4)
            entries[key] = e

        msg_label = tk.Label(win, text="", bg="#0a0a2e", fg="#ff4444", font=("Segoe UI", 9))
        msg_label.pack(pady=(5, 0))

        def do_change():
            ok, msg = auth.change_password(
                entries["old"].get(), entries["new"].get(), entries["confirm"].get())
            if ok:
                messagebox.showinfo("Success", msg)
                win.destroy()
            else:
                msg_label.config(text=msg)

        tk.Button(win, text="Change Password", bg="#16213e", fg="#00ff88",
                  font=("Segoe UI", 11, "bold"), relief=tk.FLAT,
                  command=do_change).pack(pady=(10, 0))

    def _encrypt_sensitive_data(self):
        """Encrypt all sensitive data directories."""
        hipaa = self._get_hipaa()
        if not hipaa:
            messagebox.showwarning("Not Available", "HIPAA module not loaded.")
            return

        total = 0
        for d in hipaa.protected_dirs:
            if d.exists():
                count = hipaa.encrypt_existing_files(d)
                total += count

        if total > 0:
            messagebox.showinfo("Encryption Complete",
                                f"Encrypted {total} files across protected directories.")
        else:
            messagebox.showinfo("Encryption Status",
                                "All sensitive files are already encrypted or no files found.")

    def _do_logout(self):
        auth = self._get_auth()
        if auth:
            auth.logout()
            messagebox.showinfo("Logged Out", "You have been logged out.\nRestart Monica to log in again.")

    def _start_lesson(self, category: str):
        """Start a teaching lesson."""
        teacher = self._get_teacher()
        if not teacher:
            messagebox.showwarning("Not Available", "Teaching module not loaded.")
            return
        ok = teacher.start_lesson_by_name(category)
        if not ok:
            messagebox.showwarning("No Lessons", f"No lessons found for: {category}")
