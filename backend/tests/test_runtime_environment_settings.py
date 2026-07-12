"""Regression tests for the development-only runtime environment editor."""

from pathlib import Path

from flask_jwt_extended import create_access_token

from app import app
from admin_settings import _TRACKED_ENV_VARS


def _super_admin_headers():
    with app.app_context():
        token = create_access_token(
            identity="1",
            additional_claims={"role": "super_admin", "name": "Root Admin"},
        )
    return {"Authorization": f"Bearer {token}"}


def test_environment_updates_are_disabled_by_default(monkeypatch):
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.delenv("ALLOW_RUNTIME_ENV_MUTATION", raising=False)

    def unexpected_write(*_args, **_kwargs):
        raise AssertionError("production configuration must never write backend/.env")

    monkeypatch.setattr("admin_settings.set_key", unexpected_write)
    response = app.test_client().post(
        "/api/admin/settings/env",
        headers=_super_admin_headers(),
        json={"name": "FRONTEND_URL", "value": "https://example.test"},
    )

    assert response.status_code == 403
    assert "hosting platform" in response.get_json()["message"]


def test_environment_updates_require_both_development_switches(monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("ALLOW_RUNTIME_ENV_MUTATION", "false")

    response = app.test_client().post(
        "/api/admin/settings/env",
        headers=_super_admin_headers(),
        json={"name": "FRONTEND_URL", "value": "https://example.test"},
    )

    assert response.status_code == 403


def test_environment_updates_work_after_explicit_development_opt_in(monkeypatch):
    writes = []
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("ALLOW_RUNTIME_ENV_MUTATION", "true")
    monkeypatch.setenv("FRONTEND_URL", "http://localhost:5173")
    monkeypatch.setattr(
        "admin_settings.set_key",
        lambda path, name, value, **kwargs: writes.append(
            (path, name, value, kwargs)
        ),
    )

    response = app.test_client().post(
        "/api/admin/settings/env",
        headers=_super_admin_headers(),
        json={"name": "FRONTEND_URL", "value": "https://example.test"},
    )

    assert response.status_code == 200
    assert writes[0][1:3] == ("FRONTEND_URL", "https://example.test")


def test_backend_environment_template_matches_admin_status_contract():
    template = Path(__file__).resolve().parents[1] / ".env.example"
    template_names = {
        line.split("=", 1)[0]
        for line in template.read_text(encoding="utf-8").splitlines()
        if line and not line.startswith("#") and "=" in line
    }

    assert template_names == set(_TRACKED_ENV_VARS)


def test_environment_status_reports_runtime_mutation_state(monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("ALLOW_RUNTIME_ENV_MUTATION", "true")

    response = app.test_client().get(
        "/api/admin/settings/env",
        headers=_super_admin_headers(),
    )

    assert response.status_code == 200
    assert response.get_json()["runtime_mutation_enabled"] is True
