# 🚀 CYGNUSA Elite-Hire - AI-Enabled HR Evaluation System

> **Team:** Akshat (Backend) | Shaivi (Frontend) | Prashanth (Database)  

---

## 🎯 NEW ARCHITECTURE: Two-Sided Platform

### **Interviewee (Candidate) Flow:**
1. Select "I'm an Interviewee" on login page
2. Fill basic details: Name, Email, Phone
3. Upload resume (PDF/DOCX)
4. Submit → Wait for response
5. If rejected: Receive rejection email
6. If accepted: Receive assessment invitation email with scheduled time
7. Take assessment at scheduled time
8. Wait for final decision

### **Interviewer (Recruiter) Flow:**
1. Select "I'm an Interviewer" on login page
2. See dashboard with all candidate submissions
3. For each candidate, see:
   - Resume details
   - **AI Match Score** (auto-calculated)
   - **AI-Generated Pros & Cons**
4. Options:
   - **Reject** → Candidate gets rejection email
   - **Accept & Schedule** → Schedule assessment, candidate gets invitation email
5. After candidate completes assessment:
   - View assessment results
   - See **AI Hiring Recommendation** (with rationale)
6. Final Decision: Hire or No-Hire

---

## 📊 Project Progress Overview

### **Overall Completion:** 🟢🟢🟢⬜⬜⬜⬜⬜⬜⬜ 25%

| Phase | Status | Owner | Completion |
|-------|--------|-------|------------|
| 🏗️ Infrastructure | 🟢 COMPLETE | Prashanth | 100% |
| 🔐 Authentication | ⬜ Not Started | Shaivi + Akshat | 0% |
| 📄 Resume System | 🟡 In Progress | Akshat | 70% |
| 📝 Assessment Engine | 🟡 In Progress | Akshat + Shaivi | 60% |
| 👁️ Proctoring | ⬜ Not Started | Shaivi + Akshat | 0% |
| 🤖 AI Decision Engine | ⬜ Not Started | Akshat | 0% |
| 📧 Email System | ⬜ Not Started | Akshat | 0% |
| 🎨 UI/UX | 🟡 In Progress | Shaivi | 30% |
| 🧪 Integration | 🟡 In Progress | All | 25% |

**Legend:** 🟢 Done | 🟡 In Progress | 🔴 Blocked | ⬜ Not Started

**Latest Update:** Architecture redesigned for two-sided platform with separate Interviewer/Interviewee workflows.

---

## 🏗️ SYSTEM ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────────┐
│                        LANDING PAGE                              │
│                  "Are you an Interviewer or                      │
│                       Interviewee?"                              │
└────────────────┬────────────────────────────────┬────────────────┘
                 │                                 │
                 │                                 │
        ┌────────▼────────┐              ┌────────▼────────┐
        │   INTERVIEWEE    │              │   INTERVIEWER   │
        │      FLOW        │              │      FLOW       │
        └────────┬────────┘              └────────┬────────┘
                 │                                 │
                 │                                 │
        1. Fill Form                      1. Login (JWT)
        2. Upload Resume                  2. Dashboard
        3. Wait                               ↓
                 │                         View Candidates
                 │                         - Match Score
                 │                         - AI Pros/Cons
                 │                             ↓
                 │                         [Reject] → Email
                 │                             OR
                 │                         [Schedule] → Email
                 │                             ↓
                 ├─────────────────────────────┘
                 │
        4. Receive Email                  3. Monitor Assessments
        5. Take Assessment                4. View Results
           (at scheduled time)            5. See AI Recommendation
                 │                             ↓
                 │                         [Hire/No-Hire] → Email
                 │                             │
        6. Receive Final Email        ────────┘
                 │
            [END]
