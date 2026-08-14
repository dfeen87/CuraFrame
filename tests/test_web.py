# Copyright (c) Don Michael Feeney Jr. Licensed under the MIT License.
"""
Tests for the CuraFrame web application (FastAPI).

Covers:
- Dashboard route returns HTML (not JSON)
- Calculator route responds correctly
- Registration creates a new user and prevents duplicates
- Login and session management
- JWT authentication
"""

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_csrf_token(client: TestClient, path: str) -> str:
    """GET *path* to receive the CSRF cookie, then return its value."""
    client.get(path)
    return client.cookies.get("csrf_token", "")


def _register(client: TestClient, username: str, email: str, password: str):
    """Register via the CSRF-protected /register endpoint."""
    csrf = _get_csrf_token(client, "/register")
    return client.post(
        "/register",
        data={"username": username, "email": email, "password": password,
              "csrf_token": csrf},
    )


def _login(client: TestClient, username: str, password: str):
    """Log in via the CSRF-protected /login endpoint."""
    csrf = _get_csrf_token(client, "/login")
    return client.post(
        "/login",
        data={"username": username, "password": password, "csrf_token": csrf},
    )


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
    _register(client, "alice", "alice@example.com", "secret01")
    _login(client, "alice", "secret01")
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
        response = _register(client, "bob", "bob@example.com", "password123")
        # After redirect-follow the final page should be the login page
        assert response.status_code == 200
        assert b"Log In" in response.content or b"login" in response.content.lower()

    def test_register_prevents_duplicate_username(self, client):
        """Registering the same username twice returns a 400 with an error message."""
        _register(client, "carol", "carol@example.com", "password1")

        # Second attempt with same username
        response = _register(client, "carol", "carol2@example.com", "password1")
        assert response.status_code == 400
        assert b"already" in response.content.lower()

    def test_register_prevents_duplicate_email(self, client):
        """Registering the same email twice returns a 400 with an error message."""
        _register(client, "dave", "shared@example.com", "password1")
        response = _register(client, "dave2", "shared@example.com", "password1")
        assert response.status_code == 400
        assert b"already" in response.content.lower()

    def test_register_requires_all_fields(self, client):
        """Missing a required field returns a 400 or 422."""
        response = _register(client, "eve", "", "password1")
        # FastAPI form validation or our own check should catch this
        assert response.status_code in (400, 422)

    def test_register_rejects_short_password(self, client):
        """Passwords shorter than 8 characters are rejected with a 400."""
        response = _register(client, "shortpw", "shortpw@example.com", "abc")
        assert response.status_code == 400
        assert b"8" in response.content  # error message mentions the minimum length


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

