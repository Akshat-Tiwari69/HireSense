# HireSense — AI-Powered Recruitment Platform

**Case study:** [tiwaribabu.in/projects/hiresense](https://tiwaribabu.in/projects/hiresense)

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
| Assessment Engine | MCQ, coding challenges (Python and JavaScript, run through a Piston code runner), psychometric scenarios |
| Live Proctoring | WebRTC video stream to a proctor, with violation detection (face, tab-switch, window focus, copy-paste, camera loss) |
| Role-Based Dashboards | Admin, hiring review (Interviewer, Recruiter, Sector Admin), Proctor, and a token-based candidate assessment page |
| Email Automation | Assessment invitations, rejections, final decisions |
| Public Demo Mode | Optional `DEMO_MODE` with one-click staff sign-in and a nightly reset |

---

## User Roles

| Role | Access |
|------|--------|
| Admin | Full system — users, candidates, jobs, sectors, question banks, analytics, email and audit logs |
| Super Admin | Admin access, plus creating, editing, and deleting admin and super admin accounts |
| Sector Admin | Scoped to their sector's jobs and candidates |
| Recruiter | Hiring review and job postings within their sector |
| Interviewer | Candidate review, assessment scheduling, final decisions for assigned candidates |
| Proctor | Live session monitoring and violation review |
| Candidate | No account: job listings, application submission, and an emailed assessment link |

---

## Setup

### Prerequisites

- Python 3.12 (CI and production; 3.10 is the minimum)
- Node.js 20–24 and npm 10+
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

# Create the first admin, interviewer, and proctor accounts
python ../database/seed_users.py

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

App runs at `http://localhost:5173`. The Vite dev server proxies `/api` and
`/socket.io` to the backend on port 5000.

---

## Documentation

All documentation lives in `docs/`. Start with the index:

| Document | What it covers |
|----------|----------------|
| [docs/DOCUMENTATION_INDEX.md](docs/DOCUMENTATION_INDEX.md) | Full doc index + quick API reference |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System design, data flows, module responsibilities |
| [docs/BACKEND_FLOW_MAP.md](docs/BACKEND_FLOW_MAP.md) | End-to-end request, database, lifecycle, and failure-boundary map |
| [docs/BACKEND_FILE_REFERENCE.md](docs/BACKEND_FILE_REFERENCE.md) | Every backend Python file and its functions |
| [docs/DATABASE.md](docs/DATABASE.md) | All tables, relationships, indexes |
| [docs/API.md](docs/API.md) | Complete REST API reference with examples |
| [docs/PROCTOR_USER_SETUP.md](docs/PROCTOR_USER_SETUP.md) | Proctor accounts and the proctor dashboard |
| [docs/ROLES.md](docs/ROLES.md) | Role definitions, permissions, access control |
| [docs/DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md) | How production is built and deployed (VPS, Caddy, GitHub Actions) |
| [deploy/README.md](deploy/README.md) | Host setup, secrets, Caddy, and the public demo |
| [database/README.md](database/README.md) | Schema contract, migrations, and validation |
| [docs/SETUP.md](docs/SETUP.md) | All environment variables and local setup |

---

## Production

Production runs on a single VPS: Caddy serves the built React app and proxies
`/api` and `/socket.io` to one Gunicorn/eventlet worker. Pushes to `main` run
the quality checks in GitHub Actions and, when they pass, deploy an immutable
release over SSH. See [docs/DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md).

Known limits of the current deployment:

- The code runner (Piston) is disabled in production, so technical assessments
  with a coding section cannot be scheduled there. Non-technical assessments work.
- WebRTC uses public STUN servers only. Without a TURN server, proctor video can
  fail across restrictive or symmetric NAT networks.
- Live PostgreSQL, email, OpenAI, Piston, and WebRTC behaviour needs real
  external services; `/api/health/ready` returns 503 when PostgreSQL is unreachable.

---

## Branch Strategy

`main` is the only long-lived branch and is deployed automatically. Work happens
on short-lived feature branches that are merged into `main` through pull
requests once the GitHub Actions checks pass.

---

## Quality Checks

```bash
# Frontend: unit tests, lint, dead-code analysis, and production build
cd frontend
npm run check
npm audit

# Backend: tests, static checks, and syntax compilation
cd ../backend
pip install -r requirements-dev.txt
pytest
ruff check .
python -m compileall -q .

# Database: static schema contract check (no database needed)
cd ..
python database/validate_schema.py
```

---

## License

MIT License.
