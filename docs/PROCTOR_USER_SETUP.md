# Proctor User Setup Guide

Proctor accounts are created through the Admin Dashboard — no scripts needed.

---

## Creating a Proctor via Admin Dashboard

1. Log in as an Admin
2. Go to the **Users** tab in the Admin Dashboard
3. Click **Create User**
4. Fill in the proctor's email, name, and a strong temporary password
5. Set **Role** to `proctor`
6. Send the credentials to the proctor securely — they should change their password immediately

---

## Creating the First Proctor Without the Admin UI

If no admin exists yet, run the seeder from the repository root. It creates
`admin@hiresense.com`, `interviewer@hiresense.com`, and `proctor@hiresense.com`:

```bash
SEED_PROCTOR_PASSWORD='choose-a-strong-password' python database/seed_users.py
```

To insert a single proctor directly, hash the password with Werkzeug, which is
what the backend uses to verify logins:

```python
import os
import psycopg2
from werkzeug.security import generate_password_hash

email = "proctor@yourcompany.com"
password = "choose-a-strong-password"   # change this
name = "Proctor Name"

conn = psycopg2.connect(os.environ["DATABASE_URL"])
with conn, conn.cursor() as cur:
    cur.execute(
        "INSERT INTO users (email, password_hash, role, name) VALUES (%s, %s, 'proctor', %s)",
        (email, generate_password_hash(password), name),
    )
conn.close()
print(f"Created proctor: {email}")
```

Never commit real credentials to the repository.

---

## Proctor Dashboard Features

### Summary
- Scheduled assessments today, active sessions, assessments completed today,
  and violation events today
- The dashboard refreshes every 30 seconds while the browser tab is visible

### Scheduled Tab
- Upcoming assessments with candidate and scheduled time
- Claim an unassigned assessment to proctor it

### Active Tab
- Ongoing assessments with their current violation count
- Open the live WebRTC video for a session

### Completed Tab
- Your finished assessments with violation counts and scores

### Violation Details (Per Assessment)
Click **View Details** on any assessment to see:
- All violations with timestamps
- Violation type and severity
- Detailed descriptions
- Screenshot evidence, where the browser captured it (opened in a new tab)

Violation types reported by the candidate's browser: tab hidden, window focus
lost, copy/cut/paste, no face detected, multiple faces, and camera interrupted.

---

## Role Permissions

| Action | Admin | Interviewer / Recruiter / Sector Admin | Proctor |
|--------|-------|-------------|---------|
| Open the Proctor Dashboard | No | No | Yes |
| Watch live assessment video | No | Yes (from the hiring dashboard) | Yes |
| Review violation records | No | No | Yes |
| Schedule assessments | No | Yes | No |
| Manage users | Yes | No | No |

---

## Managing Proctors via SQL

### List all proctor accounts
```sql
SELECT id, email, name, created_at
FROM users
WHERE role = 'proctor'
ORDER BY created_at DESC;
```

### Change a proctor's role
```sql
-- Promote to admin
UPDATE users SET role = 'admin' WHERE email = 'proctor@yourcompany.com';

-- Demote to interviewer
UPDATE users SET role = 'interviewer' WHERE email = 'proctor@yourcompany.com';
```

A role change signs the user out: existing tokens stop working because their
role no longer matches the account. `sector_admin` and `recruiter` also need a
`sector_id`.

### Remove a proctor
```sql
DELETE FROM users WHERE email = 'proctor@yourcompany.com' AND role = 'proctor';
```

---

## Security Practices

1. Use strong, unique passwords for every proctor account
2. Proctor accounts should only exist for users who actively monitor assessments — remove them when no longer needed
3. Never share credentials in plain text over email or chat; use a password manager
4. Regularly audit the proctor user list via the Admin Dashboard

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Access Denied" on /proctor | Verify the user has `role = 'proctor'` in the database |
| Dashboard not loading | Check browser console and verify backend is running |
| No assessments showing | The Scheduled tab lists future assessments within the next few days that are unassigned or assigned to this proctor; check the schedule time and assignment |
| Auto-refresh not working | Refresh pauses while the tab is hidden; check the browser console for errors |
| Live video never connects | Check camera permission on the candidate side; restrictive NATs need a TURN server, which is not configured |
