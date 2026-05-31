import calendar as _calendar
import math
import re
from collections import Counter, defaultdict
from datetime import date
from typing import Any

from .club_normalization import normalize_club_name


def serialize_data_state(items: list[Any], partial: bool = False, message: str | None = None) -> dict[str, str]:
    if partial:
        return {"completeness": "partial", "message": message or "Some analytics are unavailable for this selection."}
    if not items:
        return {"completeness": "empty", "message": message or "No matching data is available."}
    return {"completeness": "complete", "message": message or "Data loaded successfully."}


def build_pool_detail_rows(rows: list[dict]) -> list[dict]:
    pools: dict[str, dict] = {}
    for row in rows:
        pool = pools.setdefault(
            row["pool_id"],
            {
                "pool_id": row["pool_id"],
                "pool_name": row["pool_name"],
                "division": row["division"],
                "tournament_id": row["tournament_id"],
                "standings": [],
                "matchups": [],
            },
        )
        if row.get("team_name"):
            identity = _identity_from_row(row)
            pool["standings"].append(
                {
                    "rank": row.get("rank_seed"),
                    "team_name": row["team_name"],
                    "club_key": identity.club_key,
                    "display_name": identity.display_name,
                    "source_club_name": identity.source_club_name,
                    "normalization_status": identity.normalization_status,
                    "matches_record": f"{row.get('matches_won', 0)}-{row.get('matches_lost', 0)}",
                    "sets_record": row.get("sets_record", "N/A"),
                    "point_diff": row.get("point_diff", 0),
                    "status_label": _status_label(row),
                }
            )
        if row.get("match_id"):
            pool["matchups"].append(
                {
                    "match_id": row["match_id"],
                    "tournament_id": row["tournament_id"],
                    "pool_id": row["pool_id"],
                    "team_name": row["match_team_name"],
                    "opponent_name": row["opponent_name"],
                    "outcome": row["outcome"],
                    "score_log": row.get("score_log") or "",
                }
            )
    for pool in pools.values():
        pool["standings"].sort(key=lambda item: (item["rank"] is None, item["rank"]))
        deduped: dict[tuple[str, str], dict] = {}
        for matchup in pool["matchups"]:
            key = (matchup["match_id"], matchup["team_name"])
            deduped[key] = matchup
        pool["matchups"] = list(deduped.values())
    return list(pools.values())


def _status_label(row: dict) -> str:
    finish = row.get("pool_finish")
    if finish == 1:
        return "Clinched 1st"
    if finish == 2:
        return "Advanced"
    if finish:
        return f"Finished {finish}"
    return "In progress"


def build_club_rankings(rows: list[dict]) -> list[dict]:
    clubs = []
    for index, row in enumerate(rows, start=1):
        identity = _identity_from_row(row)
        clubs.append(
            {
                "club_key": identity.club_key,
                "display_name": identity.display_name,
                "source_club_name": identity.source_club_name,
                "normalization_status": identity.normalization_status,
                "rank": index,
                "teams_active": row.get("teams_active", 0),
                "win_rate": round(float(row.get("win_rate") or 0), 3),
                "trend_label": row.get("trend_label") or "Stable",
                "ranking_score": row.get("ranking_score", 0),
            }
        )
    return clubs


