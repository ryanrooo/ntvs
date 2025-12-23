
import requests
from bs4 import BeautifulSoup
import re
import csv
import sys
import hashlib
import os
import logging

# Ensure directories exist
os.makedirs("data", exist_ok=True)
os.makedirs("logs", exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/extract.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Base URL for VStar results
BASE_URL = "https://results.vstarvolleyball.com"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0"
}

def generate_id(text):
    """Generates a stable, short hash ID for a string."""
    return hashlib.md5(text.encode('utf-8')).hexdigest()[:8]

def clean_division(file_name):
    return file_name.replace(".html", "").replace(" Pools", "").strip()

def extract_club_name(team_name):
    if not isinstance(team_name, str): return "Unknown"
    parts = team_name.split()
    if not parts: return "Unknown"
    return parts[0]

def get_tournament_page(tournament_id):
    url = f"{BASE_URL}/index.php?id={tournament_id}"
    logger.info(f"Fetching tournament page: {url}")
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200: return None
    return response.text

def parse_result_links(html, tournament_id):
    soup = BeautifulSoup(html, 'html.parser')
    result_files = []
    elements = soup.find_all(attrs={"data-bs-file": True, "data-bs-eventid": tournament_id})
    for el in elements:
        file_name = el['data-bs-file']
        if "Pools" in file_name and "assignment" not in file_name:
             result_files.append(file_name)
    return list(set(result_files))

# --- Extraction Logic ---

def extract_pool_data(tournament_id, file_name):
    # Note: This function now receives the DB_TOURNAMENT_ID (e.g. kickoffclassic_2025)
    # But fetching URL needs the VStar ID.
    # However, 'view.php' uses `?id=kickoffclassic`, not `_2025`.
    # Quick Fix: The `file_name` argument comes from `parse_result_links`.
    # But the URL construction looks like: `view.php?id={tournament_id}...`.
    # This BREAKS if we pass `kickoffclassic_2025` here.
    
    # Correction: pass both IDs or strip suffix.
    # Simpler: Split ID on first underscore? No, some IDs might have underscores.
    # Let's clean this up by passing `vstar_id` AND `db_tournament_id` to this function?
    # Or extracting vstar_id from the passed ID if we assume a format.
    
    # I'll rely on the caller to handle this properly, but since I am overwriting the file,
    # I will modify the signature to accept `vstar_id` for fetching and `db_tournament_id` for Logic.
    pass

