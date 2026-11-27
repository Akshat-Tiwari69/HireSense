# HireSense Documentation Index

Complete documentation for the AI-Powered Recruitment Platform.

---

## Quick Navigation

### Getting Started
- [Project Overview](#project-overview)
- [Quick Start Guide](#quick-start)
- [Environment Setup](SETUP.md)

### Architecture & Design
- [Project Architecture](ARCHITECTURE.md)
- [Backend Flow Map](BACKEND_FLOW_MAP.md)
- [Database Schema](DATABASE.md)
- [Backend File Reference](BACKEND_FILE_REFERENCE.md)

### API Documentation
- [API Documentation](API.md) - Complete REST API reference with authentication

### Features
- [Roles and Workflows](ROLES.md) - Assessment, hiring, and administration workflows
- [Proctor Setup](PROCTOR_USER_SETUP.md) - Proctor account and monitoring setup

### Deployment
- [Deployment Guide](DEPLOYMENT_GUIDE.md) - How production is built and deployed (VPS, Caddy, GitHub Actions)
- [Host Setup](../deploy/README.md) - Server installation, secrets, and the public demo
- [Environment Configuration](SETUP.md) - Canonical environment variables

---

## Project Overview

HireSense is a full-stack AI-enabled hiring platform that covers the complete recruitment pipeline — from resume submission and AI analysis through technical assessments with live proctoring to final hiring decisions.

### Key Features

| Feature | Description |
|---------|-------------|
| AI Resume Analysis | OpenAI GPT-4o-mini pros/cons generation and match scoring |
| Job Matching | Rule-based + AI re-ranking of candidate-to-job fit |
| Multi-Role System | Super Admin, Admin, Sector Admin, Recruiter, Interviewer, Proctor, Candidate roles |
| Assessment Engine | MCQ, coding challenges (Python and JavaScript), psychometric scenarios |
| Live Proctoring | WebRTC video with in-browser face detection and violation tracking (tab, focus, copy/paste, camera) |
| Email Automation | Assessment invitations, rejections, final decisions |
| Time-Windowed Access | ±30 minute assessment access windows |
| Public Demo Mode | Optional one-click staff sign-in with a nightly data reset |

### Technology Stack

| Layer | Technologies |
|-------|-------------|
| Frontend | React 18, Vite, Tailwind CSS, shadcn/ui, Socket.IO client |
| Backend | Flask 3.0, Flask-JWT-Extended, Flask-Limiter, Flask-CORS, Socket.IO |
| Database | PostgreSQL 15 (Supabase compatible) |
| AI | OpenAI GPT-4o-mini (optional, deterministic fallbacks) |
| Realtime | Socket.IO + WebRTC (simple-peer) |
| Email | Resend API, SMTP fallback |
| Code execution | Piston (disabled in production) |
| Hosting | Single VPS: Caddy + Gunicorn/eventlet, Supabase PostgreSQL |

---

## Quick Start

### Prerequisites

- Python 3.12 (3.10 minimum)
- Node.js 20–24
- PostgreSQL 15+ (or Supabase)
- OpenAI API key (optional; deterministic fallbacks are available)

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate    # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment (see SETUP.md for all variables)
cp .env.example .env

# Initialize a fresh database. Use --reconcile for an existing installation.
python scripts/run_migration.py --schema

# Create the first admin, interviewer, and proctor accounts
python ../database/seed_users.py

# Start server
python run.py
```

Server runs at: `http://localhost:5000`

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure the public backend URL
cp .env.example .env.local

# Start development server
npm run dev
```

App runs at: `http://localhost:5173`

### 3. Test the Application

1. Open `http://localhost:5173/jobs` and apply to a role with a resume
   (create a job posting first from the Admin Dashboard if none exist)
2. Log in as the seeded interviewer
3. Review the candidate in the hiring dashboard at `/dashboard`

---

## Documentation Files

### Architecture & Reference

| Document | Description |
|----------|-------------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | Complete system architecture, data flow, module responsibilities |
| [DATABASE.md](DATABASE.md) | All tables, relationships, indexes, and migration modes |
| [BACKEND_FILE_REFERENCE.md](BACKEND_FILE_REFERENCE.md) | All Python files and their functions |

### API & Features

| Document | Description |
|----------|-------------|
| [API.md](API.md) | Complete REST API reference with authentication |
| [ROLES.md](ROLES.md) | Role permissions and end-to-end workflows |

### Operations

| Document | Description |
|----------|-------------|
| [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) | Production topology, release flow, and environment |
| [../deploy/README.md](../deploy/README.md) | Host installation and the public demo |
| [SETUP.md](SETUP.md) | All environment variables and local setup |
| [PROCTOR_USER_SETUP.md](PROCTOR_USER_SETUP.md) | Proctor accounts and the proctor dashboard |

---

## User Workflows

### Candidate Flow

```
Landing Page → Apply → Upload Resume → Acknowledgement Email
                                              ↓
                              Wait for Assessment Invitation
                                              ↓
                              Click Assessment Link (±30 min window)
                                              ↓
                              Complete Assessment (MCQ → Coding → Psychometric)
                                              ↓
                              Receive Final Decision Email
```

### Interviewer Flow

```
Login → Hiring Dashboard → Review Candidates
                          ↓
            View AI Match Scores & Pros/Cons
                          ↓
         ┌────────────────┴────────────────┐
         ↓                                 ↓
    Reject (Email sent)         Schedule Assessment (Email sent)
                                           ↓
                               View Assessment Results
                                           ↓
                               Make Final Decision (Email sent)
```

### Admin Flow

```
Login → Admin Dashboard
               ↓
     ┌─────────┼──────────┐
     ↓         ↓          ↓
User Mgmt  Job Mgmt   Analytics, Email & Audit Logs
     ↓         ↓
  CRUD       CRUD Jobs, Sectors,
  Users      Bulk Upload, Question Banks
```

### Proctor Flow

```
Login → Proctor Dashboard
               ↓
   View Active Assessment Sessions
               ↓
   Claim a Session → Monitor Live Video
               ↓
   Review Violations and Screenshot Evidence
```

---

## API Quick Reference

### Authentication

```bash
# Login
POST /api/auth/login
Body: {"email": "...", "password": "..."}

# Verify Token
GET /api/auth/verify
Headers: Authorization: Bearer <token>
```

### Resume Upload

```bash
POST /api/resume/upload
Content-Type: multipart/form-data
Body: file, job_id, name, email, phone (optional)
```

The public success response contains only `candidate_id`, `application_status`,
and the selected job ID/title. Parsed resume and AI-review details remain private
to authorized hiring staff.

### Interviewer Actions

```bash
# List candidates
GET /api/interviewer/candidates

# Schedule assessment
POST /api/interviewer/candidates/:id/schedule
Body: {"scheduled_time": "2026-01-25T14:00:00"}

# Make decision
POST /api/interviewer/assessments/:id/final-decision
Body: {"decision": "hire", "rationale": "...", "next_steps": "..."}
```

### Assessment (Candidate)

```bash
# All candidate calls send: X-Assessment-Token: <token from the link>

# Verify token
GET /api/interviewee/assessment/verify

# Start assessment
POST /api/interviewee/assessment/start

# Submit MCQ answer
POST /api/interviewee/assessment/:id/submit-answer
Body: {"type": "mcq", "questionId": 1, "answer": "A", "timeSpent": 30}

# Complete assessment
POST /api/interviewee/assessment/:id/complete
```

---

## Environment Variables

### Required

```bash
DATABASE_URL=postgresql://user:pass@host:5432/dbname
JWT_SECRET_KEY=<32+ character random string>
APP_ENV=development            # unset means production rules
```

### Optional

```bash
OPENAI_API_KEY=sk-...          # AI features (deterministic fallbacks without it)
RESEND_API_KEY=re_...          # Email via Resend API
SMTP_HOST=smtp.gmail.com       # Email via SMTP (fallback)
CORS_ORIGINS=https://...       # Restrict CORS in production
```

See [SETUP.md](SETUP.md) and the canonical templates in `backend/.env.example`
and `frontend/.env.example` for the complete reference.

---

## Common Issues

| Issue | Solution |
|-------|----------|
| CORS error | Check `CORS_ORIGINS` matches the frontend URL |
| JWT invalid | Verify `JWT_SECRET_KEY` is set and matches between restarts |
| AI not working | Check `OPENAI_API_KEY` is valid and has credits; without it, rule-based fallbacks are used |
| Email not sending | Configure either `RESEND_API_KEY` or SMTP variables |
| DB connection failed | Verify `DATABASE_URL` format: `postgresql://user:pass@host/db` |

---

*Last Updated: November 2026*
