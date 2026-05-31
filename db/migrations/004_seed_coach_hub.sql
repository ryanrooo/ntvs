-- Seed 004: idempotent demo data for the Coach & Club Hub.
-- Rerun-safe: coaches/club_attributes use ON CONFLICT DO UPDATE; positions and
-- endorsements dedupe on their natural/expression unique indexes; verification
-- requests guard with NOT EXISTS; schedule/leaders adapt to whatever tournaments
-- already exist (so this seeds nothing rather than violating FKs on an empty DB).
-- Coach career totals are STORED demo values (per clarification), not computed.

SET search_path TO ntvs;

-- ── coaches ────────────────────────────────────────────────────────────────
INSERT INTO coaches (coach_key, display_name, base_slug, collision_rank, normalization_status,
                     club_key, role, city, initials, gradient, verified, about,
                     wins, win_rate, commits, gold, seasons, certifications, specialties)
VALUES
 ('maria-alvarez','Maria Alvarez','maria-alvarez',1,'direct','drive-nation','Head Coach — 17 Open','Frisco','MA','linear-gradient(135deg,#f5c518,#ff8a3d)',TRUE,
  'Eleven seasons developing nationally ranked 17s with a player-first, defense-anchored system.',
  312,0.812,14,6,11,ARRAY['USAV CAP III','SafeSport Trained','IMPACT'],ARRAY['Serve-receive','Player development','Recruiting']),
 ('james-carter','James Carter','james-carter',1,'direct','madfrog','Club Director — 16s','Plano','JC','linear-gradient(135deg,#5bb8ff,#8b5cf6)',TRUE,
  'Club director and 16s lead focused on building competitive depth across the program.',
  268,0.744,9,4,9,ARRAY['USAV CAP II','SafeSport Trained'],ARRAY['Program building','Blocking systems']),
 ('priya-nair','Priya Nair','priya-nair',1,'direct','skyline-juniors','Head Coach — 15 National','Dallas','PN','linear-gradient(135deg,#4ade80,#22d3ee)',FALSE,
  'Fifth-year head coach emphasizing fast tempo offense and young-athlete confidence.',
  141,0.690,3,1,5,ARRAY['USAV CAP I','SafeSport Trained'],ARRAY['Tempo offense','Setter training']),
 ('devon-brooks','Devon Brooks','devon-brooks',1,'direct','tav','Assistant — 18 Elite','Arlington','DB','linear-gradient(135deg,#f5c518,#4ade80)',TRUE,
  'Assistant on a perennial 18 Elite contender; specializes in serving and transition.',
  198,0.701,7,2,7,ARRAY['USAV CAP II','SafeSport Trained'],ARRAY['Serving','Transition offense']),
 ('sara-kim','Sara Kim','sara-kim',1,'direct','dynasty','Head Coach — 14 Premier','McKinney','SK','linear-gradient(135deg,#ff8a3d,#f87171)',FALSE,
  'Builds fundamentals and competitive habits in younger premier teams.',
  88,0.640,1,0,3,ARRAY['USAV CAP I','SafeSport Trained'],ARRAY['Fundamentals','Ball control']),
 ('carlos-mendez','Carlos Mendez','carlos-mendez',1,'direct','drive-nation','Head Coach — 18 Open','Frisco','CM','linear-gradient(135deg,#5bb8ff,#4ade80)',TRUE,
  'Fourteen seasons and multiple national medals leading flagship 18 Open teams.',
  401,0.835,22,8,14,ARRAY['USAV CAP III','SafeSport Trained','IMPACT'],ARRAY['Recruiting','Offensive systems','Leadership']),
 ('emily-zhang','Emily Zhang','emily-zhang',1,'direct','excel','Recruiting Coordinator','Allen','EZ','linear-gradient(135deg,#8b5cf6,#f5c518)',FALSE,
  'Connects families with college programs and coordinates recruiting events.',
  0,0.000,5,0,4,ARRAY['SafeSport Trained'],ARRAY['Recruiting','College placement']),
 ('marcus-webb','Marcus Webb','marcus-webb',1,'direct',NULL,'Skills Trainer','Denton','MW','linear-gradient(135deg,#94a3b8,#5bb8ff)',FALSE,
  'Independent skills trainer working with hitters and liberos across area clubs.',
  54,0.610,0,0,2,ARRAY['SafeSport Trained'],ARRAY['Hitting mechanics','Defense']),
 ('sara-kim-2','Sara Kim','sara-kim',2,'collision-resolved','tav','Assistant — 16 National','Arlington','SK','linear-gradient(135deg,#22d3ee,#8b5cf6)',FALSE,
  'Second-year assistant supporting a competitive 16 National group.',
  36,0.580,0,0,2,ARRAY['USAV CAP I'],ARRAY['Defense','Serve-receive'])
