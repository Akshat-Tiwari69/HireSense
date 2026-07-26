import pytest
from psycopg2.pool import PoolError

import db_config


class FakeConnection:
    def __init__(self, *, closed=False, rollback_error=None):
        self.closed = int(closed)
        self.rollback_error = rollback_error
        self.rollback_calls = 0

    def rollback(self):
        self.rollback_calls += 1
        if self.rollback_error:
            raise self.rollback_error


class FakePool:
    def __init__(self, connections):
        self.connections = list(connections)
        self.returned = []

    def getconn(self):
        return self.connections.pop(0)

    def putconn(self, connection, close=False):
        self.returned.append((connection, close))


class FakeSlots:
    def __init__(self, acquired=True):
        self.acquired = acquired
        self.releases = 0

    def acquire(self, timeout=None):
        self.timeout = timeout
        return self.acquired

    def release(self):
        self.releases += 1


@pytest.fixture(autouse=True)
def reset_connection_pool(monkeypatch):
    monkeypatch.setattr(db_config, "_connection_pool", None)
    monkeypatch.setattr(db_config, "_pool_slots", None)


def test_connection_pool_is_created_once_and_reuses_returned_connections(monkeypatch):
    connection = FakeConnection()
    pool = FakePool([connection, connection])
    constructor_calls = []

    def create_pool(minimum, maximum, database_url, **kwargs):
        constructor_calls.append((minimum, maximum, database_url, kwargs))
        return pool

    monkeypatch.setenv("DATABASE_URL", "postgresql://runtime@example.test/database")
    monkeypatch.setenv("DB_POOL_MIN", "1")
    monkeypatch.setenv("DB_POOL_MAX", "2")
    monkeypatch.setattr(db_config, "ThreadedConnectionPool", create_pool)

    first = db_config.get_connection()
    db_config.return_connection(first)
    second = db_config.get_connection()

    assert second is connection
    assert len(constructor_calls) == 1
    assert constructor_calls[0][:3] == (
        1,
        2,
        "postgresql://runtime@example.test/database",
    )
    assert pool.returned == [(connection, False)]


def test_connection_pool_is_published_only_after_its_slot_guard(monkeypatch):
    pool = FakePool([])
    pool_seen_during_slot_initialization = []

    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("DATABASE_URL", "postgresql://runtime@example.test/database")
    monkeypatch.setattr(
        db_config,
        "ThreadedConnectionPool",
        lambda *_args, **_kwargs: pool,
    )

    def create_slots(_maximum):
        pool_seen_during_slot_initialization.append(db_config._connection_pool)
        return FakeSlots()

    monkeypatch.setattr(db_config.threading, "BoundedSemaphore", create_slots)

    assert db_config._get_connection_pool() is pool
    assert pool_seen_during_slot_initialization == [None]
    assert isinstance(db_config._pool_slots, FakeSlots)


def test_return_connection_rolls_back_before_reuse(monkeypatch):
    connection = FakeConnection()
    pool = FakePool([])
    slots = FakeSlots()
    monkeypatch.setattr(db_config, "_connection_pool", pool)
    monkeypatch.setattr(db_config, "_pool_slots", slots)

    db_config.return_connection(connection)

    assert connection.rollback_calls == 1
    assert pool.returned == [(connection, False)]
    assert slots.releases == 1


@pytest.mark.parametrize(
    "connection",
    [
        FakeConnection(closed=True),
        FakeConnection(rollback_error=RuntimeError("connection lost")),
    ],
)
def test_return_connection_discards_closed_or_broken_connections(monkeypatch, connection):
    pool = FakePool([])
    slots = FakeSlots()
    monkeypatch.setattr(db_config, "_connection_pool", pool)
    monkeypatch.setattr(db_config, "_pool_slots", slots)

    db_config.return_connection(connection)

    assert pool.returned == [(connection, True)]
    assert slots.releases == 1


def test_connection_checkout_waits_for_a_slot_instead_of_exhausting_pool(monkeypatch):
    pool = FakePool([])
    slots = FakeSlots(acquired=False)
    monkeypatch.setattr(db_config, "_connection_pool", pool)
    monkeypatch.setattr(db_config, "_pool_slots", slots)
    monkeypatch.setenv("DB_POOL_ACQUIRE_TIMEOUT_SECONDS", "3")

    with pytest.raises(PoolError, match="timed out"):
        db_config.get_connection()

    assert slots.timeout == 3.0


@pytest.mark.parametrize(
    ("minimum", "maximum"),
    [("0", "2"), ("2", "1"), ("1", "21"), ("one", "2")],
)
def test_invalid_connection_pool_bounds_fail_closed(monkeypatch, minimum, maximum):
    monkeypatch.setenv("DB_POOL_MIN", minimum)
    monkeypatch.setenv("DB_POOL_MAX", maximum)

    with pytest.raises(RuntimeError, match="DB_POOL"):
        db_config._pool_bounds()


@pytest.mark.parametrize(
    "sslmode",
    [None, "no", "disable", "allow", "prefer", "require", "verify-ca"],
)
def test_production_database_url_rejects_insecure_tls_modes(monkeypatch, sslmode):
    suffix = "" if sslmode is None else f"?sslmode={sslmode}"
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv(
        "DATABASE_URL",
        f"postgresql://hiresense_app@database.example/hiresense{suffix}",
    )

    with pytest.raises(RuntimeError, match="sslmode"):
        db_config._database_url()


def test_production_database_url_requires_full_certificate_and_hostname_verification(
    monkeypatch,
):
    sslmode = "verify-full"
    database_url = (
        "postgresql://hiresense_app@database.example/hiresense"
        f"?sslmode={sslmode}"
    )
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("DATABASE_URL", database_url)

    assert db_config._database_url() == database_url


def test_production_database_url_requires_runtime_role(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://postgres@database.example/hiresense?sslmode=verify-full",
    )

    with pytest.raises(RuntimeError, match="hiresense_app"):
        db_config._database_url()


class RuntimeIdentityCursor:
    def __init__(self, row):
        self.row = row

    def execute(self, _query):
        pass

    def fetchone(self):
        return self.row

    def close(self):
        pass


class RuntimeIdentityConnection:
    def __init__(self, row):
        self._row = row

    def cursor(self):
        return RuntimeIdentityCursor(self._row)


def test_production_runtime_identity_rejects_bypass_rls():
    connection = RuntimeIdentityConnection(
        ("hiresense_app", True, False, False, False, False, True, False, False)
    )

    with pytest.raises(RuntimeError, match="least-privilege"):
        db_config._verify_runtime_database_identity(connection)


def test_production_runtime_identity_accepts_least_privilege_role():
    connection = RuntimeIdentityConnection(
        ("hiresense_app", True, False, False, False, False, False, False, False)
    )

    db_config._verify_runtime_database_identity(connection)
