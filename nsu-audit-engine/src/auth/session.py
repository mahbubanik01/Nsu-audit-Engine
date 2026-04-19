"""
Session Store
Persists active sessions to a local JSON file for CLI use.
For web/mobile, swap this for a database-backed store.
"""

import json
import os
import time
from typing import Optional
from auth.config import AuthConfig


class SessionStore:
    """
    Manages persistent sessions for the CLI.
    Stores the latest token so users don't re-login every time.
    """

    def __init__(self, config: Optional[AuthConfig] = None):
        self.config = config or AuthConfig.from_env()
        self._file = self.config.sessions_file

    def save_token(self, email: str, token: str):
        """Save an authenticated session."""
        data = self._load()
        data[email.lower()] = {
            "token": token,
            "saved_at": time.time(),
        }
        self._write(data)

    def get_token(self, email: Optional[str] = None) -> Optional[str]:
        """
        Get saved token.
        If email is None, return the most recently saved token.
        """
        data = self._load()
        if not data:
            return None

        if email:
            entry = data.get(email.lower())
            return entry["token"] if entry else None

        # Return most recent
        latest = max(data.values(), key=lambda x: x.get("saved_at", 0))
        return latest["token"]

    def clear(self, email: Optional[str] = None):
        """Clear a session or all sessions."""
        if email:
            data = self._load()
            data.pop(email.lower(), None)
            self._write(data)
        else:
            self._write({})

    def _load(self) -> dict:
        """Load sessions from file."""
        if not os.path.exists(self._file):
            return {}
        try:
            with open(self._file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}

    def _write(self, data: dict):
        """Write sessions to file."""
        os.makedirs(os.path.dirname(self._file), exist_ok=True)
        with open(self._file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
