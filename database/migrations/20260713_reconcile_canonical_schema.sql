-- Reconcile legacy HireSense schemas with database/schema_postgres.sql.
--
-- Safety guarantees:
--   * every useful legacy value is copied to its canonical home before duplicate
--     aliases are removed;
--   * only objects proven unused by the runtime are deleted;
--   * integrity checks abort the transaction instead of silently rewriting invalid
--     historical business data;
--   * uniqueness is enabled only when existing data has no duplicates. A warning
--     identifies any key that needs an explicit, business-approved data cleanup.
--
-- Canonical names:
--   job_descriptions.created_by   (legacy: created_by_id)
--   job_descriptions.work_mode    (legacy: location)
--   candidates.best_match_job_id  (legacy: job_id)
--   assessments.scheduled_assessment_id (legacy reverse assessment_id link)
--   audit_log                     (legacy: admin_audit_log)

BEGIN;

-- --------------------------------------------------------------------------
-- Runtime-required columns
-- --------------------------------------------------------------------------

DO $job_work_mode$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = current_schema()
          AND table_name = 'job_descriptions'
          AND column_name = 'location'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = current_schema()
          AND table_name = 'job_descriptions'
          AND column_name = 'work_mode'
    ) THEN
        ALTER TABLE job_descriptions RENAME COLUMN location TO work_mode;
    ELSIF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = current_schema()
          AND table_name = 'job_descriptions'
          AND column_name = 'location'
    ) AND EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = current_schema()
          AND table_name = 'job_descriptions'
          AND column_name = 'work_mode'
    ) THEN
        UPDATE job_descriptions
        SET work_mode = COALESCE(
            NULLIF(BTRIM(work_mode), ''),
            NULLIF(BTRIM(location), '')
        );
        ALTER TABLE job_descriptions DROP COLUMN location;
    ELSIF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = current_schema()
          AND table_name = 'job_descriptions'
          AND column_name = 'work_mode'
    ) THEN
        ALTER TABLE job_descriptions ADD COLUMN work_mode TEXT;
    END IF;
END
$job_work_mode$;

ALTER TABLE job_descriptions
    ADD COLUMN IF NOT EXISTS created_by INTEGER,
    ADD COLUMN IF NOT EXISTS role_complexity_level TEXT DEFAULT 'intermediate';

ALTER TABLE candidates
    ADD COLUMN IF NOT EXISTS best_match_job_id INTEGER;

ALTER TABLE assessments
    ADD COLUMN IF NOT EXISTS scheduled_assessment_id INTEGER,
    ADD COLUMN IF NOT EXISTS automated_recommendation TEXT,
    ADD COLUMN IF NOT EXISTS automated_rationale TEXT,
    ADD COLUMN IF NOT EXISTS recommended_next_step TEXT,
    ADD COLUMN IF NOT EXISTS final_decision TEXT,
    ADD COLUMN IF NOT EXISTS final_rationale TEXT;

ALTER TABLE proctoring_violations
    ADD COLUMN IF NOT EXISTS screenshot_path TEXT;

ALTER TABLE scheduled_assessments
    ADD COLUMN IF NOT EXISTS job_id INTEGER,
    ADD COLUMN IF NOT EXISTS proctor_id INTEGER,
    ADD COLUMN IF NOT EXISTS access_token_hash TEXT;

-- Candidate invitation tokens are bearer capabilities. Preserve every existing
-- invitation while replacing the recoverable secret with an irreversible lookup
-- hash. PostgreSQL's SHA-256 bytea function is built in and needs no extension.
DO $assessment_tokens$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = current_schema()
          AND table_name = 'scheduled_assessments'
          AND column_name = 'access_token'
    ) THEN
        EXECUTE $sql$
            UPDATE scheduled_assessments
            SET access_token_hash = COALESCE(
                access_token_hash,
                encode(sha256(convert_to(access_token, 'UTF8')), 'hex')
            )
            WHERE access_token IS NOT NULL
        $sql$;
    END IF;

    IF EXISTS (
        SELECT 1
        FROM scheduled_assessments
        WHERE access_token_hash IS NULL
           OR access_token_hash !~ '^[0-9a-f]{64}$'
    ) THEN
        RAISE EXCEPTION
            'Cannot secure scheduled assessment tokens: missing or invalid token hash';
    END IF;
END
$assessment_tokens$;

ALTER TABLE scheduled_assessments
    DROP COLUMN IF EXISTS access_token;

COMMENT ON COLUMN scheduled_assessments.access_token_hash IS
    'Irreversible SHA-256 lookup hash of the candidate assessment capability.';

UPDATE job_descriptions
SET role_complexity_level = 'intermediate'
WHERE role_complexity_level IS NULL;

ALTER TABLE job_descriptions
    ALTER COLUMN role_complexity_level SET DEFAULT 'intermediate';

-- --------------------------------------------------------------------------
-- Backfill legacy aliases without deleting them
-- --------------------------------------------------------------------------

DO $$
DECLARE
    legacy_link_conflict BOOLEAN;
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = current_schema()
          AND table_name = 'job_descriptions'
          AND column_name = 'created_by_id'
    ) THEN
        EXECUTE $sql$
            UPDATE job_descriptions
            SET created_by = created_by_id
            WHERE created_by IS NULL
              AND created_by_id IS NOT NULL
        $sql$;

        COMMENT ON COLUMN job_descriptions.created_by_id IS
            'Deprecated legacy alias. Use job_descriptions.created_by.';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = current_schema()
          AND table_name = 'candidates'
          AND column_name = 'job_id'
    ) THEN
        EXECUTE $sql$
            UPDATE candidates
            SET best_match_job_id = job_id
            WHERE best_match_job_id IS NULL
              AND job_id IS NOT NULL
        $sql$;

        COMMENT ON COLUMN candidates.job_id IS
            'Deprecated legacy alias. Use candidates.best_match_job_id.';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = current_schema()
          AND table_name = 'scheduled_assessments'
          AND column_name = 'assessment_id'
    ) THEN
        EXECUTE $sql$
            SELECT EXISTS (
                SELECT legacy_schedule.assessment_id
                FROM scheduled_assessments AS legacy_schedule
                WHERE legacy_schedule.assessment_id IS NOT NULL
                GROUP BY legacy_schedule.assessment_id
                HAVING COUNT(*) > 1
            )
        $sql$ INTO legacy_link_conflict;
        IF legacy_link_conflict THEN
            RAISE EXCEPTION
                'Multiple schedules reference the same legacy assessment; refusing to discard ambiguous relationships';
        END IF;

        EXECUTE $sql$
            SELECT EXISTS (
                SELECT 1
                FROM scheduled_assessments AS legacy_schedule
                JOIN assessments AS linked_assessment
                  ON linked_assessment.id = legacy_schedule.assessment_id
                WHERE legacy_schedule.assessment_id IS NOT NULL
                  AND linked_assessment.scheduled_assessment_id IS NOT NULL
                  AND linked_assessment.scheduled_assessment_id <> legacy_schedule.id
            )
        $sql$ INTO legacy_link_conflict;
        IF legacy_link_conflict THEN
            RAISE EXCEPTION
                'A legacy reverse schedule link conflicts with the canonical schedule link; refusing to discard either relationship';
        END IF;

        EXECUTE $sql$
            WITH legacy_links AS (
                SELECT
                    legacy_schedule.assessment_id,
                    legacy_schedule.id AS scheduled_assessment_id
                FROM scheduled_assessments AS legacy_schedule
                WHERE legacy_schedule.assessment_id IS NOT NULL
                  AND NOT EXISTS (
                      SELECT 1
                      FROM assessments AS linked_assessment
                      WHERE linked_assessment.scheduled_assessment_id =
                            legacy_schedule.id
                  )
            )
            UPDATE assessments AS target_assessment
            SET scheduled_assessment_id = legacy_link.scheduled_assessment_id
            FROM legacy_links AS legacy_link
            WHERE target_assessment.id = legacy_link.assessment_id
              AND target_assessment.scheduled_assessment_id IS NULL
        $sql$;
    END IF;
