
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Load Data
tournaments = pd.read_csv('db_tournaments.csv')
teams = pd.read_csv('db_teams.csv')
pools = pd.read_csv('db_pools.csv')
standings = pd.read_csv('db_pool_standings.csv')

# Join Standings to Pools (to get Tournament ID)
pool_results = pd.merge(standings, pools, on='pool_id')

# Join with Tournaments (to get Tournament Name)
pool_results = pd.merge(pool_results, tournaments, on='tournament_id')

# Join with Teams (to get Club Name)
pool_results = pd.merge(pool_results, teams, on='team_name')

# Group by Tournament and Club
club_perf = pool_results.groupby(['name', 'club_name']).agg({
    'matches_won': 'sum',
    'matches_lost': 'sum',
    'team_name': 'nunique' 
}).rename(columns={'team_name': 'teams_participating'})

# Calculate Metrics
club_perf['total_matches'] = club_perf['matches_won'] + club_perf['matches_lost']
club_perf['win_rate'] = club_perf['matches_won'] / club_perf['total_matches']

club_perf = club_perf[club_perf['total_matches'] > 0]

# Reset index to make manipulation easier
club_perf = club_perf.reset_index()

# Rename the 'name' column (from groupby) to 'tournament_name'
club_perf.rename(columns={'name': 'tournament_name'}, inplace=True)

# Sort
club_perf = club_perf.sort_values(by=['tournament_name', 'win_rate', 'matches_won'], ascending=[True, False, False])

# Display Top 5 Per Tournament
print("--- Best Performing Clubs by Tournament (Top 5) ---")

unique_tournaments = club_perf['tournament_name'].unique()

for tourney in unique_tournaments:
    print(f"\nTournament: {tourney}")
    t_data = club_perf[club_perf['tournament_name'] == tourney]
    
    top_5 = t_data.head(5)
    print(top_5[['club_name', 'teams_participating', 'matches_won', 'matches_lost', 'win_rate']].to_string(index=False, float_format='{:.3f}'.format))
    
    winner = t_data.iloc[0]
    print(f"--> BEST CLUB: {winner['club_name']} ({winner['win_rate']:.1%} Win Rate)")

# Save Full Report
club_perf.to_csv('tournament_club_rankings.csv', index=False)
print("\nFull rankings saved to 'tournament_club_rankings.csv'")
