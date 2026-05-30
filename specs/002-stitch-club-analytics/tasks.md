# Tasks: Stitch-Matched Club Analytics Experience

**Input**: Design documents from `/specs/002-stitch-club-analytics/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Include the automated and manual verification tasks required by the
constitution. If behavior, data contracts, orchestration, or API responses change,
corresponding tests are REQUIRED unless the plan explicitly documents why automation is
not feasible.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **NTVS default**: `code/`, `dags/`, `db/`, `tests/` at repository root
- **Extended app split**: add feature-specific directories only if justified in plan.md
- Paths shown below assume the default NTVS layout - adjust only when the plan requires it

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create feature directories and placeholder modules in `code/templates/`, `code/services/`, `db/migrations/`, `tests/unit/`, `tests/integration/`, and `tests/contract/`
- [X] T002 Add implementation dependencies and test tooling updates in `requirements.txt`
- [X] T003 [P] Add shared FastAPI template/static configuration scaffolding in `code/api.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create analytics schema migration with deterministic club alias collision handling in `db/migrations/002_club_analytics.sql`
- [X] T005 Update bootstrap schema support for collision-safe analytics objects in `db/init.sql`
- [X] T006 [P] Implement deterministic club normalization and stable slug-collision resolution helpers in `code/services/club_normalization.py`
- [X] T007 [P] Implement shared analytics query layer for tournaments, clubs, alias mapping, standings, and head-to-head data in `code/services/analytics_queries.py`
- [X] T008 [P] Implement shared page/API response mappers, including alias metadata, in `code/services/view_models.py`
- [X] T009 Add analytics contract routes and common no-data handling in `code/api.py`
- [X] T010 [P] Add unit coverage for club normalization and collision resolution rules in `tests/unit/test_club_normalization.py`
- [X] T011 [P] Add integration coverage for analytics query primitives and rerunnable alias mapping in `tests/integration/test_club_analytics_queries.py`
- [X] T012 [P] Add contract coverage for analytics endpoints and alias metadata in `tests/contract/test_analytics_api.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Browse Tournament and Pool Results (Priority: P1) 🎯 MVP

**Goal**: Deliver the homepage and Saturday pool results experience with real tournament, pool, standings, and match data

**Independent Test**: Open the homepage and pool results page, apply filters, and verify that featured tournament content, pool standings, and pool matchup summaries update correctly from stored data

### Tests for User Story 1 ⚠️

- [X] T013 [P] [US1] Extend contract tests for `/api/home` and `/api/pool-results` in `tests/contract/test_analytics_api.py`
- [X] T014 [P] [US1] Add integration tests for homepage spotlight and pool filter queries in `tests/integration/test_club_analytics_queries.py`

### Implementation for User Story 1

- [X] T015 [P] [US1] Implement homepage tournament and featured pool query functions in `code/services/analytics_queries.py`
- [X] T016 [P] [US1] Implement pool-results filter, standings, and matchup view models in `code/services/view_models.py`
- [X] T017 [US1] Add homepage and pool-results API handlers in `code/api.py`
- [X] T018 [P] [US1] Create shared layout and homepage template in `code/templates/layout.html` and `code/templates/home.html`
- [X] T019 [P] [US1] Create Saturday pool results template in `code/templates/saturday_pool_results.html`
- [X] T020 [P] [US1] Add shared Stitch-aligned styling assets for homepage and pool results in `code/static/css/club_analytics.css`
- [X] T021 [US1] Wire navigation and filter form behavior for homepage-to-pool drill-down in `code/api.py`
- [X] T022 [US1] Add partial-data and no-results states for homepage and pool results in `code/templates/home.html` and `code/templates/saturday_pool_results.html`

**Checkpoint**: User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Evaluate Club Performance and Profiles (Priority: P2)

**Goal**: Deliver club search, rankings, and profile views with aggregated club/team performance and explicit stable club identities

**Independent Test**: Search for a known club, open the club rankings view and the club profile view, and verify that grouped teams, aggregate metrics, alias metadata, and recent activity are consistent with stored results

### Tests for User Story 2 ⚠️

- [X] T023 [P] [US2] Extend contract tests for `/api/clubs` and `/api/clubs/{club_key}` in `tests/contract/test_analytics_api.py`
- [X] T024 [P] [US2] Add integration tests for club ranking, profile aggregation, and collision-safe alias lookup in `tests/integration/test_club_analytics_queries.py`

### Implementation for User Story 2

- [X] T025 [P] [US2] Implement club ranking, search, alias lookup, and profile aggregation queries in `code/services/analytics_queries.py`
- [X] T026 [P] [US2] Implement club ranking rows, alias metadata, profile summaries, and team performance view models in `code/services/view_models.py`
- [X] T027 [US2] Add club rankings and club profile API/page handlers in `code/api.py`
- [X] T028 [P] [US2] Create club rankings template in `code/templates/club_rankings.html`
- [X] T029 [P] [US2] Create club profile template in `code/templates/club_profile.html`
- [X] T030 [US2] Add club search, sort, and empty-state behavior in `code/templates/club_rankings.html` and `code/api.py`
- [X] T031 [US2] Add profile partial-data messaging, alias metadata, and recent activity sections in `code/templates/club_profile.html`

**Checkpoint**: User Stories 1 and 2 should both work independently

---

## Phase 5: User Story 3 - Compare Clubs Side by Side (Priority: P3)

**Goal**: Deliver side-by-side club comparison with normalized metrics and direct matchup history

**Independent Test**: Select two clubs with known results, open the comparison page, and verify that the view shows consistent metrics for both clubs plus correct direct head-to-head history or an explicit no-history state

### Tests for User Story 3 ⚠️

- [X] T032 [P] [US3] Extend contract tests for `/api/clubs/compare` in `tests/contract/test_analytics_api.py`
- [X] T033 [P] [US3] Add integration tests for head-to-head and comparison metric queries in `tests/integration/test_club_analytics_queries.py`

### Implementation for User Story 3

- [X] T034 [P] [US3] Implement club comparison and head-to-head queries using resolved `club_key` identities in `code/services/analytics_queries.py`
- [X] T035 [P] [US3] Implement comparison metric and matchup-history view models in `code/services/view_models.py`
- [X] T036 [US3] Add club comparison API/page handler in `code/api.py`
- [X] T037 [P] [US3] Create club comparison template in `code/templates/club_comparison.html`
- [X] T038 [US3] Add club selector, side-by-side metric panels, and no-history state handling in `code/templates/club_comparison.html` and `code/api.py`

**Checkpoint**: User Stories 1, 2, and 3 should all be independently functional

---

## Phase 6: User Story 4 - Preserve the Exported Page Experience (Priority: P4)

**Goal**: Bring the implemented pages into close structural and visual alignment with the exported Stitch references

**Independent Test**: Compare each implemented page to the exported HTML and screenshots in `stitch_ntvs` and verify that the same primary layout regions, hierarchy, callouts, and navigation intent are present while using real data

### Tests for User Story 4 ⚠️

- [X] T039 [P] [US4] Add page response tests for exported-page coverage and no-placeholder rendering in `tests/contract/test_analytics_api.py`

### Implementation for User Story 4

- [X] T040 [P] [US4] Adapt shared editorial visual system from Stitch exports into `code/static/css/club_analytics.css`
- [X] T041 [P] [US4] Align homepage structure and spotlight sections with `stitch_ntvs/ntvs_homepage/code.html` in `code/templates/home.html`
- [X] T042 [P] [US4] Align Saturday pool results layout with `stitch_ntvs/saturday_pool_results/code.html` in `code/templates/saturday_pool_results.html`
- [X] T043 [P] [US4] Align club rankings/profile layout with `stitch_ntvs/club_rankings_profiles/code.html` in `code/templates/club_rankings.html` and `code/templates/club_profile.html`
- [X] T044 [P] [US4] Align club comparison layout with `stitch_ntvs/club_comparison_tool/code.html` in `code/templates/club_comparison.html`
- [X] T045 [US4] Replace any remaining sample-only content with real-data fallbacks across `code/templates/*.html`

**Checkpoint**: All user stories should now be independently functional and visually aligned with the exported references

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T046 [P] Add request logging and partial-data trace logging for analytics routes in `code/api.py`
- [X] T047 Verify rollback, refresh, and slug-collision rerun procedure for analytics schema objects in `db/migrations/002_club_analytics.sql` and `specs/002-stitch-club-analytics/quickstart.md`
- [X] T048 [P] Document runtime validation and feature walkthrough in `specs/002-stitch-club-analytics/quickstart.md`
- [X] T049 Run quickstart validation and record any required corrections in `specs/002-stitch-club-analytics/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - blocks all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational completion - defines MVP
- **User Story 2 (Phase 4)**: Depends on Foundational completion and reuses club normalization and alias foundations
- **User Story 3 (Phase 5)**: Depends on Foundational completion and benefits from club aggregation delivered in User Story 2
- **User Story 4 (Phase 6)**: Depends on the corresponding functional stories being implemented so the visual pass maps to real data
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational - no dependency on later stories
- **User Story 2 (P2)**: Can start after Foundational - shares foundations with US1 but remains independently testable
- **User Story 3 (P3)**: Depends conceptually on club aggregation from US2 for normalized comparisons
- **User Story 4 (P4)**: Depends on implemented US1-US3 pages to finalize Stitch parity against live data

### Within Each User Story

- Contract and integration tests for the story should be added before or alongside implementation and must fail before final completion when feasible
- Query logic before handler wiring
- Handler wiring before template integration
- Template behavior before empty-state and navigation polish
- Story validation before moving to the next priority

### Parallel Opportunities

- T002 and T003 can run in parallel after T001
- T004 and T005 should stay sequential, while T006, T007, and T008 can run in parallel after schema direction is set
- T010, T011, and T012 can run in parallel once the foundational contracts are stable
- Within US1, T015, T016, T018, T019, and T020 can run in parallel
- Within US2, T025, T026, T028, and T029 can run in parallel
- Within US3, T034, T035, and T037 can run in parallel
- Within US4, T040 through T044 can run in parallel once the functional pages exist

---

## Parallel Example: User Story 2

```bash
# Launch User Story 2 test coverage together:
Task: "Extend contract tests for /api/clubs and /api/clubs/{club_key} in tests/contract/test_analytics_api.py"
Task: "Add integration tests for club ranking, profile aggregation, and collision-safe alias lookup in tests/integration/test_club_analytics_queries.py"

# Launch User Story 2 implementation slices together:
Task: "Implement club ranking, search, alias lookup, and profile aggregation queries in code/services/analytics_queries.py"
Task: "Implement club ranking rows, alias metadata, profile summaries, and team performance view models in code/services/view_models.py"
Task: "Create club rankings template in code/templates/club_rankings.html"
Task: "Create club profile template in code/templates/club_profile.html"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. Stop and validate homepage and Saturday pool results against real data
5. Demo the MVP before starting club-focused stories

### Incremental Delivery

1. Complete Setup and Foundational work
2. Deliver User Story 1 for homepage and pool results
3. Add User Story 2 for club rankings and club profiles with stable alias handling
4. Add User Story 3 for side-by-side comparison and head-to-head history
5. Finish User Story 4 to match the exported Stitch page experience
6. Run cross-cutting validation and polish

### Parallel Team Strategy

1. One developer handles schema/query foundations while another prepares templates/static assets
2. After foundations complete:
   - Developer A: homepage and pool results
   - Developer B: club rankings and profiles
   - Developer C: comparison experience
3. Final pass aligns all pages with Stitch exports and validates contracts

---

## Notes

- Total tasks: 49
- User Story task counts:
  - US1: 10 tasks
  - US2: 9 tasks
  - US3: 7 tasks
  - US4: 7 tasks
- Suggested MVP scope: Phase 1, Phase 2, and User Story 1
- All tasks follow the required checklist format with task ID, optional parallel marker, required story label in story phases, and explicit file paths
