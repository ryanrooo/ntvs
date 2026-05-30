import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "code"))

from services.analytics_queries import get_club_comparison, get_club_profile, get_club_rankings, get_pool_results


class FakeCursor:
    def __init__(self, rows):
        self.rows = rows

    def execute(self, query, params=None):
        self.query = query
        self.params = params

    def fetchall(self):
        return self.rows

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class FakeConnection:
    def __init__(self, rows_per_call):
        self.rows_per_call = rows_per_call
        self.calls = 0

    def cursor(self, cursor_factory=None):
        rows = self.rows_per_call[self.calls]
        self.calls += 1
        return FakeCursor(rows)


def test_get_pool_results_groups_standings_and_matchups():
    conn = FakeConnection([
        [
            {
                "pool_id": "p1",
                "pool_name": "Pool A",
                "division": "17 Open",
                "tournament_id": "t1",
                "rank_seed": 1,
                "matches_won": 3,
                "matches_lost": 0,
                "point_diff": 20,
                "pool_finish": 1,
                "team_name": "Drive Nation 17 Royal",
                "club_name": "Drive Nation",
                "sets_record": "6-1",
                "match_id": "m1",
                "match_team_name": "Drive Nation 17 Royal",
                "opponent_name": "Madfrog 17 Black",
                "outcome": "Won",
                "score_log": "25-20,25-22",
            }
        ]
    ])
    data = get_pool_results(conn, "t1", None, None, None)
    assert data["pools"][0]["standings"][0]["team_name"] == "Drive Nation 17 Royal"
    assert data["pools"][0]["matchups"][0]["outcome"] == "Won"


def test_get_club_rankings_returns_ranked_rows():
    conn = FakeConnection([
        [
            {
                "club_key": "drive-nation",
                "display_name": "Drive Nation",
                "source_club_name": "Drive Nation",
                "normalization_status": "direct",
                "teams_active": 2,
                "win_rate": 0.8,
                "ranking_score": 14.2,
                "trend_label": "Stable",
            },
            {
                "club_key": "madfrog",
                "display_name": "Madfrog",
                "source_club_name": "Madfrog",
                "normalization_status": "direct",
                "teams_active": 1,
                "win_rate": 0.5,
                "ranking_score": 9.1,
                "trend_label": "Stable",
            },
        ]
    ])
    rankings = get_club_rankings(conn, None, "rank", None)
    assert rankings[0]["rank"] == 1
    assert rankings[0]["club_key"] == "drive-nation"


def test_get_club_comparison_reports_missing_head_to_head():
    conn = FakeConnection([
        [],
        [],
        [],
    ])
    comparison = get_club_comparison(conn, "drive-nation", "madfrog")
    assert comparison["head_to_head"]["available"] is False
    assert comparison["data_state"]["completeness"] == "partial"


def test_get_club_profile_shapes_team_and_tournament_data():
    conn = FakeConnection([
        [
            {
                "club_key": "drive-nation",
                "display_name": "Drive Nation",
                "source_club_name": "Drive Nation",
                "normalization_status": "direct",
                "base_slug": "drive-nation",
                "collision_rank": 1,
                "team_name": "Drive Nation 17 Royal",
                "division": "17 Open",
                "matches_won": 3,
                "matches_lost": 1,
                "point_diff_total": 14,
                "teams_active": 1,
                "win_rate": 0.75,
                "ranking_score": 11.4,
                "tournament_id": "t1",
                "tournament_name": "Lone Star Classic",
                "match_id": "m1",
                "pool_id": "p1",
                "opponent_name": "Madfrog 17 Black",
                "outcome": "Won",
                "score_log": "25-18,25-20",
            }
        ]
    ])
    profile = get_club_profile(conn, "drive-nation")
    assert profile["club"]["club_key"] == "drive-nation"
    assert profile["teams"][0]["team_name"] == "Drive Nation 17 Royal"
    assert profile["recent_tournaments"][0]["name"] == "Lone Star Classic"


def test_get_club_rankings_preserves_collision_resolved_alias_metadata():
    conn = FakeConnection([
        [
            {
                "club_key": "rival-2",
                "display_name": "Rival!",
                "source_club_name": "Rival!",
                "normalization_status": "collision-resolved",
                "teams_active": 1,
                "win_rate": 0.667,
                "ranking_score": 8.2,
                "trend_label": "Stable",
            }
        ]
    ])

    rankings = get_club_rankings(conn, "rival", "rank", None)

    assert rankings[0]["club_key"] == "rival-2"
    assert rankings[0]["source_club_name"] == "Rival!"
    assert rankings[0]["normalization_status"] == "collision-resolved"
