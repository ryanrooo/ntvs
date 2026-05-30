"""Endorsement write idempotency (FR-031, SC-008) against a real Postgres.

Skips when no database is reachable. Uses a seeded coach plus a unique author
label, and cleans up after itself so reruns stay green.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "code"))

from services import coach_commands, db


def _db_available() -> bool:
    try:
        with db.read_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM ntvs.coaches LIMIT 1")
        return True
    except Exception:
        db.close_pool()
        return False


pytestmark = pytest.mark.skipif(not _db_available(), reason="no database / coach data available")

COACH = "devon-brooks"            # seeded
AUTHOR = "PYTEST Endorser"
BODY = "Fantastic energy and the athletes improved a lot this season."


def _cleanup():
    with db.write_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM ntvs.endorsements WHERE coach_key = %s AND author_label = %s",
                (COACH, AUTHOR),
            )


def _count():
    with db.read_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT count(*) FROM ntvs.endorsements WHERE coach_key = %s AND author_label = %s",
                (COACH, AUTHOR),
            )
            return cur.fetchone()[0]


def test_add_endorsement_dedupes_same_day_submit():
    _cleanup()
    try:
        first = coach_commands.add_endorsement(COACH, AUTHOR, "Parent", 5, ["Development"], BODY)
        assert first is not None and first["applied"] is True

        again = coach_commands.add_endorsement(COACH, AUTHOR, "Parent", 5, ["Development"], BODY)
        assert again["applied"] is False                    # idempotent no-op
        assert again["endorsement"]["body"] == BODY

        assert _count() == 1                                 # exactly one row persisted
    finally:
        _cleanup()


def test_add_endorsement_unknown_coach_returns_none():
    assert coach_commands.add_endorsement("nobody-xyz", AUTHOR, "Parent", 5, [], BODY) is None


# ── US3: positions + verification requests ─────────────────────────────────

PCLUB = "Pytest FC"


def _cleanup_positions():
    with db.write_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM ntvs.coach_positions WHERE coach_key = %s AND club_label = %s", (COACH, PCLUB))


def test_add_position_dedupes_on_natural_key():
    _cleanup_positions()
    try:
        first = coach_commands.add_position(COACH, PCLUB, "Assistant", "15-16", "2020-2022")
        assert first is not None and first["applied"] is True and first["position"]["status"] == "pending"
        again = coach_commands.add_position(COACH, PCLUB, "Assistant", "15-16", "2020-2022")
        assert again["applied"] is False
        assert again["position"]["position_id"] == first["position"]["position_id"]
    finally:
        _cleanup_positions()


def test_delete_position_idempotent_and_blocks_verified():
    _cleanup_positions()
    try:
        pid = coach_commands.add_position(COACH, PCLUB, "Assistant", "15-16", "2020-2022")["position"]["position_id"]
        assert coach_commands.delete_position(COACH, pid) == {"removed": True, "reason": "deleted"}
        assert coach_commands.delete_position(COACH, pid)["removed"] is True  # idempotent (absent)

        pid2 = coach_commands.add_position(COACH, PCLUB, "Head Coach", "17", "2021-2023")["position"]["position_id"]
        with db.write_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE ntvs.coach_positions SET status='verified' WHERE position_id = %s", (pid2,))
        assert coach_commands.delete_position(COACH, pid2) == {"removed": False, "reason": "verified"}
    finally:
        _cleanup_positions()


def test_create_verification_request_dedupes_pending():
    club = "pytest-fc"

    def _cleanup_req():
        with db.write_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM ntvs.verification_requests WHERE coach_key = %s AND club_key = %s", (COACH, club))

    _cleanup_req()
    try:
        first = coach_commands.create_verification_request(COACH, club, note="please confirm")
        assert first is not None and first["applied"] is True and first["status"] == "pending"
        again = coach_commands.create_verification_request(COACH, club, note="please confirm")
        assert again["applied"] is False and again["request_id"] == first["request_id"]
    finally:
        _cleanup_req()
