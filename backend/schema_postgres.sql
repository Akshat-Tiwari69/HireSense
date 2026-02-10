-- HireSense Database Schema (PostgreSQL)

-- Users
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL,
    name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- Candidates
CREATE TABLE IF NOT EXISTS candidates (
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    phone TEXT NOT NULL,
    resume_path TEXT NOT NULL,
    parsed_skills TEXT,
    years_experience INTEGER,
    education TEXT,
    match_score INTEGER,
    shortlist_status TEXT,
    pros TEXT,
    cons TEXT,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Job Descriptions
CREATE TABLE IF NOT EXISTS job_descriptions (
    title TEXT NOT NULL,
    description TEXT,
    required_skills TEXT,
    min_experience INTEGER,
    department TEXT,
    location TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Scheduled Assessments (created without FK to assessments to avoid circular dependency)
CREATE TABLE IF NOT EXISTS scheduled_assessments (
    candidate_id INTEGER NOT NULL,
    interviewer_id INTEGER NOT NULL,
    scheduled_time TIMESTAMP NOT NULL,
    status TEXT DEFAULT 'scheduled',
    assessment_id INTEGER,
    access_token TEXT UNIQUE,
    started_at TIMESTAMP,
    is_streaming BOOLEAN DEFAULT false,
    stream_started_at TIMESTAMP,
    stream_ended_at TIMESTAMP,
    is_technical_role BOOLEAN DEFAULT true,
    questions_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE,
    FOREIGN KEY (interviewer_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_scheduled_assessments_candidate ON scheduled_assessments(candidate_id);
CREATE INDEX IF NOT EXISTS idx_scheduled_assessments_time ON scheduled_assessments(scheduled_time);

-- Assessments (created without FK to scheduled_assessments to avoid circular dependency)
CREATE TABLE IF NOT EXISTS assessments (
    candidate_id INTEGER NOT NULL,
    job_id INTEGER,
    technical_score REAL,
    psychometric_score REAL,
    overall_score REAL,
    decision TEXT,
    rationale TEXT,
    proctoring_violations INTEGER DEFAULT 0,
    status TEXT DEFAULT 'in_progress',
    scheduled_assessment_id INTEGER,
    hiring_recommendation TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    questions_data JSONB,  -- Stores generated MCQ, coding, psychometric questions
    time_elapsed_seconds INTEGER DEFAULT 0,  -- Tracks elapsed time for resume functionality
    FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE,
    FOREIGN KEY (job_id) REFERENCES job_descriptions(id) ON DELETE SET NULL
);

-- MCQ Responses
CREATE TABLE IF NOT EXISTS mcq_responses (
    assessment_id INTEGER NOT NULL,
    question_id INTEGER NOT NULL,
    selected_answer TEXT NOT NULL,
    is_correct BOOLEAN,
    time_spent INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (assessment_id) REFERENCES assessments(id) ON DELETE CASCADE
);

-- Coding Submissions
CREATE TABLE IF NOT EXISTS coding_submissions (
    assessment_id INTEGER NOT NULL,
    problem_id INTEGER NOT NULL,
    language TEXT NOT NULL,
    code TEXT NOT NULL,
    test_cases_passed INTEGER,
    total_test_cases INTEGER,
    execution_time REAL,
    error_message TEXT,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (assessment_id) REFERENCES assessments(id) ON DELETE CASCADE
);

-- Proctoring Events
CREATE TABLE IF NOT EXISTS proctoring_events (
    assessment_id INTEGER NOT NULL,
    event_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    details TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (assessment_id) REFERENCES assessments(id) ON DELETE CASCADE
);

-- Psychometric Responses
CREATE TABLE IF NOT EXISTS psychometric_responses (
    assessment_id INTEGER NOT NULL,
    question_id INTEGER NOT NULL,
    trait TEXT NOT NULL,
    score INTEGER,
    scenario_response TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (assessment_id) REFERENCES assessments(id) ON DELETE CASCADE
);

-- Email Logs
CREATE TABLE IF NOT EXISTS email_logs (
    recipient_email TEXT NOT NULL,
    recipient_name TEXT NOT NULL,
    email_type TEXT NOT NULL,
    subject TEXT NOT NULL,
    status TEXT DEFAULT 'sent',
    error_message TEXT,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Proctoring Violations Table
CREATE TABLE IF NOT EXISTS proctoring_violations (
    assessment_id INTEGER NOT NULL,
    violation_type TEXT NOT NULL,
    description TEXT,
    screenshot_url TEXT,
    severity TEXT DEFAULT 'medium',
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (assessment_id) REFERENCES assessments(id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_email_logs_recipient ON email_logs(recipient_email);
CREATE INDEX IF NOT EXISTS idx_email_logs_type ON email_logs(email_type);
CREATE INDEX IF NOT EXISTS idx_email_logs_status ON email_logs(status);

CREATE INDEX IF NOT EXISTS idx_candidates_email ON candidates(email);
CREATE INDEX IF NOT EXISTS idx_candidates_status ON candidates(shortlist_status);
CREATE INDEX IF NOT EXISTS idx_assessments_candidate ON assessments(candidate_id);
CREATE INDEX IF NOT EXISTS idx_assessments_status ON assessments(status);
CREATE INDEX IF NOT EXISTS idx_mcq_assessment ON mcq_responses(assessment_id);
CREATE INDEX IF NOT EXISTS idx_coding_assessment ON coding_submissions(assessment_id);
CREATE INDEX IF NOT EXISTS idx_proctoring_assessment ON proctoring_events(assessment_id);
CREATE INDEX IF NOT EXISTS idx_psychometric_assessment ON psychometric_responses(assessment_id);
CREATE INDEX IF NOT EXISTS idx_proctoring_violations_assessment ON proctoring_violations(assessment_id);

-- Add circular FKs after both tables exist
ALTER TABLE scheduled_assessments
    ADD CONSTRAINT fk_sched_assessment
    FOREIGN KEY (assessment_id) REFERENCES assessments(id) ON DELETE SET NULL;

ALTER TABLE assessments
    ADD CONSTRAINT fk_assessment_scheduled
    FOREIGN KEY (scheduled_assessment_id) REFERENCES scheduled_assessments(id) ON DELETE SET NULL;
