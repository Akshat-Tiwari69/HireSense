# API Reference

**Base URL**: `http://localhost:5000` (Local)

All API responses follow a standard JSON structure:
```json
{
  "status": "success|error",
  "message": "Description...",
  "data": { ... }
}
```

## 🔐 Authentication

### Register User
`POST /auth/register`
- **Payload**: `{ "email": "...", "password": "...", "role": "interviewer|admin", "name": "..." }`
- **Response**: User ID.

### Login
`POST /auth/login`
- **Payload**: `{ "email": "...", "password": "..." }`
- **Response**: JWT Token (`access_token`).

---

## 🛡️ Admin Endpoints
*Requires `Authorization: Bearer <token>` (Admin Role)*

### Get System Stats
`GET /admin/analytics`
- Returns global counts of users, candidates, and assessments.

### Manage Users
`GET /admin/users`
- List all registered system users.

### Database Health
`GET /admin/db/tables`
- Returns current table row counts and health status.

---

## 👁️ Proctor Endpoints
*Requires `Authorization: Bearer <token>` (Proctor|Admin Role)*

### Active Assessments
`GET /proctor/assessments/active`
- Returns list of candidates currently taking tests.

### Scheduled Assessments
`GET /proctor/assessments/scheduled`
- Returns upcoming assessments.

### Incident Logs
`GET /proctor/assessments/completed`
- Returns finished assessments with potential red flags.

---

## 📝 Candidate & Interviewer

### Get Candidates
`GET /interviewer/candidates`
- List all candidates with their application status.

### Schedule Interview
`POST /interviewer/schedule_interview`
- **Payload**: `{ "candidate_id": "...", "date": "...", "time": "..." }`

### Submit Resume (Public)
`POST /upload_resume`
- **Multipart Form**: `file` (PDF/DOCX).
- **Response**: Extracted skills and AI analysis.