```

---

## 🗓️ Development Roadmap

### **Phase 1:** Core Foundation
- ✅ Database setup
- 🔄 Authentication & login system
- 🔄 Resume upload with AI analysis
- 🔄 Email notification system

### **Phase 2:** Assessment & Dashboard
- Interviewer dashboard
- Accept/reject functionality
- Assessment scheduling
- Assessment interface for candidates
- AI hiring decision engine

### **Phase 3:** Polish & Testing
- Proctoring features
- End-to-end testing
- UI/UX improvements
- Deployment preparation

---

# 📋 TASK BREAKDOWN

---

## 💾 PRASHANTH - DATABASE ARCHITECT

### **PHASE 1: Database Foundation** 🟡

#### ✅ Task 1.1: Database Connection (COMPLETED)
**Priority:** 🔥 CRITICAL | **Status:** ✅ COMPLETE

**Objective:** Establish database connection and verification

**Deliverables:**
- [x] `backend/db_config.py` with connection functions
- [x] Connection test functionality

**Tech Stack:** SQLite

---

#### ✅ Task 1.2: Create Database Tables (COMPLETED)
**Priority:** 🔥 CRITICAL | **Status:** ✅ COMPLETE

**Objective:** Design and implement database schema

**Tables Created:**
- [x] `candidates` - Resume data and match scores
- [x] `job_descriptions` - Job requirements
- [x] `assessments` - Assessment tracking
- [x] `mcq_responses` - MCQ answers
- [x] `coding_submissions` - Code submissions
- [x] `proctoring_events` - Activity logs
- [x] `psychometric_responses` - Trait assessments

**Files:**
- [x] `database/schema.sql`
- [x] `backend/init_db.py`

---

#### ✅ Task 1.3: Database Helper Functions (COMPLETED)
**Priority:** 🔥 CRITICAL | **Status:** ✅ COMPLETE

**Objective:** Create database operation abstractions

**Functions Implemented (13 total):**
- [x] Candidate management (insert, get, update)
- [x] Assessment operations (create, update, retrieve)
- [x] Response tracking (MCQ, coding, psychometric, proctoring)
- [x] Score calculations

**File:** `backend/db_helpers.py`

---

### **PHASE 2: Database Extension for New Architecture** ⬜

#### Task 1.4: Add Authentication Tables
**Priority:** 🔥 CRITICAL | **Status:** ⬜ TODO

**Objective:** Support user authentication system

**Requirements:**
- [ ] Create `users` table with fields: id, email (unique), password_hash, role (interviewer/interviewee), name, timestamps
- [ ] Add indexes on email and role
- [ ] Implement helper functions:
  - `create_user(email, password_hash, role, name)` - returns user_id
  - `get_user_by_email(email)` - for login validation
  - `get_user_by_id(user_id)` - for JWT token validation

---

#### Task 1.5: Add Assessment Scheduling Tables
**Priority:** 🔥 CRITICAL | **Status:** ⬜ TODO

**Objective:** Track scheduled assessments with time validation

**Requirements:**
- [ ] Create `scheduled_assessments` table with fields: id, candidate_id, interviewer_id, scheduled_time, status, assessment_id, timestamps
- [ ] Link to candidates, users, and assessments tables using foreign keys
- [ ] Add indexes on candidate_id and scheduled_time
- [ ] Implement helper functions:
  - `create_scheduled_assessment(candidate_id, interviewer_id, scheduled_time)` - returns scheduled_assessment_id
  - `get_scheduled_assessment(candidate_id)` - get scheduling details
  - `update_scheduled_assessment_status(scheduled_assessment_id, status, assessment_id)` - update status
  - `check_assessment_time_valid(candidate_id, current_time)` - validate if current time is within ±30 min window

**Status Values:** scheduled, in_progress, completed, cancelled

---

#### Task 1.6: Add Email Logging Table
**Priority:** 🟡 MEDIUM | **Status:** ⬜ TODO

**Objective:** Track all sent emails for auditing

**Requirements:**
- [ ] Create `email_logs` table with fields: id, recipient_email, recipient_name, email_type, subject, status, error_message, sent_at
- [ ] Add indexes on recipient_email and email_type
- [ ] Implement helper functions:
  - `log_email(recipient_email, recipient_name, email_type, subject, status, error_message)` - log email attempt
  - `get_candidate_emails(candidate_email)` - retrieve email history

**Email Types:** rejection, invitation, final_decision  
**Status Values:** sent, failed

---

#### Task 1.7: Modify Existing Tables
**Priority:** 🔥 CRITICAL | **Status:** ⬜ TODO

**Objective:** Update existing schema for two-sided platform

**Requirements:**
- [ ] Add to `candidates` table: pros (TEXT for JSON list), cons (TEXT for JSON list), status (with check constraint)
- [ ] Add to `assessments` table: scheduled_assessment_id (foreign key), hiring_recommendation (TEXT)
- [ ] Update helper functions:
  - Modify `insert_candidate()` to accept pros, cons, status parameters
  - Add `update_candidate_status(candidate_id, status)` function
  - Modify `update_assessment_scores()` to accept hiring_recommendation and scheduled_assessment_id

**Candidate Status Values:** pending, rejected, scheduled, assessment_complete, hired, not_hired

---

### 📌 PRASHANTH'S DELIVERABLES
- [x] Database connection ✅
- [x] All 8 base tables ✅
- [x] 13 helper functions ✅
- [ ] **NEW:** Authentication tables
- [ ] **NEW:** Scheduling tables
- [ ] **NEW:** Email logging
- [ ] **NEW:** Table modifications

---

## 🔧 AKSHAT - BACKEND ARCHITECT

### **PHASE 0: Authentication System** ⬜ NEW

#### Task 2.0: User Authentication APIs
**Priority:** 🔥 CRITICAL | **Status:** ⬜ TODO

**Objective:** Enable role-based authentication for interviewers and interviewees

**Requirements:**
- [ ] Install flask-jwt-extended and password hashing library
- [ ] Create endpoints:
  - `POST /api/auth/register` - accepts email, password, role, name; returns user_id
  - `POST /api/auth/login` - validates credentials, returns JWT token with role in claims  
  - `GET /api/auth/me` - protected endpoint, returns current user info
- [ ] Use Prashanth's user helper functions
- [ ] Hash passwords before database storage
- [ ] Include user role in JWT claims for frontend routing

---

### **PHASE 1: AI Resume Analysis** ⬜ NEW

#### Task 2.1: AI Pros & Cons Generator  
**Priority:** 🔥 CRITICAL | **Status:** ⬜ TODO

**Objective:** Generate AI-powered resume analysis

**Requirements:**
- [ ] Create function `generate_pros_cons(resume_text, job_requirements, skills, experience)` - returns dict with pros/cons lists
- [ ] Integrate Claude API or OpenAI API with appropriate prompt
- [ ] Update `/api/resume/upload` endpoint to call this function
- [ ] Store results using Prashanth's updated candidates table
- [ ] Return pros/cons with match score in response

---

### **PHASE 2: Email Notification System** ⬜ NEW

#### Task 2.2: Email Service
**Priority:** 🔥 CRITICAL | **Status:** ⬜ TODO

**Objective:** Automated email notifications at key decision points

**Requirements:**
- [ ] Create `backend/email_service.py` with email functions
- [ ] Implement three email types: rejection, assessment invitation, final decision
- [ ] Create functions:
  - `send_rejection_email(candidate_email, candidate_name)`
  - `send_assessment_invitation(candidate_email, candidate_name, assessment_link, scheduled_time)`
  - `send_final_decision_email(candidate_email, candidate_name, decision, rationale)`
- [ ] Use flask-mail or smtplib with Gmail/SendGrid
- [ ] Log all attempts using Prashanth's email_logs table
- [ ] Handle errors and log failures

**Integration:** Triggered by interviewer actions (reject, schedule, final decision)

---

### **PHASE 3: Interviewer Dashboard APIs** ⬜ NEW

#### Task 2.3: Interviewer Management Endpoints
**Priority:** 🔥 CRITICAL | **Status:** ⬜ TODO

**Objective:** APIs for candidate review and decision workflow

**Requirements:**
- [ ] Create JWT-protected endpoints (require role=interviewer):
  - `GET /api/interviewer/candidates` - list all with resume data, scores, pros/cons, status
  - `GET /api/interviewer/candidates/:id` - detailed candidate info
  - `POST /api/interviewer/candidates/:id/reject` - reject + send email + update status
  - `POST /api/interviewer/candidates/:id/schedule` - schedule assessment (body: scheduled_time) + send invite
  - `GET /api/interviewer/assessments/:candidate_id` - results with AI recommendation
  - `POST /api/interviewer/assessments/:id/final-decision` - hire/no-hire (body: decision, notes) + send email
- [ ] Validate JWT and role on all endpoints
- [ ] Use Prashanth's helper functions
- [ ] Integrate email service

---

### **PHASE 4: Assessment Scheduling** ⬜ NEW

#### Task 2.4: Time-Based Assessment Access
**Priority:** 🟡 MEDIUM | **Status:** ⬜ TODO

**Objective:** Enforce scheduled time windows for assessments

**Requirements:**
- [ ] Update `POST /api/assessment/start`:
  - Check for scheduled assessment
  - Validate current time within ±30 min window
  - Return 403 if outside window
  - Update status to "in_progress" if valid
- [ ] Create `GET /api/interviewee/my-assessment/:candidate_id` - returns scheduled_time, status, can_start flag
- [ ] Mark "completed" when assessment finished

---

### **COMPLETED TASKS**

#### ✅ Task 2.5: Flask API Setup
**Status:** ✅ COMPLETE

**Completed:**
- Flask server on port 5000
- CORS enabled
- Health check endpoint
- Uploads directory

---

#### ✅ Task 2.6: Resume Upload Endpoint
**Status:** ✅ COMPLETE

**Completed:**
- `POST /api/resume/upload` endpoint
- File validation (PDF/DOCX)
- Form data handling
- Secure file storage

---

#### ✅ Task 2.7: Resume Parsing Engine
**Status:** ✅ COMPLETE

**Completed:**
- Text extraction (PDF/DOCX)
- Skills, experience, education parsing
- Match score calculation
- Database integration

**Test Results:** 32 skills, 5 years exp, Bachelor's degree, 83% match

---

#### ✅ Task 2.8: Assessment APIs
**Status:** ✅ COMPLETE

**Completed:**
- 5 assessment endpoints (start, mcq/submit, code/submit, psychometric/submit, complete)
- `backend/questions_bank.py` with 10 MCQs, 3 coding problems, 5 psychometric scenarios
- Score calculation (MCQ 60% + Coding 40% = Technical; Technical 70% + Psychometric 30% = Overall)
- Decision generation based on thresholds

**Test Results:** MCQ 66.67%, Coding 66.67%, Technical 66.67%, Psychometric 80%, Overall 70.67%, Decision: Recommend for Hire

---

### 📌 AKSHAT'S DELIVERABLES
- [x] Flask server running ✅
- [x] Resume upload + parsing ✅
- [x] Assessment APIs ✅
- [x] Basic scoring system ✅
- [ ] **NEW:** JWT authentication
- [ ] **NEW:** AI pros/cons generator
- [ ] **NEW:** Email notification service
- [ ] **NEW:** Interviewer dashboard APIs
- [ ] **NEW:** Assessment scheduling

---

## 🎨 SHAIVI - FRONTEND ARCHITECT

**Commit message:** `feat: add resume parsing and matching logic`

**Status:** ✅ COMPLETED - Needs minor updates for new flow

---

### **PHASE 1B: AI Resume Analysis** ⬜ NEW - CRITICAL

#### Task 2.3B: AI Pros & Cons Generator
**Time:** 2 hours | **Priority:** 🔥 CRITICAL

**Goal:** Generate AI-powered pros and cons for each resume

**Update `resume_parser.py` or create `resume_analyzer.py`:**

**New function:**
- [ ] `generate_pros_cons(resume_text, job_requirements, skills, experience)` → returns {"pros": [...], "cons": [...]}

**What it should do:**
- [ ] Take parsed resume data as input
- [ ] Call Claude API or OpenAI API
- [ ] Prompt: "Analyze this candidate's resume. List 3-5 pros and 3-5 cons for hiring them."
- [ ] Parse AI response into structured format
- [ ] Return pros and cons lists

**Integration:**
- [ ] Update `/api/resume/upload` endpoint to call this function
- [ ] Store pros/cons in database (add columns to candidates table or create new table)
- [ ] Return pros/cons in API response along with match score

**Hints:**
- Use same AI API as decision engine (Claude/OpenAI)
- Keep prompt concise but include relevant details
- Parse JSON response or use structured output
- Cache results to avoid re-calling AI for same resume

**Success criteria:** Upload resume → See match score + AI pros/cons in interviewer dashboard

**Commit message:** `feat: add AI-powered resume pros/cons analysis`

---

### **PHASE 2: Email Notification System** ⬜ NEW - CRITICAL

#### Task 2.8: Email Service Setup
**Time:** 2 hours | **Priority:** 🔥 CRITICAL

**Goal:** Send automated emails to candidates

**Create `backend/email_service.py`:**

**Email templates needed:**
1. **Rejection Email** - "Thank you for applying, unfortunately..."
2. **Assessment Invitation** - "Congratulations! You've been shortlisted. Please take assessment at [scheduled_time]"
3. **Final Decision Email** - Hire or No-Hire result

**Functions to create:**
- [ ] `send_rejection_email(candidate_email, candidate_name)` 
- [ ] `send_assessment_invitation(candidate_email, candidate_name, assessment_link, scheduled_time)`
- [ ] `send_final_decision_email(candidate_email, candidate_name, decision, rationale)`

**What you need:**
- Use `flask-mail` or `smtplib` for sending emails
- Use Gmail SMTP or SendGrid API
- Create HTML email templates (simple, professional)
- Log all sent emails to database (Prashanth's email_logs table)

**API Endpoints:**
- [ ] Email sending is triggered by other endpoints (reject, schedule, complete assessment)
- [ ] No direct email endpoint needed, it's a service function

**Hints:**
- Gmail SMTP: `smtp.gmail.com:587` with app password
- SendGrid: Easy API, 100 free emails/day
- Use Jinja2 templates for HTML emails
- Test with your own email first!

**Success criteria:** Candidate receives email when interviewer clicks Reject or Schedule

**Commit message:** `feat: add email notification service`

---

### **PHASE 3: Interviewer Dashboard APIs** ⬜ NEW

#### Task 2.9: Interviewer Review Endpoints
**Time:** 2 hours | **Priority:** 🔥 CRITICAL

**Goal:** APIs for interviewer to review and manage candidates

**Create these endpoints:**

**Candidate Management:**
- [ ] `GET /api/interviewer/candidates` - Get all candidates with resume data, match score, pros/cons (requires JWT, role=interviewer)
- [ ] `GET /api/interviewer/candidates/:id` - Get detailed candidate info
- [ ] `POST /api/interviewer/candidates/:id/reject` - Reject candidate, trigger rejection email
- [ ] `POST /api/interviewer/candidates/:id/schedule` - Accept & schedule assessment
  - Body: `{"scheduled_time": "2026-01-20T10:00:00"}`
  - Trigger: Send assessment invitation email
  - Create scheduled_assessment record

**Assessment Results:**
- [ ] `GET /api/interviewer/assessments/:candidate_id` - Get assessment results with AI hiring recommendation
- [ ] `POST /api/interviewer/assessments/:id/final-decision` - Make final hire/no-hire decision
  - Body: `{"decision": "hire" or "no-hire", "notes": "..."}`
  - Trigger: Send final decision email

**Hints:**
- All endpoints need `@jwt_required()` and check role == "interviewer"
- Use Prashanth's helper functions for database operations
- Call email_service functions to send emails
- Return proper status codes: 200 (success), 403 (forbidden), 404 (not found)

**Success criteria:** Interviewer can see candidates, reject/accept, and make final decisions via API

**Commit message:** `feat: add interviewer management endpoints`

---

### **PHASE 4: Assessment Scheduling** ⬜ NEW

#### Task 2.10: Scheduled Assessment Flow
**Time:** 1-2 hours | **Priority:** 🟡 MEDIUM

**Goal:** Only allow candidates to take assessment at scheduled time

**Update assessment endpoints:**

**Modify `/api/assessment/start`:**
- [ ] Check if candidate has a scheduled assessment
- [ ] Check if current time is within allowed window (e.g., scheduled_time ± 30 mins)
- [ ] If not scheduled or wrong time: Return 403 Forbidden
- [ ] If valid: Proceed with assessment

**Add endpoint:**
- [ ] `GET /api/interviewee/my-assessment` - Get scheduled assessment details (requires JWT, role=interviewee)
  - Returns: scheduled_time, status ("pending", "completed", "scheduled")
  - If completed: Return assessment results link

**Hints:**
- Use Python datetime to compare times
- Store timezone info or use UTC
- Update scheduled_assessment status to "in_progress" when they start
- Mark as "completed" when they finish

**Success criteria:** Candidate can only start assessment at scheduled time, gets error otherwise

**Commit message:** `feat: add assessment scheduling and time validation`

---

#### ✅ Task 2.4: Assessment APIs (COMPLETED)
**Time:** 2 hours | **Priority:** 🔥 HIGH

**Goal:** Create API endpoints for assessment flow

**Created endpoints:**
- [x] `POST /api/assessment/start` - Takes candidate_id, creates assessment, returns 10 MCQ questions, 1 coding problem, 3 psychometric scenarios
- [x] `POST /api/assessment/mcq/submit` - Save MCQ answer with time taken, return if correct and correct answer
- [x] `POST /api/assessment/code/submit` - Save code submission, run placeholder tests, return test results (2/3 passing)
- [x] `POST /api/assessment/psychometric/submit` - Save trait scores and text response for each scenario
- [x] `POST /api/assessment/complete` - Calculate final scores (MCQ: 60%, Coding: 40% for technical; 70% technical + 30% psychometric for overall), generate decision

**Created files:**
- [x] `backend/questions_bank.py` - Contains 10 MCQ questions, 3 coding problems, 5 psychometric scenarios with helper functions

**Integration:**
- [x] Uses Prashanth's helper functions to save all responses to database
- [x] Calculates technical score (60% MCQ + 40% coding)
- [x] Calculates overall score (70% technical + 30% psychometric)
- [x] Returns decision: "Recommend for Hire" (>=70), "Consider for Interview" (>=50), "Not Recommended" (<50)

**Test results:**
- ✅ Start assessment returns 10 MCQs, 1 coding problem, 3 scenarios
- ✅ MCQ submissions saved with correct/incorrect tracking
- ✅ Coding submissions saved with test results
- ✅ Psychometric responses saved with multiple trait scores
- ✅ Final assessment shows: MCQ: 66.67%, Coding: 66.67%, Technical: 66.67%, Psychometric: 80%, Overall: 70.67%, Decision: Recommend for Hire

**Commit message:** `feat: add assessment submission endpoints with scoring`

**Status:** ✅ COMPLETED - All 5 assessment endpoints working and tested!

---

#### ✅ Task 2.5: Code Execution Sandbox
**Time:** 2-3 hours | **Priority:** 🟡 MEDIUM

**Goal:** Safely run candidate's code and test it

**Create `backend/grading_engine.py`:**

**What it needs:**
- [ ] `execute_code(code, language, test_cases)` → returns pass/fail for each test
- [ ] Timeout protection (5 seconds max)
- [ ] Test against hidden test cases
- [ ] Return execution time

**Hints:**
- Use `subprocess.run()` with timeout
- For Python: Write code to temp file, execute with `python tempfile.py`
- Capture stdout and compare with expected output
- Handle errors gracefully (syntax errors, runtime errors)
- **Security warning:** Real sandbox needs Docker or isolated environment!

**Success criteria:** Submit code that solves a problem → Get test case results

**Commit message:** `feat: add code execution and grading`

---

#### ✅ Task 2.6: AI Decision Engine  
**Time:** 2 hours | **Priority:** 🔥 HIGH

**Goal:** Generate hire/no-hire decision with explanation

**Create `backend/decision_engine.py`:**

**What it needs:**
- [ ] `generate_decision(assessment_data)` → returns decision + rationale

**The function should:**
- [ ] Take technical score, psychometric scores, proctoring events
- [ ] Use Claude API or OpenAI to generate rationale
- [ ] Return "Hire" / "No-Hire" / "Maybe" with detailed explanation
- [ ] Include competency map (strengths/weaknesses)

**Hints:**
- Call Anthropic API: `https://api.anthropic.com/v1/messages`
- Prompt should include all scores and ask for hiring recommendation
- Parse AI response to extract decision and reasoning
- Consider proctoring flags in the decision
- Return structured JSON with decision, rationale, and competency breakdown

