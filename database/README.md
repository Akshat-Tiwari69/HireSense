# Database contract

HireSense has one PostgreSQL contract: [`schema_contract.py`](schema_contract.py)
defines the exact 14 tables, columns, constraints, indexes, foreign keys, and
timezone-aware timestamps that must exist. [`schema_postgres.sql`](schema_postgres.sql)
is the matching fresh-install schema.

## Supported tables

```text
sectors                    users
candidates                 job_descriptions
scheduled_assessments      assessments
mcq_responses              coding_submissions
psychometric_responses     proctoring_violations
email_logs                 candidate_job_matches
audit_log                  custom_question_bank
```

`job_descriptions` is the historical database name for job postings. The
application uses these canonical names:

| Canonical object | Removed legacy alias |
| --- | --- |
| `job_descriptions.created_by` | `created_by_id` |
| `candidates.best_match_job_id` | `candidates.job_id` |
| `assessments.scheduled_assessment_id` | `scheduled_assessments.assessment_id` |
| `assessments.automated_recommendation` and `final_decision` | overloaded `assessments.decision` |
| `assessments.automated_rationale` and `final_rationale` | overloaded `assessments.rationale` |
| `assessments.recommended_next_step` | `assessments.hiring_recommendation` |
| `proctoring_violations.screenshot_path` | `screenshot_url` |
| `scheduled_assessments.access_token_hash` | raw `access_token` storage |
| `audit_log` | `admin_audit_log` |

The schedule/session relationship is one-way. An assessment optionally points
to its schedule through `assessments.scheduled_assessment_id`; a unique index
allows at most one assessment for a schedule. There is no reverse assessment
column on `scheduled_assessments`.

## Apply the schema

Run from the repository root. The migration runner prefers
`DATABASE_ADMIN_URL` and falls back to `DATABASE_URL`.

```powershell
# Empty database only
python backend/scripts/run_migration.py --schema

# Existing HireSense database only
python backend/scripts/run_migration.py --reconcile
```

Reconciliation uses
[`20260713_reconcile_canonical_schema.sql`](migrations/20260713_reconcile_canonical_schema.sql).
It copies known legacy values, removes obsolete tables/columns/indexes, adds the
canonical constraints, and is safe to retry. Do not replay the older migration
files as an ordered fresh-install history.

The runner takes a PostgreSQL advisory lock, applies and verifies the change in
one transaction, and rolls back on any mismatch. Historical duplicate active
schedules, assessment links, responses, or candidate/job matches must be
resolved explicitly before their unique indexes can be installed.

## Validate

The static check needs no database:

```powershell
python database/validate_schema.py
```

The integration check must use a disposable PostgreSQL database. It creates and
drops an isolated temporary schema, applies the fresh schema and reconciliation
twice, and exercises legacy backfills without touching objects outside that
temporary schema.

```powershell
python database/validate_schema.py --database-url postgresql://user:password@host/database
```

`SCHEMA_TEST_DATABASE_URL` may replace the command-line URL.

## Runtime security

The Flask backend connects directly to PostgreSQL. In production,
`DATABASE_URL` should use the non-administrative `hiresense_app` role;
`DATABASE_ADMIN_URL` is reserved for schema work. Both URLs must set
`sslmode=verify-full` so libpq verifies the certificate chain and hostname.

All 14 tables have RLS enabled. Supabase Data API roles `anon` and
`authenticated` have no public-schema or table privileges. When
`hiresense_app` exists, each table receives the `hiresense_backend_access`
policy plus only the table/sequence privileges needed by the backend. This is
defence in depth: request-level authorization remains in Flask.

User and candidate email uniqueness is case-insensitive through unique indexes
on `LOWER(email)`. All application timestamps are `TIMESTAMPTZ`.

## Removed legacy objects

The canonical contract rejects these tables:

```text
admin_audit_log    proctoring_events    questions    sector_email_configs
```

It also rejects duplicate/stale columns including `users.permissions`,
`candidates.parsed_skills_json`, `coding_submissions.execution_time`,
`coding_submissions.error_message`, `custom_question_bank.filename`, the old
job/candidate aliases above, the overloaded assessment decision fields, the
misnamed screenshot URL field, and the former streaming/reverse-link columns
on `scheduled_assessments`. Candidate invitation capabilities are stored only
as SHA-256 lookup hashes; the raw token exists only in the invitation link.
