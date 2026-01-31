-- ============================================================================
-- Create Proctor User (PostgreSQL)
-- Creates a proctor account for monitoring assessments
-- ============================================================================

-- Default proctor credentials:
-- Email: proctor@hiresense.com
-- Password: Proctor@123
-- (Change password after first login!)

-- Password hash for 'Proctor@123' using bcrypt (cost factor 12)
-- Generated with: bcrypt.hashpw('Proctor@123'.encode('utf-8'), bcrypt.gensalt(12))

INSERT INTO users (email, password_hash, role, name, created_at, updated_at)
VALUES (
    'proctor@hiresense.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5LE2wrUgn.SSy',  -- Proctor@123
    'proctor',
    'Proctoring Admin',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
)
ON CONFLICT (email) DO UPDATE 
SET 
    role = 'proctor',
    name = 'Proctoring Admin',
    updated_at = CURRENT_TIMESTAMP;

-- Verify the user was created
SELECT id, email, role, name, created_at 
FROM users 
WHERE email = 'proctor@hiresense.com';

-- ============================================================================
-- Additional Proctor Users (Optional)
-- ============================================================================

-- Add more proctors if needed:
/*
INSERT INTO users (email, password_hash, role, name)
VALUES 
    ('proctor2@hiresense.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5LE2wrUgn.SSy', 'proctor', 'Senior Proctor'),
    ('proctor3@hiresense.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5LE2wrUgn.SSy', 'proctor', 'Junior Proctor')
ON CONFLICT (email) DO NOTHING;
*/

-- ============================================================================
-- Quick Reference
-- ============================================================================

-- Login URL: https://your-app.com/login
-- Email: proctor@hiresense.com
-- Password: Proctor@123
-- After login, go to: https://your-app.com/proctor

-- To change password (run as proctor user after login via UI or API):
-- POST /api/user/change-password
-- { "old_password": "Proctor@123", "new_password": "YourNewPassword123!" }

-- To list all proctors:
-- SELECT id, email, name, created_at FROM users WHERE role = 'proctor';

-- To delete a proctor:
-- DELETE FROM users WHERE email = 'proctor@hiresense.com';
