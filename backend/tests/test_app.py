"""Application-level smoke and health-contract tests."""

import app as app_module
from app import app
from flask_jwt_extended import create_access_token


def test_root_describes_service():
    response = app.test_client().get("/")

    assert response.status_code == 200
    assert response.get_json() == {
        "status": "success",
        "service": "HireSense API",
        "version": "1.0.0",
        "health": "/api/health",
    }


def test_proctor_role_cannot_read_uploaded_candidate_files():
    with app.app_context():
        token = create_access_token(
            identity="9",
            additional_claims={"role": "proctor", "name": "Proctor"},
        )

    response = app.test_client().get(
        "/uploads/private-resume.pdf",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


def test_health_endpoint():
    response = app.test_client().get("/api/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_removed_legacy_assessment_route_is_not_registered():
    response = app.test_client().post("/api/assessment/start")

    assert response.status_code == 404


def test_http_errors_use_json_contract():
    response = app.test_client().get("/definitely-not-a-route")

    assert response.status_code == 404
    assert response.get_json()["status"] == "error"


def test_readiness_reports_database_success(monkeypatch):
    class Cursor:
        def execute(self, query):
            assert query == "SELECT 1"

        def fetchone(self):
            return (1,)

    class Connection:
        closed = False

        def cursor(self):
            return Cursor()

        def close(self):
            self.closed = True

    connection = Connection()
    monkeypatch.setattr(app_module, "get_connection", lambda: connection)

    response = app.test_client().get("/api/health/ready")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ready", "database": "ok"}
    assert connection.closed is True


def test_readiness_reports_database_failure(monkeypatch):
    def unavailable():
        raise RuntimeError("database offline")

    monkeypatch.setattr(app_module, "get_connection", unavailable)
    response = app.test_client().get("/api/health/ready")

    assert response.status_code == 503
    assert response.get_json() == {
        "status": "not_ready",
        "database": "unavailable",
    }


def test_staff_token_is_revoked_when_role_changes(monkeypatch):
    monkeypatch.setattr(
        app_module,
        "get_user_by_id",
        lambda _user_id: {
            "role": "interviewer",
            "updated_at": "2026-07-13T04:00:00+00:00",
        },
    )

    assert app_module._is_staff_token_revoked({
        "sub": "7",
        "role": "admin",
        "user_auth_version": "2026-07-13T04:00:00+00:00",
    }) is True


def test_staff_token_is_revoked_after_user_update(monkeypatch):
    monkeypatch.setattr(
        app_module,
        "get_user_by_id",
        lambda _user_id: {
            "role": "admin",
            "updated_at": "2026-07-13T05:00:00+00:00",
        },
    )

    assert app_module._is_staff_token_revoked({
        "sub": "7",
        "role": "admin",
        "user_auth_version": "2026-07-13T04:00:00+00:00",
    }) is True
