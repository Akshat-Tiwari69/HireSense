"""Least-privilege contracts for interviewer candidate access."""

from contextlib import contextmanager

import pytest
from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token

import interviewer_routes


@pytest.fixture
def interviewer_app():
    app = Flask(__name__)
    app.config.update(
        JWT_SECRET_KEY="test-secret-key-that-is-long-enough",
        TESTING=True,
    )
    JWTManager(app)
    app.register_blueprint(interviewer_routes.interviewer_bp, url_prefix="/api/interviewer")
    return app


def _headers(app, user_id=7, role="interviewer", sector_id=None):
    claims = {"role": role, "name": "Hiring reviewer"}
    if sector_id is not None:
        claims["sector_id"] = sector_id
    with app.app_context():
        token = create_access_token(
            identity=str(user_id),
            additional_claims=claims,
        )
    return {"Authorization": f"Bearer {token}"}


def test_candidate_scope_distinguishes_assignment_and_applies_reviewer_sector(monkeypatch):
    class Cursor:
        query = None
        params = None

        def execute(self, query, params):
            self.query = " ".join(query.split())
            self.params = params

        @staticmethod
        def fetchone():
            return ("assigned",)

    cursor = Cursor()

    class Connection:
        @staticmethod
        def cursor():
            return cursor

    @contextmanager
    def fake_db_connection():
        yield Connection()

    monkeypatch.setattr(interviewer_routes, "db_connection", fake_db_connection, raising=False)

    assert interviewer_routes._candidate_access_scope(3, 7, 12) == "assigned"
    assert cursor.params == (7, 3, 12)
    assert "own_assignment.interviewer_id = %s" in cursor.query
    assert "c.status IN ('applied', 'pending', 'absence_of_details')" in cursor.query
    assert "NOT EXISTS" in cursor.query
    assert "c.sector_id = %s" in cursor.query


def test_assessment_assignment_uses_canonical_forward_schedule_link(monkeypatch):
    class Cursor:
        query = None
        params = None

        def execute(self, query, params):
            self.query = " ".join(query.split())
            self.params = params

        @staticmethod
        def fetchone():
            return (1,)

    cursor = Cursor()

    class Connection:
        @staticmethod
        def cursor():
            return cursor

    @contextmanager
    def fake_db_connection():
        yield Connection()

    monkeypatch.setattr(interviewer_routes, "db_connection", fake_db_connection, raising=False)

    assert interviewer_routes._assessment_is_assigned(11, 7, 12) is True
    assert cursor.params == (11, 7, 12)
    assert "sa.id = a.scheduled_assessment_id" in cursor.query
    assert "sa.assessment_id" not in cursor.query
    assert "c.sector_id = %s" in cursor.query


@pytest.mark.parametrize(
    ("method", "path", "payload"),
    [
        ("get", "/api/interviewer/candidates/3", None),
        ("get", "/api/interviewer/candidates/3/resume", None),
        ("post", "/api/interviewer/candidates/3/reject", {}),
        ("get", "/api/interviewer/assessments/3", None),
    ],
)
def test_sensitive_candidate_routes_reject_another_interviewers_assignment(
    monkeypatch, interviewer_app, method, path, payload
):
    monkeypatch.setattr(
        interviewer_routes,
        "_candidate_access_scope",
        lambda _candidate_id, _interviewer_id, _sector_id=None: None,
        raising=False,
    )
    monkeypatch.setattr(
        interviewer_routes,
        "get_candidate_by_id",
        lambda _candidate_id: {
            "id": 3,
            "name": "Candidate",
            "email": "candidate@example.test",
            "pros": [],
            "cons": [],
        },
    )
    monkeypatch.setattr(
        interviewer_routes,
        "get_latest_completed_assessment_by_candidate_id",
        lambda _candidate_id: {"id": 11},
    )
    monkeypatch.setattr(
        interviewer_routes,
        "reject_scheduled_candidate",
        lambda *_args: {
            "candidate_id": 3,
            "candidate_name": "Candidate",
            "candidate_email": "candidate@example.test",
            "should_notify": True,
        },
        raising=False,
    )
    monkeypatch.setattr(interviewer_routes, "send_rejection_email", lambda **_kwargs: False)

    response = getattr(interviewer_app.test_client(), method)(
        path,
        headers=_headers(interviewer_app),
        json=payload,
    )

    assert response.status_code == 403
    assert response.get_json()["message"] == "Access denied to this candidate"


