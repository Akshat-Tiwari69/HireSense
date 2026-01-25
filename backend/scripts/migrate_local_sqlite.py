"""
Local SQLite migration helper for development.

What it does:
1) Adds new columns to scheduled_assessments if missing:
   - access_token (VARCHAR(64))
   - proctoring_enabled (BOOLEAN DEFAULT 1)
   - started_at (TEXT)
   - completed_at (TEXT)
2) Backfills access_token for any existing rows missing a token.

Usage (from backend folder):
    python scripts/migrate_local_sqlite.py

Notes:
- This only affects the local SQLite database (database.db).
- It is safe to re-run; operations are idempotent.
"""

import hashlib
import os
import sqlite3
import time
from pathlib import Path


# Local SQLite path (adjusted for repo layout)
# backend/scripts/ -> ../database/elite_hire.db
DB_PATH = (Path(__file__).resolve().parent.parent.parent / "database" / "elite_hire.db").resolve()


def ensure_columns(conn):
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(scheduled_assessments)")
    cols = {row[1] for row in cursor.fetchall()}

    def add_if_missing(name: str, ddl: str):
        if name not in cols:
            cursor.execute(ddl)
            print(f"Added column: {name}")
        else:
            print(f"Column already exists: {name}")

    add_if_missing("access_token", "ALTER TABLE scheduled_assessments ADD COLUMN access_token VARCHAR(64)")
    add_if_missing("proctoring_enabled", "ALTER TABLE scheduled_assessments ADD COLUMN proctoring_enabled BOOLEAN DEFAULT 1")
    add_if_missing("started_at", "ALTER TABLE scheduled_assessments ADD COLUMN started_at TEXT")
    add_if_missing("completed_at", "ALTER TABLE scheduled_assessments ADD COLUMN completed_at TEXT")

    conn.commit()


def backfill_tokens(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT id, access_token FROM scheduled_assessments")
    rows = cursor.fetchall()
    updated = 0
    for row_id, token in rows:
        if not token:
            new_token = hashlib.md5(f"{row_id}-{time.time()}".encode()).hexdigest()
            cursor.execute(
                "UPDATE scheduled_assessments SET access_token = ? WHERE id = ?",
                (new_token, row_id),
            )
            updated += 1
    conn.commit()
    print(f"Backfilled tokens for {updated} rows")


def main():
    if not DB_PATH.exists():
        raise SystemExit(f"database.db not found at {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    try:
        ensure_columns(conn)
        backfill_tokens(conn)
    finally:
        conn.close()

    print("Migration completed successfully for local SQLite.")


if __name__ == "__main__":
    main()
