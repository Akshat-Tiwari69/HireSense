"""Candidate-management contract tests."""

from contextlib import contextmanager

import admin_candidates
from flask_jwt_extended import create_access_token

from admin_candidates import _remove_resume_file
from app import app


class FakeCursor:
    rowcount = 1

    def __init__(self, rows=None):
        self.params = None
        self.rows = rows or []

    def execute(self, _query, params=None):
        self.params = params

    def fetchall(self):
        return self.rows


class FakeConnection:
    def __init__(self, rows=None):
        self.cursor_instance = FakeCursor(rows)
        self.committed = False
        self.rolled_back = False
        self.closed = False

    def cursor(self):
        return self.cursor_instance

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def close(self):
        self.closed = True


def _admin_headers():
    with app.app_context():
        token = create_access_token(
            identity="1",
            additional_claims={"role": "admin", "name": "Admin"},
        )
    return {"Authorization": f"Bearer {token}"}


def test_status_update_does_not_overwrite_shortlist_status(monkeypatch):
    connection = FakeConnection()
    monkeypatch.setattr("admin_candidates.get_connection", lambda: connection)

    response = app.test_client().put(
        "/api/admin/candidates/5",
        headers=_admin_headers(),
        json={"status": "Under Review"},
    )

    assert response.status_code == 200
    assert connection.cursor_instance.params == ["under_review", 5]
    assert connection.committed is True
    assert connection.closed is True


def test_candidate_update_rejects_out_of_range_match_score():
    response = app.test_client().put(
        "/api/admin/candidates/5",
        headers=_admin_headers(),
        json={"match_score": 101},
    )

    assert response.status_code == 400
    assert response.get_json()["message"] == "Match score must be between 0 and 100"


def test_resume_cleanup_cannot_delete_outside_upload_directory(tmp_path, monkeypatch):
    monkeypatch.setenv("UPLOAD_FOLDER", str(tmp_path / "uploads"))
    outside = tmp_path / "outside.pdf"
    outside.write_bytes(b"candidate data")

    _remove_resume_file(str(outside))

    assert outside.exists()


def test_resume_cleanup_removes_owned_upload(tmp_path, monkeypatch):
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    monkeypatch.setenv("UPLOAD_FOLDER", str(upload_dir))
    resume = upload_dir / "resume.pdf"
    resume.write_bytes(b"candidate data")

    _remove_resume_file(str(resume))

    assert not resume.exists()


def test_candidate_delete_removes_resume_and_proctoring_evidence(
    tmp_path, monkeypatch, caplog
):
    upload_dir = tmp_path / "uploads"
    evidence_dir = upload_dir / "violations"
    evidence_dir.mkdir(parents=True)
    resume = upload_dir / "resume.pdf"
    evidence = evidence_dir / "evidence.jpg"
    resume.write_bytes(b"resume")
    evidence.write_bytes(b"evidence")
    monkeypatch.setenv("UPLOAD_FOLDER", str(upload_dir))
    monkeypatch.setitem(app.config, "UPLOAD_FOLDER", str(upload_dir))

    class DeleteCursor:
        def execute(self, _query, _params=None):
            pass

        def fetchone(self):
            return (str(resume),)

        def fetchall(self):
            return [("/uploads/violations/evidence.jpg",)]

    class DeleteConnection:
        def cursor(self):
            return DeleteCursor()

        def commit(self):
            pass

    @contextmanager
    def connection_factory():
        yield DeleteConnection()

    monkeypatch.setattr(admin_candidates, "db_connection", connection_factory)
    response = app.test_client().delete(
        "/api/admin/candidates/5",
        headers=_admin_headers(),
    )

    assert response.status_code == 200
    assert not resume.exists()
    assert not evidence.exists()
    assert "Private Candidate" not in caplog.text
    assert "private@example.test" not in caplog.text


def test_reset_uses_canonical_status_without_destroying_candidate_history(monkeypatch):
    executed = []

    class ResetCursor:
        def __init__(self):
            self.rows = iter([("Candidate",), (False,)])

        def execute(self, query, params=None):
            executed.append((str(query), params))

        def fetchone(self):
            return next(self.rows)

    class ResetConnection:
        def cursor(self):
            return ResetCursor()

        def commit(self):
            pass

    @contextmanager
    def connection_factory():
        yield ResetConnection()

    monkeypatch.setattr(admin_candidates, "db_connection", connection_factory)
    response = app.test_client().post(
        "/api/admin/reset-candidate-status/5",
        headers=_admin_headers(),
    )

    assert response.status_code == 200
    sql = "\n".join(query for query, _params in executed)
    assert "DELETE FROM assessments" not in sql
    assert "DELETE FROM scheduled_assessments" not in sql
    assert "status = 'applied'" in sql
    assert "shortlist_status" not in sql


def test_reset_rejects_candidate_with_active_schedule_or_assessment(monkeypatch):
    executed = []

    class ResetCursor:
        def __init__(self):
            self.rows = iter([("Candidate",), (True,)])

        def execute(self, query, params=None):
            executed.append((str(query), params))

        def fetchone(self):
            return next(self.rows)

    class ResetConnection:
        committed = False

        def cursor(self):
            return ResetCursor()

        def commit(self):
            self.committed = True

    connection = ResetConnection()

    @contextmanager
    def connection_factory():
        yield connection

    monkeypatch.setattr(admin_candidates, "db_connection", connection_factory)
    response = app.test_client().post(
        "/api/admin/reset-candidate-status/5",
        headers=_admin_headers(),
    )

    assert response.status_code == 409
    assert response.get_json()["message"] == (
        "Cancel or complete the active assessment before resetting this candidate"
    )
    assert connection.committed is False
    sql = "\n".join(query for query, _params in executed)
    assert "scheduled_assessments" in sql
    assert "assessments" in sql
    assert "status = 'applied'" not in sql


def test_blank_phone_is_optional_and_candidate_feed_hides_resume_path(monkeypatch):
    connection = FakeConnection([(
        5,
        "Candidate",
        "candidate@example.com",
        "",
        82,
        "absence_of_details",
        None,
        4,
        "Backend Engineer",
    )])
    monkeypatch.setattr(admin_candidates, "get_connection", lambda: connection)

    response = app.test_client().get(
        "/api/admin/absence-of-details",
        headers=_admin_headers(),
    )

    assert response.status_code == 200
    candidate = response.get_json()["data"][0]
    assert "phone" not in candidate["missing_fields"]
    assert "resume_path" not in candidate


def test_all_candidates_feed_hides_resume_path(monkeypatch):
    connection = FakeConnection([(
        5,
        "Candidate",
        "candidate@example.com",
        "",
        82,
        "Potential",
        "Strong API experience",
        "Limited domain experience",
        None,
        "under_review",
    )])
    monkeypatch.setattr(admin_candidates, "get_connection", lambda: connection)

    response = app.test_client().get(
        "/api/admin/candidates",
        headers=_admin_headers(),
    )

    assert response.status_code == 200
    assert "resume_path" not in response.get_json()["data"][0]
