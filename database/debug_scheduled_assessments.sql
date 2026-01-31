-- ============================================================================
-- Debug Scheduled Assessments
-- Use this to check what's in your scheduled_assessments table
-- ============================================================================

-- Check all scheduled assessments
SELECT 
    sa.id,
    sa.candidate_id,
    c.name as candidate_name,
    c.email as candidate_email,
    sa.scheduled_time,
    sa.status,
    sa.proctoring_enabled,
    sa.access_token,
    sa.created_at
FROM scheduled_assessments sa
LEFT JOIN candidates c ON sa.candidate_id = c.id
ORDER BY sa.created_at DESC;

-- Count by status
SELECT status, COUNT(*) as count
FROM scheduled_assessments
GROUP BY status;

-- Check for any without proctoring_enabled
SELECT COUNT(*) as count_without_proctoring
FROM scheduled_assessments
WHERE proctoring_enabled IS NULL OR proctoring_enabled = false;

-- Check table structure (PostgreSQL)
SELECT column_name, data_type, column_default, is_nullable
FROM information_schema.columns
WHERE table_name = 'scheduled_assessments'
ORDER BY ordinal_position;
