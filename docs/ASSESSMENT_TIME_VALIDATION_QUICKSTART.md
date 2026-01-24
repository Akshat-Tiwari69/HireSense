# Assessment Time Validation - Quick Reference

Fast reference for the Assessment Time Validation system (Task A9).

## What Changed?

Candidates can now **only start assessments within ±30 minutes of their scheduled time**. This ensures fairness and maintains the integrity of the assessment process.

---

## For Candidates

### **Before Your Assessment**

1. **Check Your Assessment Status**
```bash
curl -X GET "http://localhost:5000/api/interviewee/my-assessment/1"
```

Response tells you:
- When assessment starts
- How many minutes until you can begin
- Whether you can start now

### **When Assessment is Ready**

2. **Start the Assessment**
```bash
curl -X POST "http://localhost:5000/api/interviewee/assessment/start/1" \
  -H "Content-Type: application/json"
```

**Success (200):** Get all questions
**Error (403):** "Assessment not available yet" - Wait or try later

### **After You're Done**

3. **Complete the Assessment**
```bash
curl -X POST "http://localhost:5000/api/interviewee/assessment/42/complete" \
  -H "Content-Type: application/json"
```

Response includes:
- All your scores
- Hiring recommendation
- Decision status

---

## For Interviewers

### **1. Schedule Assessment**
```bash
curl -X POST "http://localhost:5000/api/interviewer/candidates/1/schedule" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "scheduled_time": "2026-02-01T14:00:00"
  }'
```

Candidate automatically receives invitation email.

### **2. Monitor Assessment**
Check dashboard to see:
- Assessment status (scheduled, in_progress, completed)
- When candidate started
- Assessment results

