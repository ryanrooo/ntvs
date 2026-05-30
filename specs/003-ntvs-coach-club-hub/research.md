# Phase 0 Research: NTVS Coach & Club Hub

All four scope-critical unknowns were resolved during `/speckit.clarify` (recorded in spec
Clarifications). This document captures the remaining technical decisions needed before design, each as
Decision / Rationale / Alternatives.

## R1. Interactivity model: server-rendered + progressive enhancement

- **Decision**: Keep the existing server-rendered Jinja architecture. Render all data and states on the
  server; add small vanilla-JS modules for the genuinely interactive bits (star picker, live tone gate,
  char counter, tab/view switching, club-pin toggles, live résumé preview). No SPA framework, no build
  step.
- **Rationale**: The repo is FastAPI + Jinja with an empty `static/js`. The handoff's React is a design
  reference only (README says so). Introducing React/a bundler would violate the constitution's
  "incremental, reversible changes over large rewrites" and add tooling/deps. Vanilla JS over
  server-rendered HTML keeps pages functional for reads without JS and matches project scale.
- **Alternatives**:
  - Port the React prototype as an SPA — rejected: large rewrite, new build/runtime deps, splits the
    app into two stacks.
  - HTMX/Alpine — viable and lighter than React, but still a new dependency; the interactions here are
    simple enough for ~4 small vanilla modules.

## R2. Club-pin persistence (shared across directory / profile / compare)

- **Decision**: Store the pinned set as a small cookie `ntvs_pins` (comma-separated `club_key`s, max 4).
  The server reads it to render "Pinned/✓" state and to drive the compare page; `pins.js` toggles it
  client-side and updates the UI optimistically. Compare also accepts an explicit `clubs` query param
  (shareable URL) which takes precedence over the cookie when present.
- **Rationale**: FR-019 requires the pinned set to be consistent across three server-rendered pages, so
  the server must see it — a cookie is the simplest shared, session-scoped store with no auth and no new
  storage. Matches the "persists for the session, not across devices" assumption. The `clubs` param keeps
  comparisons linkable and keeps `/api/clubs/compare` backward compatible.
- **Alternatives**:
  - `localStorage` only — rejected: invisible to the server, so initial render can't show pin state.
  - Server session table — rejected: needs identity/session infra that's explicitly out of scope.

## R3. Multi-club compare contract (2→4 clubs) without breaking the existing endpoint

- **Decision**: Extend `/api/clubs/compare` to accept a repeatable `clubs` parameter (2–4 `club_key`s)
  while still accepting the legacy `club_a` + `club_b`. Internally normalize both into a list. The
  comparison response gains a `clubs[]` array, a `metrics[]` table with per-metric `best_club_key` (and
  `dir` where lower-is-better, e.g. season fee), and `radar` axis/normalized-value data.
- **Rationale**: Constitution treats API behavior as a contract; keeping `club_a/club_b` working makes
  the change additive/backward compatible. Best-value and radar normalization are computed server-side so
  templates stay logic-light.
- **Alternatives**: New `/api/clubs/compare-multi` endpoint — rejected: duplicates logic and leaves two
  contracts to maintain.

## R4. Coach identity & coach→club linkage

- **Decision**: New `coach_normalization` module mirroring `club_normalization`: `coach_key` =
  slug(display_name) + collision_rank, assigned stably so identically named coaches stay distinct. A
  coach row stores a nullable `club_key` (its primary affiliation) referencing the canonical club
  identity; `coach_positions` each carry their own `club_key`. When a `club_key` has no canonical match,
  the profile shows the claimed club name without a link (graceful degrade, per edge case).
- **Rationale**: Satisfies FR-004/FR-032 (canonical identity, duplicate handling) by reusing the proven
  club pattern; reusing `club_key` avoids inventing a second identifier for clubs.
- **Alternatives**: Random UUID coach ids — rejected: opaque URLs and no deterministic seed/idempotency
  for re-seeding.

## R5. Endorsement positive-only policy (rating floor + tone gate)

