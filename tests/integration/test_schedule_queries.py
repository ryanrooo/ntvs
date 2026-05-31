import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "code"))

from services.view_models import build_results, build_schedule


def _rows():
    return [
        {"tournament_id": "t1", "name": "Lone Star Classic", "event_date": date(2026, 3, 8), "month_key": "2026-03",
         "venue": "Allen SP", "city": "Allen", "team_count": 212, "age_lo": 12, "age_hi": 18, "division": "Open",
         "status": "Open", "within_mi": 12, "featured": True, "completed": True},
        {"tournament_id": "t2", "name": "Plano Power", "event_date": date(2026, 3, 15), "month_key": "2026-03",
         "venue": "Plano EC", "city": "Plano", "team_count": 96, "age_lo": 13, "age_hi": 17, "division": "Club",
         "status": "Open", "within_mi": 20, "featured": False, "completed": False},
        {"tournament_id": "t3", "name": "DFW Showcase", "event_date": date(2026, 4, 5), "month_key": "2026-04",
         "venue": "Arlington CC", "city": "Arlington", "team_count": 180, "age_lo": 15, "age_hi": 18, "division": "Open",
         "status": "Waitlist", "within_mi": 35, "featured": False, "completed": False},
    ]


def test_groups_by_month_and_counts_totals():
    s = build_schedule(_rows(), {"open_only": False, "month": "", "within_mi": ""}, ["2026-03", "2026-04"])
    assert [m["key"] for m in s["months"]] == ["2026-03", "2026-04"]
    assert s["months"][0]["label"] == "March 2026"
    assert len(s["months"][0]["tournaments"]) == 2
    assert s["counts"] == {"tournaments": 3, "teams": 212 + 96 + 180}
    assert len(s["month_options"]) == 2


def test_calendar_marks_event_days():
    s = build_schedule(_rows(), {}, ["2026-03"])
    march = s["months"][0]["calendar"]
    days_with_events = [c["day"] for week in march for c in week if c["events"]]
    assert 8 in days_with_events
    assert 15 in days_with_events


def test_map_points_dedupe_by_city():
    rows = _rows() + [{"tournament_id": "t4", "name": "Extra", "event_date": date(2026, 3, 22), "month_key": "2026-03",
                       "venue": "v", "city": "Allen", "team_count": 50, "age_lo": 12, "age_hi": 18, "division": "Open",
                       "status": "Open", "within_mi": 10, "featured": False, "completed": False}]
    s = build_schedule(rows, {}, ["2026-03"])
    allen = next(p for p in s["map_points"] if p["city"] == "Allen")
    assert allen["count"] == 2
    assert allen["featured"] is True


def test_empty_schedule_reports_empty_state():
    s = build_schedule([], {}, [])
    assert s["data_state"]["completeness"] == "empty"
    assert s["counts"]["tournaments"] == 0


# ── US7: results assembly ──────────────────────────────────────────────────

def test_build_results_podium_bracket_standings_leaders():
    placements = [
        {"placement": 1, "team_name": "DN 18B", "club_key": "drive-nation", "club_name": "Drive Nation"},
        {"placement": 2, "team_name": "LS 18P", "club_key": None, "club_name": "Lone Star"},
        {"placement": 3, "team_name": "SK 18R", "club_key": None, "club_name": "Skyline"},
    ]
    bracket = [
        {"match_id": "m1", "round_label": "Final", "team_name": "DN 18B", "opponent_name": "LS 18P", "outcome": "Won", "score_log": "25-19,25-22"},
        {"match_id": "m1", "round_label": "Final", "team_name": "LS 18P", "opponent_name": "DN 18B", "outcome": "Lost", "score_log": "19-25,22-25"},
    ]
    standings = [{"team_name": "DN 18B", "matches_won": 6, "matches_lost": 0, "point_diff": 40, "division": "18 Open"}]
    leaders = [{"category": "kills", "rank": 1, "player_name": "A. Johnson", "club_label": "Drive Nation", "value": 58}]

    res = build_results({"tournament_id": "t1", "name": "Lone Star"}, placements, bracket, standings, leaders)
    assert len(res["podium"]) == 3
    assert res["champion"]["team_name"] == "DN 18B"
    assert len(res["rounds"][0]["matches"]) == 1          # two bracket rows -> one match (deduped)
    assert res["rounds"][0]["matches"][0]["team_won"] is True
    assert res["standings"][0]["record"] == "6–0"
    assert res["has_leaders"] is True and res["leaders"]["kills"][0]["value"] == 58
    assert res["data_state"]["completeness"] == "complete"


def test_build_results_empty_marks_unavailable():
    res = build_results({"tournament_id": "t1", "name": "X"}, [], [], [], [])
    assert res["has_bracket"] is False
    assert res["has_leaders"] is False
    assert res["data_state"]["completeness"] == "empty"
