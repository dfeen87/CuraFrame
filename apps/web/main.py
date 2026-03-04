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
import hmac
import json
import os
import secrets
import sqlite3
from contextlib import closing
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from fastapi import Cookie, FastAPI, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from jose import JWTError, jwt

try:
    import psycopg
except ImportError:  # pragma: no cover - optional dependency at runtime
    psycopg = None

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

_TEMPLATE_DIR = Path(__file__).parent / "templates"

# Database path – override via CURAFRAME_DATABASE_URL (PostgreSQL) or CURAFRAME_DB (SQLite)
_DEFAULT_DB = Path(__file__).parent.parent.parent / "curaframe.db"
DB_PATH = os.environ.get("CURAFRAME_DATABASE_URL") or os.environ.get(
    "CURAFRAME_DB", str(_DEFAULT_DB)
)

# Set to "1"/"true"/"yes" in production (HTTPS) to mark the session cookie secure
_SECURE_COOKIES = os.environ.get("CURAFRAME_SECURE_COOKIES", "0").lower() in (
    "1", "true", "yes"
)

# Minimum acceptable password length for new registrations
_MIN_PASSWORD_LENGTH = 8

# Maximum acceptable input lengths (to prevent DoS via extreme-length strings)
_MAX_USERNAME_LENGTH = 64
_MAX_EMAIL_LENGTH = 254
_MAX_PASSWORD_LENGTH = 128

# Username validation: 3–64 alphanumeric + underscore characters
import re as _re
_USERNAME_MIN_LENGTH = 3
_USERNAME_RE = _re.compile(r"^[A-Za-z0-9_]+$")
_EMAIL_RE = _re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# PBKDF2-HMAC-SHA256 iteration count (OWASP 2023 recommendation)
_PBKDF2_ITERATIONS = 260_000

# JWT configuration – set JWT_SECRET in the environment before deploying.
# If not set, a per-process random secret is used (tokens are invalidated on restart).
JWT_SECRET: str = os.environ.get("JWT_SECRET", secrets.token_urlsafe(32))
_JWT_ALGORITHM = "HS256"

# JWT expiration window (hours). Override via CURAFRAME_JWT_EXPIRATION_HOURS.
JWT_EXPIRATION_HOURS: int = int(
    os.environ.get("CURAFRAME_JWT_EXPIRATION_HOURS", "24")
)

# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def _is_postgres(db_path: str) -> bool:
    return db_path.startswith("postgresql://") or db_path.startswith("postgres://")


def _get_connection(db_path: str = DB_PATH):
    if _is_postgres(db_path):
        if psycopg is None:
            raise RuntimeError(
                "PostgreSQL connection requested but psycopg is not installed. "
                "Install it with `pip install psycopg[binary]`."
            )
        return psycopg.connect(db_path)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _adapt_query(query: str, db_path: str) -> str:
    if _is_postgres(db_path):
        return query.replace("?", "%s")
    return query


def _execute(conn, db_path: str, query: str, params: tuple = ()):
    if _is_postgres(db_path):
        with closing(conn.cursor()) as cur:
            cur.execute(_adapt_query(query, db_path), params)
            return cur.rowcount
    return conn.execute(query, params)


def _fetchone(conn, db_path: str, query: str, params: tuple = ()):
    if _is_postgres(db_path):
        with closing(conn.cursor()) as cur:
            cur.execute(_adapt_query(query, db_path), params)
            row = cur.fetchone()
            if row is None:
                return None
            columns = [desc.name for desc in cur.description]
            return dict(zip(columns, row))

    return conn.execute(query, params).fetchone()


def _fetchall(conn, db_path: str, query: str, params: tuple = ()):
    if _is_postgres(db_path):
        with closing(conn.cursor()) as cur:
            cur.execute(_adapt_query(query, db_path), params)
            rows = cur.fetchall()
            columns = [desc.name for desc in cur.description]
            return [dict(zip(columns, row)) for row in rows]

    return conn.execute(query, params).fetchall()


