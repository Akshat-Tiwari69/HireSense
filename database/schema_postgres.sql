-- ============================================================================
-- HireSense canonical database schema (PostgreSQL / Supabase)
--
-- This file defines the schema for a fresh installation and is safe to run more
-- than once. Existing installations must run migrations in database/migrations;
-- 20260713_reconcile_canonical_schema.sql upgrades all known legacy variants.
--
-- Canonical names used by the application:
--   job_descriptions.created_by   (not created_by_id)
--   candidates.best_match_job_id  (not candidates.job_id)
--   audit_log                     (not admin_audit_log)
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
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Users: Authentication for interviewers, proctors, admins
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL,               -- 'interviewer', 'admin', 'proctor', 'super_admin', 'sector_admin', 'recruiter'
    name TEXT NOT NULL,
    sector_id INTEGER REFERENCES sectors(id) ON DELETE RESTRICT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT users_role_check CHECK (
        role IN ('interviewer', 'admin', 'proctor', 'super_admin', 'sector_admin', 'recruiter')
    ),
    CONSTRAINT users_sector_scope_check CHECK (
        role NOT IN ('sector_admin', 'recruiter') OR sector_id IS NOT NULL
    )
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email_lower_unique
    ON users(LOWER(email));
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_sector ON users(sector_id);

-- Candidates: Resume data and match scores
CREATE TABLE IF NOT EXISTS candidates (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT NOT NULL,
    resume_path TEXT NOT NULL,
    parsed_skills TEXT,                     -- JSON string: '["Python", "JavaScript"]'
    years_experience INTEGER,
    education TEXT,
    match_score INTEGER,                    -- 0-100
    shortlist_status TEXT,                  -- 'High Match', 'Potential', 'Reject'
    pros TEXT,                              -- Newline-separated strengths
    cons TEXT,                              -- Newline-separated weaknesses
    status TEXT NOT NULL DEFAULT 'pending', -- Application lifecycle state
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    best_match_job_id INTEGER,              -- FK added after job_descriptions table
    sector_id INTEGER REFERENCES sectors(id) ON DELETE SET NULL,
    CONSTRAINT candidates_years_experience_check CHECK (
        years_experience IS NULL OR years_experience >= 0
    ),
    CONSTRAINT candidates_match_score_check CHECK (
        match_score IS NULL OR match_score BETWEEN 0 AND 100
    ),
    CONSTRAINT candidates_shortlist_status_check CHECK (
        shortlist_status IS NULL OR shortlist_status IN ('High Match', 'Potential', 'Reject')
    ),
    CONSTRAINT candidates_status_check CHECK (
        status IN (
            'applied', 'absence_of_details', 'pending', 'under_review',
            'rejected', 'completed', 'hired'
        )
    )
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_candidates_email_lower_unique
    ON candidates(LOWER(email));
CREATE INDEX IF NOT EXISTS idx_candidates_status ON candidates(status);
CREATE INDEX IF NOT EXISTS idx_candidates_shortlist_status ON candidates(shortlist_status);
CREATE INDEX IF NOT EXISTS idx_candidates_best_job ON candidates(best_match_job_id);
CREATE INDEX IF NOT EXISTS idx_candidates_sector ON candidates(sector_id);

-- Job Descriptions: Job postings with skills and requirements
CREATE TABLE IF NOT EXISTS job_descriptions (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    required_skills TEXT,                   -- JSON or comma-separated skills
    min_experience INTEGER NOT NULL DEFAULT 0,
    department TEXT,
    work_mode TEXT NOT NULL DEFAULT 'On-Site',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    -- Extended columns (from job postings migration)
    sector_id INTEGER REFERENCES sectors(id) ON DELETE SET NULL,
    status TEXT NOT NULL DEFAULT 'active',  -- 'active', 'paused', 'closed', 'draft'
    preferred_skills TEXT,                  -- JSON array
    salary_range TEXT,
    employment_type TEXT NOT NULL DEFAULT 'full-time', -- 'full-time', 'part-time', 'contract', 'internship'
    experience_level TEXT NOT NULL DEFAULT 'mid', -- 'junior', 'mid', 'senior', 'lead', 'principal'
    closes_at TIMESTAMPTZ,
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    max_experience INTEGER,
    role_complexity_level TEXT NOT NULL DEFAULT 'intermediate',
    CONSTRAINT job_descriptions_experience_check CHECK (
        min_experience >= 0
        AND (max_experience IS NULL OR max_experience >= min_experience)
    ),
    CONSTRAINT job_descriptions_status_check CHECK (
        status IN ('active', 'paused', 'closed', 'draft')
    ),
    CONSTRAINT job_descriptions_type_check CHECK (
        employment_type IN ('full-time', 'part-time', 'contract', 'internship')
    ),
    CONSTRAINT job_descriptions_experience_level_check CHECK (
        experience_level IN ('junior', 'mid', 'senior', 'lead', 'principal')
    ),
    CONSTRAINT job_descriptions_work_mode_check CHECK (
        work_mode IN ('Remote', 'On-Site', 'Hybrid')
    )
);

CREATE INDEX IF NOT EXISTS idx_job_descriptions_sector ON job_descriptions(sector_id);
CREATE INDEX IF NOT EXISTS idx_job_descriptions_status ON job_descriptions(status);
CREATE INDEX IF NOT EXISTS idx_job_descriptions_level ON job_descriptions(experience_level);
CREATE INDEX IF NOT EXISTS idx_job_descriptions_created_by ON job_descriptions(created_by);

-- Add candidates FK to job_descriptions (after both tables exist)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conrelid = 'candidates'::regclass
          AND conname = 'candidates_best_match_job_id_fkey'
    ) THEN
        ALTER TABLE candidates
            ADD CONSTRAINT candidates_best_match_job_id_fkey
            FOREIGN KEY (best_match_job_id)
            REFERENCES job_descriptions(id) ON DELETE SET NULL;
    END IF;
