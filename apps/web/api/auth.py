# Licensed under the PolyForm Noncommercial License 1.0.0
from __future__ import annotations

import logging
import re
import sqlite3
from typing import Optional

from fastapi import APIRouter, Cookie, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse

from apps.web.core.dependencies import get_db
from cura_frame.db import execute, fetchone, hash_password, verify_password, is_postgres

try:
    import psycopg
except ImportError:  # pragma: no cover
    psycopg = None

logger = logging.getLogger(__name__)
router = APIRouter()
_USERNAME_RE = re.compile(r"^[A-Za-z0-9_]+$")
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@router.get("/register", response_class=HTMLResponse)
def register_get(request: Request):
    csrf_token = request.app.state.generate_csrf_token()
    response = request.app.state.templates.TemplateResponse(
        request, "register.html", {"error": None, "csrf_token": csrf_token}
    )
    response.set_cookie(
        "csrf_token", csrf_token, httponly=False, samesite="lax", secure=request.app.state.config.secure_cookies
    )
    return response


@router.post("/register", response_class=HTMLResponse)
def register_post(
    request: Request,
    db=Depends(get_db),
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    csrf_token: str = Form(default=""),
    csrf_token_cookie: Optional[str] = Cookie(default=None, alias="csrf_token"),
):
    config = request.app.state.config
    if not request.app.state.validate_csrf(csrf_token, csrf_token_cookie):
        return request.app.state.templates.TemplateResponse(
            request,
            "register.html",
            {"error": "Invalid or missing CSRF token.", "csrf_token": ""},
            status_code=status.HTTP_403_FORBIDDEN,
        )
    username = username.strip()
    email = email.strip()
    if not username or not email or not password:
        return request.app.state.templates.TemplateResponse(request, "register.html", {"error": "All fields are required.", "csrf_token": csrf_token}, status_code=status.HTTP_400_BAD_REQUEST)
    if not (config.username_min_length <= len(username) <= config.max_username_length):
        return request.app.state.templates.TemplateResponse(request, "register.html", {"error": f"Username must be {config.username_min_length}–{config.max_username_length} characters.", "csrf_token": csrf_token}, status_code=status.HTTP_400_BAD_REQUEST)
    if not _USERNAME_RE.match(username):
        return request.app.state.templates.TemplateResponse(request, "register.html", {"error": "Username may only contain letters, digits, and underscores.", "csrf_token": csrf_token}, status_code=status.HTTP_400_BAD_REQUEST)
    if len(email) > config.max_email_length or not _EMAIL_RE.match(email):
        return request.app.state.templates.TemplateResponse(request, "register.html", {"error": "Invalid email address.", "csrf_token": csrf_token}, status_code=status.HTTP_400_BAD_REQUEST)
    if len(password) < config.min_password_length:
        return request.app.state.templates.TemplateResponse(request, "register.html", {"error": f"Password must be at least {config.min_password_length} characters.", "csrf_token": csrf_token}, status_code=status.HTTP_400_BAD_REQUEST)
    if len(password) > config.max_password_length:
        return request.app.state.templates.TemplateResponse(request, "register.html", {"error": f"Password must be at most {config.max_password_length} characters.", "csrf_token": csrf_token}, status_code=status.HTTP_400_BAD_REQUEST)

    integrity_errors = (sqlite3.IntegrityError,)
    if is_postgres(request.app.state.db_path) and psycopg is not None:
        integrity_errors = (sqlite3.IntegrityError, psycopg.IntegrityError)
    try:
        execute(db, request.app.state.db_path, "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)", (username, email, hash_password(password)))
        db.commit()
    except integrity_errors:
        return request.app.state.templates.TemplateResponse(request, "register.html", {"error": "Username or email is already registered.", "csrf_token": csrf_token}, status_code=status.HTTP_400_BAD_REQUEST)
    return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)


@router.get("/login", response_class=HTMLResponse)
def login_get(request: Request):
    csrf_token = request.app.state.generate_csrf_token()
    response = request.app.state.templates.TemplateResponse(request, "login.html", {"error": None, "csrf_token": csrf_token})
    response.set_cookie("csrf_token", csrf_token, httponly=False, samesite="lax", secure=request.app.state.config.secure_cookies)
    return response


@router.post("/login", response_class=HTMLResponse)
def login_post(
    request: Request,
    db=Depends(get_db),
    username: str = Form(...),
    password: str = Form(...),
    csrf_token: str = Form(default=""),
    csrf_token_cookie: Optional[str] = Cookie(default=None, alias="csrf_token"),
):
    if not request.app.state.validate_csrf(csrf_token, csrf_token_cookie):
        return request.app.state.templates.TemplateResponse(request, "login.html", {"error": "Invalid or missing CSRF token.", "csrf_token": ""}, status_code=status.HTTP_403_FORBIDDEN)
    row = fetchone(db, request.app.state.db_path, "SELECT username, password_hash FROM users WHERE username = ?", (username.strip(),))
    if row is None or not verify_password(password, row["password_hash"]):
        return request.app.state.templates.TemplateResponse(request, "login.html", {"error": "Invalid username or password.", "csrf_token": csrf_token}, status_code=status.HTTP_401_UNAUTHORIZED)
    token = request.app.state.create_jwt(row["username"])
    response = RedirectResponse("/dashboard", status_code=status.HTTP_302_FOUND)
    response.set_cookie("session", token, httponly=True, samesite="lax", secure=request.app.state.config.secure_cookies)
    return response


@router.get("/logout")
def logout():
    response = RedirectResponse("/login", status_code=status.HTTP_302_FOUND)
    response.delete_cookie("session")
    return response
