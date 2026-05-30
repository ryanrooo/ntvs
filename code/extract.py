
import requests
from bs4 import BeautifulSoup
import re
import csv
import sys
import hashlib
import os
import logging
from urllib.parse import urlparse, parse_qs

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
ALL_EVENTS_URL = "https://vstarvolleyball.com/?page_id=409&scope=All"
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

def get_html(url):
    logger.info(f"Fetching page: {url}")
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        return response.text
    except requests.RequestException as exc:
        logger.warning(f"Failed to fetch {url}: {exc}")
        return None

def get_tournament_page(tournament_id):
    url = f"{BASE_URL}/index.php?id={tournament_id}"
    return get_html(url)

def discover_tournaments():
    html = get_html(ALL_EVENTS_URL)
    if not html:
        return []

    soup = BeautifulSoup(html, 'html.parser')
    content = soup.select_one('article') or soup.select_one('.entry-content') or soup

    tournaments = []
    seen_ids = set()

    for link in content.find_all('a', href=True):
        href = link['href'].strip()
        if not href.startswith(f"{BASE_URL}/index.php?id="):
            continue

        event_name = link.get_text(" ", strip=True)
        if not event_name:
            continue

        parsed = urlparse(href)
        event_id = parse_qs(parsed.query).get("id", [None])[0]
        if not event_id or event_id in seen_ids:
            continue

        seen_ids.add(event_id)
        tournaments.append({
            "vstar_id": event_id,
            "name": event_name
        })

    logger.info(f"Discovered {len(tournaments)} tournaments from the VSTAR all-events page.")
    return tournaments

def parse_division_tier(file_name):
    """Split '14 Silver A.html' → ('14','Silver A'), '13C Bronze.html' → ('13C','Bronze')."""
    base = file_name.replace('.html', '').strip()
    # Age group may include letter suffixes (13C, 14Re) or ranges (17-18)
    m = re.match(r'^(\d+[A-Za-z]*(?:-\d+)?)\s+(.*)', base)
    if m:
        return m.group(1), m.group(2).strip() or 'Open'
    return base, 'Open'

def detect_bracket_content_type(html):
    """Returns 'pool' if the file is a pool-standings sheet, 'elimination' otherwise."""
    soup = BeautifulSoup(html, 'html.parser')
    table = soup.find('table')
    if not table:
        return 'unknown'
    rows = table.find_all('tr')
    if len(rows) < 2:
        return 'unknown'
    row2_text = ' '.join(c.get_text(strip=True) for c in rows[1].find_all('td'))
    return 'pool' if 'Matches' in row2_text else 'elimination'

def parse_result_links(html, tournament_id):
    soup = BeautifulSoup(html, 'html.parser')
    pool_files, bracket_files = [], []
    elements = soup.find_all(attrs={"data-bs-file": True, "data-bs-eventid": tournament_id})
    for el in elements:
        file_name = el['data-bs-file']
        if 'assignment' in file_name:
            continue
        if 'Pools' in file_name:
            pool_files.append(file_name)
        else:
            bracket_files.append(file_name)
    return sorted(set(pool_files)), sorted(set(bracket_files))

# --- Extraction Logic ---

def _build_grid(table):
    """Build a colspan-aware 2D grid: (row, col) -> text."""
    grid = {}
    for ri, row in enumerate(table.find_all('tr')):
        ci = 0
        for cell in row.find_all('td'):
            colspan = int(cell.get('colspan', 1) or 1)
            txt = ' '.join(cell.get_text().split())
            if txt and txt != '\xa0':
                grid[(ri, ci)] = txt
            ci += colspan
    return grid

