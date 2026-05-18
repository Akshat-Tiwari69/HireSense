# HireSense Project Issues Audit

This file records the security, design, logic, runtime, build, and documentation issues found during a whole-project review.

## Checks run

- `python -m compileall backend database` — passed.
- `npm run build` — failed because `API_BASE_URL` is imported but not exported.
- `npm run lint` — failed with 871 reported problems.
- `pytest -q` — could not collect tests in this environment because `eventlet` was missing.

## Critical / high-impact issues

### 1. Frontend production build is broken

`frontend/src/components/ProctorMonitor.jsx` and `frontend/src/hooks/useProctorStream.js` import `API_BASE_URL`, but `frontend/src/services/api.js` declares it as a local constant and only exports `api`.

**Impact:** `npm run build` fails, so the frontend cannot be built for production.

**Suggested fix:** export `API_BASE_URL` from `frontend/src/services/api.js`.

### 2. Proctor API routes are probably double-prefixed

`backend/proctor_routes.py` defines the blueprint with `url_prefix='/api/proctor'`, and `backend/app.py` also registers it with `url_prefix='/api/proctor'`.

**Impact:** routes likely become `/api/proctor/api/proctor/...` instead of `/api/proctor/...`, causing frontend calls to fail with 404.

**Suggested fix:** remove one of the two prefixes. Prefer defining `proctor_bp = Blueprint('proctor', __name__)` and keeping the prefix in `app.py`.

### 3. Proctor routes call `get_connection(use_dict_cursor=True)`, but `get_connection` accepts no arguments

`backend/proctor_routes.py` calls `get_connection(use_dict_cursor=True)`, while `backend/db_config.py` defines `get_connection()` without parameters.

**Impact:** proctor dashboard routes will crash immediately when called.

**Suggested fix:** either update `get_connection` to accept cursor options or use `conn.cursor(cursor_factory=RealDictCursor)` in proctor routes.

### 4. Legacy dashboard endpoints expose and mutate candidate data without authentication

`backend/app.py` exposes `/api/dashboard/candidates` and `/api/dashboard/candidates/<candidate_id>/shortlist` without JWT or role checks.

**Impact:** anyone who can reach the backend can fetch all candidates and mutate shortlist state.

**Suggested fix:** remove these legacy endpoints or protect them with JWT and role authorization.

### 5. Duplicate `/api/auth/login` route exists

The auth blueprint has the real JWT login implementation, but `backend/app.py` also defines `/api/auth/login` and returns a mock token under `data.token` instead of `data.access_token`.

**Impact:** behavior depends on route ordering. If the legacy route is used, frontend login fails or clients receive an unusable fake token.

**Suggested fix:** delete the legacy login route from `backend/app.py`.

### 6. Assessment answer, completion, violation, and timer endpoints are tokenless

Candidate-facing endpoints under `/api/interviewee/assessment/<assessment_id>/...` accept only an assessment id and do not require a JWT, access token, or ownership check.

**Impact:** anyone who knows or guesses an assessment id can submit answers, complete an assessment, forge violations, or manipulate elapsed time.

**Suggested fix:** require and verify the scheduled assessment access token for every assessment-specific candidate endpoint.

### 7. WebSocket proctoring trusts unverified candidate tokens and interviewer user ids

The WebSocket server has TODO comments for verifying candidate access tokens and interviewer monitoring permissions, but currently trusts client-provided values.

**Impact:** attackers can join assessment rooms as fake candidates or interviewers and participate in WebRTC signaling.

**Suggested fix:** authenticate Socket.IO connections with JWT for staff and signed assessment tokens for candidates, then verify room membership server-side.

### 8. Uploaded resumes and violation screenshots are publicly served

`backend/app.py` serves everything under `/uploads/<path:filename>`. Resume uploads and violation screenshots are stored under the upload directory.

**Impact:** sensitive PII files can be accessed directly if URLs leak or are discovered.

**Suggested fix:** store private files outside public static paths and provide authenticated download endpoints with role/ownership checks.

### 9. Resume upload can leave orphan files and return success when DB insert fails

Resume files are saved before all validation is complete. If candidate insert fails, the exception is logged, but the endpoint can still return HTTP 200 with `candidate_id` set to `None`.

**Impact:** the server can accumulate orphaned PII files, and applicants may see success even when no candidate record exists.

**Suggested fix:** validate before saving where possible, delete files on failure, and return an error if persistence fails.

### 10. Admin settings endpoint can write arbitrary environment variables

