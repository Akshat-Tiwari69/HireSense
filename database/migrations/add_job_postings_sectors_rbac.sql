-- ============================================================================
-- Migration: Job Postings, Sectors, RBAC, and Skill-based Matching
-- Adds full job posting lifecycle, sector-based access, role hierarchy,
-- required/preferred skills, and candidate-job matching.
-- ============================================================================

-- 1) SECTORS TABLE
-- Represents organizational divisions (Engineering, Sales, Marketing, etc.)
CREATE TABLE IF NOT EXISTS sectors (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    email_alias TEXT UNIQUE,              -- e.g. eng@company.com, sales@company.com
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2) EXTEND USERS with sector + granular role
-- Roles: super_admin, sector_admin, recruiter, interviewer, proctor
ALTER TABLE users ADD COLUMN IF NOT EXISTS sector_id INTEGER REFERENCES sectors(id) ON DELETE SET NULL;
ALTER TABLE users ADD COLUMN IF NOT EXISTS permissions JSONB DEFAULT '{}';

-- Update role column to support new roles (backwards compatible — old 'admin' maps to 'super_admin')
-- We keep the existing role values working and add new ones
CREATE INDEX IF NOT EXISTS idx_users_sector ON users(sector_id);

-- 3) UPGRADE job_descriptions TABLE to full job_postings
-- Add columns that the existing table is missing
ALTER TABLE job_descriptions ADD COLUMN IF NOT EXISTS sector_id INTEGER REFERENCES sectors(id) ON DELETE SET NULL;
ALTER TABLE job_descriptions ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'active';
ALTER TABLE job_descriptions ADD COLUMN IF NOT EXISTS preferred_skills TEXT;     -- JSON array
ALTER TABLE job_descriptions ADD COLUMN IF NOT EXISTS salary_range TEXT;
ALTER TABLE job_descriptions ADD COLUMN IF NOT EXISTS employment_type TEXT DEFAULT 'full-time';
ALTER TABLE job_descriptions ADD COLUMN IF NOT EXISTS experience_level TEXT DEFAULT 'mid';  -- junior, mid, senior, lead, principal
ALTER TABLE job_descriptions ADD COLUMN IF NOT EXISTS closes_at TIMESTAMP;
ALTER TABLE job_descriptions ADD COLUMN IF NOT EXISTS created_by INTEGER REFERENCES users(id) ON DELETE SET NULL;
ALTER TABLE job_descriptions ADD COLUMN IF NOT EXISTS max_experience INTEGER;

CREATE INDEX IF NOT EXISTS idx_job_descriptions_sector ON job_descriptions(sector_id);
CREATE INDEX IF NOT EXISTS idx_job_descriptions_status ON job_descriptions(status);
CREATE INDEX IF NOT EXISTS idx_job_descriptions_level ON job_descriptions(experience_level);

-- 4) CANDIDATE-JOB MATCHING TABLE
-- AI-determined mapping of candidates to best-fit job postings
CREATE TABLE IF NOT EXISTS candidate_job_matches (
    id SERIAL PRIMARY KEY,
    candidate_id INTEGER NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    job_id INTEGER NOT NULL REFERENCES job_descriptions(id) ON DELETE CASCADE,
    match_score INTEGER DEFAULT 0,              -- 0-100
    skill_match_score INTEGER DEFAULT 0,        -- 0-100 how many required skills match
    experience_match_score INTEGER DEFAULT 0,   -- 0-100 experience fit
    ai_reasoning TEXT,                          -- AI explanation of the match
    status TEXT DEFAULT 'auto_matched',         -- auto_matched, confirmed, rejected
    matched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviewed_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    reviewed_at TIMESTAMP,
    UNIQUE(candidate_id, job_id)
);

CREATE INDEX IF NOT EXISTS idx_candidate_job_matches_candidate ON candidate_job_matches(candidate_id);
CREATE INDEX IF NOT EXISTS idx_candidate_job_matches_job ON candidate_job_matches(job_id);
CREATE INDEX IF NOT EXISTS idx_candidate_job_matches_score ON candidate_job_matches(match_score DESC);

-- 5) EXTEND CANDIDATES with skills and matched job
ALTER TABLE candidates ADD COLUMN IF NOT EXISTS parsed_skills_json JSONB DEFAULT '[]';
ALTER TABLE candidates ADD COLUMN IF NOT EXISTS best_match_job_id INTEGER REFERENCES job_descriptions(id) ON DELETE SET NULL;
ALTER TABLE candidates ADD COLUMN IF NOT EXISTS sector_id INTEGER REFERENCES sectors(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_candidates_best_job ON candidates(best_match_job_id);
CREATE INDEX IF NOT EXISTS idx_candidates_sector ON candidates(sector_id);

-- 6) AUDIT LOG TABLE
-- Tracks all user actions for compliance
CREATE TABLE IF NOT EXISTS audit_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    user_email TEXT,
    action TEXT NOT NULL,                     -- e.g. 'create_job', 'match_candidate', 'update_status'
    entity_type TEXT,                         -- e.g. 'job_posting', 'candidate', 'user'
    entity_id INTEGER,
    details JSONB,                            -- Additional context
    ip_address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_audit_log_user ON audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_action ON audit_log(action);
CREATE INDEX IF NOT EXISTS idx_audit_log_entity ON audit_log(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_created ON audit_log(created_at DESC);

-- 7) SECTOR EMAIL CONFIG TABLE
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

-- 8) SEED DEFAULT SECTORS
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
