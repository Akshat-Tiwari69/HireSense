# Database Schema

HireSense uses PostgreSQL with a canonical schema and a legacy reconciliation path.

## Core Tables
- `users`: platform users and role metadata
- `candidates`: applicant profile + parsed resume data
- `sectors`: organizational sector boundaries
- `job_descriptions`: canonical job postings table
- `scheduled_assessments`: schedule metadata
- `assessments`: assessment lifecycle, scores, status
- `mcq_responses`, `coding_submissions`, `psychometric_responses`
- `proctoring_events`, `proctoring_violations`
- `candidate_job_matches`
- `email_logs`, `audit_log`

## Naming Note
`job_descriptions` is the database name; UI/API call them job postings.

## Migration Modes
- Fresh DB: `python backend/scripts/run_migration.py --schema`
- Existing legacy DB: `python backend/scripts/run_migration.py --reconcile`

## Schema Artifacts
- `database/schema_postgres.sql`
- `database/migrations/20260713_reconcile_canonical_schema.sql`
- `database/validate_schema.py`

## Next Reads
- [Roles and Permissions](Roles-and-Permissions.md)
- [Assessment and Proctoring](Assessment-and-Proctoring.md)
