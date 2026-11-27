# Setup and installation guide

This guide walks you through setting up the HireSense development
environment on your local machine.

## Prerequisites

Before you begin, make sure you have the following installed:

- **Python** 3.12 (CI and production use 3.12; 3.10 is the minimum)
- **Node.js** 20–24 with npm 10 or newer
- **PostgreSQL** 15 or higher (local instance or Supabase)
- **Git** for version control

Optional (for AI features):

- **OpenAI API key** for resume analysis, job matching, and question generation

## Backend setup

1. Navigate to the backend directory:

   ```bash
   cd backend
   ```

2. Create and activate a virtual environment:

   ```bash
   python -m venv venv

   # Windows
   venv\Scripts\activate

   # macOS / Linux
   source venv/bin/activate
   ```

3. Install Python dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Copy the canonical environment template and replace its placeholder values:

   ```bash
   cp .env.example .env
   ```

   The backend reads the names in `backend/.env.example`. At minimum, set
   `DATABASE_URL` and a random `JWT_SECRET_KEY` of at least 32 characters.
   Keep `APP_ENV=development` from the template: when `APP_ENV` is unset the
   backend assumes production and applies the strict production checks (for
   example, it requires `sslmode=verify-full` on `DATABASE_URL`).
   `OPENAI_API_KEY` enables AI-backed features, while email can use either
   `RESEND_API_KEY` or the `SMTP_*` variables in the template.

   > **Note:** For local development you can create a `backend/local.env`
   > file instead. The application loads `local.env` first when present,
   > falling back to `.env`.

5. Initialize a fresh, empty database:

   ```bash
   python scripts/run_migration.py --schema
   ```

   If the database already contains an older HireSense installation, do not
   re-run the fresh schema. Reconcile it instead:

   ```bash
   python scripts/run_migration.py --reconcile
   ```

   Both commands use the canonical `database/schema_postgres.sql` and
   `database/migrations/20260713_reconcile_canonical_schema.sql` artifacts and
   verify required runtime columns before committing.

6. Start the backend server:

   ```bash
   python run.py
   ```

   The API is now available at `http://localhost:5000`.

7. Create the first staff accounts (run from the repository root):

   ```bash
   python database/seed_users.py
   ```

   This creates `admin@hiresense.com`, `interviewer@hiresense.com`, and
   `proctor@hiresense.com`. Set `SEED_ADMIN_PASSWORD`,
   `SEED_INTERVIEWER_PASSWORD`, and `SEED_PROCTOR_PASSWORD` to choose the
   passwords; any you leave out are generated and printed once. Create further
   users from the Admin Dashboard's **Users** tab.

## Frontend setup

1. Navigate to the frontend directory:

   ```bash
   cd frontend
   ```

2. Install Node.js dependencies:

   ```bash
   npm install
   ```

3. Create a `frontend/.env.local` file from the public template:

   ```bash
   cp .env.example .env.local
   ```

   `VITE_API_BASE_URL` is embedded into the browser bundle. Never place secrets
   in a `VITE_*` variable.

4. Start the development server:

   ```bash
   npm run dev
   ```

   The UI is now available at `http://localhost:5173`.

## Running both services

Open two terminal windows and start each service:

```bash
# Terminal 1 — Backend
cd backend && python run.py

# Terminal 2 — Frontend
cd frontend && npm run dev
```

In development the frontend calls the API on its own origin, and the Vite dev
server proxies `/api` and `/socket.io` (including WebSockets) to
`http://127.0.0.1:5000`. Leave `VITE_API_BASE_URL` empty unless the API is
served from a different origin.

## Database migrations

Use `python backend/scripts/run_migration.py --schema` once for a fresh
database. Use `--reconcile` for an existing installation. Historical files in
`database/migrations/` are records of past changes and are not an ordered setup
sequence; the dated `20260713` reconciliation migration is the supported legacy
upgrade path.

## User roles

There is no public registration endpoint. Staff accounts come from
`database/seed_users.py` or the Admin Dashboard. Available roles:

| Role | Description |
|------|------------|
| `super_admin` | Full system access, including managing admin accounts |
| `admin` | Full system access (treated as `super_admin` for job and sector rules) |
| `sector_admin` | Hiring review and job management within one sector (requires `sector_id`) |
| `recruiter` | Hiring review and job postings within one sector (requires `sector_id`) |
| `interviewer` | Review assigned candidates, schedule assessments, record decisions |
| `proctor` | Live session monitoring and violation review |

Candidates never get an account; they use the emailed assessment link.
See [ROLES.md](ROLES.md) for details.

## Production deployment

Production runs on a single VPS with Caddy and one Gunicorn/eventlet worker,
deployed from `main` by GitHub Actions. See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
and [deploy/README.md](../deploy/README.md).

To build the frontend locally:

```bash
cd frontend
npm run build
```

The output is written to `frontend/dist/`.

## Troubleshooting

- **Database connection errors** — Verify your `DATABASE_URL` is correct
  and that PostgreSQL is running. For Supabase, check that your IP is
  allowlisted.
- **OpenAI API errors** — Confirm your `OPENAI_API_KEY` is valid. AI
  features gracefully fall back to rule-based analysis when the key is
  missing.
- **CORS errors** — Set `CORS_ORIGINS` to a comma-separated list of exact
  frontend origins. Do not use wildcard origins in production.
- **WebSocket connection issues** — The Socket.IO server runs on the same
  port as the Flask API (5000). Verify that eventlet is installed correctly
  and that you opened the app through the Vite dev server so `/socket.io`
  is proxied.
- **Coding questions fail to run** — Code execution needs a Piston runner.
  In development the runner is enabled by default and expects Piston at
  `http://127.0.0.1:2000/api/v2/execute`; set `CODE_RUNNER_URL` to use another
  one. With `CODE_RUNNER_ENABLED=false`, technical assessments cannot be
  scheduled and only non-technical ones are available.
