---
description: "Task list for NTVS Coach & Club Hub (NTVS-2 Handoff)"
---

# Tasks: NTVS Coach & Club Hub (NTVS-2 Handoff)

**Input**: Design documents from `/specs/003-ntvs-coach-club-hub/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/coach-club-api.yaml, quickstart.md

**Tests**: REQUIRED. The constitution ("Test Evidence Before Merge") and plan list unit,
integration, and contract suites; this feature changes data contracts, adds API responses, and
introduces write actions, so tests are written first per story and must fail before implementation.

**Organization**: Tasks are grouped by user story (priority order from spec.md) so each story can be
implemented and tested as an independent increment.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel — different file, no dependency on an incomplete task
- **[Story]**: Owning user story (US1–US8); Setup/Foundational/Polish carry no story label
- Every task names an exact file path

## Path Conventions

NTVS default layout at repo root: `code/` (app: `api.py`, `services/`, `templates/`, `static/`),
`db/migrations/` (schema), `tests/{unit,integration,contract}/`. This feature lives entirely in
`code/` + `db/` + `tests/` (no new top-level dirs), per plan.md Structure Decision.

> **⚠️ Shared serialization points** (cannot be `[P]` across stories — same file): `code/api.py`,
> `code/services/view_models.py`, `code/services/analytics_queries.py`, `code/services/coach_commands.py`
> (US2/US3/US4), `code/services/coach_queries.py` (US1/US4), `code/services/schedule_queries.py`
> (US6/US7), `code/static/css/club_analytics.css` (all), `code/static/js/tabs.js` (US1/US6/US7),
> `code/templates/layout.html`, `code/templates/club_rankings.html` + `club_profile.html` (US5/US8),
> and the single contract suite `tests/contract/test_coach_club_api.py` (all). `[P]` within a story
> still holds where tasks touch genuinely different files.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Clear known foot-guns and confirm the build/test baseline before any feature work.

- [X] T001 Remove the local `email_validator.py` shim and the stray `email_validator-2.0.0.dist-info/`, and confirm a pinned `email-validator` line in `requirements.txt` (PR-4)
- [X] T002 [P] Ensure pytest test layout exists (`tests/unit/`, `tests/integration/`, `tests/contract/` with package init files as needed) and a `DATABASE_URL` pointing at a disposable Postgres test DB per quickstart.md §1
- [X] T003 Boot the unchanged app (`docker compose up` or `cd code && uvicorn api:app --reload`) and confirm existing pages/endpoints serve, establishing a green baseline before changes

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Schema, seed, DB access, coach identity, write-path safety, and the app-wide re-theme/nav
that every story builds on.

**⚠️ CRITICAL**: No user story work begins until this phase is complete.

- [X] T004 Create additive, rerun-safe migration `db/migrations/004_coach_hub.sql` defining all seven tables (`coaches`, `coach_positions`, `endorsements`, `verification_requests`, `club_attributes`, `tournament_schedule`, `stat_leaders`) with `CREATE TABLE IF NOT EXISTS` / `ADD COLUMN IF NOT EXISTS`, CHECK constraints (`endorsements.stars IN (4,5)`), dedupe UNIQUE keys (positions `(coach_key, club_label, role, years)`; endorsements `(coach_key, author_label, body_hash, created_at::date)`; `stat_leaders (tournament_id, category, rank)`), FKs to existing `club_key`/`tournament_id`, and search indexes — per data-model.md
- [X] T005 Create idempotent demo seed `db/migrations/004_seed_coach_hub.sql` (coaches, coach_positions, endorsements, verification_requests, club_attributes, tournament_schedule, stat_leaders) using `ON CONFLICT DO NOTHING/UPDATE`, sized to cover every story's independent test (research R7)
- [X] T006 Apply `004_coach_hub.sql` then `004_seed_coach_hub.sql` to the test DB and re-apply both to prove rerun-safety (no duplicates, no errors), per quickstart.md §1
- [X] T007 [P] Create `code/services/db.py` — `ThreadedConnectionPool` + `read_conn()` / `write_conn()` context managers (write commits on success, rolls back on exception, returns connection to pool) (PR-1)
- [X] T008 [P] Integration test `tests/integration/test_db_helpers.py` — `write_conn` commits, an exception inside `write_conn` rolls back, and pool connections are reused (PR-1)
- [X] T009 Refactor `code/api.py` to route DB access through `code/services/db.py` (reads via `read_conn`, keeping `fetch_with_connection` as a thin read shim; writes via `write_conn`) with no behavior change to existing reads (PR-1)
- [X] T010 [P] Create `code/services/coach_normalization.py` — stable `coach_key = slug(display_name) + collision_rank`, mirroring `club_normalization` so identically named coaches stay distinct (research R4, FR-004)
- [X] T011 [P] Unit test `tests/unit/test_coach_normalization.py` — deterministic slugs, collision_rank increments for same-name coaches, stable keys across reruns
- [X] T012 [P] Create `code/services/rate_limit.py` — config-gated (`NTVS_WRITE_GATING`) per-IP rate limiter + honeypot check for endorsement/position POSTs and a shared-token check (`NTVS_DIRECTOR_TOKEN`) for director resolve; ON by default in production, OFF for local/demo; throttled/rejected requests persist nothing (PR-3, FR-035)
- [X] T013 Update `code/templates/layout.html` — add primary nav entries (Coaches, Schedule, Compare, Director per FR-033), swap the Google Fonts link to Bricolage Grotesque / IBM Plex Sans / JetBrains Mono, and add re-theme hooks (research R8, FR-034)
- [X] T014 Re-map `code/static/css/club_analytics.css` `:root` custom properties to the amber/deep-navy token system (accent `#f5c518`; surfaces `#0a1020`/`#0f1729`/`#131c33`; win `#4ade80`/loss `#f87171`; cyan `#5bb8ff`), so existing pages pick up the new look via the shared variables (FR-034, research R8)