ON CONFLICT (coach_key) DO UPDATE SET
    display_name=EXCLUDED.display_name, base_slug=EXCLUDED.base_slug,
    collision_rank=EXCLUDED.collision_rank, normalization_status=EXCLUDED.normalization_status,
    club_key=EXCLUDED.club_key, role=EXCLUDED.role, city=EXCLUDED.city,
    initials=EXCLUDED.initials, gradient=EXCLUDED.gradient, verified=EXCLUDED.verified,
    about=EXCLUDED.about, wins=EXCLUDED.wins, win_rate=EXCLUDED.win_rate,
    commits=EXCLUDED.commits, gold=EXCLUDED.gold, seasons=EXCLUDED.seasons,
    certifications=EXCLUDED.certifications, specialties=EXCLUDED.specialties;

-- ── coach_positions (career timeline + "teams coached") ─────────────────────
INSERT INTO coach_positions (coach_key, club_key, club_label, club_color, role, age_group, years, record, note, status)
VALUES
 ('maria-alvarez','drive-nation','Drive Nation','#f5c518','Head Coach','17 Open','2021–2025','84–12','Two regional titles.','verified'),
 ('maria-alvarez','north-texas-elite','North Texas Elite','#5bb8ff','Assistant Coach','16 National','2018–2021','51–20',NULL,'verified'),
 ('carlos-mendez','drive-nation','Drive Nation','#5bb8ff','Head Coach','18 Open','2019–2025','120–18','Multiple national medals.','verified'),
 ('carlos-mendez','madfrog','MadFrog','#8b5cf6','Assistant Coach','17 Open','2016–2019','66–22',NULL,'verified'),
 ('james-carter','madfrog','MadFrog','#5bb8ff','Club Director','16s','2017–2025','140–40','Oversees 16s program.','verified'),
 ('devon-brooks','tav','TAV','#f5c518','Assistant Coach','18 Elite','2020–2025','70–28',NULL,'verified'),
 ('priya-nair','skyline-juniors','Skyline Juniors','#4ade80','Head Coach','15 National','2022–2025','48–22','Awaiting club confirmation.','pending'),
 ('sara-kim','dynasty','Dynasty','#ff8a3d','Head Coach','14 Premier','2023–2025','30–18',NULL,'pending'),
 ('emily-zhang','excel','Excel','#8b5cf6','Recruiting Coordinator',NULL,'2021–2025',NULL,NULL,'pending'),
 ('marcus-webb',NULL,'Independent','#94a3b8','Skills Trainer',NULL,'2023–2025',NULL,'Not affiliated with a single club.','pending'),
 ('sara-kim-2','tav','TAV','#22d3ee','Assistant Coach','16 National','2024–2025','18–10',NULL,'pending')
ON CONFLICT (coach_key, club_label, role, COALESCE(years, '')) DO NOTHING;

