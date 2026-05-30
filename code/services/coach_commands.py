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


def _body_hash(body: str) -> str:
    return hashlib.md5(body.strip().lower().encode("utf-8")).hexdigest()


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
