from __future__ import annotations

from typing import Any

from psycopg2.extras import RealDictCursor


def fetch_all_dict(cursor) -> list[dict[str, Any]]:
    return [dict(row) for row in cursor.fetchall()]


def get_tournaments(conn) -> list[dict[str, Any]]:
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(
            """
            SELECT tournament_id, name
            FROM ntvs.tournaments
            ORDER BY tournament_id DESC, name ASC
            """
        )
        return fetch_all_dict(cursor)


def get_homepage_data(conn, tournament_id: str | None = None) -> dict[str, Any]:
    tournaments = get_tournaments(conn)
    selected = tournament_id or (tournaments[0]["tournament_id"] if tournaments else None)
    pools = get_pool_results(conn, selected, None, None, None)["pools"] if selected else []
    clubs = get_club_rankings(conn, None, "rank", None)[:5]
    featured_matchups = []
    if pools:
        for pool in pools[:2]:
            featured_matchups.extend(pool.get("matchups", [])[:2])
    featured_tournament = next((t for t in tournaments if t["tournament_id"] == selected), None)
    return {
        "featured_tournament": featured_tournament,
        "featured_pools": [{"pool_id": p["pool_id"], "pool_name": p["pool_name"], "division": p["division"], "tournament_id": p["tournament_id"]} for p in pools[:3]],
        "featured_clubs": clubs,
        "featured_matchups": featured_matchups[:4],
        "tournaments": tournaments,
    }


def get_pool_results(conn, tournament_id: str | None, age_group: str | None, division: str | None, club_name: str | None) -> dict[str, Any]:
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        filters = []
        params: list[Any] = []
        if tournament_id:
            filters.append("p.tournament_id = %s")
            params.append(tournament_id)
        if division:
            filters.append("p.division ILIKE %s")
            params.append(f"%{division}%")
        if club_name:
            filters.append("(ctm.display_name ILIKE %s OR ctm.source_club_name ILIKE %s)")
            params.append(f"%{club_name}%")
            params.append(f"%{club_name}%")
        query = f"""
            SELECT
                p.pool_id,
                p.pool_name,
                p.division,
                p.tournament_id,
                ps.rank_seed,
                ps.matches_won,
                ps.matches_lost,
                ps.point_diff,
                ps.pool_finish,
                ps.team_name,
                ctm.club_key,
                ctm.display_name,
                ctm.source_club_name,
                ctm.normalization_status,
                ctm.base_slug,
                ctm.collision_rank,
                CONCAT(COALESCE(m.sets_won, 0), '-', COALESCE(m.sets_lost, 0)) AS sets_record,
                m.match_id,
                m.team_name AS match_team_name,
                m.opponent_name,
                m.outcome,
                m.score_log
            FROM ntvs.pools p
            LEFT JOIN ntvs.pool_standings ps ON ps.pool_id = p.pool_id
            LEFT JOIN ntvs.club_team_map ctm ON ctm.team_name = ps.team_name
            LEFT JOIN ntvs.match_results m ON m.pool_id = p.pool_id AND m.team_name = ps.team_name
            {"WHERE " + " AND ".join(filters) if filters else ""}
            ORDER BY p.tournament_id DESC, p.division, p.pool_name, ps.rank_seed NULLS LAST
        """
        cursor.execute(query, params)
        rows = fetch_all_dict(cursor)
    if age_group:
        rows = [row for row in rows if age_group.lower() in (row.get("division") or "").lower()]
    from .view_models import build_pool_detail_rows, serialize_data_state

    pools = build_pool_detail_rows(rows)
    return {"filters": {"tournament_id": tournament_id or "", "age_group": age_group or "", "division": division or "", "club_name": club_name or ""}, "pools": pools, "data_state": serialize_data_state(pools)}


def get_club_rankings(conn, q: str | None, sort: str | None, division: str | None) -> list[dict[str, Any]]:
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        filters = []
        params: list[Any] = []
        if q:
            filters.append("(css.display_name ILIKE %s OR css.source_club_name ILIKE %s OR css.club_key ILIKE %s)")
            params.append(f"%{q}%")
            params.append(f"%{q}%")
            params.append(f"%{q}%")
        if division:
            filters.append(
                """
                EXISTS (
                    SELECT 1
                    FROM ntvs.club_team_map division_map
                    WHERE division_map.club_key = css.club_key
                      AND division_map.division ILIKE %s
                )
                """
            )
            params.append(f"%{division}%")
        query = f"""
            SELECT
                css.club_key,
                css.display_name,
                css.source_club_name,
                css.normalization_status,
                css.teams_active,
                css.matches_won,
                css.matches_lost,
                css.sets_won,
                css.sets_lost,
                css.point_diff_total,
                CASE
                    WHEN COALESCE(css.matches_won + css.matches_lost, 0) = 0 THEN 0
                    ELSE ROUND(
                        css.matches_won::numeric / NULLIF(css.matches_won + css.matches_lost, 0),
                        3
                    )
                END AS win_rate,
                css.ranking_score,
                'Stable' AS trend_label
            FROM ntvs.club_season_summary css
            {"WHERE " + " AND ".join(filters) if filters else ""}
            ORDER BY
                {"css.teams_active DESC, css.display_name ASC" if sort == "teams" else "win_rate DESC, css.ranking_score DESC, css.display_name ASC" if sort == "win_rate" else "css.ranking_score DESC, win_rate DESC, css.display_name ASC"}
        """
        cursor.execute(query, params)
        rows = fetch_all_dict(cursor)
    from .view_models import build_club_rankings
    return build_club_rankings(rows)


