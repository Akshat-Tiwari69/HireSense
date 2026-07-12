"""Database connection lifecycle tests that do not require PostgreSQL."""

import pytest

import db_config


class FakeConnection:
    def __init__(self):
        self.closed = False
        self.rolled_back = False

    def close(self):
        self.closed = True

    def rollback(self):
        self.rolled_back = True


def test_get_connection_requires_database_url(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        db_config.get_connection()


def test_get_connection_applies_timeout_and_application_name(monkeypatch):
    captured = {}
    expected = FakeConnection()

    def fake_connect(url, **kwargs):
        captured["url"] = url
        captured.update(kwargs)
        return expected

    monkeypatch.setenv("DATABASE_URL", "postgres://user:pass@example.test/database")
    monkeypatch.setattr(db_config.psycopg2, "connect", fake_connect)

    actual = db_config.get_connection()

    assert actual is expected
    assert captured["url"].startswith("postgresql://")
    assert captured["connect_timeout"] == 10
    assert captured["application_name"] == "hiresense-api"
    assert "statement_timeout=30000" in captured["options"]


def test_db_connection_rolls_back_and_closes_on_error(monkeypatch):
    connection = FakeConnection()
    monkeypatch.setattr(db_config, "get_connection", lambda: connection)

    with pytest.raises(ValueError, match="boom"):
        with db_config.db_connection():
            raise ValueError("boom")

    assert connection.rolled_back is True
    assert connection.closed is True
