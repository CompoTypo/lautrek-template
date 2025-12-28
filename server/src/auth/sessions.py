"""Session management."""
import hashlib
import secrets
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Request, Response
from src.config import settings
from src.db.connection import get_db

SESSION_COOKIE_NAME = "app_session"
SESSION_DURATION_HOURS = 24
REMEMBER_ME_DURATION_DAYS = 30

@dataclass
class Session:
    id: str
    user_id: str
    expires_at: str
    @property
    def is_expired(self) -> bool:
        return datetime.fromisoformat(self.expires_at) < datetime.utcnow()

def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()

def create_session(user_id: str, request: Request, remember_me: bool = False) -> tuple[str, str]:
    db = get_db()
    now = datetime.utcnow()
    session_id = str(uuid.uuid4())
    session_token = secrets.token_urlsafe(32)
    token_hash = _hash_token(session_token)
    expires_at = now + (timedelta(days=REMEMBER_ME_DURATION_DAYS) if remember_me else timedelta(hours=SESSION_DURATION_HOURS))
    ip_address = request.client.host if request.client else None
    db.execute(
        "INSERT INTO sessions (id, user_id, token_hash, created_at, expires_at, last_active_at, ip_address, is_remember_me) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (session_id, user_id, token_hash, now.isoformat(), expires_at.isoformat(), now.isoformat(), ip_address, 1 if remember_me else 0),
    )
    db.commit()
    return session_id, session_token

def validate_session(token: str) -> Optional[Session]:
    if not token:
        return None
    token_hash = _hash_token(token)
    db = get_db()
    cursor = db.execute("SELECT id, user_id, expires_at FROM sessions WHERE token_hash = ?", (token_hash,))
    row = cursor.fetchone()
    if not row:
        return None
    session = Session(id=row["id"], user_id=row["user_id"], expires_at=row["expires_at"])
    if session.is_expired:
        delete_session(session.id)
        return None
    db.execute("UPDATE sessions SET last_active_at = ? WHERE id = ?", (datetime.utcnow().isoformat(), session.id))
    db.commit()
    return session

def delete_session(session_id: str) -> bool:
    db = get_db()
    cursor = db.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
    db.commit()
    return cursor.rowcount > 0

def set_session_cookie(response: Response, session_token: str, remember_me: bool = False) -> None:
    max_age = REMEMBER_ME_DURATION_DAYS * 86400 if remember_me else SESSION_DURATION_HOURS * 3600
    response.set_cookie(key=SESSION_COOKIE_NAME, value=session_token, max_age=max_age, httponly=True, secure=settings.is_production, samesite="lax", path="/")

def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(key=SESSION_COOKIE_NAME, path="/")
