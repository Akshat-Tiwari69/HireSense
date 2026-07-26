"""Candidate repository transaction and mapping tests."""

from contextlib import contextmanager
from pathlib import Path

import candidate_db
import psycopg2
import pytest
from user_db import DuplicateEmailError


class FakeCursor:
    def __init__(self):
        self.calls = []

    def execute(self, query, params=None):
        self.calls.append((query, params))

    def fetchone(self):
        return (99,)

    def fetchall(self):
        return []


class FakeConnection:
    def __init__(self):
        self.cursor_instance = FakeCursor()
        self.committed = False

    def cursor(self):
        return self.cursor_instance

    def commit(self):
        self.committed = True


def test_candidate_application_creates_candidate_and_match_atomically(monkeypatch):
    connection = FakeConnection()

    @contextmanager
    def fake_db_connection():
        yield connection

    monkeypatch.setattr(candidate_db, "db_connection", fake_db_connection)

    candidate_id = candidate_db.insert_candidate_application(
        name="Candidate",
        email="candidate@example.com",
        phone="123",
        resume_path="uploads/resume.pdf",
        parsed_data={"skills": ["Python"], "experience": 3, "match_score": 82},
        job_id=12,
        ai_reasoning="Strong match",
    )

    assert candidate_id == 99
    assert len(connection.cursor_instance.calls) == 2
    insert_query = " ".join(connection.cursor_instance.calls[0][0].split())
    assert "FROM job_descriptions j" in insert_query
    assert "j.sector_id" in insert_query
    assert connection.cursor_instance.calls[0][1][1] == "candidate@example.com"
    assert connection.cursor_instance.calls[0][1][-2:] == (12, 12)
    assert connection.cursor_instance.calls[1][1] == (99, 12, 82, "Strong match")
    assert connection.committed is True


def test_candidate_application_normalizes_email_before_insert(monkeypatch):
    connection = FakeConnection()

    @contextmanager
    def fake_db_connection():
        yield connection

    monkeypatch.setattr(candidate_db, "db_connection", fake_db_connection)

    candidate_db.insert_candidate_application(
        name="Candidate",
        email="  Candidate@Example.COM ",
        phone="123",
        resume_path="uploads/resume.pdf",
        parsed_data={"skills": [], "experience": 0, "match_score": 50},
        job_id=12,
    )

    inserted_values = connection.cursor_instance.calls[0][1]
    assert inserted_values[1] == "candidate@example.com"


def test_canonical_and_upgrade_sql_enforce_case_insensitive_candidate_email():
    project_root = Path(__file__).resolve().parents[2]
    canonical_sql = (project_root / "database" / "schema_postgres.sql").read_text()
    migration_sql = (
        project_root
        / "database"
        / "migrations"
        / "20260713_reconcile_canonical_schema.sql"
    ).read_text()

    expected_index = "idx_candidates_email_lower_unique"
    expected_expression = "ON candidates(LOWER(email))"
    assert expected_index in canonical_sql
    assert expected_expression in canonical_sql
    assert expected_index in migration_sql
    assert expected_expression in migration_sql


def test_candidate_application_maps_unique_email_race_to_duplicate_error(monkeypatch):
    class DuplicateCursor:
        def execute(self, _query, _params=None):
            raise psycopg2.errors.UniqueViolation("private duplicate detail")

    class DuplicateConnection:
        def cursor(self):
            return DuplicateCursor()

    @contextmanager
    def fake_db_connection():
        yield DuplicateConnection()

    monkeypatch.setattr(candidate_db, "db_connection", fake_db_connection)

    with pytest.raises(DuplicateEmailError, match="Email already exists"):
        candidate_db.insert_candidate_application(
            name="Candidate",
            email="candidate@example.test",
            phone="123",
            resume_path="uploads/resume.pdf",
            parsed_data={"skills": [], "experience": 0, "match_score": 50},
            job_id=12,
        )


def test_interviewer_candidate_query_only_returns_assignments_and_claimable_queue(
    monkeypatch,
):
    connection = FakeConnection()

    @contextmanager
    def fake_db_connection():
        yield connection

    monkeypatch.setattr(candidate_db, "db_connection", fake_db_connection)

    assert candidate_db.get_interviewer_candidates(7) == []

    query, params = connection.cursor_instance.calls[0]
    compact_query = " ".join(query.split())
    assert params == (7, 7)
    assert "assignment.assessment_id" in compact_query
    assert "own_assignment.interviewer_id = %s" in compact_query
    assert "c.status IN ('applied', 'pending', 'absence_of_details')" in compact_query
    assert "NOT EXISTS" in compact_query


def test_interviewer_candidate_query_applies_optional_sector_scope(monkeypatch):
    connection = FakeConnection()

    @contextmanager
    def fake_db_connection():
        yield connection

    monkeypatch.setattr(candidate_db, "db_connection", fake_db_connection)

    assert candidate_db.get_interviewer_candidates(7, sector_id=2) == []

    query, params = connection.cursor_instance.calls[0]
    compact_query = " ".join(query.split())
    assert params == (7, 7, 2)
    assert ") AND c.sector_id = %s" in compact_query


def test_interviewer_candidate_returns_assessment_status_separately(monkeypatch):
    connection = FakeConnection()
    connection.cursor_instance.fetchall = lambda: [
        (
            7, "Candidate", "candidate@example.com", "123", "resume.pdf",
            '["Python"]', 3, "BSc", 88, "Potential", None, None,
            "applied", None, None, 41, None, "in_progress",
        )
    ]

    @contextmanager
    def fake_db_connection():
        yield connection

    monkeypatch.setattr(candidate_db, "db_connection", fake_db_connection)

    candidate = candidate_db.get_interviewer_candidates(9)[0]

    query = " ".join(connection.cursor_instance.calls[0][0].split())
    assert "sa.status AS assessment_status" in query
    assert candidate["status"] == "applied"
    assert candidate["assessment_status"] == "in_progress"
