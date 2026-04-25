import hashlib
import secrets
from typing import Tuple


def generate_api_key() -> Tuple[str, str]:
    """Generate API key and its hash. Return (key, hash)."""
    key = f"sk_{secrets.token_urlsafe(32)}"
    key_hash = hashlib.sha256(key.encode()).hexdigest()
    return key, key_hash


def hash_api_key(key: str) -> str:
    """Hash an API key for storage."""
    return hashlib.sha256(key.encode()).hexdigest()


def verify_api_key(key: str, key_hash: str) -> bool:
    """Verify an API key against its hash."""
    return hash_api_key(key) == key_hash
