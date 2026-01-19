# 🚀 CYGNUSA Elite-Hire - AI-Enabled HR Evaluation System

> **Team:** Akshat (Backend) | Shaivi (Frontend) | Prashanth (Database)  
> **Hackathon:** SRM Innovation Hackathon - Edition 1  

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

### **Overall Completion:** 🟢🟢🟢⬜⬜⬜⬜⬜⬜⬜ 25% (Architecture Redesigned)

| Phase | Status | Owner | Completion |
|-------|--------|-------|------------|
| 🏗️ Infrastructure | 🟢 COMPLETE | Prashanth | 100% |
| 🔐 Authentication | ⬜ Not Started | Shaivi + Akshat | 0% |
| 📄 Resume System | 🟡 In Progress | Akshat | 70% (needs email) |
| 📝 Assessment Engine | 🟡 In Progress | Akshat + Shaivi | 60% (needs scheduling) |
| 👁️ Proctoring | ⬜ Not Started | Shaivi + Akshat | 0% |
| 🤖 AI Decision Engine | ⬜ Not Started | Akshat | 0% |
| 📧 Email System | ⬜ Not Started | Akshat | 0% |
| 🎨 UI/UX | 🟡 In Progress | Shaivi | 30% (needs redesign) |
| 🧪 Integration | 🟡 In Progress | All | 25% |

**Legend:** 🟢 Done | 🟡 In Progress | 🔴 Blocked | ⬜ Not Started

**Latest Update:** 🔄 MAJOR ARCHITECTURE CHANGE - Two-sided platform with separate Interviewer/Interviewee flows!

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

## 🗓️ REVISED 3-Day Battle Plan

### **Day 1 (Today):** Core Foundation
- ✅ Database setup (DONE)
- 🔄 Authentication & Login System (NEW - CRITICAL)
- 🔄 Resume upload (refactor for new flow)
- 🔄 AI Match Score & Pros/Cons generation (NEW - CRITICAL)
- 🔄 Email notification system setup (NEW - CRITICAL)

### **Day 2:** Interviewer Dashboard & Assessment
- Interviewer dashboard (view candidates, scores, pros/cons)
- Accept/Reject functionality with emails
- Assessment scheduling system
- Assessment interface for candidates
- AI hiring decision engine

### **Day 3:** Polish & Integration
- Proctoring (basic tab detection)
- End-to-end testing both flows
- Email templates and deliverability
- UI/UX polish
- Demo preparation

---

# 📋 TASK BREAKDOWN

---

## 💾 PRASHANTH - DATABASE ARCHITECT

### **PHASE 1: Database Foundation** 🟡

#### ✅ Task 1.1: Database Connection (COMPLETED)
**Time:** 30 mins | **Priority:** 🔥 CRITICAL

**Goal:** Get database up and running

**What you need:**
- [x] Choose: SQLite (easier) or PostgreSQL (production-ready)
- [x] Create `backend/db_config.py`
- [x] Write a `get_connection()` function
- [x] Write a `test_connection()` function that prints success/failure

**Hints:**
- SQLite: `import sqlite3`, then `sqlite3.connect('filename.db')`
- PostgreSQL: `import psycopg2`, needs connection params
- Test by running the file directly: `python db_config.py`

**Success criteria:** Running the file prints "Database connected!" ✅

**Commit message:** `db: setup database connection`

**Status:** ✅ COMPLETED - Database connection working!

---

#### ✅ Task 1.2: Create Database Tables
**Time:** 1-2 hours | **Priority:** 🔥 CRITICAL

**Goal:** Design and create all tables for the system

**Tables you need:**
- [x] `candidates` - Store resume data and match scores
- [x] `job_descriptions` - Store JD requirements  
- [x] `assessments` - Track each candidate's test
- [x] `mcq_responses` - Store MCQ answers
- [x] `coding_submissions` - Store code submissions
- [x] `proctoring_events` - Log suspicious activities
- [x] `psychometric_responses` - Store personality test data

