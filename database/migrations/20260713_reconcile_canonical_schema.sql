-- Reconcile legacy HireSense schemas with database/schema_postgres.sql.
--
-- Safety guarantees:
--   * no table or column is dropped;
--   * legacy values are copied into canonical columns before constraints are added;
--   * foreign keys are added NOT VALID so dirty historical rows do not block the
--     deployment, while all new and changed rows are still protected;
--   * uniqueness is enabled only when existing data has no duplicates. A warning
--     identifies any key that needs an explicit, business-approved data cleanup.
--
-- Canonical names:
--   job_descriptions.created_by   (legacy: created_by_id)
--   candidates.best_match_job_id  (legacy: job_id)
--   audit_log                     (legacy: admin_audit_log)

BEGIN;

-- --------------------------------------------------------------------------
-- Runtime-required columns
-- --------------------------------------------------------------------------

ALTER TABLE job_descriptions
    ADD COLUMN IF NOT EXISTS created_by INTEGER,
    ADD COLUMN IF NOT EXISTS role_complexity_level TEXT DEFAULT 'intermediate';

ALTER TABLE candidates
    ADD COLUMN IF NOT EXISTS best_match_job_id INTEGER;

ALTER TABLE scheduled_assessments
    ADD COLUMN IF NOT EXISTS job_id INTEGER,
    ADD COLUMN IF NOT EXISTS proctor_id INTEGER;

ALTER TABLE proctoring_events
    ADD COLUMN IF NOT EXISTS is_reviewed BOOLEAN DEFAULT false;

UPDATE job_descriptions
SET role_complexity_level = 'intermediate'
WHERE role_complexity_level IS NULL;

UPDATE proctoring_events
SET is_reviewed = false
WHERE is_reviewed IS NULL;

ALTER TABLE job_descriptions
    ALTER COLUMN role_complexity_level SET DEFAULT 'intermediate';

ALTER TABLE proctoring_events
    ALTER COLUMN is_reviewed SET DEFAULT false,
    ALTER COLUMN is_reviewed SET NOT NULL;

-- --------------------------------------------------------------------------
-- Backfill legacy aliases without deleting them
-- --------------------------------------------------------------------------

DO $$
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
END
$$;

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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
        RAISE WARNING 'admin_audit_log has neither action nor action_type; legacy rows were not copied';
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

    COMMENT ON TABLE admin_audit_log IS
        'Deprecated legacy audit table. New writes belong in audit_log.';
END
$$;

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
END
$$;

-- --------------------------------------------------------------------------
-- Indexes used by runtime joins and filters
-- --------------------------------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_job_descriptions_created_by
    ON job_descriptions(created_by);
CREATE INDEX IF NOT EXISTS idx_candidates_best_job
    ON candidates(best_match_job_id);
CREATE INDEX IF NOT EXISTS idx_scheduled_assessments_job
    ON scheduled_assessments(job_id);
CREATE INDEX IF NOT EXISTS idx_scheduled_assessments_proctor
    ON scheduled_assessments(proctor_id);
CREATE INDEX IF NOT EXISTS idx_assessments_job
    ON assessments(job_id);
CREATE INDEX IF NOT EXISTS idx_proctoring_events_reviewed
    ON proctoring_events(is_reviewed);
CREATE INDEX IF NOT EXISTS idx_audit_log_user
    ON audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_action
    ON audit_log(action);
CREATE INDEX IF NOT EXISTS idx_audit_log_entity
    ON audit_log(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_created
    ON audit_log(created_at DESC);

-- --------------------------------------------------------------------------
-- One logical response per assessment/question (or coding problem).
-- Existing duplicates are never deleted automatically.
-- --------------------------------------------------------------------------

DO $$
BEGIN
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

COMMIT;