class TestLogin:
    def test_login_page_returns_html(self, client):
        response = client.get("/login")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_login_with_valid_credentials_redirects_to_dashboard(self, client):
        _register(client, "frank", "frank@example.com", "password1")
        response = _login(client, "frank", "password1")
        assert response.status_code == 200
        # Should end up on the dashboard
        assert b"Dashboard" in response.content or b"Welcome" in response.content

    def test_login_with_wrong_password_returns_401(self, client):
        _register(client, "grace", "grace@example.com", "rightpass")
        response = _login(client, "grace", "wrongpass")
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

    def test_calculator_lipinski_bundle_with_full_properties(self, registered_client):
        """Lipinski bundle is fully evaluated when all Ro5 properties are provided."""
        response = registered_client.post(
            "/calculator",
            data={
                "logP": "3.0",
                "molecular_weight": "350.0",
                "hydrogen_bond_donors": "2",
                "hydrogen_bond_acceptors": "6",
                "bundle": "lipinski",
            },
        )
        assert response.status_code == 200
        assert b"accepted" in response.content.lower()

    def test_calculator_lipinski_bundle_rejects_heavy_molecule(self, registered_client):
        """Lipinski bundle rejects a molecule with MW > 500 Da."""
        response = registered_client.post(
            "/calculator",
            data={
                "logP": "3.0",
                "molecular_weight": "650.0",   # violates MW ≤ 500
                "hydrogen_bond_donors": "2",
                "hydrogen_bond_acceptors": "6",
                "bundle": "lipinski",
            },
        )
        assert response.status_code == 200
        assert b"rejected" in response.content.lower()
        assert b"molecular_weight" in response.content

    def test_calculator_cardianx_bundle_accepted(self, registered_client):
        """CardiAnx bundle is fully evaluated with all required properties provided."""
        response = registered_client.post(
            "/calculator",
            data={
                "logP": "3.0",
                "molecular_weight": "480.0",
                "polar_surface_area": "70.0",
                "hydrogen_bond_donors": "2",
                "hydrogen_bond_acceptors": "6",
                "hERG_IC50": "15.0",
                "beta1_selectivity": "120.0",
                "Kd_5HT1A": "10.0",
                "Kd_5HT2A": "600.0",
                "Kd_D2": "1200.0",
                "plasma_half_life": "12.0",
                "bundle": "cardianx",
            },
        )
        assert response.status_code == 200
        assert b"accepted" in response.content.lower()

    def test_calculator_cardianx_bundle_rejected_herg(self, registered_client):
        """CardiAnx bundle rejects a candidate with hERG IC50 below threshold."""
        response = registered_client.post(
            "/calculator",
            data={
                "logP": "3.0",
                "molecular_weight": "480.0",
                "polar_surface_area": "70.0",
                "hydrogen_bond_donors": "2",
                "hydrogen_bond_acceptors": "6",
                "hERG_IC50": "2.0",   # violates hERG_IC50 ≥ 10
                "beta1_selectivity": "120.0",
                "Kd_5HT1A": "10.0",
                "Kd_5HT2A": "600.0",
                "Kd_D2": "1200.0",
                "plasma_half_life": "12.0",
                "bundle": "cardianx",
            },
        )
        assert response.status_code == 200
        assert b"rejected" in response.content.lower()
        assert b"hERG" in response.content

    def test_calculator_new_fields_shown_in_form(self, registered_client):
        """Calculator GET page exposes the new property input fields."""
        response = registered_client.get("/calculator")
        body = response.content
        assert b"molecular_weight" in body
        assert b"polar_surface_area" in body
        assert b"hydrogen_bond_donors" in body
        assert b"hydrogen_bond_acceptors" in body
        assert b"Kd_5HT1A" in body
        assert b"Kd_5HT2A" in body
        assert b"Kd_D2" in body
        assert b"plasma_half_life" in body

    def test_calculator_zero_logP_is_evaluated_not_skipped(self, registered_client):
        """A submitted logP of 0.0 must be included in evaluation, not treated as absent."""
        # logP=0.0 satisfies the ≤ 4.0 constraint, so the result should be accepted
        # (previously a 0.0 was silently dropped, making the result indeterminate).
        response = registered_client.post(
            "/calculator",
            data={
                "logP": "0.0",
                "hERG_IC50": "20.0",
                "beta1_selectivity": "150.0",
                "bundle": "core-safety",
            },
        )
        assert response.status_code == 200
        assert b"accepted" in response.content.lower()


# ---------------------------------------------------------------------------
# Sweep
# ---------------------------------------------------------------------------

class TestSweep:
    def test_sweep_redirects_unauthenticated(self, client):
        """GET /sweep redirects unauthenticated users to /login."""
        response = client.get("/sweep")
        assert response.status_code == 200
        assert b"Log In" in response.content or b"login" in response.content.lower()

    def test_sweep_get_returns_html_when_authenticated(self, registered_client):
        """GET /sweep returns the sweep page for signed-in users."""
        response = registered_client.get("/sweep")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert b"Sensitivity Sweep" in response.content

    def test_sweep_post_runs_sweep_and_shows_results(self, registered_client):
        """POST /sweep evaluates a range of values and renders the visual timeline."""
        response = registered_client.post(
            "/sweep",
            data={
                "logP": "2.0",
                "hERG_IC50": "15.0",
                "beta1_selectivity": "120.0",
                "sweep_prop": "logP",
                "sweep_min": "1.0",
                "sweep_max": "5.0",
                "sweep_steps": "5",
                "bundle": "core-safety",
                "population": "None",
            },
        )
        assert response.status_code == 200
        body = response.content
        assert b"Sweep Visualization" in body
        assert b"Transitions" in body or b"boundary" in body.lower()
        # Verify the swept values (1.0, 2.0, 3.0, 4.0, 5.0) are present in the table
        assert b"1.00" in body
        assert b"3.00" in body
        assert b"5.00" in body


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
        _register(client_a, "user_a", "user_a@x.com", "password1")
        _login(client_a, "user_a", "password1")

        # Register and log in as user B
        _register(client_b, "user_b", "user_b@x.com", "password1")
        _login(client_b, "user_b", "password1")

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


