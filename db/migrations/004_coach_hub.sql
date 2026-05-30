-- Migration 004: NTVS Coach & Club Hub (NTVS-2 handoff)
-- Additive + rerun-safe. Creates the net-new, NTVS-owned tables for coaches,
-- endorsements, verification, club presentation attributes, tournament schedule,
-- and stat leaders. Existing scraper-owned tables/views are untouched.
--
-- Source-of-truth notes (constitution: Canonical Data Integrity):
--   * coach/endorsement/verification data is user-generated/seeded, NOT derived
--     from match_results/pool_standings/bracket_* (those stay canonical for perf).
--   * coach.club_key / coach_positions.club_key are SOFT links to the canonical
--     club_key (club_aliases / club_team_map). No hard FK: a claimed club may not
--     exist in the canonical set yet, in which case the UI degrades to club_label.
--   * coaches.verified and all counts/averages are caches/derivations, recomputed
--     from source rows -- never the single source of truth for linkage.

CREATE SCHEMA IF NOT EXISTS ntvs;
SET search_path TO ntvs;

-- 1. coaches -- canonical coach identity + stored resume summary -------------
CREATE TABLE IF NOT EXISTS coaches (
    coach_key            VARCHAR(120) PRIMARY KEY,
    display_name         VARCHAR(100) NOT NULL,
    base_slug            VARCHAR(120) NOT NULL,
    collision_rank       INT          NOT NULL DEFAULT 1,
    normalization_status VARCHAR(32)  NOT NULL DEFAULT 'direct',
    club_key             VARCHAR(120),                       -- soft link (nullable)
    role                 VARCHAR(80),
    city                 VARCHAR(80),
    initials             VARCHAR(4),
    gradient             VARCHAR(80),
    verified             BOOLEAN      NOT NULL DEFAULT FALSE, -- cache of ">=1 verified position"
    about                TEXT,
    wins                 INT          NOT NULL DEFAULT 0,
    win_rate             NUMERIC(4,3) NOT NULL DEFAULT 0 CHECK (win_rate >= 0 AND win_rate <= 1),
    commits              INT          NOT NULL DEFAULT 0,
    gold                 INT          NOT NULL DEFAULT 0,
    seasons              INT          NOT NULL DEFAULT 0,
    certifications       TEXT[],
    specialties          TEXT[]
);
CREATE INDEX IF NOT EXISTS idx_coaches_verified ON coaches (verified);
CREATE INDEX IF NOT EXISTS idx_coaches_club_key ON coaches (club_key);
CREATE INDEX IF NOT EXISTS idx_coaches_name_lower ON coaches (LOWER(display_name));

-- 2. coach_positions -- one resume/career entry -----------------------------
CREATE TABLE IF NOT EXISTS coach_positions (
    position_id BIGSERIAL PRIMARY KEY,
    coach_key   VARCHAR(120) NOT NULL REFERENCES coaches (coach_key) ON DELETE CASCADE,
    club_key    VARCHAR(120),                       -- soft link (nullable)
    club_label  VARCHAR(100) NOT NULL,              -- as claimed (shown if club_key unmatched)
    club_color  VARCHAR(16),
    role        VARCHAR(80)  NOT NULL,
    age_group   VARCHAR(40),
    years       VARCHAR(20),
    record      VARCHAR(20),
    note        TEXT,
    status      VARCHAR(16)  NOT NULL DEFAULT 'pending'
                CHECK (status IN ('pending', 'verified', 'denied'))
);
CREATE INDEX IF NOT EXISTS idx_positions_coach ON coach_positions (coach_key);
-- idempotent-add dedupe key (years may be NULL -> COALESCE so re-adds collapse):
CREATE UNIQUE INDEX IF NOT EXISTS uq_position_natural
    ON coach_positions (coach_key, club_label, role, COALESCE(years, ''));

-- 3. endorsements -- public, positive-only feedback (append-only) ------------
CREATE TABLE IF NOT EXISTS endorsements (
    endorsement_id BIGSERIAL PRIMARY KEY,
    coach_key      VARCHAR(120) NOT NULL REFERENCES coaches (coach_key) ON DELETE CASCADE,
    author_label   VARCHAR(80)  NOT NULL,
    relationship   VARCHAR(20)  NOT NULL,
    stars          SMALLINT     NOT NULL CHECK (stars IN (4, 5)), -- rating floor in DB too
    tags           TEXT[],
    body           VARCHAR(500) NOT NULL,
    created_at     TIMESTAMPTZ  NOT NULL DEFAULT now(),
    -- created_date is a stored UTC date (immutable, indexable) used for same-day dedupe;
    -- timestamptz::date is session-tz-dependent so it cannot be used in a unique index.
    created_date   DATE         NOT NULL DEFAULT ((now() AT TIME ZONE 'UTC')::date),
    body_hash      VARCHAR(64)  NOT NULL
);
-- ADD COLUMN keeps the migration rerun-safe if an older endorsements table predates created_date:
ALTER TABLE endorsements
    ADD COLUMN IF NOT EXISTS created_date DATE NOT NULL DEFAULT ((now() AT TIME ZONE 'UTC')::date);