def build_club_profile(
    club_key: str,
    rows: list[dict],
    bracket_rows: list[dict] | None = None,
    placement_rows: list[dict] | None = None,
) -> dict:
    bracket_rows = bracket_rows or []
    placement_rows = placement_rows or []

    if not rows and not bracket_rows and not placement_rows:
        identity = normalize_club_name(club_key.replace("-", " ").title(), club_key=club_key)
        return {
            "club": {
                "club_key": identity.club_key, "display_name": identity.display_name,
                "source_club_name": identity.source_club_name,
                "normalization_status": identity.normalization_status,
                "teams_active": 0, "win_rate": 0, "ranking_score": 0, "latest_activity_date": None,
            },
            "teams": [], "team_seasons": {}, "placements": [], "champions": [],
            "recent_tournaments": [], "recent_matchups": [], "recent_bracket_matchups": [],
        }

    first = (rows or bracket_rows or placement_rows)[0]
    identity = _identity_from_row(first)

    # Build per-team season structure
    team_seasons: dict[str, dict] = {}

    for row in rows:
        tn = row["team_name"]
        if tn not in team_seasons:
            team_seasons[tn] = {
                "team_name": tn, "division": row.get("division") or "",
                "matches_won": row.get("matches_won", 0), "matches_lost": row.get("matches_lost", 0),
                "tournaments": {},
            }
        tid = row.get("tournament_id")
        if not tid:
            continue
        tourney = team_seasons[tn]["tournaments"].setdefault(tid, {
            "tournament_id": tid, "tournament_name": row.get("tournament_name") or tid,
            "pool_matches": {}, "bracket_matches": [], "bracket_placement": None, "bracket_tier": None,
        })
        if row.get("match_id"):
            tourney["pool_matches"][row["match_id"]] = {
                "match_id": row["match_id"], "opponent_name": row.get("opponent_name"),
                "outcome": row.get("outcome"), "score_log": row.get("score_log") or "",
            }

    for brow in bracket_rows:
        tn = brow["team_name"]
        tid = brow.get("tournament_id")
        if not tid:
            continue
        if tn not in team_seasons:
            team_seasons[tn] = {
                "team_name": tn, "division": brow.get("division") or "",
                "matches_won": 0, "matches_lost": 0, "tournaments": {},
            }
        tourney = team_seasons[tn]["tournaments"].setdefault(tid, {
            "tournament_id": tid, "tournament_name": brow.get("tournament_name") or tid,
            "pool_matches": {}, "bracket_matches": [], "bracket_placement": None,
            "bracket_tier": brow.get("bracket_tier"),
        })
        if not tourney["bracket_tier"]:
            tourney["bracket_tier"] = brow.get("bracket_tier")
        tourney["bracket_matches"].append({
            "match_id": brow["match_id"], "bracket_tier": brow.get("bracket_tier"),
            "round_label": brow.get("round_label"), "opponent_name": brow.get("opponent_name"),
            "outcome": brow.get("outcome"), "score_log": brow.get("score_log") or "",
        })

    for prow in placement_rows:
        tn, tid = prow["team_name"], prow.get("tournament_id")
        if tid and tn in team_seasons and tid in team_seasons[tn]["tournaments"]:
            team_seasons[tn]["tournaments"][tid]["bracket_placement"] = prow.get("placement")

    # Finalise: convert tournament dicts to sorted lists
    teams_list = []
    for tn, ts in team_seasons.items():
        sorted_tourneys = sorted(ts["tournaments"].values(), key=lambda t: t["tournament_id"], reverse=True)
        for t in sorted_tourneys:
            t["pool_matches"] = list(t["pool_matches"].values())
        teams_list.append({
            "team_name": tn, "division": ts["division"],
            "matches_won": ts["matches_won"], "matches_lost": ts["matches_lost"],
            "tournaments": sorted_tourneys,
        })
    teams_list.sort(key=lambda t: (t["division"], t["team_name"]))

    seen_t: dict[str, str] = {}
    for row in rows:
        if row.get("tournament_id"):
            seen_t[row["tournament_id"]] = row.get("tournament_name") or row["tournament_id"]
    recent_tournaments = [
        {"tournament_id": tid, "name": name}
        for tid, name in sorted(seen_t.items(), reverse=True)[:5]
    ]

    seen_pm: set = set()
    recent_matchups = []
    for row in rows:
        if row.get("match_id"):
            k = (row["match_id"], row["team_name"])
            if k not in seen_pm:
                seen_pm.add(k)
                recent_matchups.append({
                    "match_id": row["match_id"], "tournament_id": row.get("tournament_id"),
                    "team_name": row.get("team_name"), "opponent_name": row.get("opponent_name"),
                    "outcome": row.get("outcome"), "score_log": row.get("score_log") or "",
                })

    seen_bm: set = set()
    recent_bracket_matchups = []
    for brow in bracket_rows:
        k = (brow["match_id"], brow["team_name"])
        if k not in seen_bm:
            seen_bm.add(k)
            recent_bracket_matchups.append({
                "match_id": brow["match_id"], "tournament_id": brow.get("tournament_id"),
                "tournament_name": brow.get("tournament_name"), "team_name": brow.get("team_name"),
                "bracket_tier": brow.get("bracket_tier"), "round_label": brow.get("round_label"),
                "opponent_name": brow.get("opponent_name"), "outcome": brow.get("outcome"),
                "score_log": brow.get("score_log") or "",
            })

    champions = [p for p in placement_rows if p.get("placement") == 1]

    return {
        "club": {
            "club_key": identity.club_key, "display_name": identity.display_name,
            "source_club_name": identity.source_club_name,
            "normalization_status": identity.normalization_status,
            "teams_active": first.get("teams_active", len(team_seasons)),
            "win_rate": round(float(first.get("win_rate") or 0), 3),
            "ranking_score": first.get("ranking_score", 0),
            "latest_activity_date": first.get("latest_activity_date"),
        },
        "teams": teams_list,
        "team_seasons": {t["team_name"]: t for t in teams_list},
        "placements": placement_rows,
        "champions": champions,
        "recent_tournaments": recent_tournaments,
        "recent_matchups": recent_matchups[:10],
        "recent_bracket_matchups": recent_bracket_matchups[:10],
    }


