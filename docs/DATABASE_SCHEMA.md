# Database Schema Documentation

Complete database schema documentation for CYGNUSA Elite-Hire.

---

## Overview

CYGNUSA Elite-Hire supports dual database backends:
- **SQLite** - Development and testing
- **PostgreSQL** - Production deployment

Both schemas are functionally identical with minor syntax differences.

---

## Database Configuration

### Development (SQLite)

```python
# db_config.py
DATABASE_PATH = os.path.join(BASE_DIR, 'elite_hire.db')

def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn
```

### Production (PostgreSQL)

```python
# db_config.py
DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db_connection():
    if DATABASE_URL:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    else:
        # Fallback to SQLite
        return sqlite3.connect(DATABASE_PATH)
```

---

## Entity Relationship Diagram

```
┌─────────────────┐       ┌─────────────────────┐       ┌────────────────┐
│     users       │       │     candidates      │       │  assessments   │
├─────────────────┤       ├─────────────────────┤       ├────────────────┤
│ id (PK)         │       │ id (PK)             │───────│ id (PK)        │
│ email           │       │ name                │       │ candidate_id   │
│ password_hash   │       │ email               │       │ technical_score│
│ role            │       │ phone               │       │ psychometric   │
│ name            │       │ resume_path         │       │ mcq_score      │
│ created_at      │       │ skills              │       │ coding_score   │
│ updated_at      │       │ experience          │       │ decision       │
└────────┬────────┘       │ education           │       │ created_at     │
         │                │ match_score         │       │ completed_at   │
         │                │ pros                │       └───────┬────────┘
         │                │ cons                │               │
         │                │ status              │               │
         │                │ created_at          │               │
         │                └─────────┬───────────┘               │
         │                          │                           │
         │                          │                           │
┌────────┴────────────────┐         │                           │
│ scheduled_assessments   │─────────┘                           │
├─────────────────────────┤                                     │
│ id (PK)                 │                                     │
│ candidate_id (FK)       │                                     │
│ interviewer_id (FK)     │                                     │
│ assessment_token        │                                     │
│ scheduled_time          │                                     │
│ status                  │                                     │
│ assessment_id (FK)      │─────────────────────────────────────┘
│ created_at              │
│ updated_at              │
└─────────────────────────┘
         │
         │
┌────────┴────────────────────────────────────────────────────────────────┐
│                                                                          │
│     ┌────────────────┐   ┌────────────────────┐   ┌────────────────────┐│
│     │ mcq_responses  │   │ coding_submissions │   │ psychometric_resp  ││
│     ├────────────────┤   ├────────────────────┤   ├────────────────────┤│
│     │ id (PK)        │   │ id (PK)            │   │ id (PK)            ││
│     │ assessment_id  │   │ assessment_id (FK) │   │ assessment_id (FK) ││
│     │ question_id    │   │ problem_id         │   │ scenario_id        ││
│     │ answer         │   │ code               │   │ trait_scores       ││
│     │ is_correct     │   │ language           │   │ response_text      ││
│     │ time_taken     │   │ test_results       │   │ created_at         ││
│     │ created_at     │   │ score              │   └────────────────────┘│
│     └────────────────┘   │ created_at         │                         │
│                          └────────────────────┘                         │
└─────────────────────────────────────────────────────────────────────────┘
         
┌─────────────────────┐   ┌─────────────────────┐   ┌─────────────────────┐
│ proctoring_events   │   │    email_logs       │   │  job_descriptions   │
├─────────────────────┤   ├─────────────────────┤   ├─────────────────────┤
│ id (PK)             │   │ id (PK)             │   │ id (PK)             │
│ assessment_id (FK)  │   │ recipient_email     │   │ title               │
│ event_type          │   │ recipient_name      │   │ description         │
│ details             │   │ email_type          │   │ requirements        │
│ timestamp           │   │ subject             │   │ skills              │
└─────────────────────┘   │ status              │   │ experience_min      │
                          │ error_message       │   │ created_at          │
                          │ sent_at             │   │ updated_at          │
                          └─────────────────────┘   └─────────────────────┘
```

