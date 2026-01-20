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

### **Overall Completion:** 🟢🟢🟢🟢🟢🟢🟢🟢 85%

| Phase | Status | Owner | Completion |
|---------------|-------|------------|
| 🏗️ Infrastructure | 🟢 COMPLETE | Prashanth | 100% |
| 📄 Resume System | � COMPLETE | Akshat | 100% |
| 📝 Assessment Engine | 🟢 COMPLETE | Akshat + Shaivi | 100% |
| 👁️ Proctoring | 🟢 COMPLETE | Shaivi + Akshat | 100% |
| 🤖 AI Decision Engine | 🟡 In Progress | Akshat | 60% |
| 🎨 UI/UX | � COMPLETE | Shaivi | 100% |
| 🧪 Integration | 🟢 COMPLETE | All | 100% |

**Legend:** 🟢 Done | 🟡 In Progress | 🔴 Blocked | ⬜ Not Started

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

**Priority Legend:** 🔥 CRITICAL | 🟡 MEDIUM | 🟢 LOW

---

## 💾 PRASHANTH - DATABASE TASKS

### ✅ COMPLETED TASKS

**Task P1: Database Connection** ✅  
- Created `backend/db_config.py` with connection functions
- SQLite database setup complete

**Task P2: Base Schema Tables** ✅  
- Created 8 tables: candidates, assessments, job_descriptions, mcq_responses, coding_submissions, psychometric_responses, proctoring_events
- Files: `database/schema.sql`, `backend/init_db.py`

**Task P3: Database Helper Functions** ✅  
- Implemented 13 helper functions in `backend/db_helpers.py`
- Candidate management, assessment operations, response tracking, score calculations

---

### 🔥 URGENT TASKS (Do These Next)

**Task P4: Authentication Tables** 🔥  
**Status:** ⬜ TODO

**Requirements:**
- [ ] Create `users` table: id, email (unique), password_hash, role, name, timestamps
- [ ] Add indexes on email and role
- [ ] Implement helper functions:
  - `create_user(email, password_hash, role, name)`
  - `get_user_by_email(email)`
  - `get_user_by_id(user_id)`

---

**Task P5: Assessment Scheduling Table** 🔥  
**Status:** ⬜ TODO

**Requirements:**
- [ ] Create `scheduled_assessments` table: id, candidate_id, interviewer_id, scheduled_time, status, assessment_id, timestamps
- [ ] Foreign keys to candidates, users, assessments
- [ ] Indexes on candidate_id and scheduled_time
- [ ] Implement helper functions:
  - `create_scheduled_assessment(candidate_id, interviewer_id, scheduled_time)`
  - `get_scheduled_assessment(candidate_id)`
  - `update_scheduled_assessment_status(scheduled_assessment_id, status, assessment_id)`
  - `check_assessment_time_valid(candidate_id, current_time)` - validates ±30 min window

---

**Task P6: Update Existing Tables** 🔥  
**Status:** ⬜ TODO

**Requirements:**
- [ ] Add to `candidates` table: pros, cons, status columns
- [ ] Add to `assessments` table: scheduled_assessment_id, hiring_recommendation
- [ ] Update helper functions:
  - Modify `insert_candidate()` for new parameters
  - Add `update_candidate_status(candidate_id, status)`
  - Modify `update_assessment_scores()` for new fields

---

### 🟡 OPTIONAL TASKS

**Task P7: Email Logging Table** 🟡  
**Status:** ⬜ TODO

**Requirements:**
- [ ] Create `email_logs` table: id, recipient_email, recipient_name, email_type, subject, status, error_message, sent_at
- [ ] Implement helper functions:
  - `log_email(...)` - log email attempt
  - `get_candidate_emails(candidate_email)` - retrieve history

---

## 🔧 AKSHAT - BACKEND TASKS

### ✅ COMPLETED TASKS

**Task A1: Flask API Setup** ✅  
- Flask server running on port 5000
- CORS enabled, health check endpoint
- Uploads directory created

**Task A2: Resume Upload Endpoint** ✅  
- `POST /api/resume/upload` endpoint functional
- File validation (PDF/DOCX)
- Secure file storage

**Task A3: Resume Parsing Engine** ✅  
- Text extraction from PDF/DOCX
- Skills, experience, education extraction
- Match score calculation (0-100)
- Database integration
- Test: 32 skills, 5 years exp, 83% match

**Task A4: Assessment APIs** ✅  
- 5 endpoints: start, mcq/submit, code/submit, psychometric/submit, complete
- Created `backend/questions_bank.py` with questions
- Score calculation and decision generation
- Test: Overall 70.67%, Decision: Recommend for Hire

