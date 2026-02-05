-- Reset assessment system to "Applied" state
-- This keeps candidates but removes all assessment records and schedules

BEGIN;

-- 1. Remove all proctoring and response data
DELETE FROM proctoring_violations;
DELETE FROM proctoring_events;
DELETE FROM psychometric_responses;
DELETE FROM coding_submissions;
DELETE FROM mcq_responses;

-- 2. Remove assessments 
-- (Foreign keys in scheduled_assessments are cleared first)
UPDATE scheduled_assessments SET assessment_id = NULL;
DELETE FROM assessments;

-- 3. Remove all scheduled assessments
DELETE FROM scheduled_assessments;

-- 4. Reset candidate statuses to 'pending' (Applied state)
UPDATE candidates 
SET status = 'pending',
    shortlist_status = NULL;

-- 5. Reset primary key sequences for assessment tables
ALTER SEQUENCE IF EXISTS scheduled_assessments_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS assessments_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS mcq_responses_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS coding_submissions_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS psychometric_responses_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS proctoring_events_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS proctoring_violations_id_seq RESTART WITH 1;

COMMIT;
