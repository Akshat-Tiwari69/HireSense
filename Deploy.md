# Deploy Guide (Render + Railway, main branch only)

## Overview
- Backend: Flask (Gunicorn) on Render or Railway Web Service
- DB: Postgres (Render or Railway) using `DATABASE_URL`
- Frontend: Vite static site on Render Static Site or Railway service
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
    - Option A (Windows PowerShell, using external DB URL):
       ```pwsh
       # Replace with your EXTERNAL Postgres URL from Render
       $env:PGURL="postgresql://<user>:<pass>@<host>.render.com/<db>"
       psql "$env:PGURL" -f database/schema.sql
       ```
    - Option B (No psql installed): use the included Python script (psycopg2 is in requirements):
       ```pwsh
       # External URL recommended when running from your laptop
       $env:DATABASE_URL="postgresql://<user>:<pass>@<host>.render.com/<db>"
       python backend/migrate_postgres.py
       ```
    - Option C (On Render): set a one-time Manual Deploy Command to run either command using the INTERNAL URL already set as `DATABASE_URL`.
5) Verify health: open Render service URL `/api/health` (or root) to confirm it responds.

## Frontend Setup (Render Static Site)
1) In Render, create **Static Site** pointing to root `/` (not `/frontend`).
   - **Build command:** `cd frontend && npm install && npm run build`
   - **Publish directory:** `frontend/dist`
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

---

## Backend Setup (Railway)
1) Create a project in Railway and connect this GitHub repo.
2) Add a new service for the backend and set the **root directory** to `/backend`.
   - Railway will use Nixpacks to detect Python.
   - Build command (auto): `pip install -r requirements.txt`
   - Start command: `gunicorn app:app --bind 0.0.0.0:$PORT --timeout 90` (Procfile present)
3) Add a **Postgres** plugin in Railway and copy its `DATABASE_URL`.
4) Environment variables (Backend service → Variables):
   - `DATABASE_URL` = from Railway Postgres plugin
   - `OPENAI_API_KEY` = your key (optional)
   - `JWT_SECRET_KEY` = random strong string
   - SMTP (optional): `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `SMTP_SENDER_NAME`
5) Migrate/Initialize DB (one-time):
   - Option A (Railway Shell → Backend service):
     ```bash
     python init_db.py
     ```
   - Option B (Local with external connection string):
     ```pwsh
     $env:DATABASE_URL="postgresql://<user>:<pass>@<host>/<db>"
     python backend\init_db.py
     ```
6) Verify health: open Railway service URL `/api/health`.

## Frontend Setup (Railway)
Option A — Separate service (recommended):
- Create a new service and set **root directory** to `/frontend`.
- Build command: `npm install && npm run build`
- Start command: `npm run preview -- --host 0.0.0.0 --port $PORT`
- Environment variable: `VITE_API_BASE_URL` = `https://<your-backend>.railway.app`

Option B — Deploy to Vercel/Netlify, keep backend on Railway:
- Build and publish via provider UI, set `VITE_API_BASE_URL` to your Railway backend URL.

## Notes for Railway
- Railway sets `PORT` automatically; Gunicorn binds to it.
- `uploads/` is ephemeral; use S3-compatible storage for persistence.
- Protect `main` and deploy from `main` branch.
