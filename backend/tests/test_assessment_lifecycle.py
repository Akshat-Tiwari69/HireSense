"""Transaction-level tests for assessment scheduling, responses, and completion."""

from contextlib import contextmanager
import hashlib
from pathlib import Path

import pytest
from flask import Flask

import assessment_db
import interviewee_answers
import questions_bank


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


def test_psychometric_scoring_does_not_depend_on_option_position_distance():
    assert interviewee_answers._psychometric_option_score(1, 1) == 10
    assert interviewee_answers._psychometric_option_score(0, 1) == 0
    assert interviewee_answers._psychometric_option_score(2, 1) == 0
    assert interviewee_answers._psychometric_option_score(3, 1) == 0


def test_coding_answer_is_rejected_before_loading_questions_when_runner_is_disabled(
    monkeypatch, answers_client
):
    monkeypatch.setattr(
        interviewee_answers,
        "verify_assessment_access_token",
        lambda *_args, **_kwargs: True,
    )
    monkeypatch.setattr(
        interviewee_answers,
        "get_assessment_by_id",
        lambda _assessment_id: {"status": "in_progress"},
    )
    monkeypatch.setattr(interviewee_answers, "code_runner_enabled", lambda: False)
    monkeypatch.setattr(
        interviewee_answers,
        "get_assessment_questions",
        lambda *_args: (_ for _ in ()).throw(
            AssertionError("disabled runner loaded coding questions")
        ),
    )

    response = answers_client.post(
        "/assessment/9/submit-answer",
        headers={"X-Assessment-Token": "candidate-token"},
        json={
            "type": "coding",
            "questionId": 1,
            "language": "python",
            "code": "print('hello')",
        },
    )

    assert response.status_code == 503
    assert response.get_json()["message"] == (
        "Coding assessments are temporarily unavailable."
    )


def test_fallback_psychometric_scenario_can_be_scored_and_saved(
    monkeypatch, answers_client
):
    scenarios = questions_bank.get_psychometric_scenarios(count=3)
    assert all(
        isinstance(scenario.get("optimal_choice"), int)
        and 0 <= scenario["optimal_choice"] < len(scenario["options"])
        for scenario in scenarios
    )
    saved = {}
    monkeypatch.setattr(
        interviewee_answers,
        "verify_assessment_access_token",
        lambda *_args, **_kwargs: True,
    )
    monkeypatch.setattr(
        interviewee_answers,
        "get_assessment_by_id",
        lambda _assessment_id: {"status": "in_progress"},
    )
    monkeypatch.setattr(
        interviewee_answers,
        "get_assessment_questions",
        lambda _assessment_id: {"psychometric_scenarios": scenarios},
    )
    monkeypatch.setattr(
        interviewee_answers,
        "save_psychometric_response",
        lambda **kwargs: saved.update(kwargs),
    )

    response = answers_client.post(
        "/assessment/9/submit-answer",
        headers={"X-Assessment-Token": "candidate-token"},
        json={
            "type": "psychometric",
            "questionId": scenarios[0]["id"],
            "selectedOption": scenarios[0]["optimal_choice"],
        },
    )

    assert response.status_code == 200
    assert saved["score"] == 10


