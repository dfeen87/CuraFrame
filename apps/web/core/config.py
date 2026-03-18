from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


_TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"
_DEFAULT_DB = Path(__file__).resolve().parents[3] / "curaframe.db"


@dataclass(frozen=True)
class WebConfig:
    db_path: str
    secure_cookies: bool
    min_password_length: int
    max_username_length: int
    max_email_length: int
    max_password_length: int
    username_min_length: int
    jwt_secret: str
    jwt_algorithm: str
    jwt_expiration_hours: int


def load_config(db_path: str | None = None) -> WebConfig:
    configured_db_path = (
        db_path
        or os.environ.get("CURAFRAME_DATABASE_URL")
        or os.environ.get("DATABASE_URL")
        or os.environ.get("CURAFRAME_DB", str(_DEFAULT_DB))
    )
    jwt_secret = os.environ.get("JWT_SECRET")
    if jwt_secret is None:
        raise RuntimeError("JWT_SECRET environment variable is not set")

    return WebConfig(
        db_path=configured_db_path,
        secure_cookies=os.environ.get("CURAFRAME_SECURE_COOKIES", "0").lower() in {"1", "true", "yes"},
        min_password_length=8,
        max_username_length=64,
        max_email_length=254,
        max_password_length=128,
        username_min_length=3,
        jwt_secret=jwt_secret,
        jwt_algorithm="HS256",
        jwt_expiration_hours=int(os.environ.get("CURAFRAME_JWT_EXPIRATION_HOURS", "24")),
    )
