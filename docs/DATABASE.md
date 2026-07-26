# Database schema

HireSense uses PostgreSQL (including Supabase-hosted PostgreSQL) through the
Flask backend. The canonical contract contains exactly 14 application tables.
[`database/schema_contract.py`](../database/schema_contract.py) is the
machine-readable source of truth; this document explains its data model.

`job_descriptions` is the historical database name for the job postings shown
by the API and UI.

## Relationships

```mermaid
erDiagram
    SECTORS ||--o{ USERS : scopes
    SECTORS ||--o{ CANDIDATES : scopes
    SECTORS ||--o{ JOB_DESCRIPTIONS : categorizes
    USERS ||--o{ JOB_DESCRIPTIONS : creates
    CANDIDATES ||--o{ SCHEDULED_ASSESSMENTS : receives
    USERS ||--o{ SCHEDULED_ASSESSMENTS : interviews
    USERS ||--o{ SCHEDULED_ASSESSMENTS : proctors
    JOB_DESCRIPTIONS ||--o{ SCHEDULED_ASSESSMENTS : targets
    SCHEDULED_ASSESSMENTS ||--o| ASSESSMENTS : starts
    CANDIDATES ||--o{ ASSESSMENTS : takes
    JOB_DESCRIPTIONS ||--o{ ASSESSMENTS : evaluates_for
    ASSESSMENTS ||--o{ MCQ_RESPONSES : contains
    ASSESSMENTS ||--o{ CODING_SUBMISSIONS : contains
    ASSESSMENTS ||--o{ PSYCHOMETRIC_RESPONSES : contains
    ASSESSMENTS ||--o{ PROCTORING_VIOLATIONS : records
    CANDIDATES ||--o{ CANDIDATE_JOB_MATCHES : receives
    JOB_DESCRIPTIONS ||--o{ CANDIDATE_JOB_MATCHES : receives
    USERS ||--o{ CANDIDATE_JOB_MATCHES : reviews
    USERS ||--o{ AUDIT_LOG : performs
    USERS ||--o{ CUSTOM_QUESTION_BANK : uploads
```

The assessment link is deliberately one-way:
`assessments.scheduled_assessment_id` references `scheduled_assessments.id` and
is unique when present. `scheduled_assessments` has no `assessment_id` column.
The link may be null for a legacy or manually created assessment.

Deleting a candidate cascades to that candidate's schedules, assessments, and
job matches; deleting an assessment cascades to its answers, submissions, and
violations. Deleting a scheduled interviewer is restricted. Optional ownership,
sector, job, proctor, reviewer, uploader, and audit-user links become null when
their referenced row is removed.

## Canonical tables and fields

Every timestamp below is `TIMESTAMPTZ`. Primary keys are integer `SERIAL`
values.

