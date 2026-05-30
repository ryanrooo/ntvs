// NTVS Prototype — Club director dashboard (approve/deny)
function PDirector() {
  const { store } = useNav();
  const requests = store.requests;
  const [decided, setDecided] = useState({}); // id -> 'verified' | 'denied'

  const roster = [
    ["James Whitfield", "17 Elite · HC", "Verified"],
    ["Dana Cho", "16 Elite · HC", "Verified"],
    ["Tom Becker", "14 Elite · HC", "Verified"],
    ["Sasha Petrov", "13 Black · Asst", "Invite sent"],
  ];

  const decide = (r, verdict) => {
    setDecided((d) => ({ ...d, [r.id]: verdict }));
    store.toast(verdict === "verified" ? `${r.name} verified & linked` : `${r.name}'s request denied`, verdict === "verified" ? "ok" : "warn");
    setTimeout(() => store.resolveRequest(r.id), 650);
  };

  const verifiedCount = 11 + Object.values(decided).filter((v) => v === "verified").length;

  return (
    <div className="page" style={{ padding: 0, display: "flex", flexDirection: "column" }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "20px 40px", borderBottom: "1px solid var(--border)", background: "var(--bg-2)" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
          <div style={{ width: 44, height: 44, borderRadius: 10, background: "#f5c518", color: "#0a0a0a", display: "grid", placeItems: "center", fontFamily: "var(--font-display)", fontWeight: 700, fontSize: 18 }}>TA</div>
          <div><div className="kicker" style={{ marginBottom: 4 }}>Club Director · Texas Advantage</div><h2 style={{ fontSize: 20 }}>Coaching staff & verification</h2></div>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <button className="btn" onClick={() => store.toast("Team manager opened")}>Manage teams</button>
          <button className="btn btn-primary" onClick={() => store.toast("Invite link copied")}>＋ Invite coach</button>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1.7fr 1fr", gap: 36, padding: "30px 40px 56px", flex: 1, overflow: "auto" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 16 }}>
            <h2 style={{ fontSize: 22 }}>Pending requests</h2>
            <span className="chip chip-amber" style={{ fontSize: 11 }}>{requests.length} awaiting review</span>
          </div>
          {requests.length === 0 ? (
            <div className="card" style={{ padding: 48, textAlign: "center" }}>
              <div style={{ fontSize: 30, marginBottom: 10 }}>✓</div>
              <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 6 }}>All caught up</div>
              <p style={{ fontSize: 13, color: "var(--muted)" }}>No verification requests waiting. New ones will appear here.</p>
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              {requests.map((r) => {
                const v = decided[r.id];
                return (
                  <div key={r.id} className="card" style={{ padding: 20, transition: "opacity .5s, transform .5s", opacity: v ? 0.55 : 1, borderColor: v === "verified" ? "var(--win)" : v === "denied" ? "var(--loss)" : "var(--border)" }}>
                    <div style={{ display: "flex", gap: 16 }}>
                      <div style={{ width: 48, height: 48, borderRadius: 10, background: r.color, color: "#0a0a0a", display: "grid", placeItems: "center", fontFamily: "var(--font-display)", fontWeight: 700, fontSize: 17, flexShrink: 0 }}>{r.init}</div>
                      <div style={{ flex: 1 }}>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                          <div><div style={{ fontWeight: 600, fontSize: 16 }}>{r.name}</div><div style={{ fontSize: 13, color: "var(--fg-2)", marginTop: 3 }}>{r.role} · <span className="mono">{r.claim}</span></div></div>
                          <span style={{ fontSize: 11, color: "var(--muted)" }}>{r.when}</span>
                        </div>
                        <div style={{ display: "flex", alignItems: "center", gap: 12, marginTop: 14 }}>
                          <span className={r.match === "Strong" ? "chip chip-win" : "chip chip-amber"} style={{ fontSize: 10 }}>{r.match === "Strong" ? "✓ STRONG MATCH" : "◐ PARTIAL MATCH"}</span>
                          <div style={{ flex: 1 }}><Bar value={r.matchPct} color={r.match === "Strong" ? "var(--win)" : "var(--accent)"} height={6} /></div>
                          <span className="mono tabular" style={{ fontSize: 12, color: "var(--muted)" }}>{r.matchPct}%</span>
                        </div>
                        <div style={{ fontSize: 12, color: "var(--muted)", marginTop: 8 }}>{r.note}</div>
                        {v ? (
                          <div style={{ marginTop: 16, fontSize: 13, fontWeight: 600, color: v === "verified" ? "var(--win)" : "var(--loss)" }}>{v === "verified" ? "✓ Verified & linked" : "✕ Request denied"}</div>
                        ) : (
                          <div style={{ display: "flex", gap: 8, marginTop: 16 }}>
                            <button className="btn btn-primary" style={{ fontSize: 13 }} onClick={() => decide(r, "verified")}>✓ Verify & link</button>
                            <button className="btn" style={{ fontSize: 13 }} onClick={() => store.toast("Opening " + r.name + "'s match records")}>View records</button>
                            <button className="btn btn-ghost" style={{ fontSize: 13, color: "var(--loss)", marginLeft: "auto" }} onClick={() => decide(r, "denied")}>Deny</button>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
            {[["14", "Coaches"], [String(verifiedCount), "Verified"], [String(requests.length), "Pending"], ["96%", "Match rate"]].map(([v, k]) => (
              <div key={k} className="card" style={{ padding: 16 }}><div className="stat-num" style={{ fontSize: 28 }}>{v}</div><div className="label" style={{ marginTop: 4 }}>{k}</div></div>
            ))}
          </div>
          <div>
            <h3 style={{ fontSize: 16, marginBottom: 14 }}>Current staff</h3>
            <div className="card">
              {roster.map(([n, role, status], i) => (
                <div key={n} style={{ display: "flex", alignItems: "center", gap: 12, padding: "13px 16px", borderTop: i ? "1px solid var(--border-soft)" : "none" }}>
                  <div style={{ width: 34, height: 34, borderRadius: 999, background: "var(--surface-2)", display: "grid", placeItems: "center", fontSize: 12, fontWeight: 600, fontFamily: "var(--font-display)" }}>{n.split(" ").map((w) => w[0]).join("")}</div>
                  <div style={{ flex: 1 }}><div style={{ fontSize: 13, fontWeight: 600 }}>{n}</div><div style={{ fontSize: 11, color: "var(--muted)", marginTop: 2 }}>{role}</div></div>
                  <span style={{ fontSize: 11, color: status === "Verified" ? "var(--cyan)" : "var(--muted)", display: "flex", alignItems: "center", gap: 5 }}>{status === "Verified" && <VerifiedBadge size={13} />}{status}</span>
                </div>
              ))}
            </div>
          </div>
          <div className="card" style={{ padding: 18, background: "var(--bg-2)" }}>
            <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 6 }}>How verification works</div>
            <p style={{ fontSize: 12, color: "var(--muted)", lineHeight: 1.55 }}>NTVS cross-checks a coach's claimed teams against logged match records. You give the final ✓ — verified coaches appear on your club page and in recruiter search.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
window.PDirector = PDirector;
