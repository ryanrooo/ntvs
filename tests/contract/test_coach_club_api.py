import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "code"))

import api

CARD = {
    "coach_key": "maria-alvarez", "display_name": "Maria Alvarez", "role": "Head Coach — 17 Open",
    "club_key": "drive-nation", "club_label": "Drive Nation", "club_color": "#f5c518",
    "verified": True, "initials": "MA", "gradient": "linear-gradient(135deg,#f5c518,#ff8a3d)",
    "wins": 312, "win_rate": 0.812, "commits": 14, "rating": 4.7, "endorse_count": 3,
}

PROFILE = {
    "coach": CARD,
    "city": "Frisco",
    "about": "Eleven seasons developing nationally ranked 17s.",
    "verified": True,
    "totals": {"wins": 312, "win_rate": 0.812, "commits": 14, "gold": 6, "seasons": 11},
    "certifications": ["USAV CAP III", "SafeSport Trained"],
    "specialties": ["Recruiting", "Player development"],
    "career": [
        {
            "position_id": 1, "club_key": "drive-nation", "club_label": "Drive Nation",
            "club_color": "#f5c518", "role": "Head Coach", "age_group": "17 Open",
            "years": "2021–2025", "record": "84–12", "note": None, "status": "verified",
        }
    ],
    "teams": [{"club_key": "drive-nation", "club_label": "Drive Nation", "age_group": "17 Open", "years": "2021–2025"}],
    "verified_positions": 1,
    "endorsement_summary": {"avg_rating": 4.7, "count": 3, "most_mentioned": [{"tag": "Development", "count": 2}]},
    "endorsements": [
        {"author_label": "Parent of an OH", "relationship": "Parent", "stars": 5,
         "tags": ["Development"], "body": "Fantastic with the girls.", "date": "May 02, 2026"}
    ],
    "data_state": {"completeness": "complete", "message": "Coaches loaded."},
}


def test_api_coaches_returns_cards_and_state(monkeypatch):
    monkeypatch.setattr(api, "fetch_with_connection", lambda func, *a, **k: [CARD])
    client = TestClient(api.create_app())
    response = client.get("/api/coaches?q=maria&verified_only=true")
    assert response.status_code == 200
    body = response.json()
    assert body["coaches"][0]["coach_key"] == "maria-alvarez"
    assert body["data_state"]["completeness"] == "complete"


def test_api_coaches_empty_state(monkeypatch):
    monkeypatch.setattr(api, "fetch_with_connection", lambda func, *a, **k: [])
    client = TestClient(api.create_app())
    response = client.get("/api/coaches?q=zzz")
    assert response.status_code == 200
    assert response.json()["data_state"]["completeness"] == "empty"


def test_api_coach_profile_returns_profile(monkeypatch):
    monkeypatch.setattr(api, "fetch_with_connection", lambda func, *a, **k: PROFILE)
    client = TestClient(api.create_app())
    response = client.get("/api/coaches/maria-alvarez")
    assert response.status_code == 200
    assert response.json()["coach"]["display_name"] == "Maria Alvarez"
    assert response.json()["endorsement_summary"]["count"] == 3


def test_api_coach_profile_404_when_missing(monkeypatch):
    monkeypatch.setattr(api, "fetch_with_connection", lambda func, *a, **k: None)
    client = TestClient(api.create_app())
    assert client.get("/api/coaches/nobody").status_code == 404


def test_coaches_directory_page_renders(monkeypatch):
    monkeypatch.setattr(api, "fetch_with_connection", lambda func, *a, **k: [CARD])
    client = TestClient(api.create_app())
    response = client.get("/coaches")
    assert response.status_code == 200
    assert "Maria Alvarez" in response.text
    assert "Drive Nation" in response.text


def test_coach_profile_page_renders_with_verification(monkeypatch):
    monkeypatch.setattr(api, "fetch_with_connection", lambda func, *a, **k: PROFILE)
    client = TestClient(api.create_app())
    response = client.get("/coaches/maria-alvarez")
    assert response.status_code == 200
    assert "Verified" in response.text
    assert "Fantastic with the girls." in response.text


# ── US2: endorsements ──────────────────────────────────────────────────────

def test_post_endorsement_accepts_valid(monkeypatch):
    monkeypatch.setattr(
        api.coach_commands, "add_endorsement",
        lambda *a, **k: {
            "endorsement": {"author_label": "Parent", "relationship": "Parent", "stars": 5,
                            "tags": ["Development"], "body": "Great coach.", "date": "May 30, 2026"},
            "applied": True,
        },
    )
    client = TestClient(api.create_app())
    r = client.post("/api/coaches/maria-alvarez/endorsements",
                    json={"relationship": "Parent", "stars": 5, "tags": ["Development"], "body": "Great coach."})
    assert r.status_code == 201
    assert r.json()["stars"] == 5


