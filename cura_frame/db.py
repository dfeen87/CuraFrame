# Licensed under the PolyForm Noncommercial License 1.0.0
"""CuraFrame shared database layer."""

from __future__ import annotations

import os
import sqlite3
from contextlib import closing
from typing import Any

try:
    from passlib.context import CryptContext
except ImportError:  # pragma: no cover
    CryptContext = None

from cryptography.exceptions import InvalidKey
from cryptography.hazmat.primitives.kdf.argon2 import Argon2id

try:
    import psycopg
except ImportError:  # pragma: no cover
    psycopg = None

_PASSWORD_CONTEXT = (
    CryptContext(schemes=["argon2"], deprecated="auto") if CryptContext is not None else None
)
_ARGON2_LENGTH = 32
_ARGON2_ITERATIONS = 3
_ARGON2_LANES = 4
_ARGON2_MEMORY_COST = 64 * 1024


def is_postgres(db_path: str) -> bool:
    return db_path.startswith("postgresql://") or db_path.startswith("postgres://")


def get_connection(db_path: str):
    if is_postgres(db_path):
        if psycopg is None:
            raise RuntimeError(
                "PostgreSQL connection requested but psycopg is not installed. "
                "Install it with `pip install psycopg[binary] psycopg-pool`."
            )
        return psycopg.connect(db_path)

    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def execute(conn: Any, db_path: str, query: str, params: tuple = ()) -> Any:
    if is_postgres(db_path):
        with closing(conn.cursor()) as cur:
            cur.execute(query, params)
            return cur.rowcount
    return conn.execute(query, params)


def fetchone(conn: Any, db_path: str, query: str, params: tuple = ()):
    if is_postgres(db_path):
        with closing(conn.cursor()) as cur:
            cur.execute(query, params)
            row = cur.fetchone()
            if row is None:
                return None
            columns = [desc.name for desc in cur.description]
            return dict(zip(columns, row))
    return conn.execute(query, params).fetchone()


def fetchall(conn: Any, db_path: str, query: str, params: tuple = ()):
    if is_postgres(db_path):
        with closing(conn.cursor()) as cur:
            cur.execute(query, params)
            rows = cur.fetchall()
            columns = [desc.name for desc in cur.description]
            return [dict(zip(columns, row)) for row in rows]
    return conn.execute(query, params).fetchall()


def _hash_password_with_cryptography(password: str) -> str:
    salt = os.urandom(16)
    kdf = Argon2id(
        salt=salt,
        length=_ARGON2_LENGTH,
        iterations=_ARGON2_ITERATIONS,
        lanes=_ARGON2_LANES,
        memory_cost=_ARGON2_MEMORY_COST,
    )
    return kdf.derive_phc_encoded(password.encode("utf-8"))


def _verify_password_with_cryptography(password: str, stored_hash: str) -> bool:
    try:
        Argon2id.verify_phc_encoded(password.encode("utf-8"), stored_hash)
        return True
    except (InvalidKey, ValueError, TypeError):
        return False


def hash_password(password: str) -> str:
    if _PASSWORD_CONTEXT is not None:
        return _PASSWORD_CONTEXT.hash(password)
    return _hash_password_with_cryptography(password)


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        if _PASSWORD_CONTEXT is not None:
            return _PASSWORD_CONTEXT.verify(password, stored_hash)
        return _verify_password_with_cryptography(password, stored_hash)
    except Exception:  # noqa: BLE001
        return False
