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


def test_init_db_creates_custom_populations_table(test_db_path, init_test_db):
    conn = sqlite3.connect(test_db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='custom_populations'")
    assert cursor.fetchone() is not None
    conn.close()


def test_save_get_delete_custom_populations(init_test_db):
    username = "test_pop_user"
    db_auth.register_user(username, "test_pop@example.com", "password123")

    modifiers = [
        {"parameter": "clearance", "operator": "*", "value": 0.5},
        {"parameter": "beta1_selectivity", "operator": "*", "value": 2.0}
    ]

    # Save custom population
    assert db_auth.save_custom_population(
        username,
        "renal-impaired asthmatic",
        "Reduced clearance and doubled selectivity.",
        modifiers
    ) is True

    # Retrieve custom population
    pops = db_auth.get_custom_populations(username)
    assert len(pops) == 1
    pop = pops[0]
    assert pop["name"] == "renal-impaired asthmatic"
    assert pop["description"] == "Reduced clearance and doubled selectivity."
    assert pop["modifiers"] == modifiers

    # Update custom population
    updated_modifiers = [
        {"parameter": "clearance", "operator": "*", "value": 0.4}
    ]
    assert db_auth.save_custom_population(
        username,
        "renal-impaired asthmatic",
        "Updated description.",
        updated_modifiers
    ) is True

    pops = db_auth.get_custom_populations(username)
    assert len(pops) == 1
    assert pops[0]["description"] == "Updated description."
    assert pops[0]["modifiers"] == updated_modifiers

    # Delete custom population
    assert db_auth.delete_custom_population(username, "renal-impaired asthmatic") is True
    assert len(db_auth.get_custom_populations(username)) == 0


def test_make_custom_modifier():
    import sys
    from pathlib import Path
    app_dir = str(Path(__file__).parent.parent / "apps" / "console_streamlit")
    if app_dir not in sys.path:
        sys.path.insert(0, app_dir)

    from app import make_custom_modifier
    from cura_frame.core import Constraint

    # Create dummy constraint with scalar threshold
    c_scalar = Constraint(
        name="test_scalar",
        threshold=10.0,
        comparator=lambda v, t: v >= t,
        rationale="test"
    )

    # Test multiplication modifier
    fn_mult = make_custom_modifier("*", 2.0)
    assert fn_mult(c_scalar) == 20.0

    # Test division modifier
    fn_div = make_custom_modifier("/", 2.0)
    assert fn_div(c_scalar) == 5.0

    # Test addition modifier
    fn_add = make_custom_modifier("+", 5.0)
    assert fn_add(c_scalar) == 15.0

    # Test subtraction modifier
    fn_sub = make_custom_modifier("-", 3.0)
    assert fn_sub(c_scalar) == 7.0

    # Test override modifier
    fn_override = make_custom_modifier("Override", 42.0)
    assert fn_override(c_scalar) == 42.0

    # Create dummy constraint with tuple threshold (range)
    c_tuple = Constraint(
        name="test_range",
        threshold=(100.0, 500.0),
        comparator=lambda v, t: t[0] <= v <= t[1],
        rationale="test"
    )

    # Test multiplication on range
    fn_mult_range = make_custom_modifier("*", 0.9)
    assert fn_mult_range(c_tuple) == (100.0, 450.0)

    # Test override on range
    fn_override_range = make_custom_modifier("Override", 600.0)
    assert fn_override_range(c_tuple) == (100.0, 600.0)
