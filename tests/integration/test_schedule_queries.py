import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "code"))

from services.view_models import build_schedule


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
