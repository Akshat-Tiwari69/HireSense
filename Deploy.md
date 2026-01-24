# Deploy Guide (Render-friendly, main branch only)

## Overview
- Backend: Flask (Gunicorn) on Render Web Service
- DB: Postgres (Render free tier) using `DATABASE_URL`
- Frontend: Vite static site on Render Static Site
- Auth: JWT
- Emails: SMTP (Gmail app password for dev), optional
- File uploads: Local `uploads/` (non-persistent on redeploy); for persistence use S3-compatible bucket (e.g., Cloudflare R2)

## Prereqs
- GitHub repo with `main` protected (deploys track `main` only)
- Render account
- OpenAI key (if using AI parsing)

## Backend Setup (Render)
1) In Render, create **Postgres** → copy `DATABASE_URL`.
2) Create **Web Service** pointing to repo path `/backend`.
   - Build command: `pip install -r requirements.txt`
   - Start command: `gunicorn app:app --bind 0.0.0.0:$PORT --timeout 90`
   - Branch: `main` (auto-deploy on main only)
3) Env vars (Render → Environment):
   - `DATABASE_URL` = from Render Postgres
   - `OPENAI_API_KEY` = your key
   - `JWT_SECRET_KEY` = random strong string
   - SMTP (optional): `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `SMTP_SENDER_NAME`
   - Optional storage: `STORAGE_BUCKET_URL`, `STORAGE_BUCKET_KEY`, `STORAGE_BUCKET_SECRET` (if you switch uploads to S3/R2)
   - **Use the internal Postgres URL for `DATABASE_URL`**; keep the external URL only for local psql/GUI access. Do not commit secrets.
4) Migrate DB (one-time):
   - From your machine (with psql): `psql "$DATABASE_URL" -f database/schema.sql`
   - Or add a Render "Manual Deploy Command" with the same line and run once.
5) Verify health: open Render service URL `/api/health` (or root) to confirm it responds.

## Frontend Setup (Render Static Site)
1) In Render, create **Static Site** pointing to `/frontend`.
   - Build command: `npm install && npm run build`
   - Publish directory: `dist`
   - Branch: `main`
2) Env var (Frontend):
   - `VITE_API_BASE_URL` = `https://<your-backend>.onrender.com`
3) After deploy, visit the static site URL; login/flows should hit the backend via the configured base URL.

## Local Dev
- Backend: `cd backend && python app.py`
- Frontend: `cd frontend && npm install && npm run dev`
- API base locally: defaults to `http://127.0.0.1:5000` (or same-origin if served together). Override with `VITE_API_BASE_URL` if needed.

## File Upload Persistence (optional but recommended)
- Current deploy uses local `uploads/` → will reset on each redeploy.
- To persist: provision S3-compatible storage (e.g., Cloudflare R2), add bucket creds, update upload code to write/read from bucket.

## Branch Behavior
- Render auto-deploy is pinned to `main`. Other branches do not deploy. With GitHub protection rules, only approved merges reach `main`.

## Quick Checklist
- [ ] `gunicorn` and `psycopg2-binary` in requirements (done)
- [ ] `Procfile` present (done)
- [ ] `db_config.py` reads `DATABASE_URL` (done)
- [ ] Frontend uses `VITE_API_BASE_URL` (done)
- [ ] Render Postgres created; `DATABASE_URL` set
- [ ] Backend service created; env vars set; build/start commands set
- [ ] DB schema applied to Postgres
- [ ] Frontend static site created; `VITE_API_BASE_URL` set
- [ ] Test login/upload/dashboard/assessment end-to-end on deployed URLs