**Hints:**
- Create `database/schema.sql` with CREATE TABLE statements
- Think about: What fields? What data types? What's the primary key?
- Use FOREIGN KEYs to link tables (e.g., assessment links to candidate)
- Create `backend/init_db.py` that reads schema.sql and executes it
- Candidates need: id, name, email, resume_path, parsed_skills (JSON/TEXT), match_score
- Assessments need: id, candidate_id, technical_score, psychometric_score, decision, rationale

**Success criteria:** Running `python init_db.py` creates all tables without errors ✅

**Commit message:** `db: create database schema with all tables`

**Status:** ✅ COMPLETED - All 8 tables created with proper relationships and indices!

---

#### ✅ Task 1.3: Database Helper Functions (COMPLETED)
**Time:** 2-3 hours | **Priority:** 🔥 CRITICAL

**Goal:** Create reusable functions for database operations

**Create `backend/db_helpers.py` with these functions:**

**Candidate functions:**
- [x] `insert_candidate(name, email, phone, resume_path, parsed_data)` → returns candidate_id
- [x] `get_candidate_by_id(id)` → returns candidate dict
- [x] `get_all_candidates()` → returns list of all candidates
- [x] `update_candidate_shortlist(id, status, score)` → updates match score

**Assessment functions:**
- [x] `create_assessment(candidate_id)` → returns assessment_id
- [x] `update_assessment_scores(assessment_id, scores, decision, rationale)`
- [x] `get_assessment_by_id(id)` → returns assessment details

**Response tracking:**
- [x] `save_mcq_response(assessment_id, question_id, answer, is_correct, time)`
- [x] `save_coding_submission(assessment_id, problem_id, code, passed, total)`
- [x] `log_proctoring_event(assessment_id, event_type, severity, details)`
- [x] `save_psychometric_response(assessment_id, trait, score)`

**Score calculation:**
- [x] `get_mcq_score(assessment_id)` → returns percentage
- [x] `get_coding_score(assessment_id)` → returns percentage  
- [x] `get_psychometric_scores(assessment_id)` → returns trait scores

**Hints:**
- Use `cursor.execute()` for SQL queries
- Use `cursor.lastrowid` to get ID of inserted row
- Use `cursor.fetchone()` for single result, `cursor.fetchall()` for multiple
- Always `conn.commit()` after INSERT/UPDATE
- Store lists/dicts as JSON strings: `json.dumps()` and `json.loads()`
- Add try-except blocks for error handling

**Success criteria:** Create a test file that inserts a candidate, creates an assessment, and retrieves it ✅

**Commit message:** `db: add database helper functions`

**Status:** ✅ COMPLETED - All 13 helper functions created and tested successfully!

---

### 📌 PRASHANTH'S DELIVERABLES CHECKLIST
- [x] Database connection working ✅
- [x] All 8 tables created ✅
- [x] Helper functions written and tested ✅
- [x] Can insert and retrieve data successfully ✅
- [ ] **NEW:** Add `users` table (interviewer/interviewee, email, password_hash, role)
- [ ] **NEW:** Add `scheduled_assessments` table (candidate_id, interviewer_id, scheduled_time, status)
- [ ] **NEW:** Update `assessments` table to link to scheduled_assessments
- [ ] **NEW:** Add email_logs table (to track sent emails)
- [ ] Pull Request created to merge into `dev`

---

## 🔧 AKSHAT - BACKEND ARCHITECT

### **PHASE 0: Authentication System** ⬜ NEW - CRITICAL

#### Task 2.0.1: User Authentication APIs
**Time:** 2-3 hours | **Priority:** 🔥 CRITICAL

**Goal:** Enable login/signup for interviewers and interviewees

**Create these endpoints:**

**Authentication:**
- [ ] `POST /api/auth/register` - Register new user (email, password, role: "interviewer" or "interviewee")
- [ ] `POST /api/auth/login` - Login user, return JWT token
- [ ] `POST /api/auth/logout` - Logout user (optional, mainly frontend)
- [ ] `GET /api/auth/me` - Get current user info from token