END
$$;

-- Split the legacy overloaded decision fields into immutable automated output
-- and an explicit human decision. Existing values are preserved according to
-- their known domain; a prior human overwrite cannot recreate discarded AI text.
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = current_schema()
          AND table_name = 'assessments'
          AND column_name = 'decision'
    ) THEN
        EXECUTE $sql$
            UPDATE assessments
            SET automated_recommendation = COALESCE(
                    automated_recommendation,
                    CASE WHEN decision NOT IN ('Hire', 'No-Hire') THEN decision END
                ),
                automated_rationale = COALESCE(
                    automated_rationale,
                    CASE WHEN decision NOT IN ('Hire', 'No-Hire') THEN rationale END
                ),
                final_decision = COALESCE(
                    final_decision,
                    CASE WHEN decision IN ('Hire', 'No-Hire') THEN decision END
                ),
                final_rationale = COALESCE(
                    final_rationale,
                    CASE WHEN decision IN ('Hire', 'No-Hire') THEN rationale END
                )
        $sql$;
    END IF;

    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = current_schema()
          AND table_name = 'assessments'
          AND column_name = 'hiring_recommendation'
    ) THEN
        EXECUTE $sql$
            UPDATE assessments
            SET recommended_next_step = COALESCE(
                recommended_next_step, hiring_recommendation
            )
        $sql$;
    END IF;

    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = current_schema()
          AND table_name = 'proctoring_violations'
          AND column_name = 'screenshot_url'
    ) THEN
        EXECUTE $sql$
            UPDATE proctoring_violations
            SET screenshot_path = COALESCE(screenshot_path, screenshot_url)
        $sql$;
    END IF;
END
$$;

ALTER TABLE assessments
    DROP COLUMN IF EXISTS decision,
    DROP COLUMN IF EXISTS rationale,
    DROP COLUMN IF EXISTS hiring_recommendation;
ALTER TABLE proctoring_violations
    DROP COLUMN IF EXISTS screenshot_url;

ALTER TABLE scheduled_assessments
    DROP COLUMN IF EXISTS assessment_id;

-- Remove aliases and fields that have no production readers or writers. Uploaded
-- question-bank display names live in original_filename; preserve any old value
-- before removing the duplicate filename column.
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = current_schema()
          AND table_name = 'custom_question_bank'
          AND column_name = 'filename'
    ) THEN
        EXECUTE $sql$
            UPDATE custom_question_bank
            SET original_filename = filename
            WHERE (original_filename IS NULL OR BTRIM(original_filename) = '')
              AND filename IS NOT NULL
        $sql$;
    END IF;
END
$$;

ALTER TABLE users
    DROP COLUMN IF EXISTS permissions;
ALTER TABLE candidates
    DROP COLUMN IF EXISTS job_id,
    DROP COLUMN IF EXISTS parsed_skills_json;
ALTER TABLE job_descriptions
    DROP COLUMN IF EXISTS created_by_id;
ALTER TABLE scheduled_assessments
    DROP COLUMN IF EXISTS is_streaming,
    DROP COLUMN IF EXISTS stream_started_at,
    DROP COLUMN IF EXISTS stream_ended_at;
ALTER TABLE coding_submissions
    DROP COLUMN IF EXISTS execution_time,
    DROP COLUMN IF EXISTS error_message;
ALTER TABLE custom_question_bank
    DROP COLUMN IF EXISTS filename;

-- --------------------------------------------------------------------------
-- Canonical audit log and migration of the legacy admin-only audit table
-- --------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS audit_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    user_email TEXT,
    action TEXT NOT NULL,
    entity_type TEXT,
    entity_id INTEGER,
    details JSONB,
    ip_address TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

DO $$
DECLARE
    legacy_action_column TEXT;
BEGIN
    IF to_regclass('admin_audit_log') IS NULL THEN
        RETURN;
    END IF;

    SELECT column_name
    INTO legacy_action_column
    FROM information_schema.columns
    WHERE table_schema = current_schema()
      AND table_name = 'admin_audit_log'
      AND column_name IN ('action', 'action_type')
    ORDER BY CASE column_name WHEN 'action' THEN 1 ELSE 2 END
    LIMIT 1;

    IF legacy_action_column IS NULL THEN
        IF EXISTS (SELECT 1 FROM admin_audit_log LIMIT 1) THEN
            RAISE EXCEPTION USING
                MESSAGE = 'admin_audit_log contains rows but has neither action nor action_type; refusing to discard audit history',
                HINT = 'Export or explicitly map the legacy audit rows before rerunning this migration.';
        END IF;
        RETURN;
    END IF;

    EXECUTE format($sql$
        INSERT INTO audit_log (
            user_id,
            user_email,
            action,
            entity_type,
            entity_id,
            details,
            ip_address,
            created_at
        )
        SELECT
            legacy.admin_id,
            NULL,
            COALESCE(legacy.%I::TEXT, 'legacy_admin_action'),
            legacy.entity_type,
            legacy.entity_id,
            jsonb_build_object(
                'legacy_source', 'admin_audit_log',
                'legacy_id', legacy.id,
                'old_values', legacy.old_values,
                'new_values', legacy.new_values
            ),
            legacy.ip_address,
            legacy.timestamp
        FROM admin_audit_log AS legacy
        WHERE NOT EXISTS (
            SELECT 1
            FROM audit_log AS canonical
            WHERE canonical.details @> jsonb_build_object(
                'legacy_source', 'admin_audit_log',
                'legacy_id', legacy.id
            )
        )
    $sql$, legacy_action_column);

    IF EXISTS (
        SELECT 1
        FROM admin_audit_log AS legacy
        WHERE NOT EXISTS (
            SELECT 1
            FROM audit_log AS canonical
            WHERE canonical.details @> jsonb_build_object(
                'legacy_source', 'admin_audit_log',
                'legacy_id', legacy.id
            )
        )
    ) THEN
        RAISE EXCEPTION USING
            MESSAGE = 'Not every admin_audit_log row was copied; refusing to drop the legacy table',
            HINT = 'Inspect the legacy audit schema and migrate every row explicitly.';
    END IF;

    COMMENT ON TABLE admin_audit_log IS
        'Deprecated legacy audit table. New writes belong in audit_log.';
