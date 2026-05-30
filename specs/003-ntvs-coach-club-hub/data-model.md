# Phase 1 Data Model: NTVS Coach & Club Hub

Schema: `ntvs`. All new objects are additive (migration `004_coach_hub.sql`). Existing tables
(`tournaments`, `teams`, `pools`, `pool_standings`, `match_results`, `club_aliases`, `bracket_matches`,
`bracket_placements`) and views (`club_team_map`, `club_season_summary`, `club_head_to_head_summary`)
are unchanged. Performance/ranking stays derived from `club_season_summary`; the new tables hold only
NTVS-owned descriptive/curated data.

## Entity overview

```
club identity (existing: club_aliases.club_key) ──< club_attributes (1:1)
                                                └──< coaches.club_key (0..N)
                                                └──< coach_positions.club_key (0..N)
coaches (coach_key) ──< coach_positions (1:N)
                    └──< endorsements (1:N)
                    └──< verification_requests (1:N)
coach_positions ──< verification_requests.position_id (0..1)
tournaments (existing: tournament_id) ──< tournament_schedule (1:1)
                                       └──< stat_leaders (1:N)
```

## New tables

### `coaches`
Canonical coach identity + stored résumé summary (per clarification, totals are stored, not computed).

| Column | Type | Notes |
|--------|------|-------|
| `coach_key` | VARCHAR(120) PK | slug(display_name) + collision_rank (see coach_normalization) |
| `display_name` | VARCHAR(100) NOT NULL | |
| `base_slug` | VARCHAR(120) NOT NULL | for collision grouping |
| `collision_rank` | INT NOT NULL DEFAULT 1 | distinguishes same-name coaches |
| `normalization_status` | VARCHAR(32) NOT NULL DEFAULT 'direct' | `direct` / `collision-resolved` |
| `club_key` | VARCHAR(120) NULL | primary affiliation → canonical club identity (nullable) |
| `role` | VARCHAR(80) | e.g. "Head Coach — 17 Open" |
| `city` | VARCHAR(80) | |
| `initials` | VARCHAR(4) | avatar initials |
| `gradient` | VARCHAR(80) | CSS gradient token for avatar |
| `verified` | BOOLEAN NOT NULL DEFAULT FALSE | derived/maintained: TRUE iff ≥1 verified position |
| `about` | TEXT | |
| `wins` | INT NOT NULL DEFAULT 0 | stored career total |
| `win_rate` | NUMERIC(4,3) NOT NULL DEFAULT 0 | 0–1 |
| `commits` | INT NOT NULL DEFAULT 0 | college commits |
| `gold` | INT NOT NULL DEFAULT 0 | gold finishes |
| `seasons` | INT NOT NULL DEFAULT 0 | |
| `certifications` | TEXT[] | cert labels |
| `specialties` | TEXT[] | specialty chips |

Indexes: `(verified)`, `(club_key)`, trigram/`LOWER(display_name)` for search (or simple `ILIKE`).

**Validation**: `coach_key` unique & stable; `win_rate ∈ [0,1]`. `verified` is a cache of "has a
verified position" — recomputed on any position status change (never the source of truth for linkage).

### `coach_positions`
One résumé/career entry. Drives the timeline, "teams coached", profile strength, and verification.

| Column | Type | Notes |
|--------|------|-------|
| `position_id` | BIGSERIAL PK | surrogate |
| `coach_key` | VARCHAR(120) NOT NULL → coaches | |
| `club_key` | VARCHAR(120) NULL | canonical club link when matched |
| `club_label` | VARCHAR(100) NOT NULL | as claimed (shown if `club_key` unmatched) |
| `club_color` | VARCHAR(16) | timeline dot color |
| `role` | VARCHAR(80) NOT NULL | required |
| `age_group` | VARCHAR(40) | "17 Open" etc. |
| `years` | VARCHAR(20) | "2021–2024" |
| `record` | VARCHAR(20) | "84–12" (display only) |
| `note` | TEXT | |
| `status` | VARCHAR(16) NOT NULL DEFAULT 'pending' | `pending` / `verified` / `denied` |

