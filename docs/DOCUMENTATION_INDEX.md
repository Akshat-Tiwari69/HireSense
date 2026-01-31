# CYGNUSA Elite-Hire Documentation Index

Complete documentation for the AI-Enabled HR Evaluation System.

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
- [Proctoring System](PROCTOR_GUIDE.md) - Face detection and violation monitoring
- [Admin Dashboard](ADMIN_DASHBOARD_GUIDE.md) - User and job management

### Deployment
- [Deployment Guide](DEPLOYMENT_GUIDE.md) - Production deployment
- [Environment Configuration](ENVIRONMENT_CONFIG.md) - All environment variables

---

## Project Overview

CYGNUSA Elite-Hire is a comprehensive AI-enabled hiring platform that streamlines the recruitment process from resume submission to final hiring decision.

### Key Features

| Feature | Description |
|---------|-------------|
| AI Resume Analysis | OpenAI-powered pros/cons generation |
| Multi-Role System | Interviewer, Admin, Proctor roles |
| Assessment System | MCQ, Coding, Psychometric tests |
| Proctoring | Browser-based face detection |
| Email Notifications | Automated candidate communication |
| Time-Windowed Access | ±30 minute assessment windows |

### Technology Stack

| Layer | Technologies |
|-------|-------------|
| Frontend | React 18, Vite, Tailwind CSS, Shadcn UI |
| Backend | Flask, Flask-JWT-Extended, Flask-CORS |
| Database | SQLite (dev), PostgreSQL (prod) |
| AI | OpenAI GPT-4o-mini |
| Email | Resend API, SMTP |
| Code Execution | Piston API |

---

## Quick Start

### Prerequisites

- Python 3.8+
- Node.js 16+
- OpenAI API key

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Initialize database
python init_db.py

# Start server
python app.py
```

Server runs at: http://localhost:5000

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
echo "VITE_API_BASE_URL=http://localhost:5000" > .env

# Start development server
npm run dev
```

App runs at: http://localhost:5173

### 3. Test the Application

1. Open http://localhost:5173
2. Click "I'm a Candidate" → Apply with resume
3. Login as interviewer: `interviewer@company.com` / `password123`
4. Review candidate in dashboard

---

## Documentation Files

### Architecture & Reference

| Document | Description |
|----------|-------------|
| [PROJECT_ARCHITECTURE.md](PROJECT_ARCHITECTURE.md) | Complete system architecture, data flow, security |
| [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md) | All database tables, relationships, indexes |
| [BACKEND_FILE_REFERENCE.md](BACKEND_FILE_REFERENCE.md) | All Python files with function documentation |
| [FRONTEND_GUIDE.md](FRONTEND_GUIDE.md) | React components, pages, routing |

### API & Features

| Document | Description |
|----------|-------------|
| [API_DOCS.md](API_DOCS.md) | Complete REST API reference with authentication |
| [ASSESSMENT_SYSTEM_GUIDE.md](ASSESSMENT_SYSTEM_GUIDE.md) | MCQ, coding, psychometric tests, time validation |
| [PROCTOR_GUIDE.md](PROCTOR_GUIDE.md) | Proctoring, face detection, violation monitoring |
| [ADMIN_DASHBOARD_GUIDE.md](ADMIN_DASHBOARD_GUIDE.md) | Admin panel, user management, job descriptions |

### Operations

| Document | Description |
|----------|-------------|
| [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) | Production deployment (Railway, Render, Vercel) |
| [ENVIRONMENT_CONFIG.md](ENVIRONMENT_CONFIG.md) | All environment variables reference |

---

## User Workflows

### Candidate Flow

```
Landing Page → Apply → Upload Resume → Receive Email
                               ↓
              Wait for Assessment Invitation
                               ↓
              Assessment Link (±30 min window)
                               ↓
              Take Assessment (MCQ → Coding → Psychometric)
                               ↓
              Receive Decision Email
```

### Interviewer Flow

```
Login → Dashboard → Review Candidates
                         ↓
           View AI Scores & Pros/Cons
                         ↓
        ┌────────────────┴────────────────┐
        ↓                                 ↓
   Reject (Email)              Schedule Assessment (Email)
                                          ↓
                              View Assessment Results
                                          ↓
                              Make Final Decision (Email)
```

### Admin Flow

```
Login → Admin Dashboard
              ↓
    ┌─────────┴─────────┐
    ↓                   ↓
User Management    Job Descriptions
    ↓                   ↓
CRUD Users         CRUD Jobs
```

### Proctor Flow

```
Login → Proctor Dashboard
              ↓
    View Active Assessments
              ↓
    Monitor Violations
              ↓
    Flag for Review
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

### Assessment

```bash
# Verify token
GET /api/interviewee/assessment/verify/:token

# Start assessment
POST /api/interviewee/assessment/start-by-token/:token

# Submit MCQ
POST /api/assessment/mcq/submit
Body: {"assessment_id": 1, "question_id": 1, "answer": 0}

# Complete
POST /api/assessment/complete
Body: {"assessment_id": 1}
```

---

## Environment Variables

### Required

```bash
JWT_SECRET_KEY=<32+ char secret>
OPENAI_API_KEY=sk-...
```

### Optional

```bash
DATABASE_URL=postgresql://...  # Default: SQLite
RESEND_API_KEY=re_...          # Email via Resend
SMTP_HOST=smtp.gmail.com       # Email via SMTP
CORS_ORIGINS=https://...       # Production frontend
```

See [ENVIRONMENT_CONFIG.md](ENVIRONMENT_CONFIG.md) for complete reference.

---

## Support

### Common Issues

| Issue | Solution |
|-------|----------|
| CORS error | Check `CORS_ORIGINS` matches frontend URL |
| JWT invalid | Verify `JWT_SECRET_KEY` is set |
| AI not working | Check `OPENAI_API_KEY` is valid |
| Email not sent | Configure Resend or SMTP |

### Getting Help

1. Check relevant documentation
2. Review error logs
3. Check environment configuration
4. Verify database connection

---

*Documentation Version: 1.0*
*Last Updated: January 2026*
