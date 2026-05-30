# ntvs Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-05-29

## Active Technologies
- Python 3.11 + FastAPI, Uvicorn, psycopg2-binary, python-dotenv, Jinja2, (002-stitch-club-analytics)
- PostgreSQL 15 in schema `ntvs` (002-stitch-club-analytics)
- Python 3.10 + FastAPI 0.97, Jinja2, psycopg2-binary, pydantic<2, uvicorn (existing set — no new runtime deps) (003-ntvs-coach-club-hub)
- PostgreSQL, schema `ntvs` (additive migration `db/migrations/004_coach_hub.sql` + idempotent seed) (003-ntvs-coach-club-hub)

- Python 3.11 + FastAPI, Uvicorn, psycopg2-binary, python-dotenv, standard (002-stitch-club-analytics)

## Project Structure

```text
backend/
frontend/
tests/
```

## Commands

cd src [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] pytest [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] ruff check .

## Code Style

Python 3.11: Follow standard conventions

## Recent Changes
- 003-ntvs-coach-club-hub: Added Python 3.10 + FastAPI 0.97, Jinja2, psycopg2-binary, pydantic<2, uvicorn (existing set — no new runtime deps)
- 002-stitch-club-analytics: Added Python 3.11 + FastAPI, Uvicorn, psycopg2-binary, python-dotenv, Jinja2,

- 002-stitch-club-analytics: Added Python 3.11 + FastAPI, Uvicorn, psycopg2-binary, python-dotenv, standard

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
