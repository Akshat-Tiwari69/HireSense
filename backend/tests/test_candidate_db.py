"""Candidate repository transaction and mapping tests."""

from contextlib import contextmanager
from pathlib import Path

import candidate_db


class FakeCursor:
    def __init__(self):
        self.calls = []

    def execute(self, query, params=None):
        self.calls.append((query, params))

    def fetchone(self):
        return (99,)


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
    assert connection.cursor_instance.calls[0][1][1] == "candidate@example.com"
    assert connection.cursor_instance.calls[0][1][-1] == 12
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
