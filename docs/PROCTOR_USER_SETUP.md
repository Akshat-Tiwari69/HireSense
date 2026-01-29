# Proctor User Setup Guide

## Quick Setup

### Option 1: Using Python Script (Recommended)

```bash
# Navigate to project root
cd f:\Code\cygnusa-elite-hire

# Run the script
python scripts/create_proctor_user.py

# Or with custom credentials
python scripts/create_proctor_user.py proctor@mycompany.com MySecurePass123 "Lead Proctor"
```

The script will:
- Generate a bcrypt password hash
- Create SQL INSERT statement
- Save SQL to a file
- Show login credentials

### Option 2: Using SQL Directly

```bash
# Connect to your Render PostgreSQL database
psql -h your-render-host -U your-user -d your-database

# Run the SQL file
\i database/create_proctor_user.sql
```

## Default Credentials

**⚠️ Change these after first login!**

- **Email:** `proctor@hiresense.com`
- **Password:** `Proctor@123`
- **Dashboard URL:** `https://your-app.com/proctor`

## Accessing Proctor Dashboard

1. **Login:** Navigate to `/login`
2. **Enter credentials:**
   - Email: `proctor@hiresense.com`
   - Password: `Proctor@123`
3. **Access Dashboard:** You'll be redirected to `/proctor`

## Proctor Dashboard Features

### Overview Tab
- **Stats Cards:**
  - Scheduled assessments count
  - Active assessments count  
  - Completed today count
  - Violations detected today

### Scheduled Tab
- View all upcoming assessments
- See candidate name, email, scheduled time
- Time until assessment starts
- Proctoring status (enabled/disabled)

### Active Tab
- Monitor ongoing assessments in real-time
- See current violations count
- View assessment progress
- Auto-refreshes every 10 seconds

### Completed Tab
- Review finished assessments
- Check violation counts
- View scores and results
- Filter by date

### Violations View (Per Assessment)
Click "View Details" on any assessment to see:
- All violations with timestamps
- Violation type and severity
- Detailed descriptions
- Timeline of events

## Permission Levels

| Role | Dashboard | Schedule | Monitor | Review |
|------|-----------|----------|---------|--------|
| Admin | ✅ Full | ✅ | ✅ | ✅ |
| Interviewer | ✅ Limited | ✅ | ❌ | ✅ |
| Proctor | ✅ Full | ❌ | ✅ | ✅ |

## Creating Multiple Proctors

### Method 1: Python Script
```bash
python scripts/create_proctor_user.py proctor1@company.com Pass123 "Proctor 1"
python scripts/create_proctor_user.py proctor2@company.com Pass456 "Proctor 2"
```

### Method 2: SQL
```sql
INSERT INTO users (email, password_hash, role, name)
VALUES 
    ('proctor1@company.com', '$2b$12$...', 'proctor', 'Night Shift Proctor'),
    ('proctor2@company.com', '$2b$12$...', 'proctor', 'Day Shift Proctor');
```

## Managing Proctors

### List All Proctors
```sql
SELECT id, email, name, created_at 
FROM users 
WHERE role = 'proctor'
ORDER BY created_at DESC;
```

### Update Proctor Details
```sql
UPDATE users 
SET name = 'Senior Proctor', updated_at = CURRENT_TIMESTAMP
WHERE email = 'proctor@hiresense.com';
```

### Delete Proctor
```sql
DELETE FROM users 
WHERE email = 'proctor@hiresense.com' AND role = 'proctor';
```

### Change Role
```sql
-- Promote to admin
UPDATE users SET role = 'admin' WHERE email = 'proctor@hiresense.com';

-- Demote to interviewer
UPDATE users SET role = 'interviewer' WHERE email = 'proctor@hiresense.com';
```

## Troubleshooting

### "Access Denied" Error
- Verify the user has `role = 'proctor'` in database
- Check if user is logged in with correct email
- Clear browser cache and re-login

### Dashboard Not Loading
- Check browser console for errors
- Verify backend API is running
- Check `/api/proctor/stats` endpoint responds

### No Assessments Showing
- Verify assessments exist with `proctoring_enabled = true`
- Check assessment status (scheduled/in_progress/completed)
- Verify time filters if applied

### Auto-Refresh Not Working
- Check if toggle is enabled (top right of dashboard)
- Look for JavaScript errors in console
- Verify API endpoints are accessible

## Security Best Practices

1. **Change Default Password:** Immediately after first login
2. **Use Strong Passwords:** Min 12 characters, mixed case, numbers, symbols
3. **Rotate Credentials:** Change passwords every 90 days
4. **Limit Access:** Only create proctors who need monitoring access
5. **Audit Logs:** Regularly review who accessed what and when
6. **2FA (Future):** Consider implementing two-factor authentication

## API Endpoints Used

```
GET  /api/proctor/stats                    - Dashboard statistics
GET  /api/proctor/assessments/scheduled    - Upcoming assessments
GET  /api/proctor/assessments/active       - Ongoing assessments
GET  /api/proctor/assessments/completed    - Finished assessments
GET  /api/proctor/assessment/{id}/violations - Violation details
POST /api/proctor/assessment/{id}/flag     - Flag assessment for review
```

## Password Change via API

```bash
curl -X POST https://your-app.com/api/user/change-password \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "old_password": "Proctor@123",
    "new_password": "MyNewSecurePassword123!"
  }'
```

## Environment Variables

No additional environment variables needed for proctor users.
Proctoring is controlled at assessment level via `proctoring_enabled` flag.

## Support

For issues or questions:
- Check backend logs for errors
- Verify database connection
- Review proctor_routes.py for API logic
- Test with Postman/curl to isolate frontend vs backend issues
