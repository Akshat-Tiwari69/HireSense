# HireSense Documentation Index

Complete documentation for the AI-Powered Recruitment Platform.

---

## Quick Navigation

### Getting Started
- [Project Overview](#project-overview)
- [Quick Start Guide](#quick-start)
- [Environment Setup](ENVIRONMENT_CONFIG.md)

### Architecture & Design
- [Project Architecture](PROJECT_ARCHITECTURE.md)
- [Database Schema](DATABASE_SCHEMA.md)
- [Backend File Reference](BACKEND_FILE_REFERENCE.md)
- [Frontend Guide](FRONTEND_GUIDE.md)

### API Documentation
- [API Documentation](API_DOCS.md) - Complete REST API reference with authentication

### Features
- [Assessment System](ASSESSMENT_SYSTEM_GUIDE.md) - MCQ, Coding, Psychometric tests
- [Proctoring System](PROCTOR_GUIDE.md) - WebRTC face detection and violation monitoring
- [Admin Dashboard](ADMIN_DASHBOARD_GUIDE.md) - User and job management

### Deployment
- [Deployment Guide](DEPLOYMENT_GUIDE.md) - Production deployment (Railway, Render, Vercel)
- [Environment Configuration](ENVIRONMENT_CONFIG.md) - All environment variables

---

## Project Overview

HireSense is a full-stack AI-enabled hiring platform that covers the complete recruitment pipeline — from resume submission and AI analysis through technical assessments with live proctoring to final hiring decisions.

### Key Features

| Feature | Description |
|---------|-------------|
| AI Resume Analysis | OpenAI GPT-4o-mini pros/cons generation and match scoring |
| Job Matching | Rule-based + AI re-ranking of candidate-to-job fit |
| Multi-Role System | Admin, Sector Admin, Interviewer, Proctor, Candidate roles |
| Assessment Engine | MCQ, Coding challenges (multi-language), Psychometric tests |
| Live Proctoring | WebRTC video with face detection and violation tracking |
| Email Automation | Assessment invitations, rejections, final decisions |
| Time-Windowed Access | ±30 minute assessment access windows |

### Technology Stack

| Layer | Technologies |
|-------|-------------|
| Frontend | React 18, Vite, Tailwind CSS, shadcn/ui, Recharts, Socket.IO client |
| Backend | Flask 3.0, Flask-JWT-Extended, Flask-Limiter, Flask-CORS, Socket.IO |
| Database | PostgreSQL 15 (Supabase compatible) |
| AI | OpenAI GPT-4o-mini |
| Realtime | Socket.IO + WebRTC (simple-peer) |
| Email | Resend API, SMTP fallback |

---

## Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+
- PostgreSQL 15+ (or Supabase)
- OpenAI API key

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate    # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment (see ENVIRONMENT_CONFIG.md for all variables)
cp .env.example .env

# Run database migrations
python scripts/run_migration.py

# Start server
python app.py
```

Server runs at: `http://localhost:5000`

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
echo "VITE_API_BASE_URL=http://localhost:5000" > .env.local

# Start development server
npm run dev
```

App runs at: `http://localhost:5173`

### 3. Test the Application

1. Open `http://localhost:5173`
2. Click "I'm a Candidate" → Apply with a resume
3. Login as an interviewer using credentials created via the admin panel
4. Review the candidate in the interviewer dashboard

---

## Documentation Files

### Architecture & Reference

| Document | Description |
|----------|-------------|
| [PROJECT_ARCHITECTURE.md](PROJECT_ARCHITECTURE.md) | Complete system architecture, data flow, module responsibilities |
| [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md) | All tables, relationships, indexes |
| [BACKEND_FILE_REFERENCE.md](BACKEND_FILE_REFERENCE.md) | All Python files and their functions |
| [FRONTEND_GUIDE.md](FRONTEND_GUIDE.md) | React components, pages, routing |

### API & Features

| Document | Description |
|----------|-------------|
| [API_DOCS.md](API_DOCS.md) | Complete REST API reference with authentication |
| [ASSESSMENT_SYSTEM_GUIDE.md](ASSESSMENT_SYSTEM_GUIDE.md) | MCQ, coding, psychometric tests |
| [PROCTOR_GUIDE.md](PROCTOR_GUIDE.md) | Proctoring, face detection, violation monitoring |
| [ADMIN_DASHBOARD_GUIDE.md](ADMIN_DASHBOARD_GUIDE.md) | Admin panel, user management, job descriptions |

### Operations

| Document | Description |
|----------|-------------|
| [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) | Production deployment (Railway, Render, Vercel) |
| [ENVIRONMENT_CONFIG.md](ENVIRONMENT_CONFIG.md) | All environment variables reference |
| [PROCTOR_USER_SETUP.md](PROCTOR_USER_SETUP.md) | Creating proctor accounts |

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
Login → Dashboard → Review Candidates
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
User Mgmt  Job Mgmt   Analytics
     ↓         ↓
  CRUD       CRUD
  Users      Jobs
```

### Proctor Flow

```
Login → Proctor Dashboard
               ↓
   View Active Assessment Sessions
               ↓
   Monitor Live Video Feeds
               ↓
   Review & Record Violations
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
Body: file, name, email, phone
```

### Interviewer Actions

```bash
# List candidates
GET /api/interviewer/candidates

# Schedule assessment
POST /api/interviewer/candidates/:id/schedule
Body: {"scheduled_time": "2026-01-25T14:00:00"}

# Make decision
POST /api/interviewer/assessments/:id/final-decision
Body: {"decision": "hire", "rationale": "..."}
```

### Assessment (Candidate)

```bash
# Verify token
GET /api/interviewee/assessment/verify/:token

# Start assessment
POST /api/interviewee/assessment/start-by-token/:token

# Submit MCQ answer
POST /api/assessment/mcq/submit
Body: {"assessment_id": 1, "question_id": 1, "answer": 0}

# Complete assessment
POST /api/assessment/complete
Body: {"assessment_id": 1}
```

---

## Environment Variables

### Required

```bash
DATABASE_URL=postgresql://user:pass@host:5432/dbname
JWT_SECRET_KEY=<32+ character random string>
OPENAI_API_KEY=sk-...
```

### Optional

```bash
RESEND_API_KEY=re_...          # Email via Resend API
SMTP_HOST=smtp.gmail.com       # Email via SMTP (fallback)
CORS_ORIGINS=https://...       # Restrict CORS in production
```

See [ENVIRONMENT_CONFIG.md](ENVIRONMENT_CONFIG.md) for the complete reference.

---

## Common Issues

| Issue | Solution |
|-------|----------|
| CORS error | Check `CORS_ORIGINS` matches the frontend URL |
| JWT invalid | Verify `JWT_SECRET_KEY` is set and matches between restarts |
| AI not working | Check `OPENAI_API_KEY` is valid and has credits |
| Email not sending | Configure either `RESEND_API_KEY` or SMTP variables |
| DB connection failed | Verify `DATABASE_URL` format: `postgresql://user:pass@host/db` |

---

*Last Updated: May 2026*
