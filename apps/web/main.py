"""
CuraFrame Web Application — FastAPI entry point

Routes:
  GET  /            → redirect to /dashboard or /login
  GET  /dashboard   → dashboard HTML page (requires login)
  GET  /calculator  → calculator form (requires login)
  POST /calculator  → evaluate candidate properties (requires login)
  POST /logs/record → save a calculator result to the user's log (requires login)
  GET  /logs        → view the current user's log history (requires login)
  GET  /register    → registration form
  POST /register    → create new user account
  GET  /login       → login form
  POST /login       → authenticate and create session
  GET  /logout      → destroy session and redirect to /login
"""

from __future__ import annotations

import hashlib
import os
import secrets
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import Cookie, FastAPI, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

_TEMPLATE_DIR = Path(__file__).parent / "templates"

# Database path – override via CURAFRAME_DB env variable (useful in tests)
_DEFAULT_DB = Path(__file__).parent.parent.parent / "curaframe.db"
DB_PATH = os.environ.get("CURAFRAME_DB", str(_DEFAULT_DB))

# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def _get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _init_db(db_path: str = DB_PATH) -> None:
    """Create the users and logs tables if they do not already exist."""
    conn = _get_connection(db_path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            username      TEXT    UNIQUE NOT NULL,
            email         TEXT    UNIQUE NOT NULL,
            password_hash TEXT           NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS logs (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            username          TEXT    NOT NULL,
            timestamp         TEXT    NOT NULL,
            logP              REAL,
            hERG_IC50         REAL,
            beta1_selectivity REAL,
            bundle            TEXT,
            status            TEXT
        )
        """
    )
    conn.commit()
    conn.close()


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

def create_app(db_path: Optional[str] = None) -> FastAPI:
    """
    Create and return a configured FastAPI application.

    Parameters
    ----------
    db_path:
        Path to the SQLite database file.  Defaults to the module-level
        ``DB_PATH`` (which respects the ``CURAFRAME_DB`` env variable).
    """
    resolved_db = db_path or DB_PATH
    _init_db(resolved_db)

    app = FastAPI(title="CuraFrame")
    templates = Jinja2Templates(directory=str(_TEMPLATE_DIR))
    # In-memory session store scoped to this app instance: {token: username}
    sessions: dict[str, str] = {}

    # ------------------------------------------------------------------
    # Auth helpers (scoped to this app instance)
    # ------------------------------------------------------------------

    def _current_user(session: Optional[str]) -> Optional[str]:
        if session and session in sessions:
            return sessions[session]
        return None

    # ------------------------------------------------------------------
    # Routes
    # ------------------------------------------------------------------

    @app.get("/", response_class=HTMLResponse)
    async def home(session: Optional[str] = Cookie(default=None)):
        if _current_user(session):
            return RedirectResponse("/dashboard", status_code=status.HTTP_302_FOUND)
        return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)

    # ---- Dashboard -------------------------------------------------------

    @app.get("/dashboard", response_class=HTMLResponse)
    async def dashboard(
        request: Request,
        session: Optional[str] = Cookie(default=None),
    ):
        user = _current_user(session)
        if not user:
            return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)
        return templates.TemplateResponse(
            request, "dashboard.html", {"user": user}
        )

    # ---- Calculator ------------------------------------------------------

    @app.get("/calculator", response_class=HTMLResponse)
    async def calculator_get(
        request: Request,
        session: Optional[str] = Cookie(default=None),
    ):
        user = _current_user(session)
        if not user:
            return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)
        return templates.TemplateResponse(
            request,
            "calculator.html",
            {"user": user, "result": None, "error": None},
        )

    @app.post("/calculator", response_class=HTMLResponse)
    async def calculator_post(
        request: Request,
        session: Optional[str] = Cookie(default=None),
        logP: float = Form(default=0.0),
        hERG_IC50: float = Form(default=0.0),
        beta1_selectivity: float = Form(default=0.0),
        bundle: str = Form(default="core-safety"),
    ):
        user = _current_user(session)
        if not user:
            return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)

        from cura_frame import Candidate
        from cura_frame.cli import evaluate_candidate

        try:
            candidate = Candidate(
                name="web_calculator",
                properties={
                    "logP": logP,
                    "hERG_IC50": hERG_IC50,
                    "beta1_selectivity": beta1_selectivity,
                },
            )
            result = evaluate_candidate(
                candidate=candidate,
                bundle_name=bundle,
                population=None,
                strict=False,
            )
            return templates.TemplateResponse(
                request,
                "calculator.html",
                {
                    "user": user,
                    "result": result,
                    "bundle": bundle,
                    "error": None,
                    "logP": logP,
                    "hERG_IC50": hERG_IC50,
                    "beta1_selectivity": beta1_selectivity,
                },
            )
        except Exception as exc:  # noqa: BLE001
            return templates.TemplateResponse(
                request,
                "calculator.html",
                {
                    "user": user,
                    "result": None,
                    "error": str(exc),
                    "bundle": bundle,
                    "logP": logP,
                    "hERG_IC50": hERG_IC50,
                    "beta1_selectivity": beta1_selectivity,
                },
            )

    # ---- Log recording ---------------------------------------------------

    @app.post("/logs/record", response_class=HTMLResponse)
    async def logs_record(
        request: Request,
        session: Optional[str] = Cookie(default=None),
        logP: float = Form(default=0.0),
        hERG_IC50: float = Form(default=0.0),
        beta1_selectivity: float = Form(default=0.0),
        bundle: str = Form(default="core-safety"),
        status_val: str = Form(default=""),
    ):
        user = _current_user(session)
        if not user:
            return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)

        conn = _get_connection(resolved_db)
        conn.execute(
            """
            INSERT INTO logs (username, timestamp, logP, hERG_IC50, beta1_selectivity, bundle, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user,
                datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
                logP,
                hERG_IC50,
                beta1_selectivity,
                bundle,
                status_val,
            ),
        )
        conn.commit()
        conn.close()
        return RedirectResponse("/logs", status_code=status.HTTP_302_FOUND)

    @app.get("/logs", response_class=HTMLResponse)
    async def logs_get(
        request: Request,
        session: Optional[str] = Cookie(default=None),
    ):
        user = _current_user(session)
        if not user:
            return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)

        conn = _get_connection(resolved_db)
        rows = conn.execute(
            """
            SELECT id, timestamp, logP, hERG_IC50, beta1_selectivity, bundle, status
            FROM logs
            WHERE username = ?
            ORDER BY id DESC
            """,
            (user,),
        ).fetchall()
        conn.close()
        return templates.TemplateResponse(
            request,
            "logs.html",
            {"user": user, "logs": [dict(r) for r in rows]},
        )

    # ---- Register --------------------------------------------------------

    @app.get("/register", response_class=HTMLResponse)
    async def register_get(request: Request):
        return templates.TemplateResponse(
            request, "register.html", {"error": None}
        )

    @app.post("/register", response_class=HTMLResponse)
    async def register_post(
        request: Request,
        username: str = Form(...),
        email: str = Form(...),
        password: str = Form(...),
    ):
        if not username or not email or not password:
            return templates.TemplateResponse(
                request,
                "register.html",
                {"error": "All fields are required."},
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        conn = _get_connection(resolved_db)
        try:
            conn.execute(
                "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                (username.strip(), email.strip(), _hash_password(password)),
            )
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return templates.TemplateResponse(
                request,
                "register.html",
                {"error": "Username or email is already registered."},
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        else:
            conn.close()
            return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)

    # ---- Login -----------------------------------------------------------

    @app.get("/login", response_class=HTMLResponse)
    async def login_get(request: Request):
        return templates.TemplateResponse(
            request, "login.html", {"error": None}
        )

    @app.post("/login", response_class=HTMLResponse)
    async def login_post(
        request: Request,
        username: str = Form(...),
        password: str = Form(...),
    ):
        conn = _get_connection(resolved_db)
        row = conn.execute(
            "SELECT username FROM users WHERE username = ? AND password_hash = ?",
            (username.strip(), _hash_password(password)),
        ).fetchone()
        conn.close()

        if row is None:
            return templates.TemplateResponse(
                request,
                "login.html",
                {"error": "Invalid username or password."},
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        token = secrets.token_urlsafe(32)
        sessions[token] = row["username"]

        response = RedirectResponse("/dashboard", status_code=status.HTTP_302_FOUND)
        response.set_cookie("session", token, httponly=True, samesite="lax")
        return response

    # ---- Logout ----------------------------------------------------------

    @app.get("/logout")
    async def logout(session: Optional[str] = Cookie(default=None)):
        if session and session in sessions:
            del sessions[session]
        response = RedirectResponse("/login", status_code=status.HTTP_302_FOUND)
        response.delete_cookie("session")
        return response

    return app


# ---------------------------------------------------------------------------
# Module-level app instance (used by uvicorn / render.yaml)
# ---------------------------------------------------------------------------

app = create_app()
