-- CYGNUSA Elite-Hire Database Schema
-- All tables for the AI-enabled HR evaluation system

-- Candidates table: Store resume data and match scores
CREATE TABLE IF NOT EXISTS candidates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    phone TEXT NOT NULL,
    resume_path TEXT NOT NULL,
    parsed_skills TEXT,  -- JSON format: ["Python", "JavaScript", "SQL"]
    years_experience INTEGER,
    education TEXT,
    match_score INTEGER,  -- 0-100
    shortlist_status TEXT,  -- "High Match", "Potential", "Reject"
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Job descriptions table: Store JD requirements
CREATE TABLE IF NOT EXISTS job_descriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    required_skills TEXT,  -- JSON format: ["Python", "Django", "PostgreSQL"]
    min_experience INTEGER,
    department TEXT,
    location TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Assessments table: Track each candidate's test
CREATE TABLE IF NOT EXISTS assessments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    candidate_id INTEGER NOT NULL,
    job_id INTEGER,
    technical_score REAL,  -- 0-100
    psychometric_score REAL,  -- 0-100
    overall_score REAL,  -- weighted average
    decision TEXT,  -- "Hire", "No-Hire", "Maybe"
    rationale TEXT,  -- AI-generated explanation
    proctoring_violations INTEGER DEFAULT 0,
    status TEXT DEFAULT 'in_progress',  -- 'in_progress', 'completed'
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE,
    FOREIGN KEY (job_id) REFERENCES job_descriptions(id) ON DELETE SET NULL
);

-- MCQ responses table: Store MCQ answers
CREATE TABLE IF NOT EXISTS mcq_responses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
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
    id INTEGER PRIMARY KEY AUTOINCREMENT,
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
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    assessment_id INTEGER NOT NULL,
    event_type TEXT NOT NULL,  -- "multiple_faces", "no_face", "tab_switch", "copy_paste", "keyboard_shortcut"
    severity TEXT NOT NULL,  -- "low", "medium", "high"
    details TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (assessment_id) REFERENCES assessments(id) ON DELETE CASCADE
);

-- Psychometric responses table: Store personality test data
CREATE TABLE IF NOT EXISTS psychometric_responses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    assessment_id INTEGER NOT NULL,
    question_id INTEGER NOT NULL,
    trait TEXT NOT NULL,  -- "leadership", "resilience", "teamwork", etc.
    score INTEGER,  -- 1-10
    scenario_response TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (assessment_id) REFERENCES assessments(id) ON DELETE CASCADE
);

-- Create indices for better query performance
CREATE INDEX IF NOT EXISTS idx_candidates_email ON candidates(email);
CREATE INDEX IF NOT EXISTS idx_candidates_status ON candidates(shortlist_status);
CREATE INDEX IF NOT EXISTS idx_assessments_candidate ON assessments(candidate_id);
CREATE INDEX IF NOT EXISTS idx_assessments_status ON assessments(status);
CREATE INDEX IF NOT EXISTS idx_mcq_assessment ON mcq_responses(assessment_id);
CREATE INDEX IF NOT EXISTS idx_coding_assessment ON coding_submissions(assessment_id);
CREATE INDEX IF NOT EXISTS idx_proctoring_assessment ON proctoring_events(assessment_id);
CREATE INDEX IF NOT EXISTS idx_psychometric_assessment ON psychometric_responses(assessment_id);