---

## Table Definitions

### users

Stores all system users (interviewers, admins, proctors).

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('interviewer', 'admin', 'proctor')),
    name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Unique identifier |
| email | TEXT | UNIQUE, NOT NULL | Login email |
| password_hash | TEXT | NOT NULL | bcrypt hashed password |
| role | TEXT | NOT NULL | interviewer, admin, or proctor |
| name | TEXT | NOT NULL | Display name |
| created_at | TIMESTAMP | DEFAULT NOW | Account creation time |
| updated_at | TIMESTAMP | DEFAULT NOW | Last update time |

**Indexes:**
```sql
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
```

---

### candidates

Stores job applicants and their resume analysis.

```sql
CREATE TABLE candidates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT,
    resume_path TEXT,
    original_filename TEXT,
    skills TEXT,
    experience INTEGER,
    education TEXT,
    match_score REAL,
    pros TEXT,
    cons TEXT,
    overall_assessment TEXT,
    recommendation TEXT,
    confidence_score INTEGER,
    enhanced_match_score REAL,
    status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'under_review', 'rejected', 'hired')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Unique identifier |
| name | TEXT | Candidate full name |
| email | TEXT | Contact email |
| phone | TEXT | Contact phone |
| resume_path | TEXT | Path to uploaded resume file |
| original_filename | TEXT | Original resume filename |
| skills | TEXT | Comma-separated skills list |
| experience | INTEGER | Years of experience |
| education | TEXT | Education background |
| match_score | REAL | Initial match score (0-100) |
| pros | TEXT | Newline-separated strengths |
| cons | TEXT | Newline-separated weaknesses |
| overall_assessment | TEXT | AI-generated assessment summary |
| recommendation | TEXT | Strong/Good/Moderate/Weak Match |
| confidence_score | INTEGER | AI confidence (0-100) |
| enhanced_match_score | REAL | AI-enhanced score (0-100) |
| status | TEXT | pending, under_review, rejected, hired |
| created_at | TIMESTAMP | Application time |
| updated_at | TIMESTAMP | Last update time |

**Status Flow:**
```
pending → under_review → hired
    ↓          ↓
 rejected   rejected
