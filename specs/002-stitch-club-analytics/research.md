# Research: Stitch-Matched Club Analytics Experience

## Decision 1: Extend the existing FastAPI service instead of introducing a new frontend stack

- **Decision**: Implement the Stitch-matched experience as server-rendered pages and
  JSON analytics endpoints within the current FastAPI service.
- **Rationale**: The repository already ships a single Python API container and has no
  existing frontend application. Keeping the feature in the current service reduces
  deployment complexity, preserves the current compose workflow, and fits the spec's
  requirement to recreate known pages backed by existing PostgreSQL data.
- **Alternatives considered**:
  - Build a separate frontend application: rejected because it introduces a second app,
    new tooling, and additional contracts before the first analytics release is proven.
  - Serve only JSON and ignore page rendering: rejected because the feature explicitly
    requires reproducing the exported Stitch pages.

## Decision 2: Derive club analytics from normalized club identity rules centered on team records

- **Decision**: Use the `teams.club_name` field as the canonical first-pass club identity
  and add deterministic normalization rules to handle inconsistent team naming and club
  aggregation.
- **Rationale**: The current schema already stores `club_name`, which gives a better
  club anchor than parsing team names alone. Normalization logic is still necessary
  because display names, historical data quality, and comparison workflows require
  repeatable grouping behavior.
- **Alternatives considered**:
  - Infer clubs solely from team-name prefixes: rejected because the schema already has a
    better source and prefix parsing would introduce avoidable ambiguity.
  - Require manual club curation before shipping: rejected for first release because it
    blocks useful analytics that can be produced from existing records.

## Decision 3: Resolve slug collisions with deterministic stable key suffixing

- **Decision**: When multiple source club names normalize to the same base slug, assign a
  stable unique `club_key` by applying a deterministic ordering rule and suffixing later
  collisions rather than merging the clubs.
- **Rationale**: The amended spec now requires unique stable club identities and
  rerunnable migrations. Deterministic suffixing preserves each original source club name
  and avoids unique-constraint failures while keeping reruns stable.
- **Alternatives considered**:
  - Merge colliding clubs into one identity: rejected because it creates ambiguous club
    analytics and can silently combine unrelated source names.
  - Use random or time-based suffixes: rejected because reruns would not be stable.

## Decision 4: Add a controlled schema evolution path for club analytics support

- **Decision**: Introduce a migration file for additive database objects needed by the
  feature, including collision-safe alias mapping and derived analytical helpers, while
  keeping `db/init.sql` as bootstrap state for clean environments.
- **Rationale**: The repository currently initializes the schema from a single SQL file.
  Analytics work requires durable alias behavior, and a migration file provides
  traceability and safer rollout than repeatedly editing bootstrap SQL alone.
- **Alternatives considered**:
  - Change only `db/init.sql`: rejected because it obscures upgrade order for existing
    environments.
  - Avoid persistent alias objects: rejected because club comparison and rankings need a
    stable identity contract across views.

## Decision 5: Expose explicit analytics contracts for page data and direct JSON consumption

- **Decision**: Define read-only analytics endpoints for homepage summaries, pool
  results, club rankings, club profiles, and club comparisons, and use those same
  contracts to back rendered pages.
- **Rationale**: Explicit contracts keep the UI, tests, and data aggregation aligned and
  make it easier to validate partial-data and empty-state behavior. This also preserves
  compatibility by separating analytics responses from existing tournament endpoints.
- **Alternatives considered**:
  - Query the database directly from templates without endpoint contracts: rejected
    because it reduces traceability and makes contract testing weaker.
  - Overload existing tournament endpoints: rejected because the analytics payloads have
    different consumers and would increase regression risk.

## Decision 6: Use deterministic ranking and comparison metrics limited to current stored data

- **Decision**: The first release will compute club rankings and comparison metrics only
  from available tournament participation, pool standings, match outcomes, set counts,
  and point-difference style values already present in storage.
- **Rationale**: The specification forbids fabricated analytics. Limiting calculations to
  existing trustworthy data ensures every displayed metric is explainable and testable.
- **Alternatives considered**:
  - Recreate every visual metric from the Stitch samples exactly, even when unsupported
    by the database: rejected because it would require invented values.
  - Delay club rankings until richer data exists: rejected because the current schema is
    sufficient for an initial, clearly defined ranking model.

## Decision 7: Validate the feature through layered tests and explicit partial-data handling

- **Decision**: Cover the feature with unit tests for normalization and slug-collision
  resolution, integration tests for SQL aggregation and head-to-head history, and
  contract/page tests for rendered analytics responses and empty states.
- **Rationale**: The constitution requires test evidence proportionate to risk. The main
  risks here are silent data drift, incorrect alias mapping, incorrect aggregation, and
  misleading page output.
- **Alternatives considered**:
  - Manual spot checks only: rejected because collision handling and match-history logic
    can regress silently.
  - UI snapshot testing only: rejected because it would not prove the correctness of the
    underlying analytics.
