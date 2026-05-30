"""Read queries for the coach directory and coach profile (US1).

Coach career totals are STORED fields on ``coaches`` (per clarification); the
endorsement summary (avg rating, count, most-mentioned tags) is DERIVED on read
from ``endorsements`` and never stored. Shaping lives in ``view_models``.
"""
from __future__ import annotations

from typing import Any

from psycopg2.extras import RealDictCursor


def fetch_all_dict(cursor) -> list[dict[str, Any]]:
    return [dict(row) for row in cursor.fetchall()]


def get_coach_directory(conn, q: str | None = None, verified_only: bool = False) -> list[dict[str, Any]]:
    filters: list[str] = []
    params: list[Any] = []
    if q:
        filters.append(
            "(c.display_name ILIKE %s OR c.club_key ILIKE %s "
            "OR EXISTS (SELECT 1 FROM ntvs.coach_positions p2 "
            "WHERE p2.coach_key = c.coach_key AND p2.club_label ILIKE %s))"
        )
        like = f"%{q}%"
        params.extend([like, like, like])
    if verified_only:
        filters.append("c.verified = TRUE")
    where = ("WHERE " + " AND ".join(filters)) if filters else ""
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(
            f"""
            SELECT
                c.coach_key, c.display_name, c.role, c.club_key, c.city,
                c.initials, c.gradient, c.verified, c.wins, c.win_rate, c.commits,
                COALESCE(e.avg_rating, 0) AS rating,
                COALESCE(e.cnt, 0)        AS endorse_count,
                cp.club_label, cp.club_color
            FROM ntvs.coaches c
            LEFT JOIN (
                SELECT coach_key, ROUND(AVG(stars), 1) AS avg_rating, COUNT(*) AS cnt
                FROM ntvs.endorsements
                GROUP BY coach_key
            ) e ON e.coach_key = c.coach_key
            LEFT JOIN LATERAL (
                SELECT club_label, club_color
                FROM ntvs.coach_positions p
                WHERE p.coach_key = c.coach_key
                ORDER BY (p.club_key IS NOT DISTINCT FROM c.club_key) DESC,
                         (p.status = 'verified') DESC, p.position_id
                LIMIT 1
            ) cp ON TRUE
            {where}
            ORDER BY c.verified DESC, rating DESC, c.wins DESC, c.display_name ASC
            """,
            params,
        )
        rows = fetch_all_dict(cursor)
    from .view_models import build_coach_cards

    return build_coach_cards(rows)


def get_coach_profile(conn, coach_key: str) -> dict[str, Any] | None:
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(
            """
            SELECT coach_key, display_name, role, club_key, city, initials, gradient,
                   verified, about, wins, win_rate, commits, gold, seasons,
                   certifications, specialties
            FROM ntvs.coaches
            WHERE coach_key = %s
            """,
            (coach_key,),
        )
        coach_rows = fetch_all_dict(cursor)
    if not coach_rows:
        return None

    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(
            """
            SELECT position_id, club_key, club_label, club_color, role, age_group,
                   years, record, note, status
            FROM ntvs.coach_positions
            WHERE coach_key = %s
            ORDER BY (status = 'verified') DESC, position_id
            """,
            (coach_key,),
        )
        positions = fetch_all_dict(cursor)

    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(
            """
            SELECT endorsement_id, author_label, relationship, stars, tags, body, created_at
            FROM ntvs.endorsements
            WHERE coach_key = %s
            ORDER BY created_at DESC, endorsement_id DESC
            """,
            (coach_key,),
        )
        endorsements = fetch_all_dict(cursor)

    from .view_models import build_coach_profile

    return build_coach_profile(coach_rows[0], positions, endorsements)
