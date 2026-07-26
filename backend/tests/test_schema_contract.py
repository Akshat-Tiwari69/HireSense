"""Contract tests for the one canonical PostgreSQL model."""

from pathlib import Path
import re
import sys


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY_ROOT))

from database.schema_contract import (  # noqa: E402
    APP_TABLES,
    FORBIDDEN_COLUMNS,
    REQUIRED_CHECK_CONSTRAINTS,
    REQUIRED_FOREIGN_KEYS,
    REQUIRED_NOT_NULL_COLUMNS,
    REQUIRED_UNIQUE_INDEXES,
    TABLE_COLUMNS,
)


def test_contract_lists_only_runtime_tables():
    assert APP_TABLES == {
        "assessments",
        "audit_log",
        "candidate_job_matches",
        "candidates",
        "coding_submissions",
        "custom_question_bank",
        "email_logs",
        "job_descriptions",
        "mcq_responses",
        "proctoring_violations",
        "psychometric_responses",
        "scheduled_assessments",
        "sectors",
        "users",
    }


def test_contract_has_no_known_duplicate_or_dead_columns():
    dead_columns = {
        ("users", "permissions"),
        ("candidates", "parsed_skills_json"),
        ("scheduled_assessments", "assessment_id"),
        ("scheduled_assessments", "access_token"),
        ("scheduled_assessments", "is_streaming"),
        ("scheduled_assessments", "stream_started_at"),
        ("scheduled_assessments", "stream_ended_at"),
        ("coding_submissions", "execution_time"),
        ("coding_submissions", "error_message"),
        ("custom_question_bank", "filename"),
    }

    actual_columns = {
        (table_name, column_name)
        for table_name, columns in TABLE_COLUMNS.items()
        for column_name in columns
    }

    assert actual_columns.isdisjoint(dead_columns)


def test_every_runtime_table_has_a_complete_primary_key_contract():
    assert set(TABLE_COLUMNS) == APP_TABLES
    assert all("id" in columns for columns in TABLE_COLUMNS.values())


def test_canonical_sql_creates_exactly_the_runtime_tables():
    schema_sql = (
        REPOSITORY_ROOT / "database" / "schema_postgres.sql"
    ).read_text(encoding="utf-8")
    created_tables = {
        match.group(1).lower()
        for match in re.finditer(
            r"CREATE\s+TABLE\s+IF\s+NOT\s+EXISTS\s+([a-z_]+)",
            schema_sql,
            re.IGNORECASE,
        )
    }

    assert created_tables == APP_TABLES


def test_canonical_sql_names_every_required_integrity_constraint():
    schema_sql = (
        REPOSITORY_ROOT / "database" / "schema_postgres.sql"
    ).read_text(encoding="utf-8").lower()

    for constraint_name in REQUIRED_CHECK_CONSTRAINTS:
        assert f"constraint {constraint_name.lower()} check" in schema_sql

    for index_name in REQUIRED_UNIQUE_INDEXES:
        assert f"unique index if not exists {index_name.lower()}" in schema_sql


def test_sector_scoped_staff_roles_require_a_sector_in_fresh_and_upgraded_schemas():
    schema_sql = (REPOSITORY_ROOT / "database" / "schema_postgres.sql").read_text(
        encoding="utf-8"
    ).lower()
    migration_sql = (
        REPOSITORY_ROOT
        / "database"
        / "migrations"
        / "20260713_reconcile_canonical_schema.sql"
    ).read_text(encoding="utf-8").lower()

    expression = "role not in ('sector_admin', 'recruiter') or sector_id is not null"
    assert "constraint users_sector_scope_check check" in schema_sql
    assert expression in schema_sql
    assert "'users', 'users_sector_scope_check'" in migration_sql
    assert expression in migration_sql


def test_sector_deletion_is_restricted_while_staff_still_reference_it():
    schema_sql = (REPOSITORY_ROOT / "database" / "schema_postgres.sql").read_text(
        encoding="utf-8"
    ).lower()
    migration_sql = (
        REPOSITORY_ROOT
        / "database"
        / "migrations"
        / "20260713_reconcile_canonical_schema.sql"
    ).read_text(encoding="utf-8").lower()

    assert "sector_id integer references sectors(id) on delete restrict" in schema_sql
    assert ("users", "sector_id", "sectors", "r") in REQUIRED_FOREIGN_KEYS
    assert "users_sector_id_fkey" in migration_sql
    assert "constraint_record.confdeltype <> 'r'" in migration_sql


def test_job_work_mode_replaces_the_misnamed_location_column_everywhere():
    schema_sql = (REPOSITORY_ROOT / "database" / "schema_postgres.sql").read_text(
        encoding="utf-8"
    )
    migration_sql = (
        REPOSITORY_ROOT
        / "database"
        / "migrations"
        / "20260713_reconcile_canonical_schema.sql"
    ).read_text(encoding="utf-8")

    assert "work_mode" in TABLE_COLUMNS["job_descriptions"]
    assert "location" not in TABLE_COLUMNS["job_descriptions"]
    assert ("job_descriptions", "location") in FORBIDDEN_COLUMNS
    assert ("job_descriptions", "work_mode") in REQUIRED_NOT_NULL_COLUMNS
    assert "job_descriptions_work_mode_check" in REQUIRED_CHECK_CONSTRAINTS

    job_definition = schema_sql.split(
        "CREATE TABLE IF NOT EXISTS job_descriptions (", 1
    )[1].split("\n);", 1)[0]
    assert "work_mode TEXT NOT NULL DEFAULT 'On-Site'" in job_definition
    assert "location" not in job_definition
    assert "work_mode IN ('Remote', 'On-Site', 'Hybrid')" in job_definition

    assert "RENAME COLUMN location TO work_mode" in migration_sql
    assert "DROP COLUMN location" in migration_sql
    assert "ALTER COLUMN work_mode SET NOT NULL" in migration_sql
    assert "work_mode IN ('Remote', 'On-Site', 'Hybrid')" in migration_sql


