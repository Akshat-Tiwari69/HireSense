# HireSense — User Roles & Permissions

This document defines the four primary user roles in HireSense, what each role can do, and how they interact within the hiring pipeline.

---

## Role Hierarchy

```
Admin (highest)
  └── Interviewer
  └── Proctor
  └── Candidate (no login — token-based access)
```

| Role | Login Required | Dashboard | Purpose |
|------|---------------|-----------|---------|
| **Admin** | ✅ Email + Password | Admin Dashboard | Full system management |
| **Interviewer** | ✅ Email + Password | Interviewer Dashboard | Candidate evaluation & hiring decisions |
| **Proctor** | ✅ Email + Password | Proctor Dashboard | Live assessment monitoring |
| **Candidate** | ❌ Token-based link | Assessment Page | Takes assessments |

---

## 🔴 Admin

The **Admin** has full control over the entire HireSense system. They manage users, candidates, job postings, system settings, and have access to analytics.

### User Management
- View all users (admins, interviewers, proctors)
- Create new users with any role
- Update user details (name, email, role, password)
- Delete users

### Candidate Management
- View all candidates with AI analysis, match scores, and status
- Edit candidate details (name, email, phone, status)
- Delete candidates and all related data
- Reset candidate status back to "Applied"
- View candidates with missing information ("Absence of Details")

### Job Postings
- Create new job postings with required/preferred skills, salary range, experience level
- Edit existing job postings
- Delete job postings
- Use **AI Enhance** to polish job descriptions automatically

### Sector Management
- Create, update, and delete sectors (departments/divisions)
- Assign sectors to users and job postings

### Bulk Resume Upload
- Upload a ZIP/RAR archive containing multiple PDF/DOCX resumes
- All resumes are processed in parallel by multiple AI agents
- Each resume is scored against a selected job posting
- View detailed results: match scores, AI recommendations, missing info, duplicates, errors

### Custom Question Bank
- Upload PDF/DOCX files containing custom questions
- AI parses and extracts questions automatically
- Toggle question banks active/inactive
- Delete question banks
- Active question banks blend into future assessments

### Database Management
- View all database tables and their contents
- View database statistics (row counts, table sizes)

### System Settings
- View status of environment variables (API keys, SMTP config)
- Update environment variables (OpenAI API key, SMTP settings, etc.)
- Changes persist to `.env` file

### Analytics
- System-wide statistics: total candidates, assessments, hiring rates
- Candidate status distribution (applied, under review, hired, rejected)
- Assessment completion rates and average scores

### Email Logs
- View all sent emails with timestamps, recipients, and delivery status

### Audit Log
- View all system actions (who did what and when)

---

## 🟢 Interviewer

The **Interviewer** manages the candidate evaluation pipeline — from reviewing resumes to making final hiring decisions.

### Candidate Review
- View all candidates with:
  - AI-generated match scores
  - Parsed skills, experience, and education
  - AI pros/cons analysis and recommendation (Strong Match, Good Match, Moderate Match, Weak Match)
- Filter candidates by status (pending, under review, rejected, hired)
- Sort candidates by name, date, or match score
- View detailed candidate profiles

### Resume Management
- Download original resume files (PDF/DOCX)

### Assessment Scheduling
- Schedule assessments for candidates at a specific date/time
- Choose between **Technical** (MCQ + Coding + Psychometric) and **Non-Technical** (MCQ + Psychometric only) assessments
- AI automatically generates tailored questions based on the candidate's resume and the job requirements
- Candidate receives an email with a unique assessment link

### Candidate Decisions
- **Reject** a candidate with an optional reason/feedback
  - Candidate automatically receives a rejection email
- View assessment results after a candidate completes their assessment:
  - MCQ scores
  - Coding scores (if technical)
  - Psychometric trait scores
  - Overall score and AI recommendation

### Final Hiring Decision
- Make a **Hire** or **No-Hire** decision after reviewing assessment results
- Add rationale and next steps
- Candidate automatically receives a decision email with next steps

### Dashboard Statistics
- Total candidates count
- Candidates by status breakdown
- Average match scores

### Candidate Notes
- Add and view notes for individual candidates (for internal team communication)

---

## 🟡 Proctor

