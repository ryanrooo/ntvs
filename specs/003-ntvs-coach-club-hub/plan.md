# Implementation Plan: NTVS Coach & Club Hub (NTVS-2 Handoff)

**Branch**: `003-ntvs-coach-club-hub` | **Date**: 2026-05-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-ntvs-coach-club-hub/spec.md`

## Summary

Add a coach scouting + verification layer and upgraded club/tournament browsing to the existing
server-rendered NTVS app, recreating the 10-screen NTVS-2 design handoff. Coaches, coaching positions,
endorsements, and verification requests are net-new persisted entities (seeded/user-generated, kept
separate from the scraped match data). Club and tournament records gain new NTVS-owned presentation
attributes (tier, color, medals, fee, radar dims; schedule date/venue/status). The whole app is
re-themed to the handoff's amber/deep-navy design system.

**Technical approach**: stay on the existing stack — FastAPI app factory + Jinja templates + a single
CSS file + PostgreSQL (`ntvs` schema), with the service-layer split already in place
(`analytics_queries` for SQL, `view_models` for shaping, `*_normalization` for identity). Add a new
additive migration (`004_coach_hub.sql`) plus idempotent seed data, new read/write service modules,
additive API endpoints + pages, six new templates, and light progressive-enhancement JS (the prototype
is React, but the production app is server-rendered, so interactivity — star picker, tone gate, tab/view
switches, club pins — is vanilla JS over server-rendered HTML). No authentication is introduced; write
actions are fully open per the clarified demo posture.

## Technical Context

**Language/Version**: Python 3.10
**Primary Dependencies**: FastAPI 0.97, Jinja2, psycopg2-binary, pydantic<2, uvicorn (existing set — no new runtime deps)
**Storage**: PostgreSQL, schema `ntvs` (additive migration `db/migrations/004_coach_hub.sql` + idempotent seed)
**Testing**: pytest — `tests/unit`, `tests/integration`, `tests/contract` (existing layout)
**Target Platform**: Linux server via Docker Compose; served by uvicorn on :8000
**Project Type**: Web service — server-rendered pages (Jinja) + parallel read-only JSON API + new write endpoints
**Performance Goals**: Read pages/endpoints p95 < 300ms at current scale (consistent with existing analytics pages); no heavy compute introduced
**Constraints**: No new runtime dependencies; client-side interactivity must be progressive enhancement (page works without JS for reads); writes must be idempotent
**Scale/Scope**: ~84 clubs, ~600 teams, ~1.2k coaches (seeded), ~9k matches; 10 screens, ~6 new templates, ~10 new endpoints

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Canonical Data Integrity**:
  - New entities: `coaches`, `coach_positions`, `endorsements`, `verification_requests`; new
    presentation attributes for clubs (`club_attributes`) and tournaments (`tournament_schedule`),
    plus `stat_leaders` for results.
  - **Source of truth**: coach/endorsement/verification data is user-generated/seeded and owned by
    NTVS — explicitly NOT derived from or written back into the scraped `match_results`/
    `pool_standings`/`bracket_*` tables, which remain the single source of truth for club/tournament
    performance. Coach career totals are stored fields (per clarification), not computed from matches.
  - **Identity**: coaches get stable keys via a `coach_normalization` module mirroring the existing
    `club_normalization` (slug + collision_rank), so identically named coaches stay distinct.
    Coach→club links use the existing canonical `club_key`; presentation tables key on `club_key` /
    `tournament_id` so there is no second identifier for the same entity.
  - **Duplicate handling**: surrogate ids for endorsements/requests; idempotent seed via
    `ON CONFLICT DO NOTHING/UPDATE`; write endpoints dedupe (see idempotency below).
- **Idempotent Pipeline Slices**:
  - No ETL/Airflow/scraper steps change in this feature, so pipeline replay behavior is unaffected.
  - Migration `004` is rerun-safe: `CREATE TABLE IF NOT EXISTS`, `ADD COLUMN IF NOT EXISTS`,
    `CREATE OR REPLACE VIEW`; seed uses `ON CONFLICT`. Re-applying produces no duplicates.
  - Write endpoints are retry-safe: verification resolve guards on current status (re-resolving a
    decided/missing request is a no-op); position add is keyed to avoid duplicate (coach, club, role,
    years); endorsement insert dedupes on (coach_id, author, body) within the same day. Counts
    (avg rating, endorsement count, verified count) are derived from rows, never incremented in place.
  - **Write correctness depends on transactional, row-locked access** (see Production Readiness PR-1/
    PR-2): the existing `fetch_with_connection` helper never commits and would silently roll back
    writes, and the status guard on verification resolve must hold a `SELECT … FOR UPDATE` lock so two
    concurrent approvals cannot both pass. These are prerequisites for the write stories, not optional.
- **Contracted Interfaces & Compatibility**:
  - All new endpoints are additive. The one change to an existing contract — `/api/clubs/compare` —
    stays backward compatible: it continues to accept `club_a`/`club_b` and additionally accepts a
    repeatable `clubs` param (2–4). Documented in `contracts/coach-club-api.yaml`.
  - Schema migration `004` is additive only (new tables; new columns are nullable / defaulted);
    existing queries and the `club_*` views are unaffected. Rollback = drop the new tables/columns.
  - No new environment variables. No file-format changes.
- **Test Evidence Before Merge**:
  - Unit: `coach_normalization` (collision keys), `endorsement_policy` (rating floor + tone-gate
    regex, including borderline cases), compare best-value/`dir=-1` fee logic, profile-strength
    formula, schedule filter logic.
  - Integration: new read queries and idempotent write commands against a Postgres test DB
    (add/resolve verification flips verified state once; duplicate endorsement is a no-op).
  - Contract: new endpoints + page renders return expected shape and `data_state`; `/api/clubs/compare`
    still honors `club_a`/`club_b`.
- **Operability & Traceability**:
  - Every new endpoint emits a `logger.info` line mirroring the existing pattern, including the
    `data_state.completeness` for reads and the action + idempotency outcome (applied/no-op) for
    writes, preserving traceability from request → stored rows → rendered response.
  - Production operability gaps (connection pooling, worker model, healthcheck, log durability,
    write-endpoint exposure) are tracked in **Production Readiness** below so they become tasks rather
    than launch-day surprises.

**Result**: PASS — no violations. The write path adds prerequisites (transactional/pooled access,
row-locking) captured under Production Readiness. Complexity Tracking left empty.

## Project Structure

### Documentation (this feature)

```text
specs/003-ntvs-coach-club-hub/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── coach-club-api.yaml   # Phase 1 output (new + changed endpoints)
├── checklists/
│   └── requirements.md  # from /speckit.specify
└── tasks.md             # /speckit.tasks (NOT created here)
```

### Source Code (repository root)

```text
db/
├── init.sql                         # (unchanged baseline)
└── migrations/
    ├── 002_club_analytics.sql       # (existing)
    ├── 003_bracket_tables.sql       # (existing)
    ├── 004_coach_hub.sql            # NEW: coaches, coach_positions, endorsements,
    │                                #      verification_requests, club_attributes,
    │                                #      tournament_schedule, stat_leaders (+ views)
    └── 004_seed_coach_hub.sql       # NEW: idempotent demo seed (coaches/clubs/schedule)

