// NTVS Prototype — data store
const CLUBS = [
  { id: "tav", name: "Texas Advantage",   city: "Plano",      tier: 1, win: 0.78, teams: 24, gold: 9, silver: 6, bronze: 4, color: "#f5c518", est: 2009, rank: 1, commits: 38, coaches: 14, fee: 3400, vals: [0.9,0.78,0.85,0.7,0.95], about: "Plano-based program in the USAV Lone Star Region. Known for setter development and consistent 18-Open qualification. Trains in a 6-court West Plano facility." },
  { id: "drv", name: "Drive Nation",      city: "Frisco",     tier: 1, win: 0.74, teams: 22, gold: 8, silver: 5, bronze: 7, color: "#5bb8ff", est: 2012, rank: 2, commits: 41, coaches: 12, fee: 3650, vals: [0.82,0.74,0.7,0.88,0.8], about: "Frisco powerhouse with a national footprint. Deep 17s and 18s, strong defensive systems, and a large recruiting pipeline." },
  { id: "scv", name: "Skyline Club",      city: "Dallas",     tier: 1, win: 0.71, teams: 19, gold: 6, silver: 8, bronze: 5, color: "#a78bfa", est: 2010, rank: 3, commits: 29, coaches: 11, fee: 3500, vals: [0.78,0.71,0.62,0.76,0.7], about: "Dallas club with a balanced age-group spread and a reputation for clean serve-receive and gritty defense." },
  { id: "trn", name: "Texas Tornados",    city: "Fort Worth", tier: 2, win: 0.65, teams: 16, gold: 4, silver: 6, bronze: 6, color: "#fb923c", est: 2014, rank: 6, commits: 19, coaches: 8,  fee: 2900, vals: [0.6,0.65,0.55,0.6,0.5], about: "Fort Worth program on the rise, focused on player development from 13s up." },
  { id: "ntx", name: "North Texas Elite", city: "Denton",     tier: 2, win: 0.61, teams: 14, gold: 3, silver: 5, bronze: 8, color: "#4ade80", est: 2015, rank: 8, commits: 14, coaches: 9,  fee: 2750, vals: [0.55,0.61,0.45,0.62,0.42], about: "Denton-based club with strong ties to UNT and a developmental philosophy." },
  { id: "lon", name: "Lone Star VBC",     city: "Arlington",  tier: 2, win: 0.58, teams: 13, gold: 2, silver: 7, bronze: 5, color: "#f472b6", est: 2013, rank: 11, commits: 12, coaches: 7, fee: 2800, vals: [0.5,0.58,0.4,0.55,0.38], about: "Arlington club known for competitive 16s and a tight-knit community." },
  { id: "mck", name: "McKinney Spike",    city: "McKinney",   tier: 3, win: 0.49, teams: 9,  gold: 1, silver: 3, bronze: 4, color: "#94a3b8", est: 2018, rank: 19, commits: 5,  coaches: 6, fee: 2400, vals: [0.4,0.49,0.3,0.45,0.25], about: "Younger McKinney club building its base in the 12s–15s ranks." },
  { id: "all", name: "Allen Aces",        city: "Allen",      tier: 3, win: 0.46, teams: 8,  gold: 1, silver: 2, bronze: 5, color: "#94a3b8", est: 2019, rank: 22, commits: 4,  coaches: 5, fee: 2350, vals: [0.38,0.46,0.28,0.42,0.22], about: "Allen-based developmental club focused on first- and second-year players." },
];
const clubById = (id) => CLUBS.find((c) => c.id === id);

// Teams per club (for profile)
const TEAMS = {
  tav: [
    ["18 Elite", "Maria Delgado", "31–6", 1, "USAV 18 Open"],
    ["17 Elite", "James Whitfield", "28–9", 1, "USAV 17 Open"],
    ["16 Elite", "Dana Cho", "26–11", 2, "USAV 16 Open"],
    ["16 Black", "Pete Ramos", "22–13", 3, "USAV 16 USA"],
    ["15 Elite", "Karen Voss", "24–10", 2, "USAV 15 Open"],
    ["14 Elite", "Tom Becker", "19–14", 3, "USAV 14 Open"],
  ],
  drv: [
    ["18 Black", "Maria Delgado", "31–6", 1, "USAV 18 Open"],
    ["17 National", "Greg Salas", "27–10", 2, "USAV 17 Open"],
    ["16 Black", "Lia Moreno", "24–12", 3, "USAV 16 Open"],
    ["15 National", "Drew Kim", "22–11", 2, "USAV 15 Open"],
  ],
  scv: [
    ["18 Royal", "Priya Nair", "26–12", 2, "USAV 18 Open"],
    ["17 Royal", "Carlos Vega", "23–13", 3, "USAV 17 Open"],
    ["16 Royal", "Beth Lang", "21–14", 3, "USAV 16 USA"],
  ],
};
const genericTeams = (c) => [
  [`18 ${c.tier===1?"Elite":"Black"}`, "Staff Coach", "22–13", 2, "USAV 18 Open"],
  [`17 ${c.tier===1?"Elite":"Black"}`, "Staff Coach", "20–14", 3, "USAV 17 USA"],
  [`16 ${c.tier===1?"Elite":"Black"}`, "Staff Coach", "18–15", 3, "USAV 16 USA"],
];
const teamsFor = (id) => TEAMS[id] || genericTeams(clubById(id));

