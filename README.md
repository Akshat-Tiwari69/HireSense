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

### **Overall Completion:** 🟢🟢🟢🟢🟢⬜⬜⬜⬜⬜ 40%

| Phase | Status | Owner | Completion |
|-------|--------|-------|------------|
| 🏗️ Database (Base) | 🟢 COMPLETE | Prashanth | 100% |
| 🏗️ Database (Auth Tables) | 🟢 COMPLETE | Prashanth | 100% |
| 🏗️ Database (Scheduling Tables) | 🟢 COMPLETE | Prashanth | 100% |
| 🏗️ Database (Other Tables) | ⬜ Not Started | Prashanth | 0% |
| 🔐 Authentication | ⬜ Not Started | Akshat + Shaivi | 0% |
| 📄 Resume Parsing | 🟢 COMPLETE | Akshat | 100% |
| 🤖 AI Resume Analysis | ⬜ Not Started | Akshat | 0% |
| 📝 Assessment Backend | 🟢 COMPLETE | Akshat | 100% |
| 📝 Assessment Frontend | 🟡 In Progress | Shaivi | 20% |
| 📧 Email System | ⬜ Not Started | Akshat | 0% |
| 👔 Interviewer APIs | ⬜ Not Started | Akshat | 0% |
| 🎨 Frontend Pages | 🟡 In Progress | Shaivi | 15% |
| 🧪 Integration Testing | 🟡 In Progress | All | 25% |

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

**Task P4: Authentication Tables** ✅  
- Created `users` table with fields: id, email (unique), password_hash, role, name, timestamps
- Added indexes on email and role for fast lookups
- Implemented 3 helper functions:
  - `create_user(email, password_hash, role, name)`
  - `get_user_by_email(email)`
  - `get_user_by_id(user_id)`

**Task P5: Assessment Scheduling Table** ✅  
- Created `scheduled_assessments` table with fields: id, candidate_id, interviewer_id, scheduled_time, status, assessment_id, timestamps
- Added foreign keys to candidates, users, assessments tables
- Added indexes on candidate_id and scheduled_time for fast lookups
- Implemented 4 helper functions:
  - `create_scheduled_assessment(candidate_id, interviewer_id, scheduled_time)`
  - `get_scheduled_assessment(candidate_id)`
  - `update_scheduled_assessment_status(scheduled_assessment_id, status, assessment_id)`
  - `check_assessment_time_valid(candidate_id, current_time)` - validates ±30 min window

**Task P6: Update Existing Tables** ✅  
- Added to `candidates` table: pros, cons, status columns
- Added to `assessments` table: scheduled_assessment_id, hiring_recommendation columns
- Updated helper functions:
  - Modified `insert_candidate()` to accept pros, cons, status parameters
  - Added `update_candidate_status(candidate_id, status, pros, cons)` function
  - Modified `update_assessment_scores()` to accept scheduled_assessment_id and hiring_recommendation

---

### 🔥 URGENT TASKS (Do These Next)

---

### 🟡 OPTIONAL TASKS

**Task P7: Email Logging Table** ✅  
- Created `email_logs` table with fields: id, recipient_email, recipient_name, email_type, subject, status, error_message, sent_at
- Added indexes on recipient_email, email_type, and status for fast lookups
- Implemented 2 helper functions:
  - `log_email(recipient_email, recipient_name, email_type, subject, status, error_message)` - log email attempts
  - `get_candidate_emails(candidate_email)` - retrieve email history for a candidate

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

### 🔥 URGENT TASKS (Do These Next)

**Task A5: JWT Authentication** 🔥  
**Status:** ⬜ TODO

**Requirements:**
- [ ] Install flask-jwt-extended
- [ ] Create endpoints:
  - `POST /api/auth/register` - email, password, role, name
  - `POST /api/auth/login` - validates, returns JWT with role
  - `GET /api/auth/me` - protected, returns user info
- [ ] Use Prashanth's user helper functions
- [ ] Hash passwords before storage

---

**Task A6: AI Pros/Cons Generator** 🔥  
**Status:** ⬜ TODO

**Requirements:**
- [ ] Create function `generate_pros_cons(resume_text, job_requirements, skills, experience)`
- [ ] Integrate Claude/OpenAI API
- [ ] Update `/api/resume/upload` to call this function
- [ ] Store in database using Prashanth's updated table
- [ ] Return pros/cons with match score

---

**Task A7: Email Notification Service** 🔥  
**Status:** ⬜ TODO

**Requirements:**
- [ ] Create `backend/email_service.py`
- [ ] Implement three email functions:
  - `send_rejection_email(candidate_email, candidate_name)`
  - `send_assessment_invitation(candidate_email, candidate_name, assessment_link, scheduled_time)`
  - `send_final_decision_email(candidate_email, candidate_name, decision, rationale)`
