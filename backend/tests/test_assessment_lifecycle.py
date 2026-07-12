"""Transaction-level tests for assessment scheduling, responses, and completion."""

from contextlib import contextmanager

import pytest
from flask import Flask

import assessment_db
import interviewee_answers


class ScriptedCursor:
    def __init__(self, steps):
        self.steps = list(steps)
        self.executions = []
        self.current = {}
        self.rowcount = 0

    def execute(self, sql, params=None):
        assert self.steps, f"Unexpected SQL: {sql}"
        step = self.steps.pop(0)
        compact_sql = " ".join(sql.split())
        assert step["contains"] in compact_sql
        self.executions.append((compact_sql, params))
        self.current = step
        self.rowcount = step.get("rowcount", 0)

    def fetchone(self):
        return self.current.get("fetchone")

    def fetchall(self):
        return self.current.get("fetchall", [])


class FakeConnection:
    def __init__(self, steps):
        self.cursor_instance = ScriptedCursor(steps)
        self.commits = 0

    def cursor(self):
        return self.cursor_instance

    def commit(self):
        self.commits += 1


def install_connection(monkeypatch, steps):
    connection = FakeConnection(steps)

    @contextmanager
    def fake_db_connection():
        yield connection

    monkeypatch.setattr(assessment_db, "db_connection", fake_db_connection)
    return connection


@pytest.fixture
def answers_client():
    app = Flask(__name__)
    app.register_blueprint(interviewee_answers.interviewee_answers_bp)
    return app.test_client()


def test_start_is_atomic_and_copies_scheduled_job(monkeypatch):
    connection = install_connection(
        monkeypatch,
        [
            {
                "contains": "FROM scheduled_assessments WHERE access_token = %s FOR UPDATE",
                "fetchone": (7, 3, 42, "scheduled", None),
            },
            {
                "contains": "FROM assessments WHERE scheduled_assessment_id = %s",
                "fetchone": None,
            },
            {
                "contains": "INSERT INTO assessments",
                "fetchone": (99,),
            },
            {"contains": "UPDATE scheduled_assessments", "rowcount": 1},
        ],
    )

    result = assessment_db.start_assessment_by_token("secure-token")

    assert result == {
        "assessment_id": 99,
        "scheduled_assessment_id": 7,
        "candidate_id": 3,
        "job_id": 42,
        "is_resume": False,
    }
    insert_params = connection.cursor_instance.executions[2][1]
    assert insert_params == (3, 42, 7)
    assert connection.commits == 1
    assert not connection.cursor_instance.steps


def test_resume_rejects_assessment_after_deadline(monkeypatch):
    connection = install_connection(
        monkeypatch,
        [
            {
                "contains": "FROM scheduled_assessments WHERE access_token = %s FOR UPDATE",
                "fetchone": (7, 3, 42, "in_progress", 99),
            },
            {
                "contains": "FROM assessments WHERE scheduled_assessment_id = %s",
                "fetchone": (99, "in_progress", True),
            },
        ],
    )

    with pytest.raises(assessment_db.AssessmentStateError, match="time limit"):
        assessment_db.start_assessment_by_token("secure-token")

    assert connection.commits == 0
    assert not connection.cursor_instance.steps


def test_schedule_creation_persists_job_token_and_candidate_state(monkeypatch):
    connection = install_connection(
        monkeypatch,
        [
            {"contains": "INSERT INTO scheduled_assessments", "fetchone": (7,)},
            {"contains": "UPDATE candidates", "rowcount": 1},
        ],
    )

    scheduled_id = assessment_db.create_scheduled_assessment(
        candidate_id=3,
        interviewer_id=5,
        job_id=42,
        scheduled_time="2026-07-14T10:00:00",
        questions_data={"mcq_questions": []},
        access_token="secure-token",
    )

    assert scheduled_id == 7
    insert_params = connection.cursor_instance.executions[0][1]
    assert insert_params[0:4] == (3, 5, 42, "2026-07-14T10:00:00")
    assert insert_params[-1] == "secure-token"
    assert connection.cursor_instance.executions[1][1] == (3,)
    assert connection.commits == 1


