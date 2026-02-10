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

4. Create a `backend/.env` file with the following configuration:

   ```properties
   # Database
   DATABASE_URL=postgresql://postgres:password@localhost:5432/elite_hire

   # Security
   SECRET_KEY=your_flask_secret_key
   JWT_SECRET_KEY=your_jwt_signing_key

   # OpenAI (required for AI features)
   OPENAI_API_KEY=your_openai_api_key

   # Supabase (optional, if using Supabase as your database host)
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=your_anon_key

   # Email — SMTP (optional)
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USERNAME=your_email@gmail.com
   SMTP_PASSWORD=your_app_password

   # Email — Resend (optional, alternative to SMTP)
   RESEND_API_KEY=your_resend_api_key
   ```

   > **Note:** For local development you can create a `backend/local.env`
   > file instead. The application loads `local.env` first when present,
   > falling back to `.env`.

5. Initialize the database:

   ```bash
   psql "$DATABASE_URL" -f ../database/schema_postgresql.sql
   ```

6. Start the backend server:

   ```bash
   python app.py
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

3. Create a `frontend/.env` file:

   ```properties
   VITE_API_BASE_URL=http://localhost:5000
   ```

4. Start the development server:

   ```bash
   npm run dev
   ```

   The UI is now available at `http://localhost:5173`.

## Running both services

Open two terminal windows and start each service:

```bash
# Terminal 1 — Backend
cd backend && python app.py

# Terminal 2 — Frontend
cd frontend && npm run dev
```

The frontend auto-detects the backend URL. If you access the app from a
network IP (for example, testing on another device), the frontend falls
back to `http://<your-ip>:5000` automatically.

## Database migrations

Incremental migrations are stored in `database/migrations/`. Apply them in
order after the initial schema import:

```bash
psql "$DATABASE_URL" -f database/migrations/add_assessment_token.sql
psql "$DATABASE_URL" -f database/migrations/add_job_postings_sectors_rbac.sql
```

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
- **CORS errors** — The backend enables CORS for all origins in development.
  For production, configure allowed origins in `app.py`.
- **WebSocket connection issues** — The Socket.IO server runs on the same
  port as the Flask API (5000). Verify that eventlet is installed correctly.
