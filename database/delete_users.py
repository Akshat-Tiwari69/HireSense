"""
HireSense - Delete All Users Script
USE WITH CAUTION: This will permanently remove ALL users from the database.

Usage:
    python delete_users.py
"""

import os
import sys
import argparse

# Load .env from the backend folder if running from project root
env_path = os.path.join(os.path.dirname(__file__), '..', 'backend', '.env')
if os.path.exists(env_path):
    from dotenv import load_dotenv
    load_dotenv(env_path)

try:
    import psycopg2
except ImportError:
    print("Missing dependency: psycopg2-binary")
    print("Run: pip install psycopg2-binary python-dotenv")
    sys.exit(1)

# ── CLI ────────────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser(description="Delete all users from the HireSense database.")
parser.add_argument(
    "--db-url",
    default=os.environ.get("DATABASE_URL"),
    help="PostgreSQL connection URL (defaults to DATABASE_URL env var)"
)
parser.add_argument(
    "--force",
    action="store_true",
    help="Skip confirmation prompt"
)
args = parser.parse_args()

if not args.db_url:
    print("ERROR: No database URL provided.")
    sys.exit(1)

# Normalise postgres:// → postgresql://
db_url = args.db_url
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

# ── Confirmation ───────────────────────────────────────────────────────────────
if not args.force:
    confirm = input("⚠️  WARNING: This will delete ALL users from the database. Are you sure? (y/n): ")
    if confirm.lower() != 'y':
        print("Operation cancelled.")
        sys.exit(0)

# ── Execute ────────────────────────────────────────────────────────────────────
try:
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    
    cur.execute("DELETE FROM users;")
    deleted_count = cur.rowcount
    
    conn.commit()
    print(f"\nSUCCESS: Deleted {deleted_count} users from the database.")
    conn.close()
except Exception as e:
    print(f"\nERROR: {e}")
    sys.exit(1)
