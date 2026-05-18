# Deployment Guide

Complete guide for deploying HireSense to production environments.

---

## Deployment Options

| Platform | Frontend | Backend | Database | Best For |
|----------|----------|---------|----------|----------|
| Railway | N/A | Flask | PostgreSQL | Backend + DB |
| Render | N/A | Flask | PostgreSQL | Backend + DB |
| Vercel | React/Vite | N/A | N/A | Frontend only |
| Netlify | React/Vite | N/A | N/A | Frontend only |
| Heroku | Both | Flask | PostgreSQL | Full stack |
| AWS | Both | EC2/Lambda | RDS | Enterprise |

**Recommended Setup:**
- Frontend: Vercel or Netlify
- Backend: Railway or Render
- Database: Managed PostgreSQL

---

## Backend Deployment

### Railway Deployment

#### 1. Prepare Project

Ensure these files exist in `backend/`:

```
backend/
├── app.py
├── requirements.txt
├── Procfile
├── runtime.txt
└── nixpacks.toml
```

**Procfile:**
```
web: gunicorn app:app
```

**runtime.txt:**
```
python-3.11.0
```

**nixpacks.toml:**
```toml
[phases.setup]
nixPkgs = ["python311"]

[phases.install]
cmds = ["pip install -r requirements.txt"]

[start]
cmd = "gunicorn app:app --bind 0.0.0.0:$PORT"
```

#### 2. Deploy to Railway

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Initialize project
cd backend
railway init

# Add PostgreSQL
railway add --plugin postgresql

# Deploy
railway up
```

#### 3. Configure Environment Variables

In Railway dashboard, add:

```
FLASK_ENV=production
JWT_SECRET_KEY=your-production-secret-key
DATABASE_URL=postgresql://... (auto-set by Railway)
OPENAI_API_KEY=sk-your-openai-key
RESEND_API_KEY=re_your-resend-key
CORS_ORIGINS=https://your-frontend-domain.com
```

---

### Render Deployment

#### 1. Create render.yaml

```yaml
# render.yaml
services:
  - type: web
    name: elite-hire-backend
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn app:app
    envVars:
      - key: FLASK_ENV
        value: production
      - key: JWT_SECRET_KEY
        generateValue: true
      - key: DATABASE_URL
        fromDatabase:
          name: elite-hire-db
          property: connectionString

databases:
  - name: elite-hire-db
    plan: free
```

#### 2. Deploy

1. Push code to GitHub
2. Connect Render to repository
3. Render auto-deploys on push

---

## Frontend Deployment

### Vercel Deployment

#### 1. Configure Build

Create `vercel.json` in frontend/:

```json
{
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "framework": "vite",
  "rewrites": [
    { "source": "/(.*)", "destination": "/index.html" }
  ]
}
```

#### 2. Set Environment Variables

```bash
# In Vercel dashboard or CLI
VITE_API_BASE_URL=https://your-backend-url.railway.app
```

#### 3. Deploy

```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
cd frontend
vercel
```

---

### Netlify Deployment

#### 1. Configure Build

Create `netlify.toml` in frontend/:

```toml
[build]
  command = "npm run build"
  publish = "dist"