**What you need:**
- Use `flask-jwt-extended` for JWT tokens
- Hash passwords with `bcrypt` or `werkzeug.security`
- Store users in Prashanth's new `users` table
- Return role in JWT token so frontend knows interviewer vs interviewee

**Hints:**
- Install: `pip install flask-jwt-extended`
- Use `@jwt_required()` decorator to protect routes
- Store JWT in localStorage on frontend
- Include role in JWT claims: `additional_claims={"role": user_role}`

**Success criteria:** Can register, login, and get protected user info

**Commit message:** `feat: add user authentication with JWT`

---

#### ✅ Task 2.1: Flask API Setup
**Time:** 30 mins | **Priority:** 🔥 CRITICAL

**Goal:** Get Flask server running with basic endpoint

**What to do:**
- [x] Update `backend/requirements.txt` with: flask, flask-cors, PyPDF2, python-docx
- [x] Run `pip install -r requirements.txt`
- [x] Create basic Flask app in `app.py`
- [x] Enable CORS (so frontend can call your APIs)
- [x] Create `/api/health` endpoint that returns `{"status": "ok"}`
- [x] Create `uploads/` folder for resume storage

**Hints:**
- Import Flask and CORS
- `app = Flask(__name__)` and `CORS(app)`
- Use `@app.route()` decorator for endpoints
- Run with `app.run(debug=True, port=5000)`
- Test by visiting `http://localhost:5000/api/health` in browser

**Success criteria:** Browser shows your JSON response

**Commit message:** `feat: setup Flask API with health check`

---

#### ✅ Task 2.2: Resume Upload Endpoint
**Time:** 1 hour | **Priority:** 🔥 CRITICAL

**Goal:** Accept resume files from frontend

**Create endpoint: `POST /api/resume/upload`**

**What it should do:**
- [x] Accept file upload (PDF/DOCX only)
- [x] Accept form data: name, email, phone
- [x] Validate: file exists, correct type, name and email provided
- [x] Generate unique filename (hint: use `uuid`)
- [x] Save file to `uploads/` folder
- [x] Return success response with file path

**Hints:**
- Use `request.files['file']` to get uploaded file
- Use `request.form.get('name')` for form data
- Check file extension: `filename.endswith('.pdf')`
- Save with: `file.save(filepath)`
- Use `werkzeug.utils.secure_filename()` for security
- Return JSON with status and file path

**Success criteria:** Can upload a file using Postman/curl and see it in uploads folder

**Commit message:** `feat: add resume upload endpoint`

---

#### ✅ Task 2.3: Resume Parsing Engine
**Time:** 3-4 hours | **Priority:** 🔥 CRITICAL

**Goal:** Extract meaningful data from resumes

**Create `backend/resume_parser.py` with:**

**Text extraction:**
- [x] `extract_text_from_pdf(filepath)` → returns text string
- [x] `extract_text_from_docx(filepath)` → returns text string

**Data extraction:**
- [x] `extract_skills(text)` → returns list of skills found
- [x] `extract_experience(text)` → returns years as integer
- [x] `extract_education(text)` → returns degree string

**Matching logic:**
- [x] `calculate_match_score(candidate_skills, candidate_exp, jd_skills, jd_min_exp)` → returns score 0-100
- [x] `get_shortlist_status(score)` → returns "High Match" / "Potential" / "Reject"

**Main function:**
- [x] `parse_resume(filepath, job_description)` → returns dict with all parsed data

**Hints:**
- For PDF: Use `PyPDF2.PdfReader`, loop through pages, extract text
- For DOCX: Use `python-docx`, loop through paragraphs
- For skills: Create a list of common skills, search for them in text (case-insensitive)
- For experience: Use regex to find patterns like "X years of experience"
- For education: Search for keywords like "B.Tech", "M.Tech", "Bachelor", "Master"
- Match score: Weight skills (70%) + experience (30%)
- High Match: 70+, Potential: 40-69, Reject: <40

**Integration:**
- [x] Update upload endpoint to call `parse_resume()` after saving file
- [x] Use Prashanth's `insert_candidate()` to save parsed data to database
- [x] Return parsed data in API response

**Success criteria:** Upload resume → Get JSON with skills, experience, education, match score

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

