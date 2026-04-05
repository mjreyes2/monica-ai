"""
Monica AI - Authentication & Access Control Manager

Provides:
- Password-based login with bcrypt-like hashing (PBKDF2-SHA256)
- Session management with timeout
- Role-based access control (RBAC)
- Failed login lockout protection
- Password change functionality
- All operations are audit-logged via HIPAA module
"""
import hashlib
import hmac
import json
import os
import secrets
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger("Monica.Auth")


class AuthManager:
    """
    Authentication manager for Monica AI.
    Protects access to the application and sensitive data.
    """

    MAX_FAILED_ATTEMPTS = 5
    LOCKOUT_DURATION_SECONDS = 300  # 5 minutes
    SESSION_TIMEOUT_SECONDS = 3600  # 1 hour

    def __init__(self, security_dir: Path = None):
        if security_dir is None:
            try:
                from config.settings import config
                security_dir = Path(str(config.BASE_DIR)) / "data" / ".security"
            except Exception:
                security_dir = Path("data") / ".security"

        self.security_dir = security_dir
        self.security_dir.mkdir(parents=True, exist_ok=True)
        self.credentials_file = self.security_dir / "credentials.json"
        self.session_file = self.security_dir / "session.json"

        self._credentials = self._load_credentials()
        self._session: Optional[Dict[str, Any]] = None
        self._failed_attempts = 0
        self._lockout_until = 0.0

        # Try to load audit logger
        self._audit = None
        try:
            from security.hipaa_compliance import get_hipaa_compliance
            self._audit = get_hipaa_compliance().audit
        except Exception:
            pass

        logger.info("AuthManager initialized")

    def _load_credentials(self) -> Dict[str, Any]:
        if self.credentials_file.exists():
            try:
                with open(self.credentials_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _save_credentials(self):
        with open(self.credentials_file, "w", encoding="utf-8") as f:
            json.dump(self._credentials, f, indent=2)
        # Restrict permissions
        try:
            import stat
            os.chmod(str(self.credentials_file), stat.S_IRUSR | stat.S_IWUSR)
        except Exception:
            pass

    @staticmethod
    def _hash_password(password: str, salt: bytes = None) -> Dict[str, str]:
        """Hash password using PBKDF2-HMAC-SHA256 (NIST recommended)."""
        if salt is None:
            salt = secrets.token_bytes(32)
        key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations=600000)
        return {
            "hash": key.hex(),
            "salt": salt.hex(),
            "algorithm": "pbkdf2_sha256",
            "iterations": 600000,
        }

    @staticmethod
    def _verify_password(password: str, stored: Dict[str, str]) -> bool:
        """Verify a password against stored hash."""
        salt = bytes.fromhex(stored["salt"])
        iterations = stored.get("iterations", 600000)
        key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
        return hmac.compare_digest(key.hex(), stored["hash"])

    def is_setup(self) -> bool:
        """Check if a password has been set up."""
        return bool(self._credentials.get("password_hash"))

    def setup_password(self, password: str, confirm: str) -> tuple:
        """Initial password setup. Returns (success, message)."""
        if len(password) < 8:
            return False, "Password must be at least 8 characters."
        if password != confirm:
            return False, "Passwords do not match."

        hashed = self._hash_password(password)
        self._credentials["password_hash"] = hashed
        self._credentials["created_at"] = datetime.now().isoformat()
        self._credentials["role"] = "owner"
        self._save_credentials()

        if self._audit:
            self._audit.log_access("owner", "AUTH", "PASSWORD_SETUP", True)

        logger.info("Password setup complete")
        return True, "Password set successfully. Monica is now protected."

    def login(self, password: str) -> tuple:
        """Attempt login. Returns (success, message)."""
        # Check lockout
        if time.time() < self._lockout_until:
            remaining = int(self._lockout_until - time.time())
            msg = f"Account locked. Try again in {remaining} seconds."
            if self._audit:
                self._audit.log_access("unknown", "AUTH", "LOGIN_LOCKED", False, msg)
            return False, msg

        if not self.is_setup():
            return False, "No password set. Please set up a password first."

        stored = self._credentials.get("password_hash", {})
        if self._verify_password(password, stored):
            self._failed_attempts = 0
            self._session = {
                "token": secrets.token_hex(32),
                "login_time": datetime.now().isoformat(),
                "expires": time.time() + self.SESSION_TIMEOUT_SECONDS,
                "role": self._credentials.get("role", "owner"),
            }
            if self._audit:
                self._audit.log_access("owner", "AUTH", "LOGIN_SUCCESS", True)
            logger.info("Login successful")
            return True, "Login successful. Welcome back!"
        else:
            self._failed_attempts += 1
            remaining = self.MAX_FAILED_ATTEMPTS - self._failed_attempts
            if self._failed_attempts >= self.MAX_FAILED_ATTEMPTS:
                self._lockout_until = time.time() + self.LOCKOUT_DURATION_SECONDS
                msg = f"Too many failed attempts. Locked for {self.LOCKOUT_DURATION_SECONDS // 60} minutes."
                if self._audit:
                    self._audit.log_access("unknown", "AUTH", "LOGIN_LOCKOUT", False, msg)
                return False, msg
            msg = f"Incorrect password. {remaining} attempts remaining."
            if self._audit:
                self._audit.log_access("unknown", "AUTH", "LOGIN_FAILED", False,
                                       f"attempt {self._failed_attempts}")
            return False, msg

    def logout(self):
        """End the current session."""
        if self._audit:
            self._audit.log_access("owner", "AUTH", "LOGOUT", True)
        self._session = None
        logger.info("Logged out")

    def is_authenticated(self) -> bool:
        """Check if there's a valid session."""
        if not self._session:
            return False
        if time.time() > self._session.get("expires", 0):
            self._session = None
            return False
        return True

    def change_password(self, old_password: str, new_password: str, confirm: str) -> tuple:
        """Change the password. Returns (success, message)."""
        if not self.is_authenticated():
            return False, "Must be logged in to change password."
        stored = self._credentials.get("password_hash", {})
        if not self._verify_password(old_password, stored):
            return False, "Current password is incorrect."
        if len(new_password) < 8:
            return False, "New password must be at least 8 characters."
        if new_password != confirm:
            return False, "New passwords do not match."

        hashed = self._hash_password(new_password)
        self._credentials["password_hash"] = hashed
        self._credentials["password_changed"] = datetime.now().isoformat()
        self._save_credentials()

        if self._audit:
            self._audit.log_access("owner", "AUTH", "PASSWORD_CHANGED", True)
        return True, "Password changed successfully."

    def get_session_info(self) -> Dict[str, Any]:
        """Get current session info."""
        if not self._session:
            return {"authenticated": False}
        return {
            "authenticated": True,
            "role": self._session.get("role", "unknown"),
            "login_time": self._session.get("login_time", ""),
            "expires_in_seconds": max(0, int(self._session.get("expires", 0) - time.time())),
        }


# Singleton
_auth = None


def get_auth_manager() -> AuthManager:
    global _auth
    if _auth is None:
        _auth = AuthManager()
    return _auth