**Checkpoint**: Schema + seed live, pooled/transactional DB access, coach identity, write gating, and the base design system are in place — user stories can begin.

---

## Phase 3: User Story 1 - Scout coaches via verified résumés (Priority: P1) 🎯 MVP

**Goal**: A browsable, searchable coaches directory and a full coach résumé profile (career history, totals, certs, specialties, timeline, teams, endorsements) with a clear verified badge — all read-only from seeded data.

**Independent Test**: Load `/coaches` with seeded coaches, search by name and toggle "Verified only", open a profile, and confirm résumé sections + verification badge render correctly; the club link routes to `/clubs/{club_key}`.

### Tests for User Story 1 ⚠️ (write first, must fail)

- [X] T015 [P] [US1] Contract tests for `GET /api/coaches` (CoachCard list, `q` search, `verified_only`, empty state, `data_state`) and `GET /api/coaches/{coach_key}` (CoachProfile shape + 404) in `tests/contract/test_coach_club_api.py`
- [X] T016 [P] [US1] Integration test for coach directory/profile reads (name+club search, verified filter, derived avg_rating/endorsement_count/most_mentioned) in `tests/integration/test_coach_queries.py`

### Implementation for User Story 1

- [X] T017 [P] [US1] Implement coach directory + profile read queries (substring `q` over coach/club name, `verified_only` filter, derived endorsement summary `avg_rating`/`count`/`most_mentioned`) in `code/services/coach_queries.py`
- [X] T018 [US1] Add CoachCard + CoachProfile view-model shaping (career timeline, teams coached, stored totals, derived rating/endorse_count, `data_state` complete/partial/empty) in `code/services/view_models.py`
- [X] T019 [US1] Add `GET /api/coaches` and `GET /api/coaches/{coach_key}` JSON endpoints plus `/coaches` and `/coaches/{coach_key}` page routes, each emitting `logger.info` with `data_state.completeness`, in `code/api.py`
- [X] T020 [P] [US1] Create coaches directory template (coach-card grid with name/role/club/badge/summary stats, name+club search box, "Verified only" toggle, empty state) in `code/templates/coaches_directory.html`
- [X] T021 [P] [US1] Create coach profile template (identity, verified badge, totals, certifications, specialties, career timeline, teams coached, endorsements tab + count; canonical club link to `/clubs/{club_key}` else plain claimed label) in `code/templates/coach_profile.html`
- [X] T022 [P] [US1] Create `code/static/js/tabs.js` for coach-profile tab switching (career / teams / endorsements)
- [X] T023 [US1] Add coach card / profile / verified-badge / timeline / chip styles to `code/static/css/club_analytics.css`

