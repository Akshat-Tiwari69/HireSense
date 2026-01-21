# Assessment Time Validation - Complete Guide

Comprehensive documentation for the Assessment Time Validation system (Task A9).

## Overview

The Assessment Time Validation system ensures that candidates can only start and complete assessments within a scheduled time window of **±30 minutes** from their scheduled assessment time. This is critical for:

- **Fairness:** All candidates get equal assessment conditions
- **Proctoring:** Prevents unauthorized assessment attempts
- **Integrity:** Ensures assessments happen at scheduled times
- **Compliance:** Maintains audit trail for hiring process

---

## How It Works

### **Assessment Scheduling Flow**

```
1. Interviewer schedules assessment
   POST /api/interviewer/candidates/:id/schedule
   ↓
2. Database creates scheduled_assessment record
   - scheduled_time: ISO format datetime
   - status: 'scheduled'
   - window: ±30 minutes
   ↓
3. Candidate receives invitation email
   - Assessment link
   - Scheduled date/time
   - Instructions
   ↓
4. Candidate attempts to start assessment
   POST /api/interviewee/assessment/start/:candidate_id
   ↓
5. System validates time
   - Check ±30 minute window
   - If valid: Return questions ✅
   - If invalid: Return 403 Forbidden ❌
```

---

## Endpoints

### **1. Get My Assessment Info**

**Endpoint:** `GET /api/interviewee/my-assessment/:candidate_id`

**Description:** Get assessment scheduling and status information. Use to check if you can start the assessment.

**Example Request:**
```bash
curl -X GET "http://localhost:5000/api/interviewee/my-assessment/1"
```

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
    "status": "scheduled",
    "assessment_id": null
  }
}
```

**Error Response (404):**
```json
{
  "status": "error",
  "message": "No assessment scheduled yet"
}
```

---

### **2. Start Assessment (With Time Validation)**

**Endpoint:** `POST /api/interviewee/assessment/start/:candidate_id`

**Description:** Start assessment with automatic time window validation. Returns 403 if outside the ±30 minute window.

**Time Validation Logic:**
- If current time is between `scheduled_time - 30 min` and `scheduled_time + 30 min`: ✅ Start assessment
- If current time is outside window: ❌ Return 403 Forbidden
- Assessment link shows in candidate dashboard while within window

**Example Requests:**

**Valid Time (Within Window):**
```bash
curl -X POST "http://localhost:5000/api/interviewee/assessment/start/1" \
  -H "Content-Type: application/json"
```

**Success Response (201):**
```json
{
  "status": "success",
  "message": "Assessment started successfully",
  "data": {
    "assessment_id": 42,
    "candidate_id": 1,
    "scheduled_time": "2026-02-01T14:00:00",
    "mcq_questions": [
      {
        "id": 1,
        "question": "What is the time complexity of quicksort?",
        "options": ["O(n)", "O(n log n)", "O(n²)", "O(2^n)"],
        "time_limit": 30,
        "category": "Algorithms",
        "difficulty": "medium"
      }
    ],
    "coding_problem": {
      "id": 5,
      "title": "Two Sum",
      "description": "Given an array of integers...",
      "example": "Input: [2,7,11,15], target=9\nOutput: [0,1]",
      "difficulty": "easy"
    },
    "psychometric_scenarios": [
      {
        "id": 1,
        "scenario": "You missed a deadline...",
        "traits": ["decision_making", "communication"]
      }
    ]
  }
}
```

**Invalid Time (Outside Window):**
```bash
# Try to start 45 minutes before scheduled time
curl -X POST "http://localhost:5000/api/interviewee/assessment/start/1" \
  -H "Content-Type: application/json"
```

**Error Response (403):**
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

**Resume In-Progress Assessment:**
If assessment was started and is in progress:
```json
{
  "status": "success",
  "message": "Assessment resumed",
  "data": {
    "assessment_id": 42,
    "resumed": true,
    "mcq_questions": [...],
    "coding_problem": {...},
    "psychometric_scenarios": [...]
  }
}
```

---

### **3. Complete Assessment**

**Endpoint:** `POST /api/interviewee/assessment/:assessment_id/complete`

**Description:** Submit final assessment and receive AI-powered hiring recommendation.

**Example Request:**
```bash
curl -X POST "http://localhost:5000/api/interviewee/assessment/42/complete" \
  -H "Content-Type: application/json"
```

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
    "rationale": "Strong technical and soft skills demonstrated. Candidate shows excellent problem-solving ability and communication.",
    "ai_recommendation": "Proceed to HR discussion"
  }
}
```

---

## Time Validation Details

### **Window Calculation**

```
Scheduled Time: 2026-02-01 14:00:00
Early Window:   2026-02-01 13:30:00 (30 min before)
Late Window:    2026-02-01 14:30:00 (30 min after)

✅ Valid Times:
  - 13:30:00 to 14:30:00 (60-minute window)

❌ Invalid Times:
  - Before 13:30:00
  - After 14:30:00
```