code/
├── api.py                           # CHANGED: new read+write endpoints & pages; compare→N clubs;
│                                    #          pooled+transactional connection helpers (PR-1)
├── services/
│   ├── db.py                        # NEW (PR-1): connection pool + read/write context managers
│   │                                #   (write ctx commits/rolls back; read ctx is read-only)
│   ├── rate_limit.py                # NEW (PR-3, prod-gated): in-process per-IP limiter + write gating
│   ├── analytics_queries.py         # CHANGED: club attrs, power rankings, N-club compare, stat leaders
│   ├── view_models.py               # CHANGED: club/tournament presentation shaping, radar normalization
│   ├── club_normalization.py        # (unchanged)
│   ├── coach_normalization.py       # NEW: stable coach identity (slug + collision_rank)
│   ├── coach_queries.py             # NEW: coach directory/profile, director queue (reads)
│   ├── coach_commands.py            # NEW: writes in a single transaction; verification resolve uses
│   │                                #   SELECT … FOR UPDATE on the request row (PR-2)
│   ├── endorsement_policy.py        # NEW: rating floor + deterministic tone gate
│   └── schedule_queries.py          # NEW: tournament schedule + results assembly
├── templates/
│   ├── layout.html                  # CHANGED: nav (Coaches/Schedule), re-theme hooks
│   ├── home.html                    # CHANGED: hero/rankings/featured (hi-fi)
│   ├── club_rankings.html           # CHANGED: tiers, form, medals, pin toggle
│   ├── club_profile.html            # CHANGED: medal cabinet, trend, commits, pin
│   ├── club_comparison.html         # CHANGED: up to 4 clubs + radar + best-value
│   ├── coaches_directory.html       # NEW
│   ├── coach_profile.html           # NEW (tabs + endorsements composer)
│   ├── coach_editor.html            # NEW (stepper + live preview)
│   ├── director.html                # NEW (verification queue)
│   ├── schedule.html                # NEW (list/calendar/map)
│   └── results.html                 # NEW (podium/bracket/standings/scores/leaders)
└── static/
    ├── css/
    │   └── club_analytics.css       # CHANGED: re-theme to amber/navy token system
    └── js/
        ├── pins.js                  # NEW: club-pin cookie + toggle UI sync
        ├── endorse.js               # NEW: star picker + live tone gate + char counter
        ├── tabs.js                  # NEW: tab/view switching (coach tabs, schedule views, results tabs)
        └── editor.js                # NEW: live résumé preview + profile-strength meter