**Checkpoint**: US1 is fully functional and demoable as the MVP — coaches can be browsed, searched, filtered, and read in full.

---

## Phase 4: User Story 2 - Leave a positive-only endorsement (Priority: P2)

**Goal**: A supportive endorsement composer on a coach profile (4–5 star rating, relationship, strength tags, note) that screens negative wording and posts immediately, updating the coach's average rating, count, and most-mentioned strengths.

**Independent Test**: On a seeded coach profile, submit a valid positive endorsement and confirm it prepends and updates the summary; submit a negative-worded note and confirm it is blocked with guidance.

### Tests for User Story 2 ⚠️ (write first, must fail)

- [X] T024 [P] [US2] Unit test `tests/unit/test_endorsement_policy.py` — rating floor accepts only {4,5}; deterministic tone-gate regex rejects flagged words and handles borderline negation (e.g. "never bad"); length > 500 rejected
- [X] T025 [P] [US2] Contract test for `POST /api/coaches/{coach_key}/endorsements` (201 accepted; 422 `rating_too_low` / `negative_tone` / `too_long`; idempotent same-day dedupe returns existing row) in `tests/contract/test_coach_club_api.py`
- [X] T026 [P] [US2] Integration test for endorsement write idempotency (duplicate same-day submit is a no-op — guarded by the UNIQUE dedupe constraint `(coach_key, author_label, body_hash, created_at::date)` even under concurrent submits; `avg_rating`/`count` derived from rows, never incremented) in `tests/integration/test_coach_commands.py`

### Implementation for User Story 2

- [X] T027 [P] [US2] Implement `code/services/endorsement_policy.py` — rating floor + deterministic case-insensitive word-boundary tone-gate regex (research R5) + length cap, exposed as one function shared by client and server
- [X] T028 [US2] Implement `add_endorsement` in `code/services/coach_commands.py` — `write_conn` transaction, `body_hash` dedupe key `(coach_key, author_label, body_hash, created_date)`, apply `endorsement_policy`, honeypot/rate-limit hook from `rate_limit` (PR-2/PR-3)
- [X] T029 [US2] Add `POST /api/coaches/{coach_key}/endorsements` endpoint (201 Endorsement / 422 PolicyError), wired to `rate_limit` gating, with `logger.info` recording applied/no-op outcome, in `code/api.py`
- [X] T030 [US2] Add the endorsement composer to `code/templates/coach_profile.html` (relationship select, strength tags, star picker allowing only 4–5 with 1–3 visibly disabled, body + remaining-character counter, hidden honeypot field) and prepend the accepted endorsement to the list
- [X] T031 [P] [US2] Create `code/static/js/endorse.js` — star picker, live tone gate (same rule as server), char counter, submit + optimistic list/summary refresh
- [X] T032 [US2] Add star-picker / composer / endorsement-card styles to `code/static/css/club_analytics.css`

**Checkpoint**: US1 + US2 work independently — coaches can be scouted and endorsed under the positive-only policy.

---

## Phase 5: User Story 3 - Claim and build a coaching résumé (Priority: P2)

**Goal**: A guided résumé editor where a coach adds positions (club+role required), sees a live preview with verified-position count and profile-strength meter, and submits verification requests to a club director.

