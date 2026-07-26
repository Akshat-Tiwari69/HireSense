"""Fail-closed code-runner configuration contracts."""

import code_runner_config


def test_runner_defaults_to_disabled_when_environment_is_missing(monkeypatch):
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.delenv("CODE_RUNNER_ENABLED", raising=False)
    monkeypatch.delenv("CODE_RUNNER_URL", raising=False)

    assert code_runner_config.code_runner_enabled() is False


def test_production_runner_requires_an_explicit_url(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("CODE_RUNNER_ENABLED", "true")
    monkeypatch.delenv("CODE_RUNNER_URL", raising=False)

    assert code_runner_config.code_runner_enabled() is False


def test_development_runner_can_use_the_local_default(monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.delenv("CODE_RUNNER_ENABLED", raising=False)
    monkeypatch.delenv("CODE_RUNNER_URL", raising=False)

    assert code_runner_config.code_runner_enabled() is True