- [ ] Use flask-mail or Gmail SMTP/SendGrid
- [ ] Log emails using Prashanth's email_logs table

---

**Task A8: Interviewer Dashboard APIs** 🔥  
**Status:** ⬜ TODO

**Requirements:**
- [ ] Create JWT-protected endpoints (role=interviewer):
  - `GET /api/interviewer/candidates` - list all with data
  - `GET /api/interviewer/candidates/:id` - detailed info
  - `POST /api/interviewer/candidates/:id/reject` - reject + email
  - `POST /api/interviewer/candidates/:id/schedule` - schedule + email
  - `GET /api/interviewer/assessments/:candidate_id` - results + AI recommendation
  - `POST /api/interviewer/assessments/:id/final-decision` - hire/no-hire + email
- [ ] Validate JWT and role
- [ ] Integrate email service

---

### 🟡 MEDIUM PRIORITY TASKS

**Task A9: Assessment Time Validation** 🟡  
**Status:** ⬜ TODO

**Requirements:**
- [ ] Update `POST /api/assessment/start`:
  - Check scheduled assessment exists
  - Validate time within ±30 min window
  - Return 403 if outside window
  - Update status to "in_progress"
- [ ] Create `GET /api/interviewee/my-assessment/:candidate_id`
- [ ] Mark "completed" when finished

---

## 🎨 SHAIVI - FRONTEND TASKS

### ✅ COMPLETED TASKS

**Task S1: React App Setup** ✅  
- Vite + React 18.2 running on port 5173
- Tailwind CSS configured
- React Router setup
- Basic project structure

**Task S2: Resume Upload Page** ✅  
- `UploadPage.jsx` completed (217 lines)
- Drag-and-drop file upload
- Form validation
- Success screen
- **Note:** Needs refactoring to hide scores from interviewees

---

### 🔥 URGENT TASKS (Do These Next)

**Task S3: Landing Page** 🔥  
**Status:** ⬜ TODO

**Requirements:**
- [ ] Create `pages/LandingPage.jsx`
- [ ] Role selection: "I'm an Interviewer" / "I'm an Interviewee"
- [ ] Route to login page (interviewer) or application page (interviewee)

---

**Task S4: Login Page** 🔥  
**Status:** ⬜ TODO

**Requirements:**
- [ ] Create `pages/LoginPage.jsx`
- [ ] Email/password form
- [ ] Call `POST /api/auth/login`
- [ ] Store JWT token in localStorage
- [ ] Redirect to interviewer dashboard on success

---

**Task S5: Authentication Setup** 🔥  
**Status:** ⬜ TODO

**Requirements:**
- [ ] Create `context/AuthContext.jsx` - manage auth state
- [ ] Create `components/ProtectedRoute.jsx` - JWT validation
- [ ] Setup route protection based on role
- [ ] Auto-redirect if not authenticated

---

**Task S6: Interviewer Dashboard** 🔥  
**Status:** ⬜ TODO

**Requirements:**
- [ ] Create `pages/InterviewerDashboardPage.jsx`
- [ ] Call `GET /api/interviewer/candidates`
- [ ] Display table: name, email, match score, status, pros/cons
- [ ] Action buttons: Reject, Schedule Assessment
- [ ] Modal for scheduling (date/time picker)
- [ ] Click candidate to view details

---

**Task S7: Assessment Interface** 🔥  
**Status:** 🟡 IN PROGRESS

**Requirements:**
- [ ] Update `pages/AssessmentPage.jsx`
- [ ] Time validation on load
- [ ] Three sections: MCQ (10 questions), Coding (editor), Psychometric (scenarios)
- [ ] Progress indicator
- [ ] Submit functionality
- [ ] Thank you screen after completion

**Current:** Placeholder (15 lines)

---

### 🟡 MEDIUM PRIORITY TASKS

**Task S8: Refactor Upload Page** 🟡  
**Status:** ⬜ TODO

**Requirements:**
- [ ] Hide match score and parsed data from interviewees
- [ ] Show only confirmation message
- [ ] Update API calls for new flow

---

**Task S9: Assessment Results View** 🟡  
**Status:** ⬜ TODO

**Requirements:**
- [ ] Create view for interviewer to see candidate assessment results
- [ ] Display scores, AI recommendation
- [ ] Show final hire/no-hire decision UI

---

**Task S10: UI/UX Polish** 🟡  
**Status:** ⬜ TODO

**Requirements:**
- [ ] Consistent color scheme
- [ ] Loading spinners
- [ ] Error handling
- [ ] Responsive design
- [ ] Smooth transitions

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


