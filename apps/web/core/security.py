# Licensed under the PolyForm Noncommercial License 1.0.0
from __future__ import annotations

import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt

from .config import WebConfig


def create_jwt(username: str, config: WebConfig) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": username,
        "iat": now,
        "exp": now + timedelta(hours=config.jwt_expiration_hours),
    }
    return jwt.encode(payload, config.jwt_secret, algorithm=config.jwt_algorithm)


def decode_jwt(token: str, config: WebConfig) -> Optional[str]:
    try:
        payload = jwt.decode(
            token,
            config.jwt_secret,
            algorithms=[config.jwt_algorithm],
            options={"verify_exp": True},
        )
        return payload.get("sub")
    except JWTError:
        return None


def generate_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def validate_csrf(request_token: Optional[str], cookie_token: Optional[str]) -> bool:
    if not request_token or not cookie_token:
        return False
    return hmac.compare_digest(request_token, cookie_token)