- **Decision**: Centralize in `endorsement_policy.py`:
  - Rating floor: accept only `stars ∈ {4, 5}`; reject anything else server-side (UI also disables 1–3).
  - Tone gate: a deterministic, case-insensitive regex on word boundaries —
    `\b(bad|awful|terrible|hate|worst|rude|unfair)\b` (the prototype's list) — plus length ≤ 500. A note
    that matches is rejected with guidance. The same function powers the live client check (`endorse.js`)
    and the server-side validation, so client and server agree.
  - Enforced on the server regardless of client JS (FR-007/FR-008, SC-002).
- **Rationale**: One documented rule, applied on both sides, makes SC-002 ("100% of public endorsements
  satisfy the policy") provable and testable. Favors caution (may flag borderline phrasing) per the spec.
- **Alternatives**: Sentiment-analysis/ML moderation — rejected: nondeterministic, new dependency,
  overkill; not a substitute for the human moderation that's out of scope anyway.

## R6. Write-action idempotency + production abuse gating

- **Decision**:
  - Endorsement: dedupe on `(coach_key, author_label, body_hash, created_date)` — a repeated identical
    submit on the same day is a no-op returning the existing row.
  - Position add: dedupe on `(coach_key, club_key, role, years)`.
  - Verification resolve: guard on `status='pending'`; resolving an already-decided or missing request
    is a safe no-op (FR-017). Approval flips the linked position to `verified` exactly once.
  - All counts (avg rating, endorsement count, verified count, match rate) are computed from rows on
    read, never incremented in place — so retries can't drift them.
  - Production abuse gating (**supersedes the earlier "fully open (demo)" posture**): a config-gated
    (`NTVS_WRITE_GATING`) per-IP rate limit + honeypot on endorsement/position submissions and a shared
    `NTVS_DIRECTOR_TOKEN` on verification resolve — ON in production, OFF for local/demo. Throttled or
    rejected writes return a clear message and persist nothing (FR-035, plan PR-3).
- **Rationale**: Satisfies FR-031/SC-008 and the Idempotent-Slices principle without per-user sessions;
  gating adds coarse, config-driven abuse protection for the public-production target (FR-035).
- **Alternatives**: Client-supplied idempotency keys — viable but adds protocol surface; natural-key
  dedupe is sufficient at this scale.

## R7. Source of club/tournament presentation & schedule attributes

- **Decision**: Add NTVS-owned tables keyed to existing identities: `club_attributes` (PK `club_key`)
  for tier, color, medals, commits, coaching staff, fee, est. year, about, five radar dims;
  `tournament_schedule` (PK `tournament_id`) for date, venue, city, age range, division, status,
  featured/completed flags; `stat_leaders` for results leaders. Seeded idempotently from
  `004_seed_coach_hub.sql`. Derived performance (win rate, rank) continues to come from the existing
  `club_season_summary` view — presentation tables never duplicate computed performance.
- **Rationale**: Keeps a single source of truth (FR-032): scraped performance stays in the existing
  views; only net-new descriptive attributes live in the new tables. Nullable columns + neutral
  placeholders satisfy the "missing data renders as placeholder, not zero" edge cases.
- **Alternatives**: Widen the `teams`/`tournaments` base tables — rejected: those are scraper-owned and
  mixing NTVS-curated fields into them muddies source-of-truth and rerun behavior.

## R8. Design-system re-theme (amber/navy) approach

- **Decision**: Re-map the CSS custom properties in `club_analytics.css` to the handoff tokens (accent
  `#f5c518`, surfaces on `#0a1020`/`#0f1729`/`#131c33`, win `#4ade80`, loss `#f87171`, cyan `#5bb8ff`
  for verification/links) and swap the Google Fonts link to Bricolage Grotesque / IBM Plex Sans /
  JetBrains Mono. Because existing templates already consume CSS variables (`--accent`, `--bg`, etc.),
  re-theming flows to existing pages with minimal markup change (FR-034). New component classes
  (tiers, chips, radar, bracket, podium, stepper, star picker) are added alongside.
- **Rationale**: Token indirection is already in place, so a variable re-map is the lowest-churn way to
  apply one coherent system app-wide. Exact token table lives in data-model/quickstart for reference.
- **Alternatives**: Per-screen scoped themes — rejected by clarification (chose one app-wide system).

## Resolved unknowns summary

| Topic | Resolution |
|-------|-----------|
| Coach totals source | Stored on coach (clarified) |
| Visual system | App-wide amber/navy re-theme (clarified) |
| Write access | Production abuse gating (rate-limit + honeypot + director token), OFF for local/demo; screening + idempotency (clarified — supersedes earlier "fully open") |
| Export PDF | Out of scope (clarified) |
| Interactivity | Server-rendered + vanilla JS progressive enhancement (R1) |
| Pin persistence | `ntvs_pins` cookie + `clubs` param (R2) |
| Compare contract | Additive `clubs` param, keep `club_a/b` (R3) |
| Coach identity | slug + collision_rank, reuse `club_key` (R4) |
| Tone gate | Shared deterministic regex + rating floor (R5) |
| Idempotency | Natural-key dedupe + status guards (R6) |
| Presentation data | New NTVS-owned tables keyed to existing ids (R7) |

No `NEEDS CLARIFICATION` markers remain.
