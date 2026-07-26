"""Apply the canonical HireSense schema or reconcile an existing database."""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

import psycopg2
from psycopg2 import sql
from psycopg2.extensions import parse_dsn
from dotenv import load_dotenv


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY_ROOT))

from database.schema_contract import (  # noqa: E402
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
from backend.db_config import (  # noqa: E402
    production_guards_required,
    validate_database_url,
)


BACKEND_ROOT = REPOSITORY_ROOT / "backend"
SQL_ARTIFACTS = {
    "schema": REPOSITORY_ROOT / "database" / "schema_postgres.sql",
    "reconcile": (
        REPOSITORY_ROOT
        / "database"
        / "migrations"
        / "20260713_reconcile_canonical_schema.sql"
    ),
}
CORE_TABLES = {
    "assessments",
    "candidates",
    "job_descriptions",
    "scheduled_assessments",
    "users",
}
RLS_TABLES = APP_TABLES
REQUIRED_COLUMNS = {
    (table_name, column_name)
    for table_name, columns in TABLE_COLUMNS.items()
    for column_name in columns
}


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Initialize a fresh HireSense PostgreSQL database or reconcile a "
            "legacy installation with the canonical schema."
        )
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--schema",
        dest="mode",
        action="store_const",
        const="schema",
        help="initialize a fresh, empty database with database/schema_postgres.sql",
    )
    mode.add_argument(
        "--reconcile",
        dest="mode",
        action="store_const",
        const="reconcile",
        help=(
            "upgrade an existing installation with the dated canonical "
            "reconciliation migration"
        ),
    )
    return parser


def _load_environment() -> None:
    """Load local development configuration without overriding process values."""
    local_env = BACKEND_ROOT / "local.env"
    env_file = local_env if local_env.exists() else BACKEND_ROOT / ".env"
    if env_file.exists():
        load_dotenv(env_file, override=False)


def _database_url() -> str:
    administrator_url = os.getenv("DATABASE_ADMIN_URL", "").strip()
    if production_guards_required() and not administrator_url:
        raise RuntimeError(
            "DATABASE_ADMIN_URL is required for production migrations"
        )
    database_url = administrator_url or os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        return ""
    return validate_database_url(
        database_url,
        require_tls=production_guards_required(),
    )


def _runtime_database_password() -> str | None:
    database_url = os.getenv("DATABASE_URL", "").strip()
    production = production_guards_required()
    if not database_url:
        if production:
            raise RuntimeError(
                "DATABASE_URL is required to provision the production runtime role"
            )
        return None

    validated = validate_database_url(
        database_url,
        require_tls=production,
        require_runtime_role=production,
    )
    options = parse_dsn(validated)
    if options.get("user", "").split(".", 1)[0] != "hiresense_app":
        return None
    password = options.get("password")
    if production and not password:
        raise RuntimeError(
            "Production DATABASE_URL must include the hiresense_app password"
        )
    return password


def _provision_runtime_role(cursor, password: str) -> None:
    cursor.execute(
        """
        SELECT rolsuper, rolreplication, rolbypassrls
          FROM pg_roles
         WHERE rolname = 'hiresense_app'
        """
    )
    privileged_attributes = cursor.fetchone()
    if privileged_attributes and any(privileged_attributes):
        raise RuntimeError(
            "hiresense_app has privileged attributes that this administrator "
            "cannot safely remove"
        )

    command = "ALTER" if privileged_attributes is not None else "CREATE"
    cursor.execute(
        f"""
        {command} ROLE hiresense_app WITH
            LOGIN NOCREATEDB NOCREATEROLE NOINHERIT CONNECTION LIMIT -1
            VALID UNTIL 'infinity' PASSWORD %s
        """,
        (password,),
    )
    cursor.execute("ALTER ROLE hiresense_app RESET ALL")
    cursor.execute(
        """
        SELECT parent_role.rolname
          FROM pg_auth_members AS membership
          JOIN pg_roles AS child_role ON child_role.oid = membership.member
          JOIN pg_roles AS parent_role ON parent_role.oid = membership.roleid
         WHERE child_role.rolname = 'hiresense_app'
        """
    )
    for (parent_role,) in cursor.fetchall():
        cursor.execute(
            sql.SQL("REVOKE {} FROM hiresense_app").format(
                sql.Identifier(parent_role)
            )
        )
    cursor.execute("ALTER ROLE hiresense_app SET row_security = on")


