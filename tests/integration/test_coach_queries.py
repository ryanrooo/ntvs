import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "code"))

from services.coach_queries import get_coach_directory, get_coach_profile


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


def test_directory_builds_cards_with_derived_rating():
    conn = FakeConnection([
        [
            {
                "coach_key": "maria-alvarez", "display_name": "Maria Alvarez",
                "role": "Head Coach — 17 Open", "club_key": "drive-nation", "city": "Frisco",
                "initials": "MA", "gradient": "linear-gradient(135deg,#f5c518,#ff8a3d)",
                "verified": True, "wins": 312, "win_rate": 0.812, "commits": 14,
                "rating": 4.7, "endorse_count": 3, "club_label": "Drive Nation", "club_color": "#f5c518",
            }
        ]
    ])
    cards = get_coach_directory(conn, q="maria", verified_only=True)
    assert cards[0]["coach_key"] == "maria-alvarez"
    assert cards[0]["club_label"] == "Drive Nation"
    assert cards[0]["rating"] == 4.7
    assert cards[0]["verified"] is True


def test_directory_falls_back_to_club_key_label():
    conn = FakeConnection([
        [
            {
                "coach_key": "marcus-webb", "display_name": "Marcus Webb", "role": "Skills Trainer",
                "club_key": None, "city": "Denton", "initials": "MW", "gradient": "",
                "verified": False, "wins": 54, "win_rate": 0.61, "commits": 0,
                "rating": 0, "endorse_count": 0, "club_label": None, "club_color": None,
            }
        ]
    ])
    cards = get_coach_directory(conn)
    assert cards[0]["club_label"] == "Independent"


def test_profile_assembles_sections_and_summary():
    conn = FakeConnection([
        [  # coach
            {
                "coach_key": "maria-alvarez", "display_name": "Maria Alvarez", "role": "Head Coach — 17 Open",
                "club_key": "drive-nation", "city": "Frisco", "initials": "MA",
                "gradient": "linear-gradient(135deg,#f5c518,#ff8a3d)", "verified": True,
                "about": "Eleven seasons.", "wins": 312, "win_rate": 0.812, "commits": 14,
                "gold": 6, "seasons": 11, "certifications": ["USAV CAP III"], "specialties": ["Recruiting"],
            }
        ],
        [  # positions
            {
                "position_id": 1, "club_key": "drive-nation", "club_label": "Drive Nation",
                "club_color": "#f5c518", "role": "Head Coach", "age_group": "17 Open",
                "years": "2021–2025", "record": "84–12", "note": None, "status": "verified",
            }
        ],
        [  # endorsements
            {
                "endorsement_id": 1, "author_label": "Parent of an OH", "relationship": "Parent",
                "stars": 5, "tags": ["Development", "Communication"],
                "body": "Fantastic with the girls.", "created_at": datetime(2026, 5, 2, 14, 0, 0),
            }
        ],
    ])
    profile = get_coach_profile(conn, "maria-alvarez")
    assert profile["coach"]["display_name"] == "Maria Alvarez"
    assert profile["coach"]["rating"] == 5.0
    assert profile["coach"]["endorse_count"] == 1
    assert profile["career"][0]["status"] == "verified"
    assert profile["verified_positions"] == 1
    assert profile["teams"][0]["age_group"] == "17 Open"
    assert profile["endorsement_summary"]["count"] == 1
    assert profile["endorsement_summary"]["most_mentioned"][0]["tag"] in {"Development", "Communication"}
    assert profile["data_state"]["completeness"] == "complete"


def test_profile_returns_none_when_coach_missing():
    conn = FakeConnection([[]])
    assert get_coach_profile(conn, "nobody") is None