| Table | Purpose | Canonical fields |
| --- | --- | --- |
| `sectors` | Organizational access scopes | `id`, `name`, `description`, `email_alias`, `created_at`, `updated_at` |
| `users` | Staff authentication and RBAC | `id`, `email`, `password_hash`, `role`, `name`, `sector_id`, `created_at`, `updated_at` |
| `candidates` | Applicant profile, resume analysis, and current match summary | `id`, `name`, `email`, `phone`, `resume_path`, `parsed_skills`, `years_experience`, `education`, `match_score`, `shortlist_status`, `pros`, `cons`, `status`, `created_at`, `updated_at`, `best_match_job_id`, `sector_id` |
| `job_descriptions` | Job postings and matching requirements | `id`, `title`, `description`, `required_skills`, `min_experience`, `department`, `work_mode`, `created_at`, `updated_at`, `sector_id`, `status`, `preferred_skills`, `salary_range`, `employment_type`, `experience_level`, `closes_at`, `created_by`, `max_experience`, `role_complexity_level` |
| `scheduled_assessments` | Invitation, assignment, question cache, and scheduling lifecycle | `id`, `candidate_id`, `interviewer_id`, `scheduled_time`, `status`, `created_at`, `updated_at`, `access_token_hash`, `started_at`, `is_technical_role`, `questions_data`, `job_id`, `proctor_id` |
| `assessments` | Candidate session, timer, scoring, and decision record | `id`, `candidate_id`, `job_id`, `technical_score`, `psychometric_score`, `overall_score`, `automated_recommendation`, `automated_rationale`, `recommended_next_step`, `final_decision`, `final_rationale`, `proctoring_violations`, `status`, `scheduled_assessment_id`, `started_at`, `completed_at`, `created_at`, `questions_data`, `time_elapsed_seconds` |
| `mcq_responses` | Latest answer per assessment question | `id`, `assessment_id`, `question_id`, `selected_answer`, `is_correct`, `time_spent`, `created_at` |
| `coding_submissions` | Latest code per assessment problem | `id`, `assessment_id`, `problem_id`, `language`, `code`, `test_cases_passed`, `total_test_cases`, `submitted_at` |
| `psychometric_responses` | Latest response and score per scenario | `id`, `assessment_id`, `question_id`, `trait`, `score`, `scenario_response`, `created_at` |
| `proctoring_violations` | Canonical monitoring event and optional evidence path | `id`, `assessment_id`, `violation_type`, `description`, `screenshot_path`, `timestamp`, `severity` |
| `email_logs` | Delivery audit for system email | `id`, `recipient_email`, `recipient_name`, `email_type`, `subject`, `status`, `error_message`, `sent_at` |
| `candidate_job_matches` | Per-job matching score, explanation, and review state | `id`, `candidate_id`, `job_id`, `match_score`, `skill_match_score`, `experience_match_score`, `ai_reasoning`, `status`, `matched_at`, `reviewed_by`, `reviewed_at` |
| `audit_log` | Immutable-style staff action trail | `id`, `user_id`, `user_email`, `action`, `entity_type`, `entity_id`, `details`, `ip_address`, `created_at` |
| `custom_question_bank` | Uploaded source file, extracted text, and parsed questions | `id`, `original_filename`, `file_path`, `questions_text`, `parsed_questions`, `uploaded_by`, `description`, `tags`, `is_active`, `created_at`, `updated_at` |

`parsed_skills`, `required_skills`, and `preferred_skills` are text fields whose
current application readers accept serialized JSON arrays and normalized text.
`pros` and `cons` are newline-separated text. JSON documents live in
`questions_data`, `parsed_questions`, `audit_log.details`, and no other
canonical field.

`job_descriptions.work_mode` replaces the misleading legacy `location` name.
Reconciliation renames or merges that column without discarding its values,
normalizes remote/on-site/hybrid spelling variants, and treats old city-style
values as `On-Site`.

The raw assessment access token is returned only in the invitation link and is
never stored or logged. `access_token_hash` is its unique SHA-256 lookup value.
`resume_path`, `custom_question_bank.file_path`, and
`proctoring_violations.screenshot_path` are storage references; violation images
are exposed only through the assignment-checked proctor endpoint.

## Allowed values and checks

| Field | Allowed values |
| --- | --- |
| `users.role` | `interviewer`, `admin`, `proctor`, `super_admin`, `sector_admin`, `recruiter` |
| `candidates.status` | `applied`, `absence_of_details`, `pending`, `under_review`, `rejected`, `completed`, `hired` |
| `candidates.shortlist_status` | null, `High Match`, `Potential`, `Reject` |
| `job_descriptions.status` | `active`, `paused`, `closed`, `draft` |
| `job_descriptions.employment_type` | `full-time`, `part-time`, `contract`, `internship` |
| `job_descriptions.experience_level` | `junior`, `mid`, `senior`, `lead`, `principal` |
| `job_descriptions.work_mode` | `Remote`, `On-Site`, `Hybrid` |
| `scheduled_assessments.status` | `scheduled`, `in_progress`, `completed`, `cancelled` |
| `assessments.status` | `started`, `in_progress`, `completed` |
| `assessments.final_decision` | null, `Hire`, `No-Hire` |
| `proctoring_violations.severity` | `low`, `medium`, `high`, `critical` |
| `email_logs.status` | `sent`, `failed`, `bounced` |
| `candidate_job_matches.status` | `auto_matched`, `confirmed`, `rejected` |

The database also enforces:

- candidate experience is non-negative; candidate match scores are 0–100;
- job minimum experience is non-negative and maximum is null or at least the
  minimum;
- assessment and candidate/job match scores are 0–100;
- assessment violation counts are non-negative and elapsed time is 0–3600
  seconds;
- response question/problem IDs are positive, answer times are non-negative,
  and coding pass counts cannot exceed total tests;
- psychometric scores, when present, are 1–10.