#### ✅ Everyone: Demo Preparation
**Time:** 2 hours | **Priority:** 🔥 CRITICAL

**Prepare for judges:**
- [ ] Create sample resumes (3-4 test candidates)
- [ ] Prepare demo script (what to show in what order)
- [ ] Practice the demo (5-7 minutes)
- [ ] Prepare to answer questions about architecture
- [ ] Each person knows their part inside-out

**Demo flow:**
1. Show resume upload + parsing + scoring (30 sec)
2. Show assessment interface (1 min)
3. Show proctoring in action (30 sec)
4. Show AI decision with rationale (1 min)
5. Show recruiter dashboard (1 min)
6. Explain architecture briefly (1 min)

---

## � API ENDPOINTS REFERENCE

### **Backend Server:** `http://localhost:5000`

#### **Health Check**
- **GET** `/api/health` - Check if server is running
  - Response: `{"status": "ok"}`

#### **Resume Management**
- **POST** `/api/resume/upload` - Upload and parse resume
  - Body (multipart/form-data):
    - `file`: PDF or DOCX file
    - `name`: Candidate name
    - `email`: Candidate email
    - `phone`: Phone number (optional)
  - Response: Parsed data (skills, experience, education, match_score), candidate_id, file_path

#### **Assessment System**
- **POST** `/api/assessment/start` - Start assessment for candidate
  - Body: `{"candidate_id": 1}`
  - Response: assessment_id, 10 MCQ questions, 1 coding problem, 3 psychometric scenarios

- **POST** `/api/assessment/mcq/submit` - Submit MCQ answer
  - Body: `{"assessment_id": 1, "question_id": 1, "answer": 0, "time_taken": 30}`
  - Response: `{"is_correct": true, "correct_answer": 0}`

- **POST** `/api/assessment/code/submit` - Submit code solution
  - Body: `{"assessment_id": 1, "problem_id": 1, "code": "...", "language": "python"}`
  - Response: Test results, passed_count, total_count, score

- **POST** `/api/assessment/psychometric/submit` - Submit psychometric response
  - Body: `{"assessment_id": 1, "scenario_id": 1, "trait_scores": {"leadership": 8}, "response_text": "..."}`
  - Response: Success message

- **POST** `/api/assessment/complete` - Finalize assessment and get decision
  - Body: `{"assessment_id": 1}`
  - Response: All scores (MCQ, coding, technical, psychometric, overall), decision, rationale

### **Backend Files Created/To Create**
**Existing (Keep & Modify):**
- `backend/app.py` - Main Flask application (needs auth, interviewer APIs, email integration)
- `backend/resume_parser.py` - Resume parsing (needs AI pros/cons function)
- `backend/questions_bank.py` - Assessment questions ✅
- `backend/db_config.py` - Database connection ✅
- `backend/db_helpers.py` - Database functions (needs new functions for users, scheduling)
- `backend/init_db.py` - Database initialization (needs new tables)

**New Files to Create:**
- `backend/auth.py` - JWT authentication functions
- `backend/email_service.py` - Email sending (rejection, invitation, decision)
- `backend/resume_analyzer.py` - AI pros/cons generator

### **Frontend Files - Need Major Refactoring**
**New Files to Create:**
- `frontend/src/pages/LandingPage.jsx` - Role selection page
- `frontend/src/pages/LoginPage.jsx` - Interviewer login
- `frontend/src/pages/IntervieweeApplicationPage.jsx` - Simplified upload (refactor existing)
- `frontend/src/pages/InterviewerDashboardPage.jsx` - Main interviewer dashboard
- `frontend/src/pages/AssessmentResultsPage.jsx` - View candidate assessment results
- `frontend/src/components/ProtectedRoute.jsx` - JWT-based route protection
- `frontend/src/context/AuthContext.jsx` - Auth state management

**Keep & Modify:**
- `frontend/src/pages/AssessmentPage.jsx` - Add time validation
- `frontend/src/services/api.js` - Add new API calls

