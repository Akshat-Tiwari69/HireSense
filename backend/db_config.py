"""
Database Configuration Module
PostgreSQL only (Render production)
"""

import os
from urllib.parse import urlparse
import psycopg2
from psycopg2 import extensions
from psycopg2.extras import RealDictCursor


class QmarkCursor(extensions.cursor):
    """Cursor that accepts SQLite-style '?' placeholders by mapping to '%s'."""
    def execute(self, query, vars=None):
        if query and "?" in query:
            query = query.replace("?", "%s")
        return super().execute(query, vars)
    def executemany(self, query, vars_list):
        if query and "?" in query:
            query = query.replace("?", "%s")
        return super().executemany(query, vars_list)


class QmarkDictCursor(RealDictCursor):
    """Cursor that combines RealDictCursor (dict-like rows) with ? placeholder support."""
    def execute(self, query, vars=None):
        if query and "?" in query:
            query = query.replace("?", "%s")
        return super().execute(query, vars)
    def executemany(self, query, vars_list):
        if query and "?" in query:
            query = query.replace("?", "%s")
        return super().executemany(query, vars_list)


def get_connection(use_dict_cursor: bool = False):
    """Return a PostgreSQL database connection (requires DATABASE_URL)."""
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL environment variable must be set for PostgreSQL connection.")
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    cursor_factory = QmarkDictCursor if use_dict_cursor else QmarkCursor
    return psycopg2.connect(database_url, cursor_factory=cursor_factory)


def detect_driver():
    """Always returns 'postgres' since we only support PostgreSQL."""
    return 'postgres'


def test_connection():
    conn = None
    try:
        conn = get_connection()
        if conn is None:
            print("❌ Database connection failed!")
            return False
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        print("✅ PostgreSQL database connected!")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    db_url = os.environ.get('DATABASE_URL')
    print(f"DATABASE_URL set: {'yes' if db_url else 'no'}")
    if not db_url:
        print("⚠️  Set DATABASE_URL environment variable to connect to PostgreSQL")
    else:
        test_connection()


