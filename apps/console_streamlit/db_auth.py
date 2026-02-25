"""
Database and Authentication Logic for CuraFrame Console.
Shared logic adapted from apps/web/main.py.
"""

import hashlib
import hmac
import json
import os
import secrets
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any, List

try:
    import psycopg
except ImportError:
    psycopg = None

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Database path – override via CURAFRAME_DATABASE_URL (PostgreSQL) or CURAFRAME_DB (SQLite)
# Default to repo root curaframe.db
_DEFAULT_DB = Path(__file__).parent.parent.parent / "curaframe.db"
DB_PATH = (
    os.environ.get("CURAFRAME_DATABASE_URL")
    or os.environ.get("DATABASE_URL")
    or os.environ.get("CURAFRAME_DB", str(_DEFAULT_DB))
)

# PBKDF2-HMAC-SHA256 iteration count (OWASP 2023 recommendation)
_PBKDF2_ITERATIONS = 260_000

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


def init_db(db_path: str = DB_PATH) -> None:
    """Create the users and logs tables if they do not already exist."""
    conn = _get_connection(db_path)
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
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

def _hash_password(password: str) -> str:
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, _PBKDF2_ITERATIONS
    )
    return f"pbkdf2_sha256${_PBKDF2_ITERATIONS}${salt.hex()}${key.hex()}"


def _verify_password(password: str, stored_hash: str) -> bool:
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
    except Exception:
        return False


def register_user(username: str, email: str, password: str) -> bool:
    """Register a new user. Returns True if successful, False if username/email exists."""
    conn = _get_connection(DB_PATH)

    # Check for existing user
    existing = _fetchone(
        conn,
        DB_PATH,
        "SELECT id FROM users WHERE username = ? OR email = ?",
        (username, email)
    )
    if existing:
        conn.close()
        return False

    try:
        _execute(
            conn,
            DB_PATH,
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            (username, email, _hash_password(password)),
        )
        conn.commit()
    except Exception:
        conn.close()
        return False

    conn.close()
    return True


def authenticate_user(username: str, password: str) -> bool:
    """Authenticate a user. Returns True if credentials are valid."""
    conn = _get_connection(DB_PATH)
    row = _fetchone(
        conn,
        DB_PATH,
        "SELECT password_hash FROM users WHERE username = ?",
        (username,),
    )
    conn.close()

    if row is None:
        return False

    return _verify_password(password, row["password_hash"])


# ---------------------------------------------------------------------------
# Logging helpers
# ---------------------------------------------------------------------------

def save_log(username: str, properties: Dict[str, Any], bundle: str, status: str) -> bool:
    """Save an evaluation log to the database."""
    conn = _get_connection(DB_PATH)

    try:
        _execute(
            conn,
            DB_PATH,
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
                username,
                datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
                properties.get("logP"),
                properties.get("hERG_IC50"),
                properties.get("beta1_selectivity"),
                properties.get("molecular_weight"),
                properties.get("polar_surface_area"),
                properties.get("hydrogen_bond_donors"),
                properties.get("hydrogen_bond_acceptors"),
                properties.get("Kd_5HT1A"),
                properties.get("Kd_5HT2A"),
                properties.get("Kd_D2"),
                properties.get("plasma_half_life"),
                bundle,
                status,
            ),
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"Error saving log: {e}")
        return False
    finally:
        conn.close()

def get_user_logs(username: str) -> List[Dict[str, Any]]:
    """Retrieve logs for a specific user."""
    conn = _get_connection(DB_PATH)
    rows = _fetchall(
        conn,
        DB_PATH,
        """
        SELECT id, username, timestamp,
               logP, hERG_IC50, beta1_selectivity,
               molecular_weight, polar_surface_area,
               hydrogen_bond_donors, hydrogen_bond_acceptors,
               Kd_5HT1A, Kd_5HT2A, Kd_D2, plasma_half_life,
               bundle, status
        FROM logs
        WHERE username = ?
        ORDER BY id DESC
        """,
        (username,),
    )
    conn.close()

    # Convert Row objects to dicts if needed (already handled by _fetchall for Postgres/SQLite logic)
    # But _fetchall implementation for SQLite returns Row objects if row_factory is set,
    # and _fetchall returns dicts for Postgres.
    # Let's standardize to dicts.

    if _is_postgres(DB_PATH):
        return rows # Already dicts
    else:
        return [dict(row) for row in rows]