**Independent Test**: Open `/coaches/{coach_key}/edit`, add a position and watch it appear pending in the live preview with profile strength rising, then submit a verification request that lands in the director queue.

### Tests for User Story 3 ⚠️ (write first, must fail)

- [X] T033 [P] [US3] Unit test for the profile-strength formula (increases as positions and steps are completed) in `tests/unit/test_compare_metrics.py`
- [X] T034 [P] [US3] Contract tests for `POST /api/coaches/{coach_key}/positions` (201; 422 when club or role missing; idempotent on club+role+years), `DELETE .../positions/{position_id}` (204 idempotent; 409 when verified), and `POST .../verification-requests` (201; existing pending returned) in `tests/contract/test_coach_club_api.py`
- [X] T035 [P] [US3] Integration test for position add/delete and verification-request creation idempotency (re-add is no-op; delete-of-verified blocked) in `tests/integration/test_coach_commands.py`

### Implementation for User Story 3

- [X] T036 [US3] Implement `add_position` (dedupe key `(coach_key, club_label/club_key, role, years)`), `delete_position` (409 if verified, no-op if absent), and `create_verification_request` (return existing pending) in `code/services/coach_commands.py`
- [X] T037 [US3] Add profile-strength computation (from completeness) plus pending/verified position counts to `code/services/view_models.py`
- [X] T038 [US3] Add `POST /api/coaches/{coach_key}/positions` (rate-limit + honeypot gated per FR-035), `DELETE .../positions/{position_id}`, and `POST .../verification-requests` endpoints plus the `/coaches/{coach_key}/edit` page route, with `logger.info`, in `code/api.py`
- [X] T039 [P] [US3] Create résumé editor template (stepper, position form with required club+role and remove control, live preview with mirrored career timeline, live verified-position count, profile-strength meter) in `code/templates/coach_editor.html`
- [X] T040 [P] [US3] Create `code/static/js/editor.js` — live résumé preview, profile-strength meter, add/remove position, submit verification request
- [X] T041 [US3] Add stepper / editor / live-preview / strength-meter styles to `code/static/css/club_analytics.css`

**Checkpoint**: Coaches can self-build résumés and request verification; requests are queued for US4.

---

## Phase 6: User Story 4 - Approve or deny coach verification (club director) (Priority: P2)

**Goal**: A director dashboard of pending requests (coach, claimed role/years, match-strength %, note) with approve/deny that flips the position verified-and-linked or denied, updates counts, and is safe to retry.

**Independent Test**: With seeded pending requests, approve one and confirm the coach becomes verified/linked and leaves the queue; deny another and confirm removal without linking; re-resolving is a no-op.

### Tests for User Story 4 ⚠️ (write first, must fail)

- [X] T042 [P] [US4] Contract test for `GET /api/director/requests` (requests + DirectorStats + `data_state`) and `POST /api/director/requests/{request_id}/resolve` (approve → status approved, `applied:true`; repeat → `applied:false`; deny path) in `tests/contract/test_coach_club_api.py`
- [X] T043 [P] [US4] Integration test asserting resolve is idempotent and a concurrent double-approve applies exactly once (relies on `SELECT … FOR UPDATE`), flipping `coaches.verified` once, in `tests/integration/test_coach_commands.py`

### Implementation for User Story 4

- [X] T044 [US4] Implement the director queue read (pending requests with match-strength %, DirectorStats `coaches`/`verified`/`pending`/`match_rate`, `data_state`) in `code/services/coach_queries.py`
- [X] T045 [US4] Implement `resolve_request` in `code/services/coach_commands.py` — `write_conn` + `SELECT … FOR UPDATE` on the request row, guard on `status='pending'`, approve → position `verified` + recompute `coaches.verified`, deny → position `denied`, otherwise idempotent no-op; director-token check via `rate_limit` (PR-2/PR-3)
- [X] T046 [US4] Add `GET /api/director/requests` and `POST /api/director/requests/{request_id}/resolve` endpoints plus the `/director` page route, with `logger.info` recording applied/no-op, in `code/api.py`
- [X] T047 [P] [US4] Create director dashboard template (pending queue: coach name/role/claimed years/match-strength %+bar/note + approve/deny; stats header; "all caught up" empty state) in `code/templates/director.html`
- [X] T048 [US4] Add director queue / stat-card styles to `code/static/css/club_analytics.css`

