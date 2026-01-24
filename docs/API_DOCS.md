# API Documentation

## Base URL
**Backend Server:** `http://localhost:5000`

---

## Authentication Endpoints

### 1. Register User
Create a new user account (for interviewers or admins).

**Endpoint:** `POST /api/auth/register`

**Request Body:**
```json
{
  "email": "interviewer@example.com",
  "password": "secure123456",
  "role": "interviewer",
  "name": "Jane Doe"
}
```

**Validation Rules:**
- `email`: Required, must be valid email format
- `password`: Required, minimum 8 characters
- `role`: Required, must be "interviewer" or "admin"
- `name`: Required, minimum 2 characters

**Success Response (201):**
```json
{
  "status": "success",
  "message": "User registered successfully",
  "data": {
    "user_id": 1,
    "email": "interviewer@example.com",
    "role": "interviewer",
    "name": "Jane Doe"
  }
}
```

**Error Responses:**
- `400`: Missing fields or validation error
- `409`: Email already exists
- `500`: Server error

---

### 2. Login
Authenticate user and receive JWT token.

**Endpoint:** `POST /api/auth/login`

**Request Body:**
```json
{
  "email": "interviewer@example.com",
  "password": "secure123456"
}
```

**Success Response (200):**
```json
{
  "status": "success",
  "message": "Login successful",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
      "id": 1,
      "email": "interviewer@example.com",
      "role": "interviewer",
      "name": "Jane Doe"
    }
  }
}
```

**Error Responses:**
- `400`: Missing email or password
- `401`: Invalid credentials
- `500`: Server error

**Note:** Store the `access_token` in localStorage or cookies. Include it in subsequent requests as:
```
Authorization: Bearer <access_token>
```

---

### 3. Get Current User
Get information about the currently authenticated user.

**Endpoint:** `GET /api/auth/me`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Success Response (200):**
```json
{
  "status": "success",
  "data": {
    "id": 1,
    "email": "interviewer@example.com",
    "role": "interviewer",
    "name": "Jane Doe",
    "created_at": "2026-01-21 10:30:00"
  }
}
```

**Error Responses:**
- `401`: Missing or invalid token
- `404`: User not found
- `500`: Server error

---

### 4. Verify Token
Verify if JWT token is valid.

**Endpoint:** `GET /api/auth/verify`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Success Response (200):**
```json
{
  "status": "success",
  "message": "Token is valid",
  "data": {
    "user_id": 1,
    "role": "interviewer",
    "name": "Jane Doe"
  }
}
```

**Error Responses:**
- `401`: Invalid or expired token

---

## Resume Upload

### 5. Upload Resume (With AI Analysis)
Upload and analyze a candidate's resume with AI-powered insights.

**Endpoint:** `POST /api/resume/upload`

**Content-Type:** `multipart/form-data`

**Form Data:**
- `file`: PDF or DOCX resume file (required)
- `name`: Candidate's full name (required)
- `email`: Candidate's email address (required)
- `phone`: Phone number (optional)

**Success Response (201):**
```json
{
  "status": "success",
  "message": "Resume uploaded and analyzed successfully",
  "data": {
    "candidate_id": 1,
    "file_path": "uploads/abc123_resume.pdf",
    "original_filename": "resume.pdf",
    "candidate": {
      "name": "John Doe",
      "email": "john@example.com",
      "phone": "1234567890"
    },
    "parsed_data": {
      "skills": ["Python", "JavaScript", "React", "AWS", "Docker"],
      "experience": 5,
      "education": "Bachelor of Science in Computer Science",
      "match_score": 82
    },
    "ai_analysis": {
      "pros": [
        "Strong full-stack expertise with 5 years proven experience",
        "Solid alignment with core tech stack (Python, React, AWS)",
        "Leadership experience managing team of 4 developers"
      ],
      "cons": [
        "Limited experience with containerization tools",
        "No cloud certifications mentioned"
      ],
      "overall_assessment": "Strong candidate with excellent technical skills and relevant experience. Minor gaps in DevOps can be addressed.",
      "recommendation": "Strong Match",
      "confidence_score": 88,
      "enhanced_match_score": 85,
      "key_highlights": [
        "5 years of full-stack development",
        "Built scalable microservices"
      ],
      "areas_for_improvement": [
        "Container orchestration skills",
        "Cloud certifications"
      ]
    }
  }
}
```