### **Database Tables - Need Updates**
**Existing Tables:** candidates, assessments, mcq_responses, coding_submissions, psychometric_responses, job_descriptions, proctoring_events

**New Tables Needed (Prashanth):**
- `users` - (id, email, password_hash, role, name, created_at)
- `scheduled_assessments` - (id, candidate_id, interviewer_id, scheduled_time, status, created_at)
- `email_logs` - (id, recipient_email, email_type, sent_at, status)

**Table Modifications:**
- `candidates` - Add: pros (TEXT), cons (TEXT), status (pending/rejected/scheduled/completed/hired)
- `assessments` - Add: scheduled_assessment_id (FK), hiring_recommendation (TEXT)
- `frontend/src/pages/DashboardPage.jsx` - Dashboard placeholder (13 lines)
- `frontend/src/services/api.js` - Axios API client (26 lines) ✅
- `frontend/tailwind.config.js` - Tailwind CSS configuration ✅
- `frontend/vite.config.js` - Vite build configuration ✅
- `frontend/package.json` - Dependencies: React 18.2, React Router 7.12, Axios 1.13, Tailwind 4.1 ✅

### **Frontend Server:** `http://localhost:5173` (Vite)

**Routes:**
- `/` - Resume Upload Page (fully functional) ✅
- `/assessment/:candidateId` - Assessment Interface (placeholder)
- `/dashboard` - Recruiter Dashboard (placeholder)

### **Database Tables**
- `candidates` - Resume data and match scores
- `assessments` - Assessment records with scores and decisions
- `mcq_responses` - MCQ answers tracking
- `coding_submissions` - Code submissions with test results
- `psychometric_responses` - Trait scores and responses
- `job_descriptions` - Job requirements
- `proctoring_events` - Suspicious activity logs

---

## �📊 JUDGING CRITERIA MAPPING

Remember what judges care about:

| Criteria | Weight | Who Owns This | How to Win |
|----------|--------|---------------|------------|
| **Architectural Depth** | 30% | All | Clean code structure, good API design, proper data flow |
| **Grading Accuracy** | 20% | Akshat + Prashanth | Resume parser catches skills correctly, code execution works |
| **Logic Transparency** | 20% | Akshat | AI rationale is detailed and makes sense |
| **Security & Anti-Cheat** | 15% | Shaivi + Akshat | Proctoring actually works, can't easily bypass |
| **User Experience** | 15% | Shaivi | Clean UI, intuitive flow, looks professional |

---

## 🎯 MINIMUM VIABLE PRODUCT (MVP) - UPDATED

**MUST HAVE for Demo (New Two-Sided Flow):**
- [ ] **Landing page** - Role selection (Interviewer/Interviewee)
- [ ] **Authentication** - Login for interviewers, simple form for interviewees
- [x] **Resume upload** - Interviewee submits resume ✅ (needs minor UI updates)
- [ ] **AI Analysis** - Match score + Pros/Cons generation
- [ ] **Interviewer Dashboard** - View candidates, scores, AI insights
- [ ] **Accept/Reject** - Interviewer can reject (sends email) or schedule assessment
- [ ] **Email System** - Rejection & invitation emails working
- [ ] **Scheduled Assessment** - Candidate takes test at scheduled time only
- [x] **Assessment Flow** - MCQ + Coding + Psychometric ✅ (backend done, frontend needs completion)
- [ ] **AI Hiring Decision** - Final recommendation for interviewer
- [ ] **Final Decision** - Interviewer makes hire/no-hire choice, sends email

**NICE TO HAVE (if time permits):**
- Proctoring (tab detection)
- Advanced code execution sandbox
- Beautiful UI animations
- Detailed charts/visualizations
- Email templates with HTML styling
- Assessment rescheduling

---

## 🏆 PRIORITY TASK LIST FOR TEAM

### **DAY 1 CRITICAL TASKS (Do These First!):**

**Prashanth (Database - 2-3 hours):**
1. Add `users` table with authentication fields
2. Add `scheduled_assessments` table
3. Add `email_logs` table
4. Modify `candidates` table: add pros, cons, status columns
5. Create helper functions for new tables
6. Test all database operations

