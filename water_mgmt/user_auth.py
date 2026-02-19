"""Email+password authentication using JWT.

This is separate from the existing API-key auth (auth.py). In production, you should set:
- RICE_JWT_SECRET
- RICE_USER_AUTH_MODE=required
"""

import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

import jwt
from fastapi import HTTPException, Security, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext


JWT_SECRET = os.getenv("RICE_JWT_SECRET", "dev-secret-change-me")
JWT_ALG = os.getenv("RICE_JWT_ALG", "HS256")
JWT_EXPIRES_HOURS = int(os.getenv("RICE_JWT_EXPIRES_HOURS", "168"))  # 7 days
USER_AUTH_MODE = os.getenv("RICE_USER_AUTH_MODE", "optional")  # optional|required

_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
_bearer = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return _pwd.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return _pwd.verify(password, password_hash)


def create_access_token(user_id: str, email: str) -> str:
    now = datetime.utcnow()
    payload = {
        "sub": user_id,
        "email": email,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=JWT_EXPIRES_HOURS)).timestamp()),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)


def decode_token(token: str) -> Dict[str, Any]:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def get_current_user(
    request: Request,
    creds: Optional[HTTPAuthorizationCredentials] = Security(_bearer),
):
    """Return user dict (id,email) or None in optional mode."""

    if creds is None or not creds.credentials:
        if USER_AUTH_MODE == "required":
            raise HTTPException(status_code=401, detail="Login required")
        return None

    payload = decode_token(creds.credentials)
    return {"user_id": payload.get("sub"), "email": payload.get("email")}