def test_post_endorsement_rejects_low_rating():
    client = TestClient(api.create_app())
    r = client.post("/api/coaches/maria-alvarez/endorsements",
                    json={"relationship": "Parent", "stars": 3, "body": "ok note"})
    assert r.status_code == 422
    assert r.json()["error"] == "rating_too_low"


def test_post_endorsement_rejects_negative_tone():
    client = TestClient(api.create_app())
    r = client.post("/api/coaches/maria-alvarez/endorsements",
                    json={"relationship": "Parent", "stars": 5, "body": "the worst coach ever"})
    assert r.status_code == 422
    assert r.json()["error"] == "negative_tone"


def test_post_endorsement_rejects_too_long():
    client = TestClient(api.create_app())
    r = client.post("/api/coaches/maria-alvarez/endorsements",
                    json={"relationship": "Parent", "stars": 5, "body": "x" * 501})
    assert r.status_code == 422
    assert r.json()["error"] == "too_long"


def test_post_endorsement_requires_relationship():
    client = TestClient(api.create_app())
    r = client.post("/api/coaches/maria-alvarez/endorsements",
                    json={"stars": 5, "body": "Great coach."})
    assert r.status_code == 422
    assert r.json()["error"] == "invalid"


# ── US3: positions + verification requests ─────────────────────────────────

def test_post_position_requires_club_and_role():
    client = TestClient(api.create_app())
    r = client.post("/api/coaches/maria-alvarez/positions", json={"club_label": "", "role": ""})
    assert r.status_code == 422
    assert r.json()["error"] == "invalid"


def test_post_position_accepts(monkeypatch):
    monkeypatch.setattr(
        api.coach_commands, "add_position",
        lambda *a, **k: {"position": {"position_id": 9, "club_label": "Drive Nation", "role": "Head Coach",
                                       "age_group": "17 Open", "years": "2021–2025", "status": "pending",
                                       "club_key": "drive-nation", "club_color": "#f5c518", "record": "", "note": ""},
                         "applied": True},
    )
    client = TestClient(api.create_app())
    r = client.post("/api/coaches/maria-alvarez/positions",
                    json={"club_label": "Drive Nation", "role": "Head Coach", "age_group": "17 Open", "years": "2021–2025"})
    assert r.status_code == 201
    assert r.json()["status"] == "pending"


def test_delete_position_returns_204(monkeypatch):
    monkeypatch.setattr(api.coach_commands, "delete_position", lambda *a, **k: {"removed": True, "reason": "deleted"})
    client = TestClient(api.create_app())
    r = client.delete("/api/coaches/maria-alvarez/positions/9")
    assert r.status_code == 204


def test_delete_verified_position_returns_409(monkeypatch):
    monkeypatch.setattr(api.coach_commands, "delete_position", lambda *a, **k: {"removed": False, "reason": "verified"})
    client = TestClient(api.create_app())
    r = client.delete("/api/coaches/maria-alvarez/positions/1")
    assert r.status_code == 409
    assert r.json()["error"] == "verified"


def test_post_verification_request_requires_club():
    client = TestClient(api.create_app())
    r = client.post("/api/coaches/maria-alvarez/verification-requests", json={"note": "please verify"})
    assert r.status_code == 422
    assert r.json()["error"] == "invalid"


def test_post_verification_request_accepts(monkeypatch):
    monkeypatch.setattr(api.coach_commands, "create_verification_request",
                        lambda *a, **k: {"request_id": 7, "status": "pending", "applied": True})
    client = TestClient(api.create_app())
    r = client.post("/api/coaches/maria-alvarez/verification-requests",
                    json={"club_key": "drive-nation", "position_id": 1})
    assert r.status_code == 201
    assert r.json()["status"] == "pending"


# ── US4: director queue + resolve ──────────────────────────────────────────

DIRECTOR_DATA = {
    "club_key": "skyline-juniors",
    "requests": [{
        "request_id": 1, "coach_key": "priya-nair", "club_key": "skyline-juniors", "position_id": 7,
        "name": "Priya Nair", "initials": "PN", "color": "#4ade80", "role": "Head Coach · 15 National",
        "claim_years": "2022–2025", "match_strength": "Partial", "match_pct": 62, "note": "Please confirm.", "when": "2h ago",
    }],
    "stats": {"coaches": 1, "verified": 0, "pending": 1, "match_rate": 62},
    "staff": [{"coach_key": "priya-nair", "display_name": "Priya Nair", "initials": "PN",
               "gradient": "linear-gradient(135deg,#4ade80,#22d3ee)", "role": "Head Coach — 15 National", "verified": False}],
    "data_state": {"completeness": "complete", "message": "Director queue loaded."},
}


