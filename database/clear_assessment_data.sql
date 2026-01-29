-- ============================================================================
-- Clear All Assessment Data (PostgreSQL)
-- Keeps: users table intact
-- Removes: All candidates, assessments, submissions, and related data
-- ============================================================================

-- CAUTION: This will permanently delete all assessment data!
-- Make sure you have a backup if needed.

BEGIN;

-- Disable foreign key checks temporarily (PostgreSQL)
-- Note: PostgreSQL handles cascading deletes automatically with ON DELETE CASCADE

-- Delete in correct order to respect foreign key constraints
-- Even with CASCADE, explicit deletion is cleaner

-- 1. Delete proctoring events
DELETE FROM proctoring_events;
COMMIT;

-- 2. Delete psychometric responses
DELETE FROM psychometric_responses;

-- 3. Delete coding submissions
DELETE FROM coding_submissions;

-- 4. Delete MCQ responses
DELETE FROM mcq_responses;

-- 5. Delete assessments (this will cascade to related records if ON DELETE CASCADE is set)
DELETE FROM assessments;

-- 6. Delete scheduled assessments
DELETE FROM scheduled_assessments;

-- 7. Delete candidates
DELETE FROM candidates;

-- 8. Optional: Clear email logs related to assessments
-- Uncomment if you want to clear email history too
-- DELETE FROM email_logs WHERE email_type IN ('assessment_scheduled', 'assessment_reminder', 'assessment_result');

-- Reset auto-increment sequences to start from 1
ALTER SEQUENCE IF EXISTS candidates_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS assessments_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS scheduled_assessments_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS mcq_responses_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS coding_submissions_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS psychometric_responses_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS proctoring_events_id_seq RESTART WITH 1;

-- Verify results
SELECT 'Candidates' as table_name, COUNT(*) as count FROM candidates
UNION ALL
SELECT 'Assessments', COUNT(*) FROM assessments
UNION ALL
SELECT 'Scheduled Assessments', COUNT(*) FROM scheduled_assessments
UNION ALL
SELECT 'MCQ Responses', COUNT(*) FROM mcq_responses
UNION ALL
SELECT 'Coding Submissions', COUNT(*) FROM coding_submissions
UNION ALL
SELECT 'Psychometric Responses', COUNT(*) FROM psychometric_responses
UNION ALL
SELECT 'Proctoring Events', COUNT(*) FROM proctoring_events
UNION ALL
SELECT 'Users (should remain)', COUNT(*) FROM users;

COMMIT;