def build_comparison_metrics(club_a: dict, club_b: dict) -> list[dict]:
    return [
        {"label": "Teams Active", "club_a_value": club_a["teams_active"], "club_b_value": club_b["teams_active"]},
        {"label": "Win Rate", "club_a_value": club_a["win_rate"], "club_b_value": club_b["win_rate"]},
        {"label": "Ranking Score", "club_a_value": club_a["ranking_score"], "club_b_value": club_b["ranking_score"]},
    ]


def build_head_to_head(rows: list[dict], club_a_key: str, club_b_key: str) -> dict:
    if not rows:
        return {
            "matches_played": 0,
            "club_a_wins": 0,
            "club_b_wins": 0,
            "latest_meeting": None,
            "available": False,
        }
    club_a_wins = sum(1 for row in rows if row.get("outcome") == "Won")
    club_b_wins = sum(1 for row in rows if row.get("outcome") == "Lost")
    latest = max((row.get("tournament_id") for row in rows if row.get("tournament_id")), default=None)
    return {
        "matches_played": len({row["match_id"] for row in rows}),
        "club_a_wins": club_a_wins,
        "club_b_wins": club_b_wins,
        "latest_meeting": latest,
        "available": True,
        "club_a_key": club_a_key,
        "club_b_key": club_b_key,
    }


def _unique_by_key(items: list[dict], key: str) -> list[dict]:
    deduped = {}
    for item in items:
        deduped[item[key]] = item
    return list(deduped.values())


def _identity_from_row(row: dict) -> Any:
    return normalize_club_name(
        row.get("source_club_name") or row.get("club_name"),
        row.get("team_name") or row.get("match_team_name"),
        club_key=row.get("club_key"),
        normalization_status=row.get("normalization_status"),
        base_slug=row.get("base_slug"),
        collision_rank=row.get("collision_rank"),
    )


# ── Coach Hub (US1) ─────────────────────────────────────────────────────────

def _coach_initials(name: str | None) -> str:
    parts = [p for p in re.split(r"\s+", (name or "").strip()) if p]
    if not parts:
        return "?"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()


def _coach_club_label(row: dict) -> str:
    label = (row.get("club_label") or "").strip()
    if label:
        return label
    key = (row.get("club_key") or "").strip()
    if key:
        return key.replace("-", " ").title()
    return "Independent"


def build_coach_card(row: dict) -> dict:
    return {
        "coach_key": row["coach_key"],
        "display_name": row.get("display_name") or "",
        "role": row.get("role") or "",
        "club_key": row.get("club_key"),
        "club_label": _coach_club_label(row),
        "club_color": row.get("club_color") or "#5bb8ff",
        "verified": bool(row.get("verified")),
        "initials": row.get("initials") or _coach_initials(row.get("display_name")),
        "gradient": row.get("gradient") or "linear-gradient(135deg,#f5c518,#5bb8ff)",
        "wins": int(row.get("wins") or 0),
        "win_rate": round(float(row.get("win_rate") or 0), 3),
        "commits": int(row.get("commits") or 0),
        "rating": round(float(row.get("rating") or 0), 1),
        "endorse_count": int(row.get("endorse_count") or 0),
    }