def extract_elimination_bracket(vstar_id, db_tournament_id, file_name, html):
    """Extract match results and final champion from an elimination bracket file."""
    soup = BeautifulSoup(html, 'html.parser')
    table = soup.find('table')
    if not table:
        return [], []

    grid = _build_grid(table)
    division, tier = parse_division_tier(file_name)

    # Override division/tier from embedded "Division:" cell when present
    for txt in grid.values():
        if txt.startswith('Division:'):
            div_str = txt.replace('Division:', '').strip()
            m = re.match(r'^(\d+(?:-\d+)?)\s+(.*)', div_str)
            if m:
                division, tier = m.group(1), m.group(2).strip()
            break

    SKIP_RE = re.compile(
        r'^M\d+$|^\d+:\d+\s*(AM|PM)|^CT\s*\d|^REF$|^VIPTT$'
        r'|^Loser|^Winner|CHAMPION|^Division|^Site:|^Date:'
        r'|^\d{1,2}/\d{1,2}/\d{4}|\d+-\d+.*\d+-\d+'
        r'|^5th\s+Place|^3rd\s+Place|^POOL\s+COMPLETE|Place$'
        r'|^Round|^Bracket|^Gold$|^Silver|^Bronze',
        re.I
    )

    def is_team(txt):
        if len(txt) < 5 or not re.search(r'[A-Za-z]{3,}', txt):
            return False
        return not SKIP_RE.search(txt)

    def parse_score(s):
        # normalise "25- 21" spacing then split on , ; or space-before-digit
        s = re.sub(r'(\d+)\s+-\s*(\d+)', r'\1-\2', s)
        s = re.sub(r'(\d+)\s*-\s+(\d+)', r'\1-\2', s)
        pairs = []
        for part in re.split(r'[,;]\s*|\s+(?=\d+-\d)', s.strip()):
            m = re.match(r'(\d+)-(\d+)', part.strip())
            if m:
                pairs.append((int(m.group(1)), int(m.group(2))))
        return pairs

    def outcome(pairs, for_a):
        if not pairs:
            return None
        wa = sum(1 for a, b in pairs if a > b)
        wb = sum(1 for a, b in pairs if b > a)
        if wa == wb:
            return 'Split'
        winner = wa > wb
        return ('Won' if winner else 'Lost') if for_a else ('Lost' if winner else 'Won')

    # Locate CHAMPION cell → winner is the closest team name above it
    champion_pos = None
    for pos, txt in grid.items():
        if re.match(r'^CHAMPION$', txt, re.I):
            champion_pos = pos
            break

    champion_winner = None
    if champion_pos:
        cr, cc = champion_pos
        for off in range(1, 6):
            cand = grid.get((cr - off, cc), '')
            if cand and is_team(cand):
                champion_winner = cand
                break

    # Find all match ID cells
    match_pos = {}
    for (r, c), txt in grid.items():
        if re.match(r'^M\d+$', txt):
            match_pos.setdefault(txt, (r, c))  # keep first occurrence

    SCORE_RE = re.compile(r'^\d+-\d+')

    bracket_matches = []
    placements = []

    if champion_winner:
        placements.append({
            'tournament_id': db_tournament_id,
            'division': division,
            'bracket_tier': tier,
            'team_name': champion_winner,
            'placement': 1,
        })

    for mid, (mr, mc) in sorted(match_pos.items(), key=lambda x: int(x[0][1:])):
        teams_near, scores_near = [], []

        for r in range(max(0, mr - 2), mr + 9):
            for c in range(max(0, mc - 6), mc + 7):
                txt = grid.get((r, c), '')
                if not txt:
                    continue
                dist = abs(r - mr) + abs(c - mc)
                if is_team(txt):
                    teams_near.append((dist, r, c, txt))
                elif SCORE_RE.match(txt):
                    pairs = parse_score(txt)
                    if pairs:
                        scores_near.append((dist, txt, pairs))

        # Deduplicate team names keeping closest occurrence
        seen: dict[str, tuple] = {}
        for dist, r, c, name in teams_near:
            if name not in seen or dist < seen[name][0]:
                seen[name] = (dist, r, c)

        ordered = sorted(seen.items(), key=lambda x: x[1][0])
        if len(ordered) < 2:
            continue

        team_a, team_b = ordered[0][0], ordered[1][0]
        if team_a == team_b:
            continue

        score_pairs: list = []
        score_raw = ''
        if scores_near:
            scores_near.sort()
            score_raw = scores_near[0][1]
            score_pairs = scores_near[0][2]

        # Skip if no score and no champion inference
        oa = outcome(score_pairs, True)
        ob = outcome(score_pairs, False)
        if oa is None:
            if team_a == champion_winner:
                oa, ob = 'Won', 'Lost'
            elif team_b == champion_winner:
                oa, ob = 'Lost', 'Won'
            else:
                continue  # nothing to infer

        score_a = ','.join(f'{a}-{b}' for a, b in score_pairs)
        score_b = ','.join(f'{b}-{a}' for a, b in score_pairs)
        mid_hash = generate_id(f"{db_tournament_id}_{division}_{tier}_{mid}")

        bracket_matches.append({
            'match_id': mid_hash, 'tournament_id': db_tournament_id,
            'division': division, 'bracket_tier': tier, 'round_label': mid,
            'team_name': team_a, 'opponent_name': team_b,
            'outcome': oa, 'score_log': score_a,
        })
        bracket_matches.append({
            'match_id': mid_hash, 'tournament_id': db_tournament_id,
            'division': division, 'bracket_tier': tier, 'round_label': mid,
            'team_name': team_b, 'opponent_name': team_a,
            'outcome': ob, 'score_log': score_b,
        })

    return bracket_matches, placements