def test_start_is_atomic_and_copies_scheduled_job(monkeypatch):
    connection = install_connection(
        monkeypatch,
        [
            {
                "contains": "FROM scheduled_assessments WHERE access_token_hash = %s FOR UPDATE",
                "fetchone": (7, 3, 42, "scheduled"),
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
    assert connection.cursor_instance.executions[0][1] == (
        hashlib.sha256(b"secure-token").hexdigest(),
    )
    insert_params = connection.cursor_instance.executions[2][1]
    assert insert_params == (3, 42, 7)
    schedule_update_sql, schedule_update_params = (
        connection.cursor_instance.executions[3]
    )
    assert "assessment_id" not in schedule_update_sql
    assert schedule_update_params == (7,)
    assert connection.commits == 1
    assert not connection.cursor_instance.steps


def test_resume_rejects_assessment_after_deadline(monkeypatch):
    connection = install_connection(
        monkeypatch,
        [
            {
                "contains": "FROM scheduled_assessments WHERE access_token_hash = %s FOR UPDATE",
                "fetchone": (7, 3, 42, "in_progress"),
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
            {
                "contains": "SELECT status, sector_id, best_match_job_id FROM candidates",
                "fetchone": ("applied", 2, 42),
            },
            {"contains": "FROM job_descriptions jd", "fetchone": (42,)},
            {
                "contains": "FROM scheduled_assessments WHERE candidate_id = %s AND status IN",
                "fetchone": None,
            },
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
    insert_params = connection.cursor_instance.executions[3][1]
    assert insert_params[0:4] == (3, 5, 42, "2026-07-14T10:00:00")
    assert insert_params[-1] == hashlib.sha256(b"secure-token").hexdigest()
    assert "secure-token" not in insert_params
    assert connection.cursor_instance.executions[4][1] == (3,)
    assert connection.commits == 1
    assert not connection.cursor_instance.steps


def test_failed_invitation_cancels_schedule_and_invalidates_token(monkeypatch):
    monkeypatch.setattr(
        assessment_db,
        "generate_assessment_token",
        lambda: "discarded-replacement-token",
    )
    connection = install_connection(
        monkeypatch,
        [
            {
                "contains": "FROM scheduled_assessments sa LEFT JOIN assessments a",
                "fetchone": (3, "scheduled", None),
            },
            {"contains": "UPDATE scheduled_assessments", "rowcount": 1},
            {"contains": "UPDATE candidates", "rowcount": 1},
        ],
    )

    assert assessment_db.cancel_schedule_after_invitation_failure(7, 5) is True

    schedule_sql, schedule_params = connection.cursor_instance.executions[1]
    assert "access_token_hash = %s" in schedule_sql
    assert "status = 'cancelled'" in schedule_sql
    assert schedule_params == (
        hashlib.sha256(b"discarded-replacement-token").hexdigest(),
        7,
    )
    candidate_sql, candidate_params = connection.cursor_instance.executions[2]
    assert "status = 'applied'" in candidate_sql
    assert candidate_params == (3,)
    assert connection.commits == 1
    assert not connection.cursor_instance.steps


@pytest.mark.parametrize(
    ("schedule_status", "assessment_id"),
    [("in_progress", None), ("scheduled", 99)],
)
def test_failed_invitation_does_not_cancel_a_started_assessment(
    monkeypatch, schedule_status, assessment_id
):
    connection = install_connection(
        monkeypatch,
        [
            {
                "contains": "FROM scheduled_assessments sa LEFT JOIN assessments a",
                "fetchone": (3, schedule_status, assessment_id),
            },
        ],
    )

    assert assessment_db.cancel_schedule_after_invitation_failure(7, 5) is False
    assert connection.commits == 0
    assert not connection.cursor_instance.steps


def test_schedule_transaction_rejects_an_unavailable_or_unauthorized_job(monkeypatch):
    connection = install_connection(
        monkeypatch,
        [
            {
                "contains": "SELECT status, sector_id, best_match_job_id FROM candidates",
                "fetchone": ("applied", 2, 42),
            },
            {
                "contains": "FROM job_descriptions jd",
                "fetchone": None,
            },
        ],
    )

    with pytest.raises(
        assessment_db.AssessmentStateError,
        match="not open or authorized",
    ):
        assessment_db.create_scheduled_assessment(
            candidate_id=3,
            interviewer_id=5,
            scheduled_time="2099-01-01T00:00:00Z",
            is_technical_role=False,
            questions_data={"mcq_questions": [], "psychometric_scenarios": []},
            job_id=99,
            reviewer_sector_id=2,
            access_token="secure-token",
        )

    assert connection.commits == 0
    assert not connection.cursor_instance.steps


@pytest.mark.parametrize("candidate_status", ["under_review", "completed", "hired", "rejected"])
def test_schedule_rejects_candidate_with_active_or_terminal_state(
    monkeypatch, candidate_status
):
    connection = install_connection(
        monkeypatch,
        [
            {
                "contains": "SELECT status, sector_id, best_match_job_id FROM candidates",
                "fetchone": (candidate_status, 2, 42),
            },
        ],
    )

    with pytest.raises(assessment_db.AssessmentStateError, match="cannot be scheduled"):
        assessment_db.create_scheduled_assessment(
            candidate_id=3,
            interviewer_id=5,
            scheduled_time="2026-07-14T10:00:00",
        )

    assert connection.commits == 0
    assert not connection.cursor_instance.steps


def test_schedule_rejects_an_existing_active_schedule(monkeypatch):
    connection = install_connection(
        monkeypatch,
        [
            {
                "contains": "SELECT status, sector_id, best_match_job_id FROM candidates",
                "fetchone": ("applied", 2, 42),
            },
            {
                "contains": "FROM scheduled_assessments WHERE candidate_id = %s AND status IN",
                "fetchone": (7,),
            },
        ],
    )

    with pytest.raises(assessment_db.AssessmentStateError, match="active assessment"):
        assessment_db.create_scheduled_assessment(
            candidate_id=3,
            interviewer_id=5,
            scheduled_time="2026-07-14T10:00:00",
        )

    assert connection.commits == 0
    assert not connection.cursor_instance.steps


def test_prestart_rejection_cancels_schedule_and_candidate_atomically(monkeypatch):
    connection = install_connection(
        monkeypatch,
        [
            {
                "contains": "FROM candidates c JOIN scheduled_assessments sa",
                "fetchone": (
                    "Ada Candidate",
                    "ada@example.com",
                    "under_review",
                    7,
                    "scheduled",
                ),
            },
            {"contains": "UPDATE scheduled_assessments", "rowcount": 1},
            {"contains": "UPDATE candidates", "rowcount": 1},
        ],
    )

    result = assessment_db.reject_scheduled_candidate(3, 5)

    assert result == {
        "candidate_id": 3,
        "candidate_name": "Ada Candidate",
        "candidate_email": "ada@example.com",
        "should_notify": True,
    }
    assert connection.cursor_instance.executions[0][1] == (3, 5)
    assert connection.cursor_instance.executions[1][1] == (7,)
    assert connection.cursor_instance.executions[2][1] == (3,)
    assert connection.commits == 1
    assert not connection.cursor_instance.steps


@pytest.mark.parametrize("schedule_status", ["in_progress", "completed"])
def test_rejection_cannot_override_started_or_completed_assessment(
    monkeypatch, schedule_status
):
    connection = install_connection(
        monkeypatch,
        [
            {
                "contains": "FROM candidates c JOIN scheduled_assessments sa",
                "fetchone": (
                    "Ada Candidate",
                    "ada@example.com",
                    "under_review",
                    7,
                    schedule_status,
                ),
            },
        ],
    )

    with pytest.raises(
        assessment_db.AssessmentStateError,
        match="before their assessment starts",
    ):
        assessment_db.reject_scheduled_candidate(3, 5)

    assert connection.commits == 0
    assert not connection.cursor_instance.steps


def test_rejection_retry_does_not_request_duplicate_email(monkeypatch):
    connection = install_connection(
        monkeypatch,
        [
            {
                "contains": "FROM candidates c JOIN scheduled_assessments sa",
                "fetchone": (
                    "Ada Candidate",
                    "ada@example.com",
                    "rejected",
                    7,
                    "cancelled",
                ),
            },
        ],
    )

    result = assessment_db.reject_scheduled_candidate(3, 5)

    assert result["should_notify"] is False
    assert connection.commits == 0
    assert not connection.cursor_instance.steps


def test_schema_prevents_parallel_active_schedules_for_a_candidate():
    project_root = Path(assessment_db.__file__).resolve().parent.parent
    schema_sql = (project_root / "database" / "schema_postgres.sql").read_text()
    migration_sql = (
        project_root
        / "database"
        / "migrations"
        / "20260713_reconcile_canonical_schema.sql"
    ).read_text()
    expected_index = "idx_scheduled_assessments_candidate_active_unique"
    expected_predicate = "WHERE status IN ('scheduled', 'in_progress')"

    assert expected_index in schema_sql
    assert expected_index in migration_sql
    assert expected_predicate in schema_sql
    assert expected_predicate in migration_sql


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
        "final_decision": "Hire",
        "status": "hired",
        "technical_score": 80.0,
        "psychometric_score": 60.0,
        "overall_score": pytest.approx(74.0),
        "final_rationale": "Approved",
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


def test_final_decision_cannot_be_changed_after_it_is_recorded(monkeypatch):
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
        ],
    )

    with pytest.raises(assessment_db.AssessmentStateError, match="already been recorded"):
        assessment_db.record_final_decision(9, "no-hire", "Changed mind")

    assert connection.commits == 0
    assert not connection.cursor_instance.steps


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
                    {
                        "mcq_questions": [{"id": index} for index in range(1, 5)],
                        "coding_problem": {
                            "test_cases": [{} for _index in range(10)]
                        },
                        "psychometric_scenarios": [
                            {"id": 1, "trait": "leadership"},
                            {"id": 2, "trait": "teamwork"},
                        ],
                    },
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
                "fetchall": [(1, 8), (2, 6)],
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
    assert result["automated_recommendation"] == "Recommend for Hire"
    assert result["recommended_next_step"] == "Proceed to HR discussion"
    update_params = connection.cursor_instance.executions[4][1]
    assert update_params[5] == "Proceed to HR discussion"
    assert update_params[6] == assessment_db.ASSESSMENT_DURATION_SECONDS
    assert result["time_elapsed_seconds"] == assessment_db.ASSESSMENT_DURATION_SECONDS
    schedule_update_sql, schedule_update_params = connection.cursor_instance.executions[5]
    assert "assessment_id" not in schedule_update_sql
    assert schedule_update_params == (7,)
    assert connection.commits == 1
    assert not connection.cursor_instance.steps


def test_finalize_counts_unanswered_assigned_questions_as_zero(monkeypatch):
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
                    False,
                    42,
                    {
                        "mcq_questions": [{"id": index} for index in range(1, 5)],
                        "psychometric_scenarios": [
                            {"id": 1, "trait": "leadership"},
                            {"id": 2, "trait": "teamwork"},
                        ],
                    },
                    600,
                ),
            },
            {"contains": "FROM mcq_responses", "fetchone": (1, 1)},
            {"contains": "FROM coding_submissions", "fetchone": (0, 0)},
            {
                "contains": "FROM psychometric_responses",
                "fetchall": [(1, 10)],
            },
            {"contains": "UPDATE assessments", "rowcount": 1},
            {"contains": "UPDATE scheduled_assessments", "rowcount": 1},
            {"contains": "UPDATE candidates", "rowcount": 1},
        ],
    )

    result = assessment_db.finalize_assessment(9)

    assert result["scores"] == {
        "mcq": 25.0,
        "coding": 0.0,
        "technical": 25.0,
        "psychometric": 50.0,
        "overall": 32.5,
    }
    assert result["psychometric_breakdown"] == {
        "leadership": 10.0,
        "teamwork": 0.0,
    }
    assert connection.commits == 1