**Akshat (Backend - 4-5 hours):**
1. ✅ ~~Resume upload~~ (DONE, needs AI pros/cons integration)
2. Implement JWT authentication (`POST /api/auth/login`, `/register`)
3. Create AI pros/cons generator (call Claude/OpenAI API)
4. Build email service (rejection, invitation, decision emails)
5. Create interviewer dashboard APIs (GET candidates, POST reject, POST schedule)
6. Add time validation to assessment start endpoint
7. Test all new endpoints with Postman

**Shaivi (Frontend - 4-5 hours):**
1. Create Landing Page with role selection
2. Create Login Page for interviewers
3. Set up authentication (JWT storage, protected routes)
4. Refactor Upload Page for interviewee (remove score display)
5. Start Interviewer Dashboard (candidate list, match scores)
6. Add Accept/Reject/Schedule buttons with modals
7. Test login flow and dashboard

### **DAY 2 TASKS:**
- Complete Interviewer Dashboard (pros/cons display, assessment results)
- Implement assessment scheduling UI
- Complete assessment interface for candidates
- AI hiring recommendation display
- Final decision flow (hire/no-hire)
- Email testing and verification

### **DAY 3 TASKS:**
- End-to-end testing (both user flows)
- Proctoring (if time permits)
- UI/UX polish
- Demo preparation
- Bug fixes

---
1. What did you finish yesterday?
2. What are you working on today?
3. Any blockers?

**Every evening (5 mins):**
1. What got done?
2. What's blocking you?
3. Plan for tomorrow

---

## 🆘 WHEN YOU'RE STUCK

**Check in this order:**
1. Google the exact error message
2. Ask your teammates (maybe they faced it)
3. Ask Claude (me!) - share the error
4. Check the original README for API contracts

**Don't waste more than 30 minutes stuck on one thing!**

---

## ✅ FINAL SUBMISSION CHECKLIST

**Before submitting:**
- [ ] All code pushed to GitHub
- [ ] README.md updated with setup instructions
- [ ] .env files not committed (check .gitignore)
- [ ] All team members can run the project locally
- [ ] Demo script prepared
- [ ] Screenshots/demo video ready (if required)
- [ ] Each person can explain their part

---

## 🏆 LET'S WIN THIS!

**Remember:**
- **Day 1:** Get the foundation solid
- **Day 2:** Build features fast
- **Day 3:** Make it shine

**Communication is key!** Use your group chat actively.

**Questions?** Come back to me anytime. I'll help with:
- Debugging errors
- Architecture decisions  
- Logic clarification
- Code review

Now go build something amazing! 💪🚀

---

## 📝 ARCHITECTURE CHANGE SUMMARY

### **What Changed:**
- ❌ **OLD:** Single flow where candidates directly see their scores and take assessments
- ✅ **NEW:** Two-sided platform with distinct Interviewer and Interviewee experiences

### **Key New Features:**
1. **Role-Based Authentication** - Interviewers login, Interviewees just apply
2. **AI Resume Analysis** - Auto-generates match score + pros/cons for interviewer
3. **Interviewer Control** - Accept/Reject decisions before assessment
4. **Email Notifications** - Automated emails at every stage
5. **Scheduled Assessments** - Candidates can only take test at assigned time
6. **Two-Stage AI** - Initial resume review + final hiring recommendation

### **What's Reusable:**
- ✅ Database infrastructure (with additions)
- ✅ Resume parsing engine (needs AI pros/cons integration)
- ✅ Assessment backend APIs (needs scheduling validation)
- ✅ Basic frontend structure (needs major refactoring)

### **What's New:**
- Authentication system (JWT)
- Email service
- Interviewer dashboard
- Scheduling system
- AI pros/cons generator
- Role-based routing

---

**Current Status:** Architecture redesigned, tasks reassigned, ready to implement!

**Next Steps:** 
1. Prashanth: Update database schema with new tables
2. Akshat: Implement authentication + email + AI analysis
3. Shaivi: Build landing page + login + interviewer dashboard

**Let's build this! 🚀**
