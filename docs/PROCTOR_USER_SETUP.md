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

## Creating a Proctor via SQL (Direct DB Access)

If you need to bootstrap a proctor before the admin UI is available, use Python to generate a bcrypt hash and insert directly:

```python
import bcrypt, psycopg2, os

email = "proctor@yourcompany.com"
password = "choose-a-strong-password"   # change this
name = "Proctor Name"

hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

conn = psycopg2.connect(os.environ["DATABASE_URL"])
cur = conn.cursor()
cur.execute(
    "INSERT INTO users (email, password_hash, role, name) VALUES (%s, %s, 'proctor', %s)",
    (email, hash, name)
)
conn.commit()
conn.close()
print(f"Created proctor: {email}")
```

Never commit real credentials to the repository.

---

## Proctor Dashboard Features

### Scheduled Tab
- View all upcoming assessments
- Candidate name, email, scheduled time
- Time until assessment starts

### Active Tab
- Monitor ongoing assessments in real-time
- Current violation count per candidate
- Auto-refreshes every 10 seconds

### Completed Tab
- Review finished assessments
- Check violation counts and scores

### Violation Details (Per Assessment)
Click **View Details** on any assessment to see:
- All violations with timestamps
- Violation type and severity
- Detailed descriptions

---

## Role Permissions

| Action | Admin | Interviewer | Proctor |
|--------|-------|-------------|---------|
| View proctor dashboard | Yes | No | Yes |
| Monitor live assessments | Yes | No | Yes |
| Review violation records | Yes | Yes | Yes |
| Schedule assessments | Yes | Yes | No |
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
| No assessments showing | Verify assessments exist and have `proctoring_enabled = true` |
| Auto-refresh not working | Check for JavaScript errors in browser console |