def test_director_requests_returns_queue(monkeypatch):
    monkeypatch.setattr(api, "fetch_with_connection", lambda func, *a, **k: DIRECTOR_DATA)
    client = TestClient(api.create_app())
    r = client.get("/api/director/requests?club_key=skyline-juniors")
    assert r.status_code == 200
    assert r.json()["stats"]["pending"] == 1
    assert r.json()["requests"][0]["match_strength"] == "Partial"


def test_resolve_approve_applies(monkeypatch):
    monkeypatch.setattr(api.coach_commands, "resolve_request",
                        lambda rid, dec, token=None: {"request_id": rid, "status": "approved", "applied": True})
    client = TestClient(api.create_app())
    r = client.post("/api/director/requests/1/resolve", json={"decision": "approve"})
    assert r.status_code == 200
    assert r.json()["status"] == "approved" and r.json()["applied"] is True


def test_resolve_repeat_is_idempotent(monkeypatch):
    monkeypatch.setattr(api.coach_commands, "resolve_request",
                        lambda rid, dec, token=None: {"request_id": rid, "status": "approved", "applied": False})
    client = TestClient(api.create_app())
    r = client.post("/api/director/requests/1/resolve", json={"decision": "approve"})
    assert r.status_code == 200 and r.json()["applied"] is False


def test_resolve_rejects_invalid_decision():
    client = TestClient(api.create_app())
    r = client.post("/api/director/requests/1/resolve", json={"decision": "maybe"})
    assert r.status_code == 422 and r.json()["error"] == "invalid"


def test_director_page_renders(monkeypatch):
    monkeypatch.setattr(api, "fetch_with_connection", lambda func, *a, **k: DIRECTOR_DATA)
    client = TestClient(api.create_app())
    r = client.get("/director")
    assert r.status_code == 200
    assert "Pending requests" in r.text
    assert "Priya Nair" in r.text


# ── US5: multi-club compare (clubs[] 2–4, backward compatible) ─────────────

COMPARE_DATA = {
    "clubs": [{"club_key": "drive-nation", "display_name": "Drive Nation", "color": "#f5c518", "tier": 1, "rank": 2, "win_rate": 0.74, "city": None}],
    "metrics": [{"label": "Win percentage", "key": "win_rate", "dir": 1, "values": {}, "display": {"drive-nation": "74%"}, "best_club_key": "drive-nation"}],
    "radar": {"axes": ["Win %"], "axis_labels": [{"name": "Win %", "x": 110, "y": 30}], "grid": "110,30", "series": [{"club_key": "drive-nation", "display_name": "Drive Nation", "color": "#f5c518", "points": "110,40"}]},
    "data_state": {"completeness": "complete", "message": "Comparison loaded."},
}


def test_compare_legacy_pair_still_works(monkeypatch):
    captured = {}

    def fake(func, *a, **k):
        captured["keys"] = a[0] if a else None
        return COMPARE_DATA
    monkeypatch.setattr(api, "fetch_with_connection", fake)
    client = TestClient(api.create_app())
    r = client.get("/api/clubs/compare?club_a=drive-nation&club_b=madfrog")
    assert r.status_code == 200
    assert captured["keys"] == ["drive-nation", "madfrog"]


def test_compare_clubs_param_takes_precedence(monkeypatch):
    captured = {}

    def fake(func, *a, **k):
        captured["keys"] = a[0] if a else None
        return COMPARE_DATA
    monkeypatch.setattr(api, "fetch_with_connection", fake)
    client = TestClient(api.create_app())
    r = client.get("/api/clubs/compare?clubs=a&clubs=b&clubs=c&club_a=x&club_b=y")
    assert r.status_code == 200
    assert captured["keys"] == ["a", "b", "c"]


def test_compare_rejects_fewer_than_two():
    client = TestClient(api.create_app())
    assert client.get("/api/clubs/compare?clubs=a").status_code == 422


def test_compare_rejects_more_than_four():
    client = TestClient(api.create_app())
    assert client.get("/api/clubs/compare?clubs=a&clubs=b&clubs=c&clubs=d&clubs=e").status_code == 422


def test_compare_page_renders_with_radar(monkeypatch):
    def fake(func, *a, **k):
        if getattr(func, "__name__", "") == "get_club_rankings":
            return [{"club_key": "drive-nation", "display_name": "Drive Nation", "rank": 2, "teams_active": 2, "win_rate": 0.74, "trend_label": "Stable"}]
        return COMPARE_DATA
    monkeypatch.setattr(api, "fetch_with_connection", fake)
    client = TestClient(api.create_app())
    r = client.get("/compare?clubs=drive-nation&clubs=madfrog")
    assert r.status_code == 200
    assert "Profile overlay" in r.text
    assert "Drive Nation" in r.text
