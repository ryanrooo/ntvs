
import pandas as pd

# Load Tables
tournaments = pd.read_csv('db_tournaments.csv')
teams = pd.read_csv('db_teams.csv')
pools = pd.read_csv('db_pools.csv')
standings = pd.read_csv('db_pool_standings.csv')
matches = pd.read_csv('db_match_results.csv')

# SQL Equivalent Query Simulation
# SELECT * FROM teams tm 
# JOIN match_results mr ON tm.team_name = mr.team_name
# JOIN pools p ON mr.pool_id = p.pool_id
# JOIN tournaments t ON p.tournament_id = t.tournament_id
# JOIN pool_standings ps ON tm.team_name = ps.team_name AND p.pool_id = ps.pool_id
# WHERE tm.club_name = 'RYZE'

# 1. Filter Teams
ryze_teams = teams[teams['club_name'] == 'RYZE']

# 2. Join Matches
step1 = pd.merge(ryze_teams, matches, on='team_name', how='inner')

# 3. Join Pools (using pool_id from matches)
step2 = pd.merge(step1, pools, on='pool_id', suffixes=('_team', '_pool'))

# 4. Join Tournaments
step3 = pd.merge(step2, tournaments, on='tournament_id', how='inner')

# 5. Join Standings (on pool_id and team_name)
final_df = pd.merge(step3, standings, on=['pool_id', 'team_name'], how='left')

# Select and Rename Columns for display
view = final_df[[
    'name',           # Tournament Name
    'division_pool',  # Division
    'pool_name',      # Pool
    'team_name',      # Team
    'rank_seed',      # Pool Rank
    'opponent_name',  # Opponent
    'outcome',        # W/L
    'score_log'       # Scores
]]

print("--- SQL Join Simulation Result (RYZE Matches) ---")
print(view.to_string(index=False))