def build_coach_cards(rows: list[dict]) -> list[dict]:
    return [build_coach_card(row) for row in rows]


def build_endorsement_summary(endorsements: list[dict]) -> dict:
    count = len(endorsements)
    avg = round(sum(int(e.get("stars") or 0) for e in endorsements) / count, 1) if count else 0.0
    tag_counts: Counter = Counter()
    for endorsement in endorsements:
        for tag in (endorsement.get("tags") or []):
            tag_counts[tag] += 1
    most = [{"tag": tag, "count": n} for tag, n in tag_counts.most_common(3)]
    return {"avg_rating": avg, "count": count, "most_mentioned": most}


def _build_position(p: dict) -> dict:
    return {
        "position_id": p.get("position_id"),
        "club_key": p.get("club_key"),
        "club_label": p.get("club_label") or "",
        "club_color": p.get("club_color") or "#5bb8ff",
        "role": p.get("role") or "",
        "age_group": p.get("age_group") or "",
        "years": p.get("years") or "",
        "record": p.get("record") or "",
        "note": p.get("note") or "",
        "status": p.get("status") or "pending",
    }


def _format_endorsement(e: dict) -> dict:
    created = e.get("created_at")
    date = created.strftime("%b %d, %Y") if hasattr(created, "strftime") else str(created or "")
    return {
        "author_label": e.get("author_label") or "",
        "relationship": e.get("relationship") or "",
        "stars": int(e.get("stars") or 0),
        "tags": list(e.get("tags") or []),
        "body": e.get("body") or "",
        "date": date,
    }


def _teams_from_positions(career: list[dict]) -> list[dict]:
    seen: set = set()
    teams = []
    for p in career:
        key = (p.get("club_label"), p.get("age_group"))
        if key in seen:
            continue
        seen.add(key)
        teams.append({
            "club_key": p.get("club_key"),
            "club_label": p.get("club_label") or "",
            "age_group": p.get("age_group") or "",
            "years": p.get("years") or "",
        })
    return teams


def compute_profile_strength(position_count: int, has_about: bool = False) -> int:
    """Résumé completeness 0–100 (FR-014), mirrored in editor.js.

    Base 40 for a claimed profile, +14 per position, +10 when an about/bio is present,
    capped at 100. Increases as more positions and profile detail are added.
    """
    strength = 40 + max(0, int(position_count)) * 14 + (10 if has_about else 0)
    return max(0, min(100, strength))


def _relative_time(value) -> str:
    if not hasattr(value, "timestamp"):
        return ""
    from datetime import datetime, timezone

    secs = (datetime.now(timezone.utc) - value).total_seconds()
    if secs < 3600:
        return f"{max(1, int(secs // 60))}m ago"
    if secs < 86400:
        return f"{int(secs // 3600)}h ago"
    return f"{int(secs // 86400)}d ago"


def build_director_dashboard(club_key, requests: list[dict], stats: dict, staff: list[dict]) -> dict:
    shaped_requests = [
        {
            "request_id": r["request_id"],
            "coach_key": r.get("coach_key"),
            "club_key": r.get("club_key"),
            "position_id": r.get("position_id"),
            "name": r.get("name") or "",
            "initials": r.get("initials") or _coach_initials(r.get("name")),
            "color": r.get("color") or "#5bb8ff",
            "role": r.get("role") or "",
            "claim_years": r.get("claim_years") or "",
            "match_strength": r.get("match_strength") or "Partial",
            "match_pct": int(r.get("match_pct") or 0),
            "note": r.get("note") or "",
            "when": _relative_time(r.get("created_at")),
        }
        for r in requests
    ]
    shaped_staff = [
        {
            "coach_key": s.get("coach_key"),
            "display_name": s.get("display_name") or "",
            "initials": s.get("initials") or _coach_initials(s.get("display_name")),
            "gradient": s.get("gradient") or "linear-gradient(135deg,#f5c518,#5bb8ff)",
            "role": s.get("role") or "",
            "verified": bool(s.get("verified")),
        }
        for s in staff
    ]
    return {
        "club_key": club_key,
        "requests": shaped_requests,
        "stats": {
            "coaches": int(stats.get("coaches") or 0),
            "verified": int(stats.get("verified") or 0),
            "pending": int(stats.get("pending") or 0),
            "match_rate": int(stats.get("match_rate") or 0),
        },
        "staff": shaped_staff,
        "data_state": serialize_data_state(
            shaped_requests,
            partial=not club_key,
            message="All caught up — no pending requests." if not shaped_requests else "Director queue loaded.",
        ),
    }


