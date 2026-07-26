"""Authorization contract tests for privileged admin content routes."""

import pytest
import psycopg2
from flask_jwt_extended import create_access_token

import admin_users
from app import app


@pytest.fixture
def non_admin_headers():
    with app.app_context():
        token = create_access_token(
            identity="42",
            additional_claims={"role": "interviewer", "name": "Test Interviewer"},
        )
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("post", "/api/admin/question-bank/upload"),
        ("get", "/api/admin/question-bank"),
        ("get", "/api/admin/question-bank/1"),
        ("delete", "/api/admin/question-bank/1"),
        ("patch", "/api/admin/question-bank/1/toggle"),
    ],
)
def test_question_bank_routes_reject_non_admin_users(method, path, non_admin_headers):
    response = getattr(app.test_client(), method)(path, headers=non_admin_headers)

    assert response.status_code == 403
    assert response.get_json()["message"] == "Access denied. Admin role required."


def test_regular_admin_cannot_create_another_admin():
    with app.app_context():
        token = create_access_token(
            identity="7",
            additional_claims={"role": "admin", "name": "Test Admin"},
        )

    response = app.test_client().post(
        "/api/admin/users",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Escalated User",
            "email": "escalated@example.com",
            "password": "password123",
            "role": "admin",
        },
    )

    assert response.status_code == 403
    assert response.get_json()["message"] == "Only super admins can create privileged users"


@pytest.mark.parametrize("role", ["recruiter", "sector_admin"])
def test_sector_scoped_staff_requires_sector_id(monkeypatch, role):
    monkeypatch.setattr(
        admin_users,
        "get_connection",
        lambda: (_ for _ in ()).throw(
            AssertionError("missing sector reached the database")
        ),
    )
    with app.app_context():
        token = create_access_token(
            identity="7",
            additional_claims={"role": "admin", "name": "Test Admin"},
        )

    response = app.test_client().post(
        "/api/admin/users",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Scoped Reviewer",
            "email": "reviewer@example.com",
            "password": "password123",
            "role": role,
        },
    )

    assert response.status_code == 400
    assert response.get_json()["message"] == "sector_id is required for this role"


def test_staff_provisioning_persists_and_returns_sector_id(monkeypatch):
    class Cursor:
        insert_params = None

        def execute(self, query, params=None):
            if str(query).lstrip().startswith("INSERT"):
                self.insert_params = params

        @staticmethod
        def fetchone():
            return (23,)

    class Connection:
        def __init__(self):
            self.cursor_instance = Cursor()

        def cursor(self):
            return self.cursor_instance

        @staticmethod
        def commit():
            return None

    connection = Connection()
    monkeypatch.setattr(admin_users, "get_connection", lambda: connection)
    monkeypatch.setattr(admin_users, "return_connection", lambda *_args: None)
    monkeypatch.setattr(admin_users, "hash_password", lambda _password: "hash")
    with app.app_context():
        token = create_access_token(
            identity="7",
            additional_claims={"role": "admin", "name": "Test Admin"},
        )

    response = app.test_client().post(
        "/api/admin/users",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Scoped Reviewer",
            "email": "reviewer@example.com",
            "password": "password123",
            "role": "recruiter",
            "sector_id": "12",
        },
    )

    assert response.status_code == 201
    assert response.get_json()["data"]["sector_id"] == 12
    assert connection.cursor_instance.insert_params[-1] == 12


def test_staff_listing_returns_sector_id(monkeypatch):
    class Cursor:
        @staticmethod
        def execute(*_args):
            return None

        @staticmethod
        def fetchall():
            return [(23, "Scoped Reviewer", "reviewer@example.com", "recruiter", 12, None)]

    class Connection:
        @staticmethod
        def cursor():
            return Cursor()

    monkeypatch.setattr(admin_users, "get_connection", Connection)
    monkeypatch.setattr(admin_users, "return_connection", lambda *_args: None)
    with app.app_context():
        token = create_access_token(
            identity="7",
            additional_claims={"role": "admin", "name": "Test Admin"},
        )

    response = app.test_client().get(
        "/api/admin/users",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.get_json()["data"][0]["sector_id"] == 12


def test_staff_provisioning_reports_unknown_sector(monkeypatch):
    class Cursor:
        @staticmethod
        def execute(*_args):
            raise psycopg2.errors.ForeignKeyViolation("unknown sector")

    class Connection:
        rolled_back = False

        @staticmethod
        def cursor():
            return Cursor()

        def rollback(self):
            self.rolled_back = True

    connection = Connection()
    monkeypatch.setattr(admin_users, "get_connection", lambda: connection)
    monkeypatch.setattr(admin_users, "return_connection", lambda *_args: None)
    monkeypatch.setattr(admin_users, "hash_password", lambda _password: "hash")
    with app.app_context():
        token = create_access_token(
            identity="7",
            additional_claims={"role": "admin", "name": "Test Admin"},
        )

    response = app.test_client().post(
        "/api/admin/users",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Scoped Reviewer",
            "email": "reviewer@example.com",
            "password": "password123",
            "role": "recruiter",
            "sector_id": 999,
        },
    )

    assert response.status_code == 400
    assert response.get_json()["message"] == "sector_id does not reference an existing sector"
    assert connection.rolled_back is True


def test_admin_cannot_delete_own_account():
    with app.app_context():
        token = create_access_token(
            identity="7",
            additional_claims={"role": "admin", "name": "Test Admin"},
        )

    response = app.test_client().delete(
        "/api/admin/users/7",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 400
    assert response.get_json()["message"] == "You cannot delete your own account"


def test_assigned_staff_account_cannot_be_deleted(monkeypatch):
    class Cursor:
        def execute(self, query, params):
            if query.startswith("DELETE"):
                raise psycopg2.errors.ForeignKeyViolation(
                    "scheduled assessments still reference this user"
                )

        @staticmethod
        def fetchone():
            return ("interviewer",)

    class Connection:
        def __init__(self):
            self.rollbacks = 0

        @staticmethod
        def cursor():
            return Cursor()

        def rollback(self):
            self.rollbacks += 1

    connection = Connection()
    monkeypatch.setattr(admin_users, "get_connection", lambda: connection)
    monkeypatch.setattr(admin_users, "return_connection", lambda *_args: None)

    with app.app_context():
        token = create_access_token(
            identity="1",
            additional_claims={"role": "super_admin", "name": "Root Admin"},
        )

    response = app.test_client().delete(
        "/api/admin/users/2",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 409
    assert response.get_json()["message"] == (
        "Reassign this user's active hiring work before deleting the account"
    )
    assert connection.rollbacks == 1
