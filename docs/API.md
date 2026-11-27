# API reference

This document provides a complete reference for the HireSense
REST API and WebSocket events.

## Conventions

**Base URL:** `http://localhost:5000` (development)

All responses follow a standard envelope:

```json
{
  "status": "success",
  "message": "Description",
  "data": { }
}
```

**Authentication:** Protected endpoints require a JWT token in the
`Authorization` header:

```
Authorization: Bearer <access_token>
```

Tokens expire after `JWT_ACCESS_TOKEN_MINUTES` (default 60 minutes). A token
is also rejected once the user's account is updated or deleted. Obtain a token
via the login endpoint.

## Role hierarchy

Job and sector endpoints use this minimum-level hierarchy. Other blueprints
check an explicit set of roles instead (see each section).

| Role | Level | Description |
|------|-------|-------------|
| `super_admin` | 100 | Full system control |
| `admin` | 90 | Treated as `super_admin` by job and sector endpoints |
| `sector_admin` | 70 | Sector-scoped management |
| `recruiter` | 50 | Job postings and matching |
| `interviewer` | 30 | Candidate management |
| `proctor` | 20 | Live session monitoring |

---

## Authentication

**Prefix:** `/api/auth`

### Login

```
POST /api/auth/login
```

Authenticate and receive a JWT token.

| Field | Type | Required |
|-------|------|----------|
| `email` | string | Yes |
| `password` | string | Yes |

**Response:** `data.access_token`, `data.user.{id, email, role, name}`

There is no public registration endpoint. Admins create staff accounts with
`POST /api/admin/users`.

### Demo login

```
POST /api/auth/demo-login
```

Signs in as a seeded demo account. Only exists when `DEMO_MODE=true`
(otherwise 404).

| Field | Type | Required |
|-------|------|----------|
| `role` | string | Yes; `admin`, `interviewer`, or `proctor` |

**Response:** same as login.

### Get current user

```
GET /api/auth/me
```

Returns the authenticated user's profile. Requires JWT.

**Response:** `data.{id, email, role, name, sector_id, created_at}`

### Verify token

```
GET /api/auth/verify
```

Validate that the current JWT token is still valid. Requires JWT.

**Response:** `data.{user_id, role, name}`

---

## Admin endpoints

**Prefix:** `/api/admin` — Requires `admin` or `super_admin`. Creating, editing, or deleting `admin`/`super_admin` accounts requires `super_admin`.

### User management

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/admin/users` | List all users |
| `POST` | `/api/admin/users` | Create a user (`name`, `email`, `password`, `role`) |
| `PUT` | `/api/admin/users/:user_id` | Update user fields |
| `DELETE` | `/api/admin/users/:user_id` | Delete a user |

### Candidate management

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/admin/candidates` | List all candidates with scores and status |
| `GET` | `/api/admin/absence-of-details` | Find candidates missing key information |
| `PUT` | `/api/admin/candidates/:candidate_id` | Update candidate fields |
| `DELETE` | `/api/admin/candidates/:candidate_id` | Delete candidate and related data |
| `POST` | `/api/admin/reset-candidate-status/:candidate_id` | Reset status to "Applied" |

### Analytics and logs

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/admin/db/stats` | Aggregate database statistics |
| `GET` | `/api/admin/analytics` | System-wide analytics (candidates, assessments, scores) |
| `GET` | `/api/admin/email-logs` | Email audit log (limit 100) |

### Bulk upload

```
POST /api/admin/bulk-upload
```

Upload a ZIP archive (up to 100 PDF/DOCX resumes, 10 MB each) as
`multipart/form-data`. Processes the files concurrently against a job posting.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | file | Yes | ZIP archive |
| `job_id` | string | Yes | Target job posting ID |

**Response:** `summary.{total, success, duplicates, errors}`, `results[]`

### AI enhancement

```
POST /api/admin/ai-enhance
```

Use AI to polish job or sector descriptions.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | Yes | `job` or `sector` |
| `title` | string | Yes | Title to enhance |
| `description` | string | Yes | Description to enhance |

### Question bank

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/api/admin/question-bank/upload` | `admin` | Upload question bank (PDF/DOCX) |
| `GET` | `/api/admin/question-bank` | `admin` | List all question banks |
| `GET` | `/api/admin/question-bank/:qb_id` | `admin` | Get question bank with parsed questions |
| `DELETE` | `/api/admin/question-bank/:qb_id` | `admin` | Delete question bank |
| `PATCH` | `/api/admin/question-bank/:qb_id/toggle` | `admin` | Toggle active/inactive status |

---

## Interviewer endpoints

**Prefix:** `/api/interviewer` — Requires `interviewer`, `recruiter`, or `sector_admin`. Interviewers only reach candidates assigned to them; recruiters and sector admins only reach their sector.