-- ── endorsements (fixed dates so re-seed is idempotent) ─────────────────────
INSERT INTO endorsements (coach_key, author_label, relationship, stars, tags, body, created_at, created_date, body_hash)
VALUES
 ('maria-alvarez','Parent of an OH','Parent',5,ARRAY['Development','Communication'],
  'Maria turned my daughter into a confident hitter and kept her loving the game.', TIMESTAMPTZ '2026-05-02 14:00:00+00', DATE '2026-05-02', md5(lower('Maria turned my daughter into a confident hitter and kept her loving the game.'))),
 ('maria-alvarez','Former Player','Player',5,ARRAY['Development','Culture'],
  'Best coach I ever had. Pushed us hard and always had our backs.', TIMESTAMPTZ '2026-05-04 14:00:00+00', DATE '2026-05-04', md5(lower('Best coach I ever had. Pushed us hard and always had our backs.'))),
 ('maria-alvarez','Club Staff','Club staff',4,ARRAY['Leadership'],
  'Reliable, organized, and great with families all season long.', TIMESTAMPTZ '2026-05-06 14:00:00+00', DATE '2026-05-06', md5(lower('Reliable, organized, and great with families all season long.'))),
 ('carlos-mendez','Parent of an MB','Parent',5,ARRAY['Recruiting','Leadership'],
  'Carlos helped our family navigate recruiting and our son committed early.', TIMESTAMPTZ '2026-05-03 14:00:00+00', DATE '2026-05-03', md5(lower('Carlos helped our family navigate recruiting and our son committed early.'))),
 ('carlos-mendez','Fellow Coach','Fellow coach',5,ARRAY['Systems'],
  'One of the sharpest offensive minds in the region. Always positive.', TIMESTAMPTZ '2026-05-05 14:00:00+00', DATE '2026-05-05', md5(lower('One of the sharpest offensive minds in the region. Always positive.'))),
 ('devon-brooks','Parent','Parent',4,ARRAY['Serving','Communication'],
  'Devon is patient and our serving improved so much this season.', TIMESTAMPTZ '2026-05-03 14:00:00+00', DATE '2026-05-03', md5(lower('Devon is patient and our serving improved so much this season.'))),
 ('devon-brooks','Player','Player',5,ARRAY['Development'],
  'Coach Devon believed in me and helped me earn a starting spot.', TIMESTAMPTZ '2026-05-07 14:00:00+00', DATE '2026-05-07', md5(lower('Coach Devon believed in me and helped me earn a starting spot.'))),
 ('james-carter','Parent','Parent',5,ARRAY['Leadership','Culture'],
  'Great director who keeps the whole club running smoothly.', TIMESTAMPTZ '2026-05-04 14:00:00+00', DATE '2026-05-04', md5(lower('Great director who keeps the whole club running smoothly.'))),
 ('priya-nair','Parent of a setter','Parent',5,ARRAY['Setter training','Tempo'],
  'Priya developed my setter''s tempo and decision making beautifully.', TIMESTAMPTZ '2026-05-06 14:00:00+00', DATE '2026-05-06', md5(lower('Priya developed my setter''s tempo and decision making beautifully.')))
ON CONFLICT (coach_key, author_label, body_hash, created_date) DO NOTHING;

-- ── verification_requests (pending director queue items) ────────────────────
INSERT INTO verification_requests (coach_key, club_key, position_id, name, initials, color, role, claim_years, match_strength, match_pct, note)
SELECT 'priya-nair','skyline-juniors',
       (SELECT position_id FROM coach_positions WHERE coach_key='priya-nair' AND club_label='Skyline Juniors' LIMIT 1),
       'Priya Nair','PN','#4ade80','Head Coach — 15 National','2022–2025','Partial',62,'Please confirm my 15 National head coach role.'
WHERE NOT EXISTS (SELECT 1 FROM verification_requests WHERE coach_key='priya-nair' AND club_key='skyline-juniors' AND status='pending');

INSERT INTO verification_requests (coach_key, club_key, position_id, name, initials, color, role, claim_years, match_strength, match_pct, note)
SELECT 'sara-kim','dynasty',
       (SELECT position_id FROM coach_positions WHERE coach_key='sara-kim' AND club_label='Dynasty' LIMIT 1),
       'Sara Kim','SK','#ff8a3d','Head Coach — 14 Premier','2023–2025','Strong',81,'Confirming my 14 Premier head coach position.'
WHERE NOT EXISTS (SELECT 1 FROM verification_requests WHERE coach_key='sara-kim' AND club_key='dynasty' AND status='pending');

INSERT INTO verification_requests (coach_key, club_key, position_id, name, initials, color, role, claim_years, match_strength, match_pct, note)
SELECT 'sara-kim-2','tav',
       (SELECT position_id FROM coach_positions WHERE coach_key='sara-kim-2' AND club_label='TAV' LIMIT 1),
       'Sara Kim','SK','#22d3ee','Assistant — 16 National','2024–2025','Partial',55,'Requesting confirmation of my assistant role.'
WHERE NOT EXISTS (SELECT 1 FROM verification_requests WHERE coach_key='sara-kim-2' AND club_key='tav' AND status='pending');

-- ── club_attributes (presentation/comparison; harmless if club not canonical) ─
INSERT INTO club_attributes (club_key, tier, color, gold, silver, bronze, commits, coaches_count, fee, est_year, about,
                             radar_win, radar_depth, radar_gold, radar_dev, radar_alumni)
