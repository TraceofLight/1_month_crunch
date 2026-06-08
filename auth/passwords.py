"""Password hashing helpers using the Python standard library."""

from __future__ import annotations

import hashlib
import hmac
import os


ITERATIONS = 120_000


def hash_password(password: str, salt: bytes | None = None) -> str:
    """Return a PBKDF2 password hash encoded for database storage."""

    selected_salt = salt or os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), selected_salt, ITERATIONS)
    return f"pbkdf2_sha256${ITERATIONS}${selected_salt.hex()}${digest.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Check a plain password against a stored PBKDF2 hash."""

    algorithm, iterations, salt_hex, digest_hex = stored_hash.split("$", 3)
    if algorithm != "pbkdf2_sha256":
        return False
    expected = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        bytes.fromhex(salt_hex),
        int(iterations),
    )
    return hmac.compare_digest(expected.hex(), digest_hex)
