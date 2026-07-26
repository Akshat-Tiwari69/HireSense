"""Unit and request-validation tests for authentication."""

import logging
import pytest

import auth
from auth import hash_password, validate_email, verify_password
from app import app


def test_validate_email_accepts_normal_address():
    assert validate_email("candidate@example.com") is True


def test_validate_email_rejects_invalid_address():
    assert validate_email("not-an-email") is False


def test_password_hash_round_trip():
    password_hash = hash_password("correct-horse-battery-staple")

    assert password_hash != "correct-horse-battery-staple"
    assert verify_password("correct-horse-battery-staple", password_hash) is True
    assert verify_password("wrong-password", password_hash) is False


def test_public_staff_registration_is_not_available():
    client = app.test_client()
    response = client.post(
        "/api/auth/register",
        json={
            "email": "attacker@example.com",
            "password": "password123",
            "role": "interviewer",
            "name": "Attacker",
        },
    )

    assert response.status_code == 404


def test_noop_logout_endpoint_is_not_exposed():
    response = app.test_client().post("/api/auth/logout")

    assert response.status_code == 404


@pytest.mark.parametrize(
    "payload",
    [None, [], {"email": 123, "password": "password123"}, {"email": "user@example.com", "password": 123}],
)
def test_login_rejects_malformed_json_payloads(payload):
    client = app.test_client()
    response = client.post("/api/auth/login", json=payload)

    assert response.status_code == 400


def test_unknown_login_still_performs_a_password_hash_check(monkeypatch):
    checked_hashes = []
    monkeypatch.setattr(auth, "get_user_by_email", lambda _email: None)
    monkeypatch.setattr(
        auth,
        "verify_password",
        lambda _password, password_hash: checked_hashes.append(password_hash) or False,
    )

    response = app.test_client().post(
        "/api/auth/login",
        json={"email": "unknown@example.com", "password": "not-the-password"},
    )

    assert response.status_code == 401
    assert len(checked_hashes) == 1


def test_password_check_logs_do_not_reveal_success_or_failure(caplog):
    password_hash = hash_password("correct-horse-battery-staple")

    with caplog.at_level(logging.INFO, logger="auth"):
        assert verify_password("wrong-password", password_hash) is False

    assert "successful" not in caplog.text.lower()
    assert "failed" not in caplog.text.lower()


def test_slow_login_warning_records_components_without_email(monkeypatch, caplog):
    user = {
        "id": 7,
        "email": "staff@example.test",
        "password_hash": "stored-hash",
        "role": "admin",
        "name": "Staff Member",
        "sector_id": None,
        "updated_at": None,
    }
    timestamps = iter([0.0, 0.1, 0.7, 0.8, 1.0, 2.5])
    monkeypatch.setattr(auth, "perf_counter", lambda: next(timestamps))
    monkeypatch.setattr(auth, "get_user_by_email", lambda _email: user)
    monkeypatch.setattr(auth, "verify_password", lambda *_args: True)
    monkeypatch.setattr(auth, "create_access_token", lambda **_kwargs: "token")

    with caplog.at_level(logging.WARNING, logger="auth"):
        response = app.test_client().post(
            "/api/auth/login",
            json={"email": user["email"], "password": "correct-password"},
        )

    assert response.status_code == 200
    assert "Slow login request" in caplog.text
    assert "lookup=0.600s" in caplog.text
    assert "verify=0.200s" in caplog.text
    assert "total=2.500s" in caplog.text
    assert user["email"] not in caplog.text
