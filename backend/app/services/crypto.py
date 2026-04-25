"""Symmetric encryption for sensitive credentials using Fernet (AES-128-CBC)."""
from __future__ import annotations
import base64
import hashlib

from cryptography.fernet import Fernet


def _fernet() -> Fernet:
    from app.core.config import settings
    raw = hashlib.sha256(settings.JWT_SECRET.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(raw))


def encrypt_bytes(data: bytes) -> str:
    return _fernet().encrypt(data).decode()


def decrypt_bytes(token: str) -> bytes:
    return _fernet().decrypt(token.encode())


def encrypt_str(s: str) -> str:
    return encrypt_bytes(s.encode())


def decrypt_str(token: str) -> str:
    return decrypt_bytes(token).decode()
