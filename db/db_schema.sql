-- 1. Tournaments Table
CREATE TABLE tournaments (
    tournament_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

-- 2. Teams Table
CREATE TABLE teams (
    team_name VARCHAR(100) PRIMARY KEY,
    club_name VARCHAR(100),
    division VARCHAR(50)
);

-- 3. Pools Table
CREATE TABLE pools (
    pool_id VARCHAR(100) PRIMARY KEY,
    tournament_id VARCHAR(50),
    division VARCHAR(50),
    pool_name VARCHAR(50),
    team_count INT,
    FOREIGN KEY (tournament_id) REFERENCES tournaments(tournament_id)
);

-- 4. Pool Standings Table (Link between Pools and Teams)
CREATE TABLE pool_standings (
    pool_id VARCHAR(100),
    team_name VARCHAR(100),
    rank_seed INT,
    matches_won INT,
    matches_lost INT,
    point_diff INT,
    pool_finish INT,
    PRIMARY KEY (pool_id, team_name),
    FOREIGN KEY (pool_id) REFERENCES pools(pool_id),
    FOREIGN KEY (team_name) REFERENCES teams(team_name)
);

-- 5. Match Results Table
-- Note: Contains 2 rows per match (one for each team's perspective)
CREATE TABLE match_results (
    match_id VARCHAR(50),      -- Shared ID for the specific game
    pool_id VARCHAR(100),
    team_name VARCHAR(100),    -- The subject team
    opponent_name VARCHAR(100), -- The opponent team
    outcome VARCHAR(20),       -- 'Won', 'Lost', 'Split'
    sets_won INT,
    sets_lost INT,
    score_log TEXT,
    PRIMARY KEY (match_id, team_name),
    FOREIGN KEY (pool_id) REFERENCES pools(pool_id),
    FOREIGN KEY (team_name) REFERENCES teams(team_name)
);

-- Example Query after Import:
-- SELECT * FROM match_results mr 
-- JOIN teams t ON mr.team_name = t.team_name 
-- WHERE t.club_name = 'RYZE';
