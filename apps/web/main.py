# Licensed under the PolyForm Noncommercial License 1.0.0
"""CuraFrame Web Application — FastAPI entry point."""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import FastAPI
from fastapi.templating import Jinja2Templates

from apps.web.api import auth_router, logs_router, pages_router
from apps.web.core.config import _TEMPLATE_DIR, load_config
from apps.web.core.security import create_jwt, decode_jwt, generate_csrf_token, validate_csrf
from apps.web.db.database import close_database, configure_database, init_db
from cura_frame.db import execute, fetchall, fetchone, get_connection, hash_password, verify_password

logger = logging.getLogger(__name__)

JWT_SECRET: str = load_config().jwt_secret
_JWT_ALGORITHM = load_config().jwt_algorithm


def _create_jwt(username: str) -> str:
    return create_jwt(username, load_config())


def _decode_jwt(token: str) -> Optional[str]:
    return decode_jwt(token, load_config())


def create_app(db_path: Optional[str] = None) -> FastAPI:
    config = load_config(db_path)
    init_db(config.db_path)

    app = FastAPI(title="CuraFrame")
    templates = Jinja2Templates(directory=str(_TEMPLATE_DIR))
    app.state.templates = templates
    app.state.config = config
    app.state.db_path = config.db_path
    app.state.create_jwt = lambda username: create_jwt(username, config)
    app.state.decode_jwt = lambda token: decode_jwt(token, config)
    app.state.generate_csrf_token = generate_csrf_token
    app.state.validate_csrf = validate_csrf

    @app.on_event("startup")
    def startup_event() -> None:
        configure_database(app, config)

    @app.on_event("shutdown")
    def shutdown_event() -> None:
        close_database(app)

    @app.middleware("http")
    async def add_security_headers(request, call_next):
        response = await call_next(request)
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; frame-ancestors 'none';"
        )
        return response

    app.include_router(pages_router)
    app.include_router(logs_router)
    app.include_router(auth_router)
    return app


app = create_app()