def test_token_queries_follow_assessments_scheduled_assessment_id(monkeypatch):
    queries = []

    def token_lookup(query, params=()):
        queries.append((" ".join(query.split()), params))
        return None

    monkeypatch.setattr(assessment_db, "_fetch_one", token_lookup)

    assert assessment_db.get_assessment_by_token("secure-token") is None
    assert not assessment_db.verify_assessment_access_token("secure-token", 9)

    assert len(queries) == 2
    for query, _params in queries:
        assert "a.scheduled_assessment_id = sa.id" in query
        assert "sa.assessment_id" not in query


def test_schedule_lookup_derives_assessment_id_from_forward_link(monkeypatch):
    captured = {}

    def schedule_lookup(query, params=()):
        captured["query"] = " ".join(query.split())
        captured["params"] = params
        return (7, 3, 5, None, "scheduled", 99, True, None, None, None, 42)

    monkeypatch.setattr(assessment_db, "_fetch_one", schedule_lookup)

    schedule = assessment_db.get_scheduled_assessment_by_id(7)

    assert schedule["assessment_id"] == 99
    assert "a.scheduled_assessment_id = sa.id" in captured["query"]
    assert "sa.assessment_id" not in captured["query"]


def test_repeated_finalize_preserves_terminal_candidate_status(monkeypatch):
    connection = install_connection(
        monkeypatch,
        [
            {
                "contains": "FROM assessments a LEFT JOIN scheduled_assessments",
                "fetchone": (
                    3,
                    7,
                    "completed",
                    73,
                    70,
                    72.1,
                    "Recommend for Hire",
                    "Strong result",
                    "Proceed",
                    True,
                    42,
                    {
                        "mcq_questions": [{"id": index} for index in range(1, 5)],
                        "coding_problem": {
                            "test_cases": [{} for _index in range(10)]
                        },
                        "psychometric_scenarios": [],
                    },
                    4_200,
                ),
            },
            {"contains": "FROM mcq_responses", "fetchone": (4, 3)},
            {"contains": "FROM coding_submissions", "fetchone": (7, 10)},
            {"contains": "FROM psychometric_responses", "fetchall": []},
            {"contains": "UPDATE scheduled_assessments", "rowcount": 1},
            {"contains": "UPDATE candidates", "rowcount": 1},
        ],
    )

    assessment_db.finalize_assessment(9)

    candidate_update = connection.cursor_instance.executions[-1][0]
    assert "WHEN status IN ('hired', 'rejected') THEN status" in candidate_update


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


