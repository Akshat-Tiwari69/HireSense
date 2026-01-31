-- Migration: Add missing columns to scheduled_assessments table
-- Run this if you have an existing database

-- Add assessment_token column for secure assessment URLs
ALTER TABLE scheduled_assessments ADD COLUMN assessment_token TEXT UNIQUE;

-- Add job_id column to link assessments to specific jobs
ALTER TABLE scheduled_assessments ADD COLUMN job_id INTEGER REFERENCES job_descriptions(id);

-- Add proctoring_enabled flag
ALTER TABLE scheduled_assessments ADD COLUMN proctoring_enabled INTEGER DEFAULT 1;

-- Add notes field for additional instructions
ALTER TABLE scheduled_assessments ADD COLUMN notes TEXT;

-- Create index for fast token lookups
CREATE INDEX IF NOT EXISTS idx_scheduled_assessments_token ON scheduled_assessments(assessment_token);
