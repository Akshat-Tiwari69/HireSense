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
    import secrets
    import string
    from werkzeug.security import generate_password_hash
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Run: pip install psycopg2-binary werkzeug python-dotenv")
    sys.exit(1)


def _generate_password(length=20):
    alphabet = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def _get_or_generate(env_key, label):
    val = os.environ.get(env_key)
    if val:
        return val, False
    generated = _generate_password()
    print(f"  INFO  {label}: no {env_key} env var set — generated a one-time password (shown below)")
    return generated, True


# ── Default users to seed ──────────────────────────────────────────────────────
_admin_pw, _admin_generated = _get_or_generate('SEED_ADMIN_PASSWORD', 'Admin')
_interviewer_pw, _interviewer_generated = _get_or_generate('SEED_INTERVIEWER_PASSWORD', 'Interviewer')
_proctor_pw, _proctor_generated = _get_or_generate('SEED_PROCTOR_PASSWORD', 'Proctor')

DEFAULT_USERS = [
    {
        "name":  "Admin User",
        "email": "admin@hiresense.com",
        "password": _admin_pw,
        "role":  "admin",
        "show_password": _admin_generated,
    },
    {
        "name":  "Interviewer User",
        "email": "interviewer@hiresense.com",
        "password": _interviewer_pw,
        "role":  "interviewer",
        "show_password": _interviewer_generated,
    },
    {
        "name":  "Proctor User",
        "email": "proctor@hiresense.com",
        "password": _proctor_pw,
        "role":  "proctor",
        "show_password": _proctor_generated,
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
        if user.get('show_password'):
            print(f"  OK    {user['email']} | role={user['role']} | ONE-TIME PASSWORD: {user['password']} | id={new_id}")
        else:
            print(f"  OK    {user['email']} | role={user['role']} | password set from env | id={new_id}")
        created += 1

    except Exception as e:
        print(f"  ERROR {user['email']}: {e}")
        conn.rollback()

conn.commit()
conn.close()

# ── Summary ────────────────────────────────────────────────────────────────────
print(f"\nDone! Created {created} user(s), skipped {skipped} existing.")
if created > 0:
    print("\n⚠️  Store any generated passwords shown above — they will not be shown again.")
