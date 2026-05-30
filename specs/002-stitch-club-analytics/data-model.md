# Data Model: Stitch-Matched Club Analytics Experience

## Existing Canonical Entities

### Tournament
- **Fields**:
  - `tournament_id`
  - `name`
- **Relationships**:
  - Has many `Pool`
- **Validation rules**:
  - `tournament_id` must be unique and stable across ETL reruns
  - `name` must be present for display and filtering

### Team
- **Fields**:
  - `team_name`
  - `club_name`
  - `division`
- **Relationships**:
  - Appears in many `PoolStanding`
  - Appears in many `MatchResult`
  - Belongs to one derived `Club`
- **Validation rules**:
  - `team_name` remains the canonical team identifier for existing result rows
  - `club_name` is the first-pass source for club aggregation

### Pool
- **Fields**:
  - `pool_id`
  - `tournament_id`
  - `division`
  - `pool_name`
  - `team_count`
- **Relationships**:
  - Belongs to one `Tournament`
  - Has many `PoolStanding`
  - Has many `MatchResult`
- **Validation rules**:
  - `pool_id` must uniquely represent one tournament/division/pool combination
  - `team_count` should match the number of participating standing rows when data is complete

### PoolStanding
- **Fields**:
  - `pool_id`
  - `team_name`
  - `rank_seed`
  - `matches_won`
  - `matches_lost`
  - `point_diff`
  - `pool_finish`
- **Relationships**:
  - Belongs to one `Pool`
  - Belongs to one `Team`
- **Validation rules**:
  - One row per `pool_id` and `team_name`
  - Rank order must be deterministic within a pool

### MatchResult
- **Fields**:
  - `match_id`
  - `pool_id`
  - `team_name`
  - `opponent_name`
  - `outcome`
  - `sets_won`
  - `sets_lost`
  - `score_log`
- **Relationships**:
  - Belongs to one `Pool`
  - References a subject `Team`
  - References an opponent team name
- **Validation rules**:
  - Existing model stores one row per team perspective for a shared match
  - `outcome` must be one of the supported result states
  - Duplicate match perspectives must remain idempotent on rerun

## New Derived or Supporting Entities

### ClubAliasMapping
- **Purpose**: Stable mapping from each original source club name to a unique analytical
  club key
- **Fields**:
  - `source_club_name`
  - `base_slug`
  - `club_key`
  - `display_name`
  - `normalization_status`
  - `collision_rank`
- **Relationships**:
  - Maps one source club name to one `Club`
- **Validation rules**:
  - `source_club_name` must remain unique
  - `club_key` must remain unique after collision resolution
  - Collision handling must be deterministic and rerunnable
  - Reapplying the mapping logic must not change an already assigned `club_key` unless
    the source club name itself changes

### Club
- **Purpose**: Stable analytical parent for rankings, profiles, and comparisons
- **Fields**:
  - `club_key`
  - `display_name`
  - `source_club_name`
  - `normalization_status`
- **Relationships**:
  - Has many `Team`
  - Has one or more `ClubSeasonSummary`
  - Has zero or more `ClubHeadToHeadSummary`
- **Validation rules**:
  - Every team included in club analytics must map to exactly one `club_key`
  - Colliding base slugs must not merge distinct source club names silently

### ClubSeasonSummary
- **Purpose**: Aggregated club metrics used by homepage callouts, rankings, and profiles
- **Fields**:
  - `club_key`
  - `teams_active`
  - `matches_won`
  - `matches_lost`
  - `sets_won`
  - `sets_lost`
  - `point_diff_total`
  - `tournaments_played`
  - `latest_activity_date`
  - `ranking_score`
- **Relationships**:
  - Belongs to one `Club`
- **Validation rules**:
  - Must be recomputable entirely from canonical result data
  - Shared metric definitions must match profile and comparison views

### ClubHeadToHeadSummary
- **Purpose**: Aggregated comparison of two clubs across direct matchups
- **Fields**:
  - `club_key`
  - `opponent_club_key`
  - `matches_played`
  - `matches_won`
  - `matches_lost`
  - `sets_won`
  - `sets_lost`
  - `latest_meeting`
- **Relationships**:
  - Connects two `Club` entities
- **Validation rules**:
  - Must be symmetric and traceable back to `MatchResult`
  - Must clearly support zero-matchup scenarios
  - Matchups must use resolved `club_key` identities, not ambiguous base slugs

### HomepageFeatureSummary
- **Purpose**: Selected tournament and club callouts used on the homepage
- **Fields**:
  - `featured_tournament_id`
  - `featured_tournament_name`
  - `featured_pool_ids`
  - `featured_club_keys`
  - `featured_match_ids`
  - `data_freshness_state`
- **Relationships**:
  - References `Tournament`, `Pool`, `Club`, and `MatchResult`
- **Validation rules**:
  - Must only reference current available data
  - Must degrade cleanly when spotlight data is incomplete

## Derived View Relationships

- `Tournament` -> `Pool` -> `PoolStanding` powers Saturday results and homepage pool cards
- `Team` -> `ClubAliasMapping` -> `Club` powers club search, profile aggregation, and ranking rows
- `MatchResult` + `Team` + `Club` powers direct head-to-head comparisons
- `ClubSeasonSummary` and `ClubHeadToHeadSummary` feed both page rendering and JSON contracts

## State and Refresh Model

- ETL continues to load canonical tournament, team, pool, standings, and match records
- Club alias mapping and analytical summaries are refreshed after canonical data changes
- Collision-safe key assignment is deterministic so reruns preserve existing club identities
- Page and endpoint responses are read-only consumers of canonical plus derived analytics
- Partial-data states are explicit when canonical inputs are missing for a requested summary