def extract_pool_data_v2(vstar_id, db_tournament_id, file_name):
    url = f"{BASE_URL}/view.php?id={vstar_id}&file={file_name}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200: return [], [], [], [] 

    soup = BeautifulSoup(response.text, 'html.parser')
    
    extracted_teams = {} 
    extracted_pools = {} 
    extracted_standings = [] 
    extracted_matches = [] 
    
    current_division = clean_division(file_name)
    
    current_pool_name = None
    pool_teams_map = {} 
    pool_match_sequence = [] 
    match_scores_buffer = {} 
    current_pool_standings_buffer = [] 
    
    tables = soup.find_all('table')
    
    def flush_pool():
        if not current_pool_name: return
        
        # Use DB_TOURNAMENT_ID for unique keys
        pool_id = f"{db_tournament_id}_{current_division}_{current_pool_name}".replace(" ", "").lower()
        
        if pool_id not in extracted_pools:
            extracted_pools[pool_id] = {
                "pool_id": pool_id,
                "tournament_id": db_tournament_id,
                "division": current_division,
                "pool_name": current_pool_name,
                "team_count": len(pool_teams_map)
            }
            
        for rec in current_pool_standings_buffer:
            team_name = rec['Team']
            if team_name not in extracted_teams:
                extracted_teams[team_name] = {
                    "team_name": team_name,
                    "club_name": extract_club_name(team_name),
                    "division": current_division 
                }
            
            extracted_standings.append({
                "pool_id": pool_id,
                "team_name": team_name,
                "rank_seed": rec['Rank'],
                "matches_won": rec['Won'],
                "matches_lost": rec['Lost'],
                "point_diff": rec['Point Differential'],
                "pool_finish": rec['Pool Finish']
            })
            
        for (seed_a, seed_b), games in match_scores_buffer.items():
            team_a = pool_teams_map.get(seed_a, f"Seed {seed_a}")
            team_b = pool_teams_map.get(seed_b, f"Seed {seed_b}")
            
            wins_a = 0
            wins_b = 0
            scores_formatted = []
            
            for sa, sb in games:
                scores_formatted.append(f"{sa}-{sb}")
                if sa > sb: wins_a += 1
                elif sb > sa: wins_b += 1
            
            outcome_a = "Split"
            if wins_a > wins_b: outcome_a = "Won"
            elif wins_b > wins_a: outcome_a = "Lost"
            
            matched_scores_str = ",".join(scores_formatted)
            
            extracted_matches.append({
                "match_id": generate_id(f"{pool_id}_{team_a}_{team_b}"),
                "pool_id": pool_id,
                "team_name": team_a,
                "opponent_name": team_b,
                "outcome": outcome_a,
                "sets_won": wins_a,
                "sets_lost": wins_b,
                "score_log": matched_scores_str
            })
            
            outcome_b = "Split"
            if wins_b > wins_a: outcome_b = "Won"
            elif wins_a > wins_b: outcome_b = "Lost"
            
            scores_formatted_b = [f"{sb}-{sa}" for sa, sb in games]
            matched_scores_str_b = ",".join(scores_formatted_b)

            extracted_matches.append({
                "match_id": generate_id(f"{pool_id}_{team_a}_{team_b}"),
                "pool_id": pool_id,
                "team_name": team_b,
                "opponent_name": team_a,
                "outcome": outcome_b,
                "sets_won": wins_b,
                "sets_lost": wins_a,
                "score_log": matched_scores_str_b
            })

    
    for table in tables:
        rows = table.find_all('tr')
        for row in rows:
            raw_cells = [td.get_text(strip=True) for td in row.find_all('td')]
            non_empty = [c for c in raw_cells if c]
            if not non_empty: continue
            
            first_text = non_empty[0]
            if "Pool" in first_text and len(first_text) < 15 and re.search(r'Pool\s+\d+', first_text, re.IGNORECASE):
                flush_pool()
                current_pool_name = first_text
                pool_teams_map = {}
                pool_match_sequence = []
                match_scores_buffer = {}
                current_pool_standings_buffer = []
                continue
            
            rank_idx = -1
            for idx, txt in enumerate(raw_cells):
                if re.match(r'^\d+\.$', txt):
                    rank_idx = idx
                    break
            
            if rank_idx != -1 and len(raw_cells) > rank_idx + 1:
                rank_str = raw_cells[rank_idx]
                team_name = raw_cells[rank_idx + 1]
                if team_name and "Team" not in team_name:
                    seed_num = rank_str.replace(".", "")
                    pool_teams_map[seed_num] = team_name
                    
                    stats = []
                    for k in range(rank_idx + 2, len(raw_cells)):
                        if raw_cells[k].isdigit() or raw_cells[k].startswith("-"):
                            stats.append(raw_cells[k])
                    
                    if len(stats) >= 2:
                        current_pool_standings_buffer.append({
                            "Rank": seed_num,
                            "Team": team_name,
                            "Won": stats[0],
                            "Lost": stats[1],
                            "Point Differential": stats[2] if len(stats) > 2 else "",
                            "Pool Finish": stats[3] if len(stats) > 3 else ""
                        })
                    continue
            
            potential_matches = []
            for txt in raw_cells:
                m = re.search(r'(\d+)\s*vs\s*(\d+)', txt)
                if m: potential_matches.append((m.group(1), m.group(2)))
            if len(potential_matches) > 0:
                pool_match_sequence = potential_matches
                continue
            
            score_label_idx = -1
            for idx, txt in enumerate(raw_cells):
                if "Score" in txt or "Game" in txt:
                    score_label_idx = idx
                    break
            
            if score_label_idx != -1 and pool_match_sequence:
                score_cells = raw_cells[score_label_idx + 1:]
                for i, (seed_a, seed_b) in enumerate(pool_match_sequence):
                    idx_a = i * 2
                    idx_b = i * 2 + 1
                    if idx_b < len(score_cells):
                        s1 = score_cells[idx_a]
                        s2 = score_cells[idx_b]
                        if s1.isdigit() and s2.isdigit():
                            key = (seed_a, seed_b)
                            if key not in match_scores_buffer: match_scores_buffer[key] = []
                            match_scores_buffer[key].append((int(s1), int(s2)))
                            
    flush_pool()
    return list(extracted_teams.values()), list(extracted_pools.values()), extracted_standings, extracted_matches

