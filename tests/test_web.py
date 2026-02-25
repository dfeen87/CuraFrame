"""
Tests for the CuraFrame web application (FastAPI).

Covers:
- Dashboard route returns HTML (not JSON)
- Calculator route responds correctly
- Registration creates a new user and prevents duplicates
- Login and session management
"""

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def app(tmp_path):
    """Create an isolated app instance with a temporary SQLite database."""
    from apps.web.main import create_app

    db_path = str(tmp_path / "test_curaframe.db")
    return create_app(db_path=db_path)


@pytest.fixture()
def client(app):
    """TestClient wrapping the isolated app."""
    return TestClient(app, follow_redirects=True)


@pytest.fixture()
def registered_client(client):
    """A TestClient that already has a logged-in session."""
    client.post(
        "/register",
        data={"username": "alice", "email": "alice@example.com", "password": "secret"},
    )
    client.post("/login", data={"username": "alice", "password": "secret"})
    return client


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

class TestRegistration:
    def test_register_page_returns_html(self, client):
        response = client.get("/register")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert b"Register" in response.content or b"register" in response.content

    def test_register_creates_new_user_and_redirects(self, client):
        """POST /register with valid data creates a user and redirects to /login."""
        response = client.post(
            "/register",
            data={
                "username": "bob",
                "email": "bob@example.com",
                "password": "password123",
            },
        )
        # After redirect-follow the final page should be the login page
        assert response.status_code == 200
        assert b"Log In" in response.content or b"login" in response.content.lower()

    def test_register_prevents_duplicate_username(self, client):
        """Registering the same username twice returns a 400 with an error message."""
        data = {"username": "carol", "email": "carol@example.com", "password": "pw"}
        client.post("/register", data=data)

        # Second attempt with same username
        response = client.post(
            "/register",
            data={"username": "carol", "email": "carol2@example.com", "password": "pw"},
        )
        assert response.status_code == 400
        assert b"already" in response.content.lower()

    def test_register_prevents_duplicate_email(self, client):
        """Registering the same email twice returns a 400 with an error message."""
        client.post(
            "/register",
            data={"username": "dave", "email": "shared@example.com", "password": "pw"},
        )
        response = client.post(
            "/register",
            data={"username": "dave2", "email": "shared@example.com", "password": "pw"},
        )
        assert response.status_code == 400
        assert b"already" in response.content.lower()

    def test_register_requires_all_fields(self, client):
        """Missing a required field returns a 400 or 422."""
        response = client.post(
            "/register",
            data={"username": "eve", "email": "", "password": "pw"},
        )
        # FastAPI form validation or our own check should catch this
        assert response.status_code in (400, 422)


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

class TestLogin:
    def test_login_page_returns_html(self, client):
        response = client.get("/login")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_login_with_valid_credentials_redirects_to_dashboard(self, client):
        client.post(
            "/register",
            data={"username": "frank", "email": "frank@example.com", "password": "pw"},
        )
        response = client.post(
            "/login", data={"username": "frank", "password": "pw"}
        )
        assert response.status_code == 200
        # Should end up on the dashboard
        assert b"Dashboard" in response.content or b"Welcome" in response.content

    def test_login_with_wrong_password_returns_401(self, client):
        client.post(
            "/register",
            data={"username": "grace", "email": "grace@example.com", "password": "right"},
        )
        response = client.post(
            "/login", data={"username": "grace", "password": "wrong"}
        )
        assert response.status_code == 401
        assert b"Invalid" in response.content


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

class TestDashboard:
    def test_dashboard_redirects_unauthenticated_user_to_login(self, client):
        response = client.get("/dashboard")
        assert response.status_code == 200
        # Should have been redirected to login page
        assert b"Log In" in response.content or b"login" in response.content.lower()

    def test_dashboard_returns_html_not_json(self, registered_client):
        """Visiting /dashboard returns HTML, not raw JSON."""
        response = registered_client.get("/dashboard")
        assert response.status_code == 200
        content_type = response.headers["content-type"]
        assert "text/html" in content_type
        # Confirm JSON content-type is NOT returned
        assert "application/json" not in content_type

    def test_dashboard_contains_ui_elements(self, registered_client):
        """Dashboard renders expected UI elements (cards/links)."""
        response = registered_client.get("/dashboard")
        assert response.status_code == 200
        body = response.content
        # Should contain navigation or feature links
        assert b"Calculator" in body or b"calculator" in body
        # Should NOT just be a raw JSON blob
        assert not body.strip().startswith(b"{")