const COMMITS = {
  tav: [["Ava Sanders", "OH", "Baylor"], ["Mia Tran", "S", "TCU"], ["Reese Okafor", "MB", "Texas Tech"]],
  drv: [["Jordan Lee", "S", "Texas"], ["Bella Reyes", "L", "Houston"], ["Quinn Adams", "OH", "SMU"]],
  scv: [["Priya N.", "OH", "North Texas"], ["Sam Ortiz", "L", "UTA"]],
};
const commitsFor = (id) => COMMITS[id] || [["Recruit A", "OH", "TBD"], ["Recruit B", "MB", "TBD"]];

const winHistory = (c) => {
  const base = Math.round(c.win * 100);
  return [["’20", base-16], ["’21", base-12], ["’22", base-8], ["’23", base-5], ["’24", base-3], ["’25", base]];
};

// Coaches
const COACHES = [
  {
    id: "mdelgado", name: "Maria Delgado", init: "MD", verified: true, clubId: "drv",
    grad: "linear-gradient(135deg, #5bb8ff, #2563eb)",
    role: "Head Coach · 18 Black", city: "Frisco",
    totals: { wins: 189, winRate: 73, commits: 23, gold: 11, seasons: 10 },
    certs: ["USAV CAP III", "IMPACT Certified", "SafeSport Trained", "CPR / AED"],
    specialties: ["Setter development", "Serve-receive", "Recruiting", "Defense"],
    about: "Ten-year club coach focused on setter development and recruiting. Two-time regional champion.",
    career: [
      { yr: "2022 — Present", club: "Drive Nation", clubColor: "#5bb8ff", role: "Head Coach · 18 Black", rec: "59–15", note: "USAV 18 Open qualifier ’23, ’24, ’25. Bid to GJNC." },
      { yr: "2019 — 2022", club: "Texas Advantage", clubColor: "#f5c518", role: "Head Coach · 16/17 Elite", rec: "71–28", note: "Two regional golds. Developed 9 college commits." },
      { yr: "2016 — 2019", club: "Texas Tornados", clubColor: "#fb923c", role: "Assistant Coach · 15–17", rec: "—", note: "Recruiting + serve-receive systems." },
    ],
    teams: [
      ["18 Black", "2025", "Drive Nation", "31–6", "🥇"],
      ["18 Black", "2024", "Drive Nation", "28–9", "🥈"],
      ["17 Elite", "2022", "TX Advantage", "26–11", "🥇"],
      ["16 Elite", "2021", "TX Advantage", "24–10", "🥇"],
      ["17 Elite", "2020", "TX Advantage", "21–13", "🥉"],
      ["15 Black", "2018", "Tornados", "18–15", "—"],
    ],
    rating: 4.9, endorseCount: 62,
  },
  {
    id: "jwhitfield", name: "James Whitfield", init: "JW", verified: true, clubId: "tav",
    grad: "linear-gradient(135deg, #f5c518, #d97706)",
    role: "Head Coach · 17 Elite", city: "Plano",
    totals: { wins: 142, winRate: 68, commits: 16, gold: 7, seasons: 8 },
    certs: ["USAV CAP II", "IMPACT Certified", "SafeSport Trained"],
    specialties: ["Blocking", "Offense systems", "Player development"],
    about: "Offensive-minded coach with a focus on tempo and middle play.",
    career: [
      { yr: "2018 — Present", club: "Texas Advantage", clubColor: "#f5c518", role: "Head Coach · 16/17 Elite", rec: "98–41", note: "Regional gold ’22. Eight straight Open qualifications." },
      { yr: "2016 — 2018", club: "Skyline Club", clubColor: "#a78bfa", role: "Assistant · 15–16", rec: "—", note: "Built the middle-blocker pipeline." },
    ],
    teams: [
      ["17 Elite", "2025", "TX Advantage", "28–9", "🥇"],
      ["16 Elite", "2024", "TX Advantage", "25–12", "🥈"],
      ["17 Elite", "2023", "TX Advantage", "24–13", "🥉"],
    ],
    rating: 4.8, endorseCount: 44,
  },
  {
    id: "pnair", name: "Priya Nair", init: "PN", verified: false, clubId: "scv",
    grad: "linear-gradient(135deg, #a78bfa, #7c3aed)",
    role: "Head Coach · 18 Royal", city: "Dallas",
    totals: { wins: 96, winRate: 64, commits: 9, gold: 3, seasons: 6 },
    certs: ["USAV CAP II", "SafeSport Trained"],
    specialties: ["Defense", "Serve-receive", "Team culture"],
    about: "Defense-first coach building Skyline's 18s into a regional contender.",
    career: [
      { yr: "2020 — Present", club: "Skyline Club", clubColor: "#a78bfa", role: "Head Coach · 17/18 Royal", rec: "64–34", note: "Back-to-back Open qualifications." },
    ],
    teams: [
      ["18 Royal", "2025", "Skyline", "26–12", "🥈"],
      ["17 Royal", "2024", "Skyline", "23–13", "🥉"],
    ],
    rating: 4.7, endorseCount: 28,
  },
];
const coachById = (id) => COACHES.find((c) => c.id === id);

