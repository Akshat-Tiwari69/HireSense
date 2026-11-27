# HireSense — User Roles & Permissions

This document describes each role in HireSense, what it can do, and how the
roles work together in the hiring pipeline.

---

## Roles at a Glance

| Role | Login | Workspace | Purpose |
|------|-------|-----------|---------|
| **Super Admin** (`super_admin`) | Email + password | Admin Dashboard (`/admin`) | Full system control, including admin accounts |
| **Admin** (`admin`) | Email + password | Admin Dashboard (`/admin`) | Full system management |
| **Sector Admin** (`sector_admin`) | Email + password | Hiring dashboard (`/dashboard`) | Hiring review and job management within one sector |
| **Recruiter** (`recruiter`) | Email + password | Hiring dashboard (`/dashboard`) | Hiring review and job postings within one sector |
| **Interviewer** (`interviewer`) | Email + password | Hiring dashboard (`/dashboard`) | Evaluate assigned candidates and make hiring decisions |
| **Proctor** (`proctor`) | Email + password | Proctor Dashboard (`/proctor`) | Monitor live assessments |
| **Candidate** | None (token link) | Assessment page (`/assessment`) | Apply and take the assessment |

`sector_admin` and `recruiter` accounts must have a `sector_id`; the database
enforces this. For job and sector permissions the backend treats `admin` as
`super_admin` and uses this order: `super_admin` (100) > `admin` (90) >
`sector_admin` (70) > `recruiter` (50) > `interviewer` (30) > `proctor` (20).

Each workspace is limited to its own roles. Admins use the Admin Dashboard only;
the hiring dashboard is for interviewers, recruiters, and sector admins; the
Proctor Dashboard is for proctors only.

---

## 🔴 Admin and Super Admin

Admins manage users, candidates, job postings, and content, and see
system-wide analytics and logs.

### User Management (Users tab)
- View, create, edit, and delete staff accounts
- Only a super admin can create, edit, or delete `admin` and `super_admin` accounts

### Candidate Management (Candidates tab)
- View all candidates with AI analysis, match scores, and status
- Edit candidate details and delete candidates with their related data
- Reset a candidate's status back to "Applied"
- **Absence of Details** tab: find candidates missing key information

### Job Postings and Sectors (Job Postings tab)
- Create, edit, and delete job postings (skills, experience range, work mode,
  employment type, salary range, closing date)
- Use **AI Enhance** to rewrite a job description and suggest skills
- Create, edit, and delete sectors

### Bulk Resume Upload (Bulk Upload tab)
- Upload a ZIP archive (up to 100 PDF/DOCX resumes) for a selected job posting
- Resumes are parsed and scored concurrently in a worker pool
- Results show match scores, AI recommendations, missing details, duplicates, and errors

### Custom Question Bank (Question Bank tab)
- Upload PDF/DOCX files of questions; AI extracts the questions
- Toggle question banks active/inactive, or delete them
- Active question banks are blended into newly generated assessments

### Analytics, Email Logs, and Audit Log
- **Analytics:** candidate, assessment, and score statistics
- **Email Logs:** every email sent, with recipient, time, and delivery status
- **Audit Log:** who did what and when

Production configuration is not editable in the application. It is changed
through the host's secret file (see [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)).

---

## 🟢 Interviewer, Recruiter, and Sector Admin (Hiring Review)

These three roles share the hiring dashboard at `/dashboard`. Interviewers see
the candidates assigned to them; recruiters and sector admins see candidates in
their sector.

### Candidate Review
- View candidates with AI match score, parsed skills, experience, and education
- Read the AI pros/cons analysis and recommendation
- Search, filter by status, and filter by match score
- Download the original resume (PDF/DOCX)
- Dashboard metrics: total candidates, high match, scheduled, completed, hired

### Assessment Scheduling
- Schedule an assessment at a specific date and time
- Choose **Technical** (MCQ + Coding + Psychometric) or **Non-Technical**
  (MCQ + Psychometric). Technical assessments need the code runner, which is
  disabled in production
- AI generates tailored questions from the candidate's resume and the job
- The candidate receives an email with a unique assessment link

### Live Monitoring
- Open **Monitor** on a candidate with an assessment to watch the live
  proctoring video

### Decisions
- **Reject** a candidate with an optional reason; a rejection email is sent
- Review assessment results: MCQ, coding (if technical), psychometric traits,
  overall score, and the automated recommendation
- Record a final **Hire** or **No-Hire** decision with rationale and next
  steps; the candidate receives a decision email

### Jobs and Matching (Recruiter and Sector Admin)
- Create, edit, and delete job postings in their sector through the jobs API
- Run AI candidate-to-job matching and confirm or reject matches

---

## 🟡 Proctor

