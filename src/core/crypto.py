from __future__ import annotations

import base64
import hashlib
import os
import sqlite3
from typing import Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from .storage import get_connection


class CryptoManager:
    """Manage encryption of secrets using a master password.

    The master password is not stored. Instead a key is derived from it using
    PBKDF2 and a random salt. The salt, key version and verifier hash are kept
    in the ``settings`` table. Secrets are stored encrypted in the ``secrets``
    table and re-encrypted when the master password changes.
    """

    def __init__(self, conn: Optional[sqlite3.Connection] = None) -> None:
        self.conn = conn or get_connection()
        self._fernet: Optional[Fernet] = None
        self.salt = self._get_setting("crypto_salt")
        self.version = int(self._get_setting("crypto_key_version") or 0)
        self.verifier = self._get_setting("crypto_verifier")

    # ------------------------------------------------------------------
    # Settings helpers
    # ------------------------------------------------------------------
    def _get_setting(self, key: str) -> Optional[str]:
        cur = self.conn.cursor()
        cur.execute("SELECT value FROM settings WHERE key=?", (key,))
        row = cur.fetchone()
        return row[0] if row else None

    def _set_setting(self, key: str, value: str) -> None:
        cur = self.conn.cursor()
        cur.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, value),
        )
        self.conn.commit()

    # ------------------------------------------------------------------
    # Key derivation
    # ------------------------------------------------------------------
    def derive_key(self, password: str, salt: bytes) -> bytes:
        """Derive a Fernet key from the password and salt."""

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=390_000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode("utf-8")))

    def is_configured(self) -> bool:
        """Return ``True`` if a master password has been configured."""

        return self.salt is not None and self.verifier is not None

    # ------------------------------------------------------------------
    # Master password management
    # ------------------------------------------------------------------
    def verify_master_password(self, password: str) -> bool:
        """Verify the master password, initialising it if missing."""

        if not self.is_configured():
            self.set_master_password(password)
            return True

        salt = base64.b64decode(self.salt)
        key = self.derive_key(password, salt)
        digest = hashlib.sha256(key).hexdigest()
        if digest != self.verifier:
            return False
        self._fernet = Fernet(key)
        return True

    def set_master_password(self, password: str) -> None:
        """Set a new master password and store related metadata."""

        salt = os.urandom(16)
        key = self.derive_key(password, salt)
        self._fernet = Fernet(key)
        self.salt = base64.b64encode(salt).decode("utf-8")
        self.verifier = hashlib.sha256(key).hexdigest()
        self.version += 1
        self._set_setting("crypto_salt", self.salt)
        self._set_setting("crypto_verifier", self.verifier)
        self._set_setting("crypto_key_version", str(self.version))

    def rotate_master_password(self, old_password: str, new_password: str) -> bool:
        """Change master password and re-encrypt all stored secrets."""

        if not self.verify_master_password(old_password):
            return False

        cur = self.conn.cursor()
        cur.execute("SELECT id, value FROM secrets")
        secrets = [(row[0], self.decrypt(row[1])) for row in cur.fetchall()]

        self.set_master_password(new_password)

        for secret_id, plaintext in secrets:
            cur.execute(
                "UPDATE secrets SET value=? WHERE id=?",
                (self.encrypt(plaintext), secret_id),
            )
        self.conn.commit()
        return True

    # ------------------------------------------------------------------
    # Encryption helpers
    # ------------------------------------------------------------------
    def encrypt(self, data: bytes) -> bytes:
        """Encrypt data using the current master key."""

        if self._fernet is None:
            raise RuntimeError("Master password not verified")
        return self._fernet.encrypt(data)

    def decrypt(self, token: bytes) -> bytes:
        """Decrypt data using the current master key."""

        if self._fernet is None:
            raise RuntimeError("Master password not verified")
        return self._fernet.decrypt(token)

    # ------------------------------------------------------------------
    # Secret storage convenience methods
    # ------------------------------------------------------------------
    def set_secret(self, key: str, value: str) -> None:
        token = self.encrypt(value.encode("utf-8"))
        cur = self.conn.cursor()
        cur.execute(
            "INSERT OR REPLACE INTO secrets (key, value) VALUES (?, ?)",
            (key, token),
        )
        self.conn.commit()

    def get_secret(self, key: str) -> Optional[str]:
        cur = self.conn.cursor()
        cur.execute("SELECT value FROM secrets WHERE key=?", (key,))
        row = cur.fetchone()
        if not row:
            return None
        return self.decrypt(row[0]).decode("utf-8")