tests/
├── unit/
│   ├── test_coach_normalization.py  # NEW
│   ├── test_endorsement_policy.py   # NEW
│   └── test_compare_metrics.py      # NEW (best-value + fee dir=-1 + profile strength)
├── integration/
│   ├── test_coach_queries.py        # NEW
│   ├── test_coach_commands.py       # NEW (idempotent writes; concurrent-resolve applies once — PR-2)
│   ├── test_db_helpers.py           # NEW (PR-1: write ctx commits, error rolls back, pool reuse)
│   └── test_schedule_queries.py     # NEW
└── contract/
    └── test_coach_club_api.py       # NEW (endpoints + page renders + data_state + compare compat)
```

**Structure Decision**: Reuse the existing pipeline/API layout exactly — the constitution requires the
`dags/` (orchestration) ÷ `code/` (app) ÷ `db/` (schema) separation, and this feature lives entirely in
`code/` + `db/` + `tests/`. The service split (queries / view_models / normalization) is extended with
parallel coach modules rather than overloading existing files, keeping read vs. write and analytics vs.
coach concerns isolated. A new `code/static/js/` is populated (previously empty) for progressive
enhancement.

## Production Readiness

A review of the existing stack surfaced gaps that matter once this runs in production — especially
because this feature is the first to introduce **write** endpoints, and the clarified target is
**public production from day one**. Items are split into **In-Scope** (correctness/security
prerequisites that become tasks in this feature) and **Platform Hardening** (a tracked backlog, with the
critical subset pulled into scope per the clarification). Severity: 🔴 blocker for prod, 🟠 important,
🟡 advisable.

### In-scope for this feature (write-path correctness & safety)

| ID | Finding (evidence) | Planned change | Sev |
|----|--------------------|----------------|-----|
| **PR-1** | New DB connection per request and `fetch_with_connection` **never commits** ([code/api.py:48-53](../../code/api.py#L48-L53)); a fresh connect per call ([code/api.py:39-45](../../code/api.py#L39-L45)). psycopg2 opens a transaction, so `close()` rolls writes back. | Add `code/services/db.py`: a `ThreadedConnectionPool` plus `read_conn()` / `write_conn()` context managers (write commits on success, rolls back on exception, returns connection to pool). Route reads/writes through it; keep `fetch_with_connection` as a thin read shim for back-compat. | 🔴 |
| **PR-2** | Verification resolve / endorsement / position writes guard on a status or natural key without locking — two concurrent requests can both pass the check (double-verify, dup row). | In `coach_commands.py`, run each write in one `write_conn()` transaction; verification resolve does `SELECT … FOR UPDATE` on the request row before deciding; rely on UNIQUE constraints (data-model dedupe keys) as the second line. Integration test asserts concurrent approve applies exactly once. | 🔴 |
| **PR-3** | Public-production target with open write endpoints is a spam / fake-verification / defacement vector (FR-035). | Add `code/services/rate_limit.py`: a config-gated (`NTVS_WRITE_GATING`) per-IP rate limiter + honeypot on endorsement/position POSTs and a shared-token check (`NTVS_DIRECTOR_TOKEN`) on director resolve. **ON by default in production, OFF for local/demo** (clarified). Throttled/rejected requests return a clear message and persist nothing. | 🔴 |
| **PR-4** | Local `email_validator.py` shim + fake `*.dist-info/` shadow the real `email-validator` dependency ([email_validator.py](../../email_validator.py)); near-zero validation, masks import issues. | Remove the shim and the stray dist-info; rely on the pinned `email-validator` dependency. Adds no scope but removes a foot-gun. | 🟡 |

### Platform hardening

**Clarified scope (2026-05-29):** target is **public production from day one**, so a critical subset is
**in-scope for this feature** — PR-5 (below) joins PR-1/PR-2/PR-4. The remainder (PR-6–PR-9) is a
tracked **hardening backlog** to complete before/around launch, not in this feature's task list.

| ID | Finding (evidence) | Recommendation | Sev | Scope |
|----|--------------------|----------------|-----|-------|
| **PR-5** | Single sync worker: `CMD ["python", "api.py"]` → `uvicorn.run(app)` ([code/Dockerfile:21](../../code/Dockerfile#L21)); no `api` healthcheck ([compose.yml](../../compose.yml)). | Run via `gunicorn -k uvicorn.workers.UvicornWorker` with N workers; add a `/healthz` endpoint + compose healthcheck. Tune worker count against pool size from PR-1. | 🔴 | **In feature** |
| **PR-6** | Migrations are hand-run `.sql`; `init.sql` only executes on an empty volume — no applied-state tracking, ordering, or rollback. | Adopt a migration runner (Alembic, or a tiny `schema_migrations` table + ordered runner). Make `004` the first migration under it. | 🟠 | Backlog |
| **PR-7** | Aging/loose deps: `fastapi==0.97.0`, `pydantic<2`, unpinned `psycopg2-binary` ([requirements.txt](../../requirements.txt)). | Plan a deliberate upgrade to FastAPI + pydantic v2; pin all versions; use `psycopg2` (source) or `psycopg[binary]` v3 in the image. Do as its own change, not inside this feature. | 🟠 | Backlog |
| **PR-8** | Adminer DB UI exposed on `:8080` with no boundary; Airflow seeded `admin/admin`; no TLS/reverse proxy; file logs in-container are lost on recreation. | For prod: drop/firewall Adminer, set real Airflow creds via secrets, terminate TLS at a reverse proxy (nginx/traefik), ship logs to stdout→collector or a mounted volume. | 🟠 | Backlog |
| **PR-9** | No Postgres backup/restore strategy noted for the data volume. | Define scheduled `pg_dump`/snapshot + a tested restore before launch. | 🟡 | Backlog |

**Write posture (locked by clarify, 2026-05-29):** the deployment target is public production from day
one, so PR-3 gating ships **enabled in production** (config-gated OFF for local/demo). This supersedes
the original "fully open (demo)" clarification and is now reflected in spec FR-035 and the spec
Assumptions — no open question remains here.

### Constitution alignment

PR-1/PR-2 reinforce **Idempotent Pipeline Slices** (retry-safe, lock-guarded writes) and
**Contracted Interfaces** (the pooled helper preserves existing read behavior). PR-5/PR-8/PR-9 serve
**Operability & Traceability** (durable logs, healthchecks, recoverable data). None introduces a
constitution violation; they close gaps the principles already imply.

## Complexity Tracking

> No constitution violations. No entries required.