### **Implementation in db_helpers.py**

```python
def check_assessment_time_valid(candidate_id, current_time, window_minutes=30):
    """
    Check if current time is within valid assessment window
    
    Returns:
        (is_valid, scheduled_time, message)
    """
    # Fetches scheduled time from database
    # Calculates time difference
    # Returns True if within ±30 minutes
```

### **Time Zone Handling**

- All times stored as ISO 8601 format with UTC (Z) suffix
- Example: `2026-02-01T14:00:00Z`
- Frontend should convert to local time for display only
- Backend always validates using UTC

---

## Database Updates

### **scheduled_assessments Table**

```sql
CREATE TABLE scheduled_assessments (
    id INTEGER PRIMARY KEY,
    candidate_id INTEGER NOT NULL,
    interviewer_id INTEGER NOT NULL,
    scheduled_time TEXT NOT NULL,  -- ISO format with ±30 min window
    status TEXT DEFAULT 'scheduled',  -- scheduled, in_progress, completed, cancelled
    assessment_id INTEGER,  -- Linked after assessment starts
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    FOREIGN KEY (candidate_id) REFERENCES candidates(id),
    FOREIGN KEY (interviewer_id) REFERENCES users(id),
    FOREIGN KEY (assessment_id) REFERENCES assessments(id)
);
```

**Status Flow:**
```
scheduled → in_progress → completed
       ↘
         cancelled
```

---

## Frontend Integration

### **Candidate Dashboard**

**Step 1: Check Assessment Status**
```javascript
// When candidate visits dashboard
const response = await fetch(`/api/interviewee/my-assessment/${candidateId}`);
const data = await response.json();

if (data.data.can_start) {
  // Show "Start Assessment" button
  renderStartButton();
} else {
  // Show message with time until start
  showMessage(`Assessment available in ${data.data.minutes_until_start} minutes`);
}
```

**Step 2: Start Assessment**
```javascript
const startResponse = await fetch(`/api/interviewee/assessment/start/${candidateId}`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' }
});

if (startResponse.status === 403) {
  const error = await startResponse.json();
  alert(`Cannot start now. ${error.message}`);
  // Show "Try Again" button
} else {
  // Load assessment UI with questions
  const assessment = await startResponse.json();
  loadAssessmentUI(assessment.data);
}
```

**Step 3: Complete Assessment**
```javascript
// When candidate submits final answers
const completeResponse = await fetch(`/api/interviewee/assessment/${assessmentId}/complete`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' }
});

const result = await completeResponse.json();
showResults({
  scores: result.data.scores,
  decision: result.data.decision,
  message: "We'll notify you of the hiring decision within 24 hours"
});
```

---

## Error Scenarios

### **Scenario 1: Too Early**
```
Scheduled: 14:00
Current:   13:15 (45 minutes early)
Result:    403 Forbidden
Message:   "Assessment is 45 minutes away from scheduled time"
```

### **Scenario 2: Too Late**
```
Scheduled: 14:00
Current:   14:45 (45 minutes late)
Result:    403 Forbidden
Message:   "Assessment is 45 minutes away from scheduled time"
```

### **Scenario 3: Perfect Timing**
```
Scheduled: 14:00
Current:   14:05 (5 minutes into window)
Result:    201 Created - Assessment starts
```

### **Scenario 4: No Scheduled Assessment**
```
Scheduled: (none)
Current:   any time
Result:    404 Not Found
Message:   "No assessment scheduled yet. Please contact your recruiter."
```

---

## Security Features

### **Time-Based Access Control**
- Only allows assessment attempts within scheduled window
- Prevents early or late attempts
- Acts as a form of "soft proctoring"

### **Audit Trail**
- All attempts logged in scheduled_assessments table
- Status transitions tracked with timestamps
- Enables post-assessment verification

### **Rate Limiting** (Future)
- Limit assessment start attempts to prevent brute force
- Log suspicious patterns (repeated attempts outside window)

---

## Configuration

### **Time Window**

Currently hardcoded to **30 minutes**:
```python
check_assessment_time_valid(
    candidate_id=candidate_id,
    current_time=current_time,
    window_minutes=30  # Can be configured
)
```

To change window:
```python
# In interviewee_routes.py, change:
window_minutes=30  # to 45 or any value
```

### **Environment Setup**

No additional environment variables required. Uses existing:
- `FLASK_ENV` - Flask environment
- Database connection (already configured)

---

## API Endpoints Summary

| Method | Endpoint | Purpose | Auth | Time Check |
|--------|----------|---------|------|-----------|
| GET | `/api/interviewee/my-assessment/:id` | View scheduled info | None | No |
| POST | `/api/interviewee/assessment/start/:id` | Start assessment | None | **YES** ✅ |
| POST | `/api/interviewee/assessment/:id/complete` | Complete assessment | None | No |

---

## Database Helper Functions

### **`check_assessment_time_valid(candidate_id, current_time, window_minutes=30)`**

