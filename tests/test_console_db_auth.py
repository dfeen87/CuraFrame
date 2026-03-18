import sqlite3

import pytest

from apps.console_streamlit import db_auth


@pytest.fixture
def test_db_path(tmp_path):
    return str(tmp_path / "test_console.db")


@pytest.fixture
def init_test_db(test_db_path):
    original_db_path = db_auth.DB_PATH
    db_auth.DB_PATH = test_db_path
    db_auth.init_db(test_db_path)
    yield
    db_auth.DB_PATH = original_db_path


def test_init_db_creates_tables(test_db_path, init_test_db):
    conn = sqlite3.connect(test_db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    assert cursor.fetchone() is not None
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='logs'")
    assert cursor.fetchone() is not None
    conn.close()


def test_register_and_authenticate_user(init_test_db):
    username = "testuser"
    email = "test@example.com"
    password = "password123"

    assert db_auth.register_user(username, email, password) is True
    assert db_auth.register_user(username, "other@example.com", "pass") is False
    assert db_auth.register_user("other", email, "pass") is False
    assert db_auth.authenticate_user(username, password) is True
    assert db_auth.authenticate_user(username, "wrongpass") is False
    assert db_auth.authenticate_user("nonexistent", password) is False


def test_save_and_get_logs(init_test_db):
    username = "loguser"
    db_auth.register_user(username, "log@example.com", "password123")

    assert db_auth.save_log(username, {"logP": 2.5, "hERG_IC50": 12.0}, "core-safety", "ACCEPTED") is True

    logs = db_auth.get_user_logs(username)
    assert len(logs) == 1
    row = logs[0]
    assert row["username"] == username
    assert row["bundle"] == "core-safety"
    assert row["status"] == "ACCEPTED"
    assert row["logP"] == 2.5

    db_auth.register_user("otheruser", "other@ex.com", "password123")
    assert db_auth.get_user_logs("otheruser") == []