[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200
```

#### 2. Deploy

```bash
# Install Netlify CLI
npm install -g netlify-cli

# Deploy
cd frontend
netlify deploy --prod
```

---

## Database Setup

### PostgreSQL Migration

#### 1. Create Production Database

Railway/Render automatically provision PostgreSQL.

For manual setup:
```sql
CREATE DATABASE elite_hire_prod;
CREATE USER elite_hire_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE elite_hire_prod TO elite_hire_user;
```

#### 2. Run Schema Migration

```bash
# Set DATABASE_URL
export DATABASE_URL="postgresql://user:pass@host:5432/elite_hire_prod"

# Apply schema
cd backend
python scripts/run_migration.py

# Or apply the SQL directly:
psql $DATABASE_URL < database/schema_postgres.sql
```

#### 3. Create Initial Admin

```python
# seed_production.py
import bcrypt
from db_helpers import create_user

password_hash = bcrypt.hashpw(
    'your-secure-admin-password'.encode('utf-8'),
    bcrypt.gensalt()
).decode('utf-8')

create_user(
    email='admin@yourcompany.com',
    password_hash=password_hash,
    role='admin',
    name='Admin User'
)
```

---

## Environment Configuration

### Production Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `FLASK_ENV` | Flask environment | `production` |
| `JWT_SECRET_KEY` | JWT signing key | `random-64-char-string` |
| `DATABASE_URL` | PostgreSQL connection | `postgresql://user:pass@host/db` |
| `OPENAI_API_KEY` | OpenAI API key | `sk-...` |
| `RESEND_API_KEY` | Resend email API key | `re_...` |
| `CORS_ORIGINS` | Allowed CORS origins | `https://frontend.com` |

### Generate Secure Keys

```bash
# Generate JWT secret
python -c "import secrets; print(secrets.token_hex(32))"

# Or using openssl
openssl rand -hex 32
```

---

## CORS Configuration

### Production CORS Setup

```python
# app.py
from flask_cors import CORS
import os

app = Flask(__name__)

# Production CORS
cors_origins = os.environ.get('CORS_ORIGINS', 'http://localhost:5173')
CORS(app, resources={
    r"/api/*": {
        "origins": cors_origins.split(','),
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})
```

---

## SSL/HTTPS

### Railway/Render

SSL is automatically provided for all deployments.

### Custom Domain

1. Add custom domain in platform dashboard
2. Update DNS records:
   ```
   CNAME api.yourdomain.com -> your-app.railway.app
   ```
3. SSL certificate auto-provisioned

---

## Monitoring

### Health Check Endpoint

```python
@app.route('/api/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'version': '1.0.0',
        'database': check_db_connection()
    })
```

### Logging Configuration

```python
import logging
from logging.handlers import RotatingFileHandler

if os.environ.get('FLASK_ENV') == 'production':
    handler = RotatingFileHandler(
        'logs/app.log',
        maxBytes=10000000,
        backupCount=5
    )
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)
```

---

## Deployment Checklist

### Pre-Deployment

- [ ] All tests passing
- [ ] Environment variables documented
- [ ] Database schema up to date
- [ ] Static files built (`npm run build`)
- [ ] Dependencies locked (`pip freeze > requirements.txt`)

### Backend

- [ ] `FLASK_ENV=production`
- [ ] JWT_SECRET_KEY is secure (64+ chars)
- [ ] DATABASE_URL configured
- [ ] CORS_ORIGINS set to frontend domain
- [ ] OpenAI API key configured
- [ ] Email service configured (Resend or SMTP)
- [ ] Gunicorn as WSGI server

### Frontend

- [ ] VITE_API_BASE_URL points to production backend
- [ ] Build successful (`npm run build`)
- [ ] SPA routing configured (redirects)

### Database

- [ ] PostgreSQL provisioned
- [ ] Schema migrated
- [ ] Initial admin user created
- [ ] Backup strategy in place

### Security

- [ ] HTTPS enabled
- [ ] Secure headers configured
- [ ] Rate limiting enabled
- [ ] Input validation active
- [ ] Error messages sanitized

---

## Troubleshooting

### Common Issues

#### "ModuleNotFoundError"

```bash
# Ensure all dependencies in requirements.txt
pip freeze > requirements.txt
```

#### "Database connection failed"

1. Check DATABASE_URL format
2. Verify PostgreSQL is running
3. Check network/firewall rules

#### "CORS error"

1. Verify CORS_ORIGINS matches frontend URL
2. Check for trailing slashes
3. Ensure preflight requests handled

#### "JWT token invalid"

1. Ensure JWT_SECRET_KEY same across restarts
2. Check token expiration
3. Verify Authorization header format

---

## Scaling

### Horizontal Scaling

Railway/Render support scaling:
```bash
# Railway
railway scale web=3

# Render: Configure in dashboard
```

### Database Connection Pooling

```python
# For production PostgreSQL
from psycopg2 import pool

connection_pool = pool.ThreadedConnectionPool(
    minconn=5,
    maxconn=20,
    dsn=DATABASE_URL
)
```

### Caching

Consider adding Redis for:
- Session storage
- API response caching
- Rate limiting

---

## Backup & Recovery

### Database Backup

```bash
# Manual backup
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql

# Automated (cron)
0 2 * * * pg_dump $DATABASE_URL > /backups/daily_$(date +\%Y\%m\%d).sql
```

### Restore

```bash
psql $DATABASE_URL < backup_20260125.sql
```

---

## Related Documentation

- [ENVIRONMENT_CONFIG.md](ENVIRONMENT_CONFIG.md) - All environment variables
- [PROJECT_ARCHITECTURE.md](PROJECT_ARCHITECTURE.md) - System architecture
- [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md) - Database structure

---

*Last Updated: May 2026*