### **3. View Results**
```bash
curl -X GET "http://localhost:5000/api/interviewer/assessments/1" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Time Window Rules

### **Scheduled Time: 14:00**

| Time | Status | Action |
|------|--------|--------|
| 13:15 | ❌ Too Early | Wait 15 minutes |
| 13:29 | ❌ Too Early | Wait 1 minute |
| 13:30 | ✅ Window Opens | Start assessment |
| 14:00 | ✅ On Time | Start assessment |
| 14:30 | ✅ Window Closes | Last chance to start |
| 14:31 | ❌ Too Late | Contact recruiter |

---

## JavaScript Examples

### **Check Assessment Status**
```javascript
async function checkAssessment(candidateId) {
  const res = await fetch(`/api/interviewee/my-assessment/${candidateId}`);
  const data = await res.json();
  
  console.log('Can start:', data.data.can_start);
  console.log('Minutes until start:', data.data.minutes_until_start);
  console.log('Scheduled time:', data.data.scheduled_time);
}
```

### **Start Assessment with Error Handling**
```javascript
async function startAssessment(candidateId) {
  try {
    const res = await fetch(`/api/interviewee/assessment/start/${candidateId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });
    
    if (res.status === 403) {
      const error = await res.json();
      alert(`Cannot start: ${error.message}`);
      return false;
    }
    
    const data = await res.json();
    return data.data.assessment_id;
  } catch (error) {
    console.error('Failed to start assessment:', error);
    return null;
  }
}
```

### **Complete Assessment**
```javascript
async function completeAssessment(assessmentId) {
  const res = await fetch(`/api/interviewee/assessment/${assessmentId}/complete`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' }
  });
  
  const result = await res.json();
  console.log('Overall Score:', result.data.scores.overall);
  console.log('Decision:', result.data.decision);
  console.log('Recommendation:', result.data.ai_recommendation);
  
  return result.data;
}
```

---

## API Endpoints

### **Candidate Endpoints**

| Endpoint | Purpose |
|----------|---------|
| `GET /api/interviewee/my-assessment/:id` | Check if you can start |
| `POST /api/interviewee/assessment/start/:id` | Start assessment (with time validation) |
| `POST /api/interviewee/assessment/:id/complete` | Complete and get results |

### **Interviewer Endpoints** (Unchanged)

| Endpoint | Purpose |
|----------|---------|
| `POST /api/interviewer/candidates/:id/schedule` | Schedule assessment |
| `GET /api/interviewer/assessments/:candidate_id` | View assessment results |

---

## Error Messages

### **Too Early**
```json
{
  "status": "error",
  "message": "Assessment not available yet. Assessment is 45 minutes away from scheduled time",
  "data": {
    "minutes_away": 45,
    "allowed_window": 30
  }
}
```
**Action:** Try again in 15+ minutes

### **Too Late**
```json
{
  "status": "error",
  "message": "Assessment not available yet. Assessment is 45 minutes away from scheduled time"
}
```
**Action:** Contact your recruiter

### **Not Scheduled**
```json
{
  "status": "error",
  "message": "No assessment scheduled yet. Please contact your recruiter."
}
```
**Action:** Wait for recruiter to schedule

---

## Time Window Diagram

```
Scheduled: 14:00:00

13:30:00    Window Opens (+30 min early)
     ↓
     ├─ ✅ CAN START (30 min early)
     │
14:00:00    Scheduled Time (exact)
     ↓
     ├─ ✅ CAN START (on time)
     │
14:30:00    Window Closes (-30 min late)
     ↓
     ├─ ❌ CANNOT START (window closed)
```

---

## Status Flow

```
Candidate Interview → Assessment Scheduled
                          ↓
                    Email sent to candidate
                          ↓
                    Candidate waits for window
                          ↓
         ✅ Window Opens      ❌ Window Closed
              ↓                    ↓
         [Start Button]       [Wait or Contact]
              ↓
      Assessment In Progress
              ↓
       Submit Answers/Code
              ↓
       POST .../complete
              ↓
    Scores + Recommendation
              ↓
   Recruiter Makes Decision
              ↓
   Candidate Gets Email Result
```

---

## Common Questions

**Q: What if I'm 5 minutes late?**
A: Still OK! You have a 30-minute window (13:30-14:30 for 14:00 scheduled).

**Q: My computer time is wrong. Can I still take it?**
A: The server uses UTC time. Sync your clock before the scheduled time.

**Q: Can I start early?**
A: No, 30 minutes early is the earliest you can start.

**Q: What if I need more time?**
A: Contact your recruiter. They can reschedule if needed.

**Q: Can I resume if I disconnect?**
A: Yes, as long as you reconnect within the 30-minute window.

---

## Frontend Implementation Tips

### **Auto-Refresh Status**
```javascript
// Check every 30 seconds if window is ready
setInterval(async () => {
  const status = await checkAssessment(candidateId);
  if (status.data.can_start) {
    showStartButton();
  }
}, 30000);
```

### **Countdown Timer**
```javascript
// Show minutes until window opens
function showCountdown(scheduledTime) {
  const timeUntil = new Date(scheduledTime) - new Date();
  const minutes = Math.ceil(timeUntil / 60000);
  
  if (minutes > 30) {
    document.getElementById('timer').textContent = 
      `Available in ${minutes - 30} minutes`;
  } else if (minutes > 0) {
    document.getElementById('timer').textContent = 
      `Assessment ready (${minutes} min window)`;
  } else {
    document.getElementById('timer').textContent = 
      'Assessment window closed';
  }
}
```

### **Graceful Error Handling**
```javascript
// If trying to start outside window, show retry button
async function handleStartError(error, candidateId) {
  const minutesAway = error.data.minutes_away;
  
  if (minutesAway > 0) {
    showRetryButton(minutesAway);
  } else {
    showContactRecruitersButton();
  }
}
```

---

## Testing Checklist

- [ ] Candidate can check status before window opens
- [ ] Candidate cannot start before 30-min early mark
- [ ] Candidate can start during 60-min window
- [ ] Candidate cannot start after 30-min late mark
- [ ] Error message shows minutes away
- [ ] Can resume in-progress assessment
- [ ] Complete endpoint calculates all scores
- [ ] Decision is accurate based on scores
- [ ] Scheduled status updates to completed

---

## Database Changes

**New Functions in `db_helpers.py`:**
- `check_assessment_time_valid()` - Time window validation
- `create_scheduled_assessment()` - Create schedule record
- `update_scheduled_assessment_status()` - Update status
- `get_assessment_by_candidate_id()` - Get latest assessment

**Updated Tables:**
- `scheduled_assessments` - Now tracks status flow

---

## Performance

All operations are O(1):
- Time validation: Single indexed query
- Status updates: Simple UPDATE
- No performance impact on existing endpoints

---

## Next Steps After A9

1. **Frontend Implementation** (Shaivi)
   - Landing page with role selector
   - Login page
   - Candidate assessment page with time validation
   - Interviewer dashboard

2. **Integration Testing**
   - End-to-end workflow testing
   - Edge case testing
   - Performance testing

3. **Deployment**
   - Environment setup
   - Database migration
   - Production testing

---

## Documentation

For detailed information, see:
- [ASSESSMENT_TIME_VALIDATION_GUIDE.md](ASSESSMENT_TIME_VALIDATION_GUIDE.md) - Complete reference
- [API_DOCS.md](API_DOCS.md) - All endpoints
- [INTERVIEWER_DASHBOARD_GUIDE.md](INTERVIEWER_DASHBOARD_GUIDE.md) - Interviewer features

---

*Last Updated: January 21, 2026*