**Checkpoint**: The full coach loop (scout → endorse → claim → verify) works end-to-end and independently.

---

## Phase 7: User Story 5 - Compare up to four clubs head-to-head (Priority: P3)

**Goal**: Pin up to four clubs (shared across directory/profile/compare via the `ntvs_pins` cookie) and compare them in a best-value-highlighted metrics table plus a five-axis radar overlay.

**Independent Test**: Pin three clubs from `/clubs`, open `/compare`, confirm all three appear with best-per-metric highlights (lowest fee wins) and a 3-series radar; add a fourth, confirm a fifth is refused; `?club_a=&club_b=` still works.

### Tests for User Story 5 ⚠️ (write first, must fail)

- [ ] T049 [P] [US5] Unit test `tests/unit/test_compare_metrics.py` — best value per metric, `dir=-1` (lower-is-better) for season fee, and best-marker suppression when all values tie
- [ ] T050 [P] [US5] Contract test for `GET /api/clubs/compare` (legacy `club_a`+`club_b` compat; repeatable `clubs` 2–4 with precedence; 422 outside 2–4; `metrics[].best_club_key` + `dir`; `radar` axes/series; `data_state`) in `tests/contract/test_coach_club_api.py`

### Implementation for User Story 5

- [ ] T051 [US5] Implement N-club compare data assembly (rank, win %, teams, gold/silver/bronze, coaches, commits, fee, city) from `club_season_summary` + `club_attributes` in `code/services/analytics_queries.py`
- [ ] T052 [US5] Add compare shaping in `code/services/view_models.py` — `best_club_key` per metric (dir-aware, tie suppression, neutral placeholder when missing) and radar normalization of the five `radar_*` axes to 0–1
- [ ] T053 [US5] Extend `GET /api/clubs/compare` to accept repeatable `clubs` (2–4, precedence over `club_a`/`club_b`, 422 outside range) and add the `/compare` page route that reads the `ntvs_pins` cookie and the `clubs` param, in `code/api.py`
- [ ] T054 [P] [US5] Update comparison template — up to 4 clubs metrics table (best-value highlight, neutral placeholders for missing fee/medals/radar), radar/spider chart with color-keyed legend, and empty state — in `code/templates/club_comparison.html`
- [ ] T055 [P] [US5] Create `code/static/js/pins.js` — `ntvs_pins` cookie toggle, max-4 enforcement with a clear refusal message, pinned-count badge, and UI sync across directory/profile/compare
- [ ] T056 [US5] Add pin/unpin toggle controls to `code/templates/club_rankings.html` and `code/templates/club_profile.html` (these templates are shared with US8)
- [ ] T057 [US5] Add compare-table / radar / pin-toggle styles to `code/static/css/club_analytics.css`

**Checkpoint**: Multi-club comparison works; legacy two-club compare remains intact.

---

## Phase 8: User Story 6 - Browse the tournament schedule (Priority: P3)

**Goal**: A schedule in list (by month) / calendar / map views with open-only, month, and proximity filters, a live "N tournaments · N teams" count, and links from completed tournaments to results.

**Independent Test**: Open `/schedule`, switch list/calendar/map, apply a month + "open only" filter and confirm the set and counts update, then click a completed tournament and land on its results.

### Tests for User Story 6 ⚠️ (write first, must fail)

- [ ] T058 [P] [US6] Contract test for `GET /api/schedule` (`open_only`/`month`/`within_mi` filters, `counts.{tournaments,teams}`, `data_state`, empty state) in `tests/contract/test_coach_club_api.py`
- [ ] T059 [P] [US6] Integration test for schedule queries (month grouping, filter combinations, count totals) in `tests/integration/test_schedule_queries.py`

