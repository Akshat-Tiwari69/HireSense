# Deployment Guide

## Recommended Stack
- Frontend: Vercel or Netlify
- Backend: Railway or Render
- Database: Managed PostgreSQL

## Backend Essentials
- Gunicorn with eventlet worker
- Production env vars configured (`APP_ENV`, `JWT_SECRET_KEY`, `DATABASE_URL`, `CORS_ORIGINS`)
- Persistent private upload storage (`UPLOAD_FOLDER`)

## Frontend Essentials
- Build with `npm run build`
- Set `VITE_API_BASE_URL` to deployed backend URL
- Configure SPA route rewrites

## Database Initialization
- Fresh install: `--schema`
- Existing install: `--reconcile`

## Production Checklist
- HTTPS enabled
- CORS restricted to known origins
- Rate limiting enabled
- Error responses sanitized
- Backup and restore process validated

## Source of Truth
See `/docs/DEPLOYMENT_GUIDE.md` for full platform-specific steps.
