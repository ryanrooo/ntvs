CREATE SCHEMA IF NOT EXISTS ntvs;
SET search_path TO ntvs;

CREATE TABLE IF NOT EXISTS bracket_matches (
    match_id    VARCHAR(50),
    tournament_id VARCHAR(50),
    division    VARCHAR(50),
    bracket_tier VARCHAR(50),
    round_label VARCHAR(20),
    team_name   VARCHAR(100),
    opponent_name VARCHAR(100),
    outcome     VARCHAR(20),
    score_log   TEXT,
    PRIMARY KEY (match_id, team_name),
    FOREIGN KEY (tournament_id) REFERENCES tournaments(tournament_id)
);

CREATE TABLE IF NOT EXISTS bracket_placements (
    tournament_id VARCHAR(50),
    division      VARCHAR(50),
    bracket_tier  VARCHAR(50),
    team_name     VARCHAR(100),
    placement     INT,
    PRIMARY KEY (tournament_id, division, bracket_tier, team_name)
);
