# Environment Configuration Reference

Complete reference for all environment variables used in CYGNUSA Elite-Hire.

---

## Quick Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `FLASK_ENV` | No | `development` | Flask environment |
| `JWT_SECRET_KEY` | Yes* | `dev-secret-key...` | JWT signing key |
| `DATABASE_URL` | No | SQLite | PostgreSQL connection |
| `OPENAI_API_KEY` | Yes | None | OpenAI API key |
| `RESEND_API_KEY` | No | None | Resend email API |
| `SMTP_HOST` | No | None | SMTP server host |
| `SMTP_PORT` | No | `587` | SMTP server port |
| `SMTP_USER` | No | None | SMTP username |
| `SMTP_PASS` | No | None | SMTP password |
| `CORS_ORIGINS` | No | `http://localhost:5173` | Allowed CORS origins |
| `VITE_API_BASE_URL` | No | Auto-detect | Backend API URL |

*Required in production

---

## Backend Environment Variables

### Flask Configuration

```bash
# Flask environment (development/production)
FLASK_ENV=development

# Enable debug mode (development only!)
FLASK_DEBUG=1

# Server binding
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
```

### Authentication

```bash
# JWT secret key for token signing
# CRITICAL: Change this in production!
JWT_SECRET_KEY=your-super-secret-key-minimum-32-characters

# Token expiration (hours)
JWT_ACCESS_TOKEN_EXPIRES=24
```

**Generating a secure key:**
```bash
# Python
python -c "import secrets; print(secrets.token_hex(32))"

# OpenSSL
openssl rand -hex 32

# Node.js
node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"
```

### Database

```bash
# PostgreSQL connection string (production)
DATABASE_URL=postgresql://user:password@host:5432/database_name

# SQLite path (development - automatic fallback)
# No configuration needed, uses elite_hire.db
```

**PostgreSQL URL Format:**
```
postgresql://username:password@hostname:port/database?sslmode=require
```

### OpenAI API

```bash
# OpenAI API key for resume analysis
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Optional: Override default model
OPENAI_MODEL=gpt-4o-mini
```

**Getting API Key:**
1. Go to https://platform.openai.com/api-keys
2. Create new secret key
3. Copy and store securely

### Email Service

#### Option 1: Resend API (Recommended)

```bash
# Resend API key
RESEND_API_KEY=re_xxxxxxxxxxxxxxxxxxxxxxxx

# Sender email (must be verified in Resend)
RESEND_FROM_EMAIL=notifications@yourdomain.com
```

#### Option 2: SMTP

```bash
# SMTP server configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-app-password
SMTP_SENDER_NAME=CYGNUSA Elite-Hire
SMTP_USE_TLS=true
```

**Gmail App Password:**
1. Enable 2-Factor Authentication
2. Go to Google Account > Security > App passwords
3. Generate password for "Mail"

### CORS Configuration

```bash
# Allowed CORS origins (comma-separated for multiple)
CORS_ORIGINS=http://localhost:5173

# Production example
CORS_ORIGINS=https://elite-hire.yourdomain.com,https://www.elite-hire.yourdomain.com
```

### File Upload

```bash
# Maximum upload size in bytes (default: 10MB)
MAX_CONTENT_LENGTH=10485760

# Upload directory
UPLOAD_FOLDER=uploads
```

---

## Frontend Environment Variables

### Vite Configuration

All frontend environment variables must be prefixed with `VITE_`:

```bash
# Backend API base URL
VITE_API_BASE_URL=http://localhost:5000

# Production
VITE_API_BASE_URL=https://api.yourdomain.com
```

### Creating .env Files

**Frontend (.env in frontend/):**
```bash
# Development
VITE_API_BASE_URL=http://localhost:5000

# You can also create environment-specific files:
# .env.development
# .env.production
```

**Usage in code:**
```javascript
const apiUrl = import.meta.env.VITE_API_BASE_URL;
```

---

## Environment Files

### Backend .env Example

Create `backend/.env`:

```bash
# ===================
# Flask Configuration
# ===================
FLASK_ENV=development
FLASK_DEBUG=1

# ===================
# Authentication
# ===================
JWT_SECRET_KEY=dev-secret-key-change-in-production-please

# ===================
# Database
# ===================
# Leave empty to use SQLite (development)
# DATABASE_URL=postgresql://user:pass@localhost:5432/elite_hire

# ===================
# OpenAI
# ===================
OPENAI_API_KEY=sk-your-openai-api-key-here

# ===================
# Email (Option 1: Resend)
# ===================
RESEND_API_KEY=re_your-resend-api-key

# ===================
# Email (Option 2: SMTP)
# ===================
# SMTP_HOST=smtp.gmail.com
# SMTP_PORT=587
# SMTP_USER=your-email@gmail.com
# SMTP_PASS=your-app-password
# SMTP_SENDER_NAME=CYGNUSA Elite-Hire

# ===================
# CORS
# ===================
CORS_ORIGINS=http://localhost:5173
```

### Frontend .env Example

Create `frontend/.env`:

