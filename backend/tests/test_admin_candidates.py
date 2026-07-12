"""Candidate-management contract tests."""

from contextlib import contextmanager

import admin_candidates
from flask_jwt_extended import create_access_token

from admin_candidates import _remove_resume_file
from app import app


class FakeCursor:
    rowcount = 1

    def __init__(self):
        self.params = None

    def execute(self, _query, params=None):
        self.params = params


class FakeConnection:
    def __init__(self):
        self.cursor_instance = FakeCursor()
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


def test_reset_uses_canonical_status_and_clears_assessment_history(monkeypatch):
    executed = []

    class ResetCursor:
        def execute(self, query, params=None):
            executed.append((str(query), params))

        def fetchone(self):
            return ("Candidate",)

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
    assert "DELETE FROM assessments" in sql
    assert "DELETE FROM scheduled_assessments" in sql
    assert "status = 'applied'" in sql
    assert "shortlist_status = NULL" in sql
