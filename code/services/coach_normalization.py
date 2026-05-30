"""Stable coach identity (FR-004), mirroring ``club_normalization``.

A coach key is ``slug(display_name)`` plus a 1-based ``collision_rank`` so that
two coaches whose names slugify to the same value stay distinct
(``maria-alvarez`` / ``maria-alvarez-2``). Keys are assigned deterministically by
sorted source name within each base slug, so re-seeding is reproducible.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class CoachIdentity:
    coach_key: str
    display_name: str
    base_slug: str
    collision_rank: int = 1
    normalization_status: str = "direct"


def slugify_coach_name(value: str | None) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "-", (value or "").lower()).strip("-")
    return cleaned or "unknown-coach"


def _compose_coach_key(base_slug: str, collision_rank: int) -> str:
    return base_slug if collision_rank <= 1 else f"{base_slug}-{collision_rank}"


def normalize_coach_name(
    display_name: str | None,
    *,
    coach_key: str | None = None,
    normalization_status: str | None = None,
    base_slug: str | None = None,
    collision_rank: int | None = None,
) -> CoachIdentity:
    source = (display_name or "").strip() or "Unknown Coach"
    resolved_base_slug = slugify_coach_name(base_slug or source)
    resolved_collision_rank = max(int(collision_rank or 1), 1)
    return CoachIdentity(
        coach_key=coach_key or _compose_coach_key(resolved_base_slug, resolved_collision_rank),
        display_name=source,
        base_slug=resolved_base_slug,
        collision_rank=resolved_collision_rank,
        normalization_status=normalization_status or "direct",
    )


def assign_stable_coach_keys(coach_names: Iterable[str]) -> dict[str, CoachIdentity]:
    """Assign collision-safe keys for a set of distinct source names."""
    grouped: dict[str, list[str]] = {}
    ordered_names = sorted({(name or "").strip() for name in coach_names if (name or "").strip()})
    for source_name in ordered_names:
        grouped.setdefault(slugify_coach_name(source_name), []).append(source_name)

    assignments: dict[str, CoachIdentity] = {}
    for base_slug, names in grouped.items():
        for index, source_name in enumerate(names, start=1):
            assignments[source_name] = CoachIdentity(
                coach_key=_compose_coach_key(base_slug, index),
                display_name=source_name,
                base_slug=base_slug,
                collision_rank=index,
                normalization_status="direct" if index == 1 else "collision-resolved",
            )
    return assignments