def extract_pool_data_v2(vstar_id, db_tournament_id, file_name, html=None):
    if html is None:
        url = f"{BASE_URL}/view.php?id={vstar_id}&file={file_name}"
        try:
            response = requests.get(url, headers=HEADERS, timeout=30)
            response.raise_for_status()
            html = response.text
        except requests.RequestException as exc:
            logger.warning(f"Failed to fetch result file {file_name} for {vstar_id}: {exc}")
            return [], [], [], []

    soup = BeautifulSoup(html, 'html.parser')
    
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
            if team_a.startswith("Seed ") or team_b.startswith("Seed "):
                logger.warning(
                    "Skipping unresolved matchup in %s %s %s: %s vs %s",
                    db_tournament_id,
                    current_division,
                    current_pool_name,
                    team_a,
                    team_b,
                )
                continue
            
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
            raw_cells = [' '.join(td.get_text().split()) for td in row.find_all('td')]
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
    tournaments_to_process = discover_tournaments()
    if not tournaments_to_process:
        logger.warning("No tournaments discovered from the VSTAR all-events page.")
        return
    
    db_tournaments = []
    db_teams = {}
    db_pools = {}
    db_standings = []
    db_matches = []
    db_bracket_matches = []
    db_bracket_placements = []

    for tournament in tournaments_to_process:
        vstar_id = tournament["vstar_id"]
        tournament_name = tournament["name"]
        db_tournament_id = vstar_id

        logger.info(f"Starting ETL for {tournament_name} ({db_tournament_id})...")

        t_html = get_tournament_page(vstar_id)
        if not t_html:
            logger.warning(f"Skipping {vstar_id}: No page found.")
            continue

        pool_files, bracket_files = parse_result_links(t_html, vstar_id)
        logger.info(f"  Found {len(pool_files)} pool files, {len(bracket_files)} bracket files.")
        db_tournaments.append({"tournament_id": db_tournament_id, "name": tournament_name})

        for f in pool_files:
            teams, pools, standings, matches = extract_pool_data_v2(vstar_id, db_tournament_id, f)
            logger.info(f"    Pool {f}: {len(teams)} teams, {len(matches)} matches.")
            for t in teams:
                if t['team_name'] not in db_teams:
                    db_teams[t['team_name']] = t
            for p in pools:
                db_pools[p['pool_id']] = p
            db_standings.extend(standings)
            db_matches.extend(matches)

        for f in bracket_files:
            b_html = get_html(f"{BASE_URL}/view.php?id={vstar_id}&file={f}")
            if not b_html:
                continue
            content_type = detect_bracket_content_type(b_html)
            if content_type == 'pool':
                teams, pools, standings, matches = extract_pool_data_v2(vstar_id, db_tournament_id, f, html=b_html)
                logger.info(f"    Bracket-pool {f}: {len(teams)} teams, {len(matches)} matches.")
                for t in teams:
                    if t['team_name'] not in db_teams:
                        db_teams[t['team_name']] = t
                for p in pools:
                    db_pools[p['pool_id']] = p
                db_standings.extend(standings)
                db_matches.extend(matches)
            else:
                b_matches, b_placements = extract_elimination_bracket(vstar_id, db_tournament_id, f, b_html)
                logger.info(f"    Bracket-elim {f}: {len(b_matches)//2 if b_matches else 0} matches, champion={'yes' if b_placements else 'no'}.")
                db_bracket_matches.extend(b_matches)
                db_bracket_placements.extend(b_placements)

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

    with open("data/bracket_matches.csv", 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["match_id", "tournament_id", "division", "bracket_tier", "round_label", "team_name", "opponent_name", "outcome", "score_log"])
        writer.writeheader()
        writer.writerows(db_bracket_matches)

    with open("data/bracket_placements.csv", 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["tournament_id", "division", "bracket_tier", "team_name", "placement"])
        writer.writeheader()
        writer.writerows(db_bracket_placements)

    logger.info(
        f"Total Extracted: {len(db_teams)} Teams, {len(db_pools)} Pools, {len(db_matches)} Pool Matches, "
        f"{len(db_bracket_matches)//2 if db_bracket_matches else 0} Bracket Matches, "
        f"{len(db_bracket_placements)} Champions across {len(db_tournaments)} tournaments."
    )
    logger.info("Database CSVs generated in data/ folder.")

if __name__ == "__main__":
    main()