def test_response_save_locks_assessment_and_uses_upsert(monkeypatch):
    connection = install_connection(
        monkeypatch,
        [
            {
                "contains": "SELECT status, GREATEST",
                "fetchone": ("in_progress", False),
            },
            {"contains": "INSERT INTO mcq_responses", "rowcount": 1},
        ],
    )

    assessment_db.save_mcq_response(9, 2, "B", True, 12)

    upsert_sql, params = connection.cursor_instance.executions[1]
    assert "ON CONFLICT (assessment_id, question_id) DO UPDATE" in upsert_sql
    assert params == (9, 2, "B", True, 12)
    assert connection.commits == 1


def test_response_save_rejects_completed_assessment(monkeypatch):
    connection = install_connection(
        monkeypatch,
        [
            {
                "contains": "SELECT status, GREATEST",
                "fetchone": ("completed", False),
            }
        ],
    )

    with pytest.raises(assessment_db.AssessmentStateError, match="not active"):
        assessment_db.save_mcq_response(9, 2, "B", True, 12)

    assert connection.commits == 0


def test_response_save_rejects_assessment_after_deadline(monkeypatch):
    connection = install_connection(
        monkeypatch,
        [
            {
                "contains": "SELECT status, GREATEST",
                "fetchone": ("in_progress", True),
            }
        ],
    )

    with pytest.raises(assessment_db.AssessmentStateError, match="time limit"):
        assessment_db.save_mcq_response(9, 2, "B", True, 12)

    assert connection.commits == 0


def test_update_scores_persists_recommendation_and_completes_schedule(monkeypatch):
    connection = install_connection(
        monkeypatch,
        [
            {"contains": "UPDATE assessments", "fetchone": (7,), "rowcount": 1},
            {"contains": "UPDATE scheduled_assessments", "rowcount": 1},
        ],
    )

    overall = assessment_db.update_assessment_scores(
        9,
        technical_score=80,
        psychometric_score=60,
        decision="Recommend for Hire",
        rationale="Strong result",
        scheduled_assessment_id=7,
        hiring_recommendation="Proceed to HR discussion",
    )

    assert overall == pytest.approx(74.0)
    assessment_params = connection.cursor_instance.executions[0][1]
    assert assessment_params[2] == pytest.approx(74.0)
    assert assessment_params[5] == "Proceed to HR discussion"
    assert connection.cursor_instance.executions[1][1] == (9, 7, 9)
    assert connection.commits == 1


def test_final_decision_updates_assessment_and_candidate_in_one_commit(monkeypatch):
    connection = install_connection(
        monkeypatch,
        [
            {
                "contains": "FROM assessments a JOIN candidates c",
                "fetchone": (
                    3,
                    80,
                    60,
                    "Strong result",
                    "completed",
                    "Recommend for Hire",
                    "Ada Candidate",
                    "ada@example.com",
                    "completed",
                ),
            },
            {"contains": "UPDATE assessments", "rowcount": 1},
            {"contains": "UPDATE candidates", "rowcount": 1},
        ],
    )

    result = assessment_db.record_final_decision(9, "hire", "Approved")

    assert result == {
        "assessment_id": 9,
        "candidate_id": 3,
        "candidate_name": "Ada Candidate",
        "candidate_email": "ada@example.com",
        "decision": "Hire",
        "status": "hired",
        "technical_score": 80.0,
        "psychometric_score": 60.0,
        "overall_score": pytest.approx(74.0),
        "rationale": "Approved",
        "should_notify": True,
    }
    assert connection.cursor_instance.executions[1][1] == (
        pytest.approx(74.0),
        "Hire",
        "Approved",
        9,
    )
    assert connection.cursor_instance.executions[2][1] == ("hired", 3)
    assert connection.commits == 1
    assert not connection.cursor_instance.steps


