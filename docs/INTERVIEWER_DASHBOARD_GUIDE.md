# Interviewer Dashboard API Guide

Complete documentation for the Interviewer Dashboard endpoints used by recruiters and hiring managers to manage candidates and make hiring decisions.

## Overview

The Interviewer Dashboard provides a comprehensive set of protected endpoints that allow interviewers (recruiters/hiring managers) to:
- View all candidates with their resume analysis
- Review detailed candidate information and AI-generated insights
- Schedule assessments with automatic email notifications
- View assessment results and scores
- Make final hiring decisions (hire/no-hire) with email notifications
- Track hiring pipeline statistics

**Base URL:** `http://localhost:5000/api/interviewer`

**Authentication:** All endpoints require JWT token with `interviewer` role in headers:
```
Authorization: Bearer <JWT_TOKEN>
```

---

## Authentication Requirements

All interviewer endpoints require:
1. Valid JWT access token (obtained from `/api/auth/login`)
2. Token must have `role: "interviewer"` claim
3. 24-hour token expiration

If authentication fails:
```json
{
  "status": "error",
  "message": "Access denied. Interviewer role required."
}
```

---

## Endpoints

### 1. Get All Candidates

**Endpoint:** `GET /api/interviewer/candidates`

**Authentication:** Required (interviewer role)

**Description:** Retrieve list of all candidates with resume analysis, AI insights, and current status.

**Query Parameters:**
| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `status` | string | Filter by candidate status | `pending`, `under_review`, `rejected`, `hired` |
| `sort` | string | Sort field | `name`, `date`, `match_score` |
| `order` | string | Sort direction | `asc` or `desc` |

**Example Request:**
```bash
curl -X GET "http://localhost:5000/api/interviewer/candidates?status=pending&sort=match_score&order=desc" \
  -H "Authorization: Bearer eyJhbGc..."
```

**Success Response (200):**
```json
{
  "status": "success",
  "data": [
    {
      "id": 1,
      "name": "John Doe",
      "email": "john@example.com",
      "phone": "+1-555-0100",
      "status": "pending",
      "match_score": 85.5,
      "pros": [
        "5+ years of Python experience",
        "Strong system design knowledge",
        "Good communication skills"
      ],
      "cons": [
        "Limited AWS experience",
        "No machine learning background"
      ],
      "recommendation": "Good candidate for mid-level backend role",
      "confidence_score": 0.88,
      "enhanced_match_score": 82.3,
      "resume_path": "uploads/resume_1234.pdf",
      "created_at": "2026-01-20T10:30:00"
    },
    {
      "id": 2,
      "name": "Jane Smith",
      "email": "jane@example.com",
      "phone": "+1-555-0101",
      "status": "under_review",
      "match_score": 92.0,
      "pros": [
        "Exceptional technical skills",
        "Leadership experience"
      ],
      "cons": [],
      "recommendation": "Excellent candidate for senior role",
      "confidence_score": 0.95,
      "enhanced_match_score": 90.8,
      "resume_path": "uploads/resume_5678.pdf",
      "created_at": "2026-01-21T09:15:00"
    }
  ],
  "total": 2
}
```

**Error Response (500):**
```json
{
  "status": "error",
  "message": "Failed to fetch candidates: [error details]"
}
```

---

### 2. Get Candidate Details

**Endpoint:** `GET /api/interviewer/candidates/:candidate_id`

**Authentication:** Required (interviewer role)

**Description:** Get detailed information for a specific candidate including assessment status.

**URL Parameters:**
- `candidate_id` (integer): Unique candidate identifier

**Example Request:**
```bash
curl -X GET "http://localhost:5000/api/interviewer/candidates/1" \
  -H "Authorization: Bearer eyJhbGc..."
```