// Endorsements (positive-only) keyed by coach
const SEED_REVIEWS = {
  mdelgado: [
    { who: "Parent of an OH", rel: "2024–25 season", body: "Maria pushed my daughter to play her best while keeping it fun. Communication with families was outstanding — we always knew the plan.", tags: ["Great communicator", "Positive culture"], when: "Mar 2026", stars: 5 },
    { who: "Former player", rel: "18 Black alum", body: "Best setter coaching I've had. She turned my footwork around in one season and helped me through the entire recruiting process.", tags: ["Develops players", "Recruiting help"], when: "Feb 2026", stars: 5 },
    { who: "Assistant coach", rel: "Worked alongside", body: "Sets a standard for the whole gym. Practices are organized to the minute and every kid knows their role.", tags: ["Knows the game", "Punctual"], when: "Jan 2026", stars: 5 },
  ],
  jwhitfield: [
    { who: "Parent of an MB", rel: "2024–25 season", body: "James develops middles better than anyone in the region. My son's blocking transformed.", tags: ["Develops players", "Knows the game"], when: "Feb 2026", stars: 5 },
  ],
  pnair: [
    { who: "Player", rel: "18 Royal", body: "Coach Priya built a culture where everyone competes and supports each other. Loved my season.", tags: ["Positive culture", "Team-first"], when: "Jan 2026", stars: 5 },
  ],
};
const ENDORSE_TAGS = ["Great communicator", "Develops players", "Positive culture", "Knows the game", "Recruiting help", "Punctual", "Team-first", "Motivating"];

// Tournaments
const TOURNAMENTS = [
  { id: "lsc", d: "8–9", mo: "MAR", monthKey: "MAR", name: "Lone Star Classic", venue: "Allen Sports Pavilion", city: "Allen", teams: 212, ageLo: 12, ageHi: 18, div: "Open + USA", status: "Open", within: 12, feat: true, done: true },
  { id: "ppl", d: "15", mo: "MAR", monthKey: "MAR", name: "Plano Power League #4", venue: "Plano Event Center", city: "Plano", teams: 96, ageLo: 13, ageHi: 17, div: "Club", status: "Open", within: 20, done: false },
  { id: "r9q", d: "22–23", mo: "MAR", monthKey: "MAR", name: "Region 9 Qualifier", venue: "Kay Bailey Hutchison CC", city: "Dallas", teams: 340, ageLo: 14, ageHi: 18, div: "Open", status: "Filling", within: 28, feat: true, done: false },
  { id: "fss", d: "29", mo: "MAR", monthKey: "MAR", name: "Frisco Spring Slam", venue: "Comerica Center", city: "Frisco", teams: 128, ageLo: 12, ageHi: 16, div: "Club + USA", status: "Open", within: 18, done: false },
  { id: "dfw", d: "5–6", mo: "APR", monthKey: "APR", name: "DFW Showcase", venue: "Esports Stadium Arlington", city: "Arlington", teams: 180, ageLo: 15, ageHi: 18, div: "Open", status: "Waitlist", within: 35, done: false },
  { id: "den", d: "12", mo: "APR", monthKey: "APR", name: "Denton Invitational", venue: "UNT Volleyball Center", city: "Denton", teams: 64, ageLo: 12, ageHi: 15, div: "Club", status: "Open", within: 48, done: false },
  { id: "lsrc", d: "19–20", mo: "APR", monthKey: "APR", name: "Lone Star Region Champs", venue: "Fort Worth Convention Ctr", city: "Fort Worth", teams: 410, ageLo: 12, ageHi: 18, div: "Open + USA", status: "Filling", within: 38, feat: true, done: false },
];
const tourneyById = (id) => TOURNAMENTS.find((t) => t.id === id);

// Director verification queue
const SEED_REQUESTS = [
  { id: "rq1", name: "Maria Delgado", init: "MD", color: "#5bb8ff", role: "Head Coach · 18 Black", claim: "2022–Present", match: "Strong", matchPct: 96, note: "Matched to 47 logged matches under this team.", when: "2h ago" },
  { id: "rq2", name: "Pete Ramos", init: "PR", color: "#fb923c", role: "Assistant · 16 Black", claim: "2024–Present", match: "Strong", matchPct: 91, note: "Matched to 23 logged matches.", when: "5h ago" },
  { id: "rq3", name: "Karen Voss", init: "KV", color: "#a78bfa", role: "Head Coach · 15 Elite", claim: "2023–Present", match: "Partial", matchPct: 64, note: "Some matches unlinked — review roster.", when: "1d ago" },
];

Object.assign(window, {
  CLUBS, clubById, teamsFor, commitsFor, winHistory,
  COACHES, coachById, SEED_REVIEWS, ENDORSE_TAGS,
  TOURNAMENTS, tourneyById, SEED_REQUESTS,
});
