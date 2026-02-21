"""
HireSense - Database User Seeder
Run this script after creating a new database to set up default users.

Usage:
    python seed_users.py
    python seed_users.py --db-url postgresql://postgres:password@localhost:5432/mydb

Requirements:
    pip install psycopg2-binary werkzeug python-dotenv
"""

import argparse
import os
import sys

# Load .env from the backend folder if running from project root
env_path = os.path.join(os.path.dirname(__file__), '..', 'backend', '.env')
if os.path.exists(env_path):
    from dotenv import load_dotenv
    load_dotenv(env_path)

try:
    import psycopg2
    from werkzeug.security import generate_password_hash
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Run: pip install psycopg2-binary werkzeug python-dotenv")
    sys.exit(1)

# ── Default users to seed ──────────────────────────────────────────────────────
DEFAULT_USERS = [
    {
        "name":  "Admin User",
        "email": "admin@hiresense.com",
        "password": "admin123",
        "role":  "admin",
    },
    {
        "name":  "Interviewer User",
        "email": "interviewer@hiresense.com",
        "password": "interviewer123",
        "role":  "interviewer",
    },
    {
        "name":  "Proctor User",
        "email": "proctor@hiresense.com",
        "password": "proctor123",
        "role":  "proctor",
    },
]

# ── CLI ────────────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser(description="Seed default HireSense users into a PostgreSQL database.")
parser.add_argument(
    "--db-url",
    default=os.environ.get("DATABASE_URL"),
    help="PostgreSQL connection URL (defaults to DATABASE_URL env var)"
)
parser.add_argument(
    "--skip-existing",
    action="store_true",
    default=True,
    help="Skip users that already exist (default: True)"
)
args = parser.parse_args()

if not args.db_url:
    print("ERROR: No database URL provided.")
    print("Either set DATABASE_URL in backend/.env or pass --db-url")
    sys.exit(1)

# Normalise postgres:// → postgresql://
db_url = args.db_url
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

# ── Connect ────────────────────────────────────────────────────────────────────
print(f"\nConnecting to database...")
try:
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    print("Connected ✓\n")
except Exception as e:
    print(f"Connection failed: {e}")
    sys.exit(1)

# ── Seed users ─────────────────────────────────────────────────────────────────
created = 0
skipped = 0

for user in DEFAULT_USERS:
    try:
        # Check if user already exists
        cur.execute("SELECT id FROM users WHERE email = %s", (user["email"],))
        existing = cur.fetchone()

        if existing:
            print(f"  SKIP  {user['email']} (already exists, id={existing[0]})")
            skipped += 1
            continue

        # Insert new user
        cur.execute(
            """
            INSERT INTO users (email, password_hash, role, name)
            VALUES (%s, %s, %s, %s)
            RETURNING id
            """,
            (
                user["email"],
                generate_password_hash(user["password"]),
                user["role"],
                user["name"],
            ),
        )
        new_id = cur.fetchone()[0]
        print(f"  OK    {user['email']} | role={user['role']} | password={user['password']} | id={new_id}")
        created += 1

    except Exception as e:
        print(f"  ERROR {user['email']}: {e}")
        conn.rollback()

conn.commit()
conn.close()

# ── Summary ────────────────────────────────────────────────────────────────────
print(f"\nDone! Created {created} user(s), skipped {skipped} existing.")
if created > 0:
    print("\nDefault credentials:")
    print("  Admin:       admin@hiresense.com      / admin123")
    print("  Interviewer: interviewer@hiresense.com / interviewer123")
    print("  Proctor:     proctor@hiresense.com     / proctor123")
    print("\n⚠️  Change these passwords after first login!")
