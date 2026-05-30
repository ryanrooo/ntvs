# Implementation Plan: Stitch-Matched Club Analytics Experience

**Branch**: `002-stitch-club-analytics` | **Date**: 2026-03-22 | **Spec**: [/Users/ryannguyen/Documents/projects/ntvs/specs/002-stitch-club-analytics/spec.md](/Users/ryannguyen/Documents/projects/ntvs/specs/002-stitch-club-analytics/spec.md)
**Input**: Feature specification from `/specs/002-stitch-club-analytics/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Build a Stitch-matched NTVS web experience on top of the existing FastAPI and
PostgreSQL stack by adding data-backed homepage, Saturday pool results, club ranking and
profile, and club comparison views. The implementation will preserve the exported page
hierarchy from `stitch_ntvs`, expose dedicated analytics endpoints from the current API
service, and introduce collision-safe club alias mapping so club-level aggregation,
head-to-head history, and pool-day summaries stay deterministic and rerunnable even when
multiple source club names normalize to the same slug candidate.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: FastAPI, Uvicorn, psycopg2-binary, python-dotenv, Jinja2,
pytest, existing Stitch-exported HTML/CSS assets adapted into the app  
**Storage**: PostgreSQL 15 in schema `ntvs`  
**Testing**: pytest for API, query, and HTML response validation; SQL-backed integration
tests for aggregation, slug-collision resolution, and head-to-head logic  
**Target Platform**: Docker Compose local stack with FastAPI service on Linux container  
**Project Type**: Data-backed web service serving analytics pages and JSON endpoints  
**Performance Goals**: Primary analytics pages and backing endpoints should return
usable content for typical single-tournament or single-club requests in under 2 seconds
in the local containerized environment  
**Constraints**: Must preserve real-data fidelity, keep ETL and migration reruns safe,
avoid breaking existing tournament endpoints, and limit first-release analytics to
metrics derivable from current stored results  
**Scale/Scope**: Four user-facing pages, several read-only analytics endpoints, stable
club alias mapping, collision-safe key assignment, and validation against current
regional tournament data

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Canonical Data Integrity**: Pass. Source-of-truth remains the existing `tournaments`,
  `teams`, `pools`, `pool_standings`, and `match_results` tables. The design adds a
  deterministic `club_aliases` mapping layer that preserves original source club names
  while assigning unique stable club identities.
- **Idempotent Pipeline Slices**: Pass. Existing ETL rerun safety must be preserved.
  Collision-safe club alias generation and derived views must be recomputed in a
  deterministic way so retries and reapplication do not create unique-constraint
  failures or identity drift.
- **Contracted Interfaces & Compatibility**: Pass with explicit contract updates. The
  feature adds new read-only page and JSON interfaces while preserving current `/` and
  `/tournaments` behavior. The club identity contract now explicitly guarantees stable
  unique `club_key` values even when multiple source club names share the same slug
  candidate.
- **Test Evidence Before Merge**: Pass. Plan includes unit tests for normalization and
  slug-collision resolution, integration tests for SQL aggregation and head-to-head
  results, and endpoint/page tests for rendered outputs and no-placeholder behavior.
- **Operability & Traceability**: Pass. New analytics handlers will log request context,
  selected filters, and partial-data conditions. Club alias mapping and derived metrics
  will remain traceable back to original source club names, tournament rows, and match
  rows.

## Project Structure

### Documentation (this feature)

```text
specs/002-stitch-club-analytics/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── analytics-api.yaml
└── tasks.md
```

### Source Code (repository root)

```text
code/
├── api.py
├── extract.py
├── load_data.py
├── static/
│   ├── css/
│   ├── js/
│   └── images/
├── templates/
│   ├── layout.html
│   ├── home.html
│   ├── saturday_pool_results.html
│   ├── club_rankings.html
│   ├── club_profile.html
│   └── club_comparison.html
└── services/
    ├── analytics_queries.py
    ├── club_normalization.py
    └── view_models.py

db/
├── init.sql
└── migrations/
    └── 002_club_analytics.sql

tests/
├── contract/
│   └── test_analytics_api.py
├── integration/
│   └── test_club_analytics_queries.py
└── unit/
    └── test_club_normalization.py
```

**Structure Decision**: Keep the existing single FastAPI service and extend it with a
small service layer plus server-rendered templates and static assets. Add `db/migrations`
for controlled schema evolution and explicit club alias behavior instead of spreading DDL
changes across unrelated files.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Add `code/templates` and `code/services` directories | The feature introduces multiple pages and shared analytics logic that need separation from the current single-file API | Keeping all HTML rendering and SQL in `code/api.py` would make club aggregation, slug-collision handling, page rendering, and testing brittle |
| Add migration file alongside `db/init.sql` | Existing schema needs an explicit evolution path for club aliases, collision-safe key assignment, and derived analytics views | Editing only `db/init.sql` would not document upgrade order or support safe reapplication in existing environments |