**Success Response (200):**
```json
{
  "status": "success",
  "data": {
    "id": 1,
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+1-555-0100",
    "status": "pending",
    "match_score": 85.5,
    "pros": [
      "5+ years of Python experience",
      "Strong system design knowledge"
    ],
    "cons": [
      "Limited AWS experience"
    ],
    "recommendation": "Good candidate for mid-level backend role",
    "confidence_score": 0.88,
    "enhanced_match_score": 82.3,
    "resume_path": "uploads/resume_1234.pdf",
    "created_at": "2026-01-20T10:30:00",
    "assessment": null
  }
}
```

**Error Response (404):**
```json
{
  "status": "error",
  "message": "Candidate not found"
}
```

---

### 3. Reject Candidate

**Endpoint:** `POST /api/interviewer/candidates/:candidate_id/reject`

**Authentication:** Required (interviewer role)

**Description:** Reject a candidate after resume review. Sends professional rejection email automatically.

**URL Parameters:**
- `candidate_id` (integer): Unique candidate identifier

**Request Body:**
```json
{
  "reason": "Experience doesn't align with current requirements"
}
```

**Example Request:**
```bash
curl -X POST "http://localhost:5000/api/interviewer/candidates/1/reject" \
  -H "Authorization: Bearer eyJhbGc..." \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "Limited experience in required tech stack"
  }'
```

**Success Response (200):**
```json
{
  "status": "success",
  "message": "Candidate rejected successfully",
  "data": {
    "candidate_id": 1,
    "candidate_name": "John Doe",
    "status": "rejected",
    "email_sent": true
  }
}
```

**Error Response (404):**
```json
{
  "status": "error",
  "message": "Candidate not found"
}
```

---

### 4. Schedule Assessment

**Endpoint:** `POST /api/interviewer/candidates/:candidate_id/schedule`

**Authentication:** Required (interviewer role)

**Description:** Schedule an assessment for a candidate. Automatically sends invitation email with unique assessment link.

**URL Parameters:**
- `candidate_id` (integer): Unique candidate identifier

**Request Body:**
```json
{
  "scheduled_time": "2026-02-01T14:00:00",
  "additional_info": "Please complete the assessment by February 3rd. Interview will be conducted via video call."
}
```

**Scheduled Time Formats Accepted:**
- ISO 8601: `2026-02-01T14:00:00`
- ISO with timezone: `2026-02-01T14:00:00+00:00`
- Standard format: `02/01/2026 14:00:00`

**Example Request:**
```bash
curl -X POST "http://localhost:5000/api/interviewer/candidates/1/schedule" \
  -H "Authorization: Bearer eyJhbGc..." \
  -H "Content-Type: application/json" \
  -d '{
    "scheduled_time": "2026-02-01T14:00:00",
    "additional_info": "Please complete by February 3rd"
  }'
```

**Success Response (201):**
```json
{
  "status": "success",
  "message": "Assessment scheduled successfully",
  "data": {
    "candidate_id": 1,
    "candidate_name": "John Doe",
    "scheduled_assessment_id": 15,
    "scheduled_time": "2026-02-01T14:00:00",
    "assessment_link": "http://localhost:5173/assessment/15",
    "status": "under_review",
    "email_sent": true
  }
}
```

**Error Response (400):**
```json
{
  "status": "error",
  "message": "scheduled_time is required"
}
```

**Error Response (404):**
```json
{
  "status": "error",
  "message": "Candidate not found"
}
```

---

### 5. Get Assessment Results

**Endpoint:** `GET /api/interviewer/assessments/:candidate_id`

**Authentication:** Required (interviewer role)

**Description:** Retrieve assessment results and scores for a candidate (if assessment has been completed).

**URL Parameters:**
- `candidate_id` (integer): Unique candidate identifier

**Example Request:**
```bash
curl -X GET "http://localhost:5000/api/interviewer/assessments/1" \
  -H "Authorization: Bearer eyJhbGc..."
```

