# Copyright (c) Don Michael Feeney Jr. Licensed under the MIT License.
"""
Database and Authentication Logic for CuraFrame Console.
Shared database helpers are imported from cura_frame.db.
"""

import os
import re
import sqlite3
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any, List

from cura_frame.db import (
    is_postgres as _is_postgres,
    get_connection as _get_connection,
    execute as _execute,
    fetchone as _fetchone,
    fetchall as _fetchall,
    hash_password as _hash_password,
    verify_password as _verify_password,
)

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

# Input validation limits
_USERNAME_MIN_LENGTH = 3
_USERNAME_MAX_LENGTH = 64
_EMAIL_MAX_LENGTH = 254
_PASSWORD_MIN_LENGTH = 8
_PASSWORD_MAX_LENGTH = 128
_USERNAME_RE = re.compile(r"^[A-Za-z0-9_]+$")
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# ---------------------------------------------------------------------------
# Database initialisation
# ---------------------------------------------------------------------------

def init_db(db_path: str = DB_PATH) -> None:
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
                CREATE TABLE IF NOT EXISTS custom_populations (
                    id            BIGSERIAL PRIMARY KEY,
                    username      TEXT NOT NULL,
                    name          TEXT NOT NULL,
                    description   TEXT,
                    modifiers     TEXT NOT NULL,
                    UNIQUE(username, name)
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
                CREATE TABLE IF NOT EXISTS custom_populations (
                    id            INTEGER PRIMARY KEY AUTOINCREMENT,
                    username      TEXT NOT NULL,
                    name          TEXT NOT NULL,
                    description   TEXT,
                    modifiers     TEXT NOT NULL,
                    UNIQUE(username, name)
                )
                """,
            )
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

def register_user(username: str, email: str, password: str) -> bool:
    """Register a new user. Returns True if successful, False if username/email exists or validation fails."""
    # Input validation
    if not (_USERNAME_MIN_LENGTH <= len(username) <= _USERNAME_MAX_LENGTH):
        return False
    if not _USERNAME_RE.match(username):
        return False
    if len(email) > _EMAIL_MAX_LENGTH or not _EMAIL_RE.match(email):
        return False
    if not (_PASSWORD_MIN_LENGTH <= len(password) <= _PASSWORD_MAX_LENGTH):
        return False

    conn = _get_connection(DB_PATH)
    try:
        # Check for existing user
        existing = _fetchone(
            conn,
            DB_PATH,
            "SELECT id FROM users WHERE username = ? OR email = ?",
            (username, email)
        )
        if existing:
            return False

        _execute(
            conn,
            DB_PATH,
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            (username, email, _hash_password(password)),
        )
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()


def authenticate_user(username: str, password: str) -> bool:
    """Authenticate a user. Returns True if credentials are valid."""
    conn = _get_connection(DB_PATH)
    try:
        row = _fetchone(
            conn,
            DB_PATH,
            "SELECT password_hash FROM users WHERE username = ?",
            (username,),
        )
    finally:
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
    try:
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
    finally:
        conn.close()

    # Convert Row objects to dicts if needed (already handled by _fetchall for Postgres/SQLite logic)
    # But _fetchall implementation for SQLite returns Row objects if row_factory is set,
    # and _fetchall returns dicts for Postgres.
    # Let's standardize to dicts.

    if _is_postgres(DB_PATH):
        return rows  # Already dicts
    else:
        return [dict(row) for row in rows]

def save_custom_population(username: str, name: str, description: str, modifiers: List[Dict[str, Any]]) -> bool:
    """Save or update a custom population profile for a user."""
    conn = _get_connection(DB_PATH)
    try:
        json_modifiers = json.dumps(modifiers)
        # Check if already exists
        row = _fetchone(
            conn,
            DB_PATH,
            "SELECT id FROM custom_populations WHERE username = ? AND name = ?",
            (username, name),
        )
        if row:
            _execute(
                conn,
                DB_PATH,
                "UPDATE custom_populations SET description = ?, modifiers = ? WHERE username = ? AND name = ?",
                (description, json_modifiers, username, name),
            )
        else:
            _execute(
                conn,
                DB_PATH,
                "INSERT INTO custom_populations (username, name, description, modifiers) VALUES (?, ?, ?, ?)",
                (username, name, description, json_modifiers),
            )
        conn.commit()
        return True
    except Exception as e:
        print(f"Error saving custom population: {e}")
        return False
    finally:
        conn.close()

def get_custom_populations(username: str) -> List[Dict[str, Any]]:
    """Retrieve all custom populations for a user."""
    conn = _get_connection(DB_PATH)
    try:
        rows = _fetchall(
            conn,
            DB_PATH,
            "SELECT name, description, modifiers FROM custom_populations WHERE username = ? ORDER BY name ASC",
            (username,),
        )
        results = []
        for r in rows:
            row_dict = dict(r) if not isinstance(r, dict) else r
            try:
                mods = json.loads(row_dict["modifiers"])
            except Exception:
                mods = []
            results.append({
                "name": row_dict["name"],
                "description": row_dict["description"],
                "modifiers": mods
            })
        return results
    except Exception as e:
        print(f"Error getting custom populations: {e}")
        return []
    finally:
        conn.close()

def delete_custom_population(username: str, name: str) -> bool:
    """Delete a custom population for a user."""
    conn = _get_connection(DB_PATH)
    try:
        _execute(
            conn,
            DB_PATH,
            "DELETE FROM custom_populations WHERE username = ? AND name = ?",
            (username, name),
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"Error deleting custom population: {e}")
        return False
    finally:
        conn.close()