---

### **PHASE 2: Assessment Engine** ⬜

#### ✅ Task 2.4: Assessment APIs
**Time:** 2 hours | **Priority:** 🔥 HIGH

**Create these endpoints:**

**Start assessment:**
- [ ] `POST /api/assessment/start` - Takes candidate_id, creates assessment, returns questions

**Submit answers:**
- [ ] `POST /api/assessment/mcq/submit` - Save MCQ answer, return if correct
- [ ] `POST /api/assessment/code/submit` - Run code, return test results
- [ ] `POST /api/assessment/psychometric/submit` - Save slider/scenario responses

**Complete assessment:**
- [ ] `POST /api/assessment/complete` - Calculate final scores, return decision

**Hints:**
- Use Prashanth's helper functions to save/retrieve data
- For code execution: Research `subprocess` or Docker (be careful with security!)
- Store MCQ questions in a Python list/dict (or separate JSON file)
- Calculate technical score from MCQ + coding
- Calculate psychometric score from trait averages

**Commit message:** `feat: add assessment submission endpoints`

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
- [x] Flask server running
- [x] Resume upload working
- [x] Resume parsing extracting data correctly
- [ ] Assessment APIs created
- [ ] Code execution working (even if basic)
- [ ] AI decision engine generating rationale
- [ ] Proctoring endpoint logging events
- [ ] All endpoints tested with Postman
- [ ] Pull Request to merge into `dev`

---

## 🎨 SHAIVI - FRONTEND ARCHITECT

### **PHASE 1: UI Foundation** ⬜

#### ✅ Task 3.1: React Project Setup
**Time:** 30 mins | **Priority:** 🔥 CRITICAL

**Goal:** Get React app running

**What to do:**
- [x] `cd frontend`
- [x] Initialize React app: `npx create-react-app .` (or Vite for faster builds)
- [x] Install dependencies: axios, react-router-dom, tailwindcss
- [x] Setup Tailwind CSS
- [x] Create folder structure: components/, pages/, services/
- [x] Create basic routing (React Router)

**Routes you need:**
- `/` - Home/Upload page
- `/assessment/:candidateId` - Assessment interface
- `/dashboard` - Recruiter dashboard

**Success criteria:** React app runs on `localhost:3000`

**Commit message:** `feat: setup React project with routing`

---

#### ✅ Task 3.2: Resume Upload Page
**Time:** 2 hours | **Priority:** 🔥 CRITICAL

**Goal:** Let candidates upload their resume

**Create `pages/UploadPage.jsx`:**

**What it needs:**
- [ ] File upload input (accept only PDF/DOCX)
- [ ] Form fields: Name, Email, Phone
- [ ] Submit button
- [ ] Loading state while uploading
- [ ] Show success message with match score after upload
- [ ] Show error message if upload fails

**Hints:**
- Use `<input type="file" accept=".pdf,.docx" />`
- Use FormData to send file + form data
- Use axios to POST to `/api/resume/upload`
- Show parsed data (skills, experience, match score) after successful upload
- Add validation (check if file selected, email format, etc.)

**Success criteria:** Upload resume → See parsed results on screen

**Commit message:** `feat: add resume upload page`

---

#### ✅ Task 3.3: Assessment Interface
**Time:** 4-5 hours | **Priority:** 🔥 CRITICAL

**Goal:** Complete assessment UI where candidates take tests

**Create `pages/AssessmentPage.jsx` with sections:**

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

#### ✅ Task 3.5: Recruiter Dashboard
**Time:** 3 hours | **Priority:** 🔥 HIGH

**Goal:** Show all candidates and their results

**Create `pages/DashboardPage.jsx`:**

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

**Commit message:** `ui: polish design and user experience`

---

### 📌 SHAIVI'S DELIVERABLES CHECKLIST
- [ ] React app running
- [ ] Resume upload page working
- [ ] Complete assessment interface (MCQ, Code, Text, Psychometric)
- [ ] Proctoring detecting tab switches
- [ ] Recruiter dashboard showing candidates
- [ ] All pages styled and responsive
- [ ] All API calls working (test with Akshat's backend)
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
- ✅ Recruiter Dashboard
- ✅ Landing Page & Navigation
- ✅ Proctoring Integration

### In Progress
- 🔄 AI-powered resume analysis (Advanced)
- 🔄 Assessment scheduling system

### Planned
- ⬜ JWT authentication
- ⬜ Email notification system
- ⬜ AI hiring recommendations (Advanced)

---