Unique dedupe key: `(coach_key, club_label, role, years)` — supports idempotent add.
**State transitions**: `pending → verified` (director approve) or `pending → denied` (director deny).
`verified`/`denied` are terminal for that request; a denied claim may be re-submitted as a new pending
position.

### `endorsements`
Public, positive-only feedback. Append-only; summaries are derived on read.

| Column | Type | Notes |
|--------|------|-------|
| `endorsement_id` | BIGSERIAL PK | |
| `coach_key` | VARCHAR(120) NOT NULL → coaches | |
| `author_label` | VARCHAR(80) NOT NULL | e.g. "Parent of an OH" |
| `relationship` | VARCHAR(20) NOT NULL | `Parent`/`Player`/`Fellow coach`/`Club staff` |
| `stars` | SMALLINT NOT NULL | CHECK (`stars` IN (4,5)) — rating floor enforced in DB too |
| `tags` | TEXT[] | selected strength tags |
| `body` | VARCHAR(500) NOT NULL | length-capped; passes tone gate |
| `created_at` | TIMESTAMPTZ NOT NULL DEFAULT now() | |
| `body_hash` | VARCHAR(64) NOT NULL | for idempotent dedupe |

Dedupe key: unique `(coach_key, author_label, body_hash, created_at::date)`.
**Derived on read** (never stored): `avg_rating = round(avg(stars),1)`, `endorsement_count`,
`most_mentioned = top tags by frequency`. Coach card `rating`/`endorseCount` come from here.

### `verification_requests`
A coach's claim awaiting a club director's decision.

| Column | Type | Notes |
|--------|------|-------|
| `request_id` | BIGSERIAL PK | |
| `coach_key` | VARCHAR(120) NOT NULL → coaches | |
| `club_key` | VARCHAR(120) NOT NULL | target club's director queue |
| `position_id` | BIGINT NULL → coach_positions | claim being verified |
| `name` | VARCHAR(100) NOT NULL | coach name snapshot |
| `initials` | VARCHAR(4) | |
| `color` | VARCHAR(16) | |
| `role` | VARCHAR(80) | |
| `claim_years` | VARCHAR(20) | claimed years |
| `match_strength` | VARCHAR(16) | `Strong` / `Partial` — heuristic affiliation signal (seeded/snapshot), **not** derived from canonical match data |
| `match_pct` | SMALLINT | 0–100 — heuristic, not computed from match records |
| `note` | TEXT | |
| `status` | VARCHAR(16) NOT NULL DEFAULT 'pending' | `pending`/`approved`/`denied` |
| `created_at` | TIMESTAMPTZ NOT NULL DEFAULT now() | |
| `resolved_at` | TIMESTAMPTZ NULL | |

**State transitions**: `pending → approved` (also flips `position.status='verified'` and recomputes
`coaches.verified`) or `pending → denied` (also flips `position.status='denied'`). Resolve guards on
`status='pending'`; otherwise no-op (idempotent, FR-017).
**Match strength**: `match_strength`/`match_pct` are an *indicative* affiliation-confidence signal —
seeded for demo rows and assigned heuristically on coach-submitted requests (e.g. name/club/role
overlap). They are explicitly **not** derived from canonical `match_results`/standings (coaches are
not linked to team match records, per clarification), so the figure is advisory only (FR-016).

### `club_attributes`
NTVS-curated presentation/comparison fields for an existing club identity. 1:1 with `club_key`.

| Column | Type | Notes |
|--------|------|-------|
| `club_key` | VARCHAR(120) PK | → canonical club identity |
| `tier` | SMALLINT | 1–3 (nullable → neutral placeholder) |
| `color` | VARCHAR(16) | brand hex |
| `gold` / `silver` / `bronze` | INT | medal counts |
| `commits` | INT | college commits |
| `coaches_count` | INT | coaching staff size |
| `fee` | INT NULL | season fee (compare: lower-is-better) |
| `est_year` | SMALLINT | founded |
| `about` | TEXT | |
| `radar_win` / `radar_depth` / `radar_gold` / `radar_dev` / `radar_alumni` | NUMERIC(3,2) | 0–1 radar axes |

