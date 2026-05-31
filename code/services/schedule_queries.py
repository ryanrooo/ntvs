"""Read queries for the tournament schedule (US6) and results (US7).

Schedule attributes come from the NTVS-owned ``tournament_schedule`` table;
results reuse the existing scraped bracket/standings/match tables plus
``stat_leaders``. Shaping (month grouping, calendar grid, map points, bracket
rounds) lives in ``view_models``.
"""
from __future__ import annotations

from typing import Any

from psycopg2.extras import RealDictCursor


def fetch_all_dict(cursor) -> list[dict[str, Any]]:
    return [dict(row) for row in cursor.fetchall()]


def get_schedule(conn, open_only: bool = False, month: str | None = None, within_mi: int | None = None) -> dict[str, Any]:
    filters = ["TRUE"]
    params: list[Any] = []
    if open_only:
        filters.append("ts.status = 'Open'")
    if month:
        filters.append("ts.month_key = %s")
        params.append(month)
    if within_mi:
        filters.append("ts.within_mi <= %s")
        params.append(int(within_mi))
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(
            f"""
            SELECT ts.tournament_id, t.name, ts.event_date, ts.month_key, ts.venue, ts.city,
                   ts.team_count, ts.age_lo, ts.age_hi, ts.division, ts.status, ts.within_mi,
                   ts.featured, ts.completed
            FROM ntvs.tournament_schedule ts
            JOIN ntvs.tournaments t ON t.tournament_id = ts.tournament_id
            WHERE {' AND '.join(filters)}
            ORDER BY ts.event_date ASC, t.name ASC
            """,
            params,
        )
        rows = fetch_all_dict(cursor)
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute("SELECT DISTINCT month_key FROM ntvs.tournament_schedule WHERE month_key IS NOT NULL ORDER BY month_key")
        all_months = [r["month_key"] for r in fetch_all_dict(cursor)]
    from .view_models import build_schedule

    return build_schedule(rows, {"open_only": open_only, "month": month or "", "within_mi": within_mi or ""}, all_months)


def get_results(conn, tournament_id: str) -> dict[str, Any] | None:
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute("SELECT tournament_id, name FROM ntvs.tournaments WHERE tournament_id = %s", (tournament_id,))
        tournament = cursor.fetchone()
    if tournament is None:
        return None

    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(
            """
            SELECT bp.placement, bp.team_name, bp.division, bp.bracket_tier,
                   ctm.club_key, ctm.display_name AS club_name
            FROM ntvs.bracket_placements bp
            LEFT JOIN ntvs.club_team_map ctm ON ctm.team_name = bp.team_name
            WHERE bp.tournament_id = %s
            ORDER BY bp.placement ASC
            """,
            (tournament_id,),
        )
        placements = fetch_all_dict(cursor)

    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(
            """
            SELECT match_id, division, bracket_tier, round_label, team_name, opponent_name, outcome, score_log
            FROM ntvs.bracket_matches
            WHERE tournament_id = %s
            ORDER BY bracket_tier, round_label, match_id
            """,
            (tournament_id,),
        )
        bracket = fetch_all_dict(cursor)

    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(
            """
            SELECT ps.team_name, ps.rank_seed, ps.matches_won, ps.matches_lost, ps.point_diff, ps.pool_finish, p.division
            FROM ntvs.pool_standings ps
            JOIN ntvs.pools p ON p.pool_id = ps.pool_id
            WHERE p.tournament_id = %s
            ORDER BY p.division, ps.rank_seed NULLS LAST, ps.matches_won DESC
            """,
            (tournament_id,),
        )
        standings = fetch_all_dict(cursor)

    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(
            """
            SELECT category, rank, player_name, club_label, value
            FROM ntvs.stat_leaders
            WHERE tournament_id = %s
            ORDER BY category, rank
            """,
            (tournament_id,),
        )
        leaders = fetch_all_dict(cursor)

    from .view_models import build_results

    return build_results(dict(tournament), placements, bracket, standings, leaders)
