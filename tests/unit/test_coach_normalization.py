import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "code"))

from services.coach_normalization import (
    assign_stable_coach_keys,
    normalize_coach_name,
    slugify_coach_name,
)


def test_slugify_coach_name_normalizes_spaces_and_case():
    assert slugify_coach_name("Maria Alvarez") == "maria-alvarez"
    assert slugify_coach_name("  J.J. O'Brien!! ") == "j-j-o-brien"


def test_slugify_coach_name_falls_back_for_empty():
    assert slugify_coach_name("") == "unknown-coach"
    assert slugify_coach_name(None) == "unknown-coach"


def test_normalize_coach_name_basic():
    identity = normalize_coach_name("Carlos Mendez")
    assert identity.coach_key == "carlos-mendez"
    assert identity.display_name == "Carlos Mendez"
    assert identity.collision_rank == 1
    assert identity.normalization_status == "direct"


def test_assign_stable_coach_keys_resolves_slug_collisions_deterministically():
    assignments = assign_stable_coach_keys(["Maria Alvarez", "Maria-Alvarez!", "Carlos Mendez"])

    assert assignments["Carlos Mendez"].coach_key == "carlos-mendez"
    assert assignments["Maria Alvarez"].coach_key == "maria-alvarez"
    assert assignments["Maria-Alvarez!"].coach_key == "maria-alvarez-2"
    assert assignments["Maria-Alvarez!"].normalization_status == "collision-resolved"


def test_normalize_coach_name_preserves_supplied_metadata():
    identity = normalize_coach_name(
        "Sara Kim",
        coach_key="sara-kim-2",
        normalization_status="collision-resolved",
        base_slug="sara-kim",
        collision_rank=2,
    )
    assert identity.coach_key == "sara-kim-2"
    assert identity.base_slug == "sara-kim"
    assert identity.collision_rank == 2
    assert identity.normalization_status == "collision-resolved"