END
$$;

DROP TABLE IF EXISTS admin_audit_log;

-- These tables were retired before a stable cross-version column contract was
-- established.  Never guess at a data mapping: an operator must explicitly
-- export or migrate any surviving rows before reconciliation may remove them.
DO $$
DECLARE
    legacy_retired_table TEXT;
    has_legacy_rows BOOLEAN;
BEGIN
    FOREACH legacy_retired_table IN ARRAY ARRAY[
        'proctoring_events',
        'questions',
        'sector_email_configs'
    ]
    LOOP
        IF to_regclass(format('public.%I', legacy_retired_table)) IS NULL THEN
            CONTINUE;
        END IF;

        EXECUTE format(
            'SELECT EXISTS (SELECT 1 FROM public.%I LIMIT 1)',
            legacy_retired_table
        ) INTO has_legacy_rows;

        IF has_legacy_rows THEN
            RAISE EXCEPTION USING
                MESSAGE = format(
                    'Legacy table %I contains data and cannot be dropped automatically',
                    legacy_retired_table
                ),
                HINT = 'Export or explicitly migrate every legacy row, empty the table, and rerun this migration.';
        END IF;
    END LOOP;
END
$$;

DROP TABLE IF EXISTS proctoring_events;
DROP TABLE IF EXISTS questions;
DROP TABLE IF EXISTS sector_email_configs;

-- --------------------------------------------------------------------------
-- Foreign keys. Column-based checks tolerate old constraint names.
-- --------------------------------------------------------------------------

DO $$
DECLARE
    stale_constraint TEXT;
BEGIN
    -- A few historical migrations created these columns with PostgreSQL's
    -- default ON DELETE NO ACTION. Replace only incompatible constraints; no
    -- table data is changed or discarded.
    FOR stale_constraint IN
        SELECT constraint_record.conname
        FROM pg_constraint AS constraint_record
        JOIN pg_attribute AS constrained_column
          ON constrained_column.attrelid = constraint_record.conrelid
         AND constrained_column.attnum = ANY (constraint_record.conkey)
        WHERE constraint_record.conrelid = 'job_descriptions'::regclass
          AND constraint_record.contype = 'f'
          AND constrained_column.attname = 'created_by'
          AND (
              constraint_record.confrelid <> 'users'::regclass
              OR constraint_record.confdeltype <> 'n'
          )
    LOOP
        EXECUTE format(
            'ALTER TABLE job_descriptions DROP CONSTRAINT %I',
            stale_constraint
        );
    END LOOP;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint AS constraint_record
        JOIN pg_attribute AS constrained_column
          ON constrained_column.attrelid = constraint_record.conrelid
         AND constrained_column.attnum = ANY (constraint_record.conkey)
        WHERE constraint_record.conrelid = 'job_descriptions'::regclass
          AND constraint_record.contype = 'f'
          AND constrained_column.attname = 'created_by'
          AND constraint_record.confrelid = 'users'::regclass
          AND constraint_record.confdeltype = 'n'
    ) THEN
        ALTER TABLE job_descriptions
            ADD CONSTRAINT job_descriptions_created_by_fkey
            FOREIGN KEY (created_by) REFERENCES users(id)
            ON DELETE SET NULL NOT VALID;
    END IF;

    FOR stale_constraint IN
        SELECT constraint_record.conname
        FROM pg_constraint AS constraint_record
        JOIN pg_attribute AS constrained_column
          ON constrained_column.attrelid = constraint_record.conrelid
         AND constrained_column.attnum = ANY (constraint_record.conkey)
        WHERE constraint_record.conrelid = 'candidates'::regclass
          AND constraint_record.contype = 'f'
          AND constrained_column.attname = 'best_match_job_id'
          AND (
              constraint_record.confrelid <> 'job_descriptions'::regclass
              OR constraint_record.confdeltype <> 'n'
          )
    LOOP
        EXECUTE format(
            'ALTER TABLE candidates DROP CONSTRAINT %I',
            stale_constraint
        );
    END LOOP;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint AS constraint_record
        JOIN pg_attribute AS constrained_column
          ON constrained_column.attrelid = constraint_record.conrelid
         AND constrained_column.attnum = ANY (constraint_record.conkey)
        WHERE constraint_record.conrelid = 'candidates'::regclass
          AND constraint_record.contype = 'f'
          AND constrained_column.attname = 'best_match_job_id'
          AND constraint_record.confrelid = 'job_descriptions'::regclass
          AND constraint_record.confdeltype = 'n'
    ) THEN
        ALTER TABLE candidates
            ADD CONSTRAINT candidates_best_match_job_id_fkey
            FOREIGN KEY (best_match_job_id) REFERENCES job_descriptions(id)
            ON DELETE SET NULL NOT VALID;
    END IF;

    FOR stale_constraint IN
        SELECT constraint_record.conname
        FROM pg_constraint AS constraint_record
        JOIN pg_attribute AS constrained_column
          ON constrained_column.attrelid = constraint_record.conrelid
         AND constrained_column.attnum = ANY (constraint_record.conkey)
        WHERE constraint_record.conrelid = 'scheduled_assessments'::regclass
          AND constraint_record.contype = 'f'
          AND constrained_column.attname = 'job_id'
          AND (
              constraint_record.confrelid <> 'job_descriptions'::regclass
              OR constraint_record.confdeltype <> 'n'
          )
    LOOP
        EXECUTE format(
            'ALTER TABLE scheduled_assessments DROP CONSTRAINT %I',
            stale_constraint
        );
    END LOOP;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint AS constraint_record
        JOIN pg_attribute AS constrained_column
          ON constrained_column.attrelid = constraint_record.conrelid
         AND constrained_column.attnum = ANY (constraint_record.conkey)
        WHERE constraint_record.conrelid = 'scheduled_assessments'::regclass
          AND constraint_record.contype = 'f'
          AND constrained_column.attname = 'job_id'
          AND constraint_record.confrelid = 'job_descriptions'::regclass
          AND constraint_record.confdeltype = 'n'
    ) THEN
        ALTER TABLE scheduled_assessments
            ADD CONSTRAINT scheduled_assessments_job_id_fkey
            FOREIGN KEY (job_id) REFERENCES job_descriptions(id)
            ON DELETE SET NULL NOT VALID;
    END IF;

    FOR stale_constraint IN
        SELECT constraint_record.conname
        FROM pg_constraint AS constraint_record
        JOIN pg_attribute AS constrained_column
          ON constrained_column.attrelid = constraint_record.conrelid
         AND constrained_column.attnum = ANY (constraint_record.conkey)
        WHERE constraint_record.conrelid = 'scheduled_assessments'::regclass
          AND constraint_record.contype = 'f'
          AND constrained_column.attname = 'proctor_id'
          AND (
              constraint_record.confrelid <> 'users'::regclass
              OR constraint_record.confdeltype <> 'n'
          )
    LOOP
        EXECUTE format(
            'ALTER TABLE scheduled_assessments DROP CONSTRAINT %I',
            stale_constraint
        );
    END LOOP;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint AS constraint_record
        JOIN pg_attribute AS constrained_column
          ON constrained_column.attrelid = constraint_record.conrelid
         AND constrained_column.attnum = ANY (constraint_record.conkey)
        WHERE constraint_record.conrelid = 'scheduled_assessments'::regclass
          AND constraint_record.contype = 'f'
          AND constrained_column.attname = 'proctor_id'
          AND constraint_record.confrelid = 'users'::regclass
          AND constraint_record.confdeltype = 'n'
    ) THEN
        ALTER TABLE scheduled_assessments
            ADD CONSTRAINT scheduled_assessments_proctor_id_fkey
            FOREIGN KEY (proctor_id) REFERENCES users(id)
            ON DELETE SET NULL NOT VALID;
    END IF;

    FOR stale_constraint IN
        SELECT constraint_record.conname
        FROM pg_constraint AS constraint_record
        JOIN pg_attribute AS constrained_column
          ON constrained_column.attrelid = constraint_record.conrelid
         AND constrained_column.attnum = ANY (constraint_record.conkey)
        WHERE constraint_record.conrelid = 'assessments'::regclass
          AND constraint_record.contype = 'f'
          AND constrained_column.attname = 'scheduled_assessment_id'
          AND (
              constraint_record.confrelid <> 'scheduled_assessments'::regclass
              OR constraint_record.confdeltype <> 'n'
          )
    LOOP
        EXECUTE format(
            'ALTER TABLE assessments DROP CONSTRAINT %I',
            stale_constraint
        );
    END LOOP;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint AS constraint_record
        JOIN pg_attribute AS constrained_column
          ON constrained_column.attrelid = constraint_record.conrelid
         AND constrained_column.attnum = ANY (constraint_record.conkey)
        WHERE constraint_record.conrelid = 'assessments'::regclass
          AND constraint_record.contype = 'f'
          AND constrained_column.attname = 'scheduled_assessment_id'
          AND constraint_record.confrelid = 'scheduled_assessments'::regclass
          AND constraint_record.confdeltype = 'n'
    ) THEN
        ALTER TABLE assessments
            ADD CONSTRAINT assessments_scheduled_assessment_id_fkey
            FOREIGN KEY (scheduled_assessment_id)
            REFERENCES scheduled_assessments(id)
            ON DELETE SET NULL NOT VALID;
    END IF;