# ---------------------------------------------------------------------------
# Security headers
# ---------------------------------------------------------------------------

class TestSecurityHeaders:
    """HTTP security headers must be present on every response."""

    def _assert_security_headers(self, response):
        assert response.headers.get("x-frame-options") == "DENY"
        assert response.headers.get("x-content-type-options") == "nosniff"
        assert response.headers.get("referrer-policy") == "strict-origin-when-cross-origin"

    def test_security_headers_on_login_page(self, client):
        response = client.get("/login")
        self._assert_security_headers(response)

    def test_security_headers_on_register_page(self, client):
        response = client.get("/register")
        self._assert_security_headers(response)

    def test_security_headers_on_dashboard(self, registered_client):
        response = registered_client.get("/dashboard")
        self._assert_security_headers(response)

    def test_security_headers_on_calculator(self, registered_client):
        response = registered_client.get("/calculator")
        self._assert_security_headers(response)


# ---------------------------------------------------------------------------
# Three-dots dropdown menu (Sign in / Sign out)
# ---------------------------------------------------------------------------

class TestSignInMenu:
    def test_dropdown_has_sign_in_on_public_page(self, client):
        """The three-dots dropdown must offer 'Sign in' on public pages."""
        response = client.get("/login")
        assert b'href="/login"' in response.content
        assert b'Sign in' in response.content

    def test_dropdown_has_sign_in_on_register_page(self, client):
        """The three-dots dropdown must offer 'Sign in' on the register page."""
        response = client.get("/register")
        assert b'href="/login"' in response.content
        assert b'Sign in' in response.content

    def test_dropdown_sign_in_not_a_nav_button(self, client):
        """Sign in must appear as a plain dropdown link, not a btn-primary nav button."""
        response = client.get("/login")
        assert b'href="/login" class="btn btn-primary btn-sm"' not in response.content

    def test_dropdown_has_sign_out_when_authenticated(self, registered_client):
        """The three-dots dropdown must offer 'Sign out' when the user is logged in."""
        response = registered_client.get("/dashboard")
        assert b'href="/logout"' in response.content
        assert b'Sign out' in response.content

    def test_dropdown_has_about_item(self, client):
        """The three-dots dropdown must always show an 'About' item."""
        response = client.get("/login")
        assert b'About' in response.content

    def test_dropdown_form_link_absent_when_unauthenticated(self, client):
        """The Form link must NOT appear in the dropdown for unauthenticated users."""
        response = client.get("/login")
        assert b'href="/form"' not in response.content

    def test_dropdown_form_link_present_when_authenticated(self, registered_client):
        """The Form link must appear in the dropdown when the user is signed in."""
        response = registered_client.get("/dashboard")
        assert b'href="/form"' in response.content

    def test_register_form_has_minlength_8(self, client):
        """Register form password input must declare minlength=8 for client-side enforcement."""
        response = client.get("/register")
        assert b'minlength="8"' in response.content


# ---------------------------------------------------------------------------
# All-bundles form (/form)
# ---------------------------------------------------------------------------

