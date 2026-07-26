"""Unit tests for the canonical database migration entry point."""

import pytest

from scripts import run_migration


def test_migration_artifacts_are_canonical_and_present():
    schema = run_migration.SQL_ARTIFACTS["schema"]
    reconcile = run_migration.SQL_ARTIFACTS["reconcile"]

    assert schema.name == "schema_postgres.sql"
    assert schema.is_file()
    assert reconcile.name == "20260713_reconcile_canonical_schema.sql"
    assert reconcile.is_file()


def test_strip_outer_transaction_preserves_migration_body():
    sql = "-- reconciliation\nBEGIN;\nSELECT 1;\nCOMMIT;\n"

    stripped = run_migration._strip_outer_transaction(sql)

    assert stripped.startswith("-- reconciliation")
    assert "SELECT 1;" in stripped
    assert "BEGIN;" not in stripped
    assert "COMMIT;" not in stripped


def test_missing_database_url_fails_before_connecting(monkeypatch):
    monkeypatch.setattr(run_migration, "_load_environment", lambda: None)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("DATABASE_ADMIN_URL", raising=False)

    assert run_migration.main(["--schema"]) == 2


def test_legacy_postgres_url_is_normalized(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgres://user:pass@host/database")

    assert run_migration._database_url().startswith("postgresql://")


def test_migration_verifier_rejects_removed_reverse_assessment_link():
    assert (
        "scheduled_assessments",
        "assessment_id",
    ) in run_migration.FORBIDDEN_COLUMNS


def test_production_migration_requires_separate_administrator_url(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("DATABASE_ADMIN_URL", raising=False)
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://hiresense_app@database.example/hiresense"
        "?sslmode=verify-full",
    )

    with pytest.raises(RuntimeError, match="DATABASE_ADMIN_URL"):
        run_migration._database_url()


def test_production_migration_rejects_insecure_administrator_transport(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv(
        "DATABASE_ADMIN_URL",
        "postgresql://postgres@database.example/hiresense?sslmode=prefer",
    )

    with pytest.raises(RuntimeError, match="sslmode"):
        run_migration._database_url()


@pytest.mark.parametrize("sslmode", ["require", "verify-ca"])
def test_production_migration_requires_full_administrator_certificate_verification(
    monkeypatch, sslmode
):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv(
        "DATABASE_ADMIN_URL",
        "postgresql://postgres@database.example/hiresense"
        f"?sslmode={sslmode}",
    )

    with pytest.raises(RuntimeError, match="verify-full"):
        run_migration._database_url()


def test_production_runtime_credentials_require_hiresense_role(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://postgres:unit-test-value@database.example/hiresense"
        "?sslmode=verify-full",
    )

    with pytest.raises(RuntimeError, match="hiresense_app"):
        run_migration._runtime_database_password()


class RoleProvisionCursor:
    def __init__(self, role_attributes):
        self.role_attributes = role_attributes
        self.calls = []

    def execute(self, query, params=None):
        self.calls.append((str(query), params))

    def fetchone(self):
        return self.role_attributes

    def fetchall(self):
        return []


def test_runtime_role_is_provisioned_without_administrative_attributes():
    cursor = RoleProvisionCursor(role_attributes=None)

    run_migration._provision_runtime_role(cursor, "unit-test-value")

    create_sql, params = cursor.calls[1]
    assert "CREATE ROLE hiresense_app" in create_sql
    assert "VALID UNTIL 'infinity'" in create_sql
    assert "CONNECTION LIMIT -1" in create_sql
    assert params == ("unit-test-value",)
    assert "NOSUPERUSER" not in create_sql
    assert "NOREPLICATION" not in create_sql
    assert "NOBYPASSRLS" not in create_sql
    assert any("RESET ALL" in query for query, _params in cursor.calls)


def test_existing_runtime_role_does_not_reapply_superuser_only_attributes():
    cursor = RoleProvisionCursor(role_attributes=(False, False, False))

    run_migration._provision_runtime_role(cursor, "unit-test-value")

    alter_sql, params = cursor.calls[1]
    assert "ALTER ROLE hiresense_app" in alter_sql
    assert "NOSUPERUSER" not in alter_sql
    assert "NOREPLICATION" not in alter_sql
    assert "NOBYPASSRLS" not in alter_sql
    assert params == ("unit-test-value",)


def test_privileged_runtime_role_is_rejected_before_alter():
    cursor = RoleProvisionCursor(role_attributes=(True, False, False))

    with pytest.raises(RuntimeError, match="privileged attributes"):
        run_migration._provision_runtime_role(cursor, "unit-test-value")

    assert len(cursor.calls) == 1
