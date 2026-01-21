# Interviewer Dashboard - Quick Start Guide

Fast reference for using the Interviewer Dashboard API endpoints.

## Quick Setup

1. **Get JWT Token:**
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "interviewer@example.com",
    "password": "secure123456"
  }'
```

Response includes `access_token`. Use in all requests:
```bash
-H "Authorization: Bearer YOUR_TOKEN_HERE"
```

---

## Common Operations

### 1. View All Candidates

```bash
# Get all pending candidates, sorted by match score
curl -X GET "http://localhost:5000/api/interviewer/candidates?status=pending&sort=match_score&order=desc" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response Includes:**
- Candidate name, email, phone
- AI match score (0-100)
- AI-generated pros and cons list
- Current status (pending, under_review, hired, rejected)

---

### 2. Review Candidate Details

```bash
curl -X GET "http://localhost:5000/api/interviewer/candidates/1" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Shows everything including assessment status if already scheduled.

---

### 3. Reject a Candidate

```bash
curl -X POST "http://localhost:5000/api/interviewer/candidates/1/reject" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "Limited experience in required technologies"
  }'
```

✉️ **Automatic Email Sent:** Professional rejection email to candidate

---

### 4. Schedule Assessment

```bash
curl -X POST "http://localhost:5000/api/interviewer/candidates/1/schedule" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "scheduled_time": "2026-02-01T14:00:00",
    "additional_info": "Please complete by Feb 3rd. Use Chrome browser for best experience."
  }'
```

✉️ **Automatic Email Sent:** 
- Assessment invitation with unique link
- Scheduled time
- Instructions and requirements
- Your name as interviewer

---

### 5. View Assessment Results

After candidate completes assessment:

```bash
curl -X GET "http://localhost:5000/api/interviewer/assessments/1" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Shows:**
- Technical score (0-100)
- Psychometric score (0-100)
- MCQ and coding scores
- AI hiring recommendation
- Assessment completion time

---

### 6. Make Final Decision

```bash
curl -X POST "http://localhost:5000/api/interviewer/assessments/15/final-decision" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "decision": "hire",
    "rationale": "Excellent technical skills, great cultural fit, strong problem-solving",
    "next_steps": "Please confirm your availability for contract discussion by tomorrow"
  }'
```

✉️ **Automatic Email Sent:**
- Hire/No-Hire decision
- Scores breakdown
- Rationale
- Next steps

---

### 7. View Dashboard Statistics

```bash
curl -X GET "http://localhost:5000/api/interviewer/dashboard/stats" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Shows:**
- Total candidates
- Count by status (pending, under_review, hired, rejected)
- Average match score

---

## JavaScript Frontend Examples

### Using Fetch API

```javascript
const TOKEN = localStorage.getItem('token');

// 1. Get all candidates
async function getCandidates() {
  const res = await fetch('http://localhost:5000/api/interviewer/candidates', {
    headers: { 'Authorization': `Bearer ${TOKEN}` }
  });
  return res.json();
}

// 2. Reject candidate
async function rejectCandidate(candidateId, reason) {
  const res = await fetch(
    `http://localhost:5000/api/interviewer/candidates/${candidateId}/reject`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${TOKEN}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ reason })
    }
  );
  return res.json();
}

// 3. Schedule assessment
async function scheduleAssessment(candidateId, scheduledTime, info) {
  const res = await fetch(
    `http://localhost:5000/api/interviewer/candidates/${candidateId}/schedule`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${TOKEN}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        scheduled_time: scheduledTime,
        additional_info: info
      })
    }
  );
  return res.json();
}

// 4. View assessment results
async function getAssessmentResults(candidateId) {
  const res = await fetch(
    `http://localhost:5000/api/interviewer/assessments/${candidateId}`,
    { headers: { 'Authorization': `Bearer ${TOKEN}` } }
  );
  return res.json();
}

// 5. Make final decision
async function makeFinalDecision(assessmentId, decision, rationale) {
  const res = await fetch(
    `http://localhost:5000/api/interviewer/assessments/${assessmentId}/final-decision`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${TOKEN}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        decision,
        rationale
      })
    }
  );
  return res.json();
}

// 6. Get dashboard stats
async function getDashboardStats() {
  const res = await fetch(
    'http://localhost:5000/api/interviewer/dashboard/stats',
    { headers: { 'Authorization': `Bearer ${TOKEN}` } }
  );
  return res.json();
}
```

---

## Response Status Codes

| Code | Meaning | Example |
|------|---------|---------|
| 200 | Success | Candidate retrieved, assessment completed |
| 201 | Created | Assessment scheduled, new resource created |
| 400 | Bad Request | Missing required field |
| 403 | Forbidden | User is not an interviewer |
| 404 | Not Found | Candidate/Assessment doesn't exist |
| 500 | Server Error | Unexpected error (check backend logs) |

---

## Workflow Example

**Typical hiring flow:**

1. **Morning:** Check pending candidates
```javascript
const candidates = await getCandidates();
// Review: John Doe (85% match), Jane Smith (92% match)
```

2. **10:00 AM:** Schedule assessment for top candidate
```javascript
await scheduleAssessment(1, '2026-02-01T14:00:00', 'Video interview via Google Meet');
// Jane receives email with assessment link
```

3. **3:00 PM:** Check if assessment completed
```javascript
const results = await getAssessmentResults(1);
// Technical: 78.5, Psychometric: 82.0, AI Recommendation: "Hire"
```

4. **3:15 PM:** Make final decision
```javascript
await makeFinalDecision(15, 'hire', 'Excellent technical skills');
// Jane receives hire decision email
```

---

## Troubleshooting

**"Access denied. Interviewer role required."**
- Your user account must have role = "interviewer" in database
- Token must include role claim

**"Candidate not found"**
- Candidate ID doesn't exist
- Verify resume was uploaded successfully
- Check candidate ID in database

**"Email not sent"**
- SMTP configuration may be missing
- Check SMTP_HOST, SMTP_USER, SMTP_PASS environment variables
- Verify email address is valid

**Token expired (401)**
- Get new token: `POST /api/auth/login`
- Tokens expire after 24 hours

---

## Next Steps

1. Build interviewer dashboard UI with React
2. Implement assessment time validation (±30 min window)
3. Add candidate notes/comments feature
4. Setup end-to-end testing

For detailed documentation, see: [INTERVIEWER_DASHBOARD_GUIDE.md](INTERVIEWER_DASHBOARD_GUIDE.md)

---

*Last Updated: January 21, 2026*