END
$$;

-- Sector-scoped staff cannot be orphaned because their role requires a sector.
-- Require explicit reassignment before a sector is deleted.
DO $$
DECLARE
    stale_constraint TEXT;
BEGIN
    FOR stale_constraint IN
        SELECT constraint_record.conname
        FROM pg_constraint AS constraint_record
        JOIN pg_attribute AS constrained_column
          ON constrained_column.attrelid = constraint_record.conrelid
         AND constrained_column.attnum = ANY (constraint_record.conkey)
        WHERE constraint_record.conrelid = 'users'::regclass
          AND constraint_record.contype = 'f'
          AND constrained_column.attname = 'sector_id'
          AND (
              constraint_record.confrelid <> 'sectors'::regclass
              OR constraint_record.confdeltype <> 'r'
          )
    LOOP
        EXECUTE format(
            'ALTER TABLE users DROP CONSTRAINT %I',
            stale_constraint
        );
    END LOOP;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint AS constraint_record
        JOIN pg_attribute AS constrained_column
          ON constrained_column.attrelid = constraint_record.conrelid
         AND constrained_column.attnum = ANY (constraint_record.conkey)
        WHERE constraint_record.conrelid = 'users'::regclass
          AND constraint_record.contype = 'f'
          AND constrained_column.attname = 'sector_id'
          AND constraint_record.confrelid = 'sectors'::regclass
          AND constraint_record.confdeltype = 'r'
    ) THEN
        ALTER TABLE users
            ADD CONSTRAINT users_sector_id_fkey
            FOREIGN KEY (sector_id) REFERENCES sectors(id)
            ON DELETE RESTRICT;
    END IF;
END
$$;

-- Staff accounts with assigned hiring work cannot be deleted by cascading away
-- schedules. The API returns a conflict and requires explicit reassignment.
DO $$
DECLARE
    stale_constraint TEXT;
BEGIN
    FOR stale_constraint IN
        SELECT constraint_record.conname
        FROM pg_constraint AS constraint_record
        JOIN pg_attribute AS constrained_column
          ON constrained_column.attrelid = constraint_record.conrelid
         AND constrained_column.attnum = ANY (constraint_record.conkey)
        WHERE constraint_record.conrelid = 'scheduled_assessments'::regclass
          AND constraint_record.contype = 'f'
          AND constrained_column.attname = 'interviewer_id'
          AND (
              constraint_record.confrelid <> 'users'::regclass
              OR constraint_record.confdeltype <> 'r'
          )
    LOOP
        EXECUTE format(
            'ALTER TABLE scheduled_assessments DROP CONSTRAINT %I',
            stale_constraint
        );
    END LOOP;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint AS constraint_record
        JOIN pg_attribute AS constrained_column
          ON constrained_column.attrelid = constraint_record.conrelid
         AND constrained_column.attnum = ANY (constraint_record.conkey)
        WHERE constraint_record.conrelid = 'scheduled_assessments'::regclass
          AND constraint_record.contype = 'f'
          AND constrained_column.attname = 'interviewer_id'
          AND constraint_record.confrelid = 'users'::regclass
          AND constraint_record.confdeltype = 'r'
    ) THEN
        ALTER TABLE scheduled_assessments
            ADD CONSTRAINT scheduled_assessments_interviewer_id_fkey
            FOREIGN KEY (interviewer_id) REFERENCES users(id)
            ON DELETE RESTRICT NOT VALID;
    END IF;
END
$$;

-- --------------------------------------------------------------------------
-- Indexes used by runtime joins and filters
-- --------------------------------------------------------------------------

DROP INDEX IF EXISTS idx_users_email;
DROP INDEX IF EXISTS idx_candidates_email;
DROP INDEX IF EXISTS idx_candidate_job_matches_candidate;
DROP INDEX IF EXISTS idx_mcq_assessment;
DROP INDEX IF EXISTS idx_coding_assessment;
DROP INDEX IF EXISTS idx_psychometric_assessment;
DROP INDEX IF EXISTS idx_scheduled_assessments_token;
DROP INDEX IF EXISTS idx_candidates_status;