```

---

### assessments

Stores candidate assessment sessions and results.

```sql
CREATE TABLE assessments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    candidate_id INTEGER NOT NULL,
    technical_score REAL,
    psychometric_score REAL,
    mcq_score REAL,
    coding_score REAL,
    overall_score REAL,
    decision TEXT,
    rationale TEXT,
    ai_recommendation TEXT,
    psychometric_breakdown TEXT,
    proctoring_violations INTEGER DEFAULT 0,
    status TEXT DEFAULT 'in_progress' CHECK(status IN ('in_progress', 'completed', 'cancelled')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (candidate_id) REFERENCES candidates(id)
);
```

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Unique identifier |
| candidate_id | INTEGER | FK to candidates table |
| technical_score | REAL | Combined MCQ + Coding (0-100) |
| psychometric_score | REAL | Personality assessment (0-100) |
| mcq_score | REAL | MCQ section score (0-100) |
| coding_score | REAL | Coding section score (0-100) |
| overall_score | REAL | Weighted total score (0-100) |
| decision | TEXT | Hire/No-Hire/Pending |
| rationale | TEXT | Decision explanation |
| ai_recommendation | TEXT | AI-generated recommendation |
| psychometric_breakdown | TEXT | JSON breakdown of traits |
| proctoring_violations | INTEGER | Count of violations |
| status | TEXT | in_progress, completed, cancelled |
| created_at | TIMESTAMP | Assessment start time |
| completed_at | TIMESTAMP | Assessment completion time |

**Score Calculation:**
```
technical_score = (mcq_score × 0.4) + (coding_score × 0.6)
overall_score = (technical_score × 0.6) + (psychometric_score × 0.4)
```

---

### scheduled_assessments

Manages time-scheduled assessment appointments.

```sql
CREATE TABLE scheduled_assessments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    candidate_id INTEGER NOT NULL,
    interviewer_id INTEGER NOT NULL,
    assessment_token TEXT UNIQUE,
    scheduled_time TEXT NOT NULL,
    status TEXT DEFAULT 'scheduled' CHECK(status IN ('scheduled', 'in_progress', 'completed', 'cancelled', 'expired')),
    assessment_id INTEGER,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (candidate_id) REFERENCES candidates(id),
    FOREIGN KEY (interviewer_id) REFERENCES users(id),
    FOREIGN KEY (assessment_id) REFERENCES assessments(id)
);
```

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Unique identifier |
| candidate_id | INTEGER | FK to candidates |
| interviewer_id | INTEGER | FK to users (who scheduled) |
| assessment_token | TEXT | Unique token for URL |
| scheduled_time | TEXT | ISO 8601 datetime |
| status | TEXT | scheduled, in_progress, completed, cancelled, expired |
| assessment_id | INTEGER | FK to assessments (after started) |
| notes | TEXT | Additional instructions |
| created_at | TIMESTAMP | When scheduled |
| updated_at | TIMESTAMP | Last status change |

**Time Window Validation:**
```python
# Candidate can start within ±30 minutes of scheduled_time
window_start = scheduled_time - 30 minutes
window_end = scheduled_time + 30 minutes
```

---

### mcq_responses

Stores MCQ answers for each assessment.

```sql
CREATE TABLE mcq_responses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    assessment_id INTEGER NOT NULL,
    question_id INTEGER NOT NULL,
    answer INTEGER,
    is_correct BOOLEAN,
    time_taken INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (assessment_id) REFERENCES assessments(id)
);
```

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Unique identifier |
| assessment_id | INTEGER | FK to assessments |
| question_id | INTEGER | Question number (1-10) |
| answer | INTEGER | Selected option index (0-3) |
| is_correct | BOOLEAN | Whether answer is correct |
| time_taken | INTEGER | Seconds to answer |
| created_at | TIMESTAMP | Answer submission time |

---

### coding_submissions

Stores code solutions and test results.

```sql
CREATE TABLE coding_submissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    assessment_id INTEGER NOT NULL,
    problem_id INTEGER NOT NULL,
    code TEXT NOT NULL,
    language TEXT NOT NULL,
    test_results TEXT,
    passed_count INTEGER,
    total_count INTEGER,
    score REAL,
    execution_time REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (assessment_id) REFERENCES assessments(id)
);
```

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Unique identifier |
| assessment_id | INTEGER | FK to assessments |
| problem_id | INTEGER | Coding problem ID |
| code | TEXT | Submitted code |
| language | TEXT | python, javascript, cpp, java |
| test_results | TEXT | JSON array of test outcomes |
| passed_count | INTEGER | Tests passed |
| total_count | INTEGER | Total tests |
| score | REAL | Percentage score (0-100) |
| execution_time | REAL | Runtime in milliseconds |
| created_at | TIMESTAMP | Submission time |

**Supported Languages:**
- `python` - Python 3.x
- `javascript` - Node.js
- `cpp` - C++17
- `java` - Java 11

---

### psychometric_responses

Stores psychometric assessment answers.

```sql
CREATE TABLE psychometric_responses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    assessment_id INTEGER NOT NULL,
    scenario_id INTEGER NOT NULL,
    trait_scores TEXT,
    response_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (assessment_id) REFERENCES assessments(id)
);
```

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Unique identifier |
| assessment_id | INTEGER | FK to assessments |
| scenario_id | INTEGER | Scenario number (1-3) |
| trait_scores | TEXT | JSON with trait ratings |
| response_text | TEXT | Optional text response |
| created_at | TIMESTAMP | Submission time |

**Trait Scores Format:**
```json
{
  "leadership": 8,
  "communication": 7,
  "decision_making": 9,
  "stress_management": 6,
  "teamwork": 8
}
```

---

### proctoring_events

Logs proctoring violations during assessments.

```sql
CREATE TABLE proctoring_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    assessment_id INTEGER NOT NULL,
    event_type TEXT NOT NULL,
    details TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (assessment_id) REFERENCES assessments(id)
);
```

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Unique identifier |
| assessment_id | INTEGER | FK to assessments |
| event_type | TEXT | Violation type |
| details | TEXT | Additional context |
| timestamp | TIMESTAMP | When violation occurred |

**Event Types:**
- `no_face` - Face not detected
- `multiple_faces` - Multiple faces detected
- `tab_switch` - Browser tab changed
- `window_blur` - Window lost focus
- `screen_share_end` - Screen sharing stopped
- `camera_blocked` - Camera access denied

---

### email_logs

Audit trail for all sent emails.

```sql
CREATE TABLE email_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recipient_email TEXT NOT NULL,
    recipient_name TEXT,
    email_type TEXT NOT NULL,
    subject TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('sent', 'failed', 'pending')),
    error_message TEXT,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Unique identifier |
