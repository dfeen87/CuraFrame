"""
CuraFrame shared database layer.

Provides database connection helpers, query adapters, and password
utilities shared between the web application (apps/web/main.py) and
the console application (apps/console_streamlit/db_auth.py).
"""

from __future__ import annotations

import hashlib
import hmac
import os
import sqlite3
from contextlib import closing
from typing import Any

try:
    import psycopg
except ImportError:
    psycopg = None

# PBKDF2-HMAC-SHA256 iteration count (OWASP 2023 recommendation)
_PBKDF2_ITERATIONS = 260_000


def is_postgres(db_path: str) -> bool:
    """Return True if *db_path* is a PostgreSQL connection string."""
    return db_path.startswith("postgresql://") or db_path.startswith("postgres://")


def get_connection(db_path: str):
    """Open and return a database connection for *db_path*."""
    if is_postgres(db_path):
        if psycopg is None:
            raise RuntimeError(
                "PostgreSQL connection requested but psycopg is not installed. "
                "Install it with `pip install psycopg[binary]`."
            )
        return psycopg.connect(db_path)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def adapt_query(query: str, db_path: str) -> str:
    """Replace SQLite ``?`` placeholders with ``%s`` for PostgreSQL."""
    if is_postgres(db_path):
        return query.replace("?", "%s")
    return query


def execute(conn: Any, db_path: str, query: str, params: tuple = ()) -> Any:
    """Execute *query* on *conn*, returning a cursor or row-count."""
    if is_postgres(db_path):
        with closing(conn.cursor()) as cur:
            cur.execute(adapt_query(query, db_path), params)
            return cur.rowcount
    return conn.execute(query, params)


def fetchone(conn: Any, db_path: str, query: str, params: tuple = ()):
    """Execute *query* and return the first row as a mapping, or ``None``."""
    if is_postgres(db_path):
        with closing(conn.cursor()) as cur:
            cur.execute(adapt_query(query, db_path), params)
            row = cur.fetchone()
            if row is None:
                return None
            columns = [desc.name for desc in cur.description]
            return dict(zip(columns, row))

    return conn.execute(query, params).fetchone()


def fetchall(conn: Any, db_path: str, query: str, params: tuple = ()):
    """Execute *query* and return all rows as a list of mappings."""
    if is_postgres(db_path):
        with closing(conn.cursor()) as cur:
            cur.execute(adapt_query(query, db_path), params)
            rows = cur.fetchall()
            columns = [desc.name for desc in cur.description]
            return [dict(zip(columns, row)) for row in rows]

    return conn.execute(query, params).fetchall()


def hash_password(password: str) -> str:
    """Hash *password* using PBKDF2-HMAC-SHA256 with a random salt.

    Returns a ``pbkdf2_sha256$<iterations>$<salt_hex>$<key_hex>`` string
    that embeds all information needed for later verification.
    """
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, _PBKDF2_ITERATIONS
    )
    return f"pbkdf2_sha256${_PBKDF2_ITERATIONS}${salt.hex()}${key.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Return True if *password* matches *stored_hash*.

    Uses a constant-time comparison to prevent timing attacks.
    """
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
