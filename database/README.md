# Database contract

`schema_postgres.sql` is the only schema to use for a new HireSense database.
It is idempotent: applying the complete file more than once produces the same
tables, foreign keys, and indexes.

For an existing database, apply
`migrations/20260713_reconcile_canonical_schema.sql` once. The migration is also
idempotent and may be retried after a failed deployment. It reconciles the old
dashboard migration variants without dropping application data.

The remaining migration files are historical records. Do not replay all of them
on a fresh database; several describe competing versions of the same dashboard
schema.

## Canonical names

| Canonical object | Deprecated legacy object |
| --- | --- |
| `job_descriptions.created_by` | `job_descriptions.created_by_id` |
| `candidates.best_match_job_id` | `candidates.job_id` |
| `audit_log` | `admin_audit_log` |

The reconciliation migration copies legacy values into these canonical objects.
It deliberately leaves legacy columns and tables in place so rollout does not
destroy data. Application code must only use the canonical names.

## Validation

Run the static contract check from the repository root:

```text
python database/validate_schema.py
```

For the full check, provide a disposable PostgreSQL database. The validator
creates and drops an isolated temporary schema, runs the canonical schema twice,
introduces all known legacy aliases, runs the migration twice, and verifies the
resulting columns, foreign keys, indexes, and backfilled data:

```text
python database/validate_schema.py --database-url postgresql://user:password@host/database
```

`SCHEMA_TEST_DATABASE_URL` can be used instead of the command-line argument.

## Existing duplicate responses

The canonical schema permits only one assessment per schedule and one response
per assessment/question (or coding problem). The forward migration will not
guess which historical duplicate is authoritative. If duplicates exist, it
prints a warning and leaves that unique index pending; clean those records with
an explicit, reviewed data-retention decision, then rerun the migration.
