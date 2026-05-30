// NTVS Prototype — Clubs directory + Club profile
function PClubs() {
  const { go, store } = useNav();
  const [q, setQ] = useState("");
  const [tier, setTier] = useState(0);
  const [sort, setSort] = useState("rank");
  let list = CLUBS.filter((c) =>
    (tier === 0 || c.tier === tier) &&
    (q === "" || c.name.toLowerCase().includes(q.toLowerCase()) || c.city.toLowerCase().includes(q.toLowerCase()))
  );
  list = [...list].sort((a, b) => sort === "rank" ? a.rank - b.rank : sort === "win" ? b.win - a.win : b.teams - a.teams);
  const pinned = store.compare;

  return (
    <div className="page">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginBottom: 22 }}>
        <div>
          <div className="kicker" style={{ marginBottom: 10 }}>Directory · 84 clubs</div>
          <h1 style={{ fontSize: 40 }}>North Texas clubs</h1>
        </div>
        <button className="btn btn-primary" onClick={() => go("compare")} style={{ position: "relative" }}>
          Compare {pinned.length > 0 && <span className="chip chip-amber" style={{ fontSize: 10, padding: "2px 7px" }}>{pinned.length}</span>}
        </button>
      </div>

      {/* controls */}
      <div style={{ display: "flex", gap: 12, marginBottom: 20, alignItems: "center", flexWrap: "wrap" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 8, padding: "9px 13px", width: 300 }}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--muted)" strokeWidth="2"><circle cx="11" cy="11" r="7" /><path d="m21 21-4.3-4.3" /></svg>
          <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search clubs or cities…" style={{ background: "transparent", border: 0, outline: "none", color: "var(--fg)", fontSize: 13, fontFamily: "inherit", width: "100%" }} />
        </div>
        <div style={{ display: "flex", gap: 4, background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 8, padding: 4 }}>
          {[["All tiers", 0], ["Tier 1", 1], ["Tier 2", 2], ["Tier 3", 3]].map(([l, t]) => (
            <div key={l} className={`nav-link ${tier === t ? "active" : ""}`} style={{ fontSize: 12 }} onClick={() => setTier(t)}>{l}</div>
          ))}
        </div>
        <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 8 }}>
          <span className="label">Sort</span>
          {[["Rank", "rank"], ["Win %", "win"], ["Teams", "teams"]].map(([l, s]) => (
            <span key={s} className="chip" style={{ fontSize: 12, cursor: "pointer", padding: "6px 11px", background: sort === s ? "var(--surface-2)" : "transparent", color: sort === s ? "var(--fg)" : "var(--muted)", border: "1px solid var(--border)" }} onClick={() => setSort(s)}>{l}</span>
          ))}
        </div>
      </div>

      {/* table */}
      <div className="card" style={{ overflow: "hidden" }}>
        <div style={{ display: "grid", gridTemplateColumns: "60px 1fr 90px 130px 90px 110px 120px", padding: "11px 20px", background: "var(--bg-2)", borderBottom: "1px solid var(--border)" }}>
          {["Rank", "Club", "Win %", "Form", "Teams", "Medals", ""].map((h, i) => <div key={i} className="label">{h}</div>)}
        </div>
        {list.map((c, i) => {
          const onCompare = pinned.includes(c.id);
          return (
            <div key={c.id} className="row-hover" style={{ display: "grid", gridTemplateColumns: "60px 1fr 90px 130px 90px 110px 120px", padding: "13px 20px", borderTop: i ? "1px solid var(--border-soft)" : "none", alignItems: "center", cursor: "pointer" }} onClick={() => go("club", { id: c.id })}>
              <div className="stat-num" style={{ fontSize: 18, color: c.rank <= 3 ? "var(--accent)" : "var(--muted)" }}>#{c.rank}</div>
              <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                <ClubMark c={c} size={34} />
                <div>
                  <div style={{ fontWeight: 600, fontSize: 14, display: "flex", alignItems: "center", gap: 8 }}>{c.name} <span className={`tier tier-${c.tier}`}>T{c.tier}</span></div>
                  <div style={{ fontSize: 12, color: "var(--muted)", marginTop: 2 }}>{c.city}, TX</div>
                </div>
              </div>
              <div className="mono tabular" style={{ fontSize: 14 }}>{Math.round(c.win * 100)}%</div>
              <Sparkline data={[4, 5, 4, 6, 5, 7, 6, Math.round(c.win * 10)]} color={c.color} w={110} h={26} />
              <div className="mono tabular" style={{ fontSize: 14 }}>{c.teams}</div>
              <div style={{ fontSize: 12, color: "var(--fg-2)" }}>🥇{c.gold} 🥈{c.silver}</div>
              <div onClick={(e) => { e.stopPropagation(); store.toggleCompare(c.id); }}>
                <span className="chip" style={{ fontSize: 11, padding: "6px 11px", cursor: "pointer", background: onCompare ? "var(--accent)" : "var(--surface-2)", color: onCompare ? "#0a0a0a" : "var(--fg-2)", fontWeight: 600 }}>
                  {onCompare ? "✓ Pinned" : "+ Compare"}
                </span>
              </div>
            </div>
          );
        })}
        {list.length === 0 && <div style={{ padding: 40, textAlign: "center", color: "var(--muted)", fontSize: 14 }}>No clubs match “{q}”.</div>}
      </div>
    </div>
  );
}

