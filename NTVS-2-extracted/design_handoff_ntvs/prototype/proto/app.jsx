// NTVS Prototype — Coaches directory + App shell (router + store)

function PCoaches() {
  const { go } = useNav();
  const [q, setQ] = useState("");
  const [onlyVerified, setOnlyVerified] = useState(false);
  const list = COACHES.filter((c) =>
    (!onlyVerified || c.verified) &&
    (q === "" || c.name.toLowerCase().includes(q.toLowerCase()) || clubById(c.clubId).name.toLowerCase().includes(q.toLowerCase()))
  );
  return (
    <div className="page">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginBottom: 22 }}>
        <div><div className="kicker" style={{ marginBottom: 10 }}>Directory · 1,247 coaches</div><h1 style={{ fontSize: 40 }}>Coaches</h1></div>
        <button className="btn btn-primary" onClick={() => go("editor")}>Claim your profile</button>
      </div>
      <div style={{ display: "flex", gap: 12, marginBottom: 20, alignItems: "center", flexWrap: "wrap" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 8, padding: "9px 13px", width: 300 }}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--muted)" strokeWidth="2"><circle cx="11" cy="11" r="7" /><path d="m21 21-4.3-4.3" /></svg>
          <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search coaches or clubs…" style={{ background: "transparent", border: 0, outline: "none", color: "var(--fg)", fontSize: 13, fontFamily: "inherit", width: "100%" }} />
        </div>
        <span className="chip" style={{ fontSize: 12, cursor: "pointer", padding: "8px 13px", background: onlyVerified ? "var(--accent)" : "var(--surface-2)", color: onlyVerified ? "#0a0a0a" : "var(--fg-2)", fontWeight: onlyVerified ? 600 : 500 }} onClick={() => setOnlyVerified((v) => !v)}>✓ Verified only</span>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 14 }}>
        {list.map((co) => {
          const club = clubById(co.clubId);
          return (
            <div key={co.id} className="card hoverable" style={{ padding: 20, cursor: "pointer" }} onClick={() => go("coach", { id: co.id })}>
              <div style={{ display: "flex", gap: 14, alignItems: "center" }}>
                <div style={{ width: 52, height: 52, borderRadius: 12, background: co.grad, color: "#fff", display: "grid", placeItems: "center", fontFamily: "var(--font-display)", fontWeight: 700, fontSize: 18 }}>{co.init}</div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 600, fontSize: 15, display: "flex", alignItems: "center", gap: 6 }}>{co.name} {co.verified && <VerifiedBadge size={14} />}</div>
                  <div style={{ fontSize: 12, color: "var(--muted)", marginTop: 3 }}>{co.role}</div>
                </div>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 14, fontSize: 12, color: "var(--fg-2)" }}>
                <span style={{ width: 8, height: 8, borderRadius: 2, background: club.color }} />{club.name}
              </div>
              <div style={{ display: "flex", gap: 18, marginTop: 16, paddingTop: 14, borderTop: "1px solid var(--border-soft)" }}>
                {[[co.totals.wins, "Wins"], [co.totals.winRate + "%", "Win"], [co.totals.commits, "Commits"]].map(([v, k]) => (
                  <div key={k}><div className="stat-num" style={{ fontSize: 18 }}>{v}</div><div className="label" style={{ marginTop: 2 }}>{k}</div></div>
                ))}
                <div style={{ marginLeft: "auto", textAlign: "right" }}><div style={{ display: "flex", gap: 1, justifyContent: "flex-end" }}><Stars n={Math.round(co.rating)} size={11} /></div><div className="label" style={{ marginTop: 4 }}>{co.rating} · {co.endorseCount}</div></div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ---- App shell ----
function App() {
  const [route, setRoute] = useState({ page: "home" });
  const [anim, setAnim] = useState("page-enter");
  const [compare, setCompare] = useState(["tav", "drv", "trn"]);
  const [reviews, setReviews] = useState(() => JSON.parse(JSON.stringify(SEED_REVIEWS)));
  const [requests, setRequests] = useState(() => [...SEED_REQUESTS]);
  const toastRef = useRef(null);

  const go = (page, params = {}) => {
    setAnim("page-exit");
    setTimeout(() => {
      setRoute({ page, ...params });
      document.querySelector(".app-scroll")?.scrollTo(0, 0);
      setAnim("page-enter");
    }, 130);
  };

  const store = {
    compare,
    setCompare,
    toggleCompare: (id) => setCompare((p) => p.includes(id) ? p.filter((x) => x !== id) : p.length >= 4 ? (toastRef.current?.("Max 4 clubs — remove one first", "warn"), p) : [...p, id]),
    reviewsFor: (cid) => reviews[cid] || [],
    addReview: (cid, r) => setReviews((p) => ({ ...p, [cid]: [r, ...(p[cid] || [])] })),
    requests,
    resolveRequest: (id) => setRequests((p) => p.filter((r) => r.id !== id)),
    toast: (m, k) => toastRef.current?.(m, k),
  };

  const page = route.page;
  return (
    <ToastHost>
      <NavCtx.Provider value={{ route, go, store }}>
        <ToastBridge toastRef={toastRef} />
        <div className="ntvs">
          <Nav />
          <div className={`app-scroll ${anim}`} style={{ flex: 1, overflow: "auto", display: "flex", flexDirection: "column" }}>
            {page === "home" && <PHome />}
            {page === "clubs" && <PClubs />}
            {page === "club" && <PClub id={route.id} />}
            {page === "compare" && <PCompare />}
            {page === "schedule" && <PSchedule />}
            {page === "results" && <PResults id={route.id} />}
            {page === "coaches" && <PCoaches />}
            {page === "coach" && <PCoach id={route.id} />}
            {page === "editor" && <PEditor />}
            {page === "director" && <PDirector />}
          </div>
        </div>
      </NavCtx.Provider>
    </ToastHost>
  );
}

// bridge so store.toast can reach the ToastHost context
function ToastBridge({ toastRef }) {
  const push = useToast();
  useEffect(() => { toastRef.current = push; }, [push]);
  return null;
}

Object.assign(window, { PCoaches, App });
ReactDOM.createRoot(document.getElementById("root")).render(<App />);