CREATE INDEX IF NOT EXISTS idx_endorsements_coach ON endorsements (coach_key);
-- idempotent dedupe: same author + same body (hash), same day = one row:
CREATE UNIQUE INDEX IF NOT EXISTS uq_endorsement_dedupe
    ON endorsements (coach_key, author_label, body_hash, created_date);

-- 4. verification_requests -- a coach's claim awaiting a director decision ----
CREATE TABLE IF NOT EXISTS verification_requests (
    request_id     BIGSERIAL PRIMARY KEY,
    coach_key      VARCHAR(120) NOT NULL REFERENCES coaches (coach_key) ON DELETE CASCADE,
    club_key       VARCHAR(120) NOT NULL,                  -- target club's director queue
    position_id    BIGINT REFERENCES coach_positions (position_id) ON DELETE SET NULL,
    name           VARCHAR(100) NOT NULL,
    initials       VARCHAR(4),
    color          VARCHAR(16),
    role           VARCHAR(80),
    claim_years    VARCHAR(20),
    match_strength VARCHAR(16),   -- heuristic/seeded signal, NOT derived from match data
    match_pct      SMALLINT,      -- heuristic 0-100, NOT computed from match records
    note           TEXT,
    status         VARCHAR(16)  NOT NULL DEFAULT 'pending'
                   CHECK (status IN ('pending', 'approved', 'denied')),
    created_at     TIMESTAMPTZ  NOT NULL DEFAULT now(),
    resolved_at    TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_requests_club_status ON verification_requests (club_key, status);
CREATE INDEX IF NOT EXISTS idx_requests_coach ON verification_requests (coach_key);

-- 5. club_attributes -- NTVS-curated presentation/comparison fields (1:1) -----
-- PK club_key -> canonical club identity. No hard FK (canonical key can come
-- from a view). All columns nullable -> missing = neutral placeholder, not zero.
CREATE TABLE IF NOT EXISTS club_attributes (
    club_key      VARCHAR(120) PRIMARY KEY,
    tier          SMALLINT,
    color         VARCHAR(16),
    gold          INT,
    silver        INT,
    bronze        INT,
    commits       INT,
    coaches_count INT,
    fee           INT,            -- season fee (compare: lower-is-better)
    est_year      SMALLINT,
    about         TEXT,
    radar_win     NUMERIC(3,2),
    radar_depth   NUMERIC(3,2),
    radar_gold    NUMERIC(3,2),
    radar_dev     NUMERIC(3,2),
    radar_alumni  NUMERIC(3,2)
);

-- 6. tournament_schedule -- NTVS-curated schedule attributes (1:1) -----------
CREATE TABLE IF NOT EXISTS tournament_schedule (
    tournament_id VARCHAR(50) PRIMARY KEY REFERENCES tournaments (tournament_id) ON DELETE CASCADE,
    event_date    DATE,
    month_key     VARCHAR(7),     -- "2026-03" grouping key
    venue         VARCHAR(120),
    city          VARCHAR(80),
    team_count    INT,
    age_lo        SMALLINT,
    age_hi        SMALLINT,
    division      VARCHAR(50),
    status        VARCHAR(16),    -- Open / Filling / Waitlist
    within_mi     INT,            -- static distance band; basis for proximity filter
    featured      BOOLEAN DEFAULT FALSE,
    completed     BOOLEAN DEFAULT FALSE
);
CREATE INDEX IF NOT EXISTS idx_schedule_month ON tournament_schedule (month_key);

-- 7. stat_leaders -- per-tournament statistical leaders for results ----------
CREATE TABLE IF NOT EXISTS stat_leaders (
    leader_id     BIGSERIAL PRIMARY KEY,
    tournament_id VARCHAR(50)  NOT NULL REFERENCES tournaments (tournament_id) ON DELETE CASCADE,
    category      VARCHAR(16)  NOT NULL CHECK (category IN ('kills', 'assists', 'digs')),
    rank          SMALLINT     NOT NULL,
    player_name   VARCHAR(100) NOT NULL,
    club_label    VARCHAR(100),
    value         INT          NOT NULL,
    UNIQUE (tournament_id, category, rank)
);

-- Rollback guidance (migration 004 down):
--   DROP TABLE IF EXISTS ntvs.stat_leaders;
--   DROP TABLE IF EXISTS ntvs.tournament_schedule;
--   DROP TABLE IF EXISTS ntvs.club_attributes;
--   DROP TABLE IF EXISTS ntvs.verification_requests;
--   DROP TABLE IF EXISTS ntvs.endorsements;
--   DROP TABLE IF EXISTS ntvs.coach_positions;
--   DROP TABLE IF EXISTS ntvs.coaches;
-- No existing tables/views are modified, so rollback is clean.
