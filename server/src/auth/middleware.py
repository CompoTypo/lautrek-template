"""Authentication middleware."""
import logging
from dataclasses import dataclass
from typing import Optional
from fastapi import Depends, HTTPException, Request
from .api_keys import verify_api_key

logger = logging.getLogger(__name__)

@dataclass
class APIKeyInfo:
    user_id: str
    email: str
    tier: str

def extract_api_key(request: Request) -> Optional[str]:
    api_key = request.headers.get("X-API-Key")
    if api_key:
        return api_key
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[7:]
    return None

def extract_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    return request.client.host if request.client else "unknown"

async def require_auth(request: Request) -> APIKeyInfo:
    api_key = extract_api_key(request)
    if not api_key:
        raise HTTPException(status_code=401, detail={"error": "Missing API key"})
    user_info = verify_api_key(api_key)
    if not user_info:
        raise HTTPException(status_code=403, detail={"error": "Invalid API key"})
    request.state.user_id = user_info["user_id"]
    request.state.tier = user_info["tier"]
    return APIKeyInfo(user_id=user_info["user_id"], email=user_info["email"], tier=user_info["tier"])

def require_tier(min_tier: str):
    tier_order = {"free": 0, "pro": 1, "enterprise": 2}
    async def check_tier(user: APIKeyInfo = Depends(require_auth)) -> APIKeyInfo:
        if tier_order.get(user.tier, 0) < tier_order.get(min_tier, 0):
            raise HTTPException(status_code=403, detail={"error": f"Requires {min_tier} tier"})
        return user
    return check_tier