The scorer writes `automated_recommendation`, `automated_rationale`, and
`recommended_next_step`. A later interviewer outcome is stored independently
in `final_decision` and `final_rationale`, so the human review never overwrites
the automated evidence. `job_descriptions.role_complexity_level` remains
application-validated text.

## Uniqueness and deliberate snapshots

User and candidate email addresses are unique case-insensitively through
indexes on `LOWER(email)`. The schema also guarantees:

- unique sector names and sector email aliases;
- one schedule per `access_token_hash`;
- at most one active (`scheduled` or `in_progress`) schedule per candidate;
- at most one assessment per schedule;
- one candidate/job match per pair;
- one MCQ, coding, or psychometric row per assessment/question or problem.

Several repeated values are intentional lifecycle snapshots, not competing
foreign keys:

- `candidates.best_match_job_id` and `candidates.match_score` summarize the
  selected `candidate_job_matches` row;
- schedule questions are generated before the invitation, then copied to
  `assessments.questions_data` so the live session has a stable snapshot;
- schedule and assessment job/candidate/start fields preserve their respective
  orchestration and session records;
- `assessments.proctoring_violations` caches the count of canonical
  `proctoring_violations` rows and is updated in the same transaction;
- `audit_log.user_email` preserves the actor identity even if `user_id` is later
  nulled.

## Indexing

Foreign keys and frequent filters have explicit indexes. Composite unique
indexes also serve their leftmost lookup columns, so redundant single-column
indexes are intentionally absent. Important filtered indexes enforce one active
schedule per candidate and one assessment per non-null schedule.

[`database/schema_contract.py`](../database/schema_contract.py) contains the
authoritative required and forbidden index names; avoid maintaining a second
handwritten index inventory here.

## Supabase and runtime access

The browser never accesses these tables directly. Flask uses a direct PostgreSQL
connection, and request authorization is enforced by the backend.

All 14 tables have RLS enabled. The schema revokes public-schema, table,
sequence, and function access from Supabase Data API roles `anon` and
`authenticated`. When the restricted `hiresense_app` role exists, it receives a
`hiresense_backend_access` policy on each table and only normal DML/sequence
privileges. It must not be a superuser and must not have create-role,
create-database, replication, or bypass-RLS privileges.

Use `DATABASE_URL` for the `hiresense_app` runtime connection. Reserve
`DATABASE_ADMIN_URL` for schema installation and reconciliation. The RLS policy
allows the trusted backend role to reach all rows; user-, role-, sector-, and
assignment-level authorization therefore remains a Flask responsibility. In
production, both URLs must set `sslmode=verify-full` and point `sslrootcert`
at Supabase's downloaded CA certificate.

## Install, reconcile, and validate

Run from the repository root:

```powershell
# Fresh, empty PostgreSQL database
python backend/scripts/run_migration.py --schema

# Existing HireSense database
python backend/scripts/run_migration.py --reconcile

# Static contract check
python database/validate_schema.py

# Idempotence and legacy-upgrade integration check against a disposable database
python database/validate_schema.py --database-url postgresql://user:password@host/database
```

The runner applies SQL transactionally and verifies tables, exact columns,
timezone types, checks, nullability, foreign keys, indexes, RLS, Data API
revocations, and runtime-role safety before committing. The integration
validator uses an isolated temporary schema and runs the fresh schema and
reconciliation twice.

Supported artifacts:

| Starting state | Artifact |
| --- | --- |
| Empty database | [`database/schema_postgres.sql`](../database/schema_postgres.sql) |
| Existing legacy database | [`database/migrations/20260713_reconcile_canonical_schema.sql`](../database/migrations/20260713_reconcile_canonical_schema.sql) |

Older migrations are historical references, not an ordered installation
procedure.

## Removed legacy objects

Reconciliation copies recoverable canonical data before removing obsolete
objects. The final contract rejects:

- tables `admin_audit_log`, `proctoring_events`, `questions`, and
  `sector_email_configs`;
- columns `users.permissions`, `candidates.job_id`,
  `candidates.parsed_skills_json`, `job_descriptions.created_by_id`,
  `scheduled_assessments.assessment_id`, `is_streaming`, `stream_started_at`,
  and `stream_ended_at`, `coding_submissions.execution_time` and
  `error_message`, and `custom_question_bank.filename`;
- redundant legacy email, response, token, and candidate-match indexes listed
  in the machine-readable contract.
