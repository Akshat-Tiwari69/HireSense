"""Interviewee session contract tests."""

import json

import interviewee_session
from flask import Flask


class _Cursor:
    def __init__(self, row):
        self.row = row
        self.executed = None

    def execute(self, sql, params):
        self.executed = (sql, params)

    def fetchone(self):
        return self.row


class _Connection:
    def __init__(self, row):
        self.cursor_instance = _Cursor(row)

    def cursor(self):
        return self.cursor_instance


def _session_app():
    app = Flask(__name__)
    app.register_blueprint(
        interviewee_session.interviewee_session_bp,
        url_prefix="/api/interviewee",
    )
    return app


def test_verify_token_is_read_from_header_not_request_path(monkeypatch):
    captured = []
    monkeypatch.setattr(
        interviewee_session,
        "get_assessment_by_token",
        lambda token: captured.append(token) or None,
    )
    client = _session_app().test_client()

    missing = client.get("/api/interviewee/assessment/verify")
    supplied = client.get(
        "/api/interviewee/assessment/verify",
        headers={"X-Assessment-Token": "secret-assessment-token"},
    )
    legacy_path = client.get(
        "/api/interviewee/assessment/verify/secret-assessment-token"
    )

    assert missing.status_code == 403
    assert supplied.status_code == 404
    assert legacy_path.status_code == 404
    assert captured == ["secret-assessment-token"]


def test_relational_role_overrides_legacy_question_json(monkeypatch):
    payload = {
        "mcq_questions": [],
        "coding_problem": {"title": "Legacy coding question"},
        "is_technical_role": True,
    }
    connection = _Connection((json.dumps(payload), False))
    returned = []
    monkeypatch.setattr(interviewee_session, "get_connection", lambda: connection)
    monkeypatch.setattr(
        interviewee_session, "return_connection", lambda conn: returned.append(conn)
    )

    questions, is_technical = interviewee_session._load_scheduled_configuration(17)

    assert questions == payload
    assert is_technical is False
    assert connection.cursor_instance.executed[1] == (17,)
    assert returned == [connection]


def test_missing_schedule_uses_safe_default_and_releases_connection(monkeypatch):
    connection = _Connection(None)
    returned = []
    monkeypatch.setattr(interviewee_session, "get_connection", lambda: connection)
    monkeypatch.setattr(
        interviewee_session, "return_connection", lambda conn: returned.append(conn)
    )

    questions, is_technical = interviewee_session._load_scheduled_configuration(404)

    assert questions is None
    assert is_technical is True
    assert returned == [connection]