def get_club_profile(conn, club_key: str) -> dict[str, Any]:
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(
            """
            SELECT
                ctm.club_key,
                ctm.display_name,
                ctm.source_club_name,
                ctm.normalization_status,
                ctm.base_slug,
                ctm.collision_rank,
                ctm.team_name,
                ctm.division,
                COALESCE(team_stats.matches_won, 0) AS matches_won,
                COALESCE(team_stats.matches_lost, 0) AS matches_lost,
                COALESCE(team_stats.point_diff_total, 0) AS point_diff_total,
                css.teams_active,
                CASE
                    WHEN COALESCE(css.matches_won + css.matches_lost, 0) = 0 THEN 0
                    ELSE ROUND(
                        css.matches_won::numeric / NULLIF(css.matches_won + css.matches_lost, 0),
                        3
                    )
                END AS win_rate,
                css.ranking_score,
                css.latest_activity_date,
                p.tournament_id,
                tr.name AS tournament_name,
                mr.match_id,
                mr.pool_id,
                mr.opponent_name,
                mr.outcome,
                mr.score_log
            FROM ntvs.club_team_map ctm
            JOIN ntvs.club_season_summary css ON css.club_key = ctm.club_key
            LEFT JOIN (
                SELECT
                    team_name,
                    COALESCE(SUM(CASE WHEN outcome = 'Won' THEN 1 ELSE 0 END), 0) AS matches_won,
                    COALESCE(SUM(CASE WHEN outcome = 'Lost' THEN 1 ELSE 0 END), 0) AS matches_lost,
                    COALESCE(SUM(point_diff), 0) AS point_diff_total
                FROM (
                    SELECT mr.team_name, mr.outcome, 0::integer AS point_diff
                    FROM ntvs.match_results mr
                    UNION ALL
                    SELECT ps.team_name, NULL::varchar AS outcome, COALESCE(ps.point_diff, 0) AS point_diff
                    FROM ntvs.pool_standings ps
                ) AS combined_stats
                GROUP BY team_name
            ) AS team_stats ON team_stats.team_name = ctm.team_name
            LEFT JOIN ntvs.match_results mr ON mr.team_name = ctm.team_name
            LEFT JOIN ntvs.pools p ON p.pool_id = mr.pool_id
            LEFT JOIN ntvs.tournaments tr ON tr.tournament_id = p.tournament_id
            WHERE ctm.club_key = %s
            ORDER BY p.tournament_id DESC NULLS LAST, ctm.team_name ASC
            """,
            (club_key,),
        )
        rows = fetch_all_dict(cursor)

    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(
            """
            SELECT bm.match_id, bm.tournament_id, bm.division, bm.bracket_tier,
                   bm.round_label, bm.team_name, bm.opponent_name, bm.outcome, bm.score_log,
                   tr.name AS tournament_name
            FROM ntvs.bracket_matches bm
            JOIN ntvs.club_team_map ctm ON ctm.team_name = bm.team_name
            LEFT JOIN ntvs.tournaments tr ON tr.tournament_id = bm.tournament_id
            WHERE ctm.club_key = %s
            ORDER BY bm.tournament_id DESC, bm.team_name, bm.round_label
            """,
            (club_key,),
        )
        bracket_rows = fetch_all_dict(cursor)

    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(
            """
            SELECT bp.tournament_id, bp.division, bp.bracket_tier, bp.team_name, bp.placement,
                   tr.name AS tournament_name
            FROM ntvs.bracket_placements bp
            JOIN ntvs.club_team_map ctm ON ctm.team_name = bp.team_name
            LEFT JOIN ntvs.tournaments tr ON tr.tournament_id = bp.tournament_id
            WHERE ctm.club_key = %s
            ORDER BY bp.tournament_id DESC, bp.division
            """,
            (club_key,),
        )
        placement_rows = fetch_all_dict(cursor)

    from .view_models import build_club_profile
    return build_club_profile(club_key, rows, bracket_rows, placement_rows)


def get_club_comparison(conn, club_a: str, club_b: str) -> dict[str, Any]:
    profile_a = get_club_profile(conn, club_a)
    profile_b = get_club_profile(conn, club_b)
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(
            """
            SELECT mr.match_id, p.tournament_id, mr.pool_id, mr.team_name, mr.opponent_name, mr.outcome, mr.score_log
            FROM ntvs.match_results mr
            JOIN ntvs.club_team_map t1 ON t1.team_name = mr.team_name
            JOIN ntvs.club_team_map t2 ON t2.team_name = mr.opponent_name
            LEFT JOIN ntvs.pools p ON p.pool_id = mr.pool_id
            WHERE t1.club_key = %s
              AND t2.club_key = %s
            ORDER BY p.tournament_id DESC NULLS LAST, mr.match_id
            """,
            (club_a, club_b),
        )
        rows = fetch_all_dict(cursor)
    from .view_models import build_comparison_metrics, build_head_to_head, serialize_data_state

    return {
        "club_a": profile_a["club"],
        "club_b": profile_b["club"],
        "comparison_metrics": build_comparison_metrics(profile_a["club"], profile_b["club"]),
        "head_to_head": build_head_to_head(rows, club_a, club_b),
        "shared_matchups": rows,
        "data_state": serialize_data_state(rows, partial=not bool(rows), message="No direct head-to-head history is available." if not rows else "Comparison loaded successfully."),
    }
