-- Add is_technical_role column to scheduled_assessments table
-- This column determines whether coding problems should be generated for the assessment
-- TRUE (default): Technical role - includes coding problems
-- FALSE: Non-technical role - skips coding problems

ALTER TABLE scheduled_assessments 
ADD COLUMN IF NOT EXISTS is_technical_role BOOLEAN DEFAULT TRUE;

-- Update existing rows to default to technical role
UPDATE scheduled_assessments 
SET is_technical_role = TRUE 
WHERE is_technical_role IS NULL;
