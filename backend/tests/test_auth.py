"""Unit and request-validation tests for authentication."""

import pytest

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


@pytest.mark.parametrize(
    "payload",
    [None, [], "not-an-object", {"email": 123, "password": "password123", "role": "interviewer", "name": "Name"}],
)
def test_register_rejects_malformed_json_payloads(payload):
    client = app.test_client()
    response = client.post("/api/auth/register", json=payload)

    assert response.status_code == 400


@pytest.mark.parametrize(
    "payload",
    [None, [], {"email": 123, "password": "password123"}, {"email": "user@example.com", "password": 123}],
)
def test_login_rejects_malformed_json_payloads(payload):
    client = app.test_client()
    response = client.post("/api/auth/login", json=payload)

    assert response.status_code == 400
