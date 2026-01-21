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
  }
}
```

### Get Current User
```
GET /api/auth/me
```
**Headers:** `Authorization: Bearer <jwt_token>`

**Response:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "name": "John Doe",
  "role": "interviewer"
}
```

---

## Resume Management

### Upload Resume
```
POST /api/resume/upload
```
**Body (multipart/form-data):**
- `file`: PDF or DOCX file
- `name`: Candidate name
- `email`: Candidate email
- `phone`: Phone number (optional)

**Response:**
```json
{
  "candidate_id": 1,
  "parsed_data": {
    "skills": ["Python", "JavaScript", "React"],
    "experience_years": 3,
    "education": "Bachelor's in Computer Science",
    "match_score": 85,
    "pros": "Strong technical skills, relevant experience",
    "cons": "Limited leadership experience"
  },
  "file_path": "/uploads/resume_123.pdf"
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

## Error Responses

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
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `500` - Internal Server Error
