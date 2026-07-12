"""Apply the canonical HireSense schema or reconcile an existing database."""

from __future__ import annotations

import argparse
import os
import re
from pathlib import Path

import psycopg2
from dotenv import load_dotenv


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
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
REQUIRED_COLUMNS = {
    ("candidates", "best_match_job_id"),
    ("job_descriptions", "created_by"),
    ("job_descriptions", "role_complexity_level"),
    ("proctoring_events", "is_reviewed"),
    ("scheduled_assessments", "job_id"),
    ("scheduled_assessments", "proctor_id"),
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
    database_url = os.getenv("DATABASE_URL", "").strip()
    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql://", 1)
    return database_url


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


def _verify(cursor) -> None:
    cursor.execute("SELECT to_regclass('public.audit_log')")
    if cursor.fetchone()[0] is None:
        raise RuntimeError("verification failed: public.audit_log is missing")

    missing_columns: list[str] = []
    for table_name, column_name in sorted(REQUIRED_COLUMNS):
        cursor.execute(
            """
            SELECT EXISTS (
                SELECT 1
                  FROM information_schema.columns
                 WHERE table_schema = 'public'
                   AND table_name = %s
                   AND column_name = %s
            )
            """,
            (table_name, column_name),
        )
        if not cursor.fetchone()[0]:
            missing_columns.append(f"{table_name}.{column_name}")

    if missing_columns:
        raise RuntimeError(
            "verification failed; missing canonical columns: "
            + ", ".join(missing_columns)
        )


def _safe_database_error(exc: psycopg2.Error) -> str:
    primary = getattr(getattr(exc, "diag", None), "message_primary", None)
    return primary or exc.__class__.__name__


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    _load_environment()
    database_url = _database_url()
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
            _preflight(cursor, args.mode)
            cursor.execute(sql)
            _verify(cursor)
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
