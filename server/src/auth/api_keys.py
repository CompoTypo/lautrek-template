"""API key generation and validation."""
import hashlib
import secrets
from typing import Optional
from src.config import settings
from src.db.connection import get_db

API_KEY_LENGTH = 32

def generate_api_key() -> str:
    """Generate a new API key with configured prefix."""
    token = secrets.token_urlsafe(API_KEY_LENGTH)
    return f"{settings.api_key_prefix}{token}"

def hash_api_key(api_key: str) -> str:
    """Hash an API key for secure storage."""
    return hashlib.sha256(api_key.encode()).hexdigest()

def verify_api_key(api_key: str) -> Optional[dict]:
    """Verify an API key and return user info if valid."""
    if not api_key or not api_key.startswith(settings.api_key_prefix):
        return None
    if len(api_key) < len(settings.api_key_prefix) + 40:
        return None

    key_hash = hash_api_key(api_key)
    db = get_db()
    cursor = db.execute(
        "SELECT id, email, tier, email_verified FROM users WHERE api_key_hash = ?",
        (key_hash,),
    )
    row = cursor.fetchone()
    if not row or not row["email_verified"]:
        return None
    return {"user_id": row["id"], "email": row["email"], "tier": row["tier"]}
