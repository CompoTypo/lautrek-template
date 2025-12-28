"""SQLite database connection."""
import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional
from src.config import settings

logger = logging.getLogger(__name__)
_connection: Optional[sqlite3.Connection] = None

def get_db() -> sqlite3.Connection:
    global _connection
    if _connection is None:
        _connection = init_db()
    return _connection

def init_db(run_schema: bool = True) -> sqlite3.Connection:
    db_path = settings.db_path
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    if run_schema:
        _init_schema(conn)
    logger.info(f"Database initialized at {db_path}")
    return conn

def _init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY, email TEXT UNIQUE NOT NULL, password_hash TEXT,
            api_key_hash TEXT UNIQUE NOT NULL, tier TEXT NOT NULL DEFAULT 'free',
            email_verified INTEGER DEFAULT 0, verification_token TEXT, verification_expires_at TEXT,
            reset_token TEXT, reset_expires_at TEXT, stripe_customer_id TEXT,
            stripe_subscription_id TEXT, subscription_status TEXT, last_active_at TEXT,
            is_admin INTEGER DEFAULT 0, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY, user_id TEXT NOT NULL, token_hash TEXT NOT NULL,
            created_at TEXT NOT NULL, expires_at TEXT NOT NULL, last_active_at TEXT,
            ip_address TEXT, device_name TEXT, is_remember_me INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL,
            year_month TEXT NOT NULL, operation_count INTEGER DEFAULT 0, last_operation_at TEXT,
            UNIQUE(user_id, year_month), FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT NOT NULL, user_id TEXT,
            action TEXT NOT NULL, resource_type TEXT, resource_id TEXT, details TEXT, ip_address TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
        CREATE INDEX IF NOT EXISTS idx_users_api_key_hash ON users(api_key_hash);
        CREATE INDEX IF NOT EXISTS idx_sessions_token_hash ON sessions(token_hash);
        CREATE INDEX IF NOT EXISTS idx_usage_user_month ON usage(user_id, year_month);
    """)
    conn.commit()

def log_audit(action: str, user_id: Optional[str] = None, resource_type: Optional[str] = None, resource_id: Optional[str] = None, details: Optional[dict] = None, ip_address: Optional[str] = None) -> None:
    db = get_db()
    db.execute("INSERT INTO audit_log (timestamp, user_id, action, resource_type, resource_id, details, ip_address) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (datetime.utcnow().isoformat(), user_id, action, resource_type, resource_id, json.dumps(details) if details else None, ip_address))
    db.commit()
