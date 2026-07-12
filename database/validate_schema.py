"""Validate the canonical PostgreSQL schema and its forward migration.

Static contract checks run without a database::

    python database/validate_schema.py

Pass a disposable PostgreSQL database to execute the schema and migration twice,
verify their idempotence, and exercise legacy-name backfills::

    python database/validate_schema.py --database-url postgresql://...

The integration check creates and drops an isolated temporary schema. It never
creates, changes, or deletes objects outside that schema.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import secrets
import sys


DATABASE_DIR = Path(__file__).resolve().parent
CANONICAL_SCHEMA = DATABASE_DIR / "schema_postgres.sql"
RECONCILIATION_MIGRATION = (
    DATABASE_DIR / "migrations" / "20260713_reconcile_canonical_schema.sql"
)

REQUIRED_COLUMNS = {
    "job_descriptions": {"created_by", "role_complexity_level"},
    "candidates": {"best_match_job_id"},
    "scheduled_assessments": {"job_id", "proctor_id"},
    "proctoring_events": {"is_reviewed"},
}

REQUIRED_UNIQUE_INDEXES = {
    "idx_assessments_scheduled_unique",
    "idx_mcq_assessment_question_unique",
    "idx_coding_assessment_problem_unique",
    "idx_psychometric_assessment_question_unique",
}

REQUIRED_FOREIGN_KEYS = {
    ("job_descriptions", "created_by", "users", "n"),
    ("candidates", "best_match_job_id", "job_descriptions", "n"),
    ("scheduled_assessments", "job_id", "job_descriptions", "n"),
    ("scheduled_assessments", "proctor_id", "users", "n"),
}


class ValidationError(RuntimeError):
    """Raised when the schema contract is incomplete or inconsistent."""


def _table_definition(sql: str, table_name: str) -> str:
    pattern = re.compile(
        rf"CREATE\s+TABLE\s+IF\s+NOT\s+EXISTS\s+{re.escape(table_name)}\s*\((.*?)\n\);",
        re.IGNORECASE | re.DOTALL,
    )
    match = pattern.search(sql)
    if match is None:
        raise ValidationError(f"canonical schema does not create {table_name}")
    return match.group(1)


def validate_static_contract() -> None:
    """Check canonical names and required definitions without PostgreSQL."""

    schema_sql = CANONICAL_SCHEMA.read_text(encoding="utf-8")
    migration_sql = RECONCILIATION_MIGRATION.read_text(encoding="utf-8")

    for table_name, expected_columns in REQUIRED_COLUMNS.items():
        definition = _table_definition(schema_sql, table_name)
        missing = {
            column
            for column in expected_columns
            if re.search(rf"^\s*{re.escape(column)}\s+", definition, re.MULTILINE)
            is None
        }
        if missing:
            raise ValidationError(
                f"{table_name} is missing canonical columns: {sorted(missing)}"
            )

    job_definition = _table_definition(schema_sql, "job_descriptions")
    candidate_definition = _table_definition(schema_sql, "candidates")
    if re.search(r"^\s*created_by_id\s+", job_definition, re.MULTILINE):
        raise ValidationError(
            "created_by_id must not appear in the canonical job table"
        )
    if re.search(r"^\s*job_id\s+", candidate_definition, re.MULTILINE):
        raise ValidationError(
            "candidates.job_id must not appear in the canonical schema"
        )
    if re.search(
        r"CREATE\s+TABLE\s+IF\s+NOT\s+EXISTS\s+admin_audit_log\b",
        schema_sql,
        re.IGNORECASE,
    ):
        raise ValidationError("admin_audit_log must not be a canonical table")

    for index_name in REQUIRED_UNIQUE_INDEXES:
        if not re.search(
            rf"CREATE\s+UNIQUE\s+INDEX\s+IF\s+NOT\s+EXISTS\s+{re.escape(index_name)}\b",
            schema_sql,
            re.IGNORECASE,
        ):
            raise ValidationError(f"canonical schema is missing {index_name}")

    for required_phrase in (
        "ADD COLUMN IF NOT EXISTS created_by",
        "ADD COLUMN IF NOT EXISTS best_match_job_id",
        "ADD COLUMN IF NOT EXISTS job_id",
        "ADD COLUMN IF NOT EXISTS proctor_id",
        "ADD COLUMN IF NOT EXISTS is_reviewed",
        "legacy_source",
        "admin_audit_log",
    ):
        if required_phrase.lower() not in migration_sql.lower():
            raise ValidationError(
                f"reconciliation migration is missing: {required_phrase}"
            )


def _query_scalar(cursor, query: str, parameters: tuple = ()):
    cursor.execute(query, parameters)
    row = cursor.fetchone()
    return row[0] if row else None


def _validate_database_contract(cursor, schema_name: str) -> None:
    actual_columns: dict[str, set[str]] = {}
    for table_name in REQUIRED_COLUMNS:
        cursor.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = %s AND table_name = %s
            """,
            (schema_name, table_name),
        )
        actual_columns[table_name] = {row[0] for row in cursor.fetchall()}

    for table_name, expected_columns in REQUIRED_COLUMNS.items():
        missing = expected_columns - actual_columns[table_name]
        if missing:
            raise ValidationError(
                f"database table {table_name} is missing: {sorted(missing)}"
            )

    cursor.execute(
        """
        SELECT indexname
        FROM pg_indexes
        WHERE schemaname = %s AND indexname = ANY(%s)
        """,
        (schema_name, list(REQUIRED_UNIQUE_INDEXES)),
    )
    existing_indexes = {row[0] for row in cursor.fetchall()}
    missing_indexes = REQUIRED_UNIQUE_INDEXES - existing_indexes
    if missing_indexes:
        raise ValidationError(
            f"database is missing unique indexes: {sorted(missing_indexes)}"
        )

    cursor.execute(
        """
        SELECT
            source_table.relname,
            source_column.attname,
            target_table.relname,
            constraint_record.confdeltype
        FROM pg_constraint AS constraint_record
        JOIN pg_class AS source_table
          ON source_table.oid = constraint_record.conrelid
        JOIN pg_namespace AS source_namespace
          ON source_namespace.oid = source_table.relnamespace
        JOIN pg_attribute AS source_column
          ON source_column.attrelid = source_table.oid
         AND source_column.attnum = ANY (constraint_record.conkey)
        JOIN pg_class AS target_table
          ON target_table.oid = constraint_record.confrelid
        WHERE source_namespace.nspname = %s
          AND constraint_record.contype = 'f'
        """,
        (schema_name,),
    )
    actual_foreign_keys = set(cursor.fetchall())
    missing_foreign_keys = REQUIRED_FOREIGN_KEYS - actual_foreign_keys
    if missing_foreign_keys:
        raise ValidationError(
            f"database is missing foreign keys: {sorted(missing_foreign_keys)}"
        )


