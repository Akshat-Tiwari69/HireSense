"""Authorization, validation, and transaction tests for job routes."""

from contextlib import contextmanager

from flask_jwt_extended import create_access_token

import job_matcher
import job_routes
from app import app


class ScriptedCursor:
    def __init__(self, steps):
        self.steps = list(steps)
        self.executions = []
        self.current = {}
        self.rowcount = 0

    def execute(self, query, params=None):
        assert self.steps, f"Unexpected query: {query}"
        step = self.steps.pop(0)
        sql = " ".join(str(query).split())
        assert step["contains"] in sql
        self.executions.append((sql, params))
        self.current = step
        self.rowcount = step.get("rowcount", 1)

    def fetchone(self):
        return self.current.get("fetchone")

    def fetchall(self):
        return self.current.get("fetchall", [])


class FakeConnection:
    def __init__(self, steps):
        self.cursor_instance = ScriptedCursor(steps)
        self.commits = 0

    def cursor(self, *args, **kwargs):
        return self.cursor_instance

    def commit(self):
        self.commits += 1


def install_connections(monkeypatch, *step_sets):
    connections = [FakeConnection(steps) for steps in step_sets]
    pending = list(connections)

    @contextmanager
    def fake_db_connection():
        assert pending, "Unexpected database connection"
        yield pending.pop(0)

    monkeypatch.setattr(job_routes, "db_connection", fake_db_connection)
    return connections


def auth_headers(role, sector_id=None, identity="5"):
    claims = {"role": role, "name": "Test User"}
    if sector_id is not None:
        claims["sector_id"] = sector_id
    with app.app_context():
        token = create_access_token(identity=identity, additional_claims=claims)
    return {"Authorization": f"Bearer {token}"}


def valid_job_payload(**overrides):
    payload = {
        "title": "Backend Engineer",
        "required_skills": ["Python", "PostgreSQL"],
        "preferred_skills": ["Docker"],
        "min_experience": 2,
        "max_experience": 5,
        "status": "active",
        "employment_type": "full-time",
        "experience_level": "mid",
        "sector_id": 2,
    }
    payload.update(overrides)
    return payload


def test_job_mutations_reject_interviewer_role_before_database_access():
    response = app.test_client().post(
        "/api/jobs/postings",
        headers=auth_headers("interviewer"),
        json=valid_job_payload(),
    )

    assert response.status_code == 403


def test_sector_recruiter_cannot_create_job_in_another_sector():
    response = app.test_client().post(
        "/api/jobs/postings",
        headers=auth_headers("recruiter", sector_id=2),
        json=valid_job_payload(sector_id=3),
    )

    assert response.status_code == 403
    assert "own sector" in response.get_json()["message"]


def test_active_job_rejects_past_closing_time_before_database_access():
    response = app.test_client().post(
        "/api/jobs/postings",
        headers=auth_headers("super_admin"),
        json=valid_job_payload(closes_at="2020-01-01T00:00:00Z"),
    )

    assert response.status_code == 400
    assert "future closes_at" in response.get_json()["message"]


def test_create_job_accepts_skill_arrays_and_audits_in_same_commit(monkeypatch):
    (connection,) = install_connections(
        monkeypatch,
        [
            {"contains": "SELECT 1 FROM sectors", "fetchone": (1,)},
            {"contains": "INSERT INTO job_descriptions", "fetchone": (11,)},
            {"contains": "SELECT email FROM users", "fetchone": ("user@example.test",)},
            {"contains": "INSERT INTO audit_log"},
        ],
    )

    response = app.test_client().post(
        "/api/jobs/postings",
        headers=auth_headers("recruiter", sector_id=2),
        json=valid_job_payload(),
    )

    assert response.status_code == 201
    insert_params = connection.cursor_instance.executions[1][1]
    assert insert_params[2] == '["Python", "PostgreSQL"]'
    assert insert_params[3] == '["Docker"]'
    assert connection.commits == 1
    assert not connection.cursor_instance.steps


def test_public_job_detail_hides_non_active_postings(monkeypatch):
    install_connections(
        monkeypatch,
        [
            {
                "contains": "SELECT j.*, s.name as sector_name",
                "fetchone": {"id": 4, "status": "draft", "sector_id": 2},
            }
        ],
    )

    response = app.test_client().get("/api/jobs/postings/4")

    assert response.status_code == 404


def test_sector_scoped_listing_rejects_cross_sector_filter():
    response = app.test_client().get(
        "/api/jobs/postings?sector_id=3",
        headers=auth_headers("recruiter", sector_id=2),
    )

    assert response.status_code == 403