def test_final_decision_retry_does_not_request_duplicate_email(monkeypatch):
    connection = install_connection(
        monkeypatch,
        [
            {
                "contains": "FROM assessments a JOIN candidates c",
                "fetchone": (
                    3,
                    80,
                    60,
                    "Approved",
                    "completed",
                    "Hire",
                    "Ada Candidate",
                    "ada@example.com",
                    "hired",
                ),
            },
            {"contains": "UPDATE assessments", "rowcount": 1},
            {"contains": "UPDATE candidates", "rowcount": 1},
        ],
    )

    result = assessment_db.record_final_decision(9, "hire", "Approved")

    assert result["should_notify"] is False
    assert connection.commits == 1


def test_finalize_scores_and_transitions_every_link_in_one_commit(monkeypatch):
    connection = install_connection(
        monkeypatch,
        [
            {
                "contains": "FROM assessments a LEFT JOIN scheduled_assessments",
                "fetchone": (
                    3,
                    7,
                    "in_progress",
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    True,
                    42,
                    4_200,
                ),
            },
            {
                "contains": "FROM mcq_responses",
                "fetchone": (4, 3),
            },
            {
                "contains": "FROM coding_submissions",
                "fetchone": (7, 10),
            },
            {
                "contains": "FROM psychometric_responses",
                "fetchall": [("leadership", 8), ("teamwork", 6)],
            },
            {"contains": "UPDATE assessments", "rowcount": 1},
            {"contains": "UPDATE scheduled_assessments", "rowcount": 1},
            {"contains": "UPDATE candidates", "rowcount": 1},
        ],
    )

    result = assessment_db.finalize_assessment(9)

    assert result["job_id"] == 42
    assert result["scores"] == {
        "mcq": 75.0,
        "coding": 70.0,
        "technical": 73.0,
        "psychometric": 70.0,
        "overall": 72.1,
    }
    assert result["decision"] == "Recommend for Hire"
    assert result["ai_recommendation"] == "Proceed to HR discussion"
    update_params = connection.cursor_instance.executions[4][1]
    assert update_params[5] == "Proceed to HR discussion"
    assert update_params[6] == assessment_db.ASSESSMENT_DURATION_SECONDS
    assert result["time_elapsed_seconds"] == assessment_db.ASSESSMENT_DURATION_SECONDS
    assert connection.commits == 1
    assert not connection.cursor_instance.steps


def test_submit_mcq_validates_against_server_questions(
    monkeypatch, answers_client
):
    saved = {}
    monkeypatch.setattr(
        interviewee_answers,
        "verify_assessment_access_token",
        lambda token, aid, **_kwargs: True,
    )
    monkeypatch.setattr(
        interviewee_answers,
        "get_assessment_by_id",
        lambda aid: {"id": aid, "status": "in_progress"},
    )
    monkeypatch.setattr(
        interviewee_answers,
        "get_assessment_questions",
        lambda aid: {
            "mcq_questions": [
                {
                    "id": 2,
                    "options": ["one", "two", "three", "four"],
                    "correct_answer": "B",
                }
            ]
        },
    )
    monkeypatch.setattr(
        interviewee_answers,
        "save_mcq_response",
        lambda **kwargs: saved.update(kwargs),
    )

    response = answers_client.post(
        "/assessment/9/submit-answer",
        headers={"X-Assessment-Token": "secure-token"},
        json={
            "type": "mcq",
            "questionId": 2,
            "answer": "b",
            "timeSpent": 12,
        },
    )

    assert response.status_code == 200
    assert saved == {
        "assessment_id": 9,
        "question_id": 2,
        "selected_answer": "B",
        "is_correct": True,
        "time_spent": 12,
    }


def test_complete_route_returns_transaction_result(monkeypatch, answers_client):
    result = {
        "assessment_id": 9,
        "candidate_id": 3,
        "scores": {"overall": 72.1},
        "decision": "Recommend for Hire",
        "ai_recommendation": "Proceed to HR discussion",
    }
    monkeypatch.setattr(
        interviewee_answers,
        "verify_assessment_access_token",
        lambda token, aid, **_kwargs: True,
    )
    monkeypatch.setattr(
        interviewee_answers, "finalize_assessment", lambda aid: result
    )

    response = answers_client.post(
        "/assessment/9/complete",
        headers={"X-Assessment-Token": "secure-token"},
    )

    assert response.status_code == 200
    assert response.get_json()["data"] == result
