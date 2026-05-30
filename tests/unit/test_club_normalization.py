import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "code"))

from services.club_normalization import assign_stable_club_keys, normalize_club_name, slugify_club_name


def test_slugify_club_name_normalizes_spaces_and_case():
    assert slugify_club_name("North Texas Elite") == "north-texas-elite"


def test_normalize_club_name_uses_club_name_when_present():
    identity = normalize_club_name("Drive Nation", "Drive Nation 17 Royal")
    assert identity.club_key == "drive-nation"
    assert identity.display_name == "Drive Nation"
    assert identity.normalization_status == "direct"


def test_normalize_club_name_can_infer_from_team_name():
    identity = normalize_club_name(None, "Madfrog 16 Black")
    assert identity.club_key == "madfrog"
    assert identity.normalization_status == "inferred"


def test_assign_stable_club_keys_resolves_slug_collisions_deterministically():
    assignments = assign_stable_club_keys(["Rival", "Rival!", "Drive Nation"])

    assert assignments["Drive Nation"].club_key == "drive-nation"
    assert assignments["Rival"].club_key == "rival"
    assert assignments["Rival!"].club_key == "rival-2"
    assert assignments["Rival!"].normalization_status == "collision-resolved"


def test_normalize_club_name_preserves_supplied_alias_metadata():
    identity = normalize_club_name(
        "Rival!",
        "Rival! 17 Black",
        club_key="rival-2",
        normalization_status="collision-resolved",
        base_slug="rival",
        collision_rank=2,
    )

    assert identity.club_key == "rival-2"
    assert identity.base_slug == "rival"
    assert identity.collision_rank == 2
    assert identity.normalization_status == "collision-resolved"
