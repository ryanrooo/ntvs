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


def get_club_rankings(conn, q: str | None, sort: str | None, division: str | None, tier: int | None = None) -> list[dict[str, Any]]:
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
        if tier:
            filters.append("ca.tier = %s")
            params.append(int(tier))
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
                ca.tier, ca.color, ca.gold, ca.silver, ca.bronze,
                'Stable' AS trend_label
            FROM ntvs.club_season_summary css
            LEFT JOIN ntvs.club_attributes ca ON ca.club_key = css.club_key
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
                ca.tier AS club_tier,
                ca.color AS club_color,
                ca.gold AS club_gold,
                ca.silver AS club_silver,
                ca.bronze AS club_bronze,
                ca.commits AS club_commits,
                ca.coaches_count AS club_coaches,
                ca.est_year AS club_est,
                ca.about AS club_about,
                p.tournament_id,
                tr.name AS tournament_name,
                mr.match_id,
                mr.pool_id,
                mr.opponent_name,
                mr.outcome,
                mr.score_log
            FROM ntvs.club_team_map ctm
            JOIN ntvs.club_season_summary css ON css.club_key = ctm.club_key
            LEFT JOIN ntvs.club_attributes ca ON ca.club_key = ctm.club_key
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


def get_multi_club_comparison(conn, club_keys: list[str]) -> dict[str, Any]:
    """Assemble a 2–4 club comparison (US5): per-club metrics from
    club_season_summary + club_attributes, plus radar dimensions. Performance
    (rank/win%/teams) stays derived from match data; medals/fee/radar come from
    the NTVS-owned club_attributes. Best-value + radar geometry are shaped in
    view_models.build_multi_comparison."""
    rankings = get_club_rankings(conn, None, "rank", None)
    rank_map = {c["club_key"]: c for c in rankings}
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute("SELECT * FROM ntvs.club_attributes WHERE club_key = ANY(%s)", (list(club_keys),))
        attrs = {a["club_key"]: dict(a) for a in fetch_all_dict(cursor)}

    clubs = []
    for key in club_keys:
        r = rank_map.get(key, {})
        a = attrs.get(key, {})
        clubs.append({
            "club_key": key,
            "display_name": r.get("display_name") or key.replace("-", " ").title(),
            "color": a.get("color") or "#5bb8ff",
            "tier": a.get("tier"),
            "rank": r.get("rank"),
            "win_rate": round(float(r.get("win_rate") or 0), 3),
            "teams": int(r.get("teams_active") or 0),
            "gold": a.get("gold"),
            "silver": a.get("silver"),
            "bronze": a.get("bronze"),
            "coaches": a.get("coaches_count"),
            "commits": a.get("commits"),
            "fee": a.get("fee"),
            "city": None,  # not in the NTVS data model -> neutral placeholder
            "radar": [a.get("radar_win"), a.get("radar_depth"), a.get("radar_gold"), a.get("radar_dev"), a.get("radar_alumni")],
        })

    from .view_models import build_multi_comparison

    return build_multi_comparison(clubs)


def get_home_dashboard(conn) -> dict[str, Any]:
    """Home dashboard (US8): season stats, power rankings (with tier/medals/form),
    upcoming tournaments, featured coaches, and live matchups."""
    rankings = get_club_rankings(conn, None, "rank", None)
    top = rankings[:6]
    keys = [c["club_key"] for c in top]
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(
            "SELECT club_key, tier, color, gold, silver, bronze FROM ntvs.club_attributes WHERE club_key = ANY(%s)",
            (keys,),
        )
        attrs = {a["club_key"]: dict(a) for a in fetch_all_dict(cursor)}
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(
            """
            SELECT
                (SELECT count(*) FROM ntvs.club_season_summary) AS clubs,
                (SELECT count(*) FROM ntvs.teams) AS teams,
                (SELECT count(*) FROM ntvs.coaches) AS coaches,
                (SELECT count(*) FROM ntvs.coaches WHERE verified) AS verified,
                (SELECT count(*) FROM ntvs.match_results) AS matches
            """
        )
        stats = dict(cursor.fetchone())
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(
            """
            SELECT ts.tournament_id, t.name, ts.event_date, ts.venue, ts.city, ts.team_count
            FROM ntvs.tournament_schedule ts
            JOIN ntvs.tournaments t ON t.tournament_id = ts.tournament_id
            WHERE ts.completed = FALSE
            ORDER BY ts.event_date ASC, t.name ASC
            LIMIT 5
            """
        )
        upcoming = fetch_all_dict(cursor)
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(
            """
            SELECT c.coach_key, c.display_name, c.role, c.club_key, c.initials, c.gradient,
                   c.verified, c.wins, c.win_rate, c.commits,
                   COALESCE(e.avg_rating, 0) AS rating, COALESCE(e.cnt, 0) AS endorse_count,
                   cp.club_label, cp.club_color
            FROM ntvs.coaches c
            LEFT JOIN (SELECT coach_key, ROUND(AVG(stars), 1) AS avg_rating, COUNT(*) AS cnt
                       FROM ntvs.endorsements GROUP BY coach_key) e ON e.coach_key = c.coach_key
            LEFT JOIN LATERAL (SELECT club_label, club_color FROM ntvs.coach_positions p
                               WHERE p.coach_key = c.coach_key
                               ORDER BY (p.status = 'verified') DESC, p.position_id LIMIT 1) cp ON TRUE
            WHERE c.verified
            ORDER BY e.avg_rating DESC NULLS LAST, c.wins DESC
            LIMIT 3
            """
        )
        coaches = fetch_all_dict(cursor)
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(
            """
            SELECT mr.team_name, mr.opponent_name, mr.outcome, mr.score_log
            FROM ntvs.match_results mr
            WHERE mr.outcome IS NOT NULL AND mr.score_log IS NOT NULL
            ORDER BY mr.match_id DESC
            LIMIT 4
            """
        )
        matchups = fetch_all_dict(cursor)

    from .view_models import build_home_dashboard

    return build_home_dashboard(top, attrs, stats, upcoming, coaches, matchups)