The settings endpoint displays a tracked list of environment variables, but the POST endpoint accepts any variable name and writes it to the process environment and `.env`.

**Impact:** an admin account compromise can become arbitrary app configuration write access.

**Suggested fix:** enforce a strict write allowlist, require re-authentication for secret changes, audit changes, and avoid writing `.env` from web requests.

## Authorization and role model issues

### 11. Admin middleware only accepts `admin`, not `super_admin`

The auth module includes roles such as `super_admin`, `sector_admin`, and `recruiter`, but admin middleware only allows `admin`.

**Impact:** role behavior is inconsistent across routes. A `super_admin` may be rejected from admin APIs while job routes treat `admin` as `super_admin`.

**Suggested fix:** centralize RBAC logic and use one canonical role hierarchy everywhere.

### 12. Sector and recruiter scoping is not enforced consistently

Job routes define role hierarchy and a sector helper, but create/update/delete operations do not verify that sector-scoped users are allowed to act on the requested sector.

**Impact:** recruiter-level users can likely manage jobs outside their sector.

**Suggested fix:** enforce sector ownership for `sector_admin` and `recruiter`, and reserve cross-sector writes for `admin`/`super_admin`.

### 13. Candidate match endpoint is available to any authenticated user

`GET /api/jobs/matches/<candidate_id>` requires only a JWT and does not verify role, sector, or ownership.

**Impact:** any logged-in user can request match data for arbitrary candidates.

**Suggested fix:** require an appropriate role and enforce candidate/sector access checks.

### 14. Frontend route protection is not applied

The app defines dashboard routes directly. The role protection helper exists but is not used in `App.jsx`.

**Impact:** users can navigate to protected pages client-side. Backend checks still matter, but the UI can expose screens and cached/local state.

**Suggested fix:** wrap protected routes with a `ProtectedRoute` component that checks token and role.

### 15. JWT is stored in `localStorage`

The frontend reads and writes auth tokens in `localStorage`.

**Impact:** any XSS can steal tokens and impersonate users.

**Suggested fix:** prefer HttpOnly, Secure, SameSite cookies or reduce token lifetime and harden CSP if bearer tokens remain in browser storage.

## Assessment integrity issues

### 16. Candidate timer is partly client-controlled

The frontend gets initial remaining time from the server but syncs elapsed time through an unauthenticated endpoint.

**Impact:** candidates can potentially manipulate timing by calling the sync endpoint directly.

**Suggested fix:** calculate remaining time from server-side start timestamps.

### 17. Coding score trusts client-reported test counts

The frontend posts `testsPassed` and `totalTests`, and the backend saves those values directly.

**Impact:** candidates can inflate coding scores by editing the request.

**Suggested fix:** run tests server-side in a sandbox or treat client-reported coding results as untrusted.

### 18. MCQ endpoint reveals correctness immediately

The MCQ submit endpoint returns `is_correct` after saving an answer.

**Impact:** candidates can probe answers during the test, especially if retries are allowed.

**Suggested fix:** do not return correctness until the assessment is complete.

### 19. Assessment token verification returns candidate PII

The token verification endpoint returns candidate name and email for any valid token.

**Impact:** leaked assessment links expose PII before additional verification.

**Suggested fix:** reduce PII returned during verification and consider shorter-lived or one-time links.

### 20. Start window allows plus/minus 30 minutes

The token start logic uses absolute time difference, allowing starts up to 30 minutes before or 30 minutes after the scheduled time.

**Impact:** candidates can start late. This may be intended, but it should be explicit and consistently documented.

**Suggested fix:** define the allowed window precisely and enforce it with clear before/after bounds.

## Backend correctness and maintainability issues

### 21. Resume upload rate limit probably does not attach

The rate limiter attempts to limit endpoint `upload_resume`, but blueprint endpoint names are usually prefixed, such as `resume.upload_resume`.

**Impact:** the specific `10 per hour` upload limit may not apply.

**Suggested fix:** use the actual endpoint name or decorate the route directly.

### 22. Rate limiting uses in-memory storage

The limiter uses `memory://` storage.

**Impact:** limits reset on restart and are per-process, so they do not work reliably in multi-worker or multi-instance deployments.

**Suggested fix:** use Redis or another shared rate-limit backend.

### 23. Request logging verifies JWT on every response

The request logger calls `verify_jwt_in_request(optional=True)` in `after_request`.

**Impact:** every response pays JWT parsing overhead, and suppressed exceptions can hide unexpected behavior.

**Suggested fix:** store identity during authenticated request handling or only log identity when already available.

### 24. Audit logging treats JWT identity as email

