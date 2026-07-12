# Setup and installation guide

This guide walks you through setting up the HireSense development
environment on your local machine.

## Prerequisites

Before you begin, make sure you have the following installed:

- **Python** 3.9 or higher
- **Node.js** 16.0 or higher
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

The frontend auto-detects the backend URL. If you access the app from a
network IP (for example, testing on another device), the frontend falls
back to `http://<your-ip>:5000` automatically.

## Database migrations

Use `python backend/scripts/run_migration.py --schema` once for a fresh
database. Use `--reconcile` for an existing installation. Historical files in
`database/migrations/` are records of past changes and are not an ordered setup
sequence; the dated `20260713` reconciliation migration is the supported legacy
upgrade path.

## Default user roles

After database initialization, register users through the
`POST /api/auth/register` endpoint. Available roles:

| Role | Description |
|------|------------|
| `admin` | Full system access (maps to super_admin internally) |
| `interviewer` | Candidate management and assessment scheduling |
| `proctor` | Live session monitoring and violation tracking |
| `sector_admin` | Sector-scoped job and candidate management |
| `recruiter` | Job postings and candidate matching |

## Production deployment

The project includes configuration for cloud platforms such as Railway,
Render, and Heroku.

### Backend

The backend uses Gunicorn as the production WSGI server. Deployment
configuration:

- `Procfile` — Gunicorn process definition
- `nixpacks.toml` — Nixpacks build configuration
- `runtime.txt` — Python version specification

### Frontend

Build the production bundle:

```bash
cd frontend
npm run build
```

The optimized output is generated in `frontend/dist/`. Deploy this
directory to any static hosting provider.

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
  port as the Flask API (5000). Verify that eventlet is installed correctly.