All nullable: missing values render as neutral placeholders, never zeros (edge cases, FR-030).

### `tournament_schedule`
NTVS-curated schedule attributes for an existing tournament. 1:1 with `tournament_id`.

| Column | Type | Notes |
|--------|------|-------|
| `tournament_id` | VARCHAR(50) PK | → tournaments |
| `event_date` | DATE | |
| `month_key` | VARCHAR(7) | "2026-03" grouping key |
| `venue` | VARCHAR(120) | |
| `city` | VARCHAR(80) | one of the known DFW cities (map pins) |
| `team_count` | INT | |
| `age_lo` / `age_hi` | SMALLINT | age range |
| `division` | VARCHAR(50) | |
| `status` | VARCHAR(16) | `Open`/`Filling`/`Waitlist` |
| `within_mi` | INT | static distance band (miles) from a fixed DFW metro reference; basis for the proximity filter — there is no per-user geolocation |
| `featured` | BOOLEAN DEFAULT FALSE | |
| `completed` | BOOLEAN DEFAULT FALSE | links to results when TRUE |

### `stat_leaders`
Per-tournament statistical leaders for the results page.

| Column | Type | Notes |
|--------|------|-------|
| `leader_id` | BIGSERIAL PK | |
| `tournament_id` | VARCHAR(50) NOT NULL → tournaments | |
| `category` | VARCHAR(16) NOT NULL | `kills`/`assists`/`digs` |
| `rank` | SMALLINT NOT NULL | |
| `player_name` | VARCHAR(100) NOT NULL | |
| `club_label` | VARCHAR(100) | |
| `value` | INT NOT NULL | |

Unique `(tournament_id, category, rank)`. Absence → results page marks leaders "unavailable" (FR-026).

## Derived / read-time structures (no new storage)

- **Power rankings** (home, clubs): existing `club_season_summary` joined to `club_attributes`,
  ordered by `ranking_score`; `rank` assigned at read time (as `build_club_rankings` already does).
- **Compare metrics**: per pinned club, assemble {national rank, win %, teams, gold, silver/bronze,
  coaches, commits, fee (dir=-1), city} from `club_season_summary` + `club_attributes`; compute
  `best_club_key` per row (suppress when all tie).
- **Radar**: normalize the five `radar_*` axes to 0–1 per club for the overlay polygons.
- **Results**: podium from `bracket_placements`; bracket from `bracket_matches` grouped by
  `round_label`; standings from `pool_standings`; all-scores from `match_results` + `bracket_matches`;
  leaders from `stat_leaders`.
- **Featured coaches** (home): selected at read time — verified coaches ordered by derived avg
  endorsement rating then `wins` (top N). No stored `featured` flag on `coaches`.
- **Teams coached** (coach profile): derived at read time from the coach's `coach_positions`
  (distinct `age_group`/team labels with club + years). Coaches are not linked to canonical team match
  records (per clarification), so this is a résumé-sourced list, not a match-derived one.
- **Upcoming tournaments** (home, schedule): `tournament_schedule` rows with `completed = FALSE`
  ordered by `event_date` ascending.

## Pin set (no storage)

Session-scoped `ntvs_pins` cookie holding ≤4 `club_key`s; read server-side to render pin state, toggled
client-side. The compare `clubs` query param overrides the cookie when present.

## Identity & integrity rules (constitution: Canonical Data Integrity)

- `coach_key` is the single canonical coach id; same-name coaches differ by `collision_rank`.
- Coach/position/request club references use existing `club_key` — no parallel club identifier.
- Curated tables (`club_attributes`, `tournament_schedule`, `stat_leaders`) are 1:1/keyed to existing
  ids and hold only descriptive fields; computed performance is never copied into them.
- `coaches.verified` and all count/average fields are caches/derivations recomputed from source rows,
  keeping a single source of truth and making writes idempotent.
