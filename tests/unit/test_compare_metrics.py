import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "code"))

from services.view_models import build_multi_comparison, compute_profile_strength


def test_strength_base_and_per_position():
    assert compute_profile_strength(0) == 40
    assert compute_profile_strength(1) == 54
    assert compute_profile_strength(2) == 68          # matches the handoff's 68% at 2 positions


def test_strength_increases_with_positions():
    assert compute_profile_strength(3) > compute_profile_strength(2) > compute_profile_strength(1)


def test_strength_about_bonus():
    assert compute_profile_strength(2, has_about=True) == 78
    assert compute_profile_strength(2, has_about=True) > compute_profile_strength(2, has_about=False)


def test_strength_capped_at_100():
    assert compute_profile_strength(20, has_about=True) == 100


def test_strength_never_below_base():
    assert compute_profile_strength(0) >= 40
    assert compute_profile_strength(-5) >= 40


# ── US5: multi-club comparison best-value + radar ──────────────────────────

def _clubs():
    return [
        {"club_key": "a", "display_name": "A", "color": "#f5c518", "tier": 1, "rank": 1, "win_rate": 0.78,
         "teams": 24, "gold": 9, "silver": 6, "bronze": 4, "coaches": 14, "commits": 38, "fee": 3400, "city": None,
         "radar": [0.9, 0.78, 0.85, 0.7, 0.95]},
        {"club_key": "b", "display_name": "B", "color": "#5bb8ff", "tier": 1, "rank": 2, "win_rate": 0.74,
         "teams": 22, "gold": 8, "silver": 5, "bronze": 7, "coaches": 12, "commits": 41, "fee": 3650, "city": None,
         "radar": [0.82, 0.74, 0.7, 0.88, 0.8]},
        {"club_key": "c", "display_name": "C", "color": "#fb923c", "tier": 2, "rank": 6, "win_rate": 0.65,
         "teams": 16, "gold": 4, "silver": 6, "bronze": 6, "coaches": 8, "commits": 19, "fee": 2900, "city": None,
         "radar": [0.6, 0.65, 0.55, 0.6, 0.5]},
    ]


def _metric(cmp, key):
    return next(m for m in cmp["metrics"] if m["key"] == key)


def test_best_value_higher_is_better():
    cmp = build_multi_comparison(_clubs())
    assert _metric(cmp, "win_rate")["best_club_key"] == "a"
    assert _metric(cmp, "commits")["best_club_key"] == "b"
    assert _metric(cmp, "teams")["best_club_key"] == "a"


def test_best_value_lower_is_better_for_rank_and_fee():
    cmp = build_multi_comparison(_clubs())
    assert _metric(cmp, "rank")["best_club_key"] == "a"   # #1
    assert _metric(cmp, "fee")["best_club_key"] == "c"    # cheapest


def test_silver_bronze_and_city_have_no_best():
    cmp = build_multi_comparison(_clubs())
    assert _metric(cmp, "silver_bronze")["best_club_key"] is None
    assert _metric(cmp, "city")["best_club_key"] is None
    assert _metric(cmp, "city")["display"]["a"] == "—"


def test_best_suppressed_when_all_tie():
    clubs = _clubs()
    for c in clubs:
        c["gold"] = 5
    cmp = build_multi_comparison(clubs)
    assert _metric(cmp, "gold")["best_club_key"] is None


def test_fee_display_formats_currency():
    cmp = build_multi_comparison(_clubs())
    assert _metric(cmp, "fee")["display"]["a"] == "$3,400"


def test_radar_series_per_club_with_points():
    cmp = build_multi_comparison(_clubs())
    assert len(cmp["radar"]["series"]) == 3
    assert all(s["points"] for s in cmp["radar"]["series"])
    assert len(cmp["radar"]["axis_labels"]) == 5
