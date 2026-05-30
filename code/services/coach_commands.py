"""Idempotent write commands for the coach hub (US2+).

Every write goes through ``db.write_conn`` (commits on success, rolls back on
error) and dedupes on a natural key so retries can't create duplicates or drift
counts (FR-031, SC-008). Summary numbers (avg rating, counts) are always derived
on read — never incremented here.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

from psycopg2.extras import RealDictCursor

from . import db
from .club_normalization import slugify_club_name


def _body_hash(body: str) -> str:
    return hashlib.md5(body.strip().lower().encode("utf-8")).hexdigest()


def _recompute_coach_verified(cur, coach_key) -> None:
    """coaches.verified is a cache of 'has >=1 verified position' — never the source of truth."""
    cur.execute(
        """
        UPDATE ntvs.coaches
        SET verified = EXISTS (
            SELECT 1 FROM ntvs.coach_positions WHERE coach_key = %s AND status = 'verified'
        )
        WHERE coach_key = %s
        """,
        (coach_key, coach_key),
    )


def _resolve_club(cur, club_label: str):
    """Best-effort link of a free-text club label to a canonical club_key (+ brand color)."""
    slug = slugify_club_name(club_label)
    cur.execute("SELECT club_key, color FROM ntvs.club_attributes WHERE club_key = %s", (slug,))
    row = cur.fetchone()
    if row:
        return slug, row.get("color")
    cur.execute("SELECT 1 FROM ntvs.club_season_summary WHERE club_key = %s LIMIT 1", (slug,))
    if cur.fetchone():
        return slug, None
    return None, None


def add_endorsement(coach_key, author_label, relationship, stars, tags, body) -> dict[str, Any] | None:
    """Insert a (pre-validated) endorsement, deduping on
    (coach_key, author_label, body_hash, created_date).

    Returns ``{"endorsement": <shaped>, "applied": bool}`` where ``applied`` is
    False when an identical same-day endorsement already existed (no-op), or
    ``None`` when the coach does not exist.
    """
    body = (body or "").strip()
    body_hash = _body_hash(body)
    today = datetime.now(timezone.utc).date()
    with db.write_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT 1 FROM ntvs.coaches WHERE coach_key = %s", (coach_key,))
            if cur.fetchone() is None:
                return None
            cur.execute(
                """
                INSERT INTO ntvs.endorsements
                    (coach_key, author_label, relationship, stars, tags, body, created_date, body_hash)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (coach_key, author_label, body_hash, created_date) DO NOTHING
                RETURNING endorsement_id, author_label, relationship, stars, tags, body, created_at
                """,
                (coach_key, author_label, relationship, int(stars), list(tags or []), body, today, body_hash),
            )
            row = cur.fetchone()
            applied = row is not None
            if row is None:  # dedupe hit — return the existing row
                cur.execute(
                    """
                    SELECT endorsement_id, author_label, relationship, stars, tags, body, created_at
                    FROM ntvs.endorsements
                    WHERE coach_key = %s AND author_label = %s AND body_hash = %s AND created_date = %s
                    """,
                    (coach_key, author_label, body_hash, today),
                )
                row = cur.fetchone()
    from .view_models import _format_endorsement

    return {"endorsement": _format_endorsement(dict(row)), "applied": applied}


def add_position(coach_key, club_label, role, age_group=None, years=None, note=None) -> dict | None:
    """Add a pending coaching position; dedupe on (coach_key, club_label, role, years).

    Returns ``{"position": <shaped>, "applied": bool}`` or None if the coach is missing.
    """
    club_label = (club_label or "").strip()
    role = (role or "").strip()
    with db.write_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT 1 FROM ntvs.coaches WHERE coach_key = %s", (coach_key,))
            if cur.fetchone() is None:
                return None
            club_key, club_color = _resolve_club(cur, club_label)
            cur.execute(
                """
                INSERT INTO ntvs.coach_positions
                    (coach_key, club_key, club_label, club_color, role, age_group, years, note, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'pending')
                ON CONFLICT (coach_key, club_label, role, COALESCE(years, '')) DO NOTHING
                RETURNING position_id, club_key, club_label, club_color, role, age_group, years, record, note, status
                """,
                (coach_key, club_key, club_label, club_color, role, age_group or None, years or None, note or None),
            )
            row = cur.fetchone()
            applied = row is not None
            if row is None:  # dedupe hit
                cur.execute(
                    """
                    SELECT position_id, club_key, club_label, club_color, role, age_group, years, record, note, status
                    FROM ntvs.coach_positions
                    WHERE coach_key = %s AND club_label = %s AND role = %s AND COALESCE(years, '') = COALESCE(%s, '')
                    """,
                    (coach_key, club_label, role, years or None),
                )
                row = cur.fetchone()
    from .view_models import _build_position

    return {"position": _build_position(dict(row)), "applied": applied}


def delete_position(coach_key, position_id) -> dict:
    """Remove a position only while not verified. Idempotent if already absent.

    Returns {"removed": bool, "reason": "deleted"|"absent"|"verified"}.
    """
    with db.write_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT status FROM ntvs.coach_positions WHERE coach_key = %s AND position_id = %s",
                (coach_key, position_id),
            )
            row = cur.fetchone()
            if row is None:
                return {"removed": True, "reason": "absent"}
            if row["status"] == "verified":
                return {"removed": False, "reason": "verified"}
            cur.execute(
                "DELETE FROM ntvs.coach_positions WHERE coach_key = %s AND position_id = %s",
                (coach_key, position_id),
            )
            _recompute_coach_verified(cur, coach_key)
    return {"removed": True, "reason": "deleted"}


def create_verification_request(coach_key, club_key, position_id=None, note=None) -> dict | None:
    """Create a pending verification request for a claimed club affiliation.

    Returns ``{"request_id", "status", "applied"}`` (applied False if an identical
    pending request already exists) or None if the coach is missing. The
    match_strength/match_pct are a heuristic snapshot, not derived from match data.
    """
    with db.write_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT display_name, initials FROM ntvs.coaches WHERE coach_key = %s", (coach_key,))
            coach = cur.fetchone()
            if coach is None:
                return None
            cur.execute(
                "SELECT request_id FROM ntvs.verification_requests "
                "WHERE coach_key = %s AND club_key = %s AND status = 'pending' LIMIT 1",
                (coach_key, club_key),
            )
            existing = cur.fetchone()
            if existing:
                return {"request_id": existing["request_id"], "status": "pending", "applied": False}

            role = claim_years = color = None
            match_strength, match_pct = "Partial", 60
            if position_id:
                cur.execute(
                    "SELECT role, age_group, years, club_key, club_color FROM ntvs.coach_positions "
                    "WHERE position_id = %s AND coach_key = %s",
                    (position_id, coach_key),
                )
                p = cur.fetchone()
                if p:
                    role = (p["role"] or "") + (" · " + p["age_group"] if p.get("age_group") else "")
                    claim_years = p.get("years")
                    color = p.get("club_color")
                    if p.get("club_key") == club_key:  # claim links to a canonical club -> stronger signal
                        match_strength, match_pct = "Strong", 85
            cur.execute(
                """
                INSERT INTO ntvs.verification_requests
                    (coach_key, club_key, position_id, name, initials, color, role, claim_years, match_strength, match_pct, note)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING request_id, status
                """,
                (coach_key, club_key, position_id, coach["display_name"], coach.get("initials"),
                 color, role, claim_years, match_strength, match_pct, note or None),
            )
            row = cur.fetchone()
    return {"request_id": row["request_id"], "status": row["status"], "applied": True}
