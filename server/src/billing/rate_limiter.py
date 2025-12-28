"""Rate limiting by subscription tier."""
import logging
from datetime import datetime
from typing import NamedTuple
from fastapi import HTTPException, Request
from src.db.connection import get_db

logger = logging.getLogger(__name__)
TIER_LIMITS = {"free": 100, "pro": 5_000, "enterprise": float("inf")}
DAILY_LIMITS = {"free": 20, "pro": 500, "enterprise": float("inf")}

class UsageInfo(NamedTuple):
    user_id: str
    year_month: str
    operation_count: int
    limit: int
    remaining: int
    is_limited: bool

def get_current_period() -> str:
    return datetime.utcnow().strftime("%Y-%m")

def get_usage(user_id: str, tier: str) -> UsageInfo:
    year_month = get_current_period()
    limit = TIER_LIMITS.get(tier, TIER_LIMITS["free"])
    db = get_db()
    cursor = db.execute("SELECT operation_count FROM usage WHERE user_id = ? AND year_month = ?", (user_id, year_month))
    row = cursor.fetchone()
    count = row["operation_count"] if row else 0
    remaining = max(0, int(limit - count)) if limit != float("inf") else -1
    is_limited = count >= limit if limit != float("inf") else False
    return UsageInfo(user_id=user_id, year_month=year_month, operation_count=count, limit=int(limit) if limit != float("inf") else -1, remaining=remaining, is_limited=is_limited)

def increment_usage(user_id: str, operations: int = 1) -> int:
    year_month = get_current_period()
    now = datetime.utcnow().isoformat()
    db = get_db()
    cursor = db.execute("UPDATE usage SET operation_count = operation_count + ?, last_operation_at = ? WHERE user_id = ? AND year_month = ?", (operations, now, user_id, year_month))
    if cursor.rowcount == 0:
        db.execute("INSERT INTO usage (user_id, year_month, operation_count, last_operation_at) VALUES (?, ?, ?, ?)", (user_id, year_month, operations, now))
    db.commit()
    cursor = db.execute("SELECT operation_count FROM usage WHERE user_id = ? AND year_month = ?", (user_id, year_month))
    row = cursor.fetchone()
    return row["operation_count"] if row else operations

def check_rate_limit(user_id: str, tier: str) -> tuple[bool, UsageInfo]:
    usage = get_usage(user_id, tier)
    return not usage.is_limited, usage

def require_rate_limit(request: Request) -> UsageInfo:
    if not hasattr(request.state, "user_id"):
        raise HTTPException(status_code=401, detail="Authentication required")
    user_id = request.state.user_id
    tier = getattr(request.state, "tier", "free")
    allowed, usage = check_rate_limit(user_id, tier)
    if not allowed:
        raise HTTPException(status_code=429, detail={"error": "Rate limit exceeded", "limit": usage.limit, "used": usage.operation_count})
    new_count = increment_usage(user_id)
    return UsageInfo(user_id=user_id, year_month=usage.year_month, operation_count=new_count, limit=usage.limit, remaining=max(0, usage.limit - new_count) if usage.limit != -1 else -1, is_limited=False)

def get_usage_stats(user_id: str, tier: str) -> dict:
    usage = get_usage(user_id, tier)
    limit = TIER_LIMITS.get(tier, TIER_LIMITS["free"])
    return {"tier": tier, "period": usage.year_month, "operations": {"used": usage.operation_count, "limit": usage.limit, "remaining": usage.remaining}, "is_limited": usage.is_limited}

def reset_usage(user_id: str, year_month: str | None = None) -> bool:
    if year_month is None:
        year_month = get_current_period()
    db = get_db()
    cursor = db.execute("DELETE FROM usage WHERE user_id = ? AND year_month = ?", (user_id, year_month))
    db.commit()
    return cursor.rowcount > 0
