// NTVS Prototype — Schedule + Results
function PSchedule() {
  const { go } = useNav();
  const [view, setView] = useState("List");
  const [filters, setFilters] = useState({ openOnly: false, month: null, near: false });
  const sc = (s) => s === "Open" ? "chip chip-win" : s === "Filling" ? "chip chip-amber" : "chip chip-loss";

  let ev = TOURNAMENTS.filter((e) =>
    (!filters.openOnly || e.status === "Open") &&
    (!filters.month || e.monthKey === filters.month) &&
    (!filters.near || e.within <= 30)
  );
  const totalTeams = ev.reduce((s, e) => s + e.teams, 0);
  const months = [["MAR", "March 2026"], ["APR", "April 2026"]];

  const chip = (label, active, onClick) => (
    <span className="chip" style={{ padding: "7px 13px", fontSize: 12, cursor: "pointer", background: active ? "var(--accent)" : "var(--surface-2)", color: active ? "#0a0a0a" : "var(--fg-2)", fontWeight: active ? 600 : 500 }} onClick={onClick}>{label}</span>
  );

  return (
    <div className="page">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginBottom: 24 }}>
        <div>
          <div className="kicker" style={{ marginBottom: 10 }}>Spring 2026 · Region 9</div>
          <h1 style={{ fontSize: 40 }}>Tournament schedule</h1>
        </div>
        <div style={{ display: "flex", gap: 4, background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 8, padding: 4 }}>
          {["List", "Calendar", "Map"].map((v) => (
            <div key={v} className={`nav-link ${view === v ? "active" : ""}`} style={{ fontSize: 12 }} onClick={() => setView(v)}>{v}</div>
          ))}
        </div>
      </div>

      <div style={{ display: "flex", gap: 8, marginBottom: 24, alignItems: "center", flexWrap: "wrap" }}>
        {chip("Open only", filters.openOnly, () => setFilters((f) => ({ ...f, openOnly: !f.openOnly })))}
        {chip("March", filters.month === "MAR", () => setFilters((f) => ({ ...f, month: f.month === "MAR" ? null : "MAR" })))}
        {chip("April", filters.month === "APR", () => setFilters((f) => ({ ...f, month: f.month === "APR" ? null : "APR" })))}
        {chip("Within 30mi", filters.near, () => setFilters((f) => ({ ...f, near: !f.near })))}
        {(filters.openOnly || filters.month || filters.near) && <span style={{ fontSize: 12, color: "var(--cyan)", cursor: "pointer" }} onClick={() => setFilters({ openOnly: false, month: null, near: false })}>Clear</span>}
        <span style={{ marginLeft: "auto", fontSize: 12, color: "var(--muted)" }}>{ev.length} tournaments · {totalTeams.toLocaleString()} teams</span>
      </div>

      {view === "Calendar" ? (
        <CalendarView ev={ev} go={go} />
      ) : view === "Map" ? (
        <MapView ev={ev} />
      ) : (
        months.map(([mo, title]) => {
          const monthEv = ev.filter((e) => e.monthKey === mo);
          if (monthEv.length === 0) return null;
          return (
            <div key={mo} style={{ marginBottom: 32 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 14 }}>
                <h2 style={{ fontSize: 18 }}>{title}</h2><div className="divider" style={{ flex: 1 }} />
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                {monthEv.map((e) => (
                  <div key={e.id} className="card hoverable" style={{ padding: "18px 22px", display: "grid", gridTemplateColumns: "72px 1fr auto auto auto", gap: 22, alignItems: "center", borderLeft: e.feat ? "3px solid var(--accent)" : "1px solid var(--border)", cursor: "pointer" }} onClick={() => e.done ? go("results", { id: e.id }) : null}>
                    <div style={{ textAlign: "center" }}>
                      <div className="mono" style={{ fontSize: 10, color: "var(--muted)", letterSpacing: "0.1em" }}>{e.mo}</div>
                      <div className="stat-num" style={{ fontSize: 28, color: e.feat ? "var(--accent)" : "var(--fg)" }}>{e.d}</div>
                    </div>
                    <div>
                      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                        <span style={{ fontWeight: 600, fontSize: 16 }}>{e.name}</span>
                        {e.feat && <span className="chip chip-amber" style={{ fontSize: 9 }}>FEATURED</span>}
                        {e.done && <span className="chip chip-cyan" style={{ fontSize: 9 }}>RESULTS IN</span>}
                      </div>
                      <div style={{ fontSize: 12, color: "var(--muted)", marginTop: 4 }}>📍 {e.venue} · {e.city}, TX</div>
                    </div>
                    <div style={{ textAlign: "center" }}><div className="mono tabular" style={{ fontSize: 16 }}>{e.teams}</div><div className="label" style={{ marginTop: 2 }}>teams</div></div>
                    <div><div style={{ fontSize: 12, color: "var(--fg-2)" }}>{e.ageLo}–{e.ageHi}s</div><div style={{ fontSize: 11, color: "var(--muted)", marginTop: 3 }}>{e.div}</div></div>
                    <div style={{ display: "flex", flexDirection: "column", gap: 8, alignItems: "flex-end" }}>
                      <span className={sc(e.status)} style={{ fontSize: 10 }}>{e.status}</span>
                      <span style={{ fontSize: 12, color: "var(--cyan)" }}>{e.done ? "Results →" : "Details →"}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          );
        })
      )}
      {ev.length === 0 && <div className="card" style={{ padding: 40, textAlign: "center", color: "var(--muted)" }}>No tournaments match these filters.</div>}
    </div>
  );
}

function CalendarView({ ev, go }) {
  // March 2026 grid — starts Sunday. Mar 1 2026 is a Sunday.
  const days = Array.from({ length: 35 }, (_, i) => i - 0 + 1).map((d) => (d <= 31 ? d : null));
  const evByDay = {};
  ev.filter((e) => e.monthKey === "MAR").forEach((e) => { const day = parseInt(e.d); evByDay[day] = e; });
  return (
    <div className="card" style={{ padding: 22 }}>
      <h3 style={{ fontSize: 16, marginBottom: 16 }}>March 2026</h3>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(7,1fr)", gap: 8 }}>
        {["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].map((d) => <div key={d} className="label" style={{ textAlign: "center", paddingBottom: 6 }}>{d}</div>)}
        {days.map((d, i) => (
          <div key={i} style={{ aspectRatio: "1 / 0.82", borderRadius: 8, border: "1px solid var(--border-soft)", padding: 8, background: d && evByDay[d] ? "var(--surface-2)" : "transparent", cursor: d && evByDay[d] ? "pointer" : "default" }} onClick={() => d && evByDay[d] && evByDay[d].done && go("results", { id: evByDay[d].id })}>
            {d && <div className="mono" style={{ fontSize: 11, color: "var(--muted)" }}>{d}</div>}
            {d && evByDay[d] && (
              <div style={{ marginTop: 4, fontSize: 10, color: "var(--accent)", fontWeight: 600, lineHeight: 1.2 }}>{evByDay[d].name.split(" ").slice(0, 2).join(" ")}</div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function MapView({ ev }) {
  // schematic DFW positions
  const pos = { Allen: [62, 26], Plano: [56, 34], Dallas: [50, 56], Frisco: [50, 22], Arlington: [30, 60], Denton: [34, 18], "Fort Worth": [22, 58] };
  return (
    <div className="card" style={{ padding: 0, overflow: "hidden", position: "relative", height: 460, background: "var(--bg-2)" }}>
      <div style={{ position: "absolute", inset: 0, backgroundImage: "linear-gradient(var(--border-soft) 1px, transparent 1px), linear-gradient(90deg, var(--border-soft) 1px, transparent 1px)", backgroundSize: "44px 44px", opacity: 0.5 }} />
      <div style={{ position: "absolute", top: 16, left: 20, fontSize: 12, color: "var(--muted)" }} className="label">DFW Metroplex</div>
      {ev.map((e) => {
        const p = pos[e.city] || [50, 50];
        return (
          <div key={e.id} style={{ position: "absolute", left: `${p[0]}%`, top: `${p[1]}%`, transform: "translate(-50%,-50%)" }}>
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 4 }}>
              <div style={{ width: 14, height: 14, borderRadius: 999, background: e.feat ? "var(--accent)" : "var(--cyan)", boxShadow: "0 0 0 4px rgba(245,197,24,0.18)" }} />
              <div style={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 6, padding: "4px 8px", fontSize: 11, whiteSpace: "nowrap" }}>
                <div style={{ fontWeight: 600 }}>{e.city}</div>
                <div style={{ color: "var(--muted)", fontSize: 10 }}>{e.name.split(" ").slice(0, 2).join(" ")}</div>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

function PResults({ id }) {
  const { go } = useNav();
  const [tab, setTab] = useState("Bracket");
  const t = tourneyById(id) || TOURNAMENTS[0];
  const r16 = [["Drive Nation 18B", 2, "Allen Aces 18", 0], ["NTX Elite 18R", 2, "McKinney 18", 1], ["Skyline 18 Royal", 2, "Denton 18", 0], ["Lone Star 18P", 2, "Tornados 18B", 1]];
  const qf = [["Drive Nation 18B", 2, "NTX Elite 18R", 1], ["Skyline 18 Royal", 1, "Lone Star 18P", 2]];
  const sf = [["Drive Nation 18B", 2, "Lone Star 18P", 0]];
  const podium = [["🥇", "Drive Nation 18 Black", "Frisco", "var(--accent)"], ["🥈", "Lone Star 18 Premier", "Arlington", "var(--cyan)"], ["🥉", "Skyline 18 Royal", "Dallas", "var(--muted)"]];
  const standings = [["Drive Nation 18B", "6–0", "12–1"], ["Lone Star 18P", "5–1", "11–4"], ["Skyline 18 Royal", "4–2", "9–5"], ["NTX Elite 18R", "3–3", "7–7"], ["Tornados 18B", "2–4", "5–8"], ["McKinney 18", "1–5", "3–10"]];

  const MatchCell = ({ a, sa, b, sb }) => {
    const aw = sa > sb;
    return (
      <div className="card" style={{ padding: 0, overflow: "hidden", width: 200 }}>
        {[[a, sa, aw], [b, sb, !aw]].map(([tt, s, win], i) => (
          <div key={i} style={{ display: "flex", alignItems: "center", gap: 8, padding: "9px 12px", borderTop: i ? "1px solid var(--border-soft)" : "none", background: win ? "rgba(245,197,24,0.06)" : "transparent" }}>
            <span style={{ flex: 1, fontSize: 12, fontWeight: win ? 600 : 400, color: win ? "var(--fg)" : "var(--muted)" }}>{tt}</span>
            <span className="mono tabular" style={{ fontSize: 13, color: win ? "var(--accent)" : "var(--muted-2)" }}>{s}</span>
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className="page">
      <div style={{ fontSize: 12, color: "var(--muted)", marginBottom: 16 }}><span style={{ cursor: "pointer" }} onClick={() => go("schedule")}>Results</span> / <span style={{ color: "var(--fg-2)" }}>{t.name} 2026</span></div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginBottom: 8 }}>
        <div>
          <div className="kicker" style={{ marginBottom: 10 }}>Final · {t.mo} {t.d} · 18 Open</div>
          <h1 style={{ fontSize: 40 }}>{t.name}</h1>
        </div>
        <div style={{ display: "flex", gap: 4, background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 8, padding: 4 }}>
          {["Bracket", "Standings", "All scores"].map((v) => (
            <div key={v} className={`nav-link ${tab === v ? "active" : ""}`} style={{ fontSize: 12 }} onClick={() => setTab(v)}>{v}</div>
          ))}
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 16, margin: "24px 0 36px" }}>
        {podium.map(([m, n, city, col]) => (
          <div key={n} className="card" style={{ padding: 20, borderTop: `3px solid ${col}`, display: "flex", alignItems: "center", gap: 16 }}>
            <div style={{ fontSize: 34 }}>{m}</div>
            <div><div style={{ fontWeight: 600, fontSize: 16 }}>{n}</div><div style={{ fontSize: 12, color: "var(--muted)", marginTop: 3 }}>{city}, TX</div></div>
          </div>
        ))}
      </div>

      {tab === "Bracket" && (
        <React.Fragment>
          <h2 style={{ fontSize: 20, marginBottom: 20 }}>Championship bracket</h2>
          <div style={{ display: "flex", gap: 48, overflowX: "auto", paddingBottom: 12 }}>
            {[["Round of 16", r16], ["Quarterfinals", qf], ["Semifinal", sf]].map(([title, ms]) => (
              <div key={title} style={{ display: "flex", flexDirection: "column", justifyContent: "space-around", gap: 20, minWidth: 200 }}>
                <div className="label" style={{ marginBottom: 4 }}>{title}</div>
                {ms.map((m, i) => <MatchCell key={i} a={m[0]} sa={m[1]} b={m[2]} sb={m[3]} />)}
              </div>
            ))}
            <div style={{ display: "flex", flexDirection: "column", justifyContent: "center", minWidth: 200 }}>
              <div className="label" style={{ marginBottom: 12 }}>Champion</div>
              <div className="card" style={{ padding: 20, borderTop: "3px solid var(--accent)", background: "rgba(245,197,24,0.06)" }}>
                <div style={{ fontSize: 30, marginBottom: 8 }}>🏆</div>
                <div style={{ fontWeight: 700, fontSize: 17 }}>Drive Nation 18 Black</div>
                <div style={{ fontSize: 12, color: "var(--muted)", marginTop: 4 }}>6–0 on the weekend</div>
                <div className="mono" style={{ fontSize: 11, color: "var(--accent)", marginTop: 12 }}>def. Lone Star 25–19, 25–22</div>
              </div>
            </div>
          </div>
        </React.Fragment>
      )}

      {tab === "Standings" && (
        <div className="card" style={{ overflow: "hidden", maxWidth: 620 }}>
          <div style={{ display: "grid", gridTemplateColumns: "40px 1fr 100px 100px", padding: "11px 18px", background: "var(--bg-2)", borderBottom: "1px solid var(--border)" }}>
            {["#", "Team", "Pool", "Overall"].map((h) => <div key={h} className="label">{h}</div>)}
          </div>
          {standings.map(([n, pool, ov], i) => (
            <div key={n} style={{ display: "grid", gridTemplateColumns: "40px 1fr 100px 100px", padding: "13px 18px", borderTop: i ? "1px solid var(--border-soft)" : "none", alignItems: "center", fontSize: 13 }}>
              <div className="stat-num" style={{ fontSize: 16, color: i < 3 ? "var(--accent)" : "var(--muted)" }}>{i + 1}</div>
              <div style={{ fontWeight: 600 }}>{n}</div>
              <div className="mono tabular">{pool}</div>
              <div className="mono tabular" style={{ color: "var(--muted)" }}>{ov}</div>
            </div>
          ))}
        </div>
      )}

      {tab === "All scores" && (
        <div style={{ display: "flex", flexDirection: "column", gap: 10, maxWidth: 620 }}>
          {[...r16, ...qf, ...sf].map((m, i) => (
            <div key={i} className="card" style={{ padding: "12px 18px", display: "flex", alignItems: "center", gap: 12, fontSize: 13 }}>
              <span style={{ flex: 1, textAlign: "right", fontWeight: m[1] > m[3] ? 600 : 400, color: m[1] > m[3] ? "var(--fg)" : "var(--muted)" }}>{m[0]}</span>
              <span className="mono tabular" style={{ color: m[1] > m[3] ? "var(--accent)" : "var(--muted)" }}>{m[1]}</span>
              <span style={{ color: "var(--muted-2)" }}>–</span>
              <span className="mono tabular" style={{ color: m[3] > m[1] ? "var(--accent)" : "var(--muted)" }}>{m[3]}</span>
              <span style={{ flex: 1, fontWeight: m[3] > m[1] ? 600 : 400, color: m[3] > m[1] ? "var(--fg)" : "var(--muted)" }}>{m[2]}</span>
            </div>
          ))}
        </div>
      )}

      <h2 style={{ fontSize: 20, margin: "40px 0 18px" }}>Statistical leaders</h2>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 16 }}>
        {[["Kills", [["Ava Sanders", "Drive Nation", 84], ["Reese Okafor", "Skyline", 71], ["Mia Tran", "Lone Star", 66]]], ["Assists", [["Jordan Lee", "Drive Nation", 142], ["Casey Wu", "NTX Elite", 128], ["Priya Nair", "Skyline", 119]]], ["Digs", [["Sam Ortiz", "Lone Star", 97], ["Bella Reyes", "Tornados", 88], ["Kim Park", "Drive Nation", 81]]]].map(([cat, rows]) => (
          <div key={cat} className="card" style={{ padding: 20 }}>
            <div className="label" style={{ marginBottom: 14 }}>{cat} leaders</div>
            {rows.map(([n, club, v], i) => (
              <div key={n} style={{ display: "flex", alignItems: "center", gap: 12, padding: "9px 0", borderTop: i ? "1px solid var(--border-soft)" : "none" }}>
                <span className="stat-num" style={{ fontSize: 16, color: i === 0 ? "var(--accent)" : "var(--muted)", width: 16 }}>{i + 1}</span>
                <div style={{ flex: 1 }}><div style={{ fontSize: 13, fontWeight: 500 }}>{n}</div><div style={{ fontSize: 11, color: "var(--muted)", marginTop: 2 }}>{club}</div></div>
                <span className="mono tabular" style={{ fontSize: 15 }}>{v}</span>
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}
Object.assign(window, { PSchedule, PResults });
