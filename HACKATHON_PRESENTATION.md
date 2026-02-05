# HireSense - Hackathon Presentation Scripts

## 🎯 Project Overview
**HireSense** - Intelligent hiring platform with AI resume analysis, automated assessments, and real-time proctoring.

---

## 👨‍💻 FRONTEND ENGINEER (2 minutes)
**Shaivi**

"Hi! I'm Shaivi. I built our React frontend with real-time proctoring and AI-powered interfaces.

**Tech Stack**: React 18, Vite, Tailwind CSS, Socket.IO, Supabase Realtime

**Key Features:**

**1. Role-Based Dashboards**
Three interfaces - Admin, Interviewer, Candidate - each optimized with lazy loading and infinite scroll for thousands of users.

**2. AI Resume Analysis** *[Demo upload]*
Upload a resume, get instant AI analysis - skills, experience, pros/cons, ATS score. Uses optimistic rendering for instant feedback.

**3. Live Proctoring** *[Demo camera]*
Our crown jewel - custom JavaScript computer vision algorithm that:
- Detects 0, 1, or multiple faces in real-time
- Catches tab switches using Page Visibility API
- Auto-captures violation screenshots
- Streams live to interviewers via WebRTC
All client-side processing for privacy.

**4. Assessment Interface**
Three stages (MCQs, Coding, Psychometric) with Monaco Editor, real-time execution, auto-save, and time warnings. Mobile-responsive.

**Technical Challenge**: Built a custom **skin-tone clustering algorithm** for face detection - analyzes vertical stripes, detects density peaks, runs every 3s without performance impact. No ML libraries needed.

60fps, sub-100ms interactions, real-time data from three sources. Thank you!"

---

## ⚙️ BACKEND ENGINEER (2 minutes)
**Akshat**

"Hello! I'm Akshat, backend architect. Built a Flask API that powers end-to-end hiring.

**Architecture**: Python Flask, PostgreSQL, Railway deployment. JWT auth, Google Gemini AI, Socket.IO, Resend API.

**Key Features:**

**1. AI Resume Pipeline** *[Show terminal]*
Upload → Parse (PyPDF2) → AI analysis (Gemini) → Extract JSON → Database → Email notification. Complete in under 5 seconds. Rate limiting, retries, and fallbacks built-in.

**2. Smart Assessment System**
- AI generates role-specific coding problems
- Secure token-based access with expiration
- Time-window validation
- Auto-grading for MCQs, test-case evaluation for code
- Progress auto-saves with conflict resolution
- Handles disconnections and crashes gracefully

**3. Real-time Proctoring** *[Show WebSocket logs]*
- WebSocket server managing bidirectional streams
- Room-based architecture (each assessment = one room)
- Violation logging: tab switches, multiple faces, screenshots
- Base64 image decoding and filesystem storage
- Direct peer-to-peer video streaming

**4. Security**
JWT with refresh tokens, SQL injection prevention (parameterized queries), rate limiting, CORS, bcrypt passwords, token expiration (1hr access, 7-day refresh).

**Technical Challenge**: Race conditions in submission flow. Solved with **idempotency keys**, **database unique constraints**, and **optimistic locking**. Zero duplicates under stress testing.

**Performance**: 200+ concurrent WebSockets, 50 req/sec sustained, 120ms avg response, P99 under 500ms. Single Railway container with connection pooling. Thank you!"

---

## 🗄️ DATABASE ENGINEER (2 minutes)
**Prashanth**

"Hi! I'm Prashanth. I designed the database that powers HireSense.

**Architecture**: Supabase PostgreSQL, **11 tables**, 3rd Normal Form. Users (multi-role), Candidates, Assessments, 3 response tables, Violations, Scheduled assessments, Email logs.

**Key Features:**

**1. Performance Optimization** *[Show EXPLAIN]*
- Composite indexes on (candidate_id, created_at)
- B-tree on foreign keys, GIN on JSONB columns
- Partial indexes on status fields
- Connection pooling with pgBouncer
- **Result**: Most complex queries under 50ms, dashboard loads in 32ms with 10,000+ records

**2. Advanced PostgreSQL**
- **Realtime subscriptions** - Violations appear instantly for interviewers
- **JSONB for flexibility** - Skills as arrays, query with `@>` operator
- **Row Level Security** - Candidates see only their data
- **Audit trail** - created_at, updated_at, email logs for compliance

**3. Data Integrity**
NOT NULL, CHECK constraints (scores 0-100), UNIQUE (no duplicate emails), Foreign keys with CASCADE, Transaction isolation, Enum types for status.

**4. Assessment Tokens**
Unique token per assessment for one-click email access. Supports expiration, revocation, no URL vulnerabilities.

**Current Performance:**
- 1000+ candidates: 25ms query
- 5000+ responses: 18ms query
- Database size: 45MB
- Backup: Every 6 hours
- Replication: Real-time standby

**Scaling Ready**: Partitioning, read replicas, Redis caching, archival strategy, sharding if needed.

Fast, reliable, ready to scale. Thank you!"

---

## 🎬 TEAM DEMO FLOW (7 minutes total)

**1. Introduction (30 sec)** - Team Lead
"HireSense automates hiring: AI resume screening, proctored assessments, data-driven insights."

**2. Frontend (2 min)** - Shaivi
Dashboard → Resume upload → Assessment → Proctoring demo

**3. Backend (2 min)** - Akshat  
API logs → AI processing → WebSocket connections → Security

**4. Database (2 min)** - Prashanth
Schema → Query performance → Real-time updates

**5. Closing (30 sec)** - Team Lead
"Frontend: Custom CV algorithms. Backend: 200+ concurrent connections. Database: Sub-50ms queries. We reduce hiring time 70%, eliminate bias, ensure integrity. Production-ready. Questions?"

---

## 📊 KEY METRICS

- **Tech**: React + Flask + PostgreSQL + AI
- **Performance**: 60fps frontend, 120ms backend, sub-50ms database
- **Scale**: 200+ concurrent users, 10,000+ candidates ready
- **Features**: 3-stage assessments, real-time proctoring, AI analysis
- **Security**: JWT auth, rate limiting, encrypted data

---

## 💡 PRESENTATION TIPS

**DO:** Practice demos, have backup slides, show actual data, highlight challenges, time yourself, show enthusiasm

**DON'T:** Rush, apologize for bugs, read notes, go over time, forget the problem

---

## 🎤 OPENING OPTIONS

**Option 1:** "Hiring is broken. 40+ hours screening resumes, candidates cheat, bias everywhere. We fixed it."

**Option 2:** "Imagine AI screens 1000 resumes in seconds, proctoring is automatic, decisions are data-driven. That's HireSense."

**Option 3:** "We reduced hiring time 70%, eliminated bias, ensured integrity. Here's how."

---

## 🏆 CLOSING OPTIONS

**Option 1:** "HireSense isn't just a hackathon project - it's production-ready to transform hiring. Thank you!"

**Option 2:** "From AI screening to real-time proctoring, we built the future of hiring. Questions?"

**Option 3:** "Every challenge was solved in [timeframe]. Imagine what we can build next. Thank you!"

---

Good luck! 🚀