# ---------------------------------------------------------------------------
# Calculator
# ---------------------------------------------------------------------------

class TestCalculator:
    def test_calculator_redirects_unauthenticated_user(self, client):
        response = client.get("/calculator")
        assert response.status_code == 200
        assert b"Log In" in response.content or b"login" in response.content.lower()

    def test_calculator_get_returns_html(self, registered_client):
        response = registered_client.get("/calculator")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert b"Calculator" in response.content or b"calculator" in response.content.lower()

    def test_calculator_post_evaluates_safe_candidate(self, registered_client):
        """A safe candidate should produce an ACCEPTED result."""
        response = registered_client.post(
            "/calculator",
            data={
                "logP": "3.0",
                "hERG_IC50": "20.0",
                "beta1_selectivity": "150.0",
                "bundle": "core-safety",
            },
        )
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert b"accepted" in response.content.lower()

    def test_calculator_post_evaluates_unsafe_candidate(self, registered_client):
        """A candidate with a critical violation should produce a REJECTED result."""
        response = registered_client.post(
            "/calculator",
            data={
                "logP": "9.0",      # violates logP ≤ 4.0
                "hERG_IC50": "20.0",
                "beta1_selectivity": "150.0",
                "bundle": "core-safety",
            },
        )
        assert response.status_code == 200
        assert b"rejected" in response.content.lower()

    def test_calculator_post_shows_violations(self, registered_client):
        """Violations are displayed in the HTML result, not as raw JSON."""
        response = registered_client.post(
            "/calculator",
            data={
                "logP": "9.0",
                "hERG_IC50": "20.0",
                "beta1_selectivity": "150.0",
                "bundle": "core-safety",
            },
        )
        body = response.content
        assert b"logP" in body
        # Result should be HTML, not a JSON blob
        assert not body.strip().startswith(b"{")

    def test_calculator_has_reset_form(self, registered_client):
        """Calculator page has a GET form for reset that works without JavaScript."""
        response = registered_client.get("/calculator")
        body = response.text
        # A <form method="get" action="/calculator"> must exist for the Reset button
        assert 'method="get"' in body.lower() or "method='get'" in body.lower()
        assert 'action="/calculator"' in body

    def test_calculator_reset_clears_inputs(self, registered_client):
        """GET /calculator (reset) returns form with default 0.0 values."""
        response = registered_client.get("/calculator")
        assert response.status_code == 200
        body = response.text
        # All three numeric inputs must default to 0.0
        assert 'name="logP"' in body
        assert 'name="hERG_IC50"' in body
        assert 'name="beta1_selectivity"' in body
        assert body.count('value="0.0"') >= 3


# ---------------------------------------------------------------------------
# Logs
# ---------------------------------------------------------------------------

class TestLogs:
    def test_logs_page_redirects_unauthenticated(self, client):
        response = client.get("/logs")
        assert response.status_code == 200
        assert b"Log In" in response.content or b"login" in response.content.lower()

    def test_logs_page_returns_html_when_authenticated(self, registered_client):
        response = registered_client.get("/logs")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_record_log_saves_entry_for_user(self, registered_client):
        """POST /logs/record saves an entry and it appears in /logs."""
        registered_client.post(
            "/logs/record",
            data={
                "logP": "3.0",
                "hERG_IC50": "20.0",
                "beta1_selectivity": "150.0",
                "bundle": "core-safety",
                "status_val": "accepted",
            },
        )
        response = registered_client.get("/logs")
        assert response.status_code == 200
        body = response.content
        assert b"accepted" in body.lower()
        assert b"core-safety" in body

    def test_logs_are_per_user(self, app, tmp_path):
        """Two different users each see only their own logs."""
        client_a = TestClient(app, follow_redirects=True)
        client_b = TestClient(app, follow_redirects=True)

        # Register and log in as user A
        client_a.post("/register", data={"username": "ua", "email": "ua@x.com", "password": "pw"})
        client_a.post("/login", data={"username": "ua", "password": "pw"})

        # Register and log in as user B
        client_b.post("/register", data={"username": "ub", "email": "ub@x.com", "password": "pw"})
        client_b.post("/login", data={"username": "ub", "password": "pw"})

        # User A records a log
        client_a.post(
            "/logs/record",
            data={
                "logP": "1.0", "hERG_IC50": "5.0", "beta1_selectivity": "10.0",
                "bundle": "lipinski", "status_val": "accepted",
            },
        )

        # User B's logs should be empty
        resp_b = client_b.get("/logs")
        assert b"lipinski" not in resp_b.content