def _init_db(db_path: str = DB_PATH) -> None:
    """Create the users and logs tables if they do not already exist."""
    conn = _get_connection(db_path)
    try:
        if _is_postgres(db_path):
            _execute(
                conn,
                db_path,
                """
                CREATE TABLE IF NOT EXISTS users (
                    id            BIGSERIAL PRIMARY KEY,
                    username      TEXT UNIQUE NOT NULL,
                    email         TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL
                )
                """,
            )
            _execute(
                conn,
                db_path,
                """
                CREATE TABLE IF NOT EXISTS logs (
                    id                      BIGSERIAL PRIMARY KEY,
                    username                TEXT NOT NULL,
                    timestamp               TEXT NOT NULL,
                    logP                    DOUBLE PRECISION,
                    hERG_IC50               DOUBLE PRECISION,
                    beta1_selectivity       DOUBLE PRECISION,
                    molecular_weight        DOUBLE PRECISION,
                    polar_surface_area      DOUBLE PRECISION,
                    hydrogen_bond_donors    DOUBLE PRECISION,
                    hydrogen_bond_acceptors DOUBLE PRECISION,
                    Kd_5HT1A                DOUBLE PRECISION,
                    Kd_5HT2A                DOUBLE PRECISION,
                    Kd_D2                   DOUBLE PRECISION,
                    plasma_half_life        DOUBLE PRECISION,
                    bundle                  TEXT,
                    status                  TEXT
                )
                """,
            )
            _execute(
                conn,
                db_path,
                """
                CREATE TABLE IF NOT EXISTS form_submissions (
                    id                      BIGSERIAL PRIMARY KEY,
                    username                TEXT NOT NULL,
                    timestamp               TEXT NOT NULL,
                    logP                    DOUBLE PRECISION,
                    hERG_IC50               DOUBLE PRECISION,
                    beta1_selectivity       DOUBLE PRECISION,
                    molecular_weight        DOUBLE PRECISION,
                    polar_surface_area      DOUBLE PRECISION,
                    hydrogen_bond_donors    DOUBLE PRECISION,
                    hydrogen_bond_acceptors DOUBLE PRECISION,
                    Kd_5HT1A                DOUBLE PRECISION,
                    Kd_5HT2A                DOUBLE PRECISION,
                    Kd_D2                   DOUBLE PRECISION,
                    plasma_half_life        DOUBLE PRECISION,
                    results_json            TEXT
                )
                """,
            )
        else:
            _execute(
                conn,
                db_path,
                """
                CREATE TABLE IF NOT EXISTS users (
                    id            INTEGER PRIMARY KEY AUTOINCREMENT,
                    username      TEXT    UNIQUE NOT NULL,
                    email         TEXT    UNIQUE NOT NULL,
                    password_hash TEXT           NOT NULL
                )
                """,
            )
            _execute(
                conn,
                db_path,
                """
                CREATE TABLE IF NOT EXISTS logs (
                    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
                    username              TEXT    NOT NULL,
                    timestamp             TEXT    NOT NULL,
                    logP                  REAL,
                    hERG_IC50             REAL,
                    beta1_selectivity     REAL,
                    molecular_weight      REAL,
                    polar_surface_area    REAL,
                    hydrogen_bond_donors  REAL,
                    hydrogen_bond_acceptors REAL,
                    Kd_5HT1A              REAL,
                    Kd_5HT2A              REAL,
                    Kd_D2                 REAL,
                    plasma_half_life      REAL,
                    bundle                TEXT,
                    status                TEXT
                )
                """,
            )
            _execute(
                conn,
                db_path,
                """
                CREATE TABLE IF NOT EXISTS form_submissions (
                    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
                    username                TEXT    NOT NULL,
                    timestamp               TEXT    NOT NULL,
                    logP                    REAL,
                    hERG_IC50               REAL,
                    beta1_selectivity       REAL,
                    molecular_weight        REAL,
                    polar_surface_area      REAL,
                    hydrogen_bond_donors    REAL,
                    hydrogen_bond_acceptors REAL,
                    Kd_5HT1A                REAL,
                    Kd_5HT2A                REAL,
                    Kd_D2                   REAL,
                    plasma_half_life        REAL,
                    results_json            TEXT
                )
                """,
            )
        conn.commit()
    finally:
        conn.close()


def _hash_password(password: str) -> str:
    """Hash a password using PBKDF2-HMAC-SHA256 with a random salt.

    Returns a ``pbkdf2_sha256$<iterations>$<salt_hex>$<key_hex>`` string
    suitable for storage in the database.
    """
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, _PBKDF2_ITERATIONS
    )
    return f"pbkdf2_sha256${_PBKDF2_ITERATIONS}${salt.hex()}${key.hex()}"