**AI Analysis Fields:**
- `pros`: Array of 3-5 strengths
- `cons`: Array of 2-4 areas for improvement
- `overall_assessment`: Comprehensive summary
- `recommendation`: "Strong Match" | "Good Match" | "Moderate Match" | "Weak Match"
- `confidence_score`: AI's confidence in assessment (0-100)
- `enhanced_match_score`: AI-enhanced match score (0-100)
- `key_highlights`: Most impressive qualifications
- `areas_for_improvement`: Specific skill gaps

**Error Responses:**
- `400`: Missing required fields or invalid file type
- `413`: File too large (max 10MB)
- `500`: Server error

**Notes:**
- AI analysis requires OpenAI API key to be configured
- If AI fails, fallback analysis is provided
- Pros/cons are stored in database for recruiter dashboard
}
```

---

## Interviewer Dashboard

### Get All Candidates
```
GET /api/interviewer/candidates
```
**Headers:** `Authorization: Bearer <jwt_token>`

**Response:**
```json
{
  "candidates": [
    {
      "id": 1,
      "name": "John Doe",
      "email": "john@example.com",
      "match_score": 85,
      "pros": "Strong technical skills",
      "cons": "Limited experience",
      "status": "pending", // pending, rejected, scheduled, completed, hired
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

### Reject Candidate
```
POST /api/interviewer/reject
```
**Headers:** `Authorization: Bearer <jwt_token>`

**Body:**
```json
{
  "candidate_id": 1,
  "reason": "Skills do not match requirements"
}
```
**Response:**
```json
{
  "message": "Candidate rejected",
  "email_sent": true
}
```

### Schedule Assessment
```
POST /api/interviewer/schedule
```
**Headers:** `Authorization: Bearer <jwt_token>`

**Body:**
```json
{
  "candidate_id": 1,
  "scheduled_time": "2024-01-20T14:00:00Z"
}
```
**Response:**
```json
{
  "message": "Assessment scheduled",
  "scheduled_assessment_id": 1,
  "email_sent": true
}
```

### Get Assessment Results
```
GET /api/interviewer/assessment-results/:assessment_id
```
**Headers:** `Authorization: Bearer <jwt_token>`

**Response:**
```json
{
  "assessment_id": 1,
  "candidate_id": 1,
  "scores": {
    "mcq": 66.67,
    "coding": 66.67,
    "technical_overall": 66.67,
    "psychometric": 80.00,
    "overall": 70.67
  },
  "decision": "Proceed",
  "rationale": "Strong technical foundation with good problem-solving abilities",
  "hiring_recommendation": "Recommended for hire based on performance"
}
```

### Make Final Decision
```
POST /api/interviewer/final-decision
```
**Headers:** `Authorization: Bearer <jwt_token>`

**Body:**
```json
{
  "candidate_id": 1,
  "decision": "hire", // or "no_hire"
  "notes": "Excellent candidate, start ASAP"
}
```
**Response:**
```json
{
  "message": "Decision recorded",
  "email_sent": true
}
```

---

## Interviewee Assessment

### Check My Assessment
```
GET /api/interviewee/my-assessment/:candidate_id
```
**Response:**
```json
{
  "status": "scheduled",
  "scheduled_time": "2024-01-20T14:00:00Z",
  "can_start": true, // true if within ±30 mins of scheduled_time
  "message": "You can start your assessment now"
}
```

---

## Assessment System

### Health Check
```
GET /api/health
```
**Response:**
```json
{
  "status": "ok"
}
```

### Start Assessment
```
POST /api/assessment/start
```
**Body:**
```json
{
  "candidate_id": 1
}
```
**Response:**
```json
{
  "assessment_id": 1,
  "mcq_questions": [
    {
      "id": 1,
      "question": "What is the time complexity of binary search?",
      "options": ["O(n)", "O(log n)", "O(n²)", "O(1)"],
      "correct_answer": 1
    }
    // ... 9 more questions
  ],
  "coding_problem": {
    "id": 1,
    "title": "Two Sum",
    "description": "Given an array of integers...",
    "test_cases": [
      {"input": "[2,7,11,15], target=9", "expected": "[0,1]"}
    ]
  },
  "psychometric_scenarios": [
    {
      "id": 1,
      "scenario": "You're facing a tight deadline...",
      "traits": ["leadership", "stress_management"]
    }
    // ... 2 more scenarios
  ]
}
```

### Submit MCQ Answer
```
POST /api/assessment/mcq/submit
```
**Body:**
```json
{
  "assessment_id": 1,
  "question_id": 1,
  "answer": 1,
  "time_taken": 30
}
```
**Response:**
```json
{
  "is_correct": true,
  "correct_answer": 1
}
```

### Submit Code Solution
```
POST /api/assessment/code/submit
```
**Body:**
```json
{
  "assessment_id": 1,
  "problem_id": 1,
  "code": "def twoSum(nums, target):\n    ...",
  "language": "python"
}
```
**Response:**
```json
{
  "test_results": [
    {"input": "[2,7,11,15], 9", "expected": "[0,1]", "actual": "[0,1]", "passed": true}
  ],
  "passed_count": 3,
  "total_count": 3,
  "score": 100
}
```

### Submit Psychometric Response
```
POST /api/assessment/psychometric/submit
```
**Body:**
```json
{
  "assessment_id": 1,
  "scenario_id": 1,
  "trait_scores": {
    "leadership": 8,
    "stress_management": 7
  },
  "response_text": "I would prioritize tasks and delegate..."
}
```
**Response:**
```json
{
  "message": "Psychometric response saved successfully"
}
```

### Complete Assessment
```
POST /api/assessment/complete
```
**Body:**
```json
{
  "assessment_id": 1
}
```
**Response:**
```json
{
  "assessment_id": 1,
  "scores": {
    "mcq_score": 66.67,
    "coding_score": 66.67,
    "technical_score": 66.67,
    "psychometric_score": 80.00,
    "overall_score": 70.67
  },
  "decision": "Proceed",
  "rationale": "Demonstrates solid technical understanding with strong problem-solving abilities. Psychometric assessment shows good leadership potential and stress management skills."
}
```

---

## Email Service (Internal)

### Send Email
```
POST /api/email/send (Internal use only)
```
**Body:**
```json
{
  "recipient": "candidate@example.com",
  "email_type": "rejection", // rejection, invitation, decision
  "data": {
    "candidate_name": "John Doe",
    "reason": "Skills do not match requirements"
  }
}
```

---

## Interviewer Dashboard Endpoints

Complete endpoints for managing candidates, scheduling assessments, and making hiring decisions.

**Base URL:** `http://localhost:5000/api/interviewer`

**Authentication:** All endpoints require JWT token with `interviewer` role.

### 1. Get All Candidates
**Endpoint:** `GET /api/interviewer/candidates`

List all candidates with resume analysis, AI insights, and current status.

**Query Parameters:**
- `status`: Filter by candidate status (pending, under_review, rejected, hired)
- `sort`: Sort by (name, date, match_score)
- `order`: Sort direction (asc, desc)

**Success Response (200):**
```json
{
  "status": "success",
  "data": [
    {
      "id": 1,
      "name": "John Doe",
      "email": "john@example.com",
      "status": "pending",
      "match_score": 85.5,
      "pros": ["5+ years Python", "Strong system design"],
      "cons": ["Limited AWS"],
      "recommendation": "Good candidate for mid-level role",
      "enhanced_match_score": 82.3,
      "created_at": "2026-01-20T10:30:00"
    }
  ],
  "total": 1
}
```

### 2. Get Candidate Details
**Endpoint:** `GET /api/interviewer/candidates/:candidate_id`

Get detailed information for a specific candidate.

**Success Response (200):**
```json
{
  "status": "success",
  "data": {
    "id": 1,
    "name": "John Doe",
    "email": "john@example.com",
    "status": "pending",
    "match_score": 85.5,
    "pros": ["5+ years Python"],
    "cons": ["Limited AWS"],
    "recommendation": "Good candidate",
    "assessment": null
  }
}
```

### 3. Reject Candidate
**Endpoint:** `POST /api/interviewer/candidates/:candidate_id/reject`

Reject a candidate after resume review. Sends rejection email automatically.

**Request Body:**
```json
{
  "reason": "Experience doesn't align with requirements"
}
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

### 4. Schedule Assessment
**Endpoint:** `POST /api/interviewer/candidates/:candidate_id/schedule`

Schedule an assessment for a candidate. Sends invitation email with assessment link.

**Request Body:**
```json
{
  "scheduled_time": "2026-02-01T14:00:00",
  "additional_info": "Complete by February 3rd"
}
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

### 5. Get Assessment Results
**Endpoint:** `GET /api/interviewer/assessments/:candidate_id`

Retrieve assessment results and scores for a candidate.

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
    "ai_recommendation": "Strong technical fundamentals",
    "completed_at": "2026-01-21T15:45:00"
  }
}
```

### 6. Make Final Decision
**Endpoint:** `POST /api/interviewer/assessments/:assessment_id/final-decision`

Record final hiring decision (hire or no-hire) after assessment completion.

**Request Body:**
```json
{
  "decision": "hire",
  "rationale": "Excellent technical skills and cultural fit",
  "next_steps": "Please confirm your availability for HR discussion"
}
```

**Decision Options:**
- `"hire"`, `"hired"`, or `"selected"` - Offer the position
- `"no-hire"` - Reject after assessment

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

### 7. Get Dashboard Statistics
**Endpoint:** `GET /api/interviewer/dashboard/stats`

Get dashboard statistics showing candidate pipeline metrics.

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

### 8. Manage Candidate Notes
**Endpoint:** `GET /POST /api/interviewer/candidates/:candidate_id/notes`

Add or retrieve notes for a candidate (future implementation).

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

## Interviewee Assessment Endpoints

Candidate-side assessment endpoints with time validation.

**Base URL:** `http://localhost:5000/api/interviewee`

### 1. Get My Assessment Info
**Endpoint:** `GET /api/interviewee/my-assessment/:candidate_id`

Get assessment scheduling information and check if you can start.

**Success Response (200):**
```json
{
  "status": "success",
  "data": {
    "candidate_id": 1,
    "candidate_name": "John Doe",
    "scheduled_time": "2026-02-01T14:00:00",
    "window_minutes": 30,
    "current_time": "2026-02-01T13:55:00Z",
    "minutes_until_start": 5,
    "can_start": false,
    "message": "Assessment is 5 minutes away from scheduled time",
    "status": "scheduled"
  }
}
```

### 2. Start Assessment (With Time Validation)
**Endpoint:** `POST /api/interviewee/assessment/start/:candidate_id`

Start assessment. Returns 403 if outside ±30 minute window.

**Time Validation:**
- Window opens: 30 minutes before scheduled time
- Window closes: 30 minutes after scheduled time
- Outside window: Returns 403 Forbidden

**Success Response (201):**
```json
{
  "status": "success",
  "message": "Assessment started successfully",
  "data": {
    "assessment_id": 42,
    "candidate_id": 1,
    "scheduled_time": "2026-02-01T14:00:00",
    "mcq_questions": [...],
    "coding_problem": {...},
    "psychometric_scenarios": [...]
  }
}
```

**Error Response (403 - Outside Window):**
```json
{
  "status": "error",
  "message": "Assessment not available yet. Assessment is 45 minutes away from scheduled time",
  "data": {
    "scheduled_time": "2026-02-01T14:00:00",
    "current_time": "2026-02-01T13:15:00Z",
    "minutes_away": 45,
    "allowed_window": 30
  }
}
```

### 3. Complete Assessment
**Endpoint:** `POST /api/interviewee/assessment/:assessment_id/complete`

Complete assessment and receive scores with AI recommendation.

**Success Response (200):**
```json
{
  "status": "success",
  "message": "Assessment completed successfully",
  "data": {
    "assessment_id": 42,
    "candidate_id": 1,
    "scores": {
      "mcq": 75.0,
      "coding": 80.0,
      "technical": 76.0,
      "psychometric": 82.0,
      "overall": 77.2
    },
    "psychometric_breakdown": {
      "leadership": 8.5,
      "communication": 8.0,
      "decision_making": 8.5
    },
    "decision": "Recommend for Hire",
    "rationale": "Strong technical and soft skills demonstrated",
    "ai_recommendation": "Proceed to HR discussion"
  }
}
```

---

All endpoints may return error responses in the following format:

```json
{
  "error": "Error message description",
  "status": 400
}
```

**Common HTTP Status Codes:**
- `200` - Success
- `201` - Created
- `400` - Bad Request (invalid input)
- `401` - Unauthorized (missing or invalid JWT)
- `403` - Forbidden (insufficient permissions or outside assessment time window)