**Success criteria:** Given assessment scores → Get AI-generated hiring decision with rationale

**Commit message:** `feat: add AI-powered decision engine`

---

#### ✅ Task 2.7: Proctoring Event Handler
**Time:** 1 hour | **Priority:** 🟡 MEDIUM

**Goal:** Accept and log proctoring events from frontend

**Create endpoint: `POST /api/proctoring/log`**

**What it should do:**
- [ ] Accept assessment_id, event_type, severity, details
- [ ] Validate the data
- [ ] Use Prashanth's `log_proctoring_event()` to save
- [ ] Return success

**Event types to handle:**
- Multiple faces detected
- No face detected  
- Tab switched
- Copy-paste detected
- Keyboard shortcuts used

**Hints:**
- Simple endpoint, just save to database
- Frontend will call this whenever something suspicious happens
- Severity: "low", "medium", "high"

**Commit message:** `feat: add proctoring event logging`

---

### 📌 AKSHAT'S DELIVERABLES CHECKLIST
- [x] Flask server running ✅
- [x] Resume upload working ✅
- [x] Resume parsing extracting data correctly ✅
- [x] Assessment APIs created ✅
- [ ] **NEW:** User authentication with JWT (login/register)
- [ ] **NEW:** AI pros/cons generator for resumes
- [ ] **NEW:** Email notification service (rejection, invitation, decision)
- [ ] **NEW:** Interviewer dashboard APIs (accept/reject/schedule)
- [ ] **NEW:** Assessment scheduling and time validation
- [ ] AI decision engine for final hiring recommendation
- [ ] Code execution sandbox (placeholder OK)
- [ ] Proctoring endpoint logging events
- [ ] Pull Request to merge into `dev`