function PClub({ id }) {
  const { go, store } = useNav();
  const c = clubById(id) || CLUBS[0];
  const teams = teamsFor(c.id);
  const commits = commitsFor(c.id);
  const hist = winHistory(c);
  const onCompare = store.compare.includes(c.id);
  const maxMedal = c.gold + c.silver + c.bronze;
  return (
    <div className="page" style={{ padding: 0 }}>
      <div style={{ padding: "28px 56px 28px", borderBottom: "1px solid var(--border)", background: `linear-gradient(180deg, ${c.color}14, transparent)` }}>
        <div style={{ fontSize: 12, color: "var(--muted)", marginBottom: 18 }}>
          <span style={{ cursor: "pointer" }} onClick={() => go("clubs")}>Clubs</span> / North Texas / <span style={{ color: "var(--fg-2)" }}>{c.name}</span>
        </div>
        <div style={{ display: "flex", gap: 24, alignItems: "center" }}>
          <ClubMark c={c} size={76} radius={16} />
          <div style={{ flex: 1 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
              <h1 style={{ fontSize: 40 }}>{c.name}</h1>
              <span className={`tier tier-${c.tier}`} style={{ fontSize: 12 }}>TIER {c.tier}</span>
            </div>
            <div style={{ display: "flex", gap: 18, marginTop: 8, fontSize: 13, color: "var(--muted)" }}>
              <span>📍 {c.city}, TX</span><span>Est. {c.est}</span><span>{c.teams} teams · 12s–18s</span>
            </div>
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            <button className="btn" onClick={() => { store.toggleCompare(c.id); }} style={{ background: onCompare ? "var(--accent)" : undefined, color: onCompare ? "#0a0a0a" : undefined, borderColor: onCompare ? "var(--accent)" : undefined, fontWeight: onCompare ? 600 : 500 }}>{onCompare ? "✓ Pinned to compare" : "＋ Compare"}</button>
            <button className="btn" onClick={() => store.toast("Following " + c.name)}>Follow</button>
          </div>
        </div>
        <div style={{ display: "flex", gap: 40, marginTop: 26 }}>
          {[[`#${c.rank}`, "National rank"], [`${Math.round(c.win * 100)}%`, "Win rate"], [c.gold, "Gold medals"], [c.commits, "College commits"], [c.coaches, "Coaches"]].map(([v, k]) => (
            <div key={k}><div className="stat-num" style={{ fontSize: 32 }}>{v}</div><div className="label" style={{ marginTop: 4 }}>{k}</div></div>
          ))}
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1.7fr 1fr", gap: 40, padding: "32px 56px 56px" }}>
        <div>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 16 }}>
            <h2 style={{ fontSize: 24 }}>Teams · 2025–26</h2>
            <div style={{ fontSize: 12, color: "var(--muted)" }}>Sorted by age group</div>
          </div>
          <div className="card" style={{ overflow: "hidden" }}>
            <div style={{ display: "grid", gridTemplateColumns: "1.4fr 1.6fr 0.9fr 0.7fr 1.2fr", padding: "11px 18px", background: "var(--bg-2)", borderBottom: "1px solid var(--border)" }}>
              {["Team", "Head coach", "Record", "Finish", "Division"].map((h) => <div key={h} className="label">{h}</div>)}
            </div>
            {teams.map(([t, coach, rec, fin, div], i) => {
              const co = COACHES.find((x) => x.name === coach);
              return (
                <div key={i} style={{ display: "grid", gridTemplateColumns: "1.4fr 1.6fr 0.9fr 0.7fr 1.2fr", padding: "13px 18px", borderTop: i ? "1px solid var(--border-soft)" : "none", alignItems: "center", fontSize: 13 }}>
                  <div style={{ fontWeight: 600 }}>{t}</div>
                  <div style={{ color: co ? "var(--cyan)" : "var(--fg-2)", cursor: co ? "pointer" : "default" }} onClick={() => co && go("coach", { id: co.id })}>{coach}</div>
                  <div className="mono tabular">{rec}</div>
                  <div><span className={fin === 1 ? "chip chip-amber" : fin === 2 ? "chip chip-cyan" : "chip"} style={{ fontSize: 10 }}>{fin === 1 ? "🥇 Gold" : fin === 2 ? "🥈 Silver" : "🥉 Bronze"}</span></div>
                  <div style={{ color: "var(--muted)", fontSize: 12 }}>{div}</div>
                </div>
              );
            })}
          </div>

          <h2 style={{ fontSize: 24, margin: "32px 0 16px" }}>Performance trend</h2>
          <div className="card" style={{ padding: 22 }}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 16 }}>
              <div className="label">Win % by season</div>
              <div style={{ display: "flex", gap: 14, fontSize: 11, color: "var(--muted)" }}>
                <span><span style={{ color: "var(--accent)" }}>●</span> This club</span>
                <span><span style={{ color: "var(--muted-2)" }}>●</span> Region avg</span>
              </div>
            </div>
            <div style={{ display: "flex", alignItems: "flex-end", gap: 18, height: 160 }}>
              {hist.map(([yr, v], i) => {
                const avg = 52 + i;
                return (
                  <div key={yr} style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", gap: 8 }}>
                    <div style={{ display: "flex", gap: 4, alignItems: "flex-end", height: 130, width: "100%", justifyContent: "center" }}>
                      <div className="grow-bar" style={{ width: "38%", height: `${v}%`, background: c.color, borderRadius: "3px 3px 0 0" }} />
                      <div className="grow-bar" style={{ width: "38%", height: `${avg}%`, background: "var(--surface-2)", borderRadius: "3px 3px 0 0" }} />
                    </div>
                    <div className="mono" style={{ fontSize: 11, color: "var(--muted)" }}>{yr}</div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
          <div className="card" style={{ padding: 20 }}>
            <h3 style={{ fontSize: 16, marginBottom: 12 }}>About</h3>
            <p style={{ fontSize: 13, color: "var(--fg-2)", lineHeight: 1.6 }}>{c.about}</p>
          </div>
          <div className="card" style={{ padding: 20 }}>
            <h3 style={{ fontSize: 16, marginBottom: 14 }}>Medal cabinet</h3>
            {[["🥇 Gold", c.gold, "var(--accent)"], ["🥈 Silver", c.silver, "var(--cyan)"], ["🥉 Bronze", c.bronze, "var(--muted)"]].map(([k, v, col]) => (
              <div key={k} style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 12 }}>
                <span style={{ width: 70, fontSize: 13 }}>{k}</span>
                <div style={{ flex: 1 }}><Bar value={v} max={maxMedal} color={col} height={8} /></div>
                <span className="mono tabular" style={{ fontSize: 13, width: 20, textAlign: "right" }}>{v}</span>
              </div>
            ))}
          </div>
          <div className="card" style={{ padding: 20 }}>
            <h3 style={{ fontSize: 16, marginBottom: 14 }}>Recent commits</h3>
            {commits.map(([n, pos, school], i) => (
              <div key={n} style={{ display: "flex", alignItems: "center", gap: 10, padding: "8px 0", borderTop: i ? "1px solid var(--border-soft)" : "none", fontSize: 13 }}>
                <span className="chip chip-cyan" style={{ fontSize: 10, width: 32, justifyContent: "center" }}>{pos}</span>
                <span style={{ flex: 1 }}>{n}</span>
                <span style={{ color: "var(--muted)", fontSize: 12 }}>{school}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
Object.assign(window, { PClubs, PClub });
