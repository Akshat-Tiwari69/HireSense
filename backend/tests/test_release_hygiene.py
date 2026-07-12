"""Regression checks for release-time secret, storage, and entry-point hygiene."""

import logging

import pytest
from flask import Flask
from flask_jwt_extended import JWTManager

import interviewee_monitoring
from request_logger import init_request_logging, redact_sensitive_path
from storage_config import BACKEND_DIR, get_upload_root, get_upload_subdirectory


REPOSITORY_ROOT = BACKEND_DIR.parent


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        (
            "/api/interviewee/assessment/verify/secret-token-123",
            "/api/interviewee/assessment/verify/<redacted>",
        ),
        (
            "/api/interviewee/assessment/start-by-token/a.b_c-123",
            "/api/interviewee/assessment/start-by-token/<redacted>",
        ),
        ("/api/interviewee/assessment/17/time", "/api/interviewee/assessment/17/time"),
    ],
)
def test_redact_sensitive_assessment_paths(path, expected):
    assert redact_sensitive_path(path) == expected


def test_request_log_never_contains_assessment_token(caplog):
    app = Flask(__name__)
    app.config["JWT_SECRET_KEY"] = "request-logger-test-secret-longer-than-32-characters"
    JWTManager(app)
    init_request_logging(app)

    @app.get("/api/interviewee/assessment/verify/<token>")
    def verify_assessment(token):
        return {"verified": bool(token)}

    token = "super-secret-assessment-token"
    with caplog.at_level("INFO", logger="request_logger"):
        response = app.test_client().get(
            f"/api/interviewee/assessment/verify/{token}"
        )

    assert response.status_code == 200
    assert token not in caplog.text
    assert "/api/interviewee/assessment/verify/<redacted>" in caplog.text


@pytest.mark.parametrize("logger_name", ["werkzeug", "gunicorn.access"])
def test_server_access_loggers_redact_assessment_tokens(caplog, logger_name):
    app = Flask(__name__)
    init_request_logging(app)
    token = "server-access-log-secret"
    request_line = (
        f"GET /api/interviewee/assessment/start-by-token/{token} HTTP/1.1"
    )

    with caplog.at_level("INFO", logger=logger_name):
        access_logger = logging.getLogger(logger_name)
        if logger_name == "gunicorn.access":
            access_logger.info('%(r)s 200', {"r": request_line})
        else:
            access_logger.info('127.0.0.1 - "%s" 200', request_line)

    assert token not in caplog.text
    assert "start-by-token/<redacted>" in caplog.text


def test_upload_root_honours_absolute_environment_path(monkeypatch, tmp_path):
    upload_root = tmp_path / "private-uploads"
    monkeypatch.setenv("UPLOAD_FOLDER", str(upload_root))

    assert get_upload_root(create=True) == upload_root.resolve()
    assert upload_root.is_dir()
    assert get_upload_subdirectory("violations", create=True) == (
        upload_root / "violations"
    ).resolve()


def test_relative_upload_root_is_stable_across_working_directories(monkeypatch):
    monkeypatch.setenv("UPLOAD_FOLDER", "runtime/private-uploads")

    assert get_upload_root() == (BACKEND_DIR / "runtime/private-uploads").resolve()


def test_app_upload_config_is_authoritative_during_requests(monkeypatch, tmp_path):
    environment_root = tmp_path / "environment-root"
    application_root = tmp_path / "application-root"
    monkeypatch.setenv("UPLOAD_FOLDER", str(environment_root))
    app = Flask(__name__)
    app.config["UPLOAD_FOLDER"] = str(application_root)

    with app.app_context():
        assert get_upload_root() == application_root.resolve()


@pytest.mark.parametrize("invalid_part", ["..", ".", "nested/path", "nested\\path", ""])
def test_upload_subdirectory_rejects_unsafe_parts(monkeypatch, tmp_path, invalid_part):
    monkeypatch.setenv("UPLOAD_FOLDER", str(tmp_path))

    with pytest.raises(ValueError):
        get_upload_subdirectory(invalid_part)


def test_violation_screenshot_uses_configured_upload_root(monkeypatch, tmp_path):
    monkeypatch.setenv("UPLOAD_FOLDER", str(tmp_path))

    screenshot_url, screenshot_path = interviewee_monitoring._save_screenshot(
        7, b"private evidence", "jpg"
    )

    assert screenshot_path.parent == (tmp_path / "violations").resolve()
    assert screenshot_path.read_bytes() == b"private evidence"
    assert screenshot_url == f"/uploads/violations/{screenshot_path.name}"


def test_deployment_commands_use_socketio_entry_point():
    procfile = (BACKEND_DIR / "Procfile").read_text(encoding="utf-8")
    nixpacks = (BACKEND_DIR / "nixpacks.toml").read_text(encoding="utf-8")

    for command in (procfile, nixpacks):
        assert "app:app_with_socketio" in command
        assert "--worker-class eventlet" in command
        assert "--workers 1" in command


def test_development_server_disables_raw_eventlet_access_log():
    source = (BACKEND_DIR / "run.py").read_text(encoding="utf-8")

    assert "log_output=False" in source


def test_frontend_api_does_not_enable_cookie_credentials():
    api_source = (
        REPOSITORY_ROOT / "frontend" / "src" / "services" / "api.js"
    ).read_text(encoding="utf-8")

    assert "withCredentials" not in api_source


def test_interviewer_route_does_not_print_full_assessment_link():
    source = (BACKEND_DIR / "interviewer_routes.py").read_text(encoding="utf-8")

    assert "[SCHEDULE] Assessment link:" not in source
