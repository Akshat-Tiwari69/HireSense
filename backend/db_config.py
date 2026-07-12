import os
import logging
import psycopg2
import psycopg2.extras
from contextlib import contextmanager

logger = logging.getLogger(__name__)


def _statement_timeout_ms():
    raw_value = os.environ.get("DB_STATEMENT_TIMEOUT_MS", "30000")
    try:
        value = int(raw_value)
    except ValueError as error:
        raise RuntimeError("DB_STATEMENT_TIMEOUT_MS must be an integer") from error
    if not 1_000 <= value <= 600_000:
        raise RuntimeError("DB_STATEMENT_TIMEOUT_MS must be between 1000 and 600000")
    return value


def get_connection():
    """Return a PostgreSQL database connection.
    
    For Supabase free tier with limited connection slots, uses a simple connection
    instead of pooling. Connection pooling would exhaust the available slots.
    """
    try:
        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            raise RuntimeError(
                "DATABASE_URL environment variable is required. "
                "Please set it to your PostgreSQL connection string."
            )
        
        # Fix postgres:// to postgresql://
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        
        conn = psycopg2.connect(
            database_url,
            cursor_factory=psycopg2.extras.DictCursor,
            connect_timeout=10,
            application_name="hiresense-api",
            options=(
                f"-c statement_timeout={_statement_timeout_ms()} "
                "-c idle_in_transaction_session_timeout=30000"
            ),
        )
        return conn
    except Exception:
        logger.exception("Database connection failed")
        raise


def return_connection(conn):
    """Close a database connection.
    
    Since we're not using connection pooling on Supabase free tier,
    we simply close the connection to free up the slot.
    """
    if conn is None:
        return
    
    try:
        conn.close()
    except Exception:
        logger.warning("Failed to close database connection", exc_info=True)


@contextmanager
def db_connection():
    """Context manager for database connections that guarantees cleanup.
    
    Usage:
        with db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(...)
            conn.commit()
    
    On exception, the connection is rolled back and closed automatically.
    On success, the caller is responsible for calling conn.commit().
    The connection is always closed when the block exits.
    """
    conn = get_connection()
    try:
        yield conn
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        raise
    finally:
        return_connection(conn)


def execute_query(query, params=None, fetch_one=False, fetch_all=False):
    """Execute a query and optionally return results using a managed connection."""
    conn = get_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        cursor.execute(query, params or ())
        
        if fetch_one:
            result = cursor.fetchone()
        elif fetch_all:
            result = cursor.fetchall()
        else:
            result = None
        
        conn.commit()
        return result
    except Exception:
        conn.rollback()
        logger.exception("Database query failed")
        raise
    finally:
        return_connection(conn)


def execute_many(query, params_list):
    """Execute a query with multiple parameter sets using a managed connection."""
    conn = get_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        cursor.executemany(query, params_list)
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        logger.exception("Database batch query failed")
        raise
    finally:
        return_connection(conn)
