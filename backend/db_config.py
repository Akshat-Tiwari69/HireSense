import os
import psycopg2
import psycopg2.extras
from psycopg2 import pool
import threading
from contextlib import contextmanager

# Thread-local storage for connection pool (ensures pool is per-thread for thread safety)
_thread_local = threading.local()


class QmarkCursor(psycopg2.extras.DictCursor):
    """Custom cursor that uses ? placeholders instead of %s."""
    def execute(self, query, vars=None):
        if vars:
            query = query.replace("?", "%s")
        return super().execute(query, vars)

    def executemany(self, query, vars_list):
        query = query.replace("?", "%s")
        return super().executemany(query, vars_list)


def _get_connection_pool():
    """Get or create a connection pool for better performance.
    
    Connection pooling reduces overhead of creating new connections for each query.
    This can provide 10-50x speedup for high-frequency API endpoints.
    """
    if not hasattr(_thread_local, 'pool') or _thread_local.pool is None:
        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            raise RuntimeError(
                "DATABASE_URL environment variable is required. "
                "Please set it to your PostgreSQL connection string."
            )
        
        # Fix postgres:// to postgresql://
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        
        try:
            # Create connection pool with 2 minimum and 5 maximum connections
            # Supabase free tier has limited connection slots, so keep this low
            _thread_local.pool = pool.SimpleConnectionPool(
                2,  # minconn - minimum connections to keep open
                5,  # maxconn - maximum connections in pool
                database_url,
                cursor_factory=QmarkCursor
            )
        except Exception as e:
            print(f"Connection pool creation error: {e}")
            raise
    
    return _thread_local.pool


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
        
        conn = psycopg2.connect(database_url, cursor_factory=QmarkCursor)
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
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
    except Exception as e:
        print(f"Error closing connection: {e}")


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
    """Execute a query and optionally return results using pooled connection."""
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
    except Exception as e:
        conn.rollback()
        print(f"Query error: {e}")
        raise
    finally:
        # Return connection to pool instead of closing (connection pooling optimization)
        return_connection(conn)


def execute_many(query, params_list):
    """Execute a query with multiple parameter sets using pooled connection."""
    conn = get_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        cursor.executemany(query, params_list)
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Batch query error: {e}")
        raise
    finally:
        # Return connection to pool instead of closing (connection pooling optimization)
        return_connection(conn)