The **Proctor** monitors assessments in real-time to ensure integrity and fairness during candidate evaluations.

### Assessment Monitoring
- View all **scheduled** assessments (upcoming)
- View all **active** assessments (currently in-progress)
- View all **completed** assessments (finished)

### Live Proctoring (Real-Time)
- Watch candidate's live video stream via WebRTC
- See real-time connection status (connected, streaming)
- Monitor multiple assessments simultaneously

### Violation Management
- View all proctoring violations for any assessment
- Violations are automatically detected and reported by the candidate's browser:
  - **No face detected** — candidate leaves camera view
  - **Multiple faces** — someone else is in frame
  - **Tab switch** — candidate switches browser tabs
  - Other suspicious behavior
- Each violation includes: type, description, severity level, timestamp, and optional screenshot

### Proctoring Statistics
- Total scheduled assessments
- Active assessments count
- Completed assessments count
- Total violations recorded
- Violations by severity breakdown

---

## 🔵 Candidate

The **Candidate** does not have a traditional login. Instead, they interact with the system through a unique, time-limited assessment link sent via email.

### Resume Submission
- Upload a PDF or DOCX resume (max 10MB)
- Resume is automatically parsed by AI to extract:
  - Name, email, phone
  - Skills and qualifications
  - Years of experience
  - Education
- AI scores the resume against the applied job posting
- AI generates pros, cons, and a recommendation

### Assessment Access
- Receive an assessment link via email
- **Time-validated access**: Assessment can only be started within a ±30 minute window of the scheduled time
- Verify assessment token to see status and time remaining

### Taking the Assessment
- **MCQ Section**: Multiple-choice questions tailored to the job role
- **Coding Section** (technical roles only): Code editor with syntax highlighting, run test cases
- **Psychometric Section**: Scenario-based questions evaluating behavioral traits
- Submit answers individually with time tracking
- Complete the assessment to trigger automatic scoring

### Proctoring (During Assessment)
- Camera access for live video monitoring
- Browser activity monitoring (tab switches, focus loss)
- Face detection (no face, multiple faces)
- Violations are automatically reported to proctors
- Time sync — progress is saved periodically

### Assessment Results
- Final scores are calculated automatically:
  - Technical score: 60% MCQ + 40% Coding
  - Psychometric score: average of trait scores
  - Overall score: 70% Technical + 30% Psychometric
- AI generates a preliminary hiring recommendation
- Candidate receives an email with the final hiring decision

---

## Role Comparison Matrix

| Feature | Admin | Interviewer | Proctor | Candidate |
|---------|:-----:|:-----------:|:-------:|:---------:|
| Login with email/password | ✅ | ✅ | ✅ | ❌ |
| Manage users (CRUD) | ✅ | ❌ | ❌ | ❌ |
| View all candidates | ✅ | ✅ | ❌ | ❌ |
| Upload resumes (single) | ❌ | ❌ | ❌ | ✅ |
| Bulk upload resumes (ZIP) | ✅ | ❌ | ❌ | ❌ |
| Manage job postings | ✅ | ❌ | ❌ | ❌ |
| Schedule assessments | ❌ | ✅ | ❌ | ❌ |
| Take assessments | ❌ | ❌ | ❌ | ✅ |
| Make hiring decisions | ❌ | ✅ | ❌ | ❌ |
| Monitor live assessments | ❌ | ❌ | ✅ | ❌ |
| View violations | ❌ | ❌ | ✅ | ❌ |
| View analytics | ✅ | ✅ | ✅ | ❌ |
| Manage system settings | ✅ | ❌ | ❌ | ❌ |
| View database tables | ✅ | ❌ | ❌ | ❌ |
| Manage question banks | ✅ | ❌ | ❌ | ❌ |
| View email logs | ✅ | ❌ | ❌ | ❌ |
| View audit log | ✅ | ❌ | ❌ | ❌ |

---

## Default Credentials

When seeding the database with `database/seed_users.py`, the following accounts are created:

| Role | Email | Password |
|------|-------|----------|
| Admin | `admin@hiresense.com` | `admin123` |
| Interviewer | `interviewer@hiresense.com` | `interviewer123` |
| Proctor | `proctor@hiresense.com` | `proctor123` |

> ⚠️ **Change these passwords immediately in production environments.**
