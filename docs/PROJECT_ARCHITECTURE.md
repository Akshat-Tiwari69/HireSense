# CYGNUSA Elite-Hire - Project Architecture

Complete technical architecture documentation for the AI-Enabled HR Evaluation System.

---

## System Overview

CYGNUSA Elite-Hire is a full-stack AI-enabled hiring platform that streamlines the recruitment process from resume submission to final hiring decision.

### Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Frontend** | React 18 + Vite | Modern SPA with hot reload |
| **UI Framework** | Tailwind CSS + Shadcn UI | Responsive, accessible components |
| **Icons** | Lucide React | Modern icon library |
| **Backend** | Flask (Python 3.8+) | REST API server |
| **Authentication** | Flask-JWT-Extended | JWT token-based auth |
| **Database** | SQLite (dev) / PostgreSQL (prod) | Data persistence |
| **AI Integration** | OpenAI GPT-4o-mini | Resume analysis & scoring |
| **Email Service** | Resend API / SMTP | Automated notifications |
| **Code Execution** | Piston API | Secure code sandbox |
| **File Parsing** | PyPDF2 / python-docx | Resume extraction |

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND (React + Vite)                         │
├─────────────────────────────────────────────────────────────────────────────┤
│  Landing Page  │  Login  │  Apply  │  Dashboard  │  Assessment  │  Proctor  │
│       ↓            ↓          ↓           ↓             ↓            ↓       │
│                        React Router (BrowserRouter)                          │
│                                    ↓                                         │
│                        API Service (Axios + JWT)                             │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │ HTTP/REST
                                   ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                              BACKEND (Flask)                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│  app.py (Main)                                                              │
