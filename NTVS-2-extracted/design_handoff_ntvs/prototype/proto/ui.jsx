// NTVS Prototype — shared UI primitives & app context
const { useState, useEffect, useRef, createContext, useContext } = React;

const NavCtx = createContext(null);
const useNav = () => useContext(NavCtx);

// ---- Toast ----
const ToastCtx = createContext(() => {});
const useToast = () => useContext(ToastCtx);
function ToastHost({ children }) {
  const [toasts, setToasts] = useState([]);
  const push = (msg, kind = "ok") => {
    const id = Math.random().toString(36).slice(2);
    setToasts((t) => [...t, { id, msg, kind }]);
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 2600);
  };
  return (
    <ToastCtx.Provider value={push}>
      {children}
      <div style={{ position: "fixed", bottom: 24, left: "50%", transform: "translateX(-50%)", display: "flex", flexDirection: "column", gap: 8, zIndex: 9999, alignItems: "center" }}>
        {toasts.map((t) => (
          <div key={t.id} className="toast-in" style={{
            display: "flex", alignItems: "center", gap: 10, padding: "11px 16px", borderRadius: 10,
            background: "var(--surface-2)", border: "1px solid var(--border)", boxShadow: "0 8px 30px rgba(0,0,0,0.4)",
            fontSize: 13, color: "var(--fg)",
          }}>
            <span style={{ width: 18, height: 18, borderRadius: 999, background: t.kind === "ok" ? "var(--win)" : "var(--accent)", display: "grid", placeItems: "center", color: "#0a0a0a" }}>
              <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="#0a0a0a" strokeWidth="3"><path d="M20 6 9 17l-5-5" /></svg>
            </span>
            {t.msg}
          </div>
        ))}
      </div>
    </ToastCtx.Provider>
  );
}

// ---- Nav ----
function Nav() {
  const { route, go } = useNav();
  const links = [
    ["Home", "home"], ["Clubs", "clubs"], ["Compare", "compare"],
    ["Schedule", "schedule"], ["Results", "results"], ["Coaches", "coaches"],
  ];
  const isActive = (p) => {
    if (p === "clubs") return ["clubs", "club", "director"].includes(route.page);
    if (p === "coaches") return ["coaches", "coach", "editor", "reviews"].includes(route.page);
    if (p === "results") return ["results"].includes(route.page);
    return route.page === p;
  };
  return (
    <div className="nav">
      <div className="nav-logo" onClick={() => go("home")} style={{ cursor: "pointer" }}>
        <div className="mark">N</div>
        <span>NTVS</span>
        <span style={{ color: "var(--muted)", fontWeight: 400, fontSize: 12, marginLeft: 4 }}>North Texas Volleyball Stats</span>
      </div>
      <div className="nav-links">
        {links.map(([l, p]) => (
          <div key={p} className={`nav-link ${isActive(p) ? "active" : ""}`} onClick={() => go(p)}>{l}</div>
        ))}
      </div>
      <div className="nav-search" onClick={() => go("clubs")} style={{ cursor: "pointer" }}>
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="11" cy="11" r="7" /><path d="m21 21-4.3-4.3" /></svg>
        <span>Search clubs, coaches, tournaments…</span>
        <span style={{ marginLeft: "auto", fontFamily: "var(--font-mono)", fontSize: 10, color: "var(--muted-2)" }}>⌘K</span>
      </div>
      <button className="btn btn-ghost" style={{ fontSize: 12 }} onClick={() => go("director")}>Director</button>
      <button className="nav-cta" onClick={() => go("editor")}>Claim profile</button>
    </div>
  );
}