---

## 🎨 SHAIVI - FRONTEND ARCHITECT

### **PHASE 0: Authentication UI** ⬜ NEW - CRITICAL

#### Task 3.0.1: Login/Landing Page
**Time:** 2-3 hours | **Priority:** 🔥 CRITICAL

**Goal:** Create landing page where users select their role

**Create `pages/LandingPage.jsx`:**

**What it needs:**
- [ ] Hero section: "Welcome to CYGNUSA Elite-Hire"
- [ ] Two large buttons/cards:
  - **"I'm an Interviewee"** → Navigate to interviewee flow
  - **"I'm an Interviewer"** → Navigate to interviewer login
- [ ] Beautiful design (use Tailwind)
- [ ] Company branding/logo

**Create `pages/LoginPage.jsx` (for interviewers):**
- [ ] Email and password fields
- [ ] Login button
- [ ] Link to register (if needed)
- [ ] Error message display
- [ ] Call `POST /api/auth/login`
- [ ] Store JWT token in localStorage
- [ ] Redirect to interviewer dashboard on success

**Update routing in `App.jsx`:**
- [ ] `/` - LandingPage (new home)
- [ ] `/interviewer/login` - LoginPage
- [ ] `/interviewer/dashboard` - Interviewer dashboard (protected route)
- [ ] `/interviewee/apply` - Interviewee application form
- [ ] `/interviewee/assessment/:id` - Assessment (protected, time-validated)

