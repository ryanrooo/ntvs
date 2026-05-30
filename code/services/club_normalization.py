import re
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class ClubIdentity:
    club_key: str
    display_name: str
    source_club_name: str
    base_slug: str
    collision_rank: int = 1
    normalization_status: str = "direct"


def slugify_club_name(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "-", (value or "").lower()).strip("-")
    return cleaned or "unknown-club"


def normalize_club_name(
    club_name: str | None,
    team_name: str | None = None,
    *,
    club_key: str | None = None,
    normalization_status: str | None = None,
    base_slug: str | None = None,
    collision_rank: int | None = None,
) -> ClubIdentity:
    source = (club_name or "").strip() or _infer_club_name_from_team(team_name)
    display_name = source or "Unknown Club"
    resolved_base_slug = slugify_club_name(base_slug or display_name)
    resolved_collision_rank = max(int(collision_rank or 1), 1)
    return ClubIdentity(
        club_key=club_key or _compose_club_key(resolved_base_slug, resolved_collision_rank),
        display_name=display_name,
        source_club_name=display_name,
        base_slug=resolved_base_slug,
        collision_rank=resolved_collision_rank,
        normalization_status=normalization_status or ("direct" if club_name else "inferred"),
    )


def _infer_club_name_from_team(team_name: str | None) -> str:
    if not team_name:
        return "Unknown Club"
    parts = re.split(r"\s+", team_name.strip())
    return parts[0] if parts else "Unknown Club"


def _compose_club_key(base_slug: str, collision_rank: int) -> str:
    return base_slug if collision_rank <= 1 else f"{base_slug}-{collision_rank}"


def assign_stable_club_keys(club_names: Iterable[str]) -> dict[str, ClubIdentity]:
    grouped: dict[str, list[str]] = {}
    ordered_names = sorted({(name or "").strip() for name in club_names if (name or "").strip()})
    for source_name in ordered_names:
        base_slug = slugify_club_name(source_name)
        grouped.setdefault(base_slug, []).append(source_name)

    assignments: dict[str, ClubIdentity] = {}
    for base_slug, names in grouped.items():
        for index, source_name in enumerate(names, start=1):
            assignments[source_name] = ClubIdentity(
                club_key=_compose_club_key(base_slug, index),
                display_name=source_name,
                source_club_name=source_name,
                base_slug=base_slug,
                collision_rank=index,
                normalization_status="direct" if index == 1 else "collision-resolved",
            )
    return assignments


def build_club_index(teams: Iterable[dict]) -> dict[str, ClubIdentity]:
    index: dict[str, ClubIdentity] = {}
    for team in teams:
        identity = normalize_club_name(
            team.get("source_club_name") or team.get("club_name"),
            team.get("team_name"),
            club_key=team.get("club_key"),
            normalization_status=team.get("normalization_status"),
            base_slug=team.get("base_slug"),
            collision_rank=team.get("collision_rank"),
        )
        index[team["team_name"]] = identity
    return index
