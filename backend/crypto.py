"""Symmetric encryption for secrets at rest (GitHub tokens) using Fernet."""

from __future__ import annotations

import base64
import hashlib
import logging
from functools import lru_cache
from typing import Literal

from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)


class TokenEncryptionError(Exception):
    """Raised when encryption key is missing or ciphertext is invalid."""


def resolve_fernet_key(
    *,
    fernet_key: str,
    environment: Literal["dev", "test", "prod"],
    jwt_secret_key: str,
) -> str:
    """
    Return Fernet key from FERNET_KEY, or derive deterministically in dev/test only.
    Production must set FERNET_KEY explicitly.
    """
    if fernet_key:
        return fernet_key
    if environment == "prod":
        msg = "FERNET_KEY must be set in production (generate with Fernet.generate_key())"
        raise ValueError(msg)
    raw = hashlib.sha256(jwt_secret_key.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(raw).decode("ascii")


@lru_cache
def _fernet_from_key(key: str) -> Fernet:
    try:
        return Fernet(key.encode("utf-8") if isinstance(key, str) else key)
    except (ValueError, TypeError) as e:
        raise TokenEncryptionError("Invalid FERNET_KEY") from e


def encrypt_token(plaintext: str | bytes, *, fernet_key: str) -> bytes:
    """Encrypt a token for database storage. Never log plaintext or ciphertext."""
    if isinstance(plaintext, str):
        plaintext = plaintext.encode("utf-8")
    return _fernet_from_key(fernet_key).encrypt(plaintext)


def decrypt_token(ciphertext: bytes | str, *, fernet_key: str) -> str:
    """Decrypt a token after loading from the database."""
    if isinstance(ciphertext, str):
        ciphertext = ciphertext.encode("utf-8")
    try:
        return _fernet_from_key(fernet_key).decrypt(ciphertext).decode("utf-8")
    except InvalidToken as e:
        logger.warning("token_decrypt_failed")
        raise TokenEncryptionError("Could not decrypt token") from e


def encrypt_secret_string(plaintext: str, *, fernet_key: str) -> str:
    """Store arbitrary secret strings in a Text column (base64-wrapped Fernet bytes)."""
    return base64.b64encode(encrypt_token(plaintext, fernet_key=fernet_key)).decode("ascii")


def decrypt_secret_string(ciphertext: str, *, fernet_key: str) -> str:
    """Inverse of encrypt_secret_string."""
    return decrypt_token(base64.b64decode(ciphertext), fernet_key=fernet_key)