def test_reconciliation_removes_proven_dead_schema_objects():
    migration_sql = (
        REPOSITORY_ROOT
        / "database"
        / "migrations"
        / "20260713_reconcile_canonical_schema.sql"
    ).read_text(encoding="utf-8").lower()

    for table_name in {"questions", "proctoring_events", "sector_email_configs"}:
        assert f"drop table if exists {table_name}" in migration_sql

    for table_name, column_name in {
        ("users", "permissions"),
        ("candidates", "parsed_skills_json"),
        ("scheduled_assessments", "is_streaming"),
        ("scheduled_assessments", "stream_started_at"),
        ("scheduled_assessments", "stream_ended_at"),
        ("coding_submissions", "execution_time"),
        ("coding_submissions", "error_message"),
        ("custom_question_bank", "filename"),
    }:
        assert re.search(
            rf"alter\s+table\s+{table_name}.*?drop\s+column\s+if\s+exists\s+{column_name}",
            migration_sql,
            re.DOTALL,
        )


def test_reconciliation_refuses_to_drop_populated_legacy_tables():
    migration_sql = (
        REPOSITORY_ROOT
        / "database"
        / "migrations"
        / "20260713_reconcile_canonical_schema.sql"
    ).read_text(encoding="utf-8").lower()

    guard_start = migration_sql.index("legacy_retired_table")
    first_drop = migration_sql.index("drop table if exists proctoring_events")

    assert guard_start < first_drop
    assert "select exists (select 1 from public.%i limit 1)" in migration_sql
    assert "contains data and cannot be dropped automatically" in migration_sql
    for table_name in {"questions", "proctoring_events", "sector_email_configs"}:
        assert f"'{table_name}'" in migration_sql[guard_start:first_drop]


def test_legacy_admin_audit_log_is_dropped_only_after_every_row_is_copied():
    migration_sql = (
        REPOSITORY_ROOT
        / "database"
        / "migrations"
        / "20260713_reconcile_canonical_schema.sql"
    ).read_text(encoding="utf-8").lower()

    audit_block = migration_sql.split(
        "-- canonical audit log and migration of the legacy admin-only audit table",
        1,
    )[1].split("drop table if exists admin_audit_log", 1)[0]
    compact_audit_block = re.sub(r"\s+", " ", audit_block)

    assert "legacy rows were not copied" not in audit_block
    assert "contains rows but has neither action nor action_type" in compact_audit_block
    assert "not every admin_audit_log row was copied" in compact_audit_block
    assert audit_block.count("legacy_source', 'admin_audit_log'") >= 2


def test_canonical_sql_has_no_known_redundant_indexes():
    schema_sql = (
        REPOSITORY_ROOT / "database" / "schema_postgres.sql"
    ).read_text(encoding="utf-8").lower()

    for index_name in {
        "idx_users_email",
        "idx_candidates_email",
        "idx_candidate_job_matches_candidate",
        "idx_mcq_assessment",
        "idx_coding_assessment",
        "idx_psychometric_assessment",
        "idx_scheduled_assessments_token",
    }:
        assert f"index if not exists {index_name.lower()} " not in schema_sql


def test_sql_keeps_only_the_assessment_to_schedule_link():
    schema_sql = (
        REPOSITORY_ROOT / "database" / "schema_postgres.sql"
    ).read_text(encoding="utf-8")
    migration_sql = (
        REPOSITORY_ROOT
        / "database"
        / "migrations"
        / "20260713_reconcile_canonical_schema.sql"
    ).read_text(encoding="utf-8")
    scheduled_definition = schema_sql.split(
        "CREATE TABLE IF NOT EXISTS scheduled_assessments (", 1
    )[1].split("\n);", 1)[0]

    assert "assessment_id" not in scheduled_definition
    assert "fk_sched_assessment" not in schema_sql
    assert "SET scheduled_assessment_id" in migration_sql
    assert "DROP COLUMN IF EXISTS assessment_id" in migration_sql


def test_legacy_reverse_schedule_links_abort_on_ambiguous_or_conflicting_data():
    migration_sql = (
        REPOSITORY_ROOT
        / "database"
        / "migrations"
        / "20260713_reconcile_canonical_schema.sql"
    ).read_text(encoding="utf-8").lower()
    reverse_link_block = migration_sql.split(
        "and column_name = 'assessment_id'",
        1,
    )[1].split("alter table scheduled_assessments", 1)[0]
    compact_block = re.sub(r"\s+", " ", reverse_link_block)

    assert "having count(*) > 1" in compact_block
    assert "multiple schedules reference the same legacy assessment" in compact_block
    assert "conflicts with the canonical schedule link" in compact_block
    assert "linked_assessment.scheduled_assessment_id <> legacy_schedule.id" in compact_block