VALUES
 ('drive-nation',1,'#f5c518',8,5,4,42,18,3200,2009,'Flagship North Texas program with national reach.',0.92,0.88,0.95,0.85,0.90),
 ('madfrog',1,'#5bb8ff',6,7,5,28,16,2950,2004,'Long-standing Plano club known for depth.',0.84,0.90,0.80,0.82,0.78),
 ('tav',1,'#8b5cf6',7,4,6,31,20,3100,1998,'Texas Advantage Volleyball, perennial contender.',0.88,0.86,0.84,0.80,0.83),
 ('skyline-juniors',2,'#4ade80',2,3,4,9,9,2400,2014,'Developing Dallas club on the rise.',0.70,0.66,0.62,0.78,0.55),
 ('dynasty',2,'#ff8a3d',1,2,3,5,8,2200,2016,'Younger premier-focused program.',0.64,0.60,0.55,0.72,0.48),
 ('excel',3,'#a78bfa',0,1,2,7,6,2000,2018,'Recruiting-forward club in Allen.',0.58,0.55,0.45,0.62,0.60),
 ('north-texas-elite',2,'#22d3ee',3,4,3,12,10,2600,2011,'Established mid-tier program.',0.74,0.70,0.68,0.71,0.66)
ON CONFLICT (club_key) DO UPDATE SET
    tier=EXCLUDED.tier, color=EXCLUDED.color, gold=EXCLUDED.gold, silver=EXCLUDED.silver,
    bronze=EXCLUDED.bronze, commits=EXCLUDED.commits, coaches_count=EXCLUDED.coaches_count,
    fee=EXCLUDED.fee, est_year=EXCLUDED.est_year, about=EXCLUDED.about,
    radar_win=EXCLUDED.radar_win, radar_depth=EXCLUDED.radar_depth, radar_gold=EXCLUDED.radar_gold,
    radar_dev=EXCLUDED.radar_dev, radar_alumni=EXCLUDED.radar_alumni;

-- ── tournament_schedule (adaptive: derived from existing tournaments) ────────
INSERT INTO tournament_schedule (tournament_id, event_date, month_key, venue, city, team_count,
                                 age_lo, age_hi, division, status, within_mi, featured, completed)
SELECT
    t.tournament_id,
    (DATE '2026-03-01' + ((n.rn % 16) * 7))                        AS event_date,
    to_char(DATE '2026-03-01' + ((n.rn % 16) * 7), 'YYYY-MM')      AS month_key,
    (ARRAY['Irving Convention Center','Dallas Market Hall','Esports Stadium Arlington','Plano Event Center'])[1 + (n.rn % 4)] AS venue,
    (ARRAY['Irving','Dallas','Arlington','Plano','Frisco'])[1 + (n.rn % 5)] AS city,
    24 + (n.rn % 5) * 8                                            AS team_count,
    12, 18,
    (ARRAY['Open','National','Premier'])[1 + (n.rn % 3)]           AS division,
    (ARRAY['Open','Filling','Waitlist'])[1 + (n.rn % 3)]           AS status,
    (ARRAY[10,25,40,60])[1 + (n.rn % 4)]                           AS within_mi,
    (n.rn = 0)                                                     AS featured,
    (n.rn % 2 = 1)                                                 AS completed
FROM (
    SELECT tournament_id, (ROW_NUMBER() OVER (ORDER BY tournament_id) - 1)::int AS rn
    FROM tournaments
) AS n
JOIN tournaments t ON t.tournament_id = n.tournament_id
ON CONFLICT (tournament_id) DO UPDATE SET
    event_date=EXCLUDED.event_date, month_key=EXCLUDED.month_key, venue=EXCLUDED.venue,
    city=EXCLUDED.city, team_count=EXCLUDED.team_count, age_lo=EXCLUDED.age_lo, age_hi=EXCLUDED.age_hi,
    division=EXCLUDED.division, status=EXCLUDED.status, within_mi=EXCLUDED.within_mi,
    featured=EXCLUDED.featured, completed=EXCLUDED.completed;

-- ── stat_leaders (adaptive: a few leaders for the earliest tournament) ───────
INSERT INTO stat_leaders (tournament_id, category, rank, player_name, club_label, value)
SELECT first_t.tournament_id, v.category, v.rank, v.player_name, v.club_label, v.value
FROM (SELECT tournament_id FROM tournaments ORDER BY tournament_id LIMIT 1) AS first_t
CROSS JOIN (
    VALUES
      ('kills',1,'A. Johnson','Drive Nation',58),
      ('kills',2,'B. Lee','MadFrog',51),
      ('kills',3,'C. Ortiz','TAV',47),
      ('assists',1,'D. Patel','Drive Nation',132),
      ('assists',2,'E. Nguyen','Skyline Juniors',118),
      ('digs',1,'F. Garcia','TAV',96),
      ('digs',2,'G. Smith','Dynasty',88)
) AS v(category, rank, player_name, club_label, value)
ON CONFLICT (tournament_id, category, rank) DO NOTHING;