CREATE INDEX IF NOT EXISTS idx_candidates_status ON candidates(status);
CREATE INDEX IF NOT EXISTS idx_candidates_shortlist_status ON candidates(shortlist_status);
CREATE INDEX IF NOT EXISTS idx_candidates_best_job ON candidates(best_match_job_id);
CREATE INDEX IF NOT EXISTS idx_candidates_sector ON candidates(sector_id);
CREATE INDEX IF NOT EXISTS idx_candidate_job_matches_job ON candidate_job_matches(job_id);
CREATE INDEX IF NOT EXISTS idx_candidate_job_matches_score ON candidate_job_matches(match_score DESC);
CREATE INDEX IF NOT EXISTS idx_candidate_job_matches_reviewed_by ON candidate_job_matches(reviewed_by);
CREATE INDEX IF NOT EXISTS idx_custom_question_bank_uploaded_by ON custom_question_bank(uploaded_by);
CREATE INDEX IF NOT EXISTS idx_job_descriptions_created_by ON job_descriptions(created_by);
CREATE INDEX IF NOT EXISTS idx_job_descriptions_level ON job_descriptions(experience_level);
CREATE INDEX IF NOT EXISTS idx_job_descriptions_sector ON job_descriptions(sector_id);
CREATE INDEX IF NOT EXISTS idx_job_descriptions_status ON job_descriptions(status);
CREATE INDEX IF NOT EXISTS idx_scheduled_assessments_candidate ON scheduled_assessments(candidate_id);
CREATE INDEX IF NOT EXISTS idx_scheduled_assessments_interviewer ON scheduled_assessments(interviewer_id);
CREATE INDEX IF NOT EXISTS idx_scheduled_assessments_job ON scheduled_assessments(job_id);
CREATE INDEX IF NOT EXISTS idx_scheduled_assessments_proctor ON scheduled_assessments(proctor_id);
CREATE INDEX IF NOT EXISTS idx_scheduled_assessments_time ON scheduled_assessments(scheduled_time);
CREATE INDEX IF NOT EXISTS idx_assessments_candidate ON assessments(candidate_id);
CREATE INDEX IF NOT EXISTS idx_assessments_job ON assessments(job_id);
CREATE INDEX IF NOT EXISTS idx_assessments_status ON assessments(status);
CREATE INDEX IF NOT EXISTS idx_proctoring_violations_assessment ON proctoring_violations(assessment_id);
CREATE INDEX IF NOT EXISTS idx_email_logs_recipient ON email_logs(recipient_email);
CREATE INDEX IF NOT EXISTS idx_email_logs_status ON email_logs(status);
CREATE INDEX IF NOT EXISTS idx_email_logs_type ON email_logs(email_type);
CREATE INDEX IF NOT EXISTS idx_audit_log_user ON audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_action ON audit_log(action);
CREATE INDEX IF NOT EXISTS idx_audit_log_entity ON audit_log(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_created ON audit_log(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_sector ON users(sector_id);

-- --------------------------------------------------------------------------
-- One logical response per assessment/question (or coding problem).
-- Existing duplicates are never deleted automatically.
-- --------------------------------------------------------------------------

DO $$
BEGIN
    IF to_regclass('idx_users_email_lower_unique') IS NULL THEN
        IF EXISTS (
            SELECT 1
            FROM users
            GROUP BY LOWER(email)
            HAVING COUNT(*) > 1
        ) THEN
            RAISE WARNING 'Cannot create case-insensitive user email index: duplicate LOWER(email) values exist';
        ELSE
            CREATE UNIQUE INDEX idx_users_email_lower_unique
                ON users(LOWER(email));
        END IF;
    END IF;

    IF to_regclass('idx_candidates_email_lower_unique') IS NULL THEN
        IF EXISTS (
            SELECT 1
            FROM candidates
            GROUP BY LOWER(email)
            HAVING COUNT(*) > 1
        ) THEN
            RAISE WARNING 'Cannot create case-insensitive candidate email index: duplicate LOWER(email) values exist';
        ELSE
            CREATE UNIQUE INDEX idx_candidates_email_lower_unique
                ON candidates(LOWER(email));
        END IF;
    END IF;

    IF to_regclass('idx_scheduled_assessments_access_token_hash_unique') IS NULL THEN
        IF EXISTS (
            SELECT 1
            FROM scheduled_assessments
            GROUP BY access_token_hash
            HAVING COUNT(*) > 1
        ) THEN
            RAISE WARNING 'Cannot create unique assessment token-hash index: duplicate hashes exist';
        ELSE
            CREATE UNIQUE INDEX idx_scheduled_assessments_access_token_hash_unique
                ON scheduled_assessments(access_token_hash);
        END IF;
    END IF;

    IF to_regclass('idx_candidate_job_matches_candidate_job_unique') IS NULL THEN
        IF EXISTS (
            SELECT 1
            FROM candidate_job_matches
            GROUP BY candidate_id, job_id
            HAVING COUNT(*) > 1
        ) THEN
            RAISE WARNING 'Cannot create unique candidate/job index: duplicate matches exist';
        ELSE
            CREATE UNIQUE INDEX idx_candidate_job_matches_candidate_job_unique
                ON candidate_job_matches(candidate_id, job_id);
        END IF;
    END IF;

    IF to_regclass('idx_assessments_scheduled_unique') IS NULL THEN
        IF EXISTS (
            SELECT 1
            FROM assessments
            WHERE scheduled_assessment_id IS NOT NULL
            GROUP BY scheduled_assessment_id
            HAVING COUNT(*) > 1
        ) THEN
            RAISE WARNING 'Cannot create unique assessment/schedule index: duplicate scheduled_assessment_id values exist';
        ELSE
            CREATE UNIQUE INDEX idx_assessments_scheduled_unique
                ON assessments(scheduled_assessment_id)
                WHERE scheduled_assessment_id IS NOT NULL;
        END IF;
    END IF;

    IF to_regclass('idx_scheduled_assessments_candidate_active_unique') IS NULL THEN
        IF EXISTS (
            SELECT 1
            FROM scheduled_assessments
            WHERE status IN ('scheduled', 'in_progress')
            GROUP BY candidate_id
            HAVING COUNT(*) > 1
        ) THEN
            RAISE WARNING 'Cannot create unique active schedule index: candidates with multiple active schedules exist';
        ELSE
            CREATE UNIQUE INDEX idx_scheduled_assessments_candidate_active_unique
                ON scheduled_assessments(candidate_id)
                WHERE status IN ('scheduled', 'in_progress');
        END IF;
    END IF;

    IF to_regclass('idx_mcq_assessment_question_unique') IS NULL THEN
        IF EXISTS (
            SELECT 1
            FROM mcq_responses
            GROUP BY assessment_id, question_id
            HAVING COUNT(*) > 1
        ) THEN
            RAISE WARNING 'Cannot create unique MCQ response index: duplicate assessment/question values exist';
        ELSE
            CREATE UNIQUE INDEX idx_mcq_assessment_question_unique
                ON mcq_responses(assessment_id, question_id);
        END IF;
    END IF;

    IF to_regclass('idx_coding_assessment_problem_unique') IS NULL THEN
        IF EXISTS (
            SELECT 1
            FROM coding_submissions
            GROUP BY assessment_id, problem_id
            HAVING COUNT(*) > 1
        ) THEN
            RAISE WARNING 'Cannot create unique coding response index: duplicate assessment/problem values exist';
        ELSE
            CREATE UNIQUE INDEX idx_coding_assessment_problem_unique
                ON coding_submissions(assessment_id, problem_id);
        END IF;
    END IF;

    IF to_regclass('idx_psychometric_assessment_question_unique') IS NULL THEN
        IF EXISTS (
            SELECT 1
            FROM psychometric_responses
            GROUP BY assessment_id, question_id
            HAVING COUNT(*) > 1
        ) THEN
            RAISE WARNING 'Cannot create unique psychometric response index: duplicate assessment/question values exist';
        ELSE
            CREATE UNIQUE INDEX idx_psychometric_assessment_question_unique
                ON psychometric_responses(assessment_id, question_id);
        END IF;
    END IF;
END
$$;

-- The named expression/composite indexes above are the canonical uniqueness
-- enforcers. Remove older constraints only after their replacement exists.
DO $$
DECLARE
    constraint_name TEXT;
BEGIN
    IF to_regclass('idx_users_email_lower_unique') IS NOT NULL THEN
        FOR constraint_name IN
            SELECT conname
            FROM pg_constraint
            WHERE conrelid = 'users'::regclass
              AND contype = 'u'
              AND conkey = ARRAY[(
                  SELECT attnum FROM pg_attribute
                  WHERE attrelid = 'users'::regclass AND attname = 'email'
              )]::SMALLINT[]
        LOOP
            EXECUTE format('ALTER TABLE users DROP CONSTRAINT %I', constraint_name);
        END LOOP;
    END IF;

    IF to_regclass('idx_candidates_email_lower_unique') IS NOT NULL THEN
        FOR constraint_name IN
            SELECT conname
            FROM pg_constraint
            WHERE conrelid = 'candidates'::regclass
              AND contype = 'u'
              AND conkey = ARRAY[(
                  SELECT attnum FROM pg_attribute
                  WHERE attrelid = 'candidates'::regclass AND attname = 'email'
              )]::SMALLINT[]
        LOOP
            EXECUTE format('ALTER TABLE candidates DROP CONSTRAINT %I', constraint_name);
        END LOOP;
    END IF;

    IF to_regclass('idx_scheduled_assessments_access_token_hash_unique') IS NOT NULL THEN
        FOR constraint_name IN
            SELECT conname
            FROM pg_constraint
            WHERE conrelid = 'scheduled_assessments'::regclass
              AND contype = 'u'
              AND conkey = ARRAY[(
                  SELECT attnum FROM pg_attribute
                  WHERE attrelid = 'scheduled_assessments'::regclass
                    AND attname = 'access_token_hash'
              )]::SMALLINT[]
        LOOP
            EXECUTE format(
                'ALTER TABLE scheduled_assessments DROP CONSTRAINT %I',
                constraint_name
            );
        END LOOP;
    END IF;

    IF to_regclass('idx_candidate_job_matches_candidate_job_unique') IS NOT NULL THEN
        FOR constraint_name IN
            SELECT conname
            FROM pg_constraint
            WHERE conrelid = 'candidate_job_matches'::regclass
              AND contype = 'u'
              AND conkey = ARRAY[
                  (SELECT attnum FROM pg_attribute
                   WHERE attrelid = 'candidate_job_matches'::regclass
                     AND attname = 'candidate_id'),
                  (SELECT attnum FROM pg_attribute
                   WHERE attrelid = 'candidate_job_matches'::regclass
                     AND attname = 'job_id')
              ]::SMALLINT[]
        LOOP
            EXECUTE format(
                'ALTER TABLE candidate_job_matches DROP CONSTRAINT %I',
                constraint_name
            );
        END LOOP;
    END IF;
END
$$;

-- --------------------------------------------------------------------------
-- Timezone-safe timestamps
-- --------------------------------------------------------------------------

DO $$
DECLARE
    target_schema TEXT := current_schema();
    column_record RECORD;
BEGIN
    FOR column_record IN
        SELECT *
        FROM (VALUES
            ('assessments', 'started_at', 'UTC'),
            ('assessments', 'completed_at', 'UTC'),
            ('assessments', 'created_at', 'UTC'),
            ('audit_log', 'created_at', 'UTC'),
            ('candidate_job_matches', 'matched_at', 'UTC'),
            ('candidate_job_matches', 'reviewed_at', 'UTC'),
            ('candidates', 'created_at', 'UTC'),
            ('candidates', 'updated_at', 'UTC'),
            ('coding_submissions', 'submitted_at', 'UTC'),
            ('custom_question_bank', 'created_at', 'UTC'),
            ('custom_question_bank', 'updated_at', 'UTC'),
            ('email_logs', 'sent_at', 'UTC'),
            ('job_descriptions', 'created_at', 'UTC'),
            ('job_descriptions', 'updated_at', 'UTC'),
            ('job_descriptions', 'closes_at', 'Asia/Kolkata'),
            ('mcq_responses', 'created_at', 'UTC'),
            ('proctoring_violations', 'timestamp', 'UTC'),
            ('psychometric_responses', 'created_at', 'UTC'),
            ('scheduled_assessments', 'scheduled_time', 'Asia/Kolkata'),
            ('scheduled_assessments', 'created_at', 'UTC'),
            ('scheduled_assessments', 'updated_at', 'UTC'),
            ('scheduled_assessments', 'started_at', 'UTC'),
            ('sectors', 'created_at', 'UTC'),
            ('sectors', 'updated_at', 'UTC'),
            ('users', 'created_at', 'UTC'),
            ('users', 'updated_at', 'UTC')
        ) AS timestamp_columns(table_name, column_name, assumed_timezone)
    LOOP
        IF EXISTS (
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema = target_schema
              AND table_name = column_record.table_name
              AND column_name = column_record.column_name
              AND data_type = 'timestamp without time zone'
        ) THEN
            EXECUTE format(
                'ALTER TABLE %I.%I ALTER COLUMN %I TYPE TIMESTAMPTZ '
                'USING %I AT TIME ZONE %L',
                target_schema,
                column_record.table_name,
                column_record.column_name,
                column_record.column_name,
                column_record.assumed_timezone
            );
        END IF;
    END LOOP;
END
$$;

-- --------------------------------------------------------------------------
-- Canonical values, required fields, and database-level domain checks
-- --------------------------------------------------------------------------

UPDATE users
SET role = LOWER(BTRIM(role)),
    created_at = COALESCE(created_at, CURRENT_TIMESTAMP),
    updated_at = COALESCE(updated_at, CURRENT_TIMESTAMP);

UPDATE candidates
SET status = CASE LOWER(BTRIM(COALESCE(status, '')))
        WHEN '' THEN 'pending'
        WHEN 'shortlisted' THEN 'under_review'
        WHEN 'assessment_scheduled' THEN 'under_review'
        WHEN 'scheduled' THEN 'under_review'
        WHEN 'in_progress' THEN 'under_review'
        WHEN 'assessment_completed' THEN 'completed'
        ELSE LOWER(BTRIM(status))
    END,
    shortlist_status = CASE LOWER(BTRIM(COALESCE(shortlist_status, '')))
        WHEN '' THEN NULL
        WHEN 'pending review' THEN NULL
        WHEN 'high match' THEN 'High Match'
        WHEN 'potential' THEN 'Potential'
        WHEN 'reject' THEN 'Reject'
        ELSE shortlist_status
    END,
    created_at = COALESCE(created_at, CURRENT_TIMESTAMP),
    updated_at = COALESCE(updated_at, CURRENT_TIMESTAMP);

UPDATE job_descriptions
SET min_experience = COALESCE(min_experience, 0),
    status = LOWER(BTRIM(COALESCE(status, 'active'))),
    employment_type = LOWER(BTRIM(COALESCE(employment_type, 'full-time'))),
    experience_level = LOWER(BTRIM(COALESCE(experience_level, 'mid'))),
    work_mode = CASE
        WHEN LOWER(BTRIM(COALESCE(work_mode, ''))) IN (
            'remote', 'fully remote', 'work from home', 'wfh'
        ) THEN 'Remote'
        WHEN LOWER(BTRIM(COALESCE(work_mode, ''))) IN (
            'hybrid', 'hybrid remote'
        ) THEN 'Hybrid'
        WHEN LOWER(BTRIM(COALESCE(work_mode, ''))) IN (
            'on-site', 'on site', 'onsite', 'office', 'in office'
        ) THEN 'On-Site'
        ELSE 'On-Site'
    END,
    role_complexity_level = COALESCE(
        NULLIF(LOWER(BTRIM(role_complexity_level)), ''),
        'intermediate'
    ),
    created_at = COALESCE(created_at, CURRENT_TIMESTAMP),
    updated_at = COALESCE(updated_at, CURRENT_TIMESTAMP);

UPDATE scheduled_assessments
SET status = LOWER(BTRIM(COALESCE(status, 'scheduled'))),
    is_technical_role = COALESCE(is_technical_role, true),
    created_at = COALESCE(created_at, CURRENT_TIMESTAMP),
    updated_at = COALESCE(updated_at, CURRENT_TIMESTAMP);

UPDATE assessments
SET status = LOWER(BTRIM(COALESCE(status, 'in_progress'))),
    proctoring_violations = COALESCE(proctoring_violations, 0),
    time_elapsed_seconds = COALESCE(time_elapsed_seconds, 0),
    created_at = COALESCE(created_at, CURRENT_TIMESTAMP);

UPDATE mcq_responses
SET created_at = COALESCE(created_at, CURRENT_TIMESTAMP);

UPDATE coding_submissions
SET test_cases_passed = COALESCE(test_cases_passed, 0),
    total_test_cases = COALESCE(total_test_cases, 0),
    submitted_at = COALESCE(submitted_at, CURRENT_TIMESTAMP);

UPDATE psychometric_responses
SET created_at = COALESCE(created_at, CURRENT_TIMESTAMP);

UPDATE proctoring_violations
SET severity = LOWER(BTRIM(COALESCE(severity, 'medium'))),
    timestamp = COALESCE(timestamp, CURRENT_TIMESTAMP);

UPDATE email_logs
SET status = LOWER(BTRIM(COALESCE(status, 'sent'))),
    sent_at = COALESCE(sent_at, CURRENT_TIMESTAMP);

UPDATE candidate_job_matches
SET match_score = COALESCE(match_score, 0),
    skill_match_score = COALESCE(skill_match_score, 0),
    experience_match_score = COALESCE(experience_match_score, 0),
    status = LOWER(BTRIM(COALESCE(status, 'auto_matched'))),
    matched_at = COALESCE(matched_at, CURRENT_TIMESTAMP);

UPDATE audit_log
SET created_at = COALESCE(created_at, CURRENT_TIMESTAMP);

UPDATE custom_question_bank
SET is_active = COALESCE(is_active, true),
    created_at = COALESCE(created_at, CURRENT_TIMESTAMP),
    updated_at = COALESCE(updated_at, CURRENT_TIMESTAMP);

UPDATE sectors
SET created_at = COALESCE(created_at, CURRENT_TIMESTAMP),
    updated_at = COALESCE(updated_at, CURRENT_TIMESTAMP);

ALTER TABLE sectors
    ALTER COLUMN created_at SET NOT NULL,
    ALTER COLUMN updated_at SET NOT NULL;
ALTER TABLE users
    ALTER COLUMN created_at SET NOT NULL,
    ALTER COLUMN updated_at SET NOT NULL;
ALTER TABLE candidates
    ALTER COLUMN status SET DEFAULT 'pending',
    ALTER COLUMN status SET NOT NULL,
    ALTER COLUMN created_at SET NOT NULL,
    ALTER COLUMN updated_at SET NOT NULL;
ALTER TABLE job_descriptions
    ALTER COLUMN min_experience SET DEFAULT 0,
    ALTER COLUMN min_experience SET NOT NULL,
    ALTER COLUMN status SET DEFAULT 'active',
    ALTER COLUMN status SET NOT NULL,
    ALTER COLUMN employment_type SET DEFAULT 'full-time',
    ALTER COLUMN employment_type SET NOT NULL,
    ALTER COLUMN experience_level SET DEFAULT 'mid',
    ALTER COLUMN experience_level SET NOT NULL,
    ALTER COLUMN work_mode SET DEFAULT 'On-Site',
    ALTER COLUMN work_mode SET NOT NULL,
    ALTER COLUMN role_complexity_level SET DEFAULT 'intermediate',
    ALTER COLUMN role_complexity_level SET NOT NULL,
    ALTER COLUMN created_at SET NOT NULL,
    ALTER COLUMN updated_at SET NOT NULL;
ALTER TABLE scheduled_assessments
    ALTER COLUMN status SET DEFAULT 'scheduled',
    ALTER COLUMN status SET NOT NULL,
    ALTER COLUMN access_token_hash SET NOT NULL,
    ALTER COLUMN is_technical_role SET DEFAULT true,
    ALTER COLUMN is_technical_role SET NOT NULL,
    ALTER COLUMN created_at SET NOT NULL,
    ALTER COLUMN updated_at SET NOT NULL;
ALTER TABLE assessments
    ALTER COLUMN status SET DEFAULT 'in_progress',
    ALTER COLUMN status SET NOT NULL,
    ALTER COLUMN proctoring_violations SET DEFAULT 0,
    ALTER COLUMN proctoring_violations SET NOT NULL,
    ALTER COLUMN time_elapsed_seconds SET DEFAULT 0,
    ALTER COLUMN time_elapsed_seconds SET NOT NULL,
    ALTER COLUMN created_at SET NOT NULL;
ALTER TABLE mcq_responses
    ALTER COLUMN created_at SET NOT NULL;
ALTER TABLE coding_submissions
    ALTER COLUMN test_cases_passed SET DEFAULT 0,
    ALTER COLUMN test_cases_passed SET NOT NULL,
    ALTER COLUMN total_test_cases SET DEFAULT 0,
    ALTER COLUMN total_test_cases SET NOT NULL,
    ALTER COLUMN submitted_at SET NOT NULL;
ALTER TABLE psychometric_responses
    ALTER COLUMN created_at SET NOT NULL;
ALTER TABLE proctoring_violations
    ALTER COLUMN severity SET DEFAULT 'medium',
    ALTER COLUMN severity SET NOT NULL,
    ALTER COLUMN timestamp SET NOT NULL;
ALTER TABLE email_logs
    ALTER COLUMN status SET DEFAULT 'sent',
    ALTER COLUMN status SET NOT NULL,
    ALTER COLUMN sent_at SET NOT NULL;
ALTER TABLE candidate_job_matches
    ALTER COLUMN match_score SET DEFAULT 0,
    ALTER COLUMN match_score SET NOT NULL,
    ALTER COLUMN skill_match_score SET DEFAULT 0,
    ALTER COLUMN skill_match_score SET NOT NULL,
    ALTER COLUMN experience_match_score SET DEFAULT 0,
    ALTER COLUMN experience_match_score SET NOT NULL,
    ALTER COLUMN status SET DEFAULT 'auto_matched',
    ALTER COLUMN status SET NOT NULL,
    ALTER COLUMN matched_at SET NOT NULL;
ALTER TABLE audit_log
    ALTER COLUMN created_at SET NOT NULL;
ALTER TABLE custom_question_bank
    ALTER COLUMN is_active SET DEFAULT true,
    ALTER COLUMN is_active SET NOT NULL,
    ALTER COLUMN created_at SET NOT NULL,
    ALTER COLUMN updated_at SET NOT NULL;

DO $constraints$
DECLARE
    constraint_record RECORD;
BEGIN
    FOR constraint_record IN
        SELECT *
        FROM (VALUES
            ('users', 'users_role_check',
             $$role IN ('interviewer', 'admin', 'proctor', 'super_admin', 'sector_admin', 'recruiter')$$),
            ('users', 'users_sector_scope_check',
             $$role NOT IN ('sector_admin', 'recruiter') OR sector_id IS NOT NULL$$),
            ('candidates', 'candidates_years_experience_check',
             $$years_experience IS NULL OR years_experience >= 0$$),
            ('candidates', 'candidates_match_score_check',
             $$match_score IS NULL OR match_score BETWEEN 0 AND 100$$),
            ('candidates', 'candidates_shortlist_status_check',
             $$shortlist_status IS NULL OR shortlist_status IN ('High Match', 'Potential', 'Reject')$$),
            ('candidates', 'candidates_status_check',
             $$status IN ('applied', 'absence_of_details', 'pending', 'under_review', 'rejected', 'completed', 'hired')$$),
            ('job_descriptions', 'job_descriptions_experience_check',
             $$min_experience >= 0 AND (max_experience IS NULL OR max_experience >= min_experience)$$),
            ('job_descriptions', 'job_descriptions_status_check',
             $$status IN ('active', 'paused', 'closed', 'draft')$$),
            ('job_descriptions', 'job_descriptions_type_check',
             $$employment_type IN ('full-time', 'part-time', 'contract', 'internship')$$),
            ('job_descriptions', 'job_descriptions_experience_level_check',
             $$experience_level IN ('junior', 'mid', 'senior', 'lead', 'principal')$$),
            ('job_descriptions', 'job_descriptions_work_mode_check',
             $$work_mode IN ('Remote', 'On-Site', 'Hybrid')$$),
            ('scheduled_assessments', 'scheduled_assessments_status_check',
             $$status IN ('scheduled', 'in_progress', 'completed', 'cancelled')$$),
            ('scheduled_assessments', 'scheduled_assessments_access_token_hash_check',
             $$access_token_hash ~ '^[0-9a-f]{64}$'$$),
            ('assessments', 'assessments_scores_check',
             $$(technical_score IS NULL OR technical_score BETWEEN 0 AND 100) AND (psychometric_score IS NULL OR psychometric_score BETWEEN 0 AND 100) AND (overall_score IS NULL OR overall_score BETWEEN 0 AND 100)$$),
            ('assessments', 'assessments_proctoring_violations_check',
             $$proctoring_violations >= 0$$),
            ('assessments', 'assessments_status_check',
             $$status IN ('started', 'in_progress', 'completed')$$),
            ('assessments', 'assessments_final_decision_check',
             $$final_decision IS NULL OR final_decision IN ('Hire', 'No-Hire')$$),
            ('assessments', 'assessments_time_elapsed_check',
             $$time_elapsed_seconds BETWEEN 0 AND 3600$$),
            ('mcq_responses', 'mcq_responses_question_check', $$question_id > 0$$),
            ('mcq_responses', 'mcq_responses_time_check',
             $$time_spent IS NULL OR time_spent >= 0$$),
            ('coding_submissions', 'coding_submissions_counts_check',
             $$problem_id > 0 AND test_cases_passed >= 0 AND total_test_cases >= 0 AND test_cases_passed <= total_test_cases$$),
            ('psychometric_responses', 'psychometric_responses_question_check',
             $$question_id > 0$$),
            ('psychometric_responses', 'psychometric_responses_score_check',
             $$score IS NULL OR score BETWEEN 1 AND 10$$),
            ('proctoring_violations', 'proctoring_violations_severity_check',
             $$severity IN ('low', 'medium', 'high', 'critical')$$),
            ('email_logs', 'email_logs_status_check',
             $$status IN ('sent', 'failed', 'bounced')$$),
            ('candidate_job_matches', 'candidate_job_matches_scores_check',
             $$match_score BETWEEN 0 AND 100 AND skill_match_score BETWEEN 0 AND 100 AND experience_match_score BETWEEN 0 AND 100$$),
            ('candidate_job_matches', 'candidate_job_matches_status_check',
             $$status IN ('auto_matched', 'confirmed', 'rejected')$$)
        ) AS constraints(table_name, constraint_name, expression)
    LOOP
        EXECUTE format(
            'ALTER TABLE %I DROP CONSTRAINT IF EXISTS %I',
            constraint_record.table_name,
            constraint_record.constraint_name
        );
        EXECUTE format(
            'ALTER TABLE %I ADD CONSTRAINT %I CHECK (%s)',
            constraint_record.table_name,
            constraint_record.constraint_name,
            constraint_record.expression
        );
    END LOOP;
END
$constraints$;

-- --------------------------------------------------------------------------
-- Supabase Data API hardening (the application is backend-only)
-- --------------------------------------------------------------------------

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

COMMIT;