@pytest.mark.parametrize("role", ["interviewer", "recruiter", "sector_admin"])
def test_assigned_reviewers_receive_latest_completed_assessment(
    monkeypatch, interviewer_app, role
):
    requested = []
    monkeypatch.setattr(
        interviewer_routes,
        "_candidate_access_scope",
        lambda candidate_id, interviewer_id, sector_id=None: requested.append(
            (candidate_id, interviewer_id, sector_id)
        ) or "assigned",
    )
    monkeypatch.setattr(
        interviewer_routes,
        "get_latest_completed_assessment_by_candidate_id",
        lambda candidate_id: {
            "id": 17,
            "candidate_id": candidate_id,
            "status": "completed",
            "overall_score": 79.6,
            "technical_score": 82,
            "psychometric_score": 74,
        },
        raising=False,
    )
    sector_id = 12 if role != "interviewer" else None

    response = interviewer_app.test_client().get(
        "/api/interviewer/assessments/3",
        headers=_headers(interviewer_app, role=role, sector_id=sector_id),
    )

    assert response.status_code == 200
    assert response.get_json()["data"]["overall_score"] == 79.6
    assert requested == [(3, 7, sector_id)]


def test_placeholder_candidate_notes_route_is_not_registered(interviewer_app):
    response = interviewer_app.test_client().get(
        "/api/interviewer/candidates/3/notes",
        headers=_headers(interviewer_app),
    )

    assert response.status_code == 404


def test_final_decision_rejects_another_interviewers_assessment(
    monkeypatch, interviewer_app
):
    monkeypatch.setattr(
        interviewer_routes,
        "_assessment_is_assigned",
        lambda _assessment_id, _interviewer_id, _sector_id=None: False,
        raising=False,
    )
    monkeypatch.setattr(
        interviewer_routes,
        "record_final_decision",
        lambda *_args: {
            "candidate_id": 3,
            "candidate_name": "Candidate",
            "candidate_email": "candidate@example.test",
            "decision": "Hire",
            "status": "hired",
            "technical_score": 80,
            "psychometric_score": 70,
            "overall_score": 77,
            "rationale": None,
            "should_notify": False,
        },
    )

    response = interviewer_app.test_client().post(
        "/api/interviewer/assessments/11/final-decision",
        headers=_headers(interviewer_app),
        json={"decision": "hire"},
    )

    assert response.status_code == 403
    assert response.get_json()["message"] == "Access denied to this assessment"


def test_assigned_prestart_rejection_cancels_before_sending_email(
    monkeypatch, interviewer_app
):
    calls = []
    monkeypatch.setattr(
        interviewer_routes,
        "_candidate_access_scope",
        lambda _candidate_id, _interviewer_id, _sector_id=None: "assigned",
    )

    def reject(candidate_id, interviewer_id):
        calls.append(("reject", candidate_id, interviewer_id))
        return {
            "candidate_id": candidate_id,
            "candidate_name": "Candidate",
            "candidate_email": "candidate@example.test",
            "should_notify": True,
        }

    def email(**kwargs):
        calls.append(("email", kwargs))
        return True

    monkeypatch.setattr(interviewer_routes, "reject_scheduled_candidate", reject)
    monkeypatch.setattr(interviewer_routes, "send_rejection_email", email)

    response = interviewer_app.test_client().post(
        "/api/interviewer/candidates/3/reject",
        headers=_headers(interviewer_app),
        json={"reason": "Role requirements changed"},
    )

    assert response.status_code == 200
    assert calls[0] == ("reject", 3, 7)
    assert calls[1][0] == "email"
    assert calls[1][1]["reason"] == "Role requirements changed"


def test_rejection_retry_does_not_resend_email(monkeypatch, interviewer_app):
    monkeypatch.setattr(
        interviewer_routes,
        "_candidate_access_scope",
        lambda _candidate_id, _interviewer_id, _sector_id=None: "assigned",
    )
    monkeypatch.setattr(
        interviewer_routes,
        "reject_scheduled_candidate",
        lambda *_args: {
            "candidate_id": 3,
            "candidate_name": "Candidate",
            "candidate_email": "candidate@example.test",
            "should_notify": False,
        },
    )
    monkeypatch.setattr(
        interviewer_routes,
        "send_rejection_email",
        lambda **_kwargs: (_ for _ in ()).throw(
            AssertionError("rejection email was sent twice")
        ),
    )

    response = interviewer_app.test_client().post(
        "/api/interviewer/candidates/3/reject",
        headers=_headers(interviewer_app),
        json={"reason": "Role requirements changed"},
    )

    assert response.status_code == 200
    assert response.get_json()["data"]["email_sent"] is False