| recipient_email | TEXT | Email address |
| recipient_name | TEXT | Recipient name |
| email_type | TEXT | rejection, assessment_invitation, final_decision |
| subject | TEXT | Email subject line |
| status | TEXT | sent, failed, pending |
| error_message | TEXT | Error details if failed |
| sent_at | TIMESTAMP | Sending timestamp |

---

### job_descriptions

Stores job openings and requirements.

```sql
CREATE TABLE job_descriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    requirements TEXT,
    skills TEXT,
    experience_min INTEGER,
    experience_max INTEGER,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Unique identifier |
| title | TEXT | Job title |
| description | TEXT | Full description |
| requirements | TEXT | Job requirements |
| skills | TEXT | Required skills (comma-separated) |
| experience_min | INTEGER | Minimum years experience |
| experience_max | INTEGER | Maximum years experience |
| is_active | BOOLEAN | Whether actively hiring |
| created_at | TIMESTAMP | Creation time |
| updated_at | TIMESTAMP | Last update time |

---

## Database Helper Functions

### Core Operations (db_helpers.py)

```python
# User Operations
create_user(email, password_hash, role, name) → user_id
get_user_by_email(email) → user_dict
get_user_by_id(user_id) → user_dict

# Candidate Operations
create_candidate(name, email, phone, resume_path, ...) → candidate_id
get_candidate_by_id(candidate_id) → candidate_dict
get_all_candidates(status=None, sort=None, order=None) → [candidates]
update_candidate_status(candidate_id, status) → bool
update_candidate_analysis(candidate_id, pros, cons, ...) → bool

# Assessment Operations
create_assessment(candidate_id) → assessment_id
get_assessment_by_id(assessment_id) → assessment_dict
get_assessment_by_candidate_id(candidate_id) → assessment_dict
update_assessment_scores(assessment_id, scores) → bool
complete_assessment(assessment_id, decision, rationale) → bool

# Scheduled Assessments
create_scheduled_assessment(candidate_id, interviewer_id, scheduled_time) → scheduled_id
get_scheduled_assessment_by_token(token) → scheduled_dict
get_scheduled_assessment_by_candidate(candidate_id) → scheduled_dict
check_assessment_time_valid(candidate_id, current_time) → (is_valid, scheduled_time, message)
update_scheduled_assessment_status(scheduled_id, status, assessment_id=None) → bool

# MCQ Operations
save_mcq_response(assessment_id, question_id, answer, is_correct, time_taken) → response_id
get_mcq_responses(assessment_id) → [responses]
calculate_mcq_score(assessment_id) → float

