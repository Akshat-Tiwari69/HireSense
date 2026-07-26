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
web: gunicorn --worker-class eventlet --workers 1 app:app_with_socketio --bind 0.0.0.0:$PORT --timeout 90
```

**runtime.txt:**
```
python-3.11.9
```

**nixpacks.toml:**
```toml
[phases.setup]
nixPkgs = ["python311Full", "gcc", "postgresql"]
nixLibs = ["postgresql"]

[phases.install]
commands = [
  "python -m ensurepip --upgrade || true",
  "python -m pip install -r requirements.txt"
]

[start]
cmd = "LD_LIBRARY_PATH=/nix/var/nix/profiles/default/lib:$LD_LIBRARY_PATH gunicorn --worker-class eventlet --workers 1 app:app_with_socketio --bind 0.0.0.0:$PORT --timeout 90"
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
APP_ENV=production
ALLOW_RUNTIME_ENV_MUTATION=false
JWT_SECRET_KEY=<generated-64-character-random-value>
JWT_ACCESS_TOKEN_MINUTES=60
DATABASE_URL=postgresql://... (auto-set by Railway)
OPENAI_API_KEY=sk-your-openai-key
RESEND_API_KEY=re_your-resend-key
FRONTEND_URL=https://your-frontend-domain.com
CORS_ORIGINS=https://your-frontend-domain.com
TRUST_PROXY_HOPS=1
UPLOAD_FOLDER=/data/uploads
```

#### Persistent Upload Storage

Resumes and proctoring screenshots contain private candidate data. The default
`backend/uploads` directory is intended for local development only; ephemeral
containers can erase it during a restart or redeploy. In production, set
`UPLOAD_FOLDER` to a private persistent mounted volume (for example,
`/data/uploads`) or replace local storage with a durable object-store adapter.

Do not expose the upload root as a public/static directory. Restrict access,
encrypt and back it up as appropriate, and define a retention/deletion policy
that matches your hiring and privacy requirements. If an existing deployment
already has uploads, copy them before changing `UPLOAD_FOLDER` because database
records retain their stored file paths.

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
    startCommand: gunicorn --worker-class eventlet --workers 1 app:app_with_socketio --bind 0.0.0.0:$PORT --timeout 90
    envVars:
      - key: APP_ENV
        value: production
      - key: ALLOW_RUNTIME_ENV_MUTATION
        value: false
      - key: JWT_SECRET_KEY
        generateValue: true
      - key: JWT_ACCESS_TOKEN_MINUTES
        value: 60
      - key: FRONTEND_URL
        value: https://your-frontend-domain.com
      - key: CORS_ORIGINS
        value: https://your-frontend-domain.com
      - key: TRUST_PROXY_HOPS
        value: 1
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

# Initialize a fresh, empty database
cd backend
python scripts/run_migration.py --schema

# For an existing HireSense database, use the reconciliation path instead:
python scripts/run_migration.py --reconcile

# Direct SQL alternative for a fresh database (run from repository root):
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f database/schema_postgres.sql
```

The runner deliberately refuses fresh-schema mode when HireSense core tables
already exist. Back up an existing database before reconciliation and review
PostgreSQL warnings for historical duplicate data that may prevent optional
unique indexes from being created.

#### 3. Create Initial Admin

```python
# seed_production.py
import bcrypt
from user_db import create_user

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
| `APP_ENV` | Application environment; use `production` for hosted deployments | `production` |
| `ALLOW_RUNTIME_ENV_MUTATION` | Local admin `.env` editing opt-in; keep disabled in production | `false` |
| `JWT_SECRET_KEY` | JWT signing key | `random-64-char-string` |
| `JWT_ACCESS_TOKEN_MINUTES` | Staff bearer-token lifetime (5-480 minutes) | `60` |
| `DATABASE_URL` | PostgreSQL connection | `postgresql://user:pass@host/db` |
| `OPENAI_API_KEY` | OpenAI API key | `sk-...` |
| `RESEND_API_KEY` | Resend email API key | `re_...` |
| `FRONTEND_URL` | Canonical frontend base URL used in invitations | `https://frontend.com` |
| `CORS_ORIGINS` | Comma-separated HTTPS browser origins; required in production | `https://frontend.com` |
| `TRUST_PROXY_HOPS` | Exact reverse-proxy count (`0` without a proxy, `1` on Railway/Render) | `1` |
| `UPLOAD_FOLDER` | Private persistent storage path for resumes and evidence | `/data/uploads` |

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

Set `CORS_ORIGINS` to the exact HTTPS origins that host the frontend, without
paths, queries, fragments, credentials, or wildcards. The same validated list
protects HTTP and Socket.IO. Startup fails outside development if the variable
is missing or unsafe.

```text
CORS_ORIGINS=https://hire.example.com,https://admin.hire.example.com
```

Do not add the API origin unless it also serves a browser client. Local HTTP
origins are accepted only when `APP_ENV` is `dev`, `development`, `local`, or
`test`.

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

if os.environ.get('APP_ENV') == 'production':
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

- [ ] `APP_ENV=production`
- [ ] `ALLOW_RUNTIME_ENV_MUTATION=false`
- [ ] JWT_SECRET_KEY is secure (64+ chars)
- [ ] `JWT_ACCESS_TOKEN_MINUTES` is set to the intended staff session length
- [ ] DATABASE_URL configured
- [ ] `FRONTEND_URL` and `CORS_ORIGINS` use the exact production HTTPS frontend origin
- [ ] `TRUST_PROXY_HOPS` matches the deployment proxy topology (`1` on Railway/Render)
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

- [SETUP.md](SETUP.md) - Setup and environment variables
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture
- [DATABASE.md](DATABASE.md) - Database structure and migration modes

---

*Last Updated: May 2026*