│      ├── auth_bp (/api/auth/*)          - JWT Authentication                │
│      ├── interviewer_bp (/api/interviewer/*) - Recruiter Dashboard          │
│      ├── interviewee_bp (/api/interviewee/*) - Candidate Assessment         │
│      ├── admin_bp (/api/admin/*)        - Admin Management                  │
│      └── proctor_bp (/api/proctor/*)    - Proctoring Events                 │
├─────────────────────────────────────────────────────────────────────────────┤
│  Services                                                                   │
│      ├── resume_analyzer.py     - OpenAI GPT Integration                    │
│      ├── resume_parser.py       - PDF/DOCX Text Extraction                  │
│      ├── email_service.py       - Email Notifications (Resend/SMTP)         │
│      ├── questions_bank.py      - MCQ/Coding/Psychometric Questions         │
│      └── db_helpers.py          - Database Operations                       │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                                   ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DATABASE                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│  SQLite (Development) / PostgreSQL (Production)                             │
│      ├── users              - Interviewers, Admins, Proctors                │
│      ├── candidates         - Applicants with resume data                   │
│      ├── assessments        - Assessment sessions                           │
│      ├── mcq_responses      - MCQ answers                                   │
│      ├── coding_submissions - Code solutions                                │
│      ├── psychometric_responses - Personality assessments                   │
│      ├── scheduled_assessments - Time-scheduled tests                       │
│      ├── proctoring_events  - Violation tracking                            │
│      └── email_logs         - Email audit trail                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                          EXTERNAL SERVICES                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│  OpenAI API        → Resume Analysis, Pros/Cons Generation                  │
│  Resend/SMTP       → Email Notifications (rejection, invitation, decision) │
│  Piston API        → Secure Code Execution (Python, JavaScript, C++, Java) │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## User Roles & Permissions

### Role Hierarchy

```
Administrator (admin)
    ├── Full system access
    ├── User management
    ├── Job description management
    └── System configuration

Interviewer (interviewer)
    ├── View all candidates
    ├── Schedule assessments
    ├── Reject candidates
    ├── View assessment results
    └── Make hiring decisions

Proctor (proctor)
    ├── Monitor active assessments
    ├── View proctoring events
    └── Flag violations

Candidate (no account required)
    ├── Submit application + resume
    ├── Take scheduled assessment
    └── View assessment completion
```

---

## Core Workflows

### 1. Candidate Application Flow

```
1. Candidate visits Landing Page
           ↓
2. Selects "I'm a Candidate"
           ↓
3. Opens Apply Page → Fills form + Uploads Resume
           ↓
4. Backend: POST /api/resume/upload
   ├── Parse PDF/DOCX text
   ├── Extract: name, email, phone, skills, experience
   ├── Call OpenAI: generate pros, cons, match score
   └── Save to candidates table
           ↓
5. Candidate receives acknowledgment email
           ↓
6. Status: "pending" → awaiting recruiter review
```

### 2. Recruiter Review Flow

```
1. Interviewer logs in → GET /api/auth/login
           ↓
2. Dashboard loads → GET /api/interviewer/candidates
   └── Shows: name, match_score, pros, cons, status
           ↓
3. Review candidate details
           ↓
4a. REJECT → POST /api/interviewer/candidates/:id/reject
    └── Sends rejection email, status → "rejected"
           
4b. SHORTLIST → POST /api/interviewer/candidates/:id/schedule
    └── Creates scheduled_assessment, sends invitation email
    └── Status → "under_review"
```

### 3. Assessment Flow

```
1. Candidate clicks assessment link from email
           ↓
2. Token Verification → GET /api/interviewee/assessment/verify/:token
   └── Checks: token valid, time window (±30 min), not already started
           ↓
3. Start Assessment → POST /api/interviewee/assessment/start-by-token/:token
   └── Returns: mcq_questions, coding_problem, psychometric_scenarios
           ↓
4. Candidate completes sections:
   ├── MCQ: 10 questions with timer
   ├── Coding: Monaco Editor with code execution
   └── Psychometric: 3 scenarios with trait ratings
           ↓
5. Submit each section:
   ├── POST /api/assessment/mcq/submit
   ├── POST /api/assessment/code/submit
   └── POST /api/assessment/psychometric/submit
           ↓
6. Complete → POST /api/assessment/complete
   └── Calculates scores, generates AI recommendation
           ↓
7. Interviewer reviews → GET /api/interviewer/assessments/:candidate_id
           ↓
8. Final Decision → POST /api/interviewer/assessments/:id/final-decision
   └── Sends decision email (hire/no-hire)
```

### 4. Proctoring Flow

```
1. Assessment page initializes camera
           ↓
2. Face detection using face-api.js (client-side)
           ↓
3. Violations detected:
   ├── no_face - Face not visible
   ├── multiple_faces - More than one person
   ├── tab_switch - Browser tab changed
   └── window_blur - Browser window unfocused
           ↓
4. Report violation → POST /api/proctor/report-violation
           ↓
5. Proctor monitors → GET /api/proctor/active-assessments
   └── Can view real-time violations per candidate
```

---

## API Structure

### Endpoint Organization

```
/api
├── /auth                    - Authentication
│   ├── POST /register       - Create user account
│   ├── POST /login          - Get JWT token
│   ├── GET /me              - Current user info
│   └── GET /verify          - Validate token
│
├── /resume
│   └── POST /upload         - Submit resume + AI analysis
│
├── /interviewer             - Protected (interviewer role)
│   ├── GET /candidates      - List all candidates
│   ├── GET /candidates/:id  - Candidate details
│   ├── POST /candidates/:id/reject   - Reject candidate
│   ├── POST /candidates/:id/schedule - Schedule assessment
│   ├── GET /assessments/:id - Assessment results
│   └── POST /assessments/:id/final-decision - Hire/No-hire
│
├── /interviewee             - Candidate endpoints
│   ├── GET /my-assessment/:id          - Check assessment status
│   ├── GET /assessment/verify/:token   - Verify token
│   ├── POST /assessment/start/:id      - Start by candidate ID
│   ├── POST /assessment/start-by-token/:token - Start by token
│   ├── POST /assessment/:id/complete   - Complete assessment
│   └── POST /proctor/report-violation  - Report proctoring event
│
├── /admin                   - Protected (admin role)
│   ├── GET /users           - List all users
│   ├── POST /users          - Create user
│   ├── PUT /users/:id       - Update user
│   ├── DELETE /users/:id    - Delete user
│   ├── GET /job-descriptions - List job descriptions
│   └── POST /job-descriptions - Create job description
│
├── /proctor                 - Protected (proctor role)
│   ├── GET /active-assessments - Current active tests
│   ├── GET /violations/:id  - Violations for assessment
│   └── POST /flag/:id       - Flag assessment for review
│
├── /assessment              - Assessment submission
│   ├── POST /start          - Start assessment
│   ├── POST /mcq/submit     - Submit MCQ answer
│   ├── POST /code/submit    - Submit code solution
│   ├── POST /psychometric/submit - Submit psychometric
│   └── POST /complete       - Complete assessment
│
└── /health                  - Health check
    └── GET /                - Server status
```

---

## Security Architecture

### Authentication Flow

```
1. User submits credentials → POST /api/auth/login
           ↓
2. Server validates password (bcrypt)
           ↓
3. Server generates JWT with claims:
   {
     "sub": user_id,
     "role": "interviewer",
     "name": "Jane Doe",
     "exp": current_time + 24_hours
   }
           ↓
4. Client stores token in localStorage
           ↓
5. Client includes in all requests:
   Authorization: Bearer <token>
           ↓
6. Server validates with @jwt_required() decorator
```

### Security Features

| Feature | Implementation |
|---------|---------------|
| Password Hashing | bcrypt with salt |
| Token Expiration | 24 hours |
| Role-Based Access | JWT claims + decorators |
| CORS Protection | Flask-CORS configured |
| SQL Injection Prevention | Parameterized queries |
| File Upload Validation | Extension whitelist, size limits |

---

## Data Flow

### Resume Upload Data Flow

```
Client                   Server                    External
  │                         │                         │
  ├─ POST resume file ─────→│                         │
  │                         ├─ Extract text ─────────→│ PyPDF2
  │                         │←─ Raw text ────────────│
  │                         │                         │
  │                         ├─ Parse resume ─────────→│ resume_parser
  │                         │←─ Structured data ─────│
  │                         │                         │
  │                         ├─ Analyze resume ───────→│ OpenAI API
  │                         │←─ Pros/Cons/Score ─────│
  │                         │                         │
  │                         ├─ Save to DB ───────────→│ SQLite/PG
  │                         │←─ candidate_id ─────────│
  │                         │                         │
  │                         ├─ Send ack email ───────→│ Resend/SMTP
  │                         │                         │
  │←─ JSON response ────────│                         │
```

### Assessment Scoring

```
MCQ Score = (correct_answers / total_questions) × 100

Coding Score = (test_cases_passed / total_test_cases) × 100

Technical Score = (MCQ × 0.4) + (Coding × 0.6)

Psychometric Score = Average of trait ratings (1-10 scale) × 10

Overall Score = (Technical × 0.6) + (Psychometric × 0.4)
```

---

## Frontend Architecture

### Component Structure

```
src/
├── App.jsx                 # Main router configuration
├── main.jsx                # React entry point
├── pages/
│   ├── LandingPage.jsx     # Home with role selector
│   ├── LoginPage.jsx       # Authentication
│   ├── ApplyPage.jsx       # Candidate application
│   ├── InterviewerDashboardPage.jsx  # Recruiter panel
│   ├── AssessmentPage.jsx  # Full assessment interface
│   ├── AdminDashboardPage.jsx  # Admin panel
│   └── ProctorDashboardPage.jsx  # Proctoring view
├── components/
│   ├── ui/                 # Shadcn UI components
│   └── Logo.jsx            # Branding component
├── services/
│   └── api.js              # Axios instance with JWT
├── hooks/
│   └── use-toast.js        # Toast notifications
└── lib/
    └── utils.js            # Utility functions (cn)
```

### Routing Configuration

```javascript
<Routes>
  <Route path="/" element={<LandingPage />} />
  <Route path="/login" element={<LoginPage />} />
  <Route path="/apply" element={<ApplyPage />} />
  <Route path="/dashboard" element={<InterviewerDashboardPage />} />
  <Route path="/admin" element={<AdminDashboardPage />} />
  <Route path="/proctor" element={<ProctorDashboardPage />} />
  <Route path="/assessment" element={<AssessmentPage />} />
  <Route path="/assessment/:token" element={<AssessmentPage />} />
</Routes>
```

---

## Backend Architecture

### Module Organization

```
backend/
├── app.py                  # Main Flask app, blueprint registration
├── auth.py                 # Authentication blueprint
├── interviewer_routes.py   # Interviewer API endpoints
├── interviewee_routes.py   # Candidate API endpoints
├── admin_routes.py         # Admin API endpoints
├── proctor_routes.py       # Proctoring API endpoints
├── db_helpers.py           # Database operations
├── db_config.py            # Database connection
├── resume_analyzer.py      # OpenAI integration
├── resume_parser.py        # Text extraction
├── email_service.py        # Email notifications
├── questions_bank.py       # Assessment questions
├── init_db.py              # Database initialization
└── schema.sql              # SQLite schema
```

### Blueprint Registration

```python
# app.py
from auth import auth_bp
from interviewer_routes import interviewer_bp
from interviewee_routes import interviewee_bp
from admin_routes import admin_bp
from proctor_routes import proctor_bp

app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(interviewer_bp, url_prefix='/api/interviewer')
app.register_blueprint(interviewee_bp, url_prefix='/api/interviewee')
app.register_blueprint(admin_bp, url_prefix='/api/admin')
app.register_blueprint(proctor_bp, url_prefix='/api/proctor')
```

---

## Deployment Architecture

### Development

```
Frontend:  http://localhost:5173  (Vite dev server)
Backend:   http://localhost:5000  (Flask dev server)
Database:  SQLite (elite_hire.db)
```

### Production (Railway/Render)

```
Frontend:  https://elite-hire.example.com  (Netlify/Vercel)
Backend:   https://api.elite-hire.example.com  (Railway/Render)
Database:  PostgreSQL (managed)
```

### Environment-Specific Configuration

```
Development:
  - DEBUG=True
  - SQLite database
  - Console logging
  - CORS: http://localhost:5173

Production:
  - DEBUG=False
  - PostgreSQL via DATABASE_URL
  - File/service logging
  - CORS: Production frontend URL
```

---

## Performance Considerations

### Caching Strategies
- Resume analysis results cached in database
- JWT validation using in-memory verification
- Static assets served via CDN (production)

### Database Optimization
- Indexes on candidate.email, assessment.candidate_id
- Connection pooling for PostgreSQL
- Parameterized queries for security

### API Rate Limiting (Recommended)
- 100 requests/minute per IP
- 1000 requests/hour per user
- Implement via Flask-Limiter

---

## Monitoring & Logging

### Current Implementation
- Flask built-in logging
- Email logs in database
- Proctoring events stored

### Recommended Additions
- Application performance monitoring (APM)
- Error tracking (Sentry)
- Metrics collection (Prometheus)
- Log aggregation (ELK Stack)

---

## Related Documentation

- [API_DOCS.md](API_DOCS.md) - Complete API reference
- [AUTH_GUIDE.md](AUTH_GUIDE.md) - Authentication system
- [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md) - Database structure
- [FRONTEND_GUIDE.md](FRONTEND_GUIDE.md) - React components
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Production deployment

---

*Last Updated: January 2026*
*Version: 1.0*