# ── Multi-club comparison + radar (US5) ─────────────────────────────────────

_RADAR_AXES = ["Win %", "Depth", "Gold", "Dev", "Alumni"]
_RADAR_CX, _RADAR_CY, _RADAR_R = 110, 108, 78


def _radar_points(values: list) -> str:
    pts = []
    for i in range(5):
        v = values[i] if i < len(values) else 0
        v = max(0.0, min(1.0, float(v or 0)))
        ang = math.radians(-90 + i * 72)
        x = _RADAR_CX + _RADAR_R * v * math.cos(ang)
        y = _RADAR_CY + _RADAR_R * v * math.sin(ang)
        pts.append(f"{x:.1f},{y:.1f}")
    return " ".join(pts)


def _radar_axis_labels() -> list[dict]:
    out = []
    for i, name in enumerate(_RADAR_AXES):
        ang = math.radians(-90 + i * 72)
        out.append({
            "name": name,
            "x": round(_RADAR_CX + (_RADAR_R + 14) * math.cos(ang), 1),
            "y": round(_RADAR_CY + (_RADAR_R + 14) * math.sin(ang), 1),
        })
    return out


def _best_club_key(clubs: list[dict], key: str, direction: int) -> str | None:
    vals = [(c["club_key"], c.get(key)) for c in clubs if c.get(key) is not None]
    if len(vals) < 2:
        return None
    nums = [v for _, v in vals]
    if len(set(nums)) <= 1:  # all tie -> suppress the "best" marker
        return None
    target = max(nums) if direction > 0 else min(nums)
    for ck, v in vals:
        if v == target:
            return ck
    return None


def build_multi_comparison(clubs: list[dict]) -> dict:
    metric_defs = [
        ("National rank", "rank", -1, "rank"),
        ("Win percentage", "win_rate", 1, "pct"),
        ("Active teams", "teams", 1, "num"),
        ("Gold finishes", "gold", 1, "num"),
        ("Silver / Bronze", "silver_bronze", 0, "sb"),
        ("Coaching staff", "coaches", 1, "num"),
        ("College commits", "commits", 1, "num"),
        ("Season fee", "fee", -1, "money"),
        ("Home city", "city", 0, "text"),
    ]
    metrics = []
    for label, key, direction, fmt in metric_defs:
        values, display = {}, {}
        for c in clubs:
            ck = c["club_key"]
            if fmt == "sb":
                s, b = c.get("silver"), c.get("bronze")
                values[ck] = None
                display[ck] = f"{s if s is not None else '—'} / {b if b is not None else '—'}"
            elif fmt == "text":
                values[ck] = None
                display[ck] = c.get(key) or "—"
            else:
                v = c.get(key)
                values[ck] = v
                if v is None:
                    display[ck] = "—"
                elif fmt == "rank":
                    display[ck] = f"#{v}"
                elif fmt == "pct":
                    display[ck] = f"{round(float(v) * 100)}%"
                elif fmt == "money":
                    display[ck] = f"${int(v):,}"
                else:
                    display[ck] = str(v)
        best = _best_club_key(clubs, key, direction) if direction != 0 else None
        metrics.append({"label": label, "key": key, "dir": direction, "values": values, "display": display, "best_club_key": best})

    radar = {
        "axes": _RADAR_AXES,
        "axis_labels": _radar_axis_labels(),
        "grid": _radar_points([1, 1, 1, 1, 1]),
        "series": [
            {"club_key": c["club_key"], "display_name": c["display_name"], "color": c["color"], "points": _radar_points(c.get("radar") or [])}
            for c in clubs
        ],
    }
    return {
        "clubs": [{k: c.get(k) for k in ("club_key", "display_name", "color", "tier", "rank", "win_rate", "city")} for c in clubs],
        "metrics": metrics,
        "radar": radar,
        "data_state": serialize_data_state(clubs, message="Comparison loaded." if clubs else "Pin clubs to compare."),
    }


