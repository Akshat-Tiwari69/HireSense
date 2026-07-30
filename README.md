# HireSense — AI-Powered Recruitment Platform

> **Team:** Akshat (Backend) | Shaivi (Frontend) | Prashanth (Database)

HireSense is a full-stack AI-enabled hiring platform that handles the complete recruitment pipeline — from resume submission and AI analysis through technical assessments with live proctoring to final hiring decisions.

---

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| Frontend | React 18, Vite, Tailwind CSS, shadcn/ui |
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
| Super Admin | Admin access plus privileged user and development-setting controls |
| Sector Admin | Scoped to their sector's jobs and candidates |
| Recruiter | Candidate and job workflow access without system administration |
| Interviewer | Candidate review, assessment scheduling, final decisions |
| Proctor | Live session monitoring, violation reporting |
| Candidate | Job listings, application submission, assessment |

---

## Setup

### Prerequisites

- Python 3.9+
- Node.js 20
- PostgreSQL 15+ (or a Supabase project)
- OpenAI API key (optional; deterministic fallbacks are built in)

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

# Initialize a fresh database. For an existing installation, use --reconcile.
python scripts/run_migration.py --schema

# Start server (development)
python run.py
```

Server runs at `http://localhost:5000`

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Create .env.local from the public frontend template
cp .env.example .env.local
npm run dev
```

App runs at `http://localhost:5173`

---

## Documentation

Start with the [GitHub Wiki](https://github.com/Akshat-Tiwari69/HireSense/wiki)
or use the source documents in `docs/`:

| Document | What it covers |
|----------|----------------|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System design, data flows, module responsibilities |
| [docs/BACKEND_FLOW_MAP.md](docs/BACKEND_FLOW_MAP.md) | End-to-end request, database, lifecycle, and failure-boundary map |
| [docs/BACKEND_FILE_REFERENCE.md](docs/BACKEND_FILE_REFERENCE.md) | Every backend Python file and its functions |
| [docs/DATABASE.md](docs/DATABASE.md) | All tables, relationships, indexes |
| [docs/API.md](docs/API.md) | Complete REST API reference with examples |
| [docs/PROCTOR_USER_SETUP.md](docs/PROCTOR_USER_SETUP.md) | WebRTC proctoring, face detection, violations |
| [docs/ROLES.md](docs/ROLES.md) | Role definitions, permissions, access control |
| [docs/DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md) | Railway / Render / Vercel deployment |
| [docs/SETUP.md](docs/SETUP.md) | All environment variables and local setup |

---

## Refactoring and Hardening Status

The whole-project cleanup is complete on the current review branch:

- Database access is split into focused user, candidate, assessment, proctoring, and email modules.
- Admin and interviewee routes are composed from smaller domain blueprints.
- The PostgreSQL schema, dated reconciliation migration, and application field usage share one canonical contract.
- Assessment scheduling, scoring, completion, and final decisions use transaction and concurrency guards.
- Resume/archive/question ingestion is bounded and validates real file/container structure.
- JWT role changes, assessment capability tokens, private uploads, and proctor evidence are protected end to end.
- Frontend lint, dead-code analysis, dependency audit, and production build are part of `npm run check`.
- The backend regression suite covers route contracts, transactions, provider fallbacks, and security boundaries.

Live PostgreSQL, email, AI-provider, Piston, and WebRTC checks still require valid external services; readiness remains 503 when PostgreSQL is unavailable.

---

## Branch Strategy

| Branch | Purpose |
|--------|---------|
| `main` | Production-stable code only |
| `dev` | Integration branch — all features and refactoring go here first |

PRs from `dev` → `main` are reviewed before merging.

---

## Quality Checks

```bash
# Frontend: lint, dead-code analysis, and production build
cd frontend
npm run check
npm audit

# Backend: tests, static checks, and syntax compilation
cd ../backend
pip install -r requirements-dev.txt
pytest
ruff check .
python -m compileall -q .
```

---

## License

MIT License.
