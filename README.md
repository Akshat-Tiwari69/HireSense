# HireSense — AI-Powered Recruitment Platform

> **Team:** Akshat (Backend) | Shaivi (Frontend) | Prashanth (Database)

HireSense is a full-stack AI-enabled hiring platform that handles the complete recruitment pipeline — from resume submission and AI analysis through technical assessments with live proctoring to final hiring decisions.

---

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| Frontend | React 18, Vite, Tailwind CSS, shadcn/ui, Recharts |
| Backend | Flask 3.0, Flask-JWT-Extended, Flask-Limiter, Flask-CORS |
| Database | PostgreSQL 15 (Supabase compatible) |
| AI | OpenAI GPT-4o-mini (resume analysis, question generation, job matching) |
| Realtime | Socket.IO + WebRTC (live proctoring) |
| Email | Resend API with SMTP fallback |

---

## What It Does

| Feature | Description |
|---------|-------------|
| Resume Parsing & AI Analysis | Extracts skills/experience, generates pros/cons and match scores |
| Job Matching | Rule-based + AI re-ranking of candidate-to-job fit |
| Assessment Engine | MCQ, coding challenges (multi-language), psychometric tests |
| Live Proctoring | WebRTC video stream with violation detection (face, tab-switch, copy-paste) |
| Role-Based Dashboards | Admin, Sector Admin, Interviewer, Proctor, Candidate |
| Email Automation | Assessment invitations, rejections, final decisions |

---

## User Roles

| Role | Access |
|------|--------|
| Admin | Full system — users, candidates, jobs, sectors, analytics |
| Sector Admin | Scoped to their sector's jobs and candidates |
| Interviewer | Candidate review, assessment scheduling, final decisions |
| Proctor | Live session monitoring, violation reporting |
| Candidate | Job listings, application submission, assessment |

---

## Setup

### Prerequisites

- Python 3.9+
- Node.js 18+
- PostgreSQL 15+ (or a Supabase project)
- OpenAI API key

### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate    # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file — see docs/SETUP.md for all variables
cp .env.example .env        # then fill in values

# Run database migrations
python scripts/run_migration.py

# Start server (development)
python app.py
```

Server runs at `http://localhost:5000`

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Create .env.local — minimum required:
# VITE_API_BASE_URL=http://localhost:5000
npm run dev
```

App runs at `http://localhost:5173`

---

## Documentation

All documentation lives in `docs/`. Start with the index:

| Document | What it covers |
|----------|----------------|
| [docs/DOCUMENTATION_INDEX.md](docs/DOCUMENTATION_INDEX.md) | Full doc index + quick API reference |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System design, data flows, module responsibilities |
| [docs/BACKEND_FILE_REFERENCE.md](docs/BACKEND_FILE_REFERENCE.md) | Every backend Python file and its functions |
| [docs/DATABASE.md](docs/DATABASE.md) | All tables, relationships, indexes |
| [docs/API.md](docs/API.md) | Complete REST API reference with examples |
| [docs/PROCTOR_USER_SETUP.md](docs/PROCTOR_USER_SETUP.md) | WebRTC proctoring, face detection, violations |
| [docs/ROLES.md](docs/ROLES.md) | Role definitions, permissions, access control |
| [docs/DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md) | Railway / Render / Vercel deployment |
| [docs/SETUP.md](docs/SETUP.md) | All environment variables and local setup |

---

## Current Development Status

### What's Working (on `main`)
- Full candidate application flow
- AI resume analysis and job matching
- Assessment engine (MCQ, coding, psychometric)
- Live proctoring with WebRTC
- Role-based access for all 5 roles
- Email automation (Resend + SMTP fallback)
- Admin dashboard with analytics

### Active Refactoring (on `dev`)
The codebase is being restructured to make it maintainable long-term.
See the [refactoring plan](#refactoring-plan) below.

---

## Refactoring Plan

The project has several large files that are hard to maintain. We are splitting them into focused modules, one phase at a time. All changes go to `dev` branch first.

### Phase 1 — Backend DB split (done)

`backend/db_helpers.py` was 1,820 lines containing every database query for every domain. It has been split into:

| Module | Responsibility |
|--------|---------------|
| `backend/user_db.py` | User auth queries |
| `backend/candidate_db.py` | Candidate CRUD |
| `backend/assessment_db.py` | Assessments, responses, scoring, scheduling, token access |
| `backend/proctoring_db.py` | Violation recording and event logging |
| `backend/email_db.py` | Email log reads/writes |

`db_helpers.py` is now a thin re-export hub — all existing imports in other files continue to work unchanged.

### Phase 2 — Backend route split (upcoming)

| File | Lines | Plan |
|------|-------|------|
| `admin_routes.py` | 1,815 | Split into `routes/admin_users.py`, `routes/admin_jobs.py`, `routes/admin_analytics.py` |
| `interviewee_routes.py` | 1,217 | Split by assessment section |
| `app.py` | 1,081 | Extract resume endpoints into their own blueprint |

### Phase 3 — Frontend component split (upcoming)

| File | Lines | Plan |
|------|-------|------|
| `AdminDashboardPage.jsx` | 2,602 | Extract 6 tab-level sub-components |
| `AssessmentPage.jsx` | 1,654 | Extract `MCQSection`, `CodingSection`, `PsychometricSection` |
| `InterviewerDashboardPage.jsx` | 1,025 | Extract modal and list components |

### Phase 4 — Tests and CI (upcoming)

- Backend: `pytest` fixtures for every route file
- Frontend: Vitest for critical components
- GitHub Actions: lint → test → build pipeline

---

## Branch Strategy

| Branch | Purpose |
|--------|---------|
| `main` | Production-stable code only |
| `dev` | Integration branch — all features and refactoring go here first |

PRs from `dev` → `main` are reviewed before merging.

---

## License

MIT License — see [LICENSE](LICENSE) for details.
