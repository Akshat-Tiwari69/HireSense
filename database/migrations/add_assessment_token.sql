-- Migration: Add access_token to scheduled_assessments for secure assessment access
-- This token is sent to candidates via email and used to authenticate their assessment session

-- Add access_token column to scheduled_assessments
ALTER TABLE scheduled_assessments 
ADD COLUMN IF NOT EXISTS access_token VARCHAR(64) UNIQUE;

-- Add proctoring_enabled flag
ALTER TABLE scheduled_assessments 
ADD COLUMN IF NOT EXISTS proctoring_enabled BOOLEAN DEFAULT true;

-- Add started_at timestamp for tracking when assessment actually started
ALTER TABLE scheduled_assessments 
ADD COLUMN IF NOT EXISTS started_at TIMESTAMP;

-- Add completed_at timestamp
ALTER TABLE scheduled_assessments 
ADD COLUMN IF NOT EXISTS completed_at TIMESTAMP;

-- Create index on access_token for fast lookups
CREATE INDEX IF NOT EXISTS idx_scheduled_assessments_token ON scheduled_assessments(access_token);

-- Update proctoring_violations table to have more details
ALTER TABLE proctoring_violations
ADD COLUMN IF NOT EXISTS resolved BOOLEAN DEFAULT false;

ALTER TABLE proctoring_violations
ADD COLUMN IF NOT EXISTS resolved_by INTEGER REFERENCES users(id);

ALTER TABLE proctoring_violations
ADD COLUMN IF NOT EXISTS resolved_at TIMESTAMP;