def main():
    # Tournaments List with YEAR
    tournaments_to_process = [
        ("kickoffclassic", "Kickoff Classic", "2025"),
        ("bidwarmup1", "Bid Warm Up 1", "2025"),
        ("centexchallenge", "Centex Challenge", "2025"),
        ("dallasfrozenfest", "Dallas Frozen Fest", "2025"),
        ("northtexashomeopener", "North Texas Home Opener", "2025"),
        ("fwkickoff", "FW Kickoff", "2025")
    ]
    
    db_tournaments = []
    db_teams = {} 
    db_pools = {} 
    db_standings = []
    db_matches = []
    
    for vstar_id, t_name, t_year in tournaments_to_process:
        # Create UNIQUE ID for Database: ID_YEAR
        db_tournament_id = f"{vstar_id}_{t_year}"
        full_name = f"{t_name} {t_year}"
        
        logger.info(f"Starting ETL for {full_name} ({db_tournament_id})...")
        
        db_tournaments.append({"tournament_id": db_tournament_id, "name": full_name})
        
        html = get_tournament_page(vstar_id)
        if not html:
            logger.warning(f"Skipping {vstar_id}: No page found.")
            continue

        files = parse_result_links(html, vstar_id)
        logger.info(f"  Found {len(files)} result files.")
        
        for f in files:
            # Pass BOTH IDs
            teams, pools, standings, matches = extract_pool_data_v2(vstar_id, db_tournament_id, f)
            logger.info(f"    Processed {f}: {len(teams)} teams, {len(matches)} matches.")
            
            for t in teams:
                if t['team_name'] not in db_teams:
                    db_teams[t['team_name']] = t
                    
            for p in pools:
                db_pools[p['pool_id']] = p
                
            db_standings.extend(standings)
            db_matches.extend(matches)
        
    with open("data/tournaments.csv", 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["tournament_id", "name"])
        writer.writeheader()
        writer.writerows(db_tournaments)
        
    with open("data/teams.csv", 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["team_name", "club_name", "division"])
        writer.writeheader()
        writer.writerows(list(db_teams.values()))

    with open("data/pools.csv", 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["pool_id", "tournament_id", "division", "pool_name", "team_count"])
        writer.writeheader()
        writer.writerows(list(db_pools.values()))
        
    with open("data/pool_standings.csv", 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["pool_id", "team_name", "rank_seed", "matches_won", "matches_lost", "point_diff", "pool_finish"])
        writer.writeheader()
        writer.writerows(db_standings)

    with open("data/match_results.csv", 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["match_id", "pool_id", "team_name", "opponent_name", "outcome", "sets_won", "sets_lost", "score_log"])
        writer.writeheader()
        writer.writerows(db_matches)
        
    logger.info(f"Total Extracted: {len(db_teams)} Teams, {len(db_pools)} Pools, {len(db_matches)} Matches across {len(db_tournaments)} tournaments.")
    logger.info("Database CSVs generated in data/ folder.")

if __name__ == "__main__":
    main()