# Coding Operations
save_coding_submission(assessment_id, problem_id, code, language, results) → submission_id
get_coding_submissions(assessment_id) → [submissions]
calculate_coding_score(assessment_id) → float

# Psychometric Operations
save_psychometric_response(assessment_id, scenario_id, trait_scores, response_text) → response_id
get_psychometric_responses(assessment_id) → [responses]
calculate_psychometric_score(assessment_id) → float

# Proctoring Operations
log_proctoring_event(assessment_id, event_type, details) → event_id
get_proctoring_events(assessment_id) → [events]
get_violation_count(assessment_id) → int

# Email Operations
log_email(recipient_email, recipient_name, email_type, subject, status, error=None) → log_id
get_email_logs(recipient_email=None) → [logs]
```

---

## Migration Scripts

### Adding Assessment Token (SQLite)

```sql
-- database/migrations/add_assessment_token.sql
ALTER TABLE scheduled_assessments ADD COLUMN assessment_token TEXT UNIQUE;
```

### SQLite to PostgreSQL Migration

```python
# backend/scripts/migrate_local_sqlite.py
import sqlite3
import psycopg2

def migrate():
    sqlite_conn = sqlite3.connect('elite_hire.db')
    pg_conn = psycopg2.connect(DATABASE_URL)
    
    # Migrate each table
    for table in ['users', 'candidates', 'assessments', ...]:
        rows = sqlite_conn.execute(f'SELECT * FROM {table}').fetchall()
        for row in rows:
            pg_conn.execute(f'INSERT INTO {table} VALUES ({placeholders})', row)
    
    pg_conn.commit()
```

---

## Indexes for Performance

```sql
-- User lookups
CREATE INDEX idx_users_email ON users(email);

-- Candidate filtering
CREATE INDEX idx_candidates_email ON candidates(email);
CREATE INDEX idx_candidates_status ON candidates(status);
CREATE INDEX idx_candidates_created_at ON candidates(created_at);

-- Assessment lookups
CREATE INDEX idx_assessments_candidate ON assessments(candidate_id);
CREATE INDEX idx_assessments_status ON assessments(status);

-- Scheduled assessment lookups
CREATE INDEX idx_scheduled_token ON scheduled_assessments(assessment_token);
CREATE INDEX idx_scheduled_candidate ON scheduled_assessments(candidate_id);

-- Response lookups
CREATE INDEX idx_mcq_assessment ON mcq_responses(assessment_id);
CREATE INDEX idx_coding_assessment ON coding_submissions(assessment_id);
CREATE INDEX idx_psychometric_assessment ON psychometric_responses(assessment_id);

-- Email logs
CREATE INDEX idx_email_recipient ON email_logs(recipient_email);
CREATE INDEX idx_email_type ON email_logs(email_type);
```

---

## Database Initialization

### SQLite (Development)

```bash
cd backend
python init_db.py
```

This creates:
- All tables from schema.sql
- Default admin user
- Sample job descriptions

### PostgreSQL (Production)

```bash
# Set DATABASE_URL environment variable
export DATABASE_URL="postgresql://user:pass@host:5432/elite_hire"

# Run initialization
python init_db.py
```

---

## Backup & Restore

### SQLite Backup

```bash
# Backup
cp elite_hire.db elite_hire_backup_$(date +%Y%m%d).db

# Restore
cp elite_hire_backup_20260121.db elite_hire.db
```

### PostgreSQL Backup

```bash
# Backup
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql

# Restore
psql $DATABASE_URL < backup_20260121.sql
```

---

## Related Documentation

- [PROJECT_ARCHITECTURE.md](PROJECT_ARCHITECTURE.md) - System architecture
- [API_DOCS.md](API_DOCS.md) - API reference
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Production setup

---

*Last Updated: January 2026*
*Version: 1.0*