// ---- Verified badge ----
function VerifiedBadge({ size = 15 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24">
      <circle cx="12" cy="12" r="10" fill="var(--cyan)" />
      <path d="M8 12l2.5 2.5L16 9" stroke="#0a1020" strokeWidth="2.2" fill="none" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

// ---- Stars ----
function Stars({ n = 5, size = 14, color = "var(--accent)" }) {
  return (
    <div style={{ display: "flex", gap: 2 }}>
      {Array.from({ length: 5 }).map((_, i) => (
        <svg key={i} width={size} height={size} viewBox="0 0 24 24" fill={i < n ? color : "var(--surface-2)"}>
          <path d="M12 2l2.9 6.3 6.9.7-5.1 4.6 1.4 6.8L12 17.6 5.9 20.4l1.4-6.8L2.2 9l6.9-.7z" />
        </svg>
      ))}
    </div>
  );
}
// interactive star picker (locked to positive 4-5)
function StarPicker({ value, min = 4, onChange, size = 26 }) {
  const [hover, setHover] = useState(0);
  const shown = hover || value;
  return (
    <div style={{ display: "flex", gap: 3 }} onMouseLeave={() => setHover(0)}>
      {[1, 2, 3, 4, 5].map((i) => {
        const locked = i < min;
        return (
          <svg key={i} width={size} height={size} viewBox="0 0 24 24"
            fill={i <= shown ? "var(--accent)" : "var(--surface-2)"}
            style={{ cursor: locked ? "not-allowed" : "pointer", opacity: locked ? 0.4 : 1, transition: "transform .1s", transform: hover === i ? "scale(1.15)" : "none" }}
            onMouseEnter={() => !locked && setHover(i)}
            onClick={() => !locked && onChange(i)}>
            <path d="M12 2l2.9 6.3 6.9.7-5.1 4.6 1.4 6.8L12 17.6 5.9 20.4l1.4-6.8L2.2 9l6.9-.7z" />
          </svg>
        );
      })}
    </div>
  );
}

function Bar({ value, max = 100, color = "var(--accent)", height = 6, animate = true }) {
  const [w, setW] = useState(animate ? 0 : (value / max) * 100);
  useEffect(() => { const t = setTimeout(() => setW((value / max) * 100), 60); return () => clearTimeout(t); }, [value, max]);
  return (
    <div style={{ background: "var(--surface-2)", borderRadius: 999, height, overflow: "hidden" }}>
      <div style={{ width: `${w}%`, height: "100%", background: color, borderRadius: 999, transition: "width .7s cubic-bezier(.2,.7,.3,1)" }} />
    </div>
  );
}

function Sparkline({ data, color = "var(--cyan)", w = 96, h = 28 }) {
  const max = Math.max(...data), min = Math.min(...data);
  const pts = data.map((v, i) => {
    const x = (i / (data.length - 1)) * w;
    const y = h - ((v - min) / (max - min || 1)) * h;
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(" ");
  return (
    <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`}>
      <polyline points={pts} fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function Radar({ clubs, metrics }) {
  const cx = 150, cy = 140, R = 110, n = metrics.length;
  const angle = (i) => (Math.PI * 2 * i) / n - Math.PI / 2;
  const pt = (i, r) => [cx + Math.cos(angle(i)) * R * r, cy + Math.sin(angle(i)) * R * r];
  return (
    <svg width="300" height="290" viewBox="0 0 300 290">
      {[0.25, 0.5, 0.75, 1].map((r) => (
        <polygon key={r} points={metrics.map((_, i) => pt(i, r).join(",")).join(" ")} fill="none" stroke="var(--border)" strokeWidth="1" />
      ))}
      {metrics.map((_, i) => { const [x, y] = pt(i, 1); return <line key={i} x1={cx} y1={cy} x2={x} y2={y} stroke="var(--border)" strokeWidth="1" />; })}
      {clubs.map((c) => (
        <polygon key={c.id} points={metrics.map((m, i) => pt(i, c.vals[i]).join(",")).join(" ")} fill={c.color} fillOpacity="0.12" stroke={c.color} strokeWidth="2" style={{ transition: "all .5s" }} />
      ))}
      {metrics.map((m, i) => { const [x, y] = pt(i, 1.18); return (
        <text key={m} x={x} y={y} textAnchor="middle" dominantBaseline="middle" fontSize="9.5" fill="var(--muted)" fontFamily="var(--font-mono)">{m}</text>
      ); })}
    </svg>
  );
}

// club avatar
function ClubMark({ c, size = 40, radius = 8 }) {
  return (
    <div style={{ width: size, height: size, borderRadius: radius, background: c.color, color: "#0a0a0a", display: "grid", placeItems: "center", fontFamily: "var(--font-display)", fontWeight: 700, fontSize: size * 0.4, flexShrink: 0 }}>
      {c.name.split(" ").map((w) => w[0]).slice(0, 2).join("")}
    </div>
  );
}

Object.assign(window, {
  NavCtx, useNav, ToastCtx, useToast, ToastHost, Nav,
  VerifiedBadge, Stars, StarPicker, Bar, Sparkline, Radar, ClubMark,
});
