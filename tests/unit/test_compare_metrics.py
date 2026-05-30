import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "code"))

from services.view_models import compute_profile_strength


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
