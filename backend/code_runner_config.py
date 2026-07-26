"""Fail-closed configuration shared by coding assessment entry points."""

import os
from urllib.parse import urlsplit


_DEVELOPMENT_ENVIRONMENTS = {"dev", "development", "local", "test"}
_TRUTHY_ENV_VALUES = {"1", "true", "yes", "on"}


def code_runner_enabled() -> bool:
    """Return whether code execution is deliberately available in this process."""
    app_env = os.environ.get("APP_ENV", "production").strip().lower()
    configured = os.environ.get("CODE_RUNNER_ENABLED")
    enabled = (
        configured.strip().lower() in _TRUTHY_ENV_VALUES
        if configured is not None
        else app_env in _DEVELOPMENT_ENVIRONMENTS
    )
    if not enabled:
        return False

    runner_url = os.environ.get("CODE_RUNNER_URL", "").strip()
    if not runner_url:
        return app_env in _DEVELOPMENT_ENVIRONMENTS
    parsed = urlsplit(runner_url)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def code_runner_endpoint() -> str:
    """Return the configured endpoint, with a local default only for development."""
    configured = os.environ.get("CODE_RUNNER_URL", "").strip()
    if configured:
        return configured
    return "http://127.0.0.1:2000/api/v2/execute"