JWT identity is set to user id, but job routes pass `get_jwt_identity()` into `audit_log` as `admin_email`, and `audit_log` looks up `users.email`.

**Impact:** audit rows can store ids in the email field and fail to populate `user_id`.

**Suggested fix:** either use email as identity or update audit logging to treat identity as user id and fetch email by id.

### 25. Admin user creation/update lacks email and password validation

Admin user routes validate only basic presence and role values.

**Impact:** admins can create malformed emails and weak passwords.

**Suggested fix:** reuse auth validators for email format and password policy.

### 26. Password hashing logs password length

`hash_password` logs password length.

**Impact:** password length is sensitive metadata and should not be logged.

**Suggested fix:** remove password-specific logging.

### 27. Several routes return internal exception strings

Some error paths return `str(e)` to clients.

**Impact:** database, schema, or implementation details can leak to attackers and users.

**Suggested fix:** log details server-side and return generic client-facing error messages.

### 28. Admin analytics appears to query columns from the wrong table

The base schema stores `technical_score` and `psychometric_score` on `assessments`, but admin analytics averages those columns from `scheduled_assessments`.

**Impact:** analytics may fail with missing-column errors unless another migration happens to add those columns.

**Suggested fix:** query `assessments` for score aggregates or align schema and migrations.

## Frontend quality and design issues

### 29. ESLint reports 871 problems

The lint run reports hundreds of errors and warnings, including unused imports, missing prop validation, hook dependency warnings, undefined Node globals in config files, direct state mutation, and unescaped entities.

**Impact:** lint cannot be used as a useful CI quality gate until noise is reduced.

**Suggested fix:** update lint configuration for the React/Vite setup and fix high-value errors first.

### 30. Proctor monitor uses a hardcoded fallback user id

The login flow stores token, email, and role, but not `user_id`. `ProctorMonitor` reads `user_id` from localStorage and falls back to `1`.

**Impact:** proctor sessions may be attributed to the wrong user.

**Suggested fix:** store authenticated user id consistently or use the JWT server-side instead of trusting a client-provided id.

### 31. Permissions-Policy disables camera and microphone globally

Security headers set `microphone=(), camera=()`.

**Impact:** if the frontend is served through Flask or receives these headers, proctoring camera access can be blocked.

**Suggested fix:** allow camera access for the app origin on proctoring pages.

### 32. CSP allows `unsafe-inline` and `unsafe-eval`

The CSP allows unsafe script execution modes.

**Impact:** XSS defenses are weakened.

**Suggested fix:** remove unsafe directives in production and use nonces/hashes or a Vite-compatible strict CSP.

## Database, seed, and documentation issues

### 33. Seed script creates known default credentials

The seed script hardcodes `admin123`, `interviewer123`, and `proctor123`, and prints them after creation.

**Impact:** accidental production/staging use creates easily guessed accounts.

**Suggested fix:** require seed passwords from environment variables or generate one-time random passwords and force reset.

### 34. README links reference missing or renamed documentation files

The README references documentation such as `docs/ENVIRONMENT_CONFIG.md`, `docs/PROJECT_ARCHITECTURE.md`, `docs/DATABASE_SCHEMA.md`, and `docs/API_DOCS.md`, but the repository contains differently named files such as `docs/ARCHITECTURE.md`, `docs/DATABASE.md`, and `docs/API.md`.

**Impact:** onboarding links are broken or confusing.

**Suggested fix:** update README links or add the missing docs.

### 35. Job posting table naming is inconsistent across code and docs

The database uses `job_descriptions`, while routes and UI call them job postings. Some docs and migration names use mixed terminology.

**Impact:** developers can easily update the wrong table or write inconsistent migrations.

**Suggested fix:** standardize terminology in docs and code comments, or migrate to a clearer table name.

## Suggested fix order

1. Fix the frontend build failure by exporting `API_BASE_URL`.
2. Fix proctor blueprint prefixing and `get_connection(use_dict_cursor=True)`.
3. Remove or protect legacy unauthenticated endpoints in `backend/app.py`.
4. Delete duplicate legacy `/api/auth/login` route in `backend/app.py`.
5. Add token verification to assessment answer, completion, violation, and timer endpoints.
6. Authenticate and authorize Socket.IO room joins.
7. Protect uploaded resumes and screenshots behind authenticated download endpoints.
8. Fix upload failure cleanup and return errors when database persistence fails.
9. Replace in-memory rate limiting with shared storage and verify route-specific limits attach.
10. Clean lint/build/test pipelines so CI can catch regressions.