def validate_against_postgres(database_url: str) -> None:
    """Execute both SQL artifacts twice inside an isolated schema."""

    try:
        import psycopg2
        from psycopg2 import sql
    except ImportError as exc:  # pragma: no cover - depends on local tooling
        raise ValidationError(
            "psycopg2 is required for --database-url validation"
        ) from exc

    schema_sql = CANONICAL_SCHEMA.read_text(encoding="utf-8")
    migration_sql = RECONCILIATION_MIGRATION.read_text(encoding="utf-8")
    schema_name = f"hiresense_schema_check_{secrets.token_hex(6)}"

    connection = psycopg2.connect(database_url)
    connection.autocommit = True
    cursor = connection.cursor()

    try:
        cursor.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema_name)))
        cursor.execute(
            sql.SQL("SET search_path TO {}, pg_catalog").format(
                sql.Identifier(schema_name)
            )
        )

        # Running the canonical schema twice proves fresh-install idempotence.
        cursor.execute(schema_sql)
        cursor.execute(schema_sql)
        _validate_database_contract(cursor, schema_name)

        # Add both known aliases and the action_type flavor of the old audit log.
        cursor.execute(
            """
            ALTER TABLE job_descriptions ADD COLUMN created_by_id INTEGER;
            ALTER TABLE candidates ADD COLUMN job_id INTEGER;
            ALTER TABLE scheduled_assessments
                DROP CONSTRAINT scheduled_assessments_job_id_fkey;
            ALTER TABLE scheduled_assessments
                DROP CONSTRAINT scheduled_assessments_proctor_id_fkey;
            ALTER TABLE scheduled_assessments
                ADD CONSTRAINT legacy_scheduled_job_fkey
                FOREIGN KEY (job_id) REFERENCES job_descriptions(id);
            ALTER TABLE scheduled_assessments
                ADD CONSTRAINT legacy_scheduled_proctor_fkey
                FOREIGN KEY (proctor_id) REFERENCES users(id);
            CREATE TABLE admin_audit_log (
                id SERIAL PRIMARY KEY,
                admin_id INTEGER NOT NULL REFERENCES users(id),
                action_type TEXT NOT NULL,
                entity_type TEXT,
                entity_id INTEGER,
                old_values TEXT,
                new_values TEXT,
                ip_address TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            INSERT INTO users (email, password_hash, role, name)
            VALUES ('schema-check@example.invalid', 'not-a-real-password', 'admin', 'Schema Check');
            INSERT INTO job_descriptions (title, created_by_id)
            VALUES ('Legacy job', 1);
            INSERT INTO candidates (
                name, email, phone, resume_path, job_id
            ) VALUES (
                'Legacy candidate', 'candidate@example.invalid', '0', '/dev/null', 1
            );
            INSERT INTO admin_audit_log (
                admin_id, action_type, entity_type, entity_id
            ) VALUES (1, 'legacy_create', 'job_posting', 1);
            """
        )

        # Running the migration twice proves upgrade idempotence.
        cursor.execute(migration_sql)
        cursor.execute(migration_sql)
        _validate_database_contract(cursor, schema_name)

        if (
            _query_scalar(
                cursor,
                "SELECT created_by FROM job_descriptions WHERE title = 'Legacy job'",
            )
            != 1
        ):
            raise ValidationError("created_by_id was not backfilled into created_by")
        if (
            _query_scalar(
                cursor,
                "SELECT best_match_job_id FROM candidates WHERE email = 'candidate@example.invalid'",
            )
            != 1
        ):
            raise ValidationError("candidates.job_id was not backfilled")
        if (
            _query_scalar(
                cursor,
                """
            SELECT COUNT(*)
            FROM audit_log
            WHERE details @> '{"legacy_source": "admin_audit_log", "legacy_id": 1}'::jsonb
            """,
            )
            != 1
        ):
            raise ValidationError("legacy audit row was not copied exactly once")

        # Duplicate legacy responses must be reported, never deleted arbitrarily.
        cursor.execute(
            """
            DROP INDEX idx_mcq_assessment_question_unique;
            INSERT INTO assessments (candidate_id) VALUES (1);
            INSERT INTO mcq_responses (
                assessment_id, question_id, selected_answer
            ) VALUES
                (1, 99, 'first historical answer'),
                (1, 99, 'second historical answer');
            """
        )
        cursor.execute(migration_sql)
        if (
            _query_scalar(
                cursor, "SELECT to_regclass('idx_mcq_assessment_question_unique')"
            )
            is not None
        ):
            raise ValidationError(
                "migration created a unique response index over duplicate legacy rows"
            )
        if (
            _query_scalar(
                cursor,
                "SELECT COUNT(*) FROM mcq_responses WHERE assessment_id = 1 AND question_id = 99",
            )
            != 2
        ):
            raise ValidationError("migration deleted duplicate legacy responses")
    finally:
        cursor.execute("RESET search_path")
        cursor.execute(
            sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(
                sql.Identifier(schema_name)
            )
        )
        cursor.close()
        connection.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--database-url",
        default=os.environ.get("SCHEMA_TEST_DATABASE_URL"),
        help="Disposable PostgreSQL DSN (or set SCHEMA_TEST_DATABASE_URL)",
    )
    args = parser.parse_args()

    try:
        validate_static_contract()
        print("Static schema contract: OK")
        if args.database_url:
            validate_against_postgres(args.database_url)
            print("PostgreSQL idempotence and legacy upgrade: OK")
        else:
            print("PostgreSQL integration check: skipped (no database URL supplied)")
    except ValidationError as exc:
        print(f"Schema validation failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
