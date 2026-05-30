// NTVS Prototype — Home
function PHome() {
  const { go } = useNav();
  const top = CLUBS.slice(0, 6);
  return (
    <div className="page" style={{ padding: 0 }}>
      {/* HERO */}
      <div style={{ padding: "52px 56px 40px", borderBottom: "1px solid var(--border)", background: "radial-gradient(1100px 380px at 82% -10%, rgba(245,197,24,0.10), transparent 60%)" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", gap: 56 }}>
          <div style={{ maxWidth: 680 }}>
            <div className="kicker" style={{ marginBottom: 18 }}>
              <span style={{ color: "var(--accent)" }}>● LIVE</span> &nbsp;·&nbsp; 2025–26 Club Season · Week 14
            </div>
            <h1 style={{ fontSize: 68, lineHeight: 0.95 }}>
              Every set, every spike,<br />
              <span style={{ color: "var(--muted)" }}>tracked across</span> <span style={{ color: "var(--accent)" }}>North Texas.</span>
            </h1>
            <p style={{ color: "var(--fg-2)", fontSize: 17, marginTop: 22, maxWidth: 540, lineHeight: 1.5 }}>
              The independent stats hub for club volleyball from Denton to Plano. Compare programs, follow tournaments, scout coaches.
            </p>
            <div style={{ display: "flex", gap: 10, marginTop: 28, flexWrap: "wrap" }}>
              <button className="btn btn-primary" onClick={() => go("compare")}>Compare clubs →</button>
              <button className="btn" onClick={() => go("schedule")}>Browse tournaments</button>
            </div>
          </div>
          <div className="card hoverable" style={{ width: 320, padding: 20, flexShrink: 0, cursor: "pointer" }} onClick={() => go("results", { id: "lsc" })}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
              <div className="label">Live now</div>
              <div className="chip chip-amber">Lone Star Classic</div>
            </div>
            {[["Drive Nation 18B", 2, "TAV 18 Elite", 1], ["Skyline 18 Royal", 2, "Lone Star 18P", 0], ["NTX Elite 18 Red", 1, "Tornados 18B", 2]].map(([a, sa, b, sb], i) => (
              <div key={i} style={{ display: "flex", alignItems: "center", gap: 8, padding: "9px 0", borderTop: i ? "1px solid var(--border-soft)" : "none", fontSize: 13 }}>
                <span style={{ flex: 1, color: sa > sb ? "var(--fg)" : "var(--fg-2)", fontWeight: sa > sb ? 600 : 400 }}>{a}</span>
                <span className="mono tabular" style={{ color: sa > sb ? "var(--accent)" : "var(--muted)" }}>{sa}</span>
                <span style={{ color: "var(--muted-2)" }}>–</span>
                <span className="mono tabular" style={{ color: sb > sa ? "var(--accent)" : "var(--muted)" }}>{sb}</span>
                <span style={{ flex: 1, textAlign: "right", color: sb > sa ? "var(--fg)" : "var(--fg-2)", fontWeight: sb > sa ? 600 : 400 }}>{b}</span>
              </div>
            ))}
            <div style={{ marginTop: 14, fontSize: 12, color: "var(--cyan)" }}>View full bracket →</div>
          </div>
        </div>
      </div>

      {/* STATS STRIP */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", borderBottom: "1px solid var(--border)" }}>
        {[["Clubs tracked", "84", "+6 this season"], ["Active teams", "612", "12s through 18s"], ["Coach profiles", "1,247", "418 verified"], ["Matches logged", "9,302", "season-to-date"]].map(([k, v, sub], i) => (
          <div key={k} style={{ padding: "24px 28px", borderRight: i < 3 ? "1px solid var(--border)" : "none" }}>
            <div className="label" style={{ marginBottom: 10 }}>{k}</div>
            <div className="stat-num" style={{ fontSize: 40 }}>{v}</div>
            <div style={{ fontSize: 12, color: "var(--muted)", marginTop: 4 }}>{sub}</div>
          </div>
        ))}
      </div>

      {/* BODY */}
      <div style={{ display: "grid", gridTemplateColumns: "1.7fr 1fr", gap: 40, padding: "36px 56px 56px" }}>
        <div>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 18 }}>
            <h2 style={{ fontSize: 26 }}>Power Rankings</h2>
            <div style={{ fontSize: 12, color: "var(--muted)" }}>18 Open · Week 14</div>
          </div>
          <div className="card">
            {top.map((c, i) => (
              <div key={c.id} className="row-hover" style={{ display: "grid", gridTemplateColumns: "32px 1fr auto 120px auto", gap: 16, alignItems: "center", padding: "14px 20px", borderTop: i ? "1px solid var(--border-soft)" : "none", cursor: "pointer" }} onClick={() => go("club", { id: c.id })}>
                <div className="stat-num" style={{ fontSize: 22, color: i < 3 ? "var(--accent)" : "var(--muted)" }}>{i + 1}</div>
                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <span style={{ width: 8, height: 8, borderRadius: 2, background: c.color }} />
                    <span style={{ fontWeight: 600, fontSize: 14 }}>{c.name}</span>
                    <span className={`tier tier-${c.tier}`}>T{c.tier}</span>
                  </div>
                  <div style={{ fontSize: 12, color: "var(--muted)", marginTop: 3 }}>{c.city} · {c.teams} teams</div>
                </div>
                <div className="mono tabular" style={{ fontSize: 14 }}>{Math.round(c.win * 100)}%</div>
                <Bar value={c.win * 100} color={c.color} />
                <Sparkline data={[3, 5, 4, 6, 5, 7, 6 + (i % 3), 8]} color={c.color} w={72} h={24} />
              </div>
            ))}
            <div className="row-hover" style={{ padding: "14px 20px", borderTop: "1px solid var(--border-soft)", fontSize: 13, color: "var(--cyan)", cursor: "pointer" }} onClick={() => go("clubs")}>
              See full rankings (84 clubs) →
            </div>
          </div>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
          <div>
            <h3 style={{ fontSize: 16, marginBottom: 14 }}>Upcoming tournaments</h3>
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              {TOURNAMENTS.slice(0, 3).map((e) => (
                <div key={e.id} className="card hoverable" style={{ padding: "13px 16px", display: "flex", gap: 14, alignItems: "center", cursor: "pointer" }} onClick={() => go("schedule")}>
                  <div className="mono" style={{ fontSize: 11, color: "var(--accent)", width: 64, lineHeight: 1.3 }}>{e.mo} {e.d}</div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 13, fontWeight: 600 }}>{e.name}</div>
                    <div style={{ fontSize: 11, color: "var(--muted)", marginTop: 2 }}>{e.city}, TX · {e.teams} teams</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
          <div>
            <h3 style={{ fontSize: 16, marginBottom: 14 }}>Featured coaches</h3>
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              {COACHES.slice(0, 2).map((co) => (
                <div key={co.id} className="card hoverable" style={{ padding: "13px 16px", display: "flex", gap: 12, alignItems: "center", cursor: "pointer" }} onClick={() => go("coach", { id: co.id })}>
                  <div style={{ width: 38, height: 38, borderRadius: 999, background: co.grad, color: "#fff", display: "grid", placeItems: "center", fontWeight: 700, fontSize: 14, fontFamily: "var(--font-display)" }}>{co.init}</div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 13, fontWeight: 600, display: "flex", alignItems: "center", gap: 6 }}>{co.name} {co.verified && <VerifiedBadge size={13} />}</div>
                    <div style={{ fontSize: 11, color: "var(--muted)", marginTop: 2 }}>{clubById(co.clubId).name} · {co.role.split("·")[1]}</div>
                  </div>
                  <span style={{ fontSize: 11, color: "var(--cyan)" }}>View</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
window.PHome = PHome;