def _verify_password(password: str, stored_hash: str) -> bool:
    """Verify *password* against *stored_hash* in constant time."""
    try:
        algo, iterations_str, salt_hex, key_hex = stored_hash.split("$")
        if algo != "pbkdf2_sha256":
            return False
        iterations = int(iterations_str)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(key_hex)
        actual = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt, iterations
        )
        return hmac.compare_digest(actual, expected)
    except Exception:  # noqa: BLE001
        return False


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------

def _create_jwt(username: str) -> str:
    """Return a signed JWT containing the username as the ``sub`` claim."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": username,
        "iat": now,
        "exp": now + timedelta(hours=JWT_EXPIRATION_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=_JWT_ALGORITHM)


def _decode_jwt(token: str) -> Optional[str]:
    """Decode *token* and return the username, or ``None`` if invalid/expired."""
    try:
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[_JWT_ALGORITHM],
            options={"verify_exp": True},
        )
        return payload.get("sub")
    except JWTError:
        return None


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

    # ------------------------------------------------------------------
    # Security headers middleware
    # ------------------------------------------------------------------

    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "frame-ancestors 'none';"
        )
        return response

    # ------------------------------------------------------------------
    # Auth helpers (scoped to this app instance)
    # ------------------------------------------------------------------

    def _current_user(session: Optional[str]) -> Optional[str]:
        if session:
            return _decode_jwt(session)
        return None

    def _generate_csrf_token() -> str:
        """Generate a new CSRF token."""
        return secrets.token_urlsafe(32)

    def _validate_csrf(request_token: Optional[str], cookie_token: Optional[str]) -> bool:
        """Validate CSRF using double-submit cookie pattern."""
        if not request_token or not cookie_token:
            return False
        return hmac.compare_digest(request_token, cookie_token)

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
        logP: Optional[float] = Form(default=None),
        hERG_IC50: Optional[float] = Form(default=None),
        beta1_selectivity: Optional[float] = Form(default=None),
        molecular_weight: Optional[float] = Form(default=None),
        polar_surface_area: Optional[float] = Form(default=None),
        hydrogen_bond_donors: Optional[float] = Form(default=None),
        hydrogen_bond_acceptors: Optional[float] = Form(default=None),
        Kd_5HT1A: Optional[float] = Form(default=None),
        Kd_5HT2A: Optional[float] = Form(default=None),
        Kd_D2: Optional[float] = Form(default=None),
        plasma_half_life: Optional[float] = Form(default=None),
        bundle: str = Form(default="core-safety"),
    ):
        user = _current_user(session)
        if not user:
            return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)

        from cura_frame import Candidate
        from cura_frame.cli import evaluate_candidate

        # Build properties dict, omitting fields not submitted so that
        # non-strict evaluation skips constraints whose data was not provided.
        _all_props = {
            "logP": logP,
            "hERG_IC50": hERG_IC50,
            "beta1_selectivity": beta1_selectivity,
            "molecular_weight": molecular_weight,
            "polar_surface_area": polar_surface_area,
            "hydrogen_bond_donors": hydrogen_bond_donors,
            "hydrogen_bond_acceptors": hydrogen_bond_acceptors,
            "Kd_5HT1A": Kd_5HT1A,
            "Kd_5HT2A": Kd_5HT2A,
            "Kd_D2": Kd_D2,
            "plasma_half_life": plasma_half_life,
        }
        properties = {k: v for k, v in _all_props.items() if v is not None}

        try:
            candidate = Candidate(
                name="web_calculator",
                properties=properties,
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
                    "molecular_weight": molecular_weight,
                    "polar_surface_area": polar_surface_area,
                    "hydrogen_bond_donors": hydrogen_bond_donors,
                    "hydrogen_bond_acceptors": hydrogen_bond_acceptors,
                    "Kd_5HT1A": Kd_5HT1A,
                    "Kd_5HT2A": Kd_5HT2A,
                    "Kd_D2": Kd_D2,
                    "plasma_half_life": plasma_half_life,
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
                    "molecular_weight": molecular_weight,
                    "polar_surface_area": polar_surface_area,
                    "hydrogen_bond_donors": hydrogen_bond_donors,
                    "hydrogen_bond_acceptors": hydrogen_bond_acceptors,
                    "Kd_5HT1A": Kd_5HT1A,
                    "Kd_5HT2A": Kd_5HT2A,
                    "Kd_D2": Kd_D2,
                    "plasma_half_life": plasma_half_life,
                },
            )

    # ---- All-bundles form ------------------------------------------------

    _ALL_BUNDLES = [
        ("core-safety",  "Core Safety"),
        ("lipinski",     "Lipinski Ro5"),
        ("cns",          "CNS Constraints"),
        ("cardiology",   "Cardiology-Oriented"),
        ("cardianx",     "CardiAnx Dual-Domain"),
        ("oncology",     "Oncology"),
        ("anti-infective", "Anti-Infective"),
        ("metabolic-disease", "Metabolic Disease"),
    ]

    @app.get("/form", response_class=HTMLResponse)
    async def form_get(
        request: Request,
        session: Optional[str] = Cookie(default=None),
    ):
        user = _current_user(session)
        if not user:
            return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)
        return templates.TemplateResponse(
            request, "form.html", {"user": user, "results": None, "error": None}
        )

    @app.post("/form", response_class=HTMLResponse)
    async def form_post(
        request: Request,
        session: Optional[str] = Cookie(default=None),
        logP: Optional[float] = Form(default=None),
        hERG_IC50: Optional[float] = Form(default=None),
        beta1_selectivity: Optional[float] = Form(default=None),
        molecular_weight: Optional[float] = Form(default=None),
        polar_surface_area: Optional[float] = Form(default=None),
        hydrogen_bond_donors: Optional[float] = Form(default=None),
        hydrogen_bond_acceptors: Optional[float] = Form(default=None),
        Kd_5HT1A: Optional[float] = Form(default=None),
        Kd_5HT2A: Optional[float] = Form(default=None),
        Kd_D2: Optional[float] = Form(default=None),
        plasma_half_life: Optional[float] = Form(default=None),
    ):
        user = _current_user(session)
        if not user:
            return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)

        from cura_frame import Candidate
        from cura_frame.cli import evaluate_candidate

        _all_props = {
            "logP": logP,
            "hERG_IC50": hERG_IC50,
            "beta1_selectivity": beta1_selectivity,
            "molecular_weight": molecular_weight,
            "polar_surface_area": polar_surface_area,
            "hydrogen_bond_donors": hydrogen_bond_donors,
            "hydrogen_bond_acceptors": hydrogen_bond_acceptors,
            "Kd_5HT1A": Kd_5HT1A,
            "Kd_5HT2A": Kd_5HT2A,
            "Kd_D2": Kd_D2,
            "plasma_half_life": plasma_half_life,
        }
        properties = {k: v for k, v in _all_props.items() if v is not None}
        values = {k: v for k, v in _all_props.items() if v is not None}

        results = []
        try:
            candidate = Candidate(name="form_all_tests", properties=properties)
            for bundle_key, bundle_label in _ALL_BUNDLES:
                result = evaluate_candidate(
                    candidate=candidate,
                    bundle_name=bundle_key,
                    population=None,
                    strict=False,
                )
                results.append({
                    "label": bundle_label,
                    "status": result.status.value,
                    "violations": result.violations,
                })
        except Exception as exc:  # noqa: BLE001
            return templates.TemplateResponse(
                request,
                "form.html",
                {"user": user, "results": None, "error": str(exc), "values": values},
            )

        # Persist the submission and its results to the database
        results_json = json.dumps([
            {"bundle": r["label"], "status": r["status"],
             "violations": [
                 {"constraint": v.constraint, "observed": v.observed,
                  "threshold": v.threshold, "severity": v.severity.value}
                 for v in r["violations"]
             ]}
            for r in results
        ])
        conn = _get_connection(resolved_db)
        try:
            _execute(
                conn,
                resolved_db,
                """
                INSERT INTO form_submissions (
                    username, timestamp,
                    logP, hERG_IC50, beta1_selectivity,
                    molecular_weight, polar_surface_area,
                    hydrogen_bond_donors, hydrogen_bond_acceptors,
                    Kd_5HT1A, Kd_5HT2A, Kd_D2, plasma_half_life,
                    results_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user,
                    datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
                    logP, hERG_IC50, beta1_selectivity,
                    molecular_weight, polar_surface_area,
                    hydrogen_bond_donors, hydrogen_bond_acceptors,
                    Kd_5HT1A, Kd_5HT2A, Kd_D2, plasma_half_life,
                    results_json,
                ),
            )
            conn.commit()
        finally:
            conn.close()

        return templates.TemplateResponse(
            request,
            "form.html",
            {"user": user, "results": results, "error": None, "values": values},
        )

    # ---- Log recording ---------------------------------------------------

    @app.post("/logs/record", response_class=HTMLResponse)
    async def logs_record(
        request: Request,
        session: Optional[str] = Cookie(default=None),
        logP: Optional[float] = Form(default=None),
        hERG_IC50: Optional[float] = Form(default=None),
        beta1_selectivity: Optional[float] = Form(default=None),
        molecular_weight: Optional[float] = Form(default=None),
        polar_surface_area: Optional[float] = Form(default=None),
        hydrogen_bond_donors: Optional[float] = Form(default=None),
        hydrogen_bond_acceptors: Optional[float] = Form(default=None),
        Kd_5HT1A: Optional[float] = Form(default=None),
        Kd_5HT2A: Optional[float] = Form(default=None),
        Kd_D2: Optional[float] = Form(default=None),
        plasma_half_life: Optional[float] = Form(default=None),
        bundle: str = Form(default="core-safety"),
        status_val: str = Form(default=""),
    ):
        user = _current_user(session)
        if not user:
            return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)

        conn = _get_connection(resolved_db)
        try:
            _execute(
                conn,
                resolved_db,
                """
                INSERT INTO logs (
                    username, timestamp,
                    logP, hERG_IC50, beta1_selectivity,
                    molecular_weight, polar_surface_area,
                    hydrogen_bond_donors, hydrogen_bond_acceptors,
                    Kd_5HT1A, Kd_5HT2A, Kd_D2, plasma_half_life,
                    bundle, status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user,
                    datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
                    logP, hERG_IC50, beta1_selectivity,
                    molecular_weight, polar_surface_area,
                    hydrogen_bond_donors, hydrogen_bond_acceptors,
                    Kd_5HT1A, Kd_5HT2A, Kd_D2, plasma_half_life,
                    bundle,
                    status_val,
                ),
            )
            conn.commit()
        finally:
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
        try:
            rows = _fetchall(
                conn,
                resolved_db,
                """
                SELECT id, timestamp,
                       logP, hERG_IC50, beta1_selectivity,
                       molecular_weight, polar_surface_area,
                       hydrogen_bond_donors, hydrogen_bond_acceptors,
                       Kd_5HT1A, Kd_5HT2A, Kd_D2, plasma_half_life,
                       bundle, status
                FROM logs
                WHERE username = ?
                ORDER BY id DESC
                """,
                (user,),
            )
        finally:
            conn.close()
        logs = rows if _is_postgres(resolved_db) else [dict(r) for r in rows]
        return templates.TemplateResponse(
            request,
            "logs.html",
            {"user": user, "logs": logs},
        )

    # ---- Register --------------------------------------------------------

    @app.get("/register", response_class=HTMLResponse)
    async def register_get(request: Request):
        csrf_token = _generate_csrf_token()
        response = templates.TemplateResponse(
            request, "register.html", {"error": None, "csrf_token": csrf_token}
        )
        response.set_cookie(
            "csrf_token", csrf_token, httponly=False, samesite="lax",
            secure=_SECURE_COOKIES
        )
        return response

    @app.post("/register", response_class=HTMLResponse)
    async def register_post(
        request: Request,
        username: str = Form(...),
        email: str = Form(...),
        password: str = Form(...),
        csrf_token: str = Form(default=""),
        csrf_token_cookie: Optional[str] = Cookie(default=None, alias="csrf_token"),
    ):
        if not _validate_csrf(csrf_token, csrf_token_cookie):
            return templates.TemplateResponse(
                request,
                "register.html",
                {"error": "Invalid or missing CSRF token.", "csrf_token": ""},
                status_code=status.HTTP_403_FORBIDDEN,
            )

        if not username or not email or not password:
            return templates.TemplateResponse(
                request,
                "register.html",
                {"error": "All fields are required.", "csrf_token": csrf_token},
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        username = username.strip()
        email = email.strip()

        # Username validation
        if not (_USERNAME_MIN_LENGTH <= len(username) <= _MAX_USERNAME_LENGTH):
            return templates.TemplateResponse(
                request,
                "register.html",
                {"error": f"Username must be {_USERNAME_MIN_LENGTH}–{_MAX_USERNAME_LENGTH} characters.", "csrf_token": csrf_token},
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        if not _USERNAME_RE.match(username):
            return templates.TemplateResponse(
                request,
                "register.html",
                {"error": "Username may only contain letters, digits, and underscores.", "csrf_token": csrf_token},
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        # Email validation
        if len(email) > _MAX_EMAIL_LENGTH or not _EMAIL_RE.match(email):
            return templates.TemplateResponse(
                request,
                "register.html",
                {"error": "Invalid email address.", "csrf_token": csrf_token},
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        # Password validation
        if len(password) < _MIN_PASSWORD_LENGTH:
            return templates.TemplateResponse(
                request,
                "register.html",
                {"error": f"Password must be at least {_MIN_PASSWORD_LENGTH} characters.", "csrf_token": csrf_token},
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        if len(password) > _MAX_PASSWORD_LENGTH:
            return templates.TemplateResponse(
                request,
                "register.html",
                {"error": f"Password must be at most {_MAX_PASSWORD_LENGTH} characters.", "csrf_token": csrf_token},
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        conn = _get_connection(resolved_db)
        integrity_errors = (sqlite3.IntegrityError,)
        if _is_postgres(resolved_db) and psycopg is not None:
            integrity_errors = (sqlite3.IntegrityError, psycopg.IntegrityError)

        try:
            _execute(
                conn,
                resolved_db,
                "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                (username, email, _hash_password(password)),
            )
            conn.commit()
        except integrity_errors:
            return templates.TemplateResponse(
                request,
                "register.html",
                {"error": "Username or email is already registered.", "csrf_token": csrf_token},
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        finally:
            conn.close()
        return RedirectResponse("/login", status_code=status.HTTP_302_FOUND)

    # ---- Login -----------------------------------------------------------

    @app.get("/login", response_class=HTMLResponse)
    async def login_get(request: Request):
        csrf_token = _generate_csrf_token()
        response = templates.TemplateResponse(
            request, "login.html", {"error": None, "csrf_token": csrf_token}
        )
        response.set_cookie(
            "csrf_token", csrf_token, httponly=False, samesite="lax",
            secure=_SECURE_COOKIES
        )
        return response

    @app.post("/login", response_class=HTMLResponse)
    async def login_post(
        request: Request,
        username: str = Form(...),
        password: str = Form(...),
        csrf_token: str = Form(default=""),
        csrf_token_cookie: Optional[str] = Cookie(default=None, alias="csrf_token"),
    ):
        if not _validate_csrf(csrf_token, csrf_token_cookie):
            return templates.TemplateResponse(
                request,
                "login.html",
                {"error": "Invalid or missing CSRF token.", "csrf_token": ""},
                status_code=status.HTTP_403_FORBIDDEN,
            )

        conn = _get_connection(resolved_db)
        try:
            row = _fetchone(
                conn,
                resolved_db,
                "SELECT username, password_hash FROM users WHERE username = ?",
                (username.strip(),),
            )
        finally:
            conn.close()

        if row is None or not _verify_password(password, row["password_hash"]):
            return templates.TemplateResponse(
                request,
                "login.html",
                {"error": "Invalid username or password.", "csrf_token": csrf_token},
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        token = _create_jwt(row["username"])

        response = RedirectResponse("/dashboard", status_code=status.HTTP_302_FOUND)
        response.set_cookie(
            "session", token, httponly=True, samesite="lax", secure=_SECURE_COOKIES
        )
        return response

    # ---- Logout ----------------------------------------------------------

    @app.get("/logout")
    async def logout(session: Optional[str] = Cookie(default=None)):
        response = RedirectResponse("/login", status_code=status.HTTP_302_FOUND)
        response.delete_cookie("session")
        return response

    return app


# ---------------------------------------------------------------------------
# Module-level app instance (used by uvicorn / render.yaml)
# ---------------------------------------------------------------------------

app = create_app()