# ── Tournament schedule (US6) ───────────────────────────────────────────────

_CITY_POS = {
    "Irving": [55, 40], "Dallas": [50, 56], "Arlington": [30, 60], "Plano": [56, 34],
    "Frisco": [50, 22], "Allen": [62, 26], "Denton": [34, 18], "Fort Worth": [22, 58],
}


def _shape_tournament(r: dict) -> dict:
    ev = r.get("event_date")
    return {
        "tournament_id": r["tournament_id"],
        "name": r.get("name") or r["tournament_id"],
        "month_key": r.get("month_key") or (ev.strftime("%Y-%m") if hasattr(ev, "strftime") else ""),
        "mo": ev.strftime("%b").upper() if hasattr(ev, "strftime") else "",
        "day": str(ev.day) if hasattr(ev, "day") else "",
        "event_date": ev.isoformat() if hasattr(ev, "isoformat") else "",
        "venue": r.get("venue") or "",
        "city": r.get("city") or "",
        "team_count": int(r.get("team_count") or 0),
        "age_lo": r.get("age_lo"),
        "age_hi": r.get("age_hi"),
        "division": r.get("division") or "",
        "status": r.get("status") or "Open",
        "within_mi": r.get("within_mi"),
        "featured": bool(r.get("featured")),
        "completed": bool(r.get("completed")),
    }


def _schedule_calendar(month_key: str, tournaments: list[dict]) -> list[list[dict]]:
    year, month = int(month_key[:4]), int(month_key[5:7])
    by_day: dict[int, list] = {}
    for t in tournaments:
        if t["day"]:
            by_day.setdefault(int(t["day"]), []).append(t)
    grid = []
    for week in _calendar.Calendar(firstweekday=6).monthdayscalendar(year, month):
        grid.append([{"day": d or None, "events": by_day.get(d, []) if d else []} for d in week])
    return grid


def build_schedule(rows: list[dict], filters: dict, all_months: list[str] | None = None) -> dict:
    shaped = [_shape_tournament(r) for r in rows]
    month_options = [
        {"key": mk, "label": date(int(mk[:4]), int(mk[5:7]), 1).strftime("%b %Y")}
        for mk in (all_months or [])
    ]
    months_map: dict[str, list] = {}
    for t in shaped:
        months_map.setdefault(t["month_key"], []).append(t)
    months = []
    for mk in sorted(k for k in months_map if k):
        year, month = int(mk[:4]), int(mk[5:7])
        months.append({
            "key": mk,
            "label": date(year, month, 1).strftime("%B %Y"),
            "tournaments": months_map[mk],
            "calendar": _schedule_calendar(mk, months_map[mk]),
        })
    city_groups: dict[str, dict] = {}
    for t in shaped:
        if not t["city"]:
            continue
        g = city_groups.setdefault(t["city"], {"city": t["city"], "count": 0, "featured": False})
        g["count"] += 1
        g["featured"] = g["featured"] or t["featured"]
    map_points = []
    for city, g in city_groups.items():
        p = _CITY_POS.get(city, [50, 50])
        map_points.append({"x": p[0], "y": p[1], "city": city, "count": g["count"], "featured": g["featured"]})
    return {
        "months": months,
        "month_options": month_options,
        "counts": {"tournaments": len(shaped), "teams": sum(t["team_count"] for t in shaped)},
        "map_points": map_points,
        "filters": filters,
        "data_state": serialize_data_state(
            shaped, message="No tournaments match these filters." if not shaped else "Schedule loaded."),
    }


# ── Tournament results (US7) ────────────────────────────────────────────────

_MEDALS = {1: "🥇", 2: "🥈", 3: "🥉"}