@pytest.mark.parametrize("reason", [["not", "text"], "x" * 4001])
def test_rejection_reason_is_bounded_text(
    monkeypatch, interviewer_app, reason
):
    monkeypatch.setattr(
        interviewer_routes,
        "_candidate_access_scope",
        lambda _candidate_id, _interviewer_id, _sector_id=None: "assigned",
    )
    monkeypatch.setattr(
        interviewer_routes,
        "reject_scheduled_candidate",
        lambda *_args: (_ for _ in ()).throw(
            AssertionError("invalid input reached the database")
        ),
    )

    response = interviewer_app.test_client().post(
        "/api/interviewer/candidates/3/reject",
        headers=_headers(interviewer_app),
        json={"reason": reason},
    )

    assert response.status_code == 400
    assert response.get_json()["message"] == "reason must be text up to 4000 characters"


def test_candidate_list_is_scoped_to_current_interviewer(
    monkeypatch, interviewer_app
):
    requested_by = []

    def scoped_candidates(interviewer_id, sector_id=None):
        requested_by.append((interviewer_id, sector_id))
        return [{"id": 3, "name": "Assigned", "status": "under_review", "match_score": 80}]

    monkeypatch.setattr(
        interviewer_routes,
        "get_interviewer_candidates",
        scoped_candidates,
        raising=False,
    )
    monkeypatch.setattr(
        interviewer_routes,
        "get_all_candidates",
        lambda: (_ for _ in ()).throw(AssertionError("unscoped query used")),
        raising=False,
    )
    headers = _headers(interviewer_app)

    candidates = interviewer_app.test_client().get(
        "/api/interviewer/candidates", headers=headers
    )
    assert candidates.status_code == 200
    assert candidates.get_json()["data"][0]["id"] == 3
    assert requested_by == [(7, None)]


def test_unused_dashboard_stats_route_is_not_registered(interviewer_app):
    response = interviewer_app.test_client().get(
        "/api/interviewer/dashboard/stats",
        headers=_headers(interviewer_app),
    )

    assert response.status_code == 404


@pytest.mark.parametrize("role", ["recruiter", "sector_admin"])
def test_sector_reviewers_use_interviewer_api_with_sector_scope(
    monkeypatch, interviewer_app, role
):
    requested_by = []
    monkeypatch.setattr(
        interviewer_routes,
        "get_interviewer_candidates",
        lambda interviewer_id, sector_id=None: requested_by.append(
            (interviewer_id, sector_id)
        ) or [],
    )

    response = interviewer_app.test_client().get(
        "/api/interviewer/candidates",
        headers=_headers(interviewer_app, role=role, sector_id=12),
    )

    assert response.status_code == 200
    assert requested_by == [(7, 12)]


@pytest.mark.parametrize("role", ["recruiter", "sector_admin"])
def test_sector_reviewers_without_sector_are_rejected(
    monkeypatch, interviewer_app, role
):
    monkeypatch.setattr(
        interviewer_routes,
        "get_interviewer_candidates",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("missing scope reached candidate query")
        ),
    )

    response = interviewer_app.test_client().get(
        "/api/interviewer/candidates",
        headers=_headers(interviewer_app, role=role),
    )

    assert response.status_code == 403
    assert response.get_json()["message"] == "A sector assignment is required for this role"


def test_non_reviewer_role_is_rejected_by_interviewer_api(interviewer_app):
    response = interviewer_app.test_client().get(
        "/api/interviewer/candidates",
        headers=_headers(interviewer_app, role="proctor"),
    )

    assert response.status_code == 403


def test_schedule_cannot_claim_candidate_assigned_to_someone_else(
    monkeypatch, interviewer_app
):
    monkeypatch.setenv("FRONTEND_URL", "https://hire.example.test")
    monkeypatch.setattr(
        interviewer_routes,
        "_candidate_access_scope",
        lambda _candidate_id, _interviewer_id, _sector_id=None: None,
        raising=False,
    )
    monkeypatch.setattr(
        interviewer_routes,
        "get_candidate_by_id",
        lambda _candidate_id: (_ for _ in ()).throw(
            AssertionError("unauthorized candidate data was loaded")
        ),
    )

    response = interviewer_app.test_client().post(
        "/api/interviewer/candidates/3/schedule",
        headers=_headers(interviewer_app),
        json={"scheduled_time": "2026-07-15T10:00:00+05:30"},
    )

    assert response.status_code == 403
    assert response.get_json()["message"] == "Access denied to this candidate"