**Success Response (200):**
```json
{
  "status": "success",
  "data": {
    "id": 15,
    "candidate_id": 1,
    "candidate_name": "John Doe",
    "technical_score": 78.5,
    "psychometric_score": 82.0,
    "mcq_score": 76.5,
    "coding_score": 80.5,
    "decision": "Pending",
    "rationale": "Assessment completed, awaiting final review",
    "ai_recommendation": "Strong technical fundamentals with good problem-solving approach",
    "created_at": "2026-01-20T10:30:00",
    "completed_at": "2026-01-21T15:45:00"
  }
}
```

**Error Response (404):**
```json
{
  "status": "error",
  "message": "No assessment found for this candidate"
}
```

---

### 6. Make Final Decision

**Endpoint:** `POST /api/interviewer/assessments/:assessment_id/final-decision`

**Authentication:** Required (interviewer role)

**Description:** Record final hiring decision (hire or no-hire) after assessment completion. Sends decision email with scores and next steps.

**URL Parameters:**
- `assessment_id` (integer): Unique assessment identifier

**Request Body:**
```json
{
  "decision": "hire",
  "rationale": "Excellent technical skills, great cultural fit, strong problem-solving approach",
  "next_steps": "Please send us your availability for contract discussion by tomorrow."
}
```

**Decision Options:**
- `"hire"` or `"hired"` or `"selected"` - Offer the position
- `"no-hire"` - Reject after assessment

**Example Request:**
```bash
curl -X POST "http://localhost:5000/api/interviewer/assessments/15/final-decision" \
  -H "Authorization: Bearer eyJhbGc..." \
  -H "Content-Type: application/json" \
  -d '{
    "decision": "hire",
    "rationale": "Excellent fit with strong technical skills",
    "next_steps": "Please confirm your availability for HR discussion"
  }'
```

**Success Response (200):**
```json
{
  "status": "success",
  "message": "Final decision recorded successfully",
  "data": {
    "assessment_id": 15,
    "candidate_id": 1,
    "candidate_name": "John Doe",
    "decision": "Hire",
    "status": "hired",
    "scores": {
      "technical": 78.5,
      "psychometric": 82.0,
      "overall": 79.55
    },
    "email_sent": true
  }
}
```

**Error Response (400):**
```json
{
  "status": "error",
  "message": "decision must be \"hire\" or \"no-hire\""
}
```

**Error Response (404):**
```json
{
  "status": "error",
  "message": "Assessment not found"
}
```

---

### 7. Get Dashboard Statistics

**Endpoint:** `GET /api/interviewer/dashboard/stats`

**Authentication:** Required (interviewer role)

**Description:** Get dashboard statistics showing candidate pipeline metrics and average scores.

**Example Request:**
```bash
curl -X GET "http://localhost:5000/api/interviewer/dashboard/stats" \
  -H "Authorization: Bearer eyJhbGc..."
```

**Success Response (200):**
```json
{
  "status": "success",
  "data": {
    "total_candidates": 12,
    "pending": 4,
    "under_review": 3,
    "hired": 2,
    "rejected": 3,
    "average_match_score": 78.92
  }
}
```

---

### 8. Manage Candidate Notes

**Endpoint:** `GET /api/interviewer/candidates/:candidate_id/notes`

**Endpoint:** `POST /api/interviewer/candidates/:candidate_id/notes`

**Authentication:** Required (interviewer role)

**Description:** Add or retrieve notes for a candidate (future implementation).

**Example Request (GET):**
```bash
curl -X GET "http://localhost:5000/api/interviewer/candidates/1/notes" \
  -H "Authorization: Bearer eyJhbGc..."
```

**Success Response (200):**
```json
{
  "status": "success",
  "data": {
    "candidate_id": 1,
    "notes": []
  }
}
```

---

## Common Status Values

| Status | Description |
|--------|-------------|
| `pending` | Resume uploaded, awaiting review |
| `under_review` | Assessment scheduled or in progress |
| `hired` | Candidate selected and offer made |
| `rejected` | Candidate rejected at any stage |

---

## Error Handling

All endpoints follow consistent error response format:

**Authentication Error (403):**
```json
{
  "status": "error",
  "message": "Access denied. Interviewer role required."
}
```