def _strip_outer_transaction(sql: str) -> str:
    """Remove the reconciliation file's outer transaction wrapper.

    The runner owns the transaction so it can perform preflight checks, apply the
    SQL, verify the result, and roll everything back together on failure.
    """
    without_begin, begin_count = re.subn(
        r"(?im)^\s*BEGIN;\s*", "", sql, count=1
    )
    without_commit, commit_count = re.subn(
        r"(?im)\s*COMMIT;\s*$", "", without_begin, count=1
    )
    if begin_count != 1 or commit_count != 1:
        raise ValueError("reconciliation SQL must have one outer BEGIN/COMMIT pair")
    return without_commit


def _existing_core_tables(cursor) -> set[str]:
    cursor.execute(
        """
        SELECT table_name
          FROM information_schema.tables
         WHERE table_schema = 'public'
           AND table_name = ANY(%s)
        """,
        (sorted(CORE_TABLES),),
    )
    return {row[0] for row in cursor.fetchall()}


def _preflight(cursor, mode: str) -> None:
    existing = _existing_core_tables(cursor)
    if mode == "schema" and existing:
        names = ", ".join(sorted(existing))
        raise RuntimeError(
            "fresh-schema mode refused because HireSense tables already exist "
            f"({names}); use --reconcile for an existing database"
        )
    if mode == "reconcile":
        missing = CORE_TABLES - existing
        if missing:
            names = ", ".join(sorted(missing))
            raise RuntimeError(
                "reconciliation requires an existing HireSense installation; "
                f"missing core tables: {names}"
            )


