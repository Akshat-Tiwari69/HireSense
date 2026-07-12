# Backend Flow Map

This document is the operational map for the HireSense backend after the July
2026 hardening pass. It describes ownership, state transitions, and failure
boundaries; the canonical database contract remains in
`database/schema_postgres.sql`.

## Runtime composition

`backend/run.py` applies Eventlet monkey-patching before importing the app, then
serves `backend/app.py:app_with_socketio` on port 5000. `backend/app.py` composes
Flask, CORS, header-only JWT authentication, request logging, response security
headers, rate limits, seven HTTP blueprints, protected uploads, Socket.IO, and
liveness/readiness endpoints.

The request path is:

```text
client -> CORS/security/rate-limit middleware -> JWT or assessment-token guard
       -> route handler -> domain helper/transaction -> PostgreSQL
       -> bounded external provider, when required -> JSON response
```

`GET /api/health` proves that the process can answer. `GET /api/health/ready`
runs `SELECT 1` and returns 503 until PostgreSQL is available.

## HTTP ownership

| Prefix | Primary module | Responsibility |
| --- | --- | --- |
| `/api/auth` | `backend/auth.py` | Registration, login, current-user lookup, JWT issue/validation |
| `/api/resume` | `backend/resume_routes.py` | Public PDF/DOCX application intake and resume analysis |
| `/api/jobs` | `backend/job_routes.py` | Sectors, postings, public listings, matching, review, audit records |
| `/api/interviewer` | `backend/interviewer_routes.py` | Candidate review, scheduling, results, early rejection, final decision |
| `/api/interviewee` | `backend/interviewee_routes.py` | Assessment token/session, answers, code evaluation, completion, monitoring |
| `/api/proctor` | `backend/proctor_routes.py` | Proctor assignments, dashboards, violations, private evidence reads |
| `/api/admin` | `backend/admin_routes.py` | Users, candidates, content, analytics, settings, database inspection |

`backend/interviewee_routes.py` composes three focused modules:
`interviewee_session.py`, `interviewee_answers.py`, and
`interviewee_monitoring.py`. Candidate assessment calls use
`X-Assessment-Token`; staff calls use `Authorization: Bearer <JWT>`.

## Database ownership

`backend/db_config.py` is the connection boundary. It applies connection,
statement, and idle-transaction timeouts; `db_connection()` rolls back on any
exception and always closes the connection.

| Domain | Primary owner |
| --- | --- |
| Users and authentication records | `backend/user_db.py` |
| Candidates and application creation | `backend/candidate_db.py` |
| Scheduling, question snapshots, responses, scoring, final decisions | `backend/assessment_db.py` |
| Canonical proctor violations and counters | `backend/proctoring_db.py` |
| Delivery history | `backend/email_db.py` |
| Sectors, jobs, matches, job audit records | `backend/job_routes.py` |
| Proctor assignment/report queries | `backend/proctor_routes.py` |
| Admin reporting/content queries | focused `backend/admin_*.py` modules |

Inline SQL remains in route modules where the operation is specific to one
route group. Every multi-row lifecycle mutation must still use one managed
transaction and explicit row locks where concurrent requests can race.

## Hiring lifecycle

1. **Apply.** `resume_routes.py` validates the job is still open, validates the
   real PDF/DOCX container, stores it below the configured private upload root,
   extracts text, runs bounded AI analysis or a deterministic fallback, and
   calls `candidate_db.py` to create the candidate and selected-job match in one
   transaction.
2. **Review and schedule.** `interviewer_routes.py` validates ownership and
   schedule input, generates a bounded question bundle, then
   `assessment_db.create_scheduled_assessment()` inserts the schedule and moves
   the candidate to `under_review` atomically. The invitation is best-effort
   after commit, so an email failure cannot erase the schedule.
3. **Verify and start.** `interviewee_session.py` verifies the capability token,
   allowed time window, and state. `assessment_db.start_assessment_by_token()`
   locks the schedule, creates or reuses exactly one assessment, copies the job,
   and moves both records to `in_progress` atomically. Questions are snapshotted
   on the assessment so later question-bank changes cannot alter a live test.
4. **Answer and monitor.** `interviewee_answers.py` validates every answer
   against the stored snapshot and scores it server-side. Response helpers lock
   the active assessment and upsert one logical response. Code runs use bounded
   Piston requests and hidden tests. `interviewee_monitoring.py` validates time
   and screenshots; `proctoring_db.py` writes the violation and synchronized
   counter in one transaction.
5. **Complete.** `assessment_db.finalize_assessment()` locks the assessment,
   aggregates MCQ/coding/psychometric results, persists normalized scores and
   recommendation, and moves the assessment, schedule, and candidate to
   `completed` in one transaction. Completion is retry-safe.
6. **Decide.** `assessment_db.record_final_decision()` locks the completed
   assessment and candidate together, then writes the human decision and
   `hired`/`rejected` candidate status in one commit. A repeated identical
   request does not request a duplicate email. Delivery remains best-effort
   after commit.

Canonical state chains:

```text
candidate:  applied -> under_review -> completed -> hired | rejected
schedule:   scheduled -> in_progress -> completed
assessment: absent -> in_progress -> completed
```

Cancelled schedules are terminal. Legacy `started` assessments are accepted as
active only where required for backward compatibility.

## Authentication and private data invariants

- The browser never connects directly to PostgreSQL/Supabase. It uses the REST
  API exclusively.
- Staff JWTs are header-only. Each token carries the user's database update
  version; protected requests fail closed after account deletion, password
  change, or role change.
- Assessment access tokens are capability secrets. Token-bearing path segments
  and invitation links are redacted from logs.
- Resume and screenshot files live below `UPLOAD_FOLDER`, are path-contained,
  and are never public static assets. Recruiting staff use the protected upload
  route; proctors fetch screenshot blobs through an assignment-checked endpoint.
- Admin database inspection masks password hashes and assessment access tokens.
  Environment status reports configured/unconfigured state, never secret text.

## External failure boundaries

| Dependency | Behavior |
| --- | --- |
| PostgreSQL | Startup remains alive for diagnostics; readiness is 503 and DB-backed endpoints return sanitized failures. Transactions roll back and close. |
| OpenAI | Timeouts, bounded retries/prompts/responses, strict output validation, deterministic fallback, owned-client cleanup. |
| Email | Resend/SMTP timeout and fallback, duplicate-send protection, one final log record; business transaction remains committed if delivery fails. |
| Piston | Language allowlist, input/output bounds, per-call timeout, hidden-test cap; provider failure cannot execute arbitrary local processes. |
| Filesystem/object volume | Upload root is configurable. Production must mount durable private storage and define backup/retention/deletion policy. |
| Socket.IO/WebRTC | Candidate token and assigned-staff authorization before room join or relay. Room state is process-local, so multi-worker deployment requires an external Socket.IO manager. |

## Deployment order

1. Back up the existing database.
2. For a new database, apply `database/schema_postgres.sql`.
3. For an existing database, apply
   `database/migrations/20260713_reconcile_canonical_schema.sql` once.
4. Configure secrets and `UPLOAD_FOLDER`; never use the development JWT flag in
   production.
5. Start `app:app_with_socketio` with an Eventlet-compatible worker.
6. Require `/api/health/ready` to pass before sending traffic.

## Verification limits

The automated suite covers domain transactions, authorization, input bounds,
provider fallbacks, schema contracts, frontend static checks, and production
builds. A live PostgreSQL/provider/WebRTC integration pass still requires valid
external services. If the configured database hostname is unavailable,
readiness correctly remains 503 and DB-backed browser screens show their
temporary-unavailable states.
