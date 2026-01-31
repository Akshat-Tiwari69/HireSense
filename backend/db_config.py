"""
Database Configuration Module
Supports Postgres (DATABASE_URL) for production and SQLite fallback for local dev.
"""

import os
import sqlite3
from urllib.parse import urlparse

import psycopg2
from psycopg2 import extensions


class QmarkCursor(extensions.cursor):
    """Cursor that accepts SQLite-style '?' placeholders by mapping to '%s'."""

    def execute(self, query, vars=None):  # type: ignore[override]
        if query and "?" in query:
            query = query.replace("?", "%s")
        return super().execute(query, vars)

    def executemany(self, query, vars_list):  # type: ignore[override]
        if query and "?" in query:
            query = query.replace("?", "%s")
        return super().executemany(query, vars_list)

# SQLite fallback path
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'database', 'elite_hire.db')
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


def _get_postgres_connection(database_url: str, use_dict_cursor: bool = False):
    """Create a Postgres connection using psycopg2."""
    # Render/Railway often provide postgres://; psycopg2 expects postgresql://
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    cursor_factory = QmarkDictCursor if use_dict_cursor else QmarkCursor
    return psycopg2.connect(database_url, cursor_factory=cursor_factory)


def _get_sqlite_connection(use_dict_cursor: bool = False):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    if use_dict_cursor:
        conn.row_factory = sqlite3.Row  # Enables dict-like access via row['column']
    return conn


def get_connection(use_dict_cursor: bool = False):
    """Return a DB connection (Postgres when DATABASE_URL is set, else SQLite).
    
    Args:
        use_dict_cursor: If True, rows can be accessed like dicts (row['column']).
                        For PostgreSQL: uses RealDictCursor.
                        For SQLite: uses sqlite3.Row.
    """
    database_url = os.environ.get("DATABASE_URL")
    try:
        if database_url:
            return _get_postgres_connection(database_url, use_dict_cursor)
        return _get_sqlite_connection(use_dict_cursor)
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None


def detect_driver():
    """Detect which database driver is active.
    
    Returns:
        str: 'postgres' if DATABASE_URL is set, 'sqlite' otherwise.
    """
    return 'postgres' if os.environ.get("DATABASE_URL") else 'sqlite'


def test_connection():
    """Test database connectivity for the active backend."""
    conn = None
    try:
        conn = get_connection()
        if conn is None:
            print("❌ Database connection failed!")
            return False

        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        print("✅ Database connected!")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    print(f"DATABASE_URL set: {'yes' if os.environ.get('DATABASE_URL') else 'no'}")
    if not os.environ.get('DATABASE_URL'):
        print(f"Using SQLite path: {DB_PATH}")
    test_connection()