def test_schedule_rejects_a_time_in_the_past_before_loading_candidate(
    monkeypatch, interviewer_app
):
    monkeypatch.setattr(
        interviewer_routes,
        "_candidate_access_scope",
        lambda _candidate_id, _interviewer_id, _sector_id=None: "assigned",
        raising=False,
    )
    monkeypatch.setattr(
        interviewer_routes,
        "get_candidate_by_id",
        lambda _candidate_id: (_ for _ in ()).throw(
            AssertionError("past schedule loaded candidate data")
        ),
    )

    response = interviewer_app.test_client().post(
        "/api/interviewer/candidates/3/schedule",
        headers=_headers(interviewer_app),
        json={"scheduled_time": "2020-01-01T00:00:00Z"},
    )

    assert response.status_code == 400
    assert response.get_json()["message"] == "scheduled_time must be in the future"


def test_production_rejects_technical_schedule_when_runner_is_disabled(
    monkeypatch, interviewer_app
):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("FRONTEND_URL", "https://hire.example.test")
    monkeypatch.setenv("CODE_RUNNER_ENABLED", "false")
    monkeypatch.setattr(
        interviewer_routes,
        "_candidate_access_scope",
        lambda _candidate_id, _interviewer_id, _sector_id=None: "assigned",
        raising=False,
    )
    monkeypatch.setattr(
        interviewer_routes,
        "get_candidate_by_id",
        lambda _candidate_id: (_ for _ in ()).throw(
            AssertionError("disabled runner loaded candidate data")
        ),
    )

    response = interviewer_app.test_client().post(
        "/api/interviewer/candidates/3/schedule",
        headers=_headers(interviewer_app),
        json={
            "scheduled_time": "2099-01-01T00:00:00Z",
            "is_technical_role": True,
        },
    )

    assert response.status_code == 503
    assert response.get_json()["message"] == (
        "Technical assessments are temporarily unavailable."
    )


def test_schedule_rejects_requested_job_outside_candidate_scope(
    monkeypatch, interviewer_app
):
    monkeypatch.setenv("FRONTEND_URL", "https://hire.example.test")
    monkeypatch.setattr(
        interviewer_routes,
        "_candidate_access_scope",
        lambda _candidate_id, _interviewer_id, _sector_id=None: "assigned",
        raising=False,
    )
    monkeypatch.setattr(
        interviewer_routes,
        "get_candidate_by_id",
        lambda _candidate_id: {
            "id": 3,
            "name": "Candidate",
            "email": "candidate@example.test",
            "skills": ["Python"],
        },
    )
    monkeypatch.setattr(
        interviewer_routes,
        "_get_schedule_job_context",
        lambda *_args: None,
        raising=False,
    )
    monkeypatch.setattr(
        interviewer_routes,
        "_generate_assessment_questions",
        lambda **_kwargs: (_ for _ in ()).throw(
            AssertionError("unauthorized job reached question generation")
        ),
    )

    response = interviewer_app.test_client().post(
        "/api/interviewer/candidates/3/schedule",
        headers=_headers(interviewer_app, role="recruiter", sector_id=12),
        json={
            "scheduled_time": "2099-01-01T00:00:00Z",
            "is_technical_role": False,
            "job_id": 99,
        },
    )

    assert response.status_code == 400
    assert response.get_json()["message"] == (
        "Selected job is not open or authorized for this candidate"
    )


@pytest.mark.parametrize("delivery_raises", [False, True])
def test_failed_invitation_cancels_schedule_without_exposing_link(
    monkeypatch, interviewer_app, delivery_raises
):
    monkeypatch.setenv("FRONTEND_URL", "https://hire.example.test")
    monkeypatch.setattr(
        interviewer_routes,
        "_candidate_access_scope",
        lambda *_args: "assigned",
        raising=False,
    )
    monkeypatch.setattr(
        interviewer_routes,
        "get_candidate_by_id",
        lambda _candidate_id: {
            "id": 3,
            "name": "Candidate",
            "email": "candidate@example.test",
            "skills": ["Python"],
        },
    )
    monkeypatch.setattr(interviewer_routes, "_get_schedule_job_context", lambda *_args: None)
    monkeypatch.setattr(
        interviewer_routes,
        "_generate_assessment_questions",
        lambda **_kwargs: {"mcq_questions": [], "psychometric_scenarios": []},
    )
    monkeypatch.setattr(interviewer_routes, "generate_assessment_token", lambda: "secret")
    monkeypatch.setattr(interviewer_routes, "create_scheduled_assessment", lambda **_kwargs: 17)
    if delivery_raises:
        monkeypatch.setattr(
            interviewer_routes,
            "send_assessment_invitation",
            lambda **_kwargs: (_ for _ in ()).throw(ConnectionError("SMTP unavailable")),
        )
    else:
        monkeypatch.setattr(
            interviewer_routes,
            "send_assessment_invitation",
            lambda **_kwargs: False,
        )
    cancelled = []
    monkeypatch.setattr(
        interviewer_routes,
        "cancel_schedule_after_invitation_failure",
        lambda schedule_id, interviewer_id: cancelled.append(
            (schedule_id, interviewer_id)
        ) or True,
        raising=False,
    )

    response = interviewer_app.test_client().post(
        "/api/interviewer/candidates/3/schedule",
        headers=_headers(interviewer_app, user_id=7),
        json={
            "scheduled_time": "2099-01-01T00:00:00Z",
            "is_technical_role": False,
        },
    )

    assert response.status_code == 503
    payload = response.get_json()
    assert payload["status"] == "error"
    assert "assessment_link" not in payload
    assert "data" not in payload
    assert cancelled == [(17, 7)]


