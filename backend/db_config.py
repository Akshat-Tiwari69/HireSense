import os
import logging
import threading
import psycopg2
import psycopg2.extras
from psycopg2.extensions import parse_dsn
from psycopg2.pool import ThreadedConnectionPool
from contextlib import contextmanager

logger = logging.getLogger(__name__)
_connection_pool = None
_pool_slots = None
_pool_lock = threading.Lock()
_DEVELOPMENT_ENVIRONMENTS = {"dev", "development", "local", "test"}
_SECURE_SSL_MODES = {"verify-full"}


def production_guards_required():
    return (
        os.environ.get("APP_ENV", "production").strip().lower()
        not in _DEVELOPMENT_ENVIRONMENTS
    )


def validate_database_url(
    database_url,
    *,
    require_tls=False,
    require_runtime_role=False,
):
    """Validate a PostgreSQL DSN without logging its credentials."""
    normalized = database_url.strip()
    if normalized.startswith("postgres://"):
        normalized = normalized.replace("postgres://", "postgresql://", 1)
    try:
        options = parse_dsn(normalized)
    except psycopg2.ProgrammingError as error:
        raise RuntimeError(
            "DATABASE_URL must be a valid PostgreSQL connection string with a valid sslmode"
        ) from error

    if require_tls and options.get("sslmode") not in _SECURE_SSL_MODES:
        raise RuntimeError(
            "Production database connections require sslmode=verify-full"
        )
    database_user = options.get("user", "").split(".", 1)[0]
    if require_runtime_role and database_user != "hiresense_app":
        raise RuntimeError(
            "Production DATABASE_URL must authenticate as the hiresense_app runtime role"
        )
    return normalized


def _statement_timeout_ms():
    raw_value = os.environ.get("DB_STATEMENT_TIMEOUT_MS", "30000")
    try:
        value = int(raw_value)
    except ValueError as error:
        raise RuntimeError("DB_STATEMENT_TIMEOUT_MS must be an integer") from error
    if not 1_000 <= value <= 600_000:
        raise RuntimeError("DB_STATEMENT_TIMEOUT_MS must be between 1000 and 600000")
    return value


def _pool_bounds():
    try:
        minimum = int(os.environ.get("DB_POOL_MIN", "1"))
        maximum = int(os.environ.get("DB_POOL_MAX", "8"))
    except ValueError as error:
        raise RuntimeError("DB_POOL_MIN and DB_POOL_MAX must be integers") from error
    if not 1 <= minimum <= maximum <= 20:
        raise RuntimeError(
            "DB_POOL_MIN and DB_POOL_MAX must satisfy 1 <= minimum <= maximum <= 20"
        )
    return minimum, maximum


def _pool_acquire_timeout_seconds():
    try:
        timeout = float(os.environ.get("DB_POOL_ACQUIRE_TIMEOUT_SECONDS", "5"))
    except ValueError as error:
        raise RuntimeError("DB_POOL_ACQUIRE_TIMEOUT_SECONDS must be a number") from error
    if not 0.1 <= timeout <= 30:
        raise RuntimeError(
            "DB_POOL_ACQUIRE_TIMEOUT_SECONDS must be between 0.1 and 30"
        )
    return timeout


def _database_url():
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError(
            "DATABASE_URL environment variable is required. "
            "Please set it to your PostgreSQL connection string."
        )
    production = production_guards_required()
    return validate_database_url(
        database_url,
        require_tls=production,
        require_runtime_role=production,
    )


def _verify_runtime_database_identity(connection):
    """Refuse a production role that can bypass the application RLS boundary."""
    cursor = connection.cursor()
    try:
        cursor.execute(
            """
            SELECT
                current_user,
                role_record.rolcanlogin,
                role_record.rolsuper,
                role_record.rolcreaterole,
                role_record.rolcreatedb,
                role_record.rolreplication,
                role_record.rolbypassrls,
                EXISTS (
                    SELECT 1
                      FROM pg_auth_members AS membership
                     WHERE membership.member = role_record.oid
                ),
                EXISTS (
                    SELECT 1
                      FROM pg_class AS table_record
                      JOIN pg_namespace AS namespace_record
                        ON namespace_record.oid = table_record.relnamespace
                     WHERE table_record.relowner = role_record.oid
                       AND namespace_record.nspname = 'public'
                       AND table_record.relkind IN ('r', 'p')
                )
              FROM pg_roles AS role_record
             WHERE role_record.rolname = current_user
            """
        )
        identity = cursor.fetchone()
    finally:
        cursor.close()

    if (
        identity is None
        or identity[0] != "hiresense_app"
        or not identity[1]
        or any(identity[2:])
    ):
        raise RuntimeError(
            "Production database identity is not the least-privilege hiresense_app role"
        )


def _verify_connection_pool_identity(pool):
    connection = pool.getconn()
    try:
        _verify_runtime_database_identity(connection)
    except Exception:
        pool.putconn(connection, close=True)
        pool.closeall()
        raise
    pool.putconn(connection)


def _get_connection_pool():
    global _connection_pool, _pool_slots
    if _connection_pool is not None:
        return _connection_pool

    with _pool_lock:
        if _connection_pool is None:
            minimum, maximum = _pool_bounds()
            pool = ThreadedConnectionPool(
                minimum,
                maximum,
                _database_url(),
                cursor_factory=psycopg2.extras.DictCursor,
                connect_timeout=10,
                application_name="hiresense-api",
                keepalives=1,
                keepalives_idle=30,
                keepalives_interval=10,
                keepalives_count=3,
                options=(
                    f"-c statement_timeout={_statement_timeout_ms()} "
                    "-c idle_in_transaction_session_timeout=30000"
                ),
            )
            if production_guards_required():
                _verify_connection_pool_identity(pool)
            _pool_slots = threading.BoundedSemaphore(maximum)
            _connection_pool = pool
    return _connection_pool


def get_connection():
    """Borrow a PostgreSQL connection from the process-local bounded pool."""
    slot_acquired = False
    try:
        pool = _get_connection_pool()
        slot_acquired = _pool_slots.acquire(
            timeout=_pool_acquire_timeout_seconds()
        )
        if not slot_acquired:
            raise psycopg2.pool.PoolError(
                "Database connection checkout timed out"
            )
        for _attempt in range(2):
            connection = pool.getconn()
            if not connection.closed:
                return connection
            pool.putconn(connection, close=True)
        raise RuntimeError("Database pool returned closed connections")
    except Exception:
        if slot_acquired:
            _pool_slots.release()
        logger.exception("Database connection failed")
        raise


def return_connection(conn):
    """Reset and return a connection, discarding connections that cannot be reused."""
    if conn is None:
        return

    pool = _connection_pool
    if pool is None:
        conn.close()
        return

    discard = bool(conn.closed)
    try:
        if not discard:
            conn.rollback()
    except Exception:
        discard = True
        logger.warning("Discarding a broken database connection", exc_info=True)
    try:
        pool.putconn(conn, close=discard)
    finally:
        _pool_slots.release()


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
