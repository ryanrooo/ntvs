import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "code"))

import api


def test_home_page_renders_with_stubbed_data(monkeypatch):
    monkeypatch.setattr(
        api,
        "fetch_with_connection",
        lambda func, *args, **kwargs: {
            "featured_tournament": {"tournament_id": "t1", "name": "Lone Star Classic"},
            "featured_pools": [{"pool_id": "p1", "pool_name": "Pool A", "division": "17 Open", "tournament_id": "t1"}],
            "featured_clubs": [{"club_key": "drive-nation", "display_name": "Drive Nation", "rank": 1, "teams_active": 2, "win_rate": 0.8}],
            "featured_matchups": [],
            "tournaments": [{"tournament_id": "t1", "name": "Lone Star Classic"}],
        },
    )
    client = TestClient(api.create_app())
    response = client.get("/")
    assert response.status_code == 200
    assert "Lone Star Classic" in response.text


def test_pool_results_api_returns_json(monkeypatch):
    monkeypatch.setattr(
        api,
        "fetch_with_connection",
        lambda func, *args, **kwargs: {
            "filters": {"tournament_id": "t1", "age_group": "", "division": "", "club_name": ""},
            "pools": [],
            "data_state": {"completeness": "empty", "message": "No matching data is available."},
        },
    )
    client = TestClient(api.create_app())
    response = client.get("/api/pool-results?tournament_id=t1")
    assert response.status_code == 200
    assert response.json()["data_state"]["completeness"] == "empty"


def test_club_profile_api_404s_when_missing(monkeypatch):
    monkeypatch.setattr(api, "fetch_with_connection", lambda func, *args, **kwargs: {"teams": []})
    client = TestClient(api.create_app())
    response = client.get("/api/clubs/unknown-club")
    assert response.status_code == 404


def test_compare_page_renders_selection_options(monkeypatch):
    # US5 redefined /compare to the multi-club shape (clubs[]/metrics/radar).
    def fake_fetch(func, *args, **kwargs):
        if getattr(func, "__name__", "") == "get_club_rankings":
            return [{"club_key": "drive-nation", "display_name": "Drive Nation", "rank": 1, "teams_active": 2, "win_rate": 0.8, "trend_label": "Stable"}]
        return {
            "clubs": [{"club_key": "drive-nation", "display_name": "Drive Nation", "color": "#f5c518", "tier": 1, "rank": 1, "win_rate": 0.8, "city": None}],
            "metrics": [{"label": "Win percentage", "key": "win_rate", "dir": 1, "values": {}, "display": {"drive-nation": "80%"}, "best_club_key": "drive-nation"}],
            "radar": {"axes": ["Win %"], "axis_labels": [], "grid": "110,30", "series": []},
            "data_state": {"completeness": "complete", "message": "Comparison loaded."},
        }

    monkeypatch.setattr(api, "fetch_with_connection", fake_fetch)
    client = TestClient(api.create_app())
    response = client.get("/compare?clubs=drive-nation&clubs=madfrog")
    assert response.status_code == 200
    assert "Drive Nation" in response.text


def test_club_compare_api_returns_payload(monkeypatch):
    monkeypatch.setattr(
        api,
        "fetch_with_connection",
        lambda func, *args, **kwargs: {
            "club_a": {"display_name": "Drive Nation", "teams_active": 2, "win_rate": 0.8, "ranking_score": 10},
            "club_b": {"display_name": "Madfrog", "teams_active": 1, "win_rate": 0.7, "ranking_score": 8},
            "comparison_metrics": [{"label": "Win Rate", "club_a_value": 0.8, "club_b_value": 0.7}],
            "head_to_head": {"available": True, "matches_played": 2, "club_a_wins": 1, "club_b_wins": 1},
            "shared_matchups": [],
            "data_state": {"completeness": "complete", "message": "Comparison loaded successfully."},
        },
    )
    client = TestClient(api.create_app())
    response = client.get("/api/clubs/compare?club_a=drive-nation&club_b=madfrog")
    assert response.status_code == 200
    assert response.json()["head_to_head"]["matches_played"] == 2