**Hints:**
- Use React Context or state management for auth
- Create ProtectedRoute component to check JWT
- Decode JWT to get user role
- Redirect based on role

**Success criteria:** Can select role, login as interviewer, proceed as interviewee

**Commit message:** `feat: add authentication UI and role selection`

---

### **PHASE 1: Interviewee Flow** 🟡

#### Task 3.1.1: Interviewee Application Page
**Time:** 1-2 hours | **Priority:** 🔥 CRITICAL

**Goal:** Simple form for candidates to submit resume

**Refactor `pages/UploadPage.jsx` → `pages/IntervieweeApplicationPage.jsx`:**

**Keep existing:**
- [x] Name, Email, Phone fields
- [x] Resume upload (PDF/DOCX)
- [x] File validation
- [x] Submit button

**REMOVE from success screen:**
- [x] ~~Match score display~~ (interviewee shouldn't see this)
- [x] ~~Skills display~~
- [x] ~~Start Assessment button~~

**NEW success message:**
- [ ] "Thank you for applying!"
- [ ] "Your resume has been submitted successfully."
- [ ] "You will receive an email if you're selected for the next round."
- [ ] Simple, clean confirmation page

**API Integration:**
- [ ] Same endpoint: `POST /api/resume/upload`
- [ ] Backend processes resume, calculates score, generates pros/cons
- [ ] Frontend just shows confirmation

**Success criteria:** Interviewee submits resume → Sees confirmation → That's it!

**Commit message:** `feat: refactor upload page for interviewee flow`

---

### **PHASE 2: Interviewer Dashboard** ⬜ NEW - CRITICAL

#### Task 3.2.1: Interviewer Dashboard - Candidate List
**Time:** 3-4 hours | **Priority:** 🔥 CRITICAL

**Goal:** Show all candidates with AI insights to interviewer

**Create `pages/InterviewerDashboardPage.jsx`:**

**What it should display:**

**Candidate List (Table/Cards):**
- [ ] Each candidate card/row shows:
  - Name, Email, Phone
  - **Match Score** (large, colored badge: 80%+ green, 50-79% yellow, <50% red)
  - Resume uploaded date
  - Status: "Pending Review", "Rejected", "Assessment Scheduled", "Assessment Complete", "Hired", "Not Hired"
  
**AI Insights Panel (expandable for each candidate):**
- [ ] **Pros** (bulleted list, green icons)
  - e.g., "5 years Python experience", "Strong ML background"
- [ ] **Cons** (bulleted list, red icons)
  - e.g., "No cloud experience", "Limited leadership roles"

**Action Buttons:**
- [ ] **Reject** (red button) → Trigger confirmation modal → Call API → Send rejection email
- [ ] **Accept & Schedule** (green button) → Open scheduling modal
  
**Scheduling Modal:**
- [ ] Date/time picker
- [ ] Submit → Call API → Send invitation email
- [ ] Show success message

**Filters/Sorting:**
- [ ] Filter by status (All, Pending, Scheduled, Completed)
- [ ] Sort by match score (high to low, low to high)
- [ ] Search by name/email

**API Integration:**
- [ ] Call `GET /api/interviewer/candidates` on page load
- [ ] Call `POST /api/interviewer/candidates/:id/reject` on reject
- [ ] Call `POST /api/interviewer/candidates/:id/schedule` on schedule

**Hints:**
- Use protected route (check JWT role == "interviewer")
- Use React state for modal visibility
- Use a date picker library (react-datepicker)
- Show loading spinner while fetching
- Update list after actions (refetch or update state)

**Success criteria:** Interviewer sees candidates, match scores, pros/cons, can accept/reject

**Commit message:** `feat: add interviewer dashboard with candidate review`

---

#### Task 3.2.2: Assessment Results View
**Time:** 2 hours | **Priority:** 🔥 HIGH

**Goal:** Show completed assessment results to interviewer

**Add to InterviewerDashboardPage or create separate page:**

**When candidate completes assessment, show:**
- [ ] All assessment scores (MCQ, Coding, Psychometric, Overall)
- [ ] **AI Hiring Recommendation:**
  - Decision: "Recommend for Hire" / "Consider" / "Not Recommended"
  - Rationale (AI-generated paragraph)
- [ ] Detailed breakdown:
  - MCQ: X/10 correct
  - Coding: Test cases passed
  - Psychometric: Trait scores
- [ ] View submitted code (optional)
- [ ] Proctoring events log (if any violations)

**Final Decision:**
- [ ] Two buttons: **Hire** (green) | **No-Hire** (red)
- [ ] Optional text area for notes
- [ ] Call `POST /api/interviewer/assessments/:id/final-decision`
- [ ] Send final decision email to candidate
- [ ] Show confirmation

**Hints:**
- Call `GET /api/interviewer/assessments/:candidate_id`
- Use charts for score visualization (optional but nice)
- Make AI rationale prominent
- Require confirmation before final decision

**Success criteria:** Interviewer sees assessment results, AI recommendation, makes final hire/no-hire decision

**Commit message:** `feat: add assessment results and final decision UI`

---

#### ✅ Task 3.1: React Project Setup (COMPLETED)
**Time:** 30 mins | **Priority:** 🔥 CRITICAL

**Goal:** Get React app running

**What was done:**
- [x] `cd frontend`
- [x] Initialize React app with Vite (faster builds)
- [x] Install dependencies: axios (v1.13.2), react-router-dom (v7.12.0), tailwindcss (v4.1.18)
- [x] Setup Tailwind CSS with PostCSS and Autoprefixer
- [x] Create folder structure: pages/, services/ (components/ not needed yet)
- [x] Create basic routing with React Router v7

**Routes created:**
- [x] `/` - Home/Upload page (UploadPage.jsx)
- [x] `/assessment/:candidateId` - Assessment interface (AssessmentPage.jsx - placeholder)
- [x] `/dashboard` - Recruiter dashboard (DashboardPage.jsx - placeholder)

**Files created:**
- [x] `src/App.jsx` - Main app with router configuration
- [x] `src/pages/UploadPage.jsx` - Resume upload page
- [x] `src/pages/AssessmentPage.jsx` - Assessment placeholder
- [x] `src/pages/DashboardPage.jsx` - Dashboard placeholder
- [x] `src/services/api.js` - Axios API client
- [x] `tailwind.config.js` - Tailwind configuration
- [x] `vite.config.js` - Vite configuration

**Success criteria:** ✅ React app runs on `localhost:5173` (Vite default)

**Commit message:** `feat: setup React project with routing`

**Status:** ✅ COMPLETED

---

#### ✅ Task 3.2: Resume Upload Page (COMPLETED)
**Time:** 2 hours | **Priority:** 🔥 CRITICAL

**Goal:** Let candidates upload their resume

**Created `pages/UploadPage.jsx` (217 lines):**

**Implemented features:**
- [x] File upload input with drag-and-drop area (accept only PDF/DOCX)
- [x] Form fields: Name (required), Email (required), Phone (optional)
- [x] Submit button with loading state
- [x] Client-side file validation (PDF/DOCX only)
- [x] Client-side form validation (name & email required)
- [x] Loading state while uploading ("Uploading..." text)
- [x] Success screen showing:
  - Match score as large percentage (blue badge)
  - All detected skills as colored tags (blue pills)
  - "Start Assessment" button (placeholder)
- [x] Error message display (red banner)
- [x] Professional UI with Tailwind CSS styling
- [x] Responsive design (mobile-friendly)

**API Integration:**
- [x] Uses `uploadResume()` from `services/api.js`
- [x] Sends multipart/form-data to `POST /api/resume/upload`
- [x] Receives parsed data (skills, experience, education, match_score)
- [x] Proper error handling with user-friendly messages

**UI/UX Details:**
- Professional gray background with white card
- SVG upload icon in drag-and-drop area
- Indigo color scheme for buttons and accents
- Real-time file name display after selection
- Disabled button state during upload

**Success criteria:** ✅ Upload resume → See match score and skills displayed beautifully

**Commit message:** `feat: add resume upload page with full functionality`

**Status:** ✅ COMPLETED - Fully functional and tested!

---

#### ⬜ Task 3.3: Assessment Interface (PLACEHOLDER CREATED)
**Time:** 4-5 hours | **Priority:** 🔥 CRITICAL

**Goal:** Complete assessment UI where candidates take tests

**Current status:** Placeholder page created (15 lines)
- [x] Created `pages/AssessmentPage.jsx` with basic structure
- [x] Uses `useParams()` to get candidateId from URL
- [x] Simple placeholder UI showing "Assessment Page"
- [ ] Full assessment interface (MCQ, Coding, Psychometric) not implemented yet

**Still needs implementation:**

**MCQ Section:**
- [ ] Display question with 4 options (A, B, C, D)
- [ ] Radio buttons to select answer
- [ ] Timer showing time spent
- [ ] Submit button
- [ ] Show next question after submit

**Coding Section:**
- [ ] Code editor (use Monaco Editor or simple textarea)
- [ ] Language selector (Python/JavaScript/Java)
- [ ] Problem description
- [ ] Run code button
- [ ] Submit button
- [ ] Show test case results after submission

**Text Response Section:**
- [ ] Question display
- [ ] Large text area for answer
- [ ] Word count
- [ ] Submit button

**Psychometric Section:**
- [ ] Scenario description
- [ ] Slider inputs (1-10) for traits like leadership, resilience
- [ ] Text area for scenario response
- [ ] Submit button

**Progress Indicator:**
- [ ] Show which section candidate is on
- [ ] Show number of questions completed
- [ ] Navigation between sections

**Hints:**
- Use state to track current question, current section
- Create separate components: MCQQuestion, CodeEditor, TextResponse, Slider
- Call respective APIs when submitting each answer
- Store assessment_id in state after starting assessment
- Use axios to communicate with backend

**Success criteria:** Can complete full assessment flow from MCQ to psychometric

**Commit message:** `feat: add complete assessment interface`

---

#### ✅ Task 3.4: Proctoring Integration
**Time:** 2-3 hours | **Priority:** 🟡 MEDIUM

**Goal:** Monitor candidate during assessment

**Add to AssessmentPage:**

**Webcam monitoring:**
- [ ] Request camera permission
- [ ] Show small webcam feed in corner
- [ ] Detect if no face (call proctoring API)
- [ ] Detect if multiple faces (call proctoring API)

**Tab switching detection:**
- [ ] Listen for `visibilitychange` event
- [ ] Log tab switch to backend

**Copy-paste detection:**
- [ ] Disable right-click in code editor
- [ ] Listen for Ctrl+C, Ctrl+V
- [ ] Log copy-paste attempts

**Warning banner:**
- [ ] Show warning if suspicious activity detected
- [ ] Count total violations

**Hints:**
- Use `navigator.mediaDevices.getUserMedia()` for webcam
- Use `document.addEventListener('visibilitychange')` for tab detection
- Use face detection library (e.g., face-api.js) or keep it simple
- Call `/api/proctoring/log` whenever event detected
- Store events locally and batch-send to reduce API calls

**Success criteria:** Switching tabs logs an event to backend

**Commit message:** `feat: add proctoring system`

---

#### ⬜ Task 3.5: Recruiter Dashboard (PLACEHOLDER CREATED)
**Time:** 3 hours | **Priority:** 🔥 HIGH

**Goal:** Show all candidates and their results

**Current status:** Placeholder page created (13 lines)
- [x] Created `pages/DashboardPage.jsx` with basic structure
- [x] Simple placeholder UI showing "Recruiter Dashboard"
- [ ] Full dashboard with candidate list not implemented yet

**Still needs implementation:**

**What it should show:**
- [ ] Table/list of all candidates
- [ ] Each row: Name, Email, Shortlist Status, Match Score
- [ ] Filter by status (High Match / Potential / Reject)
- [ ] Sort by match score
- [ ] Click candidate to see detailed view

**Detailed view modal/page:**
- [ ] Candidate info
- [ ] Technical score, Psychometric score, Overall score
- [ ] Hiring decision (Hire/No-Hire)
- [ ] AI-generated rationale
- [ ] Competency map (visual chart of strengths/weaknesses)
- [ ] Proctoring events timeline
- [ ] View submitted code

**Hints:**
- Call `GET /api/candidates/all` to get candidate list
- Use table component or map through list
- Use recharts or chart.js for competency visualization
- Make it look professional - this is what judges will see!

**Success criteria:** Dashboard shows all candidates with scores and decisions

**Commit message:** `feat: add recruiter dashboard`

---

#### ✅ Task 3.6: UI/UX Polish
**Time:** 2 hours | **Priority:** 🟡 MEDIUM

**Goal:** Make it look professional

**What to polish:**
- [ ] Consistent color scheme (use Tailwind)
- [ ] Loading spinners everywhere data is being fetched
- [ ] Error messages are user-friendly
- [ ] Smooth transitions between sections
- [ ] Responsive design (looks good on laptop)
- [ ] Add logo/branding
- [ ] Clean typography

**Hints:**
- Create reusable components: Button, Card, Modal, Loading
- Use Tailwind's utility classes consistently
- Add hover effects on buttons
- Use icons (lucide-react or heroicons)
- Make assessment feel like a real test platform

**Success criteria:** UI looks polished and professional

**Commit message:** `feat: add assessment results and final decision UI`

---

### **PHASE 3: Interviewee Assessment** 🟡

#### Task 3.3.1: Assessment Page (Keep Existing, Add Time Validation)
**Time:** 3-4 hours | **Priority:** 🔥 CRITICAL

**Goal:** Candidate takes assessment at scheduled time

**Update `pages/AssessmentPage.jsx`:**

**Time Validation:**
- [ ] On page load, call `GET /api/interviewee/my-assessment`
- [ ] Check if assessment is scheduled
- [ ] Check if current time is within allowed window
- [ ] If not allowed: Show message "Assessment not available yet. Scheduled for: [date/time]"
- [ ] If allowed: Show assessment interface

**Assessment Interface (implement from previous plan):**
- [ ] MCQ Section (10 questions, radio buttons, timer)
- [ ] Coding Section (code editor, problem description, submit)
- [ ] Psychometric Section (scenarios, sliders, text responses)
- [ ] Progress indicator
- [ ] Submit final assessment

**Keep existing backend integration:**
- [x] Call assessment APIs (start, mcq/submit, code/submit, psychometric/submit, complete)

**After completion:**
- [ ] Show "Thank you for completing the assessment!"
- [ ] "You will receive an email with the results."
- [ ] Disable re-submission

**Success criteria:** Candidate can only take assessment at scheduled time, completes all sections

**Commit message:** `feat: add time-validated assessment interface`

---

### 📌 SHAIVI'S DELIVERABLES CHECKLIST
- [x] React app running (Vite on port 5173) ✅
- [x] Tailwind CSS setup ✅
- [ ] **NEW:** Landing page with role selection (Interviewer/Interviewee)
- [ ] **NEW:** Login page for interviewers
- [ ] **NEW:** Protected routes based on JWT role
- [x] Interviewee application page (refactored from UploadPage) - partially done
- [ ] **NEW:** Interviewer dashboard (candidate list, match scores, pros/cons)
- [ ] **NEW:** Accept/Reject/Schedule functionality
- [ ] **NEW:** Assessment results view with AI recommendation
- [ ] **NEW:** Final hire/no-hire decision UI
- [ ] Assessment interface with time validation (needs full implementation)
- [ ] UI/UX polish (consistent design across all pages)
- [ ] Pull Request to merge into `dev`

---

## 🧪 INTEGRATION & TESTING (ALL THREE)

### **Final Integration Tasks** 🟡

#### ✅ Everyone: End-to-End Testing (PARTIALLY COMPLETE)
**Time:** 2 hours | **Priority:** 🔥 CRITICAL

**Test the complete flow:**
- [x] Upload resume → See parsed data and match score ✅
- [x] Start assessment → Complete all sections ✅
- [x] Submit answers → Saved to database ✅
- [x] Complete assessment → Get AI decision (basic scoring implemented) ✅
- [ ] View in dashboard → See all data correctly
- [ ] Proctoring events → Logged and visible

**Bug fixing:**
- [x] Fixed database helper function parameter mismatches ✅
- [x] Fixed assessment endpoint response structures ✅
- [x] Verified all assessment data saves correctly ✅
- [ ] Handle edge cases
- [ ] Add error messages

**Test results:**
- ✅ Resume upload: 32 skills detected, 5 years experience, Bachelor's degree, match score 83
- ✅ Assessment start: Returns 10 MCQs, 1 coding problem, 3 scenarios
- ✅ MCQ submission: 3/3 answers saved, correctness tracked (66.67% score)
- ✅ Code submission: Code saved with 2/3 test cases passing (66.67% score)
- ✅ Psychometric: 3 traits saved (leadership: 8, communication: 7, decision_making: 9)
- ✅ Final scores: Technical 66.67%, Psychometric 80%, Overall 70.67%, Decision: "Recommend for Hire"

**Commit message:** `fix: resolve integration bugs`

**Status:** 🟡 Backend-Database integration verified, Frontend integration pending

---

## 🔧 Setup Instructions

### Prerequisites
- Python 3.8+
- Node.js 16+
- SQLite (or PostgreSQL)

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
python init_db.py
python app.py
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### Environment Variables
Create `.env` file in backend directory:
```
SECRET_KEY=your_secret_key
JWT_SECRET_KEY=your_jwt_secret
AI_API_KEY=your_ai_api_key
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email
SMTP_PASS=your_password
```

---

## 📄 License
MIT License

---

## 📚 Technical Documentation

### API Reference
For detailed API endpoint documentation, see [API_DOCS.md](docs/API_DOCS.md)

### System Architecture Files

**Backend Files:**
- `backend/app.py` - Main Flask application
- `backend/resume_parser.py` - Resume parsing engine
- `backend/questions_bank.py` - Assessment questions
- `backend/db_config.py` - Database connection
- `backend/db_helpers.py` - Database operations
- `backend/init_db.py` - Database initialization

**To be Created:**
- `backend/auth.py` - JWT authentication
- `backend/email_service.py` - Email notifications
- `backend/resume_analyzer.py` - AI analysis

**Frontend Files:**
- `frontend/src/App.jsx` - Main app component
- `frontend/src/pages/UploadPage.jsx` - Resume upload (needs refactoring)
- `frontend/src/pages/AssessmentPage.jsx` - Assessment interface (in progress)
- `frontend/src/pages/DashboardPage.jsx` - Dashboard (placeholder)
- `frontend/src/services/api.js` - API client

**To be Created:**
- `frontend/src/pages/LandingPage.jsx` - Role selection
- `frontend/src/pages/LoginPage.jsx` - Authentication
- `frontend/src/pages/InterviewerDashboardPage.jsx` - Interviewer view
- `frontend/src/components/ProtectedRoute.jsx` - Route protection
- `frontend/src/context/AuthContext.jsx` - Auth state

**Database Tables:**
- `candidates` - Resume data and match scores
- `assessments` - Assessment records
- `mcq_responses` - MCQ answers
- `coding_submissions` - Code submissions
- `psychometric_responses` - Trait scores
- `job_descriptions` - Job requirements
- `proctoring_events` - Activity logs

**To be Created:**
- `users` - Authentication data
- `scheduled_assessments` - Scheduling information
- `email_logs` - Email tracking

---

## 🎯 Core Features

### Implemented
- ✅ Resume upload and parsing
- ✅ Assessment backend (MCQ, Coding, Psychometric)
- ✅ Basic scoring system
- ✅ Database infrastructure

### In Progress
- 🔄 Two-sided platform architecture
- 🔄 AI-powered resume analysis
- 🔄 Assessment scheduling system

### Planned
- ⬜ JWT authentication
- ⬜ Email notification system
- ⬜ Interviewer dashboard
- ⬜ AI hiring recommendations
- ⬜ Proctoring features

---


