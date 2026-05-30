CREATE SCHEMA IF NOT EXISTS ntvs;
SET search_path TO ntvs;

CREATE TABLE IF NOT EXISTS club_aliases (
    source_club_name VARCHAR(100) PRIMARY KEY,
    base_slug VARCHAR(120) NOT NULL,
    club_key VARCHAR(120) NOT NULL UNIQUE,
    display_name VARCHAR(100) NOT NULL,
    normalization_status VARCHAR(32) NOT NULL DEFAULT 'direct',
    collision_rank INTEGER NOT NULL DEFAULT 1
);

ALTER TABLE club_aliases
    ADD COLUMN IF NOT EXISTS base_slug VARCHAR(120);

ALTER TABLE club_aliases
    ALTER COLUMN base_slug SET DEFAULT 'unknown-club';

UPDATE club_aliases
SET base_slug = COALESCE(NULLIF(base_slug, ''), REGEXP_REPLACE(LOWER(source_club_name), '[^a-z0-9]+', '-', 'g'), 'unknown-club')
WHERE base_slug IS NULL OR base_slug = '';

ALTER TABLE club_aliases
    ALTER COLUMN base_slug SET NOT NULL;

ALTER TABLE club_aliases
    ADD COLUMN IF NOT EXISTS collision_rank INTEGER;

UPDATE club_aliases
SET collision_rank = 1
WHERE collision_rank IS NULL OR collision_rank < 1;

ALTER TABLE club_aliases
    ALTER COLUMN collision_rank SET DEFAULT 1;

ALTER TABLE club_aliases
    ALTER COLUMN collision_rank SET NOT NULL;

WITH normalized AS (
    SELECT DISTINCT
        club_name AS source_club_name,
        COALESCE(NULLIF(REGEXP_REPLACE(LOWER(club_name), '[^a-z0-9]+', '-', 'g'), ''), 'unknown-club') AS base_slug,
        club_name AS display_name
    FROM teams
    WHERE club_name IS NOT NULL AND club_name <> ''
),
ranked AS (
    SELECT
        source_club_name,
        base_slug,
        display_name,
        ROW_NUMBER() OVER (PARTITION BY base_slug ORDER BY source_club_name) AS collision_rank
    FROM normalized
)
INSERT INTO club_aliases (source_club_name, base_slug, club_key, display_name, normalization_status, collision_rank)
SELECT
    source_club_name,
    base_slug,
    CASE
        WHEN collision_rank = 1 THEN base_slug
        ELSE base_slug || '-' || collision_rank::text
    END AS club_key,
    display_name,
    CASE
        WHEN collision_rank = 1 THEN 'direct'
        ELSE 'collision-resolved'
    END AS normalization_status,
    collision_rank
FROM ranked
ON CONFLICT (source_club_name) DO UPDATE
SET
    base_slug = EXCLUDED.base_slug,
    club_key = EXCLUDED.club_key,
    display_name = EXCLUDED.display_name,
    normalization_status = EXCLUDED.normalization_status,
    collision_rank = EXCLUDED.collision_rank;

DROP VIEW IF EXISTS club_head_to_head_summary;
DROP VIEW IF EXISTS club_season_summary;
DROP VIEW IF EXISTS club_team_map;

CREATE OR REPLACE VIEW club_team_map AS
SELECT
    t.team_name,
    t.division,
    COALESCE(ca.club_key, REGEXP_REPLACE(LOWER(COALESCE(t.club_name, split_part(t.team_name, ' ', 1))), '[^a-z0-9]+', '-', 'g')) AS club_key,
    COALESCE(ca.display_name, COALESCE(t.club_name, split_part(t.team_name, ' ', 1))) AS display_name,
    COALESCE(ca.source_club_name, COALESCE(t.club_name, split_part(t.team_name, ' ', 1))) AS source_club_name,
    COALESCE(ca.normalization_status, CASE WHEN t.club_name IS NULL OR t.club_name = '' THEN 'inferred' ELSE 'direct' END) AS normalization_status,
    COALESCE(ca.base_slug, REGEXP_REPLACE(LOWER(COALESCE(t.club_name, split_part(t.team_name, ' ', 1))), '[^a-z0-9]+', '-', 'g')) AS base_slug,
    COALESCE(ca.collision_rank, 1) AS collision_rank
FROM teams t
LEFT JOIN club_aliases ca ON ca.source_club_name = t.club_name;

CREATE OR REPLACE VIEW club_season_summary AS
SELECT
    ctm.club_key,
    ctm.display_name,
    ctm.source_club_name,
    ctm.normalization_status,
    COUNT(DISTINCT ctm.team_name) AS teams_active,
    COALESCE(SUM(CASE WHEN mr.outcome = 'Won' THEN 1 ELSE 0 END), 0) AS matches_won,
    COALESCE(SUM(CASE WHEN mr.outcome = 'Lost' THEN 1 ELSE 0 END), 0) AS matches_lost,
    COALESCE(SUM(mr.sets_won), 0) AS sets_won,
    COALESCE(SUM(mr.sets_lost), 0) AS sets_lost,
    COALESCE(SUM(ps.point_diff), 0) AS point_diff_total,
    COUNT(DISTINCT p.tournament_id) AS tournaments_played,
    MAX(p.tournament_id) AS latest_activity_date,
    (
        COALESCE(SUM(CASE WHEN mr.outcome = 'Won' THEN 1 ELSE 0 END), 0) * 3
        + COALESCE(SUM(mr.sets_won), 0)
        + COALESCE(SUM(ps.point_diff), 0) / 100.0
    ) AS ranking_score
FROM club_team_map ctm
LEFT JOIN match_results mr ON mr.team_name = ctm.team_name
LEFT JOIN pool_standings ps ON ps.team_name = ctm.team_name
LEFT JOIN pools p ON p.pool_id = mr.pool_id
GROUP BY ctm.club_key, ctm.display_name, ctm.source_club_name, ctm.normalization_status;

CREATE OR REPLACE VIEW club_head_to_head_summary AS
SELECT
    c1.club_key,
    c2.club_key AS opponent_club_key,
    COUNT(DISTINCT mr.match_id) AS matches_played,
    COALESCE(SUM(CASE WHEN mr.outcome = 'Won' THEN 1 ELSE 0 END), 0) AS matches_won,
    COALESCE(SUM(CASE WHEN mr.outcome = 'Lost' THEN 1 ELSE 0 END), 0) AS matches_lost,
    COALESCE(SUM(mr.sets_won), 0) AS sets_won,
    COALESCE(SUM(mr.sets_lost), 0) AS sets_lost,
    MAX(p.tournament_id) AS latest_meeting
FROM match_results mr
JOIN club_team_map c1 ON c1.team_name = mr.team_name
JOIN club_team_map c2 ON c2.team_name = mr.opponent_name
LEFT JOIN pools p ON p.pool_id = mr.pool_id
WHERE c1.club_key <> c2.club_key
GROUP BY c1.club_key, c2.club_key;

-- Rollback guidance:
-- 1. DROP VIEW IF EXISTS club_head_to_head_summary;
-- 2. DROP VIEW IF EXISTS club_season_summary;
-- 3. DROP VIEW IF EXISTS club_team_map;
-- 4. DROP TABLE IF EXISTS club_aliases;
-- Refresh guidance after data reload:
-- Re-run this migration so club aliases and derived views reflect the latest canonical rows.
-- Collision-safe club_key assignment is deterministic by source_club_name sort order within each base_slug.