class TestAllBundlesForm:
    def test_form_redirects_unauthenticated(self, client):
        """GET /form redirects unauthenticated users to /login."""
        response = client.get("/form")
        assert response.status_code == 200
        assert b"Log In" in response.content or b"login" in response.content.lower()

    def test_form_get_returns_html_when_authenticated(self, registered_client):
        """GET /form returns the form page for signed-in users."""
        response = registered_client.get("/form")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert b"Run All Tests" in response.content

    def test_form_shows_all_property_rows(self, registered_client):
        """The form page exposes an input row for every property."""
        response = registered_client.get("/form")
        body = response.content
        for field in [b"logP", b"molecular_weight", b"hERG_IC50",
                      b"beta1_selectivity", b"Kd_5HT1A", b"plasma_half_life"]:
            assert field in body

    def test_form_post_returns_results_for_all_bundles(self, registered_client):
        """POST /form evaluates all bundles and shows a result row for each."""
        response = registered_client.post(
            "/form",
            data={
                "logP": "3.0",
                "hERG_IC50": "20.0",
                "beta1_selectivity": "150.0",
            },
        )
        assert response.status_code == 200
        body = response.content
        for label in [b"Core Safety", b"Lipinski", b"CNS", b"Cardiology",
                      b"CardiAnx", b"Oncology", b"Anti-Infective", b"Metabolic"]:
            assert label in body

    def test_form_post_persists_submission_to_db(self, tmp_path):
        """POST /form must save a row to the form_submissions table."""
        import sqlite3
        from apps.web.main import create_app
        from fastapi.testclient import TestClient

        db_path = str(tmp_path / "form_test.db")
        application = create_app(db_path=db_path)
        c = TestClient(application, follow_redirects=True)
        _register(c, "user1", "user1@x.com", "password1")
        _login(c, "user1", "password1")
        c.post("/form", data={"logP": "2.5", "hERG_IC50": "15.0"})

        conn = sqlite3.connect(db_path)
        rows = conn.execute("SELECT username, logP, results_json FROM form_submissions").fetchall()
        conn.close()
        assert len(rows) == 1
        assert rows[0][0] == "user1"
        assert rows[0][1] == 2.5
        assert "core-safety" in rows[0][2].lower() or "Core Safety" in rows[0][2]

    def test_form_submissions_are_per_user(self, tmp_path):
        """Each user's submissions are stored independently."""
        import sqlite3
        from apps.web.main import create_app
        from fastapi.testclient import TestClient

        db_path = str(tmp_path / "form_multi.db")
        application = create_app(db_path=db_path)

        c1 = TestClient(application, follow_redirects=True)
        _register(c1, "user_a", "user_a@x.com", "password1")
        _login(c1, "user_a", "password1")
        c1.post("/form", data={"logP": "1.0"})

        c2 = TestClient(application, follow_redirects=True)
        _register(c2, "user_b", "user_b@x.com", "password1")
        _login(c2, "user_b", "password1")
        # user b has not submitted the form

        conn = sqlite3.connect(db_path)
        ua_rows = conn.execute(
            "SELECT username FROM form_submissions WHERE username=?", ("user_a",)
        ).fetchall()
        ub_rows = conn.execute(
            "SELECT username FROM form_submissions WHERE username=?", ("user_b",)
        ).fetchall()
        conn.close()
        assert len(ua_rows) == 1
        assert len(ub_rows) == 0

    def test_form_post_redirects_unauthenticated(self, client):
        """POST /form redirects unauthenticated users to /login."""
        response = client.post("/form", data={"logP": "3.0"})
        assert response.status_code == 200
        assert b"Log In" in response.content or b"login" in response.content.lower()


# ---------------------------------------------------------------------------
# Interactions Analysis (/interactions)
# ---------------------------------------------------------------------------

class TestInteractions:
    def test_interactions_redirects_unauthenticated(self, client):
        """GET /interactions redirects unauthenticated users to /login."""
        response = client.get("/interactions")
        assert response.status_code == 200
        assert b"Log In" in response.content or b"login" in response.content.lower()

    def test_interactions_get_returns_html_when_authenticated(self, registered_client):
        """GET /interactions returns the interaction analysis page for signed-in users."""
        response = registered_client.get("/interactions")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert b"Chemical Interaction & Weakest Link Analysis" in response.content

    def test_interactions_post_evaluates_safe_candidate(self, registered_client):
        """POST /interactions evaluates a safe candidate and returns an ACCEPTED result with safety margins."""
        response = registered_client.post(
            "/interactions",
            data={
                "logP": "3.0",
                "hERG_IC50": "20.0",
                "beta1_selectivity": "150.0",
                "bundle": "core-safety",
            },
        )
        assert response.status_code == 200
        body = response.content
        assert b"ACCEPTED" in body
        assert b"Safety Margin" in body or b"margin" in body.lower()
        assert b"Physical Bottleneck" in body

    def test_interactions_post_evaluates_unsafe_candidate(self, registered_client):
        """POST /interactions evaluates an unsafe candidate and returns a REJECTED result with coupled risk details."""
        response = registered_client.post(
            "/interactions",
            data={
                "logP": "5.0",            # high logP triggers several liabilities/violations
                "hERG_IC50": "2.0",       # critical hERG violation
                "CYP3A4_IC50": "1.5",     # critical CYP3A4 violation/synergy
                "aqueous_solubility": "5.0", # low solubility + high logP -> synergistic risk
                "bundle": "core-safety",
            },
        )
        assert response.status_code == 200
        body = response.content
        assert b"REJECTED" in body
        assert b"Coupled Chemical Interaction Risks" in body
        assert b"Physical Bottleneck" in body
        assert b"Epistemic Uncertainty" in body
        assert b"Chemical Synthesis & Structure-Modification Guidance" in body


