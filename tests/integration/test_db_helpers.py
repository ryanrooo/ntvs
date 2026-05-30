"""PR-1: write_conn commits, errors roll back, and the pool reuses connections.

Requires a reachable Postgres (env: DATABASE_URL or DB_HOST/DB_NAME/DB_USER/
DB_PASSWORD[/DB_PORT]). Skips cleanly when no database is available so the rest
of the suite stays green in environments without one.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "code"))

from services import db


def _db_available() -> bool:
    try:
        with db.read_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
        return True
    except Exception:
        db.close_pool()
        return False


pytestmark = pytest.mark.skipif(not _db_available(), reason="no database available")

TABLE = "tmp_ntvs_db_helpers_test"


def _reset_table():
    with db.write_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(f"CREATE TABLE IF NOT EXISTS {TABLE} (id INT)")
            cur.execute(f"TRUNCATE {TABLE}")


def test_write_conn_commits_on_success():
    _reset_table()
    with db.write_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(f"INSERT INTO {TABLE} (id) VALUES (1)")
    with db.read_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(f"SELECT COUNT(*) FROM {TABLE}")
            assert cur.fetchone()[0] == 1


def test_write_conn_rolls_back_on_error():
    _reset_table()
    with pytest.raises(RuntimeError):
        with db.write_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(f"INSERT INTO {TABLE} (id) VALUES (2)")
            raise RuntimeError("boom")
    with db.read_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(f"SELECT COUNT(*) FROM {TABLE}")
            assert cur.fetchone()[0] == 0


def test_pool_reuses_connection():
    db.get_pool()
    with db.read_conn() as conn:
        first = id(conn)
    with db.read_conn() as conn:
        second = id(conn)
    assert first == second
