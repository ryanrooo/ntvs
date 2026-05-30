"""Pooled, transactional database access (Production Readiness PR-1).

A single ``ThreadedConnectionPool`` plus two context managers:

* ``read_conn()``  — borrow a connection, roll back on exit (reads never persist).
* ``write_conn()`` — borrow a connection, COMMIT on success, ROLL BACK on error.

The previous ``psycopg2.connect`` per request never committed, so writes were
silently rolled back on ``close()``. Routing all access through this module
fixes that and bounds the number of open connections.

Connection params come from ``DATABASE_URL`` when set (e.g. on Fly.io), else from
the existing ``DB_HOST`` / ``DB_NAME`` / ``DB_USER`` / ``DB_PASSWORD`` (+ optional
``DB_PORT``) variables the app already uses.
"""
from __future__ import annotations

import os
import threading
from contextlib import contextmanager
from typing import Iterator

from psycopg2.pool import ThreadedConnectionPool

_pool: ThreadedConnectionPool | None = None
_lock = threading.Lock()


def _connect_kwargs() -> dict:
    url = os.getenv("DATABASE_URL")
    if url:
        return {"dsn": url}
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": os.getenv("DB_PORT", "5432"),
        "dbname": os.getenv("DB_NAME", "postgres"),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
    }


def get_pool() -> ThreadedConnectionPool:
    """Lazily build (once) and return the shared connection pool."""
    global _pool
    if _pool is None:
        with _lock:
            if _pool is None:
                minconn = int(os.getenv("DB_POOL_MIN", "1"))
                maxconn = int(os.getenv("DB_POOL_MAX", "10"))
                _pool = ThreadedConnectionPool(minconn, maxconn, **_connect_kwargs())
    return _pool


@contextmanager
def read_conn() -> Iterator:
    """Borrow a pooled connection for reads; never commits."""
    pool = get_pool()
    conn = pool.getconn()
    try:
        yield conn
        conn.rollback()  # release the read snapshot / any implicit transaction
    except Exception:
        conn.rollback()
        raise
    finally:
        pool.putconn(conn)


@contextmanager
def write_conn() -> Iterator:
    """Borrow a pooled connection for writes; COMMIT on success, ROLLBACK on error."""
    pool = get_pool()
    conn = pool.getconn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        pool.putconn(conn)


def close_pool() -> None:
    """Close all pooled connections (useful in tests / shutdown)."""
    global _pool
    if _pool is not None:
        _pool.closeall()
        _pool = None