def build_results(tournament: dict, placements: list[dict], bracket: list[dict],
                  standings: list[dict], leaders: list[dict]) -> dict:
    podium = []
    for p in sorted(placements, key=lambda x: (x.get("placement") or 99)):
        if p.get("placement") in (1, 2, 3):
            podium.append({
                "placement": p["placement"], "medal": _MEDALS.get(p["placement"], ""),
                "team_name": p.get("team_name"), "club_key": p.get("club_key"),
                "club_name": p.get("club_name") or p.get("team_name"),
            })
    podium = podium[:3]
    champion = podium[0] if podium and podium[0]["placement"] == 1 else None

    rounds_map: dict[str, list] = {}
    seen: set = set()
    for b in bracket:
        mid = b.get("match_id")
        if mid in seen:
            continue
        seen.add(mid)
        rl = b.get("round_label") or "Bracket"
        rounds_map.setdefault(rl, []).append({
            "match_id": mid, "team_name": b.get("team_name"), "opponent_name": b.get("opponent_name"),
            "team_won": b.get("outcome") == "Won", "score_log": b.get("score_log") or "",
        })
    rounds = [{"label": rl, "matches": ms} for rl, ms in rounds_map.items()]

    standings_out = []
    for i, s in enumerate(standings, start=1):
        standings_out.append({
            "rank": i, "team_name": s.get("team_name"), "division": s.get("division"),
            "record": f"{int(s.get('matches_won') or 0)}–{int(s.get('matches_lost') or 0)}",
            "point_diff": s.get("point_diff"),
        })

    scores = [{"round": r["label"], **m} for r in rounds for m in r["matches"]]

    leaders_map: dict[str, list] = {"kills": [], "assists": [], "digs": []}
    for ldr in leaders:
        cat = ldr.get("category")
        if cat in leaders_map:
            leaders_map[cat].append({
                "rank": ldr.get("rank"), "player_name": ldr.get("player_name"),
                "club_label": ldr.get("club_label") or "", "value": ldr.get("value"),
            })

    has_bracket = bool(rounds)
    has_standings = bool(standings_out)
    has_leaders = any(leaders_map.values())
    has_any = bool(podium) or has_bracket or has_standings
    return {
        "tournament": {"tournament_id": tournament["tournament_id"], "name": tournament["name"]},
        "podium": podium,
        "champion": champion,
        "rounds": rounds,
        "standings": standings_out,
        "scores": scores,
        "leaders": leaders_map,
        "has_bracket": has_bracket,
        "has_standings": has_standings,
        "has_leaders": has_leaders,
        "data_state": serialize_data_state(
            [1] if has_any else [],
            partial=has_any and not has_bracket,
            message="Results loaded." if has_any else "No results recorded for this tournament yet."),
    }


def build_coach_profile(coach: dict, positions: list[dict], endorsements: list[dict]) -> dict:
    summary = build_endorsement_summary(endorsements)
    career = [_build_position(p) for p in positions]

    primary = None
    for p in career:
        if coach.get("club_key") and p.get("club_key") == coach.get("club_key"):
            primary = p
            break
    if primary is None and career:
        primary = career[0]
    club_label = (primary or {}).get("club_label") or _coach_club_label(coach)
    club_color = (primary or {}).get("club_color") or "#5bb8ff"

    card = build_coach_card({
        "coach_key": coach["coach_key"],
        "display_name": coach.get("display_name"),
        "role": coach.get("role"),
        "club_key": coach.get("club_key"),
        "club_label": club_label,
        "club_color": club_color,
        "verified": coach.get("verified"),
        "initials": coach.get("initials"),
        "gradient": coach.get("gradient"),
        "wins": coach.get("wins"),
        "win_rate": coach.get("win_rate"),
        "commits": coach.get("commits"),
        "rating": summary["avg_rating"],
        "endorse_count": summary["count"],
    })

    verified_positions = sum(1 for p in career if p["status"] == "verified")
    return {
        "coach": card,
        "city": coach.get("city") or "",
        "about": coach.get("about") or "",
        "verified": bool(coach.get("verified")),
        "totals": {
            "wins": card["wins"], "win_rate": card["win_rate"], "commits": card["commits"],
            "gold": int(coach.get("gold") or 0), "seasons": int(coach.get("seasons") or 0),
        },
        "certifications": list(coach.get("certifications") or []),
        "specialties": list(coach.get("specialties") or []),
        "career": career,
        "teams": _teams_from_positions(career),
        "verified_positions": verified_positions,
        "endorsement_summary": summary,
        "endorsements": [_format_endorsement(e) for e in endorsements],
        "data_state": serialize_data_state(
            career,
            partial=not career,
            message="This coach has no recorded career history yet." if not career else "Profile loaded.",
        ),
    }