### Implementation for User Story 6

- [ ] T060 [P] [US6] Implement schedule read + filtering (join `tournament_schedule`, `open_only`/`month`/`within_mi`, month grouping, tournaments+teams counts, list/calendar/map-ready data) in `code/services/schedule_queries.py`
- [ ] T061 [US6] Add `GET /api/schedule` endpoint and `/schedule` page route with `logger.info(data_state)` in `code/api.py`
- [ ] T062 [P] [US6] Create schedule template — list grouped by month (date/name/venue/city/teams/age range/division/status chip, completed → results link), calendar month grid, schematic DFW map with city pins, filters (open-only/month/proximity) + clear-all + live "N tournaments · N teams" count + empty state — in `code/templates/schedule.html`
- [ ] T063 [US6] Extend `code/static/js/tabs.js` for schedule list/calendar/map view switching that preserves active filters
- [ ] T064 [US6] Add schedule list / calendar / map / status-chip styles to `code/static/css/club_analytics.css`

**Checkpoint**: Tournament discovery works across all three views with filters preserved.

---

## Phase 9: User Story 7 - View tournament results and brackets (Priority: P3)

**Goal**: A results page with medal podium, championship bracket (winners highlighted), final standings, all match scores, and stat leaders — switchable, with unavailable sections clearly marked.

**Independent Test**: Open `/results/{tournament_id}` for a completed tournament with bracket data and confirm podium, bracket rounds with highlighted winners, standings, all-scores, and stat leaders render; a tournament without bracket/leaders shows those sections as unavailable.

### Tests for User Story 7 ⚠️ (write first, must fail)

- [ ] T065 [P] [US7] Contract test for `GET /api/results/{tournament_id}` (podium/bracket/standings/scores/leaders + `data_state`; 404; sections marked unavailable when data missing) in `tests/contract/test_coach_club_api.py`
- [ ] T066 [P] [US7] Integration test for results assembly (podium from `bracket_placements`, bracket from `bracket_matches`, standings from `pool_standings`, scores from `match_results`, leaders from `stat_leaders`) in `tests/integration/test_schedule_queries.py`

### Implementation for User Story 7

- [ ] T067 [US7] Implement results assembly read in `code/services/schedule_queries.py` (podium, bracket grouped by `round_label` with winner flag, standings, all-scores, leaders; graceful "unavailable" when bracket/leaders missing)
- [ ] T068 [US7] Add `GET /api/results/{tournament_id}` endpoint and `/results/{tournament_id}` page route with `logger.info(data_state)` in `code/api.py`
- [ ] T069 [P] [US7] Create results template — medal podium, championship bracket (rounds left→right, winners highlighted), final standings table, all-scores list (winner highlighted), stat leaders (kills/assists/digs or "unavailable"), with bracket/standings/all-scores view switch — in `code/templates/results.html`
- [ ] T070 [US7] Extend `code/static/js/tabs.js` for results bracket/standings/all-scores switching
- [ ] T071 [US7] Add podium / bracket / standings / scores / leaders styles to `code/static/css/club_analytics.css`

**Checkpoint**: Completed tournaments surface full results from stored data.

---

## Phase 10: User Story 8 - Refreshed home and club browsing (Priority: P3)

**Goal**: A hi-fi home dashboard (hero, season stats strip, power rankings, upcoming tournaments, featured coaches) plus an upgraded clubs directory (tier/form/medals + sort/filter) and club profile (tier, medal cabinet, trend, commits, about).

**Independent Test**: Open `/` and confirm hero, stats strip, power rankings, upcoming tournaments, and featured coaches render and link out; open `/clubs` and a club profile and confirm the upgraded sections render.

### Tests for User Story 8 ⚠️ (write first, must fail)