```bash
# API Base URL
VITE_API_BASE_URL=http://localhost:5000
```

---

## Loading Environment Variables

### Python (Backend)

```python
# Using python-dotenv
from dotenv import load_dotenv
import os

load_dotenv()  # Load from .env file

jwt_secret = os.environ.get('JWT_SECRET_KEY', 'default-dev-key')
database_url = os.environ.get('DATABASE_URL')
```

### Windows PowerShell

```powershell
# Set single variable
$env:OPENAI_API_KEY="sk-your-key"

# Set multiple variables
$env:FLASK_ENV="development"
$env:JWT_SECRET_KEY="your-secret"

# View all environment variables
Get-ChildItem Env:

# View specific variable
$env:OPENAI_API_KEY
```

### Linux/Mac

```bash
# Set single variable
export OPENAI_API_KEY=sk-your-key

# Set multiple variables
export FLASK_ENV=development
export JWT_SECRET_KEY=your-secret

# Load from file
source .env
# or
export $(cat .env | xargs)
```

---

## Production Checklist

### Security Requirements

| Variable | Requirement |
|----------|-------------|
| `JWT_SECRET_KEY` | Minimum 32 characters, random |
| `DATABASE_URL` | Use SSL (`?sslmode=require`) |
| `FLASK_ENV` | Must be `production` |
| `FLASK_DEBUG` | Must be `0` or unset |

### Required Variables

```bash
# Minimum required for production
FLASK_ENV=production
JWT_SECRET_KEY=<64-char-random-string>
DATABASE_URL=postgresql://...
OPENAI_API_KEY=sk-...
CORS_ORIGINS=https://your-frontend-domain.com
```

### Email (At least one option)

```bash
# Option 1: Resend
RESEND_API_KEY=re_...

# Option 2: SMTP
SMTP_HOST=...
SMTP_USER=...
SMTP_PASS=...
```

---

## Validation Script

Create `backend/validate_env.py`:

```python
import os
import sys

def validate_environment():
    errors = []
    warnings = []
    
    # Required in production
    if os.environ.get('FLASK_ENV') == 'production':
        if not os.environ.get('JWT_SECRET_KEY') or len(os.environ.get('JWT_SECRET_KEY', '')) < 32:
            errors.append('JWT_SECRET_KEY must be at least 32 characters in production')
        
        if not os.environ.get('DATABASE_URL'):
            errors.append('DATABASE_URL required in production')
    
    # Always required
    if not os.environ.get('OPENAI_API_KEY'):
        warnings.append('OPENAI_API_KEY not set - AI analysis will fail')
    
    # Email configuration
    has_resend = bool(os.environ.get('RESEND_API_KEY'))
    has_smtp = all([
        os.environ.get('SMTP_HOST'),
        os.environ.get('SMTP_USER'),
        os.environ.get('SMTP_PASS')
    ])
    
    if not has_resend and not has_smtp:
        warnings.append('No email service configured - emails will not be sent')
    
    # Report
    if errors:
        print('ERRORS:')
        for e in errors:
            print(f'  ❌ {e}')
    
    if warnings:
        print('WARNINGS:')
        for w in warnings:
            print(f'  ⚠️ {w}')
    
    if not errors and not warnings:
        print('✅ Environment configuration valid')
    
    return len(errors) == 0

if __name__ == '__main__':
    if not validate_environment():
        sys.exit(1)
```

Run:
```bash
python validate_env.py
```

---

## Platform-Specific Configuration

### Railway

Set in Railway dashboard or CLI:
```bash
railway variables set JWT_SECRET_KEY=your-secret
railway variables set OPENAI_API_KEY=sk-...
```

### Render

Set in Render dashboard under "Environment":
- Key: `JWT_SECRET_KEY`
- Value: `your-secret-key`

### Vercel

Set in Vercel dashboard or CLI:
```bash
vercel env add VITE_API_BASE_URL
```

### Heroku

```bash
heroku config:set JWT_SECRET_KEY=your-secret
heroku config:set OPENAI_API_KEY=sk-...
```

---

## Troubleshooting

### Variable Not Found

```python
# Check if variable is set
import os
print(os.environ.get('VARIABLE_NAME', 'NOT SET'))
```

### .env Not Loading

1. Ensure `python-dotenv` installed: `pip install python-dotenv`
2. Check file name is exactly `.env` (not `.env.txt`)
3. Verify file is in correct directory
4. Call `load_dotenv()` before accessing variables

### CORS Issues

1. Check `CORS_ORIGINS` matches exactly (no trailing slash)
2. Include protocol (`https://` not just domain)
3. For multiple origins, use comma separation

---

## Related Documentation

- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Deployment instructions
- [AUTH_GUIDE.md](AUTH_GUIDE.md) - JWT configuration
- [EMAIL_SERVICE_GUIDE.md](EMAIL_SERVICE_GUIDE.md) - Email setup
- [AI_ANALYZER_GUIDE.md](AI_ANALYZER_GUIDE.md) - OpenAI setup

---

*Last Updated: January 2026*
*Version: 1.0*