### Candidate operations

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/interviewer/candidates` | List candidates (filterable by `status`, sortable by `name`/`date`/`match_score`) |
| `GET` | `/api/interviewer/candidates/:candidate_id` | Candidate detail with assessment data |
| `GET` | `/api/interviewer/candidates/:candidate_id/resume` | Download resume file |
| `POST` | `/api/interviewer/candidates/:candidate_id/reject` | Reject candidate and send email notification |

### Assessment scheduling

```
POST /api/interviewer/candidates/:candidate_id/schedule
```

Schedule an assessment and generate AI-tailored questions.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `scheduled_time` | string | Yes | ISO 8601 datetime |
| `is_technical_role` | boolean | No | Default `true`. Disables coding section when `false`. Returns an error while the code runner is disabled |
| `additional_info` | string | No | Extra context for AI question generation |

**Response:** `data.{scheduled_assessment_id, assessment_link, email_sent}`

### Assessment results

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/interviewer/assessments/:candidate_id` | Get assessment scores and details |

### Final decision

```
POST /api/interviewer/assessments/:assessment_id/final-decision
```

Record a hire or no-hire decision with optional rationale. Sends an email
notification to the candidate.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `decision` | string | Yes | `hire` or `no-hire` |
| `rationale` | string | No | Reasoning for the decision |
| `next_steps` | string | No | Next steps communicated to candidate |

---

## Candidate (interviewee) endpoints

**Prefix:** `/api/interviewee` — Token-based access (no JWT required)

### Assessment access

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/interviewee/assessment/verify` | Verify the `X-Assessment-Token` header |
| `POST` | `/api/interviewee/assessment/start` | Start or resume using the `X-Assessment-Token` header |
| `GET` | `/api/interviewee/assessment/:assessment_id/remaining-time` | Server-calculated remaining time |

The assessment can only be started within ±30 minutes of its scheduled time.
All candidate endpoints authenticate with the `X-Assessment-Token` header.

### Answer submission

```
POST /api/interviewee/assessment/:assessment_id/submit-answer
```

Submit an answer during an active assessment. The `type` field determines
the expected payload:

**MCQ:**

| Field | Type |
|-------|------|
| `type` | `"mcq"` |
| `questionId` | number |
| `answer` | `"A"`, `"B"`, `"C"`, or `"D"` |
| `timeSpent` | number (seconds) |

**Coding:**

| Field | Type |
|-------|------|
| `type` | `"coding"` |
| `questionId` | number |
| `code` | string (max 100 KB) |
| `language` | `"python"` or `"javascript"` |

The server runs the stored test cases itself; client-reported results are ignored.

**Psychometric:**

| Field | Type |
|-------|------|
| `type` | `"psychometric"` |
| `questionId` | number |
| `selectedOption` | number (option index) |

The trait and score are looked up server-side from the stored scenario.

### Run code

```
POST /api/interviewee/run-code
```

Run code against one stored test case. Returns 503 when the code runner is
disabled.

| Field | Type |
|-------|------|
| `language` | `"python"` or `"javascript"` |
| `code` | string (max 100 KB) |
| `problem_id` | number |
| `test_case_index` | number |

### Assessment completion

```
POST /api/interviewee/assessment/:assessment_id/complete
```

Finalize the assessment and calculate scores.

**Response:** `data.scores.{mcq, coding, technical, psychometric, overall}`,
`data.decision`, `data.ai_recommendation`

### Proctoring events

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/interviewee/assessment/:assessment_id/violation` | Report a proctoring violation (with optional base64 screenshot) |
| `POST` | `/api/interviewee/assessment/:assessment_id/sync-time` | Sync elapsed time |

The browser reports `violation_type` as `tab_hidden`, `focus_lost`, `copy_paste`, `no_face`,
`multiple_faces`, or `camera_interrupted` (the backend accepts any short lowercase type name). Screenshot evidence is rate limited
per assessment.

---

## Proctor endpoints

**Prefix:** `/api/proctor` — Requires `proctor`. Results are limited to assessments assigned to the current proctor or still unassigned.

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/proctor/scheduled-assessments` | List scheduled assessments available to the current proctor |
| `GET` | `/api/proctor/active-assessments` | List assigned or unassigned in-progress assessments with violation counts |
| `GET` | `/api/proctor/completed-assessments` | List the current proctor's completed assessments with scores |
| `GET` | `/api/proctor/assessments/:assessment_id/violations` | Get all violations for an assessment |
| `GET` | `/api/proctor/dashboard-stats` | Dashboard statistics scoped to the current proctor |
| `GET` | `/api/proctor/violations/:violation_id/screenshot` | Retrieve authorized violation evidence |
| `GET` | `/api/proctor/violations/flagged` | List flagged violations |
| `GET` | `/api/proctor/violation-statistics` | Violation counts by type and severity over a period (`days`, default 30) |
| `GET` | `/api/proctor/anomaly-detection` | Assessments whose violation counts or scores look unusual |
| `GET` | `/api/proctor/quality-metrics` | Proctoring quality metrics |
| `GET` | `/api/proctor/job-performance` | Scores and violation totals per job posting |
| `GET` | `/api/proctor/shift-summary` | Today's assessments, scores, and violation totals for the current proctor |
| `POST` | `/api/proctor/assign-assessment` | Claim an available assessment |

---

## Job postings and matching

**Prefix:** `/api/jobs`

### Sectors

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/api/jobs/sectors` | Public | List all sectors |
| `POST` | `/api/jobs/sectors` | `super_admin` | Create a sector |
| `PUT` | `/api/jobs/sectors/:sector_id` | `super_admin` | Update a sector |
| `DELETE` | `/api/jobs/sectors/:sector_id` | `super_admin` | Delete a sector |

