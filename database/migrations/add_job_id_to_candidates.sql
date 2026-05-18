-- Add job_id field to candidates table for auto-matching
ALTER TABLE candidates ADD COLUMN IF NOT EXISTS job_id INTEGER;
ALTER TABLE candidates ADD CONSTRAINT fk_candidates_job FOREIGN KEY (job_id) REFERENCES job_descriptions(id) ON DELETE SET NULL;
CREATE INDEX IF NOT EXISTS idx_candidates_job ON candidates(job_id);