END
$$;

-- ============================================================================
-- 2. SCHEDULING & ASSESSMENT TABLES
-- ============================================================================

-- Scheduled Assessments
CREATE TABLE IF NOT EXISTS scheduled_assessments (
    id SERIAL PRIMARY KEY,
    candidate_id INTEGER NOT NULL,
    interviewer_id INTEGER NOT NULL,
    scheduled_time TIMESTAMPTZ NOT NULL,
    status TEXT NOT NULL DEFAULT 'scheduled', -- 'scheduled', 'in_progress', 'completed', 'cancelled'
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    access_token_hash TEXT NOT NULL,        -- SHA-256 lookup hash; raw capability is never stored
    started_at TIMESTAMPTZ,
    is_technical_role BOOLEAN NOT NULL DEFAULT true, -- If false, no coding questions
    questions_data JSONB,                   -- Pre-generated questions at schedule time
    job_id INTEGER REFERENCES job_descriptions(id) ON DELETE SET NULL,
    proctor_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE,
    FOREIGN KEY (interviewer_id) REFERENCES users(id) ON DELETE RESTRICT,
    CONSTRAINT scheduled_assessments_status_check CHECK (
        status IN ('scheduled', 'in_progress', 'completed', 'cancelled')
    ),
    CONSTRAINT scheduled_assessments_access_token_hash_check CHECK (
        access_token_hash ~ '^[0-9a-f]{64}$'
    )
);

COMMENT ON COLUMN scheduled_assessments.access_token_hash IS
    'Irreversible SHA-256 lookup hash of the candidate assessment capability.';

