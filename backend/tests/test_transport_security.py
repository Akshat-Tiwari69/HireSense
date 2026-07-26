"""Transport, browser-boundary, and deployment hardening regressions."""

from datetime import timedelta
import logging

import pytest
from flask import Flask, request
from werkzeug.exceptions import BadRequest

import app as app_module
import websocket_server
from security_headers import (
    add_security_headers,
    configure_proxy_headers,
    configured_cors_origins,
)


@pytest.mark.parametrize(
    "configured",
    [
        "*",
        "http://app.example",
        "https://user:password@app.example",
        "https://app.example/path",
        "https://app.example?debug=true",
        "https://app.example#fragment",
        "ftp://app.example",
        "https://",
    ],
)
def test_production_cors_rejects_non_origins_and_insecure_origins(monkeypatch, configured):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("CORS_ORIGINS", configured)

    with pytest.raises(RuntimeError, match="CORS_ORIGINS"):
        configured_cors_origins()


def test_production_cors_requires_explicit_origins(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("CORS_ORIGINS", raising=False)

    with pytest.raises(RuntimeError, match="CORS_ORIGINS"):
        configured_cors_origins()


def test_cors_origins_are_deduplicated_and_shared_with_websocket(monkeypatch):
    configured = "https://hire.example, https://hire.example,https://admin.example"
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("CORS_ORIGINS", configured)

    assert configured_cors_origins() == [
        "https://hire.example",
        "https://admin.example",
    ]
    assert app_module.cors_origins == websocket_server._allowed_origins


def test_development_cors_has_loopback_only_fallback(monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.delenv("CORS_ORIGINS", raising=False)

    assert configured_cors_origins() == [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ]


def test_api_cors_never_allows_an_unconfigured_origin():
    response = app_module.app.test_client().options(
        "/api/health",
        headers={
            "Origin": "https://attacker.example",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.headers.get("Access-Control-Allow-Origin") is None


def test_security_headers_are_strict_and_sensitive_responses_are_not_cached():
    test_app = Flask(__name__)
    test_app.config["APP_ENV"] = "production"
    add_security_headers(test_app)

    @test_app.get("/api/admin/private")
    def private_response():
        return {"secret": True}

    response = test_app.test_client().get("/api/admin/private")

    assert response.headers["Content-Security-Policy"] == (
        "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'"
    )
    assert "unsafe-inline" not in response.headers["Content-Security-Policy"]
    assert response.headers["Referrer-Policy"] == "no-referrer"
    assert response.headers["Permissions-Policy"] == (
        "camera=(), microphone=(), geolocation=(), payment=(), usb=()"
    )
    assert response.headers["X-XSS-Protection"] == "0"
    assert response.headers["X-Permitted-Cross-Domain-Policies"] == "none"
    assert response.headers["Strict-Transport-Security"] == (
        "max-age=31536000; includeSubDomains"
    )
    assert response.headers["Cache-Control"] == "no-store"


def test_public_job_gets_remain_cacheable_and_development_omits_hsts():
    test_app = Flask(__name__)
    test_app.config["APP_ENV"] = "development"
    add_security_headers(test_app)

    @test_app.get("/api/jobs/postings")
    def public_jobs():
        return {"jobs": []}

    response = test_app.test_client().get("/api/jobs/postings")

    assert "Cache-Control" not in response.headers
    assert "Strict-Transport-Security" not in response.headers


def test_proxy_headers_are_ignored_until_an_exact_hop_count_is_configured():
    untrusted_app = Flask(__name__)
    configure_proxy_headers(untrusted_app)

    @untrusted_app.get("/")
    def untrusted_remote():
        return {"remote": request.remote_addr}

    untrusted_response = untrusted_app.test_client().get(
        "/", headers={"X-Forwarded-For": "203.0.113.8"}
    )
    assert untrusted_response.get_json()["remote"] == "127.0.0.1"

    trusted_app = Flask(__name__)
    trusted_app.config["TRUST_PROXY_HOPS"] = 1
    configure_proxy_headers(trusted_app)

    @trusted_app.get("/")
    def trusted_remote():
        return {"remote": request.remote_addr, "secure": request.is_secure}

    trusted_response = trusted_app.test_client().get(
        "/",
        headers={
            "X-Forwarded-For": "203.0.113.8",
            "X-Forwarded-Proto": "https",
        },
    )
    assert trusted_response.get_json() == {"remote": "203.0.113.8", "secure": True}


@pytest.mark.parametrize("value", ["-1", "6", "many"])
def test_proxy_hop_count_fails_closed_when_invalid(monkeypatch, value):
    monkeypatch.setenv("TRUST_PROXY_HOPS", value)

    with pytest.raises(RuntimeError, match="TRUST_PROXY_HOPS"):
        configure_proxy_headers(Flask(__name__))


def test_insecure_jwt_fallback_is_never_allowed_in_production(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("ALLOW_INSECURE_DEV_SECRET", "true")
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)

    with pytest.raises(RuntimeError, match="JWT_SECRET_KEY"):
        app_module._get_jwt_secret()


@pytest.mark.parametrize(
    "secret",
    [
        "replace-with-a-random-secret-of-at-least-32-characters",
        "dev-secret-key-change-in-production",
        "a" * 32,
    ],
)
def test_predictable_jwt_secrets_are_rejected(monkeypatch, secret):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("JWT_SECRET_KEY", secret)

    with pytest.raises(RuntimeError, match="JWT_SECRET_KEY"):
        app_module._get_jwt_secret()


def test_staff_access_tokens_default_to_one_hour(monkeypatch):
    monkeypatch.delenv("JWT_ACCESS_TOKEN_MINUTES", raising=False)

    assert app_module._get_jwt_access_token_expires() == timedelta(minutes=60)


@pytest.mark.parametrize("minutes", ["0", "481", "not-a-number"])
def test_staff_access_token_lifetime_is_bounded(monkeypatch, minutes):
    monkeypatch.setenv("JWT_ACCESS_TOKEN_MINUTES", minutes)

    with pytest.raises(RuntimeError, match="JWT_ACCESS_TOKEN_MINUTES"):
        app_module._get_jwt_access_token_expires()


def test_http_exception_descriptions_are_not_reflected_to_clients():
    secret = "postgresql://user:password@private.example/database"
    with app_module.app.app_context():
        response, status = app_module.handle_http_error(BadRequest(description=secret))

    assert status == 400
    assert secret not in response.get_json()["message"]


def test_jwt_parser_errors_are_not_copied_to_logs(caplog):
    attacker_detail = "attacker-controlled-token-fragment"

    with app_module.app.app_context(), caplog.at_level(logging.WARNING, logger="app"):
        app_module.invalid_token_callback(attacker_detail)
        app_module.unauthorized_callback(attacker_detail)

    assert attacker_detail not in caplog.text


def test_global_request_body_limit_is_enforced():
    limit = app_module.app.config["MAX_CONTENT_LENGTH"]
    response = app_module.app.test_client().post(
        "/api/auth/login",
        data=b"x" * (limit + 1),
        content_type="application/json",
    )

    assert response.status_code == 413
    assert response.get_json()["status"] == "error"


def test_socketio_signalling_payloads_have_a_small_explicit_limit():
    assert websocket_server.sio.eio.max_http_buffer_size == 256 * 1024
