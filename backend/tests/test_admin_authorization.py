"""Authorization contract tests for privileged admin content routes."""

import pytest
from flask_jwt_extended import create_access_token

from app import app
from admin_settings import _validate_env_value


@pytest.fixture
def non_admin_headers():
    with app.app_context():
        token = create_access_token(
            identity="42",
            additional_claims={"role": "interviewer", "name": "Test Interviewer"},
        )
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("post", "/api/admin/question-bank/upload"),
        ("get", "/api/admin/question-bank"),
        ("get", "/api/admin/question-bank/1"),
        ("delete", "/api/admin/question-bank/1"),
        ("patch", "/api/admin/question-bank/1/toggle"),
    ],
)
def test_question_bank_routes_reject_non_admin_users(method, path, non_admin_headers):
    response = getattr(app.test_client(), method)(path, headers=non_admin_headers)

    assert response.status_code == 403
    assert response.get_json()["message"] == "Access denied. Admin role required."


def test_environment_updates_reject_regular_admins():
    with app.app_context():
        token = create_access_token(
            identity="7",
            additional_claims={"role": "admin", "name": "Test Admin"},
        )

    response = app.test_client().post(
        "/api/admin/settings/env",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "FRONTEND_URL", "value": "https://example.test"},
    )

    assert response.status_code == 403
    assert response.get_json()["message"] == "Access denied. Super admin role required."


def test_environment_status_never_reveals_secret_fragments(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", "prefix-super-secret-suffix")
    with app.app_context():
        token = create_access_token(
            identity="7",
            additional_claims={"role": "admin", "name": "Test Admin"},
        )

    response = app.test_client().get(
        "/api/admin/settings/env",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.get_json()["data"]["JWT_SECRET_KEY"] == "***configured***"


def test_regular_admin_cannot_create_another_admin():
    with app.app_context():
        token = create_access_token(
            identity="7",
            additional_claims={"role": "admin", "name": "Test Admin"},
        )

    response = app.test_client().post(
        "/api/admin/users",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Escalated User",
            "email": "escalated@example.com",
            "password": "password123",
            "role": "admin",
        },
    )

    assert response.status_code == 403
    assert response.get_json()["message"] == "Only super admins can create privileged users"


def test_admin_cannot_delete_own_account():
    with app.app_context():
        token = create_access_token(
            identity="7",
            additional_claims={"role": "admin", "name": "Test Admin"},
        )

    response = app.test_client().delete(
        "/api/admin/users/7",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 400
    assert response.get_json()["message"] == "You cannot delete your own account"


def test_environment_updates_reject_newline_injection(monkeypatch):
    with app.app_context():
        token = create_access_token(
            identity="1",
            additional_claims={"role": "super_admin", "name": "Root Admin"},
        )

    def unexpected_write(*_args, **_kwargs):
        raise AssertionError("invalid values must be rejected before writing the env file")

    monkeypatch.setattr("admin_settings.set_key", unexpected_write)
    response = app.test_client().post(
        "/api/admin/settings/env",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "FRONTEND_URL", "value": "https://safe.test\nJWT_SECRET_KEY=stolen"},
    )

    assert response.status_code == 400
    assert response.get_json()["message"] == "Variable value contains invalid characters"


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("JWT_SECRET_KEY", "too-short"),
        ("SMTP_PORT", "70000"),
        ("EMAIL_PROVIDER", "unknown"),
        ("CORS_ORIGINS", "javascript:alert(1)"),
        ("DB_STATEMENT_TIMEOUT_MS", "999"),
    ],
)
def test_environment_value_validation_rejects_unsafe_configuration(name, value):
    assert _validate_env_value(name, value) is not None
