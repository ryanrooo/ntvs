import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "code"))

from services.endorsement_policy import (
    MAX_BODY,
    PolicyError,
    check_endorsement,
    has_negative_tone,
)


def test_rating_floor_accepts_4_and_5():
    assert check_endorsement(4, "Great coach.") == (4, "Great coach.")
    assert check_endorsement(5, "Outstanding season.") == (5, "Outstanding season.")


@pytest.mark.parametrize("stars", [3, 2, 1, 0, "x", None])
def test_rating_floor_rejects_below_4(stars):
    with pytest.raises(PolicyError) as exc:
        check_endorsement(stars, "ok note")
    assert exc.value.code == "rating_too_low"


def test_tone_gate_rejects_flagged_words():
    for note in ["the worst coach", "was rude to players", "terrible attitude", "I hate this"]:
        with pytest.raises(PolicyError) as exc:
            check_endorsement(5, note)
        assert exc.value.code == "negative_tone"


def test_tone_gate_flags_borderline_negation_cautiously():
    # "never bad" still contains the flagged token "bad" -> flagged on purpose (favors caution).
    assert has_negative_tone("never bad") is True
    with pytest.raises(PolicyError) as exc:
        check_endorsement(5, "never bad with the kids")
    assert exc.value.code == "negative_tone"


def test_tone_gate_allows_clean_positive_note():
    assert has_negative_tone("Patient, organized, and great with families.") is False
    assert check_endorsement(5, "Patient, organized, and great with families.")[0] == 5


def test_length_cap_rejects_over_max():
    with pytest.raises(PolicyError) as exc:
        check_endorsement(5, "x" * (MAX_BODY + 1))
    assert exc.value.code == "too_long"


def test_body_is_trimmed():
    stars, body = check_endorsement(4, "  spaced out  ")
    assert body == "spaced out"