def test_submit_coding_does_not_persist_zero_when_runner_is_unavailable(
    monkeypatch, answers_client
):
    saved = []
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
        lambda _aid: {
            "coding_problem": {
                "id": 4,
                "starter_code": {"python": "def solve(value):\n    pass"},
                "test_cases": [{"input": "2", "expected": "4"}],
            }
        },
    )
    monkeypatch.setattr(
        interviewee_answers,
        "_evaluate_server_side",
        lambda *_args: (_ for _ in ()).throw(ConnectionError("runner offline")),
    )
    monkeypatch.setattr(
        interviewee_answers,
        "save_coding_submission",
        lambda **kwargs: saved.append(kwargs),
    )

    response = answers_client.post(
        "/assessment/9/submit-answer",
        headers={"X-Assessment-Token": "secure-token"},
        json={
            "type": "coding",
            "questionId": 4,
            "language": "python",
            "code": "def solve(value):\n    return value * 2",
        },
    )

    assert response.status_code == 503
    assert "not saved" in response.get_json()["message"].lower()
    assert saved == []


def test_submit_coding_rejects_problem_without_server_test_cases(
    monkeypatch, answers_client
):
    saved = []
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
        lambda _aid: {
            "coding_problem": {
                "id": 4,
                "starter_code": {"python": "def solve(value):\n    pass"},
                "test_cases": [],
            }
        },
    )
    monkeypatch.setattr(
        interviewee_answers,
        "save_coding_submission",
        lambda **kwargs: saved.append(kwargs),
    )

    response = answers_client.post(
        "/assessment/9/submit-answer",
        headers={"X-Assessment-Token": "secure-token"},
        json={
            "type": "coding",
            "questionId": 4,
            "language": "python",
            "code": "def solve(value):\n    return value * 2",
        },
    )

    assert response.status_code == 409
    assert saved == []