CREATE INDEX IF NOT EXISTS idx_scheduled_assessments_candidate ON scheduled_assessments(candidate_id);
CREATE INDEX IF NOT EXISTS idx_scheduled_assessments_time ON scheduled_assessments(scheduled_time);
CREATE INDEX IF NOT EXISTS idx_scheduled_assessments_interviewer ON scheduled_assessments(interviewer_id);
CREATE INDEX IF NOT EXISTS idx_scheduled_assessments_job ON scheduled_assessments(job_id);
CREATE INDEX IF NOT EXISTS idx_scheduled_assessments_proctor ON scheduled_assessments(proctor_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_scheduled_assessments_access_token_hash_unique
    ON scheduled_assessments(access_token_hash);
CREATE UNIQUE INDEX IF NOT EXISTS idx_scheduled_assessments_candidate_active_unique
    ON scheduled_assessments(candidate_id)
    WHERE status IN ('scheduled', 'in_progress');

-- Assessments: Track each candidate's test
CREATE TABLE IF NOT EXISTS assessments (
    id SERIAL PRIMARY KEY,
    candidate_id INTEGER NOT NULL,
    job_id INTEGER,
    technical_score REAL,                   -- 0-100
    psychometric_score REAL,                -- 0-100
    overall_score REAL,                     -- Weighted average
    automated_recommendation TEXT,          -- Score-derived recommendation
    automated_rationale TEXT,               -- Score-derived explanation
    recommended_next_step TEXT,
    final_decision TEXT,                    -- Human decision: 'Hire' or 'No-Hire'
    final_rationale TEXT,
    proctoring_violations INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'in_progress', -- 'started', 'in_progress', 'completed'
    scheduled_assessment_id INTEGER,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    questions_data JSONB,                   -- Generated MCQ, coding, psychometric questions
    time_elapsed_seconds INTEGER NOT NULL DEFAULT 0, -- Elapsed time for resume functionality
    FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE,
    FOREIGN KEY (job_id) REFERENCES job_descriptions(id) ON DELETE SET NULL,
    CONSTRAINT assessments_scores_check CHECK (
        (technical_score IS NULL OR technical_score BETWEEN 0 AND 100)
        AND (psychometric_score IS NULL OR psychometric_score BETWEEN 0 AND 100)
        AND (overall_score IS NULL OR overall_score BETWEEN 0 AND 100)
    ),
    CONSTRAINT assessments_proctoring_violations_check CHECK (
        proctoring_violations >= 0
    ),
    CONSTRAINT assessments_status_check CHECK (
        status IN ('started', 'in_progress', 'completed')
    ),
    CONSTRAINT assessments_final_decision_check CHECK (
        final_decision IS NULL OR final_decision IN ('Hire', 'No-Hire')
    ),
    CONSTRAINT assessments_time_elapsed_check CHECK (
        time_elapsed_seconds BETWEEN 0 AND 3600
    )
);

CREATE INDEX IF NOT EXISTS idx_assessments_candidate ON assessments(candidate_id);
CREATE INDEX IF NOT EXISTS idx_assessments_status ON assessments(status);
CREATE INDEX IF NOT EXISTS idx_assessments_job ON assessments(job_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_assessments_scheduled_unique
    ON assessments(scheduled_assessment_id)
    WHERE scheduled_assessment_id IS NOT NULL;

-- Link each assessment to at most one scheduled assessment
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conrelid = 'assessments'::regclass
          AND conname = 'fk_assessment_scheduled'
    ) THEN
        ALTER TABLE assessments
            ADD CONSTRAINT fk_assessment_scheduled
            FOREIGN KEY (scheduled_assessment_id)
            REFERENCES scheduled_assessments(id) ON DELETE SET NULL;
    END IF;
END
$$;


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
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (assessment_id) REFERENCES assessments(id) ON DELETE CASCADE,
    CONSTRAINT mcq_responses_question_check CHECK (question_id > 0),
    CONSTRAINT mcq_responses_time_check CHECK (
        time_spent IS NULL OR time_spent >= 0
    )
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_mcq_assessment_question_unique
    ON mcq_responses(assessment_id, question_id);

-- Coding Submissions
CREATE TABLE IF NOT EXISTS coding_submissions (
    id SERIAL PRIMARY KEY,
    assessment_id INTEGER NOT NULL,
    problem_id INTEGER NOT NULL,
    language TEXT NOT NULL,
    code TEXT NOT NULL,
    test_cases_passed INTEGER NOT NULL DEFAULT 0,
    total_test_cases INTEGER NOT NULL DEFAULT 0,
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (assessment_id) REFERENCES assessments(id) ON DELETE CASCADE,
    CONSTRAINT coding_submissions_counts_check CHECK (
        problem_id > 0
        AND test_cases_passed >= 0
        AND total_test_cases >= 0
        AND test_cases_passed <= total_test_cases
    )
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_coding_assessment_problem_unique
    ON coding_submissions(assessment_id, problem_id);

-- Psychometric Responses
CREATE TABLE IF NOT EXISTS psychometric_responses (
    id SERIAL PRIMARY KEY,
    assessment_id INTEGER NOT NULL,
    question_id INTEGER NOT NULL,
    trait TEXT NOT NULL,                     -- 'leadership', 'resilience', 'teamwork', etc.
    score INTEGER,                          -- 1-10 when scored
    scenario_response TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (assessment_id) REFERENCES assessments(id) ON DELETE CASCADE,
    CONSTRAINT psychometric_responses_question_check CHECK (question_id > 0),
    CONSTRAINT psychometric_responses_score_check CHECK (score BETWEEN 1 AND 10)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_psychometric_assessment_question_unique
    ON psychometric_responses(assessment_id, question_id);


-- ============================================================================
-- 4. PROCTORING TABLES
-- ============================================================================

-- Proctoring Violations (active violation tracking)
CREATE TABLE IF NOT EXISTS proctoring_violations (
    id SERIAL PRIMARY KEY,
    assessment_id INTEGER NOT NULL,
    violation_type TEXT NOT NULL,            -- 'no_face', 'multiple_faces', 'tab_switch', 'copy_paste'
    description TEXT,
    screenshot_path TEXT,                   -- Private storage path, never public URL
    timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    severity TEXT NOT NULL DEFAULT 'medium', -- 'low', 'medium', 'high', 'critical'
    FOREIGN KEY (assessment_id) REFERENCES assessments(id) ON DELETE CASCADE,
    CONSTRAINT proctoring_violations_severity_check CHECK (
        severity IN ('low', 'medium', 'high', 'critical')
    )
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
    status TEXT NOT NULL DEFAULT 'sent',    -- 'sent', 'failed', 'bounced'
    error_message TEXT,
    sent_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT email_logs_status_check CHECK (
        status IN ('sent', 'failed', 'bounced')
    )
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
    match_score INTEGER NOT NULL DEFAULT 0, -- 0-100
    skill_match_score INTEGER NOT NULL DEFAULT 0, -- 0-100
    experience_match_score INTEGER NOT NULL DEFAULT 0, -- 0-100
    ai_reasoning TEXT,
    status TEXT NOT NULL DEFAULT 'auto_matched', -- 'auto_matched', 'confirmed', 'rejected'
    matched_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    reviewed_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    reviewed_at TIMESTAMPTZ,
    CONSTRAINT candidate_job_matches_scores_check CHECK (
        match_score BETWEEN 0 AND 100
        AND skill_match_score BETWEEN 0 AND 100
        AND experience_match_score BETWEEN 0 AND 100
    ),
    CONSTRAINT candidate_job_matches_status_check CHECK (
        status IN ('auto_matched', 'confirmed', 'rejected')
    )
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_candidate_job_matches_candidate_job_unique
    ON candidate_job_matches(candidate_id, job_id);
CREATE INDEX IF NOT EXISTS idx_candidate_job_matches_job ON candidate_job_matches(job_id);
CREATE INDEX IF NOT EXISTS idx_candidate_job_matches_score ON candidate_job_matches(match_score DESC);
CREATE INDEX IF NOT EXISTS idx_candidate_job_matches_reviewed_by ON candidate_job_matches(reviewed_by);

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
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_audit_log_user ON audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_action ON audit_log(action);
CREATE INDEX IF NOT EXISTS idx_audit_log_entity ON audit_log(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_created ON audit_log(created_at DESC);

-- ============================================================================
-- 7. CUSTOM QUESTION BANK TABLE
-- ============================================================================

-- Custom Question Bank: User-uploaded question files
CREATE TABLE IF NOT EXISTS custom_question_bank (
    id SERIAL PRIMARY KEY,
    original_filename VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    questions_text TEXT NOT NULL,
    parsed_questions JSONB,
    uploaded_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    description TEXT,
    tags TEXT,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_custom_question_bank_uploaded_by
    ON custom_question_bank(uploaded_by);


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


-- ============================================================================
-- 9. SUPABASE DATA API HARDENING
-- ============================================================================

-- HireSense accesses PostgreSQL exclusively through the Flask backend. Supabase
-- grants its Data API roles broad default privileges, so remove those grants and
-- enable RLS as defense in depth. The backend's direct postgres connection is
-- unaffected; a future direct-to-Supabase client must add explicit policies.
DO $$
DECLARE
    target_schema TEXT := current_schema();
    api_role TEXT;
    app_table TEXT;
BEGIN
    EXECUTE format('REVOKE ALL PRIVILEGES ON SCHEMA %I FROM PUBLIC', target_schema);

    FOR api_role IN
        SELECT rolname
        FROM pg_roles
        WHERE rolname = ANY (ARRAY['anon', 'authenticated'])
    LOOP
        EXECUTE format(
            'REVOKE USAGE ON SCHEMA %I FROM %I', target_schema, api_role
        );
        EXECUTE format(
            'REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA %I FROM %I',
            target_schema, api_role
        );
        EXECUTE format(
            'REVOKE ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA %I FROM %I',
            target_schema, api_role
        );
        EXECUTE format(
            'REVOKE ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA %I FROM %I',
            target_schema, api_role
        );
        EXECUTE format(
            'ALTER DEFAULT PRIVILEGES IN SCHEMA %I '
            'REVOKE ALL PRIVILEGES ON TABLES FROM %I',
            target_schema, api_role
        );
        EXECUTE format(
            'ALTER DEFAULT PRIVILEGES IN SCHEMA %I '
            'REVOKE ALL PRIVILEGES ON SEQUENCES FROM %I',
            target_schema, api_role
        );
        EXECUTE format(
            'ALTER DEFAULT PRIVILEGES IN SCHEMA %I '
            'REVOKE ALL PRIVILEGES ON FUNCTIONS FROM %I',
            target_schema, api_role
        );
    END LOOP;

    FOREACH app_table IN ARRAY ARRAY[
        'sectors', 'users', 'job_descriptions', 'candidates',
        'scheduled_assessments', 'assessments', 'mcq_responses',
        'coding_submissions', 'psychometric_responses',
        'proctoring_violations', 'email_logs', 'candidate_job_matches',
        'audit_log', 'custom_question_bank'
    ]
    LOOP
        IF to_regclass(format('%I.%I', target_schema, app_table)) IS NOT NULL THEN
            EXECUTE format(
                'ALTER TABLE %I.%I ENABLE ROW LEVEL SECURITY',
                target_schema, app_table
            );
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'hiresense_app')
               AND NOT EXISTS (
                   SELECT 1
                   FROM pg_policies
                   WHERE schemaname = target_schema
                     AND tablename = app_table
                     AND policyname = 'hiresense_backend_access'
               ) THEN
                EXECUTE format(
                    'CREATE POLICY hiresense_backend_access ON %I.%I '
                    'FOR ALL TO hiresense_app USING (true) WITH CHECK (true)',
                    target_schema, app_table
                );
            END IF;
        END IF;
    END LOOP;

    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'hiresense_app') THEN
        EXECUTE format(
            'GRANT USAGE ON SCHEMA %I TO hiresense_app', target_schema
        );
        EXECUTE format(
            'GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA %I '
            'TO hiresense_app', target_schema
        );
        EXECUTE format(
            'GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA %I TO hiresense_app',
            target_schema
        );
        EXECUTE format(
            'ALTER DEFAULT PRIVILEGES IN SCHEMA %I '
            'GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO hiresense_app',
            target_schema
        );
        EXECUTE format(
            'ALTER DEFAULT PRIVILEGES IN SCHEMA %I '
            'GRANT USAGE, SELECT ON SEQUENCES TO hiresense_app',
            target_schema
        );
    END IF;
END
$$;
