-- CYGNUSA Elite-Hire Database Schema
-- PostgreSQL version for Supabase Migration
-- All tables for the AI-enabled HR evaluation system

-- Users table: Store authentication data for interviewers, proctors, and admins
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

-- Candidates table: Store resume data and match scores
CREATE TABLE IF NOT EXISTS candidates (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    phone TEXT NOT NULL,
    resume_path TEXT NOT NULL,
    parsed_skills TEXT,  -- JSON format: ["Python", "JavaScript", "SQL"]
    years_experience INTEGER,
    education TEXT,
    match_score INTEGER,  -- 0-100
    shortlist_status TEXT,  -- "High Match", "Potential", "Reject"
    pros TEXT,  -- JSON format: ["pro1", "pro2", "pro3"] - AI generated
    cons TEXT,  -- JSON format: ["con1", "con2", "con3"] - AI generated
    status TEXT DEFAULT 'pending',  -- "pending", "shortlisted", "rejected", "assessment_scheduled", "assessment_completed"
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Job descriptions table: Store JD requirements
CREATE TABLE IF NOT EXISTS job_descriptions (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    required_skills TEXT,  -- JSON format: ["Python", "Django", "PostgreSQL"]
    min_experience INTEGER,
    department TEXT,
    location TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Questions table (create early, no dependencies)
CREATE TABLE IF NOT EXISTS questions (
    id SERIAL PRIMARY KEY,
    question_type TEXT NOT NULL,  -- "mcq", "coding", "psychometric"
    category TEXT,
    difficulty TEXT,
    content TEXT NOT NULL,
    options TEXT,  -- JSON for MCQ options
    correct_answer TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Scheduled assessments table: Track scheduled assessment sessions (NO FOREIGN KEY TO ASSESSMENTS YET)
CREATE TABLE IF NOT EXISTS scheduled_assessments (
    id SERIAL PRIMARY KEY,
    candidate_id INTEGER NOT NULL,
    interviewer_id INTEGER NOT NULL,
    scheduled_time TIMESTAMP NOT NULL,
    status TEXT DEFAULT 'scheduled',  -- 'scheduled', 'in_progress', 'completed', 'cancelled'
    assessment_id INTEGER,  -- Will add FK constraint later
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE,
    FOREIGN KEY (interviewer_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Create indexes for scheduled_assessments table
CREATE INDEX IF NOT EXISTS idx_scheduled_assessments_candidate ON scheduled_assessments(candidate_id);
CREATE INDEX IF NOT EXISTS idx_scheduled_assessments_time ON scheduled_assessments(scheduled_time);

-- Assessments table: Track each candidate's test
CREATE TABLE IF NOT EXISTS assessments (
    id SERIAL PRIMARY KEY,
    candidate_id INTEGER NOT NULL,
    job_id INTEGER,
    technical_score REAL,  -- 0-100
    psychometric_score REAL,  -- 0-100
    overall_score REAL,  -- weighted average
    decision TEXT,  -- "Hire", "No-Hire", "Maybe"
    rationale TEXT,  -- AI-generated explanation
    proctoring_violations INTEGER DEFAULT 0,
    status TEXT DEFAULT 'in_progress',  -- 'in_progress', 'completed'
    scheduled_assessment_id INTEGER,  -- Link to scheduled_assessments table
    hiring_recommendation TEXT,  -- AI-generated hiring recommendation with rationale
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    questions_data JSONB,  -- Stores generated MCQ, coding, psychometric questions for resume
    time_elapsed_seconds INTEGER DEFAULT 0,  -- Tracks elapsed time for resume functionality
    FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE,
    FOREIGN KEY (job_id) REFERENCES job_descriptions(id) ON DELETE SET NULL,
    FOREIGN KEY (scheduled_assessment_id) REFERENCES scheduled_assessments(id) ON DELETE SET NULL
);

-- MCQ responses table: Store MCQ answers
CREATE TABLE IF NOT EXISTS mcq_responses (
    id SERIAL PRIMARY KEY,
    assessment_id INTEGER NOT NULL,
    question_id INTEGER NOT NULL,
    selected_answer TEXT NOT NULL,  -- A, B, C, D
    is_correct BOOLEAN,
    time_spent INTEGER,  -- seconds
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (assessment_id) REFERENCES assessments(id) ON DELETE CASCADE
);

-- Coding submissions table: Store code submissions
CREATE TABLE IF NOT EXISTS coding_submissions (
    id SERIAL PRIMARY KEY,
    assessment_id INTEGER NOT NULL,
    problem_id INTEGER NOT NULL,
    language TEXT NOT NULL,  -- Python, JavaScript, Java
    code TEXT NOT NULL,
    test_cases_passed INTEGER,
    total_test_cases INTEGER,
    execution_time REAL,  -- seconds
    error_message TEXT,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (assessment_id) REFERENCES assessments(id) ON DELETE CASCADE
);

-- Proctoring events table: Log suspicious activities
CREATE TABLE IF NOT EXISTS proctoring_events (
    id SERIAL PRIMARY KEY,
    assessment_id INTEGER NOT NULL,
    event_type TEXT NOT NULL,  -- "multiple_faces", "no_face", "tab_switch", "copy_paste", "keyboard_shortcut"
    severity TEXT NOT NULL,  -- "low", "medium", "high"
    details TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (assessment_id) REFERENCES assessments(id) ON DELETE CASCADE
);

-- Proctoring violations table (for compatibility)
CREATE TABLE IF NOT EXISTS proctoring_violations (
    id SERIAL PRIMARY KEY,
    assessment_id INTEGER NOT NULL,
    violation_type TEXT NOT NULL,
    description TEXT,
    screenshot_url TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    severity TEXT,
    FOREIGN KEY (assessment_id) REFERENCES assessments(id) ON DELETE CASCADE
);

-- Psychometric responses table: Store personality test data
CREATE TABLE IF NOT EXISTS psychometric_responses (
    id SERIAL PRIMARY KEY,
    assessment_id INTEGER NOT NULL,
    question_id INTEGER NOT NULL,
    trait TEXT NOT NULL,  -- "leadership", "resilience", "teamwork", etc.
    score INTEGER,  -- 1-10
    scenario_response TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (assessment_id) REFERENCES assessments(id) ON DELETE CASCADE
);

-- Email logs table: Track all emails sent to candidates
CREATE TABLE IF NOT EXISTS email_logs (
    id SERIAL PRIMARY KEY,
    recipient_email TEXT NOT NULL,
    recipient_name TEXT NOT NULL,
    email_type TEXT NOT NULL,  -- "rejection", "assessment_invitation", "final_decision", etc.
    subject TEXT NOT NULL,
    status TEXT DEFAULT 'sent',  -- "sent", "failed", "bounced"
    error_message TEXT,  -- Error details if status is "failed"
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for email_logs table
CREATE INDEX IF NOT EXISTS idx_email_logs_recipient ON email_logs(recipient_email);
CREATE INDEX IF NOT EXISTS idx_email_logs_type ON email_logs(email_type);
CREATE INDEX IF NOT EXISTS idx_email_logs_status ON email_logs(status);

-- Create indices for better query performance
CREATE INDEX IF NOT EXISTS idx_candidates_email ON candidates(email);
CREATE INDEX IF NOT EXISTS idx_candidates_status ON candidates(shortlist_status);
CREATE INDEX IF NOT EXISTS idx_assessments_candidate ON assessments(candidate_id);
CREATE INDEX IF NOT EXISTS idx_assessments_status ON assessments(status);
CREATE INDEX IF NOT EXISTS idx_mcq_assessment ON mcq_responses(assessment_id);
CREATE INDEX IF NOT EXISTS idx_coding_assessment ON coding_submissions(assessment_id);
CREATE INDEX IF NOT EXISTS idx_proctoring_assessment ON proctoring_events(assessment_id);
CREATE INDEX IF NOT EXISTS idx_psychometric_assessment ON psychometric_responses(assessment_id);

-- Add the missing FK constraint to scheduled_assessments  (after assessments table exists)
ALTER TABLE scheduled_assessments 
DROP CONSTRAINT IF EXISTS scheduled_assessments_assessment_id_fkey;

ALTER TABLE scheduled_assessments 
ADD CONSTRAINT scheduled_assessments_assessment_id_fkey 
FOREIGN KEY (assessment_id) REFERENCES assessments(id) ON DELETE SET NULL;
