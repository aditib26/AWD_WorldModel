"""Authentication and rate limiting middleware"""

import os
import time
import hashlib
import secrets
from typing import Optional
from collections import defaultdict
from fastapi import HTTPException, Security, Request
from fastapi.security import APIKeyHeader

# API key header
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

# Valid API keys loaded from environment or generated
# In production: set RICE_API_KEYS="key1,key2,key3"
_raw_keys = os.getenv("RICE_API_KEYS", "")
VALID_API_KEYS = set(k.strip() for k in _raw_keys.split(",") if k.strip())

# If no keys configured, generate a dev key and print it
if not VALID_API_KEYS:
    dev_key = "dev-" + secrets.token_hex(16)
    VALID_API_KEYS.add(dev_key)
    print(f"⚠️  No RICE_API_KEYS set. Dev key: {dev_key}")
    print(f"   Set RICE_API_KEYS env var for production.")

# Auth mode: "required" or "optional" (for dev)
AUTH_MODE = os.getenv("RICE_AUTH_MODE", "optional")


async def verify_api_key(
    request: Request,
    api_key: Optional[str] = Security(API_KEY_HEADER)
) -> Optional[str]:
    """Verify API key. In optional mode, allows unauthenticated access."""
    
    if AUTH_MODE == "optional":
        # Dev mode: allow all requests, but track key if provided
        return api_key or "anonymous"
    
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing API key. Set X-API-Key header."
        )
    
    if api_key not in VALID_API_KEYS:
        raise HTTPException(
            status_code=403,
            detail="Invalid API key."
        )
    
    return api_key


class RateLimiter:
    """Simple in-memory rate limiter per API key / IP."""
    
    def __init__(self, requests_per_minute: int = 30, burst: int = 10):
        self.rpm = requests_per_minute
        self.burst = burst
        self._requests = defaultdict(list)  # key -> [timestamps]
    
    def check(self, key: str) -> bool:
        """Returns True if request is allowed, False if rate limited."""
        now = time.time()
        window = 60.0  # 1 minute
        
        # Clean old entries
        self._requests[key] = [
            t for t in self._requests[key] if now - t < window
        ]
        
        if len(self._requests[key]) >= self.rpm:
            return False
        
        # Check burst (last 5 seconds)
        recent = [t for t in self._requests[key] if now - t < 5.0]
        if len(recent) >= self.burst:
            return False
        
        self._requests[key].append(now)
        return True
    
    def get_remaining(self, key: str) -> int:
        now = time.time()
        recent = [t for t in self._requests.get(key, []) if now - t < 60.0]
        return max(0, self.rpm - len(recent))


# Global rate limiter
rate_limiter = RateLimiter(
    requests_per_minute=int(os.getenv("RICE_RATE_LIMIT_RPM", "30")),
    burst=int(os.getenv("RICE_RATE_LIMIT_BURST", "10"))
)
