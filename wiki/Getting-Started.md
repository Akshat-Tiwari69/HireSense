# Getting Started

## Prerequisites
- Python 3.9+
- Node.js 20
- PostgreSQL 15+
- Optional: OpenAI API key

## Backend Setup
1. `cd backend`
2. `python -m venv venv`
3. Activate virtual environment
4. `pip install -r requirements.txt`
5. `cp .env.example .env`
6. Fresh DB: `python scripts/run_migration.py --schema`
   - Existing DB: `python scripts/run_migration.py --reconcile`
7. `python run.py`

Backend runs at `http://localhost:5000`.

## Frontend Setup
1. `cd frontend`
2. `npm install`
3. `cp .env.example .env.local`
4. `npm run dev`

Frontend runs at `http://localhost:5173`.

## Quality Checks
- Frontend: `npm run check`
- Backend tests: `pytest`
- Backend lint: `ruff check .`
- Syntax compile: `python -m compileall -q .`

## Next Reads
- [System Architecture](System-Architecture.md)
- [API Reference](API-Reference.md)
- [Roles and Permissions](Roles-and-Permissions.md)
