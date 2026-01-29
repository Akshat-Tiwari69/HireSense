
-- Insert proctor user
INSERT INTO users (email, password_hash, role, name, created_at, updated_at)
VALUES (
    'proctor@hiresense.com',
    '$2b$12$ghvQDeZZlgmskt6oXccKYuSLoUXHX/Ci4lfK/KwhGNlWNF3ZXlBrm',
    'proctor',
    'Proctoring Admin',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
)
ON CONFLICT (email) DO UPDATE 
SET 
    role = 'proctor',
    password_hash = EXCLUDED.password_hash,
    name = EXCLUDED.name,
    updated_at = CURRENT_TIMESTAMP;

-- Verify
SELECT id, email, role, name FROM users WHERE email = 'proctor@hiresense.com';
