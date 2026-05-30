# Quickstart: Stitch-Matched Club Analytics Experience

## Prerequisites

- Docker Desktop
- A populated `.env` file matching `compose.yml`
- Sample NTVS tournament data loaded into PostgreSQL

## 1. Start the local stack

```bash
docker compose up --build
```

Expected services:
- API on `http://localhost:8000`
- Adminer on `http://localhost:8080`
- Airflow on `http://localhost:8081`

## 2. Verify canonical data exists

Open Adminer or connect to PostgreSQL and confirm the following tables in schema
`ntvs` have rows:

- `tournaments`
- `teams`
- `pools`
- `pool_standings`
- `match_results`

## 3. Apply analytics schema additions

Run the feature migration after the base schema is present:

```bash
psql "$DATABASE_URL" -f db/migrations/002_club_analytics.sql
```

If you are using the default Docker Compose database from this repository, the equivalent
command is:

```bash
PGPASSWORD="$POSTGRES_PASSWORD" psql -h localhost -p 5433 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f db/migrations/002_club_analytics.sql
```

If the implementation uses derived tables or views, refresh them after loading data.

After the migration, verify collision-safe club alias assignment:

```bash
psql "$DATABASE_URL" -c "SELECT source_club_name, club_key, normalization_status FROM ntvs.club_aliases ORDER BY club_key;"
```

If known slug collisions exist, confirm that:

- each original source club name still appears in `club_aliases`
- each colliding source name has a unique stable `club_key`
- rerunning the migration does not produce a unique-constraint failure
- rerunning the migration preserves the same `club_key` for each `source_club_name`

## 4. Exercise the new analytics contracts

Example requests:

```bash
curl "http://localhost:8000/api/home"
curl "http://localhost:8000/api/pool-results?tournament_id=<id>&division=17U%20Open"
curl "http://localhost:8000/api/clubs?q=Drive"
curl "http://localhost:8000/api/clubs/<club_key>"
curl "http://localhost:8000/api/clubs/compare?club_a=<club_a>&club_b=<club_b>"
```

## 5. Validate the Stitch-matched pages

Open the production pages in a browser and compare them against the exported references
in `stitch_ntvs`:

- Homepage
- Saturday pool results
- Club rankings/profile
- Club comparison

Check that:

- each page is populated from real NTVS data
- filters and drill-down navigation work
- no-data and partial-data states are explicit
- club head-to-head summaries match underlying results

## 6. Run verification tests

```bash
pytest tests/unit/test_club_normalization.py
pytest tests/integration/test_club_analytics_queries.py
pytest tests/contract/test_analytics_api.py
```

If integration tests require seeded data, load the provided sample fixtures before
running them.

## 7. Rollback and refresh procedure

- To remove the analytics support objects, drop `club_head_to_head_summary`,
  `club_season_summary`, `club_team_map`, and then `club_aliases`.
- To refresh analytics after new ETL loads, re-run `db/migrations/002_club_analytics.sql`
  after canonical tables have been loaded.

## 8. Validation record

Validated during implementation:

- `python3 -m py_compile code/api.py code/services/club_normalization.py code/services/view_models.py code/services/analytics_queries.py`
- `python3 -m pytest tests/unit/test_club_normalization.py tests/integration/test_club_analytics_queries.py tests/contract/test_analytics_api.py`

Still required in a database-backed environment:

- apply `db/migrations/002_club_analytics.sql` against the running PostgreSQL instance
- confirm slug-collision cases are assigned stable unique `club_key` values in `ntvs.club_aliases`
- confirm homepage, pool results, club rankings/profile, and comparison pages render
  against real seeded data in the Docker Compose stack
