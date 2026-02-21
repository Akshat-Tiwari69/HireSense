-- ============================================================================
-- HireSense Database Schema (PostgreSQL / Supabase)
-- Last verified against live database: 2026-02-21
-- This is the single source-of-truth schema file.
-- ============================================================================

-- ============================================================================
-- 1. CORE TABLES (no FK dependencies)
-- ============================================================================

-- Sectors: Organizational divisions (Engineering, Sales, Marketing, etc.)
CREATE TABLE IF NOT EXISTS sectors (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    email_alias TEXT UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Users: Authentication for interviewers, proctors, admins
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL,               -- 'interviewer', 'admin', 'proctor', 'super_admin', 'sector_admin', 'recruiter'
    name TEXT NOT NULL,
    sector_id INTEGER REFERENCES sectors(id) ON DELETE SET NULL,
    permissions JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_sector ON users(sector_id);

-- Candidates: Resume data and match scores
CREATE TABLE IF NOT EXISTS candidates (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    phone TEXT NOT NULL,
    resume_path TEXT NOT NULL,
    parsed_skills TEXT,                     -- JSON string: '["Python", "JavaScript"]'
    years_experience INTEGER,
    education TEXT,
    match_score INTEGER,                    -- 0-100
    shortlist_status TEXT,                  -- 'High Match', 'Potential', 'Reject'
    pros TEXT,                              -- Newline-separated strengths
    cons TEXT,                              -- Newline-separated weaknesses
    status TEXT DEFAULT 'pending',          -- 'pending', 'shortlisted', 'rejected', 'assessment_scheduled', 'assessment_completed', 'completed'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    parsed_skills_json JSONB DEFAULT '[]',  -- Structured skills array
    best_match_job_id INTEGER,              -- FK added after job_descriptions table
    sector_id INTEGER REFERENCES sectors(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_candidates_email ON candidates(email);
CREATE INDEX IF NOT EXISTS idx_candidates_status ON candidates(shortlist_status);
CREATE INDEX IF NOT EXISTS idx_candidates_best_job ON candidates(best_match_job_id);
CREATE INDEX IF NOT EXISTS idx_candidates_sector ON candidates(sector_id);

-- Job Descriptions: Job postings with skills and requirements
CREATE TABLE IF NOT EXISTS job_descriptions (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    required_skills TEXT,                   -- JSON or comma-separated skills
    min_experience INTEGER,
    department TEXT,
    location TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- Extended columns (from job postings migration)
    sector_id INTEGER REFERENCES sectors(id) ON DELETE SET NULL,
    status TEXT DEFAULT 'active',           -- 'active', 'paused', 'closed', 'draft'
    preferred_skills TEXT,                  -- JSON array
    salary_range TEXT,
    employment_type TEXT DEFAULT 'full-time',  -- 'full-time', 'part-time', 'contract', 'internship'
    experience_level TEXT DEFAULT 'mid',    -- 'junior', 'mid', 'senior', 'lead', 'principal'
    closes_at TIMESTAMP,
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    max_experience INTEGER
);

CREATE INDEX IF NOT EXISTS idx_job_descriptions_sector ON job_descriptions(sector_id);
CREATE INDEX IF NOT EXISTS idx_job_descriptions_status ON job_descriptions(status);
CREATE INDEX IF NOT EXISTS idx_job_descriptions_level ON job_descriptions(experience_level);

-- Add candidates FK to job_descriptions (after both tables exist)
ALTER TABLE candidates
    ADD CONSTRAINT candidates_best_match_job_id_fkey
    FOREIGN KEY (best_match_job_id) REFERENCES job_descriptions(id) ON DELETE SET NULL;

-- Questions: Static question bank (legacy)
CREATE TABLE IF NOT EXISTS questions (
    id SERIAL PRIMARY KEY,
    question_type TEXT NOT NULL,    -- 'mcq', 'coding', 'psychometric'
    category TEXT,
    difficulty TEXT,
    content TEXT NOT NULL,
    options TEXT,                   -- JSON for MCQ options
    correct_answer TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================================
-- 2. SCHEDULING & ASSESSMENT TABLES
-- ============================================================================

-- Scheduled Assessments (created before assessments to break circular FK)
CREATE TABLE IF NOT EXISTS scheduled_assessments (
    id SERIAL PRIMARY KEY,
    candidate_id INTEGER NOT NULL,
    interviewer_id INTEGER NOT NULL,
    scheduled_time TIMESTAMP NOT NULL,
    status TEXT DEFAULT 'scheduled',        -- 'scheduled', 'in_progress', 'completed', 'cancelled'
    assessment_id INTEGER,                  -- FK added after assessments table
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    access_token TEXT UNIQUE,               -- Token for candidate to access assessment
    started_at TIMESTAMP,
    is_streaming BOOLEAN DEFAULT false,
    stream_started_at TIMESTAMP,
    stream_ended_at TIMESTAMP,
    is_technical_role BOOLEAN DEFAULT true, -- If false, no coding questions
    questions_data JSONB,                   -- Pre-generated questions at schedule time
    FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE,
    FOREIGN KEY (interviewer_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_scheduled_assessments_candidate ON scheduled_assessments(candidate_id);
CREATE INDEX IF NOT EXISTS idx_scheduled_assessments_time ON scheduled_assessments(scheduled_time);
CREATE INDEX IF NOT EXISTS idx_scheduled_assessments_token ON scheduled_assessments(access_token);

-- Assessments: Track each candidate's test
CREATE TABLE IF NOT EXISTS assessments (
    id SERIAL PRIMARY KEY,
    candidate_id INTEGER NOT NULL,
    job_id INTEGER,
    technical_score REAL,                   -- 0-100
    psychometric_score REAL,                -- 0-100
    overall_score REAL,                     -- Weighted average
    decision TEXT,                          -- 'Hire', 'No-Hire', 'Maybe'
    rationale TEXT,
    proctoring_violations INTEGER DEFAULT 0,
    status TEXT DEFAULT 'in_progress',      -- 'in_progress', 'completed'
    scheduled_assessment_id INTEGER,
    hiring_recommendation TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    questions_data JSONB,                   -- Generated MCQ, coding, psychometric questions
    time_elapsed_seconds INTEGER DEFAULT 0, -- Elapsed time for resume functionality
    FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE,
    FOREIGN KEY (job_id) REFERENCES job_descriptions(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_assessments_candidate ON assessments(candidate_id);
CREATE INDEX IF NOT EXISTS idx_assessments_status ON assessments(status);

-- Add circular FKs after both tables exist
ALTER TABLE scheduled_assessments
    ADD CONSTRAINT fk_sched_assessment
    FOREIGN KEY (assessment_id) REFERENCES assessments(id) ON DELETE SET NULL;

ALTER TABLE assessments
    ADD CONSTRAINT fk_assessment_scheduled
    FOREIGN KEY (scheduled_assessment_id) REFERENCES scheduled_assessments(id) ON DELETE SET NULL;


-- ============================================================================
-- 3. RESPONSE & SUBMISSION TABLES
-- ============================================================================

-- MCQ Responses
CREATE TABLE IF NOT EXISTS mcq_responses (
    id SERIAL PRIMARY KEY,
    assessment_id INTEGER NOT NULL,
    question_id INTEGER NOT NULL,
    selected_answer TEXT NOT NULL,
    is_correct BOOLEAN,
    time_spent INTEGER,                     -- Seconds
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (assessment_id) REFERENCES assessments(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_mcq_assessment ON mcq_responses(assessment_id);

-- Coding Submissions
CREATE TABLE IF NOT EXISTS coding_submissions (
    id SERIAL PRIMARY KEY,
    assessment_id INTEGER NOT NULL,
    problem_id INTEGER NOT NULL,
    language TEXT NOT NULL,
    code TEXT NOT NULL,
    test_cases_passed INTEGER,
    total_test_cases INTEGER,
    execution_time REAL,                    -- Seconds
    error_message TEXT,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (assessment_id) REFERENCES assessments(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_coding_assessment ON coding_submissions(assessment_id);

-- Psychometric Responses
CREATE TABLE IF NOT EXISTS psychometric_responses (
    id SERIAL PRIMARY KEY,
    assessment_id INTEGER NOT NULL,
    question_id INTEGER NOT NULL,
    trait TEXT NOT NULL,                     -- 'leadership', 'resilience', 'teamwork', etc.
    score INTEGER,                          -- 1-10
    scenario_response TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (assessment_id) REFERENCES assessments(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_psychometric_assessment ON psychometric_responses(assessment_id);


-- ============================================================================
-- 4. PROCTORING TABLES
-- ============================================================================

-- Proctoring Events (legacy event log)
CREATE TABLE IF NOT EXISTS proctoring_events (
    id SERIAL PRIMARY KEY,
    assessment_id INTEGER NOT NULL,
    event_type TEXT NOT NULL,               -- 'multiple_faces', 'no_face', 'tab_switch', 'copy_paste'
    severity TEXT NOT NULL,                 -- 'low', 'medium', 'high'
    details TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (assessment_id) REFERENCES assessments(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_proctoring_assessment ON proctoring_events(assessment_id);

-- Proctoring Violations (active violation tracking)
CREATE TABLE IF NOT EXISTS proctoring_violations (
    id SERIAL PRIMARY KEY,
    assessment_id INTEGER NOT NULL,
    violation_type TEXT NOT NULL,            -- 'no_face', 'multiple_faces', 'tab_switch', 'copy_paste'
    description TEXT,
    screenshot_url TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    severity TEXT,                           -- 'low', 'medium', 'high'
    FOREIGN KEY (assessment_id) REFERENCES assessments(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_proctoring_violations_assessment ON proctoring_violations(assessment_id);


-- ============================================================================
-- 5. EMAIL & COMMUNICATION TABLES
-- ============================================================================

-- Email Logs
CREATE TABLE IF NOT EXISTS email_logs (
    id SERIAL PRIMARY KEY,
    recipient_email TEXT NOT NULL,
    recipient_name TEXT NOT NULL,
    email_type TEXT NOT NULL,               -- 'rejection', 'assessment_invitation', 'final_decision'
    subject TEXT NOT NULL,
    status TEXT DEFAULT 'sent',             -- 'sent', 'failed', 'bounced'
    error_message TEXT,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_email_logs_recipient ON email_logs(recipient_email);
CREATE INDEX IF NOT EXISTS idx_email_logs_type ON email_logs(email_type);
CREATE INDEX IF NOT EXISTS idx_email_logs_status ON email_logs(status);


-- ============================================================================
-- 6. JOB MATCHING & RBAC TABLES
-- ============================================================================

-- Candidate-Job Matches
CREATE TABLE IF NOT EXISTS candidate_job_matches (
    id SERIAL PRIMARY KEY,
    candidate_id INTEGER NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    job_id INTEGER NOT NULL REFERENCES job_descriptions(id) ON DELETE CASCADE,
    match_score INTEGER DEFAULT 0,          -- 0-100
    skill_match_score INTEGER DEFAULT 0,    -- 0-100
    experience_match_score INTEGER DEFAULT 0, -- 0-100
    ai_reasoning TEXT,
    status TEXT DEFAULT 'auto_matched',     -- 'auto_matched', 'confirmed', 'rejected'
    matched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviewed_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    reviewed_at TIMESTAMP,
    UNIQUE(candidate_id, job_id)
);

CREATE INDEX IF NOT EXISTS idx_candidate_job_matches_candidate ON candidate_job_matches(candidate_id);
CREATE INDEX IF NOT EXISTS idx_candidate_job_matches_job ON candidate_job_matches(job_id);
CREATE INDEX IF NOT EXISTS idx_candidate_job_matches_score ON candidate_job_matches(match_score DESC);

-- Audit Log
CREATE TABLE IF NOT EXISTS audit_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    user_email TEXT,
    action TEXT NOT NULL,                   -- 'create_job', 'match_candidate', 'update_status'
    entity_type TEXT,                       -- 'job_posting', 'candidate', 'user'
    entity_id INTEGER,
    details JSONB,
    ip_address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_audit_log_user ON audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_action ON audit_log(action);
CREATE INDEX IF NOT EXISTS idx_audit_log_entity ON audit_log(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_created ON audit_log(created_at DESC);

-- Sector Email Configs
CREATE TABLE IF NOT EXISTS sector_email_configs (
    id SERIAL PRIMARY KEY,
    sector_id INTEGER NOT NULL REFERENCES sectors(id) ON DELETE CASCADE,
    email_address TEXT NOT NULL,
    smtp_host TEXT,
    smtp_port INTEGER DEFAULT 587,
    smtp_user TEXT,
    smtp_password_encrypted TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(sector_id)
);


-- ============================================================================
-- 7. CUSTOM QUESTION BANK TABLE
-- ============================================================================

-- Custom Question Bank: User-uploaded question files
CREATE TABLE IF NOT EXISTS custom_question_bank (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    questions_text TEXT NOT NULL,
    parsed_questions JSONB,
    uploaded_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    description TEXT,
    tags TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================================
-- 8. SEED DATA
-- ============================================================================

INSERT INTO sectors (name, description, email_alias) VALUES
    ('Engineering', 'Software Engineering & Development', 'eng@company.com'),
    ('Sales', 'Sales & Business Development', 'sales@company.com'),
    ('Marketing', 'Marketing & Communications', 'marketing@company.com'),
    ('Human Resources', 'HR & People Operations', 'hr@company.com'),
    ('Finance', 'Finance & Accounting', 'finance@company.com'),
    ('Operations', 'Operations & Infrastructure', 'ops@company.com'),
    ('Design', 'Product & UX Design', 'design@company.com'),
    ('Data Science', 'Data Science & Analytics', 'data@company.com')
ON CONFLICT (name) DO NOTHING;