def test_update_cannot_move_job_outside_recruiter_sector(monkeypatch):
    install_connections(
        monkeypatch,
        [
            {
                "contains": "SELECT * FROM job_descriptions",
                "fetchone": {
                    "id": 4,
                    "sector_id": 2,
                    "min_experience": 2,
                    "max_experience": 5,
                },
            }
        ],
    )

    response = app.test_client().put(
        "/api/jobs/postings/4",
        headers=auth_headers("recruiter", sector_id=2),
        json={"sector_id": 3},
    )

    assert response.status_code == 403


def test_matching_is_sector_scoped_and_refreshes_stale_automatic_rows(monkeypatch):
    first, second = install_connections(
        monkeypatch,
        [
            {
                "contains": "FROM candidates WHERE id = %s",
                "fetchone": {
                    "id": 7,
                    "parsed_skills": '["Python"]',
                    "parsed_skills_json": ["Python"],
                    "years_experience": 3,
                    "education": "BSc",
                    "resume_path": "",
                    "sector_id": 2,
                },
            },
            {
                "contains": "AND sector_id = %s ORDER BY id",
                "fetchall": [{"id": 10, "title": "Engineer", "sector_id": 2}],
            },
        ],
        [
            {"contains": "SELECT sector_id, updated_at FROM candidates", "fetchone": {"sector_id": 2}},
            {
                "contains": "SELECT id, updated_at FROM job_descriptions",
                "fetchall": [{"id": 10, "updated_at": None}],
            },
            {"contains": "DELETE FROM candidate_job_matches"},
            {"contains": "INSERT INTO candidate_job_matches"},
            {
                "contains": "SELECT job_id, match_score",
                "fetchone": {"job_id": 10, "match_score": 88},
            },
            {"contains": "UPDATE candidates"},
            {"contains": "SELECT email FROM users", "fetchone": ("user@example.test",)},
            {"contains": "INSERT INTO audit_log"},
        ],
    )
    monkeypatch.setattr(
        job_matcher,
        "match_candidate_to_jobs",
        lambda *args: [
            {
                "job_id": 10,
                "match_score": 88,
                "skill_match_score": 90,
                "experience_match_score": 80,
                "ai_reasoning": "Strong fit",
            }
        ],
    )
    monkeypatch.setattr(job_routes, "_extract_resume_text", lambda *args: "")

    response = app.test_client().post(
        "/api/jobs/match-candidate",
        headers=auth_headers("recruiter", sector_id=2),
        json={"candidate_id": 7},
    )

    assert response.status_code == 200
    assert first.cursor_instance.executions[1][1] == [2]
    assert "DELETE FROM candidate_job_matches" in second.cursor_instance.executions[2][0]
    assert second.commits == 1


def test_candidate_match_read_rejects_cross_sector_access(monkeypatch):
    install_connections(
        monkeypatch,
        [
            {
                "contains": "SELECT sector_id FROM candidates",
                "fetchone": {"sector_id": 3},
            }
        ],
    )

    response = app.test_client().get(
        "/api/jobs/matches/7",
        headers=auth_headers("recruiter", sector_id=2),
    )

    assert response.status_code == 403


def test_reviewer_confirmation_persists_review_fields_and_best_job(monkeypatch):
    (connection,) = install_connections(
        monkeypatch,
        [
            {
                "contains": "FROM candidate_job_matches m",
                "fetchone": {
                    "match_score": 91,
                    "status": "auto_matched",
                    "sector_id": 2,
                    "best_match_job_id": None,
                    "job_status": "active",
                    "closes_at": None,
                    "job_sector_id": 2,
                },
            },
            {"contains": "UPDATE candidate_job_matches"},
            {"contains": "UPDATE candidates"},
            {"contains": "SELECT email FROM users", "fetchone": ("user@example.test",)},
            {"contains": "INSERT INTO audit_log"},
        ],
    )

    response = app.test_client().patch(
        "/api/jobs/matches/7/10",
        headers=auth_headers("recruiter", sector_id=2),
        json={"status": "confirmed"},
    )

    assert response.status_code == 200
    review_params = connection.cursor_instance.executions[1][1]
    assert review_params == ("confirmed", 5, 7, 10)
    assert connection.cursor_instance.executions[2][1] == (10, 91, 7)
    assert connection.commits == 1


def test_audit_log_limit_is_bounded_before_database_access():
    response = app.test_client().get(
        "/api/jobs/audit-log?limit=0",
        headers=auth_headers("super_admin"),
    )

    assert response.status_code == 400