### Job postings

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/api/jobs/postings` | Public | List postings (filter by `status`, `sector_id`) |
| `GET` | `/api/jobs/postings/:job_id` | Public | Get a single posting |
| `POST` | `/api/jobs/postings` | `recruiter`+ | Create a job posting |
| `PUT` | `/api/jobs/postings/:job_id` | `recruiter`+ | Update a job posting |
| `DELETE` | `/api/jobs/postings/:job_id` | `recruiter`+ | Delete a job posting |

**Job posting fields:**

| Field | Type | Required |
|-------|------|----------|
| `title` | string | Yes |
| `required_skills` | string | Yes |
| `description` | string | No |
| `preferred_skills` | string | No |
| `min_experience` | number | No |
| `max_experience` | number | No |
| `department` | string | No |
| `work_mode` | string | No; `Remote`, `On-Site`, or `Hybrid` (defaults to `On-Site`) |
| `sector_id` | string | No |
| `status` | string | No; `active`, `paused`, `closed`, or `draft` |
| `employment_type` | string | No |
| `experience_level` | string | No |
| `salary_range` | string | No |
| `closes_at` | ISO datetime string | No; active roles must close in the future |
| `role_complexity_level` | string | No; defaults to `intermediate` |

`location` was a misleading legacy name and is rejected by write endpoints.
Clients must send `work_mode`; common work-mode spelling variants are normalized
to one of the three canonical values.

### Candidate-job matching

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/api/jobs/match-candidate` | `recruiter`+ | Trigger AI matching for a candidate (`candidate_id`) |
| `GET` | `/api/jobs/matches/:candidate_id` | Any | Get all job matches for a candidate |
| `GET` | `/api/jobs/postings/:job_id/candidates` | `recruiter`+ | Get matched candidates for a job |
| `PATCH` | `/api/jobs/matches/:candidate_id/:job_id` | `recruiter`+ | Confirm or reject a match with `{ "status": "confirmed" | "rejected" }` |

### Audit log

```
GET /api/jobs/audit-log
```

Requires `super_admin`. Returns audit trail entries with `user_email`,
`action`, `entity_type`, `details`, and `ip_address`.

---

## Root endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | API info and health status |
| `GET` | `/api/health` | Liveness: `{"status": "ok", "demo_mode": <bool>}` |
| `GET` | `/api/health/ready` | Readiness: checks PostgreSQL (503 when unavailable) and reports `code_runner` |
| `POST` | `/api/resume/upload` | Submit an application (`file`, `job_id`, `name`, `email`, optional `phone`); returns only the application ID, status, and selected job confirmation |

Uploaded files are never served publicly. Resumes are downloaded through
`/api/interviewer/candidates/:candidate_id/resume` and violation screenshots
through `/api/proctor/violations/:violation_id/screenshot`.

---

## WebSocket events

**Transport:** Socket.IO over eventlet (`/socket.io/`)

The WebSocket server handles real-time WebRTC signaling for live proctoring.

The connection itself is authenticated through the Socket.IO `auth` payload;
unauthenticated connections are refused:

- Candidate: `{role: "candidate", assessment_id, access_token}`
- Staff: `{role: "staff", assessment_id, token: <JWT>}`. Allowed for the assigned
  interviewer or proctor, and for recruiters and sector admins in the candidate's sector.

### Client to server

| Event | Payload | Description |
|-------|---------|-------------|
| `join_as_candidate` | `{assessment_id}` | Candidate joins proctoring room |
| `join_as_interviewer` | `{assessment_id}` | Staff member joins to monitor |
| `webrtc_offer` | `{assessment_id, offer}` | Forward SDP offer to interviewers |
| `webrtc_answer` | `{assessment_id, answer}` | Forward SDP answer to candidate |
| `ice_candidate` | `{assessment_id, candidate, target}` | Forward ICE candidate |
| `get_active_assessments` | `{}` | Request active room list |

### Server to client

| Event | Recipient | Description |
|-------|-----------|-------------|
| `joined` | Joining client | Room join confirmation with peer presence info |
| `candidate_joined` | Interviewers | Candidate entered the room |
| `candidate_disconnected` | Interviewers | Candidate left the room |
| `interviewer_joined` | Candidate | Triggers WebRTC offer initiation |
| `webrtc_offer` | Interviewers | Forwarded SDP offer |
| `webrtc_answer` | Candidate | Forwarded SDP answer |
| `ice_candidate` | Target peer | Forwarded ICE candidate |
| `active_assessments` | Requester | List of active assessment rooms |
| `error` | Caller | Error message |
