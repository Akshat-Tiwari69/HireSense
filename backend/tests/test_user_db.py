"""User repository freshness and uniqueness contracts."""

from contextlib import contextmanager

import psycopg2
import pytest

import user_db
from app import app
from user_db import DuplicateEmailError


class _Cursor:
    def __init__(self, row=None, error=None):
        self.row = row
        self.error = error

    def execute(self, *_args, **_kwargs):
        if self.error:
            raise self.error

    def fetchone(self):
        return self.row


class _Connection:
    def __init__(self, cursor):
        self._cursor = cursor
        self.committed = False

    def cursor(self):
        return self._cursor

    def commit(self):
        self.committed = True


def test_user_lookup_is_not_stale_cached(monkeypatch):
    rows = iter([
        (1, "user@example.com", "hash", "interviewer", "User", None, None, None),
        (1, "user@example.com", "hash", "admin", "User", None, None, None),
    ])

    @contextmanager
    def connection_factory():
        yield _Connection(_Cursor(next(rows)))

    monkeypatch.setattr(user_db, "db_connection", connection_factory)

    assert user_db.get_user_by_email("user@example.com")["role"] == "interviewer"
    assert user_db.get_user_by_email("user@example.com")["role"] == "admin"


def test_create_user_maps_unique_violation_to_duplicate_email(monkeypatch):
    @contextmanager
    def connection_factory():
        yield _Connection(_Cursor(error=psycopg2.IntegrityError("duplicate")))

    monkeypatch.setattr(user_db, "db_connection", connection_factory)

    with pytest.raises(DuplicateEmailError, match="Email already exists"):
        user_db.create_user("user@example.com", "hash", "interviewer", "User")


def test_registration_race_returns_conflict(monkeypatch):
    monkeypatch.setattr("auth.get_user_by_email", lambda _email: None)
    monkeypatch.setattr("auth.hash_password", lambda _password: "hash")

    def duplicate(*_args, **_kwargs):
        raise DuplicateEmailError("Email already exists")

    monkeypatch.setattr("auth.create_user", duplicate)
    response = app.test_client().post(
        "/api/auth/register",
        json={
            "email": "race@example.com",
            "password": "password123",
            "role": "interviewer",
            "name": "Race User",
        },
    )

    assert response.status_code == 409
    assert response.get_json()["message"] == "User with this email already exists"
