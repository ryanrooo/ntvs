
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import re

# Load data
df = pd.read_csv('kickoff_classic_teams.csv')

def extract_club_name(team_name):
    # Heuristic: First word is usually club name, e.g. "RYZE"
    # Handling exceptions: 
    # "Madfrog" is one word in some, "Mad Frog" in others? (Looks one word in data: "Madfrog 13N")
    # "FH" -> FH
    # "TEJAS" -> TEJAS
    # "1United" -> 1United
    if not isinstance(team_name, str): return "Unknown"
    
    parts = team_name.split()
    if not parts: return "Unknown"
    
    # Check for known multi-word clubs if any?
    # For now, simplistic first word.
    return parts[0]

df['Club'] = df['Team'].apply(extract_club_name)

# --- 1. General Club Performance ---

# Aggregate stats by Club
club_stats = df.groupby('Club').agg({
    'Won': 'sum',
    'Lost': 'sum',
    'Team': 'count'
}).rename(columns={'Team': 'Team Count'})

club_stats['Total Games'] = club_stats['Won'] + club_stats['Lost']
club_stats['Win Rate'] = club_stats['Won'] / club_stats['Total Games']
club_stats['Win Rate'] = club_stats['Win Rate'].fillna(0)

# Sort by Win Rate (for clubs with > 1 team or > 5 games to avoid noise)
# Let's just sort by Win Rate descending
sorted_clubs = club_stats.sort_values(by='Win Rate', ascending=False)

print("\n--- Club Performance Summary (All) ---")
# Print as CSV to console
print(sorted_clubs[['Team Count', 'Won', 'Lost', 'Win Rate']].to_csv())
sorted_clubs.to_csv('club_performance_report.csv')
print(f"Saved report to 'club_performance_report.csv'")

# Visualization 1: Top 15 Clubs by Win Rate
plt.figure(figsize=(12, 6))
top_clubs = sorted_clubs[sorted_clubs['Team Count'] >= 2].head(15) 
sns.barplot(x=top_clubs.index, y=top_clubs['Win Rate'], palette='viridis')
plt.title('Top Club Performance (Avg Win Rate in Pool Play) - Min 2 Teams')
plt.xticks(rotation=45, ha='right')
plt.ylim(0, 1)
plt.ylabel('Win Rate')
plt.tight_layout()
plt.savefig('club_performance.png')
print(f"Generated 'club_performance.png'")

# --- 2. RYZE Specific Report ---

target_club = "RYZE"
ryze_teams = df[df['Club'] == target_club].copy()

if not ryze_teams.empty:
    print(f"\n--- {target_club} Teams Report ---")
    print(ryze_teams[['Division', 'Team', 'Pool', 'Rank', 'Won', 'Lost', 'Pool Finish']].to_string(index=False))
    
    # Calculate RYZE Aggregate Stats
    total_won = ryze_teams['Won'].sum()
    total_lost = ryze_teams['Lost'].sum()
    avg_finish = ryze_teams['Pool Finish'].mean()
    
    print(f"\n{target_club} Aggregate Stats:")
    print(f"Total Match Record: {total_won}-{total_lost}")
    print(f"Win Rate: {total_won / (total_won + total_lost):.2%}")
    print(f"Average Pool Finish: {avg_finish:.2f}")

    # Visualization 2: RYZE Performance vs Average
    # Compare RYZE win rate to global average
    global_avg_wr = df['Won'].sum() / (df['Won'].sum() + df['Lost'].sum())
    ryze_wr = total_won / (total_won + total_lost)
    
    plt.figure(figsize=(6, 6))
    plt.bar(['Global Average', f'{target_club} Average'], [global_avg_wr, ryze_wr], color=['gray', 'orange'])
    plt.title(f'{target_club} Win Rate vs Tournament Average')
    plt.ylim(0, 1)
    plt.ylabel('Win Rate')
    plt.savefig('ryze_vs_avg.png')
    print(f"Generated 'ryze_vs_avg.png'")

else:
    print(f"No teams found for club: {target_club}")

# --- 3. Head to Head Analysis for RYZE ---
# Parse 'Pool Match Results' column
# Format: "Won vs Opponent (Scores) | Lost vs Opponent (Scores)"

head_to_head = {} # Opponent -> {'Won': 0, 'Lost': 0, 'Split': 0}

if not ryze_teams.empty:
    for _, row in ryze_teams.iterrows():
        matches_str = row['Pool Match Results']
        if pd.isna(matches_str): continue
        
        matches = matches_str.split(' | ')
        for m in matches:
            # Parse outcome and opponent
            # e.g. "Won vs TEAM_NAME (scores)"
            match_data = re.match(r'(Won|Lost|Split) vs (.+) \(', m)
            if match_data:
                outcome = match_data.group(1)
                opponent_name = match_data.group(2)
                
                # Extract opponent club
                opp_club = extract_club_name(opponent_name)
                
                if opp_club not in head_to_head:
                    head_to_head[opp_club] = {'Won': 0, 'Lost': 0, 'Split': 0}
                
                head_to_head[opp_club][outcome] += 1

    if head_to_head:
        print(f"\n--- {target_club} Head-to-Head Performance (CSV) ---")
        hth_df = pd.DataFrame.from_dict(head_to_head, orient='index').fillna(0)
        hth_df['Total'] = hth_df['Won'] + hth_df['Lost'] + hth_df['Split']
        hth_df['Win %'] = (hth_df['Won'] / hth_df['Total']).mul(100).round(1)
        
        # Sort by most games played against
        hth_df = hth_df.sort_values(by='Total', ascending=False)
        
        # Output as CSV
        print(hth_df.to_csv())
        hth_df.to_csv('ryze_hth_report.csv')
        print("Saved head-to-head report to 'ryze_hth_report.csv'")