The proctor monitors assessments in real time.

### Assessment Monitoring
- **Scheduled**, **Active**, and **Completed** assessment lists
- Claim an unassigned assessment to proctor it
- The dashboard refreshes every 30 seconds while the tab is visible

### Live Proctoring
- Watch the candidate's camera through WebRTC
- See whether the candidate's stream is connected

### Violation Review
- View every violation recorded for an assessment, with type, description,
  severity, time, and screenshot evidence where captured
- Violations are detected and reported by the candidate's browser:
  - **Tab hidden**: the candidate switched tabs or minimised the window
  - **Window focus lost**: the candidate moved focus to another window
  - **Copy, cut, or paste** inside the assessment
  - **No face detected**: the candidate left the camera view
  - **Multiple faces**: someone else is in frame
  - **Camera interrupted**: the camera stream stopped

### Dashboard Summary
- Scheduled assessments (upcoming today)
- Active sessions
- Assessments completed today
- Violation events today

---

## 🔵 Candidate

Candidates do not have an account. They apply from the public job listings and
take the assessment through an emailed, time-limited link.

### Application
- Browse open roles at `/jobs` and apply at `/apply/:jobId`
- Upload a PDF or DOCX resume (max 10 MB) with name, email, and optional phone
- The resume is parsed and scored against the job; the candidate only sees a
  confirmation, while the AI review is visible to hiring staff

### Assessment Access
- The assessment link carries its token in the URL fragment (`#token=…`)
- The assessment can only be started within ±30 minutes of the scheduled time

### Taking the Assessment
- **MCQ section:** multiple-choice questions for the role
- **Coding section** (technical roles only): a plain code editor with
  Python or JavaScript, and test runs through the code runner
- **Psychometric section:** scenario-based questions on behavioural traits
- Answers are saved as the candidate goes, and time is synced with the server

### Proctoring During the Assessment
- Camera access for live video monitoring
- Browser monitoring for tab switches, window focus loss, and copy/paste
- In-browser face detection (no face, multiple faces)
- Violations are reported to proctors automatically

### Scoring
- Technical score: 60% MCQ + 40% coding
- Overall score: 70% technical + 30% psychometric
- The system produces an automated recommendation; the hiring reviewer makes
  the final decision, which is emailed to the candidate

---

## Role Comparison Matrix

| Feature | Admin / Super Admin | Interviewer | Recruiter / Sector Admin | Proctor | Candidate |
|---------|:-----:|:-----:|:-----:|:-----:|:-----:|
| Login with email/password | ✅ | ✅ | ✅ | ✅ | ❌ |
| Manage staff users | ✅ | ❌ | ❌ | ❌ | ❌ |
| View candidates | ✅ all | ✅ assigned | ✅ own sector | ❌ | ❌ |
| Submit an application | ❌ | ❌ | ❌ | ❌ | ✅ |
| Bulk upload resumes (ZIP) | ✅ | ❌ | ❌ | ❌ | ❌ |
| Manage job postings | ✅ | ❌ | ✅ own sector | ❌ | ❌ |
| Manage sectors | ✅ | ❌ | ❌ | ❌ | ❌ |
| Schedule assessments | ❌ | ✅ | ✅ | ❌ | ❌ |
| Make hiring decisions | ❌ | ✅ | ✅ | ❌ | ❌ |
| Watch live assessments | ❌ | ✅ | ✅ | ✅ | ❌ |
| Review violations | ❌ | ❌ | ❌ | ✅ | ❌ |
| Take assessments | ❌ | ❌ | ❌ | ❌ | ✅ |
| Analytics | ✅ | ❌ | ❌ | Dashboard summary | ❌ |
| Question banks | ✅ | ❌ | ❌ | ❌ | ❌ |
| Email logs | ✅ | ❌ | ❌ | ❌ | ❌ |
| Audit log | ✅ | ❌ | ❌ | ❌ | ❌ |

---

## Seed Accounts

`database/seed_users.py` creates these accounts:

| Role | Email | Password source |
|------|-------|-----------------|
| Admin | `admin@hiresense.com` | `SEED_ADMIN_PASSWORD` or a generated initial password |
| Interviewer | `interviewer@hiresense.com` | `SEED_INTERVIEWER_PASSWORD` or a generated initial password |
| Proctor | `proctor@hiresense.com` | `SEED_PROCTOR_PASSWORD` or a generated initial password |

The seed script has no fixed default passwords. Generated passwords are shown
once at seed time; store them in a password manager and rotate them before
production use. Never commit seed passwords to the repository.

With `DEMO_MODE=true`, `database/seed_demo.py` adds separate demo accounts and
`/login` offers one-click Admin, Interviewer, and Proctor sign-in (see
[deploy/README.md](../deploy/README.md)).
