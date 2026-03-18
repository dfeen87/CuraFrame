from __future__ import annotations

from typing import Optional

from fastapi import Cookie, Depends, Request

from apps.web.db.database import get_db


def get_current_user(
    request: Request,
    session: Optional[str] = Cookie(default=None),
) -> Optional[str]:
    if not session:
        return None
    return request.app.state.decode_jwt(session)


def require_user(user: Optional[str] = Depends(get_current_user)) -> str | None:
    return user

__all__ = ["get_current_user", "get_db", "require_user"]