def test_complete_route_returns_candidate_safe_receipt_on_replay(
    monkeypatch, answers_client
):
    result = {
        "assessment_id": 9,
        "candidate_id": 3,
        "scores": {"overall": 72.1},
        "automated_recommendation": "Recommend for Hire",
        "automated_rationale": "Internal evaluator notes",
        "recommended_next_step": "Proceed to HR discussion",
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
    assert response.get_json()["data"] == {
        "assessment_id": 9,
        "status": "completed",
    }
    assert not {
        "automated_recommendation",
        "automated_rationale",
        "recommended_next_step",
    } & response.get_json()["data"].keys()


def test_latest_completed_assessment_ignores_newer_incomplete_attempts(monkeypatch):
    captured = {}

    def fetch_one(query, params):
        captured["query"] = " ".join(query.split())
        captured["params"] = params
        return (
            17,
            3,
            9,
            82,
            74,
            79.6,
            "Recommend for Hire",
            "Strong evidence",
            None,
            None,
            1,
            "completed",
            None,
            None,
            80,
            85,
            11,
            "Proceed to interview",
        )

    monkeypatch.setattr(assessment_db, "_fetch_one", fetch_one)

    result = assessment_db.get_latest_completed_assessment_by_candidate_id(3)

    assert result["id"] == 17
    assert captured["params"] == (3,)
    assert "WHERE a.candidate_id = %s AND a.status = 'completed'" in captured["query"]
    assert "ORDER BY a.completed_at DESC NULLS LAST, a.created_at DESC" in captured["query"]
