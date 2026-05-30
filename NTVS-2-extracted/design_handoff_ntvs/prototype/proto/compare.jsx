// NTVS Prototype — Compare (live)
function PCompare() {
  const { go, store } = useNav();
  const [adding, setAdding] = useState(false);
  const picks = store.compare.map(clubById);
  const metrics = ["Win %", "Depth", "Gold", "Dev", "Alumni"];
  const rows = [
    ["National rank", (c) => `#${c.rank}`, true, 1],
    ["Win percentage", (c) => `${Math.round(c.win * 100)}%`, true, 1],
    ["Active teams", (c) => c.teams, true, 1],
    ["Gold finishes", (c) => c.gold, true, 1],
    ["Silver / Bronze", (c) => `${c.silver} / ${c.bronze}`, false, 1],
    ["Coaching staff", (c) => c.coaches, true, 1],
    ["College commits", (c) => c.commits, true, 1],
    ["Season fee", (c) => `$${c.fee.toLocaleString()}`, true, -1],
    ["Home city", (c) => c.city, false, 1],
  ];
  const best = (fn, dir) => {
    const nums = picks.map((c) => parseFloat(String(fn(c)).replace(/[^0-9.]/g, "")));
    const target = dir > 0 ? Math.max(...nums) : Math.min(...nums);
    return nums.filter((n) => n === target).length === picks.length ? -1 : nums.indexOf(target);
  };
  const available = CLUBS.filter((c) => !store.compare.includes(c.id));

  return (
    <div className="page">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginBottom: 28 }}>
        <div>
          <div className="kicker" style={{ marginBottom: 10 }}>Comparison</div>
          <h1 style={{ fontSize: 40 }}>Club head-to-head</h1>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <button className="btn" onClick={() => setAdding((a) => !a)} disabled={picks.length >= 4} style={{ opacity: picks.length >= 4 ? 0.5 : 1 }}>＋ Add club</button>
          <button className="btn" onClick={() => store.setCompare([])}>Reset</button>
          <button className="btn btn-primary" onClick={() => store.toast("Comparison exported as PDF")}>Export PDF</button>
        </div>
      </div>

      {/* add picker */}
      {adding && (
        <div className="card pop-in" style={{ padding: 16, marginBottom: 20 }}>
          <div className="label" style={{ marginBottom: 12 }}>Add a club to compare ({4 - picks.length} slots left)</div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
            {available.map((c) => (
              <div key={c.id} className="chip hoverable" style={{ fontSize: 13, padding: "8px 13px", cursor: "pointer", display: "flex", gap: 8, alignItems: "center" }} onClick={() => { store.toggleCompare(c.id); if (picks.length + 1 >= 4) setAdding(false); }}>
                <span style={{ width: 8, height: 8, borderRadius: 2, background: c.color }} />{c.name}
              </div>
            ))}
            {available.length === 0 && <span style={{ fontSize: 13, color: "var(--muted)" }}>All clubs are pinned.</span>}
          </div>
        </div>
      )}

      {picks.length === 0 ? (
        <div className="card" style={{ padding: 60, textAlign: "center" }}>
          <div style={{ fontSize: 17, fontWeight: 600, marginBottom: 8 }}>No clubs pinned yet</div>
          <p style={{ fontSize: 14, color: "var(--muted)", marginBottom: 20 }}>Pin clubs from the directory or add them here to compare side by side.</p>
          <div style={{ display: "flex", gap: 8, justifyContent: "center" }}>
            <button className="btn btn-primary" onClick={() => setAdding(true)}>＋ Add a club</button>
            <button className="btn" onClick={() => go("clubs")}>Browse directory</button>
          </div>
        </div>
      ) : (
        <React.Fragment>
          {/* headers */}
          <div style={{ display: "grid", gridTemplateColumns: `220px repeat(${picks.length}, 1fr)`, gap: 16, marginBottom: 24 }}>
            <div style={{ display: "flex", alignItems: "flex-end" }}><span className="label">Pinned · {picks.length} of 4</span></div>
            {picks.map((c) => (
              <div key={c.id} className="card pop-in" style={{ padding: 18, borderTop: `3px solid ${c.color}` }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                  <ClubMark c={c} size={40} />
                  <span className="mono hoverable" style={{ fontSize: 13, color: "var(--muted)", cursor: "pointer", padding: 4 }} onClick={() => store.toggleCompare(c.id)}>✕</span>
                </div>
                <div style={{ fontWeight: 600, fontSize: 16, marginTop: 12, cursor: "pointer" }} onClick={() => go("club", { id: c.id })}>{c.name}</div>
                <div style={{ fontSize: 12, color: "var(--muted)", marginTop: 3 }}>{c.city}</div>
                <div style={{ display: "flex", gap: 16, marginTop: 14 }}>
                  <div><div className="stat-num" style={{ fontSize: 26, color: c.color }}>#{c.rank}</div><div className="label" style={{ marginTop: 2 }}>Rank</div></div>
                  <div><div className="stat-num" style={{ fontSize: 26 }}>{Math.round(c.win * 100)}<span style={{ fontSize: 14, color: "var(--muted)" }}>%</span></div><div className="label" style={{ marginTop: 2 }}>Win</div></div>
                </div>
              </div>
            ))}
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1.55fr 1fr", gap: 24, alignItems: "start" }}>
            <div className="card" style={{ overflow: "hidden" }}>
              {rows.map(([label, fn, hl, dir], ri) => {
                const bi = hl ? best(fn, dir) : -1;
                return (
                  <div key={label} style={{ display: "grid", gridTemplateColumns: `200px repeat(${picks.length},1fr)`, borderTop: ri ? "1px solid var(--border-soft)" : "none" }}>
                    <div style={{ padding: "13px 18px", fontSize: 13, color: "var(--muted)", background: "var(--bg-2)" }}>{label}</div>
                    {picks.map((c, i) => (
                      <div key={c.id} style={{ padding: "13px 18px", fontSize: 14, fontFamily: hl ? "var(--font-mono)" : "var(--font-sans)", fontWeight: bi === i ? 700 : 500, color: bi === i ? "var(--accent)" : "var(--fg-2)", display: "flex", alignItems: "center", gap: 8 }}>
                        {fn(c)}
                        {bi === i && <span className="chip chip-amber" style={{ fontSize: 9, padding: "2px 6px" }}>BEST</span>}
                      </div>
                    ))}
                  </div>
                );
              })}
            </div>

            <div className="card" style={{ padding: 22 }}>
              <h3 style={{ fontSize: 16, marginBottom: 4 }}>Profile overlay</h3>
              <p style={{ fontSize: 12, color: "var(--muted)", marginBottom: 8 }}>Normalized 0–100 across five program factors.</p>
              <div style={{ display: "grid", placeItems: "center" }}><Radar clubs={picks} metrics={metrics} /></div>
              <div style={{ display: "flex", flexDirection: "column", gap: 8, marginTop: 8 }}>
                {picks.map((c) => (
                  <div key={c.id} style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 13 }}>
                    <span style={{ width: 12, height: 3, borderRadius: 2, background: c.color }} />
                    <span style={{ color: "var(--fg-2)" }}>{c.name}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </React.Fragment>
      )}
    </div>
  );
}
window.PCompare = PCompare;