**Not Found Error (404):**
```json
{
  "status": "error",
  "message": "[Resource] not found"
}
```

**Bad Request Error (400):**
```json
{
  "status": "error",
  "message": "[Field] is required"
}
```

**Server Error (500):**
```json
{
  "status": "error",
  "message": "Failed to [action]: [error details]"
}
```

---

## Email Integration

All endpoints that send emails are integrated with the Email Service and:
1. Support multiple email providers (Gmail, SendGrid, AWS SES, custom SMTP)
2. Use professional HTML templates with plain text fallbacks
3. Include candidate name, assessment link, and next steps
4. Log all emails in the database for audit trail
5. Include retry logic for failed email attempts

**Email Types Sent:**
- **Assessment Invitation:** When scheduling assessment
- **Rejection Email:** When rejecting a candidate
- **Final Decision:** When making hire/no-hire decision

---

## Frontend Integration

### Authentication
1. User logs in via `/api/auth/login` with email and password
2. Receives JWT token with `interviewer` role
3. Include token in all subsequent requests:
```javascript
const headers = {
  'Authorization': `Bearer ${token}`,
  'Content-Type': 'application/json'
};
```

### Example Frontend Flow
```javascript
// Get all candidates
const getCandidates = async (token) => {
  const response = await fetch('http://localhost:5000/api/interviewer/candidates', {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  return response.json();
};

// Schedule assessment
const scheduleAssessment = async (candidateId, token, scheduledTime) => {
  const response = await fetch(
    `http://localhost:5000/api/interviewer/candidates/${candidateId}/schedule`,
    {
      method: 'POST',
      headers: { 
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ 
        scheduled_time: scheduledTime 
      })
    }
  );
  return response.json();
};

// Make final decision
const makeFinalDecision = async (assessmentId, token, decision, rationale) => {
  const response = await fetch(
    `http://localhost:5000/api/interviewer/assessments/${assessmentId}/final-decision`,
    {
      method: 'POST',
      headers: { 
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ 
        decision: decision,
        rationale: rationale
      })
    }
  );
  return response.json();
};
```

---

## Rate Limiting

Currently no rate limiting is implemented. For production deployment, consider:
- 100 requests per minute per IP
- 1000 requests per hour per authenticated user
- Implement using Flask-Limiter

---

## Security Considerations

1. **Token Security:** Tokens expire after 24 hours
2. **Role-Based Access Control:** Only `interviewer` role can access dashboard
3. **Email Verification:** All email recipients must be valid candidates
4. **Data Encryption:** Sensitive data encrypted in database (future)
5. **Audit Logging:** All decisions logged with timestamp and user ID

---

## Environment Variables Required

For production deployment, ensure these are set:
```bash
FLASK_ENV=production
JWT_SECRET_KEY=your-secret-key
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-app-password
DATABASE_URL=postgresql://user:password@localhost/dbname
```

---

## Support & Troubleshooting

**Candidate not appearing in list:**
- Ensure resume was uploaded via `/api/resume/upload`
- Check candidate status in database

**Email not sending:**
- Verify SMTP configuration
- Check SMTP_USER and SMTP_PASS environment variables
- See EMAIL_SERVICE_GUIDE.md for detailed troubleshooting

**Authentication failures:**
- Token may have expired (24-hour expiration)
- User role must be "interviewer" in database
- Verify JWT_SECRET_KEY is set correctly

**Assessment link not working:**
- Assessment must be scheduled first
- Check if scheduled_assessment_id exists in database
- Verify frontend assessment page at `/assessment/:id` is implemented

---

## Next Steps

1. **Task A9:** Implement assessment time validation (±30 minute window)
2. **Frontend:** Build Interviewer Dashboard UI (Shaivi's task S5)
3. **Testing:** Create integration tests for all endpoints
4. **Documentation:** Add API endpoint testing guide

---

*Last Updated: January 21, 2026*
*Version: 1.0*
