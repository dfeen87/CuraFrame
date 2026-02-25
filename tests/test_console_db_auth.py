
import pytest
import sqlite3
import os
from apps.console_streamlit import db_auth

@pytest.fixture
def test_db_path(tmp_path):
    """Fixture to provide a temporary database path."""
    db_file = tmp_path / "test_console.db"
    return str(db_file)

@pytest.fixture
def init_test_db(test_db_path):
    """Initialize the database and patch the global DB_PATH."""
    # Patch DB_PATH in db_auth
    original_db_path = db_auth.DB_PATH
    db_auth.DB_PATH = test_db_path

    # Must pass path explicitly because default arg is evaluated at definition time
    db_auth.init_db(test_db_path)

    yield

    # Restore DB_PATH
    db_auth.DB_PATH = original_db_path

def test_init_db_creates_tables(test_db_path, init_test_db):
    conn = sqlite3.connect(test_db_path)
    cursor = conn.cursor()

    # Check users table
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    assert cursor.fetchone() is not None

    # Check logs table
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='logs'")
    assert cursor.fetchone() is not None

    conn.close()

def test_register_and_authenticate_user(init_test_db):
    username = "testuser"
    email = "test@example.com"
    password = "password123"

    # Register
    assert db_auth.register_user(username, email, password) is True

    # Duplicate username
    assert db_auth.register_user(username, "other@example.com", "pass") is False

    # Duplicate email
    assert db_auth.register_user("other", email, "pass") is False

    # Authenticate success
    assert db_auth.authenticate_user(username, password) is True

    # Authenticate fail
    assert db_auth.authenticate_user(username, "wrongpass") is False
    assert db_auth.authenticate_user("nonexistent", password) is False

def test_save_and_get_logs(init_test_db):
    username = "loguser"
    db_auth.register_user(username, "log@example.com", "pass")

    properties = {
        "logP": 2.5,
        "hERG_IC50": 12.0
    }
    bundle = "core-safety"
    status = "ACCEPTED"

    # Save log
    assert db_auth.save_log(username, properties, bundle, status) is True

    # Get logs
    logs = db_auth.get_user_logs(username)
    assert len(logs) == 1
    # SQLite row factory returns case-insensitive keys usually if row_factory is sqlite3.Row
    # But let's check keys
    row = logs[0]
    # db_auth._fetchall returns list of dicts for Postgres,
    # but for SQLite it returns list of sqlite3.Row which behaves like dict
    # However, get_user_logs has logic to convert to dicts for SQLite?
    # No, I implemented:
    # if _is_postgres(DB_PATH): return rows
    # else: return [dict(row) for row in rows]
    # So it returns dicts.

    assert row["username"] == username
    assert row["bundle"] == bundle
    assert row["status"] == status
    assert row["logP"] == 2.5

    # Another user
    other_user = "other"
    db_auth.register_user(other_user, "other@ex.com", "pass")
    logs_other = db_auth.get_user_logs(other_user)
    assert len(logs_other) == 0

def test_postgres_adapt_query():
    # Test logic without actual postgres connection
    query = "SELECT * FROM table WHERE id = ?"
    adapted = db_auth._adapt_query(query, "postgresql://user:pass@localhost/db")
    assert adapted == "SELECT * FROM table WHERE id = %s"

    adapted_sqlite = db_auth._adapt_query(query, "sqlite.db")
    assert adapted_sqlite == query