- [ ] T072 [P] [US8] Contract test for home dashboard sections, clubs directory rows (rank/tier/win%/form/teams/medals + sort + tier/name-city filter), and club profile sections (tier/medal cabinet/trend/commits/about) with `data_state`, in `tests/contract/test_coach_club_api.py`

### Implementation for User Story 8

- [ ] T073 [US8] Extend power-rankings, clubs-directory, and club-profile queries to join `club_attributes` (tier, color, medals, commits, est_year, about) and compute form trend, in `code/services/analytics_queries.py`
- [ ] T074 [US8] Add home-dashboard shaping (hero, season stats strip, power rankings, upcoming tournaments via `schedule_queries`, featured coaches via `coach_queries`), clubs-directory rows (tier/form/medals), and club-profile sections (tier/medal cabinet/trend/commits/about) in `code/services/view_models.py`
- [ ] T075 [US8] Enhance `/` (home), `/clubs` (directory with sort rank/win%/teams + filter tier and name/city), and `/clubs/{club_key}` (profile sections) routes in `code/api.py`
- [ ] T076 [P] [US8] Update home template (hero, season stats strip, power-rankings list, upcoming tournaments, featured coaches — each linking to its detail page) in `code/templates/home.html`
- [ ] T077 [P] [US8] Update clubs directory template (rank/name/tier/win%/form trend/teams/medals + sort + tier/name-city filter) in `code/templates/club_rankings.html`
- [ ] T078 [P] [US8] Update club profile template (tier, season stats, season teams, performance trend, medal cabinet, recent commits, about) in `code/templates/club_profile.html`
- [ ] T079 [US8] Add home / tier / medal-cabinet / trend / featured-coach styles to `code/static/css/club_analytics.css`

**Checkpoint**: All eight stories are independently functional and the app presents one coherent amber/navy design system.

---

## Phase 11: Polish & Cross-Cutting Concerns

**Purpose**: Operability, end-to-end abuse-protection verification, docs, and release validation.

- [ ] T080 [P] Add a `/healthz` endpoint in `code/api.py`, switch the container to `gunicorn -k uvicorn.workers.UvicornWorker` with a worker count tuned to the PR-1 pool, and add a compose healthcheck, in `code/Dockerfile` + `compose.yml` (PR-5)
- [ ] T081 [P] Cross-cutting FR-035 gating test in `tests/contract/test_coach_club_api.py` — with `NTVS_WRITE_GATING` on, rate-limit + honeypot reject endorsement/position submissions and write no row, and a missing/invalid `NTVS_DIRECTOR_TOKEN` refuses resolve; with gating off (local) all pass
- [ ] T082 [P] Update `README.md` / feature docs with the new routes and the write-gating env vars (`NTVS_WRITE_GATING`, `NTVS_DIRECTOR_TOKEN`)
- [ ] T083 Run the quickstart.md validation across US1–US8 and confirm every new page renders a meaningful complete/partial/empty state with no error pages (SC-007)
- [ ] T084 Verify migration `004` rollback (drop new tables/columns; revert `layout.html` + `club_analytics.css`) leaves existing tables/views and data intact (quickstart.md Rollback)
- [ ] T085 [P] Verify read pages/endpoints meet p95 < 300ms at current scale (plan Performance Goals)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately.
- **Foundational (Phase 2)**: Depends on Setup — **BLOCKS all user stories**. Within it: T004 → T005 → T006 (schema before seed before apply); T007 → T009 (pool before refactor); T008 needs T007; T010 → T011; others (T012, T013, T014) independent.
- **User Stories (Phases 3–10)**: All depend on Foundational. After it, stories may proceed in parallel (if staffed) or sequentially in priority order P1 → P2 → P2 → P2 → P3…
- **Polish (Phase 11)**: Depends on the desired user stories being complete (T083/T084 need all shipped stories).

### User Story Dependencies

