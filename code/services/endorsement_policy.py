"""Positive-only endorsement policy (FR-007/FR-008, research R5).

One deterministic rule set, enforced on the server and mirrored in
``static/js/endorse.js`` so the live client check and the server agree:

* **rating floor** — only 4 or 5 stars are accepted;
* **tone gate** — a case-insensitive, word-boundary match against a fixed
  negative-word list; favors caution (e.g. "never bad" is flagged) per the spec;
* **length** — body must be 1..500 characters.

This makes SC-002 ("100% of public endorsements satisfy the policy") provable.
"""
from __future__ import annotations

import re

MAX_BODY = 500
ALLOWED_STARS = (4, 5)
RELATIONSHIPS = ("Parent", "Player", "Fellow coach", "Club staff")

# Keep this list in sync with the NEGATIVE regex in code/static/js/endorse.js.
NEGATIVE_WORDS = ("bad", "awful", "terrible", "hate", "worst", "rude", "unfair")
_NEGATIVE_RE = re.compile(r"\b(" + "|".join(NEGATIVE_WORDS) + r")\b", re.IGNORECASE)


class PolicyError(Exception):
    """Raised when an endorsement violates the positive-only policy."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code        # one of: rating_too_low | negative_tone | too_long
        self.message = message


def has_negative_tone(body: str | None) -> bool:
    return bool(_NEGATIVE_RE.search(body or ""))


def check_endorsement(stars, body: str | None) -> tuple[int, str]:
    """Validate rating + note. Returns (stars, normalized_body) or raises PolicyError.

    Empty/missing body is treated as too_long's sibling here only via length; callers
    should reject missing required fields before calling this.
    """
    try:
        stars_int = int(stars)
    except (TypeError, ValueError):
        raise PolicyError("rating_too_low", "Choose a 4 or 5 star rating.")
    if stars_int not in ALLOWED_STARS:
        raise PolicyError("rating_too_low", "Endorsements are positive-only — choose 4 or 5 stars.")

    text = (body or "").strip()
    if len(text) > MAX_BODY:
        raise PolicyError("too_long", f"Please keep it under {MAX_BODY} characters.")
    if has_negative_tone(text):
        raise PolicyError("negative_tone", "Let's keep it positive — focus on what the coach does well.")
    return stars_int, text
