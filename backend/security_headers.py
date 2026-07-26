"""Browser and reverse-proxy boundary configuration."""

from __future__ import annotations

import os
from urllib.parse import urlsplit

from flask import request
from werkzeug.middleware.proxy_fix import ProxyFix


DEVELOPMENT_ENVIRONMENTS = frozenset({"dev", "development", "local", "test"})
_DEVELOPMENT_CORS_ORIGINS = (
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
)
_SENSITIVE_API_PREFIXES = (
    "/api/auth/",
    "/api/admin/",
    "/api/interviewer/",
    "/api/interviewee/",
    "/api/proctor/",
)
_INSECURE_JWT_SECRETS = frozenset({
    "dev-secret-key-change-in-production",
    "replace-with-a-random-secret-of-at-least-32-characters",
})


def _environment(value=None):
    return (value or os.environ.get("APP_ENV", "production")).strip().lower()


def validate_jwt_secret(secret):
    """Reject missing, short, known-placeholder, and trivially predictable keys."""

    if not isinstance(secret, str) or len(secret.strip()) < 32:
        raise ValueError("must contain at least 32 characters")
    secret = secret.strip()
    if secret in _INSECURE_JWT_SECRETS or len(set(secret)) < 8:
        raise ValueError("is a known placeholder or is too predictable")
    return secret


def _normalise_origin(origin, *, require_https):
    if not isinstance(origin, str) or not origin or any(char.isspace() for char in origin):
        raise ValueError("origin is empty or contains whitespace")
    if origin == "*":
        raise ValueError("wildcard origins are forbidden")

    parsed = urlsplit(origin)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("origin must use HTTP or HTTPS and include a host")
    if require_https and parsed.scheme != "https":
        raise ValueError("deployed origins must use HTTPS")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("origin must not contain credentials")
    if parsed.path not in {"", "/"} or parsed.query or parsed.fragment:
        raise ValueError("origin must not contain a path, query, or fragment")

    try:
        port = parsed.port
    except ValueError as exc:
        raise ValueError("origin contains an invalid port") from exc

    host = parsed.hostname.lower()
    if ":" in host:
        host = f"[{host}]"
    default_port = 443 if parsed.scheme == "https" else 80
    port_suffix = f":{port}" if port is not None and port != default_port else ""
    return f"{parsed.scheme}://{host}{port_suffix}"


def validate_cors_origins(value, *, environment=None):
    """Return canonical browser origins or raise for unsafe CORS configuration."""

    if not isinstance(value, str):
        raise ValueError("CORS_ORIGINS must be a comma-separated string")
    raw_origins = [origin.strip() for origin in value.split(",") if origin.strip()]
    if not raw_origins or len(raw_origins) > 20:
        raise ValueError("CORS_ORIGINS must contain between 1 and 20 origins")

    require_https = _environment(environment) not in DEVELOPMENT_ENVIRONMENTS
    return list(dict.fromkeys(
        _normalise_origin(origin, require_https=require_https)
        for origin in raw_origins
    ))


def configured_cors_origins():
    """Load the same fail-closed CORS allowlist for HTTP and Socket.IO."""

    environment = _environment()
    configured = os.environ.get("CORS_ORIGINS", "").strip()
    if not configured:
        if environment not in DEVELOPMENT_ENVIRONMENTS:
            raise RuntimeError("CORS_ORIGINS must be configured outside development")
        configured = ",".join(_DEVELOPMENT_CORS_ORIGINS)
    try:
        return validate_cors_origins(configured, environment=environment)
    except ValueError as exc:
        raise RuntimeError(f"Invalid CORS_ORIGINS: {exc}") from exc


def configure_proxy_headers(app):
    """Trust forwarded client IP/scheme only for an explicitly known proxy count."""

    configured = app.config.get("TRUST_PROXY_HOPS")
    if configured is None:
        configured = os.environ.get("TRUST_PROXY_HOPS", "0")
    try:
        proxy_hops = int(configured)
    except (TypeError, ValueError) as exc:
        raise RuntimeError("TRUST_PROXY_HOPS must be an integer between 0 and 5") from exc
    if isinstance(configured, bool) or not 0 <= proxy_hops <= 5:
        raise RuntimeError("TRUST_PROXY_HOPS must be an integer between 0 and 5")
    if proxy_hops:
        app.wsgi_app = ProxyFix(
            app.wsgi_app,
            x_for=proxy_hops,
            x_proto=proxy_hops,
            x_host=0,
            x_port=0,
            x_prefix=0,
        )
    return app


def add_security_headers(app):
    """Add strict API-oriented response headers."""

    environment = _environment(app.config.get("APP_ENV"))

    @app.after_request
    def security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "0"
        response.headers["Content-Security-Policy"] = (
            "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'"
        )
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), payment=(), usb=()"
        )
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
        if environment not in DEVELOPMENT_ENVIRONMENTS:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )
        if (
            request.method != "GET"
            or request.path.startswith(_SENSITIVE_API_PREFIXES)
            or request.headers.get("Authorization")
            or request.headers.get("X-Assessment-Token")
        ):
            response.headers["Cache-Control"] = "no-store"
        return response

    app.logger.info("[SECURITY] Response security headers initialized")
    return app