def _verify(cursor, *, require_runtime_role: bool = False) -> None:
    cursor.execute(
        """
        SELECT table_name
          FROM information_schema.tables
         WHERE table_schema = 'public'
           AND table_name = ANY(%s)
        """,
        (sorted(APP_TABLES | FORBIDDEN_TABLES),),
    )
    found_tables = {row[0] for row in cursor.fetchall()}
    missing_tables = APP_TABLES - found_tables
    forbidden_tables = FORBIDDEN_TABLES & found_tables
    if missing_tables or forbidden_tables:
        raise RuntimeError(
            "verification failed; table contract mismatch: "
            f"missing={sorted(missing_tables)}, "
            f"forbidden={sorted(forbidden_tables)}"
        )

    cursor.execute(
        """
        SELECT table_name, column_name
          FROM information_schema.columns
         WHERE table_schema = 'public'
           AND table_name = ANY(%s)
        """,
        (sorted(APP_TABLES),),
    )
    found_columns = set(cursor.fetchall())
    missing_columns = REQUIRED_COLUMNS - found_columns
    unexpected_columns = found_columns - REQUIRED_COLUMNS
    if missing_columns or unexpected_columns:
        raise RuntimeError(
            "verification failed; column contract mismatch: "
            f"missing={sorted(missing_columns)}, "
            f"unexpected={sorted(unexpected_columns)}"
        )

    forbidden_columns = FORBIDDEN_COLUMNS & found_columns
    if forbidden_columns:
        raise RuntimeError(
            "verification failed; forbidden legacy columns remain: "
            + ", ".join(".".join(column) for column in sorted(forbidden_columns))
        )

    cursor.execute(
        """
        SELECT table_name, column_name
          FROM information_schema.columns
         WHERE table_schema = 'public'
           AND table_name = ANY(%s)
           AND data_type = 'timestamp without time zone'
        """,
        (sorted(RLS_TABLES),),
    )
    naive_timestamps = cursor.fetchall()
    if naive_timestamps:
        raise RuntimeError(
            "verification failed; timezone-naive columns remain: "
            + ", ".join(".".join(column) for column in naive_timestamps)
        )

    cursor.execute(
        """
        SELECT table_name, column_name
          FROM information_schema.columns
         WHERE table_schema = 'public'
           AND data_type = 'timestamp with time zone'
        """
    )
    timezone_columns = set(cursor.fetchall())
    missing_timezone_columns = TIMESTAMP_COLUMNS - timezone_columns
    if missing_timezone_columns:
        raise RuntimeError(
            "verification failed; timezone-aware columns are missing: "
            + ", ".join(
                ".".join(column) for column in sorted(missing_timezone_columns)
            )
        )

    cursor.execute("SELECT indexname FROM pg_indexes WHERE schemaname = 'public'")
    indexes = {row[0] for row in cursor.fetchall()}
    missing_indexes = REQUIRED_INDEXES - indexes
    redundant_indexes = FORBIDDEN_INDEXES & indexes
    if missing_indexes or redundant_indexes:
        raise RuntimeError(
            "verification failed; index contract mismatch: "
            f"missing={sorted(missing_indexes)}, "
            f"redundant={sorted(redundant_indexes)}"
        )

    cursor.execute(
        """
        SELECT index_record.relname
          FROM pg_index AS index_metadata
          JOIN pg_class AS index_record
            ON index_record.oid = index_metadata.indexrelid
          JOIN pg_namespace AS namespace_record
            ON namespace_record.oid = index_record.relnamespace
         WHERE namespace_record.nspname = 'public'
           AND index_metadata.indisunique
        """
    )
    unique_indexes = {row[0] for row in cursor.fetchall()}
    missing_unique = REQUIRED_UNIQUE_INDEXES - unique_indexes
    if missing_unique:
        raise RuntimeError(
            "verification failed; unique indexes are missing: "
            + ", ".join(sorted(missing_unique))
        )

    cursor.execute(
        """
        SELECT constraint_record.conname, constraint_record.convalidated
          FROM pg_constraint AS constraint_record
          JOIN pg_class AS table_record
            ON table_record.oid = constraint_record.conrelid
          JOIN pg_namespace AS namespace_record
            ON namespace_record.oid = table_record.relnamespace
         WHERE namespace_record.nspname = 'public'
           AND constraint_record.contype = 'c'
        """
    )
    checks = dict(cursor.fetchall())
    missing_checks = REQUIRED_CHECK_CONSTRAINTS - checks.keys()
    invalid_checks = {
        name
        for name in REQUIRED_CHECK_CONSTRAINTS & checks.keys()
        if not checks[name]
    }
    if missing_checks or invalid_checks:
        raise RuntimeError(
            "verification failed; check constraint mismatch: "
            f"missing={sorted(missing_checks)}, "
            f"unvalidated={sorted(invalid_checks)}"
        )

    cursor.execute(
        """
        SELECT table_name, column_name
          FROM information_schema.columns
         WHERE table_schema = 'public'
           AND is_nullable = 'NO'
        """
    )
    not_null_columns = set(cursor.fetchall())
    missing_not_null = REQUIRED_NOT_NULL_COLUMNS - not_null_columns
    if missing_not_null:
        raise RuntimeError(
            "verification failed; required columns allow NULL: "
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
         WHERE source_namespace.nspname = 'public'
           AND constraint_record.contype = 'f'
        """
    )
    foreign_keys = set(cursor.fetchall())
    missing_foreign_keys = REQUIRED_FOREIGN_KEYS - foreign_keys
    if missing_foreign_keys:
        raise RuntimeError(
            "verification failed; foreign keys are missing: "
            + ", ".join(str(value) for value in sorted(missing_foreign_keys))
        )

    cursor.execute(
        """
        SELECT table_record.relname
          FROM pg_class AS table_record
          JOIN pg_namespace AS namespace_record
            ON namespace_record.oid = table_record.relnamespace
         WHERE namespace_record.nspname = 'public'
           AND table_record.relname = ANY(%s)
           AND NOT table_record.relrowsecurity
        """,
        (sorted(RLS_TABLES),),
    )
    without_rls = {row[0] for row in cursor.fetchall()}
    if without_rls:
        raise RuntimeError(
            "verification failed; RLS is disabled on: "
            + ", ".join(sorted(without_rls))
        )

    cursor.execute(
        """
        SELECT grantee, table_name, privilege_type
          FROM information_schema.role_table_grants
         WHERE table_schema = 'public'
           AND grantee IN ('anon', 'authenticated')
        """
    )
    if cursor.fetchone():
        raise RuntimeError(
            "verification failed; Supabase Data API roles retain table privileges"
        )

    cursor.execute(
        """
        SELECT role_record.rolname
          FROM pg_roles AS role_record
         WHERE role_record.rolname IN ('anon', 'authenticated')
           AND has_schema_privilege(
               role_record.rolname, 'public', 'USAGE'
           )
        """
    )
    if cursor.fetchone():
        raise RuntimeError(
            "verification failed; Supabase Data API roles retain public-schema access"
        )

    cursor.execute(
        """
        SELECT
            rolcanlogin,
            rolinherit,
            rolsuper,
            rolcreaterole,
            rolcreatedb,
            rolreplication,
            rolbypassrls
          FROM pg_roles
         WHERE rolname = 'hiresense_app'
        """
    )
    runtime_role = cursor.fetchone()
    if require_runtime_role and runtime_role is None:
        raise RuntimeError(
            "verification failed; hiresense_app runtime role is missing"
        )
    if runtime_role and (
        not runtime_role[0]
        or runtime_role[1]
        or any(runtime_role[2:])
    ):
        raise RuntimeError(
            "verification failed; hiresense_app has administrative role attributes"
        )

    if runtime_role:
        cursor.execute(
            """
            SELECT parent_role.rolname
              FROM pg_auth_members AS membership
              JOIN pg_roles AS child_role ON child_role.oid = membership.member
              JOIN pg_roles AS parent_role ON parent_role.oid = membership.roleid
             WHERE child_role.rolname = 'hiresense_app'
            """
        )
        memberships = [row[0] for row in cursor.fetchall()]
        if memberships:
            raise RuntimeError(
                "verification failed; hiresense_app inherits other roles: "
                + ", ".join(sorted(memberships))
            )

        cursor.execute(
            """
            SELECT table_record.relname
              FROM pg_class AS table_record
              JOIN pg_namespace AS namespace_record
                ON namespace_record.oid = table_record.relnamespace
              JOIN pg_roles AS role_record
                ON role_record.oid = table_record.relowner
             WHERE namespace_record.nspname = 'public'
               AND table_record.relname = ANY(%s)
               AND role_record.rolname = 'hiresense_app'
            """,
            (sorted(RLS_TABLES),),
        )
        owned_tables = [row[0] for row in cursor.fetchall()]
        if owned_tables:
            raise RuntimeError(
                "verification failed; hiresense_app owns RLS tables: "
                + ", ".join(sorted(owned_tables))
            )

        cursor.execute(
            """
            SELECT COUNT(*)
              FROM pg_policies
             WHERE schemaname = 'public'
               AND policyname = 'hiresense_backend_access'
               AND tablename = ANY(%s)
            """,
            (sorted(RLS_TABLES),),
        )
        policy_count = cursor.fetchone()[0]
        if policy_count != len(RLS_TABLES):
            raise RuntimeError(
                "verification failed; hiresense_app RLS policies are incomplete"
            )


def _safe_database_error(exc: psycopg2.Error) -> str:
    primary = getattr(getattr(exc, "diag", None), "message_primary", None)
    return primary or exc.__class__.__name__


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    _load_environment()
    try:
        database_url = _database_url()
        runtime_password = _runtime_database_password()
    except RuntimeError as exc:
        print(f"Migration configuration is invalid: {exc}")
        return 2
    if not database_url:
        print("DATABASE_URL is not set; configure backend/.env or the process environment.")
        return 2

    sql_path = SQL_ARTIFACTS[args.mode]
    if not sql_path.is_file():
        print(f"Canonical SQL artifact is missing: {sql_path}")
        return 2

    try:
        sql = sql_path.read_text(encoding="utf-8")
        if args.mode == "reconcile":
            sql = _strip_outer_transaction(sql)
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"Unable to load canonical SQL: {exc}")
        return 2

    connection = None
    try:
        print(f"Applying {sql_path.relative_to(REPOSITORY_ROOT)} ...")
        connection = psycopg2.connect(
            database_url,
            application_name="hiresense-migration",
            connect_timeout=10,
        )
        connection.autocommit = False
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT pg_advisory_xact_lock(hashtext(%s))",
                ("hiresense-schema-migration",),
            )
            if runtime_password:
                _provision_runtime_role(cursor, runtime_password)
            _preflight(cursor, args.mode)
            cursor.execute(sql)
            _verify(
                cursor,
                require_runtime_role=production_guards_required(),
            )
        connection.commit()
    except psycopg2.Error as exc:
        if connection is not None:
            connection.rollback()
        print(f"Migration failed: {_safe_database_error(exc)}")
        return 1
    except (OSError, RuntimeError, ValueError) as exc:
        if connection is not None:
            connection.rollback()
        print(f"Migration failed: {exc}")
        return 1
    finally:
        if connection is not None:
            connection.close()

    print("Migration completed and canonical schema checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
