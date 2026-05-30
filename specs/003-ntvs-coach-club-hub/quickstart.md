# Quickstart: NTVS Coach & Club Hub

How to bring up the feature locally and verify each user story. Assumes the existing Docker Compose
Postgres + uvicorn workflow.

## 1. Apply schema + seed

```bash
# new additive migration + idempotent demo seed (rerun-safe)
psql "$DATABASE_URL" -f db/migrations/004_coach_hub.sql
psql "$DATABASE_URL" -f db/migrations/004_seed_coach_hub.sql
```

Both files are safe to re-run: tables use `IF NOT EXISTS`, columns `ADD COLUMN IF NOT EXISTS`, seed uses
`ON CONFLICT DO NOTHING/UPDATE`. No existing tables/views are modified.

## 2. Run the app

```bash
docker compose up        # or: cd code && uvicorn api:app --reload --port 8000
```

## 3. New routes

| Page | Route | API |
|------|-------|-----|
| Coaches directory | `/coaches` | `GET /api/coaches?q=&verified_only=` |
| Coach profile | `/coaches/{coach_key}` | `GET /api/coaches/{coach_key}` |
| Coach editor | `/coaches/{coach_key}/edit` | `POST .../positions`, `POST .../verification-requests` |
| Director dashboard | `/director?club_key=` | `GET /api/director/requests`, `POST .../resolve` |
| Schedule | `/schedule` | `GET /api/schedule?open_only=&month=&within_mi=` |
| Results | `/results/{tournament_id}` | `GET /api/results/{tournament_id}` |
| Compare (now ≤4) | `/compare?clubs=a&clubs=b&clubs=c` | `GET /api/clubs/compare?clubs=...` |
| Endorse (POST) | (on coach profile) | `POST /api/coaches/{coach_key}/endorsements` |

## 4. Verify by user story

**US1 — Scout coaches**: open `/coaches`, search a name, toggle "Verified only", open a profile; confirm
résumé tabs, verification badge, and that the club link routes to `/clubs/{club_key}`.

**US2 — Endorsement (positive-only)**:
```bash
# accepted
curl -X POST localhost:8000/api/coaches/<key>/endorsements -H 'Content-Type: application/json' \
  -d '{"author_label":"Parent of an OH","relationship":"Parent","stars":5,"tags":["Development"],"body":"Fantastic with the girls."}'
# rejected — rating floor
curl -i ... -d '{"...","stars":3,"body":"ok"}'        # → 422 rating_too_low
# rejected — tone gate
curl -i ... -d '{"...","stars":5,"body":"the worst"}' # → 422 negative_tone
```
Re-running the accepted call the same day returns the existing row (idempotent), and the coach's
`rating`/`endorse_count` reflect it once.

**US3 — Claim/build résumé**: on `/coaches/{key}/edit`, add a position (club+role required), watch the
live preview + profile-strength meter update, then submit a verification request.

**US4 — Director verify**:
```bash
curl localhost:8000/api/director/requests?club_key=<club>          # see pending
curl -X POST localhost:8000/api/director/requests/<id>/resolve -d '{"decision":"approve"}'
curl -X POST localhost:8000/api/director/requests/<id>/resolve -d '{"decision":"approve"}'  # applied:false (idempotent)
```
After approve, the coach shows verified everywhere.

**US5 — Compare ≤4 + radar**: pin clubs from `/clubs` (cookie `ntvs_pins`), open `/compare`; confirm the
metrics table marks best per row (and lowest fee), the radar overlays each club, and a 5th pin is
refused. Legacy `?club_a=&club_b=` still works.

**US6 — Schedule**: `/schedule` — switch list/calendar/map, apply month + open-only filters, confirm the
"N tournaments · N teams" count updates and a completed event links to results.

**US7 — Results**: `/results/{tournament_id}` — podium, bracket (winners highlighted), standings, all
scores, stat leaders; a tournament with no bracket/leaders shows those sections as unavailable.

**US8 — Home & clubs refresh**: `/` and `/clubs` render the re-themed hi-fi layout (hero, power
rankings, tiers, medals, trends).

## 5. Tests

```bash
pytest tests/unit/test_coach_normalization.py tests/unit/test_endorsement_policy.py \
       tests/unit/test_compare_metrics.py \
       tests/integration/test_coach_queries.py tests/integration/test_coach_commands.py \
       tests/integration/test_schedule_queries.py \
       tests/contract/test_coach_club_api.py
```

Key assertions: tone gate + rating floor reject correctly (SC-002); duplicate writes are no-ops
(SC-008); approve flips verified exactly once; `/api/clubs/compare` honors both `club_a/b` and `clubs`;
every new endpoint returns a `data_state`.

## 6. Design re-theme check

`code/static/css/club_analytics.css` `:root` now maps to amber/navy tokens; existing pages pick up the
new look via the shared CSS variables. Fonts load Bricolage Grotesque / IBM Plex Sans / JetBrains Mono.

## Rollback

Drop the new tables and added columns (migration `004` down): `coaches`, `coach_positions`,
`endorsements`, `verification_requests`, `club_attributes`, `tournament_schedule`, `stat_leaders`.
Revert `club_analytics.css` and `layout.html`. No existing data is touched, so rollback is clean.
