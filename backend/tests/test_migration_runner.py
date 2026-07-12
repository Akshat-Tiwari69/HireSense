"""Unit tests for the canonical database migration entry point."""

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

    assert run_migration.main(["--schema"]) == 2


def test_legacy_postgres_url_is_normalized(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgres://user:pass@host/database")

    assert run_migration._database_url().startswith("postgresql://")