def test_club_profile_api_returns_alias_metadata(monkeypatch):
    monkeypatch.setattr(
        api,
        "fetch_with_connection",
        lambda func, *args, **kwargs: {
            "club": {
                "club_key": "rival-2",
                "display_name": "Rival!",
                "source_club_name": "Rival!",
                "normalization_status": "collision-resolved",
                "teams_active": 1,
                "win_rate": 0.667,
                "ranking_score": 8.2,
                "latest_activity_date": "t1",
            },
            "teams": [{"team_name": "Rival! 17 Black", "division": "17 Open", "matches_won": 2, "matches_lost": 1, "points_diff": 9}],
            "recent_tournaments": [],
            "recent_matchups": [],
        },
    )
    client = TestClient(api.create_app())
    response = client.get("/api/clubs/rival-2")
    assert response.status_code == 200
    assert response.json()["club"]["source_club_name"] == "Rival!"
    assert response.json()["club"]["normalization_status"] == "collision-resolved"


def test_all_primary_pages_render_without_placeholder_copy(monkeypatch):
    def fake_fetch(func, *args, **kwargs):
        if func.__name__ == "get_homepage_data" or func.__name__ == "get_tournaments":
            return {
                "featured_tournament": {"tournament_id": "t1", "name": "Lone Star Classic"},
                "featured_pools": [{"pool_id": "p1", "pool_name": "Pool A", "division": "17 Open", "tournament_id": "t1"}],
                "featured_clubs": [{"club_key": "drive-nation", "display_name": "Drive Nation", "rank": 1, "teams_active": 2, "win_rate": 0.8}],
                "featured_matchups": [],
                "tournaments": [{"tournament_id": "t1", "name": "Lone Star Classic"}],
            } if func.__name__ == "get_homepage_data" else [{"tournament_id": "t1", "name": "Lone Star Classic"}]
        if func.__name__ == "get_pool_results":
            return {"filters": {"tournament_id": "t1", "age_group": "", "division": "", "club_name": ""}, "pools": [], "data_state": {"completeness": "empty", "message": "No matching data is available."}}
        if func.__name__ == "get_club_rankings":
            return [{"club_key": "drive-nation", "display_name": "Drive Nation", "rank": 1, "teams_active": 2, "win_rate": 0.8, "trend_label": "Stable"}]
        if func.__name__ == "get_club_profile":
            return {
                "club": {"club_key": "drive-nation", "display_name": "Drive Nation", "teams_active": 2, "win_rate": 0.8, "ranking_score": 10, "latest_activity_date": None},
                "teams": [{"team_name": "Drive Nation 17 Royal", "division": "17 Open", "matches_won": 3, "matches_lost": 1, "points_diff": 14}],
                "recent_tournaments": [],
                "recent_matchups": [],
            }
        return {
            "club_a": {"display_name": "Drive Nation", "teams_active": 2, "win_rate": 0.8, "ranking_score": 10},
            "club_b": {"display_name": "Madfrog", "teams_active": 1, "win_rate": 0.7, "ranking_score": 8},
            "comparison_metrics": [],
            "head_to_head": {"available": False, "matches_played": 0, "club_a_wins": 0, "club_b_wins": 0},
            "shared_matchups": [],
            "data_state": {"completeness": "partial", "message": "No direct head-to-head history is available."},
        }

    monkeypatch.setattr(api, "fetch_with_connection", fake_fetch)
    client = TestClient(api.create_app())
    for path in ["/", "/pool-results?tournament_id=t1", "/clubs", "/clubs/drive-nation", "/compare?club_a=drive-nation&club_b=madfrog"]:
        response = client.get(path)
        assert response.status_code == 200
        assert "[Brief Title]" not in response.text
