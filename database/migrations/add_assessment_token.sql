-- Check which candidates will be updated
SELECT c.id, c.name, c.email, c.status as current_status, a.status as assessment_status
FROM candidates c
JOIN assessments a ON c.id = a.candidate_id
WHERE a.status = 'completed' AND c.status != 'completed';

-- Then run the update
UPDATE candidates 
SET status = 'completed'
WHERE id IN (
    SELECT candidate_id 
    FROM assessments 
    WHERE status = 'completed'
);