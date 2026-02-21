# HireSense
[Repository](https://github.com/Akshat-Tiwari69/HireSense) • [Issues](https://github.com/Akshat-Tiwari69/HireSense/issues)

An AI-powered recruitment and assessment platform that automates hiring
workflows — from resume intake and job matching to live-proctored technical
assessments with real-time video monitoring.

![Python](https://img.shields.io/badge/Python-3.9+-3776AB?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0-000000?logo=flask)
![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-4169E1?logo=postgresql&logoColor=white)
![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-3.4-06B6D4?logo=tailwindcss&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-412991?logo=openai&logoColor=white)

---

## Overview

HireSense is a full-stack recruitment platform built for companies
that need a structured, secure, and intelligent hiring pipeline. It combines
AI-driven candidate evaluation with a multi-role dashboard system and a
live-proctored assessment engine.

**Key capabilities:**

- AI resume analysis and job matching powered by OpenAI GPT-4o-mini
- Three-part technical assessments (MCQ, coding challenges, psychometric)
- Live proctoring with WebRTC video streaming and violation detection
- Role-based access control across five user roles
- Automated email notifications for every stage of the hiring pipeline

## Features

### AI-powered recruitment

- **Resume analysis** — Upload PDF/DOCX resumes for automatic skill
  extraction, experience parsing, and AI-generated pros/cons evaluation
  with match scoring against job requirements.
- **Job matching engine** — Rule-based scoring combined with AI re-ranking
  to match candidates to open positions by skills, experience, and
  education.
- **Question generation** — AI-generated MCQs, coding problems, and test
  cases tailored to each candidate's resume and the target role.

### Assessment system

- **MCQ section** — Technical multiple-choice questions covering algorithms,
  data structures, web development, and more.
- **Coding challenges** — Multi-language support (Python, JavaScript, Java)
  with an integrated Monaco code editor, starter code, and automated test
  cases at easy, medium, and hard difficulty levels.
- **Psychometric evaluation** — Scenario-based trait assessment for
  teamwork, responsibility, and decision-making.
- **Secure access** — Token-based assessment links with a ±30-minute
  scheduling window and time-elapsed tracking.

### Live proctoring

- **Real-time video monitoring** — WebRTC peer-to-peer streaming from
  candidate to proctor via Socket.IO signaling.
- **Violation detection** — Tracks tab switches, copy-paste attempts,
  face detection anomalies (no face / multiple faces), and captures
  screenshots as evidence.
- **Room-based architecture** — Each assessment runs in an isolated
  session with automatic cleanup on disconnect.

### Multi-role dashboards

| Role | Capabilities |
|------|-------------|
| **Admin** | Full system control, user management, analytics, bulk operations |
| **Sector Admin** | Sector-scoped job and candidate management |
| **Interviewer** | Candidate review, assessment scheduling, email notifications |
| **Proctor** | Live session monitoring, violation tracking, assessment oversight |
| **Candidate** | Job applications, resume submission, assessment participation |

### Email automation

- Assessment invitations with secure token links
- Rejection notices with optional feedback
- Final hiring decisions
- Dual transport (Resend API with SMTP fallback) and full audit logging

## Tech stack

### Backend

| Technology | Purpose |
|-----------|---------|
| Python 3.9+ / Flask 3.0 | REST API framework |
| Flask-JWT-Extended | JWT authentication with 24-hour token expiry |
| PostgreSQL (psycopg2) | Database with connection pooling |
| Socket.IO + eventlet | Real-time WebSocket communication |
| OpenAI GPT-4o-mini | AI resume analysis, question generation, job matching |
| Resend / SMTP | Email delivery |
| PyPDF2, python-docx | Resume parsing |
| Gunicorn | Production WSGI server |
| bcrypt | Password hashing |

### Frontend

| Technology | Purpose |
|-----------|---------|
| React 18 + Vite 5 | UI framework and build tooling |
| React Router DOM 7 | Client-side routing |
| Tailwind CSS 3 | Utility-first styling |
| Radix UI + shadcn/ui | Accessible component library |
| Monaco Editor | In-browser code editor for assessments |
| Recharts | Data visualization and analytics |
| Socket.IO Client + simple-peer | WebRTC proctoring |
| Zod + React Hook Form | Form validation |
| Axios | HTTP client |

## Project structure

```
hiresense/
├── backend/
│   ├── app.py                  # Application entry point
│   ├── auth.py                 # Authentication endpoints
│   ├── admin_routes.py         # Admin dashboard API
│   ├── interviewer_routes.py   # Interviewer dashboard API
│   ├── interviewee_routes.py   # Candidate assessment API
│   ├── proctor_routes.py       # Proctoring API
│   ├── job_routes.py           # Job postings and matching API
│   ├── db_config.py            # Connection pool configuration
│   ├── db_helpers.py           # Data access layer with caching
│   ├── resume_parser.py        # Resume text extraction
│   ├── resume_analyzer.py      # AI-powered resume evaluation
│   ├── job_matcher.py          # AI job matching engine
│   ├── ai_question_generator.py# AI assessment question generator
│   ├── questions_bank.py       # Static question repository
│   ├── email_service.py        # Email notification service
│   ├── websocket_server.py     # Socket.IO / WebRTC signaling
│   ├── rate_limiter.py         # Request rate limiting
│   ├── security_headers.py     # HTTP security headers
│   ├── request_logger.py       # Request logging middleware
│   └── requirements.txt        # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── pages/              # 11 route pages
│   │   ├── components/         # Reusable UI components
│   │   ├── services/           # API client
│   │   ├── hooks/              # Custom React hooks
│   │   ├── context/            # Theme and auth providers
│   │   └── lib/                # Utility functions
│   ├── package.json
│   └── vite.config.js
├── database/
│   ├── schema_postgresql.sql   # Full database schema
│   └── migrations/             # Incremental migrations
└── docs/
    ├── API.md                  # API reference
    ├── ARCHITECTURE.md         # System architecture
    ├── DATABASE.md             # Schema documentation
    └── SETUP.md                # Installation guide
```

## Quick start

### Prerequisites

- Python 3.9 or higher
- Node.js 16.0 or higher
- PostgreSQL database (local or Supabase)
- OpenAI API key (for AI features)

### Backend setup

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

Create a `backend/.env` file:

```properties
DATABASE_URL=postgresql://user:password@host:5432/dbname
SECRET_KEY=your_flask_secret_key
JWT_SECRET_KEY=your_jwt_signing_key
OPENAI_API_KEY=your_openai_api_key

# Email (optional)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

Initialize the database and start the server:

```bash
psql "$DATABASE_URL" -f ../database/schema_postgresql.sql
python app.py
```

The API runs at `http://localhost:5000`.

### Frontend setup

```bash
cd frontend
npm install
```

Create a `frontend/.env` file:

```properties
VITE_API_BASE_URL=http://localhost:5000
```

Start the development server:

```bash
npm run dev
```

The UI runs at `http://localhost:5173`.

## API overview

All endpoints return standardized JSON responses:

```json
{
  "status": "success",
  "message": "Description",
  "data": { }
}
```

| Blueprint | Prefix | Description |
|----------|--------|-------------|
| Auth | `/api/auth` | Registration, login, JWT management |
| Admin | `/api/admin` | System administration and analytics |
| Interviewer | `/api/interviewer` | Candidate management and scheduling |
| Interviewee | `/api/interviewee` | Assessment access and submission |
| Proctor | `/api/proctor` | Live proctoring and monitoring |
| Jobs | `/api/jobs` | Job postings, sectors, and matching |

For the complete endpoint reference, see [docs/API.md](docs/API.md).

## Security

- **Authentication** — JWT tokens with configurable expiry and automatic
  refresh error handling.
- **Authorization** — Role-based access control (RBAC) with a hierarchical
  permission model across five roles.
- **Data protection** — Parameterized SQL queries, input validation,
  secure filename sanitization, and 10 MB upload limits.
- **HTTP hardening** — Content-Security-Policy, X-Frame-Options,
  X-Content-Type-Options, Referrer-Policy, and Permissions-Policy headers.
- **Rate limiting** — Configurable per-endpoint limits (200/day default,
  10/min login, 5/min register, 10/hr upload).
- **Password storage** — bcrypt hashing via werkzeug.

## Database

The platform uses PostgreSQL with 12 tables covering users, candidates,
assessments, proctoring events, email logs, and audit trails. JSONB columns
provide flexible storage for questions and assessment data.

For the full schema and entity-relationship diagram, see
[docs/DATABASE.md](docs/DATABASE.md).

## Deployment

The project includes configuration for cloud deployment on platforms like
Railway, Render, or Heroku.

- **Backend** — Gunicorn WSGI server via `Procfile`, with Nixpacks
  configuration for automated builds.
- **Frontend** — Vite production build with static hosting support.
- **Database** — Compatible with Supabase PostgreSQL, with connection
  pooling tuned for free-tier limits (2-5 connections).

## Documentation

| Document | Description |
|---------|-------------|
| [docs/SETUP.md](docs/SETUP.md) | Installation and configuration guide |
| [docs/API.md](docs/API.md) | Complete API endpoint reference |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System design and architecture |
| [docs/DATABASE.md](docs/DATABASE.md) | Database schema and ERD |

## License

This project is proprietary. All rights reserved.