# ---------------------------------------------------------------------------
# Navigation menu
# ---------------------------------------------------------------------------

class TestNavigationMenu:
    def test_signed_out_menu_contains_about_sign_in_and_register(self, client):
        response = client.get("/login")
        assert response.status_code == 200

        body = response.text
        assert "About" in body
        assert "Sign in" in body
        assert "Register" in body

        about_index = body.index("About")
        sign_in_index = body.index("Sign in")
        register_index = body.index("Register")
        assert about_index < sign_in_index < register_index


# ---------------------------------------------------------------------------
# Database adapter helpers
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# JWT authentication
# ---------------------------------------------------------------------------

class TestJWTAuthentication:
    def test_login_sets_jwt_cookie(self, client):
        """Successful login sets a cookie whose value is a valid JWT."""
        from jose import jwt as jose_jwt
        from apps.web.main import JWT_SECRET, _JWT_ALGORITHM

        _register(client, "jwtuser", "jwt@example.com", "password1")
        # Use a raw client without follow_redirects to inspect Set-Cookie header
        from fastapi.testclient import TestClient
        from apps.web.main import create_app
        raw_client = TestClient(client.app, follow_redirects=False)

        csrf = _get_csrf_token(raw_client, "/login")
        response = raw_client.post(
            "/login", data={"username": "jwtuser", "password": "password1",
                            "csrf_token": csrf}
        )
        assert response.status_code in (302, 307)
        cookie_value = response.cookies.get("session")
        assert cookie_value is not None
        payload = jose_jwt.decode(cookie_value, JWT_SECRET, algorithms=[_JWT_ALGORITHM])
        assert payload["sub"] == "jwtuser"

    def test_create_jwt_and_decode_roundtrip(self):
        """_create_jwt / _decode_jwt are inverse operations."""
        from apps.web.main import _create_jwt, _decode_jwt

        token = _create_jwt("roundtrip_user")
        assert _decode_jwt(token) == "roundtrip_user"

    def test_decode_jwt_rejects_tampered_token(self):
        """A token with a forged signature must be rejected."""
        from apps.web.main import _decode_jwt

        assert _decode_jwt("bad.token.value") is None

    def test_decode_jwt_rejects_token_signed_with_wrong_secret(self):
        """A token signed with a different secret must be rejected."""
        from jose import jwt as jose_jwt
        from apps.web.main import _decode_jwt, _JWT_ALGORITHM

        foreign_token = jose_jwt.encode({"sub": "hacker"}, "wrong-secret", algorithm=_JWT_ALGORITHM)
        assert _decode_jwt(foreign_token) is None

    def test_jwt_secret_env_var_is_used(self, monkeypatch):
        """When JWT_SECRET is set, it is used to sign tokens."""
        from datetime import datetime, timedelta, timezone
        from jose import jwt as jose_jwt
        from apps.web.core.config import load_config
        from apps.web.core.security import decode_jwt

        monkeypatch.setenv("JWT_SECRET", "my-test-secret-value")
        config = load_config()
        now = datetime.now(timezone.utc)
        token = jose_jwt.encode(
            {"sub": "envuser", "iat": now, "exp": now + timedelta(hours=24)},
            config.jwt_secret,
            algorithm=config.jwt_algorithm,
        )
        assert decode_jwt(token, config) == "envuser"

    def test_dashboard_rejects_invalid_jwt_cookie(self, client):
        """A request with a forged session cookie must be redirected to /login."""
        from fastapi.testclient import TestClient
        raw_client = TestClient(client.app, follow_redirects=True)
        raw_client.cookies.set("session", "not.a.valid.jwt")
        response = raw_client.get("/dashboard")
        assert response.status_code == 200
        assert b"Log In" in response.content or b"login" in response.content.lower()