- **US1 (P1)**: Foundational only. No dependency on other stories. **MVP.**
- **US2 (P2)**: Foundational. Surfaces on the US1 coach profile (composer added to `coach_profile.html`); independently testable via the seeded profile + API.
- **US3 (P2)**: Foundational. Shares `coach_commands.py` with US2; feeds US4 (creates requests). Independently testable end-to-end (add position → request).
- **US4 (P2)**: Foundational. Consumes requests from US3 but testable on seeded pending requests alone.
- **US5 (P3)**: Foundational. Touches `club_rankings.html`/`club_profile.html` (shared with US8) for pin controls.
- **US6 (P3)**: Foundational. Shares `schedule_queries.py` (created here) and `tabs.js` with US7.
- **US7 (P3)**: Foundational. Reuses `schedule_queries.py` and `tabs.js`; results assembly draws on existing bracket/standings tables + seeded `stat_leaders`.
- **US8 (P3)**: Foundational. Reuses `coach_queries` (featured coaches) and `schedule_queries` (upcoming) for the home dashboard.

### Within Each User Story

- Tests (contract/integration/unit) are written first and must fail before implementation.
- Order: services/queries → view-model shaping → endpoints/pages (`api.py`) → templates → JS → CSS.
- Complete and validate a story before moving to the next priority.

---

## Parallel Opportunities

- **Setup**: T002 runs alongside T001/T003.
- **Foundational**: T007, T008, T010, T011, T012 are `[P]` (distinct new files); T013 and T014 touch shared layout/CSS so run after or serialized with each other.
- **Across stories**: once Foundational is done, US1–US8 can be staffed in parallel — but every story edits `code/api.py`, `view_models.py`, and `club_analytics.css`, so those touch-points must be merged carefully (see Shared serialization points above).
- **Within a story**: the `[P]`-marked tasks (separate test files, new service modules, new templates, new JS) run together. Example below.

### Parallel Example: User Story 1

```bash
# Tests first (different files):
Task: T015 Contract tests for /api/coaches + /api/coaches/{coach_key} in tests/contract/test_coach_club_api.py
Task: T016 Integration test for coach reads in tests/integration/test_coach_queries.py

# Then independent implementation (different files):
Task: T017 coach_queries.py reads
Task: T020 coaches_directory.html
Task: T021 coach_profile.html
Task: T022 static/js/tabs.js
# T018 (view_models.py), T019 (api.py), T023 (club_analytics.css) serialize on shared files.
```

---

## Implementation Strategy

### MVP First (User Story 1 only)

1. Phase 1: Setup.
2. Phase 2: Foundational (schema/seed/db/identity/gating/theme) — **blocks everything**.
3. Phase 3: US1 — coaches directory + profile (read-only).
4. **STOP and VALIDATE** US1 independently against seeded data; demo.

### Incremental Delivery

- Foundation → US1 (MVP, scout coaches) → US2 (endorse) → US3 (claim) → US4 (verify) completes the coach loop, then US5 (compare) → US6 (schedule) → US7 (results) → US8 (home/clubs refresh). Each story is a deployable increment that doesn't break prior ones.

### Parallel Team Strategy

- After Foundational: one developer drives the coach loop (US1→US2→US3→US4, shared `coach_commands.py`/`coach_queries.py`), a second takes US5 + US8 (shared club templates + `analytics_queries.py`/`view_models.py`), a third takes US6 + US7 (shared `schedule_queries.py`/`tabs.js`). Coordinate merges on `api.py` and `club_analytics.css`.

---

## Notes

- `[P]` = different file, no incomplete-task dependency; `[Story]` maps each task to its user story.
- Tests precede implementation and must fail first (constitution: Test Evidence Before Merge).
- All writes go through `write_conn` and are idempotent (natural-key dedupe / status guards); counts are always derived from rows, never incremented in place (research R6, SC-008).
- Every new read endpoint/page emits `data_state` and a `logger.info` line; writes log applied/no-op (plan: Operability & Traceability).
- Commit after each task or logical group; stop at any checkpoint to validate a story independently.
