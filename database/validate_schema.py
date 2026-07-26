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

try:
    from .schema_contract import (
        APP_TABLES,
        FORBIDDEN_COLUMNS,
        FORBIDDEN_INDEXES,
        FORBIDDEN_TABLES,
        REQUIRED_CHECK_CONSTRAINTS,
        REQUIRED_FOREIGN_KEYS,
        REQUIRED_INDEXES,
        REQUIRED_NOT_NULL_COLUMNS,
        REQUIRED_UNIQUE_INDEXES,
        TABLE_COLUMNS,
        TIMESTAMP_COLUMNS,
    )
except ImportError:  # Direct execution: python database/validate_schema.py
    from schema_contract import (
        APP_TABLES,
        FORBIDDEN_COLUMNS,
        FORBIDDEN_INDEXES,
        FORBIDDEN_TABLES,
        REQUIRED_CHECK_CONSTRAINTS,
        REQUIRED_FOREIGN_KEYS,
        REQUIRED_INDEXES,
        REQUIRED_NOT_NULL_COLUMNS,
        REQUIRED_UNIQUE_INDEXES,
        TABLE_COLUMNS,
        TIMESTAMP_COLUMNS,
    )


DATABASE_DIR = Path(__file__).resolve().parent
CANONICAL_SCHEMA = DATABASE_DIR / "schema_postgres.sql"
RECONCILIATION_MIGRATION = (
    DATABASE_DIR / "migrations" / "20260713_reconcile_canonical_schema.sql"
)

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

    if APP_TABLES & FORBIDDEN_TABLES:
        raise ValidationError("schema contract marks a runtime table as forbidden")
    contract_columns = {
        (table_name, column_name)
        for table_name, columns in TABLE_COLUMNS.items()
        for column_name in columns
    }
    if contract_columns & FORBIDDEN_COLUMNS:
        raise ValidationError("schema contract retains a forbidden legacy column")

    created_tables = {
        match.group(1).lower()
        for match in re.finditer(
            r"CREATE\s+TABLE\s+IF\s+NOT\s+EXISTS\s+([a-z_]+)",
            schema_sql,
            re.IGNORECASE,
        )
    }
    if created_tables != APP_TABLES:
        raise ValidationError(
            "canonical table set differs from the contract; "
            f"missing={sorted(APP_TABLES - created_tables)}, "
            f"extra={sorted(created_tables - APP_TABLES)}"
        )

    column_pattern = re.compile(
        r"^\s*([a-z_][a-z0-9_]*)\s+"
        r"(?:SERIAL|TEXT|INTEGER|REAL|BOOLEAN|JSONB|VARCHAR|TIMESTAMPTZ)\b",
        re.IGNORECASE | re.MULTILINE,
    )
    for table_name, expected_columns in TABLE_COLUMNS.items():
        definition = _table_definition(schema_sql, table_name)
        actual_columns = {
            match.group(1).lower() for match in column_pattern.finditer(definition)
        }
        if actual_columns != expected_columns:
            raise ValidationError(
                f"{table_name} columns differ from the contract; "
                f"missing={sorted(expected_columns - actual_columns)}, "
                f"extra={sorted(actual_columns - expected_columns)}"
            )

    if re.search(r"^\s*\w+\s+TIMESTAMP\b", schema_sql, re.IGNORECASE | re.MULTILINE):
        raise ValidationError("canonical timestamps must use TIMESTAMPTZ")

    for index_name in REQUIRED_INDEXES:
        if not re.search(
            rf"CREATE\s+(?:UNIQUE\s+)?INDEX\s+IF\s+NOT\s+EXISTS\s+{re.escape(index_name)}\b",
            schema_sql,
            re.IGNORECASE,
        ):
            raise ValidationError(f"canonical schema is missing {index_name}")

    for index_name in REQUIRED_UNIQUE_INDEXES:
        if not re.search(
            rf"CREATE\s+UNIQUE\s+INDEX\s+IF\s+NOT\s+EXISTS\s+{re.escape(index_name)}\b",
            schema_sql,
            re.IGNORECASE,
        ):
            raise ValidationError(f"canonical unique index is missing: {index_name}")

    for index_name in FORBIDDEN_INDEXES:
        if re.search(rf"\b{re.escape(index_name)}\b", schema_sql, re.IGNORECASE):
            raise ValidationError(f"canonical schema retains redundant index {index_name}")

    for constraint_name in REQUIRED_CHECK_CONSTRAINTS:
        if not re.search(
            rf"CONSTRAINT\s+{re.escape(constraint_name)}\s+CHECK\b",
            schema_sql,
            re.IGNORECASE,
        ):
            raise ValidationError(
                f"canonical schema is missing check constraint {constraint_name}"
            )

    for required_phrase in (
        "ADD COLUMN IF NOT EXISTS created_by",
        "ADD COLUMN IF NOT EXISTS best_match_job_id",
        "RENAME COLUMN location TO work_mode",
        "DROP COLUMN location",
        "ADD COLUMN IF NOT EXISTS job_id",
        "ADD COLUMN IF NOT EXISTS proctor_id",
        "SET scheduled_assessment_id",
        "DROP COLUMN IF EXISTS assessment_id",
        "DROP COLUMN IF EXISTS permissions",
        "DROP COLUMN IF EXISTS parsed_skills_json",
        "DROP TABLE IF EXISTS proctoring_events",
        "DROP TABLE IF EXISTS questions",
        "DROP TABLE IF EXISTS sector_email_configs",
        "legacy_source",
        "DROP TABLE IF EXISTS admin_audit_log",
        "ENABLE ROW LEVEL SECURITY",
        "REVOKE ALL PRIVILEGES ON ALL TABLES",
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
    cursor.execute(
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = %s AND table_type = 'BASE TABLE'
        """,
        (schema_name,),
    )
    actual_tables = {row[0] for row in cursor.fetchall()}
    if actual_tables != APP_TABLES:
        raise ValidationError(
            "database table set differs from the contract; "
            f"missing={sorted(APP_TABLES - actual_tables)}, "
            f"extra={sorted(actual_tables - APP_TABLES)}"
        )

    cursor.execute(
        """
        SELECT table_name, column_name
        FROM information_schema.columns
        WHERE table_schema = %s AND table_name = ANY(%s)
        """,
        (schema_name, sorted(APP_TABLES)),
    )
    actual_columns = {table_name: set() for table_name in APP_TABLES}
    for table_name, column_name in cursor.fetchall():
        actual_columns[table_name].add(column_name)

    for table_name, expected_columns in TABLE_COLUMNS.items():
        if actual_columns[table_name] != expected_columns:
            raise ValidationError(
                f"database table {table_name} differs from the contract; "
                f"missing={sorted(expected_columns - actual_columns[table_name])}, "
                f"extra={sorted(actual_columns[table_name] - expected_columns)}"
            )

    cursor.execute(
        """
        SELECT indexname
        FROM pg_indexes
        WHERE schemaname = %s
        """,
        (schema_name,),
    )
    existing_indexes = {row[0] for row in cursor.fetchall()}
    missing_indexes = REQUIRED_INDEXES - existing_indexes
    if missing_indexes:
        raise ValidationError(
            f"database is missing indexes: {sorted(missing_indexes)}"
        )
    redundant_indexes = FORBIDDEN_INDEXES & existing_indexes
    if redundant_indexes:
        raise ValidationError(
            f"database retains redundant indexes: {sorted(redundant_indexes)}"
        )

    cursor.execute(
        """
        SELECT index_record.relname
        FROM pg_index AS index_metadata
        JOIN pg_class AS index_record ON index_record.oid = index_metadata.indexrelid
        JOIN pg_namespace AS namespace_record
          ON namespace_record.oid = index_record.relnamespace
        WHERE namespace_record.nspname = %s
          AND index_metadata.indisunique
        """,
        (schema_name,),
    )
    actual_unique_indexes = {row[0] for row in cursor.fetchall()}
    missing_unique = REQUIRED_UNIQUE_INDEXES - actual_unique_indexes
    if missing_unique:
        raise ValidationError(
            f"database is missing unique indexes: {sorted(missing_unique)}"
        )

    cursor.execute(
        """
        SELECT constraint_record.conname, constraint_record.convalidated
        FROM pg_constraint AS constraint_record
        JOIN pg_class AS table_record
          ON table_record.oid = constraint_record.conrelid
        JOIN pg_namespace AS namespace_record
          ON namespace_record.oid = table_record.relnamespace
        WHERE namespace_record.nspname = %s
          AND constraint_record.contype = 'c'
        """,
        (schema_name,),
    )
    checks = dict(cursor.fetchall())
    missing_checks = REQUIRED_CHECK_CONSTRAINTS - checks.keys()
    if missing_checks:
        raise ValidationError(
            f"database is missing check constraints: {sorted(missing_checks)}"
        )
    unvalidated_checks = {
        name for name in REQUIRED_CHECK_CONSTRAINTS if not checks[name]
    }
    if unvalidated_checks:
        raise ValidationError(
            f"database has unvalidated checks: {sorted(unvalidated_checks)}"
        )

    cursor.execute(
        """
        SELECT table_name, column_name
        FROM information_schema.columns
        WHERE table_schema = %s AND is_nullable = 'NO'
        """,
        (schema_name,),
    )
    not_null_columns = set(cursor.fetchall())
    missing_not_null = REQUIRED_NOT_NULL_COLUMNS - not_null_columns
    if missing_not_null:
        raise ValidationError(
            "database columns unexpectedly allow NULL: "
            + ", ".join(".".join(column) for column in sorted(missing_not_null))
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

    cursor.execute(
        """
        SELECT table_name, column_name
        FROM information_schema.columns
        WHERE table_schema = %s
          AND data_type = 'timestamp with time zone'
        """,
        (schema_name,),
    )
    timezone_columns = set(cursor.fetchall())
    missing_timezone_columns = TIMESTAMP_COLUMNS - timezone_columns
    if missing_timezone_columns:
        raise ValidationError(
            "database timestamps are not timezone-aware: "
            + ", ".join(".".join(column) for column in sorted(missing_timezone_columns))
        )

    cursor.execute(
        """
        SELECT table_record.relname
        FROM pg_class AS table_record
        JOIN pg_namespace AS namespace_record
          ON namespace_record.oid = table_record.relnamespace
        WHERE namespace_record.nspname = %s
          AND table_record.relname = ANY(%s)
          AND table_record.relkind IN ('r', 'p')
          AND NOT table_record.relrowsecurity
        """,
        (schema_name, sorted(APP_TABLES)),
    )
    tables_without_rls = {row[0] for row in cursor.fetchall()}
    if tables_without_rls:
        raise ValidationError(
            "database tables are missing RLS: " + ", ".join(sorted(tables_without_rls))
        )

    cursor.execute(
        """
        SELECT grantee, table_name, privilege_type
        FROM information_schema.role_table_grants
        WHERE table_schema = %s
          AND grantee IN ('anon', 'authenticated')
        """,
        (schema_name,),
    )
    exposed_grants = cursor.fetchall()
    if exposed_grants:
        raise ValidationError(
            "Supabase Data API roles retain table grants: "
            + ", ".join(".".join(row) for row in exposed_grants[:5])
        )

    cursor.execute(
        """
        SELECT role_record.rolname
        FROM pg_roles AS role_record
        WHERE role_record.rolname IN ('anon', 'authenticated')
          AND has_schema_privilege(
              role_record.rolname, %s, 'USAGE'
          )
        """,
        (schema_name,),
    )
    exposed_schema_roles = {row[0] for row in cursor.fetchall()}
    if exposed_schema_roles:
        raise ValidationError(
            "Supabase Data API roles retain schema access: "
            + ", ".join(sorted(exposed_schema_roles))
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

        # Add known aliases and the action_type flavor of the old audit log.
        cursor.execute(
            """
            ALTER TABLE job_descriptions
                RENAME COLUMN work_mode TO location;
            ALTER TABLE job_descriptions
                DROP CONSTRAINT job_descriptions_work_mode_check;
            ALTER TABLE job_descriptions ADD COLUMN created_by_id INTEGER;
            ALTER TABLE candidates ADD COLUMN job_id INTEGER;
            ALTER TABLE scheduled_assessments
                ADD COLUMN assessment_id INTEGER,
                ADD COLUMN access_token TEXT;
            ALTER TABLE scheduled_assessments
                ALTER COLUMN access_token_hash DROP NOT NULL;
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
            INSERT INTO job_descriptions (title, location, created_by_id)
            VALUES ('Legacy job', 'wfh', 1);
            INSERT INTO candidates (
                name, email, phone, resume_path, job_id
            ) VALUES (
                'Legacy candidate', 'candidate@example.invalid', '0', '/dev/null', 1
            );
            INSERT INTO scheduled_assessments (
                candidate_id, interviewer_id, job_id, scheduled_time,
                status, access_token
            ) VALUES (
                1, 1, 1, CURRENT_TIMESTAMP, 'scheduled', 'legacy-link-token'
            );
            INSERT INTO assessments (candidate_id, job_id)
            VALUES (1, 1);
            UPDATE scheduled_assessments
            SET assessment_id = (
                SELECT id FROM assessments ORDER BY id LIMIT 1
            )
            WHERE access_token = 'legacy-link-token';
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
                "SELECT work_mode FROM job_descriptions WHERE title = 'Legacy job'",
            )
            != "Remote"
        ):
            raise ValidationError("location was not preserved and normalized as work_mode")
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
                FROM assessments AS assessment
                JOIN scheduled_assessments AS schedule
                  ON schedule.id = assessment.scheduled_assessment_id
                WHERE schedule.access_token_hash = encode(
                    sha256(convert_to('legacy-link-token', 'UTF8')), 'hex'
                )
                """,
            )
            != 1
        ):
            raise ValidationError(
                "scheduled_assessments.assessment_id was not backfilled"
            )
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
