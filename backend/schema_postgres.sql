-- CYGNUSA Elite-Hire Database Schema (PostgreSQL)
-- All tables for the AI-enabled HR evaluation system

-- Users table: Store authentication data for interviewers, admins, and proctors
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL,  -- "interviewer", "admin", "proctor"
    name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for users table
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- Job descriptions table: Store JD requirements
CREATE TABLE IF NOT EXISTS job_descriptions (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    required_skills TEXT,  -- JSON format: ["Python", "Django", "PostgreSQL"]
    min_experience INTEGER,
    max_experience INTEGER,
    department TEXT,
    location TEXT,
    is_active BOOLEAN DEFAULT true,
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Candidates table: Store resume data and match scores
CREATE TABLE IF NOT EXISTS candidates (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    phone TEXT NOT NULL,
    resume_path TEXT NOT NULL,
    original_filename TEXT,
    parsed_skills TEXT,  -- JSON format: ["Python", "JavaScript", "SQL"]
    years_experience INTEGER,
    education TEXT,
    match_score INTEGER,  -- 0-100
    shortlist_status TEXT,  -- "High Match", "Potential", "Reject"
    pros TEXT,  -- JSON format: ["pro1", "pro2", "pro3"] - AI generated
    cons TEXT,  -- JSON format: ["con1", "con2", "con3"] - AI generated
    overall_assessment TEXT,  -- AI generated summary
    recommendation TEXT,  -- Strong/Good/Moderate/Weak Match
    confidence_score INTEGER,  -- AI confidence 0-100
    enhanced_match_score REAL,  -- AI-enhanced score
    status TEXT DEFAULT 'pending',  -- "pending", "under_review", "rejected", "hired"
    job_id INTEGER REFERENCES job_descriptions(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Scheduled assessments table: Track scheduled assessment sessions
CREATE TABLE IF NOT EXISTS scheduled_assessments (
    id SERIAL PRIMARY KEY,
    candidate_id INTEGER NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    interviewer_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    job_id INTEGER REFERENCES job_descriptions(id) ON DELETE SET NULL,
    scheduled_time TIMESTAMP NOT NULL,
    assessment_token TEXT UNIQUE,  -- Secure token for assessment URL
    status TEXT DEFAULT 'scheduled',  -- 'scheduled', 'in_progress', 'completed', 'cancelled', 'expired'
    proctoring_enabled BOOLEAN DEFAULT true,  -- Whether proctoring is required
    notes TEXT,  -- Additional instructions for candidate
    assessment_id INTEGER,  -- Will be set when assessment starts
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for scheduled_assessments table
CREATE INDEX IF NOT EXISTS idx_scheduled_assessments_candidate ON scheduled_assessments(candidate_id);
CREATE INDEX IF NOT EXISTS idx_scheduled_assessments_time ON scheduled_assessments(scheduled_time);
CREATE INDEX IF NOT EXISTS idx_scheduled_assessments_token ON scheduled_assessments(assessment_token);

-- Assessments table: Track each candidate's test
CREATE TABLE IF NOT EXISTS assessments (
    id SERIAL PRIMARY KEY,
    candidate_id INTEGER NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    job_id INTEGER REFERENCES job_descriptions(id) ON DELETE SET NULL,
    scheduled_assessment_id INTEGER REFERENCES scheduled_assessments(id) ON DELETE SET NULL,
    technical_score REAL,  -- 0-100
    psychometric_score REAL,  -- 0-100
    mcq_score REAL,  -- 0-100
    coding_score REAL,  -- 0-100
    overall_score REAL,  -- weighted average
    decision TEXT,  -- "Hire", "No-Hire", "Maybe", "Pending"
    rationale TEXT,  -- AI-generated explanation
    hiring_recommendation TEXT,  -- AI-generated hiring recommendation
    proctoring_violations INTEGER DEFAULT 0,
    status TEXT DEFAULT 'in_progress',  -- 'in_progress', 'completed', 'cancelled'
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add foreign key from scheduled_assessments to assessments
ALTER TABLE scheduled_assessments 
ADD CONSTRAINT fk_scheduled_assessment_id 
FOREIGN KEY (assessment_id) REFERENCES assessments(id) ON DELETE SET NULL;

-- MCQ responses table: Store MCQ answers
CREATE TABLE IF NOT EXISTS mcq_responses (
    id SERIAL PRIMARY KEY,
    assessment_id INTEGER NOT NULL REFERENCES assessments(id) ON DELETE CASCADE,
    question_id INTEGER NOT NULL,
    selected_answer TEXT NOT NULL,  -- A, B, C, D or index
    is_correct BOOLEAN,
    time_spent INTEGER,  -- seconds
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Coding submissions table: Store code submissions
CREATE TABLE IF NOT EXISTS coding_submissions (
    id SERIAL PRIMARY KEY,
    assessment_id INTEGER NOT NULL REFERENCES assessments(id) ON DELETE CASCADE,
    problem_id INTEGER NOT NULL,
    language TEXT NOT NULL,  -- Python, JavaScript, Java, C++
    code TEXT NOT NULL,
    test_cases_passed INTEGER,
    total_test_cases INTEGER,
    score REAL,  -- 0-100
    execution_time REAL,  -- milliseconds
    error_message TEXT,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Psychometric responses table: Store personality test data
CREATE TABLE IF NOT EXISTS psychometric_responses (
    id SERIAL PRIMARY KEY,
    assessment_id INTEGER NOT NULL REFERENCES assessments(id) ON DELETE CASCADE,
    scenario_id INTEGER NOT NULL,
    trait TEXT NOT NULL,  -- "leadership", "resilience", "teamwork", etc.
    score INTEGER,  -- 1-10
    response_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Proctoring events table: Log suspicious activities
CREATE TABLE IF NOT EXISTS proctoring_events (
    id SERIAL PRIMARY KEY,
    assessment_id INTEGER NOT NULL REFERENCES assessments(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,  -- "multiple_faces", "no_face", "tab_switch", "copy_paste"
    severity TEXT NOT NULL DEFAULT 'medium',  -- "low", "medium", "high", "critical"
    details TEXT,
    reviewed BOOLEAN DEFAULT false,
    reviewer_notes TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Email logs table: Track all emails sent to candidates
CREATE TABLE IF NOT EXISTS email_logs (
    id SERIAL PRIMARY KEY,
    recipient_email TEXT NOT NULL,
    recipient_name TEXT NOT NULL,
    email_type TEXT NOT NULL,  -- "application_received", "rejection", "assessment_invitation", "final_decision"
    subject TEXT NOT NULL,
    status TEXT DEFAULT 'sent',  -- "sent", "failed", "pending"
    error_message TEXT,  -- Error details if status is "failed"
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Interviewer preferences table: Store interviewer settings
CREATE TABLE IF NOT EXISTS interviewer_preferences (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    default_proctoring BOOLEAN DEFAULT true,
    email_notifications BOOLEAN DEFAULT true,
    auto_schedule_window INTEGER DEFAULT 30,  -- minutes
    preferred_assessment_duration INTEGER DEFAULT 60,  -- minutes
    settings_json TEXT,  -- Additional settings as JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create remaining indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_candidates_email ON candidates(email);
CREATE INDEX IF NOT EXISTS idx_candidates_status ON candidates(status);
CREATE INDEX IF NOT EXISTS idx_assessments_candidate ON assessments(candidate_id);
CREATE INDEX IF NOT EXISTS idx_assessments_status ON assessments(status);
CREATE INDEX IF NOT EXISTS idx_mcq_assessment ON mcq_responses(assessment_id);
CREATE INDEX IF NOT EXISTS idx_coding_assessment ON coding_submissions(assessment_id);
CREATE INDEX IF NOT EXISTS idx_proctoring_assessment ON proctoring_events(assessment_id);
CREATE INDEX IF NOT EXISTS idx_psychometric_assessment ON psychometric_responses(assessment_id);
CREATE INDEX IF NOT EXISTS idx_email_logs_recipient ON email_logs(recipient_email);
CREATE INDEX IF NOT EXISTS idx_email_logs_type ON email_logs(email_type);
CREATE INDEX IF NOT EXISTS idx_email_logs_status ON email_logs(status);