```python
# Check if assessment can be started
is_valid, scheduled_time, message = check_assessment_time_valid(
    candidate_id=1,
    current_time="2026-02-01T14:05:00Z",
    window_minutes=30
)

# is_valid: True/False
# scheduled_time: "2026-02-01T14:00:00Z"
# message: "Assessment is within 30 minute window"
```

### **`update_scheduled_assessment_status(scheduled_assessment_id, status, assessment_id=None)`**

```python
# Update status when assessment starts
update_scheduled_assessment_status(
    scheduled_assessment_id=1,
    status='in_progress',
    assessment_id=42
)

# Update status when assessment completes
update_scheduled_assessment_status(
    scheduled_assessment_id=1,
    status='completed',
    assessment_id=42
)
```

---

## Testing Guide

### **Test Case 1: Valid Start Time**
1. Schedule assessment for current time + 5 minutes
2. Wait 5 minutes
3. Call `/api/interviewee/assessment/start/:id`
4. **Expected:** 201 Created with questions

### **Test Case 2: Too Early**
1. Schedule assessment for current time + 45 minutes
2. Immediately call `/api/interviewee/assessment/start/:id`
3. **Expected:** 403 Forbidden with time message

### **Test Case 3: Too Late**
1. Schedule assessment for current time - 45 minutes
2. Call `/api/interviewee/assessment/start/:id`
3. **Expected:** 403 Forbidden with time message

### **Test Case 4: Resume In Progress**
1. Start assessment (within window)
2. Call `/api/interviewee/assessment/start/:id` again
3. **Expected:** 200 OK with `resumed: true`

### **Test Case 5: Complete Assessment**
1. Start assessment and answer all questions
2. Call `/api/interviewee/assessment/:id/complete`
3. **Expected:** 200 OK with scores and recommendation

---

## Workflow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│  INTERVIEWER SCHEDULES ASSESSMENT                           │
│  POST /api/interviewer/candidates/:id/schedule              │
│  scheduled_time: "2026-02-01T14:00:00Z"                     │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  CANDIDATE RECEIVES EMAIL                                   │
│  - Assessment link                                          │
│  - Scheduled time: 14:00                                    │
│  - Time window: 13:30-14:30                                │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  CANDIDATE ATTEMPTS TO START                                │
│  POST /api/interviewee/assessment/start/:candidate_id       │
└──────────────────────┬──────────────────────────────────────┘
                       │
            ┌──────────┴──────────┐
            │                     │
            ▼                     ▼
    ✅ WITHIN WINDOW      ❌ OUTSIDE WINDOW
    (13:30-14:30)         (<13:30 or >14:30)
            │                     │
            ▼                     ▼
    201 Created          403 Forbidden
    - assessment_id      - message
    - mcq_questions      - minutes_away
    - coding_problem
    - psychometric       User sees:
                         "Assessment not available
                          45 minutes away"
            │
            ▼
    CANDIDATE TAKES ASSESSMENT
    - Submit MCQ answers
    - Submit coding solution
    - Answer psychometric scenarios
            │
            ▼
    POST /api/interviewee/assessment/:id/complete
            │
            ▼
    200 OK with:
    - Scores (technical, psychometric, overall)
    - Decision (Hire/Consider/Not Recommended)
    - AI Recommendation
```

---

## Frequently Asked Questions

**Q: What if my computer clock is wrong?**
A: The server time is the authority. Adjust your system clock before the scheduled time.

**Q: Can I take the assessment early?**
A: No, you must wait until the scheduled time. The window opens 30 minutes before.

**Q: Can I take the assessment late?**
A: No, the window closes 30 minutes after scheduled time. Contact your recruiter if you miss the window.

**Q: What if I start but don't finish?**
A: The assessment will resume from where you left off if you return within the window.

**Q: What happens after the window closes?**
A: You cannot start or resume. Your recruiter must schedule a new assessment.

---

## Performance Considerations

### **Database Queries**
- `check_assessment_time_valid`: Single indexed query
- `update_scheduled_assessment_status`: Simple UPDATE
- Both operations O(1) with proper indexing

### **Time Calculations**
- Using Python datetime for accuracy
- ISO 8601 format for database storage
- Avoids timezone-related bugs

---

## Future Enhancements

1. **Configurable Windows:** Allow different windows per role
2. **Grace Period:** Extended window for network issues
3. **Notifications:** Email/SMS when window opens
4. **Late Attempts:** Allow with interviewer approval
5. **Proctoring:** Integrate with video proctoring service
6. **Analytics:** Track attempt patterns and success rates

---

## Support

For issues with assessment timing:
1. Verify system clock is correct
2. Check `GET /api/interviewee/my-assessment/:id` for exact window
3. Contact recruiter if window already passed
4. See troubleshooting section in INTERVIEWER_DASHBOARD_GUIDE.md

---

*Last Updated: January 21, 2026*
*Version: 1.0*