def test_successful_invitation_preserves_schedule_response(monkeypatch, interviewer_app):
    monkeypatch.setenv("FRONTEND_URL", "https://hire.example.test")
    monkeypatch.setattr(
        interviewer_routes,
        "_candidate_access_scope",
        lambda *_args: "assigned",
        raising=False,
    )
    monkeypatch.setattr(
        interviewer_routes,
        "get_candidate_by_id",
        lambda _candidate_id: {
            "id": 3,
            "name": "Candidate",
            "email": "candidate@example.test",
            "skills": [],
        },
    )
    monkeypatch.setattr(interviewer_routes, "_get_schedule_job_context", lambda *_args: None)
    monkeypatch.setattr(
        interviewer_routes,
        "_generate_assessment_questions",
        lambda **_kwargs: {"mcq_questions": [], "psychometric_scenarios": []},
    )
    monkeypatch.setattr(interviewer_routes, "generate_assessment_token", lambda: "secret")
    monkeypatch.setattr(interviewer_routes, "create_scheduled_assessment", lambda **_kwargs: 17)
    monkeypatch.setattr(interviewer_routes, "send_assessment_invitation", lambda **_kwargs: True)

    response = interviewer_app.test_client().post(
        "/api/interviewer/candidates/3/schedule",
        headers=_headers(interviewer_app, user_id=7),
        json={
            "scheduled_time": "2099-01-01T00:00:00Z",
            "is_technical_role": False,
        },
    )

    assert response.status_code == 201
    assert response.get_json()["data"]["assessment_link"] == (
        "https://hire.example.test/assessment#token=secret"
    )


def test_resume_download_rejects_database_path_outside_upload_root(
    monkeypatch, interviewer_app, tmp_path
):
    upload_root = tmp_path / "uploads"
    upload_root.mkdir()
    outside_resume = tmp_path / "outside.pdf"
    outside_resume.write_bytes(b"private resume")
    interviewer_app.config["UPLOAD_FOLDER"] = str(upload_root)
    monkeypatch.setattr(
        interviewer_routes,
        "_candidate_access_scope",
        lambda _candidate_id, _interviewer_id, _sector_id=None: "assigned",
        raising=False,
    )
    monkeypatch.setattr(
        interviewer_routes,
        "get_candidate_by_id",
        lambda _candidate_id: {"resume_path": str(outside_resume)},
    )

    response = interviewer_app.test_client().get(
        "/api/interviewer/candidates/3/resume",
        headers=_headers(interviewer_app),
    )

    assert response.status_code == 404
    assert response.get_json()["message"] == "Resume file not found"


def test_resume_download_serves_assigned_file_inside_upload_root(
    monkeypatch, interviewer_app, tmp_path
):
    upload_root = tmp_path / "uploads"
    upload_root.mkdir()
    resume = upload_root / "candidate.pdf"
    resume.write_bytes(b"resume bytes")
    interviewer_app.config["UPLOAD_FOLDER"] = str(upload_root)
    monkeypatch.setattr(
        interviewer_routes,
        "_candidate_access_scope",
        lambda _candidate_id, _interviewer_id, _sector_id=None: "assigned",
        raising=False,
    )
    monkeypatch.setattr(
        interviewer_routes,
        "get_candidate_by_id",
        lambda _candidate_id: {"resume_path": str(resume)},
    )

    response = interviewer_app.test_client().get(
        "/api/interviewer/candidates/3/resume",
        headers=_headers(interviewer_app),
    )

    assert response.status_code == 200
    assert response.data == b"resume bytes"
