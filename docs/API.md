# API reference

This document provides a complete reference for the Cygnusa Elite Hire
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

Tokens expire after 24 hours. Obtain a token via the login endpoint.

## Role hierarchy

The platform uses role-based access control (RBAC) with the following
hierarchy. Higher-level roles inherit access to lower-level endpoints.

| Role | Level | Description |
|------|-------|-------------|
| `super_admin` | 100 | Full system control |
| `admin` | 90 | Maps to super_admin internally |
| `sector_admin` | 70 | Sector-scoped management |
| `recruiter` | 50 | Job postings and matching |
| `interviewer` | 30 | Candidate management |
| `proctor` | 20 | Live session monitoring |

---

## Authentication

**Prefix:** `/api/auth`

### Register

```
POST /api/auth/register
```

Create a new user account.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `email` | string | Yes | Valid email address |
| `password` | string | Yes | User password |
| `role` | string | Yes | `interviewer`, `admin`, `proctor`, `sector_admin`, or `recruiter` |
| `name` | string | Yes | Display name |

**Response:** `data.user_id`, `data.email`, `data.role`, `data.name`

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

**Prefix:** `/api/admin` — Requires `admin` role

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

### Database management

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/admin/db/tables` | List all database tables |
| `GET` | `/api/admin/db/tables/:table_name` | Get table data (max 100 rows) |
| `GET` | `/api/admin/db/stats` | Aggregate database statistics |

### System settings

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/admin/settings/env` | Get environment variable status (values masked) |
| `POST` | `/api/admin/settings/env` | Set or update an environment variable (`name`, `value`) |

### Analytics and logs

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/admin/analytics` | System-wide analytics (candidates, assessments, scores) |
| `GET` | `/api/admin/email-logs` | Email audit log (limit 100) |

### Bulk upload

```
POST /api/admin/bulk-upload
```

Upload a ZIP or RAR archive containing multiple resumes. Processes all
files concurrently against a specified job posting.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | file | Yes | ZIP or RAR archive |
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
| `POST` | `/api/admin/question-bank/upload` | `admin` / `interviewer` | Upload question bank (PDF/DOCX) |
| `GET` | `/api/admin/question-bank` | `admin` / `interviewer` | List all question banks |
| `GET` | `/api/admin/question-bank/:qb_id` | `admin` / `interviewer` | Get question bank with parsed questions |
| `DELETE` | `/api/admin/question-bank/:qb_id` | `admin` | Delete question bank |
| `PATCH` | `/api/admin/question-bank/:qb_id/toggle` | Any | Toggle active/inactive status |

---

## Interviewer endpoints

**Prefix:** `/api/interviewer` — Requires `interviewer` role

### Candidate operations

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/interviewer/candidates` | List candidates (filterable by `status`, sortable by `name`/`date`/`match_score`) |
| `GET` | `/api/interviewer/candidates/:candidate_id` | Candidate detail with assessment data |
| `GET` | `/api/interviewer/candidates/:candidate_id/resume` | Download resume file |
| `POST` | `/api/interviewer/candidates/:candidate_id/reject` | Reject candidate and send email notification |
| `GET/POST` | `/api/interviewer/candidates/:candidate_id/notes` | Get or add candidate notes |

### Assessment scheduling

```
POST /api/interviewer/candidates/:candidate_id/schedule
```

Schedule an assessment and generate AI-tailored questions.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `scheduled_time` | string | Yes | ISO 8601 datetime |
| `is_technical_role` | boolean | No | Default `true`. Disables coding section when `false` |
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

### Dashboard statistics

```
GET /api/interviewer/dashboard/stats
```

Returns aggregate counts: `total_candidates`, `pending`, `under_review`,
`hired`, `rejected`, `average_match_score`.

---

## Candidate (interviewee) endpoints

**Prefix:** `/api/interviewee` — Token-based access (no JWT required)

### Assessment access

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/interviewee/my-assessment/:candidate_id` | Check assessment status and time window |
| `GET` | `/api/interviewee/assessment/verify/:token` | Verify assessment link token |
| `POST` | `/api/interviewee/assessment/start/:candidate_id` | Start assessment (validates ±30-minute window) |
| `POST` | `/api/interviewee/assessment/start-by-token/:token` | Start assessment via secure token link |

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
| `questionId` | string |
| `answer` | `"A"`, `"B"`, `"C"`, or `"D"` |
| `timeSpent` | number (seconds) |

**Coding:**

| Field | Type |
|-------|------|
| `type` | `"coding"` |
| `questionId` | string |
| `code` | string |
| `language` | `"python"`, `"javascript"`, or `"java"` |
| `testsPassed` | number |
| `totalTests` | number |

**Psychometric:**

| Field | Type |
|-------|------|
| `type` | `"psychometric"` |
| `questionId` | string |
| `trait` | string |
| `score` | number |
| `selectedOption` | string |
| `scenarioResponse` | string |

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

---

## Proctor endpoints

**Prefix:** `/api/proctor` — Requires `proctor` or `admin` role

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/proctor/assessments/scheduled` | List scheduled assessments |
| `GET` | `/api/proctor/assessments/active` | List in-progress assessments with violation counts |
| `GET` | `/api/proctor/assessments/completed` | List completed assessments with scores (limit 50) |
| `GET` | `/api/proctor/assessments/:assessment_id/violations` | Get all violations for an assessment |
| `GET` | `/api/proctor/stats` | Dashboard statistics |
| `POST` | `/api/proctor/violations` | Record a violation from the browser (no JWT required) |

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
| `location` | string | No |
| `sector_id` | string | No |
| `employment_type` | string | No |
| `experience_level` | string | No |
| `salary_range` | string | No |
| `closes_at` | string | No |

### Candidate-job matching

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/api/jobs/match-candidate` | `recruiter`+ | Trigger AI matching for a candidate (`candidate_id`) |
| `GET` | `/api/jobs/matches/:candidate_id` | Any | Get all job matches for a candidate |
| `GET` | `/api/jobs/postings/:job_id/candidates` | `recruiter`+ | Get matched candidates for a job |

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
| `GET` | `/api/health` | Health check |
| `POST` | `/api/resume/upload` | Upload and analyze a resume (form data: `file`, `job_id`) |
| `GET` | `/api/dashboard/candidates` | List all candidates |
| `POST` | `/api/dashboard/candidates/:candidate_id/shortlist` | Update shortlist status |
| `GET` | `/uploads/:filename` | Serve uploaded files |

---

## WebSocket events

**Transport:** Socket.IO over eventlet (`/socket.io/`)

The WebSocket server handles real-time WebRTC signaling for live proctoring.

### Client to server

| Event | Payload | Description |
|-------|---------|-------------|
| `join_as_candidate` | `{assessment_id, access_token}` | Candidate joins proctoring room |
| `join_as_interviewer` | `{assessment_id, user_id}` | Proctor joins to monitor |
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
