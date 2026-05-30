// NTVS Prototype — Coach profile (tabbed) + Endorsements
function PCoach({ id }) {
  const { go, store } = useNav();
  const co = coachById(id) || COACHES[0];
  const [tab, setTab] = useState("Overview");
  const club = clubById(co.clubId);
  const reviews = store.reviewsFor(co.id);

  return (
    <div className="page" style={{ padding: 0 }}>
      <div style={{ display: "grid", gridTemplateColumns: "300px 1fr", minHeight: "100%" }}>
        {/* RAIL */}
        <div style={{ borderRight: "1px solid var(--border)", padding: "36px 28px", background: "var(--bg-2)" }}>
          <div style={{ width: 96, height: 96, borderRadius: 20, background: co.grad, color: "#fff", display: "grid", placeItems: "center", fontFamily: "var(--font-display)", fontWeight: 700, fontSize: 34, marginBottom: 18 }}>{co.init}</div>
          <h1 style={{ fontSize: 28 }}>{co.name}</h1>
          {co.verified ? (
            <div style={{ display: "flex", alignItems: "center", gap: 6, marginTop: 8 }}>
              <VerifiedBadge /><span style={{ fontSize: 12, color: "var(--cyan)", fontWeight: 600 }}>Verified coach</span>
            </div>
          ) : (
            <div style={{ display: "flex", alignItems: "center", gap: 6, marginTop: 8 }}>
              <span style={{ fontSize: 12, color: "var(--muted)" }}>Unverified · pending club</span>
            </div>
          )}
          <div style={{ fontSize: 13, color: "var(--fg-2)", marginTop: 14, lineHeight: 1.5 }}>
            {co.role}<br /><span style={{ color: club.color, fontWeight: 600, cursor: "pointer" }} onClick={() => go("club", { id: club.id })}>{club.name}</span> · {co.city}, TX
          </div>
          <div style={{ display: "flex", gap: 8, marginTop: 20 }}>
            <button className="btn btn-primary" style={{ flex: 1, justifyContent: "center" }} onClick={() => store.toast("Contact request sent to " + co.name)}>Contact</button>
            <button className="btn" style={{ flex: 1, justifyContent: "center" }} onClick={() => store.toast("Following " + co.name)}>Follow</button>
          </div>
          <button className="btn btn-ghost" style={{ width: "100%", justifyContent: "center", marginTop: 10, fontSize: 12, color: "var(--muted)" }} onClick={() => go("editor")}>This is me — edit profile</button>

          <div className="divider" style={{ margin: "24px 0" }} />
          <div className="label" style={{ marginBottom: 12 }}>Career totals</div>
          {[["Matches won", co.totals.wins], ["Win rate", co.totals.winRate + "%"], ["College commits", co.totals.commits], ["Gold finishes", co.totals.gold], ["Seasons", co.totals.seasons]].map(([k, v]) => (
            <div key={k} style={{ display: "flex", justifyContent: "space-between", padding: "7px 0", fontSize: 13 }}>
              <span style={{ color: "var(--muted)" }}>{k}</span><span className="mono tabular" style={{ color: "var(--fg)" }}>{v}</span>
            </div>
          ))}
          <div className="divider" style={{ margin: "24px 0" }} />
          <div className="label" style={{ marginBottom: 12 }}>Certifications</div>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {co.certs.map((c) => <div key={c} style={{ fontSize: 12, color: "var(--fg-2)", display: "flex", gap: 8, alignItems: "center" }}><span style={{ color: "var(--cyan)" }}>✓</span>{c}</div>)}
          </div>
          <div className="divider" style={{ margin: "24px 0" }} />
          <div className="label" style={{ marginBottom: 12 }}>Specialties</div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
            {co.specialties.map((s) => <span key={s} className="chip" style={{ fontSize: 11 }}>{s}</span>)}
          </div>
        </div>

        {/* BODY */}
        <div style={{ padding: "28px 48px 56px" }}>
          {/* tabs */}
          <div style={{ display: "flex", gap: 4, borderBottom: "1px solid var(--border)", marginBottom: 28 }}>
            {["Overview", "Career", "Teams", `Endorsements · ${reviews.length}`].map((t) => {
              const key = t.split(" ·")[0];
              return <div key={t} onClick={() => setTab(key)} style={{ padding: "10px 16px", fontSize: 14, cursor: "pointer", fontWeight: tab === key ? 600 : 500, color: tab === key ? "var(--fg)" : "var(--muted)", borderBottom: tab === key ? "2px solid var(--accent)" : "2px solid transparent", marginBottom: -1 }}>{t}</div>;
            })}
          </div>

          {(tab === "Overview" || tab === "Career") && (
            <React.Fragment>
              {co.verified && (
                <div className="card" style={{ padding: "16px 20px", display: "flex", alignItems: "center", gap: 16, marginBottom: 28, borderLeft: "3px solid var(--cyan)" }}>
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--cyan)" strokeWidth="2"><path d="M10 13a5 5 0 0 0 7 0l3-3a5 5 0 0 0-7-7l-1 1" /><path d="M14 11a5 5 0 0 0-7 0l-3 3a5 5 0 0 0 7 7l1-1" /></svg>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 13, fontWeight: 600 }}>Profile connected to {club.name}</div>
                    <div style={{ fontSize: 12, color: "var(--muted)", marginTop: 2 }}>Verified by club director · {co.career.length} linked programs</div>
                  </div>
                </div>
              )}
              <h2 style={{ fontSize: 22, marginBottom: 6 }}>Coaching career</h2>
              <p style={{ fontSize: 13, color: "var(--muted)", marginBottom: 24 }}>Verified club & team history, pulled from NTVS match records.</p>
              <div style={{ position: "relative", paddingLeft: 28 }}>
                <div style={{ position: "absolute", left: 7, top: 6, bottom: 6, width: 2, background: "var(--border)" }} />
                {co.career.map((t, i) => (
                  <div key={i} style={{ position: "relative", marginBottom: 28 }}>
                    <div style={{ position: "absolute", left: -28, top: 4, width: 16, height: 16, borderRadius: 999, background: t.clubColor, border: "3px solid var(--bg)" }} />
                    <div className="card" style={{ padding: 20 }}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 8 }}>
                        <div>
                          <div style={{ display: "flex", alignItems: "center", gap: 10 }}><span style={{ width: 9, height: 9, borderRadius: 2, background: t.clubColor }} /><span style={{ fontWeight: 700, fontSize: 17 }}>{t.club}</span></div>
                          <div style={{ fontSize: 13, color: "var(--fg-2)", marginTop: 5 }}>{t.role}</div>
                        </div>
                        <div style={{ textAlign: "right" }}>
                          <div className="mono" style={{ fontSize: 12, color: "var(--muted)" }}>{t.yr}</div>
                          {t.rec !== "—" && <div className="mono tabular" style={{ fontSize: 15, color: "var(--accent)", marginTop: 4 }}>{t.rec}</div>}
                        </div>
                      </div>
                      <p style={{ fontSize: 13, color: "var(--fg-2)", marginTop: 12, lineHeight: 1.5 }}>{t.note}</p>
                    </div>
                  </div>
                ))}
              </div>
            </React.Fragment>
          )}

          {tab === "Teams" && (
            <React.Fragment>
              <h2 style={{ fontSize: 22, margin: "0 0 18px" }}>Teams coached</h2>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 12 }}>
                {co.teams.map(([team, yr, club2, rec, m], i) => (
                  <div key={i} className="card" style={{ padding: 16 }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}><span style={{ fontWeight: 600, fontSize: 14 }}>{team}</span><span style={{ fontSize: 18 }}>{m}</span></div>
                    <div style={{ fontSize: 12, color: "var(--muted)", marginTop: 6 }}>{club2} · {yr}</div>
                    <div className="mono tabular" style={{ fontSize: 14, color: "var(--fg-2)", marginTop: 8 }}>{rec}</div>
                  </div>
                ))}
              </div>
            </React.Fragment>
          )}

          {tab === "Endorsements" && <Endorsements co={co} reviews={reviews} />}
        </div>
      </div>
    </div>
  );
}

// ---- Endorsements (positive-only) ----
function Endorsements({ co, reviews }) {
  const { store } = useNav();
  const [stars, setStars] = useState(5);
  const [rel, setRel] = useState("Parent");
  const [tags, setTags] = useState(["Great communicator"]);
  const [body, setBody] = useState("");
  const [open, setOpen] = useState(false);

  const tagCounts = {};
  reviews.forEach((r) => r.tags.forEach((t) => { tagCounts[t] = (tagCounts[t] || 0) + 1; }));
  const topTags = Object.entries(tagCounts).sort((a, b) => b[1] - a[1]);
  const avg = reviews.length ? (reviews.reduce((s, r) => s + r.stars, 0) / reviews.length).toFixed(1) : "—";

  const positive = body.trim().length === 0 || !/\b(bad|awful|terrible|hate|worst|rude|unfair)\b/i.test(body);
  const toggleTag = (t) => setTags((p) => p.includes(t) ? p.filter((x) => x !== t) : [...p, t]);

  const submit = () => {
    if (!positive) { store.toast("Endorsements are positive-only — please revise", "warn"); return; }
    store.addReview(co.id, { who: rel === "Parent" ? "Parent" : rel === "Player" ? "Player" : rel, rel: "Just now", body: body.trim() || "Great coach — highly recommend!", tags, when: "Just now", stars });
    setBody(""); setTags(["Great communicator"]); setOpen(false);
    store.toast("Endorsement posted — thank you!");
  };

  return (
    <div style={{ display: "grid", gridTemplateColumns: "1.5fr 1fr", gap: 36, alignItems: "start" }}>
      <div>
        <div className="card" style={{ padding: 22, marginBottom: 20, display: "flex", gap: 36, alignItems: "center" }}>
          <div style={{ textAlign: "center" }}>
            <div className="stat-num" style={{ fontSize: 48, color: "var(--accent)" }}>{avg}</div>
            <Stars n={5} size={15} /><div style={{ fontSize: 12, color: "var(--muted)", marginTop: 8 }}>{reviews.length} endorsements</div>
          </div>
          <div style={{ flex: 1 }}>
            <div className="label" style={{ marginBottom: 12 }}>Most mentioned strengths</div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
              {topTags.length ? topTags.map(([t, n]) => <span key={t} className="chip chip-cyan" style={{ fontSize: 12, padding: "6px 11px" }}>{t} <span className="mono" style={{ opacity: 0.7 }}>·{n}</span></span>) : <span style={{ fontSize: 13, color: "var(--muted)" }}>Be the first to endorse.</span>}
            </div>
          </div>
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {reviews.map((r, i) => (
            <div key={i} className={`card ${i === 0 && r.when === "Just now" ? "pop-in" : ""}`} style={{ padding: 20 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                  <div style={{ width: 38, height: 38, borderRadius: 999, background: "var(--surface-2)", display: "grid", placeItems: "center", color: "var(--muted)" }}><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="8" r="4" /><path d="M4 21c0-4 4-6 8-6s8 2 8 6" /></svg></div>
                  <div><div style={{ fontSize: 13, fontWeight: 600 }}>{r.who}</div><div style={{ fontSize: 11, color: "var(--muted)", marginTop: 2 }}>{r.rel}</div></div>
                </div>
                <div style={{ textAlign: "right" }}><Stars n={r.stars} size={12} /><div style={{ fontSize: 11, color: "var(--muted)", marginTop: 4 }}>{r.when}</div></div>
              </div>
              <p style={{ fontSize: 14, color: "var(--fg-2)", lineHeight: 1.6 }}>{r.body}</p>
              <div style={{ display: "flex", gap: 6, marginTop: 12, flexWrap: "wrap" }}>{r.tags.map((t) => <span key={t} className="chip" style={{ fontSize: 10 }}>{t}</span>)}</div>
            </div>
          ))}
        </div>
      </div>

      {/* write */}
      <div style={{ position: "sticky", top: 0 }}>
        <div className="card" style={{ padding: 24, borderTop: "3px solid var(--cyan)" }}>
          <h3 style={{ fontSize: 18, marginBottom: 6 }}>Leave an endorsement</h3>
          <div style={{ display: "flex", gap: 10, alignItems: "flex-start", background: "rgba(91,184,255,0.08)", border: "1px solid rgba(91,184,255,0.25)", borderRadius: 8, padding: "10px 12px", marginBottom: 20 }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--cyan)" strokeWidth="2" style={{ flexShrink: 0, marginTop: 1 }}><path d="M7 11v8H4v-8zM7 11l4-7a2 2 0 0 1 3 2l-1 5h5a2 2 0 0 1 2 2.3l-1.3 6A2 2 0 0 1 20 19H7" /></svg>
            <div style={{ fontSize: 12, color: "var(--fg-2)", lineHeight: 1.5 }}>NTVS endorsements are <strong style={{ color: "var(--cyan)" }}>positive-only</strong>. Share what a coach does well — concerns go through your club director privately.</div>
          </div>
          <div className="label" style={{ marginBottom: 8 }}>Your rating</div>
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 20 }}>
            <StarPicker value={stars} onChange={setStars} />
            <span style={{ fontSize: 13, color: "var(--muted)" }}>{stars === 5 ? "Outstanding" : "Excellent"}</span>
          </div>
          <div className="label" style={{ marginBottom: 8 }}>Your relationship</div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 7, marginBottom: 20 }}>
            {["Parent", "Player", "Fellow coach", "Club staff"].map((r) => (
              <span key={r} className="chip" style={{ fontSize: 12, padding: "7px 13px", cursor: "pointer", background: rel === r ? "var(--accent)" : "var(--surface-2)", color: rel === r ? "#0a0a0a" : "var(--fg-2)", fontWeight: rel === r ? 600 : 500 }} onClick={() => setRel(r)}>{r}</span>
            ))}
          </div>
          <div className="label" style={{ marginBottom: 8 }}>What stood out? <span style={{ textTransform: "none", letterSpacing: 0, color: "var(--muted-2)" }}>(pick a few)</span></div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 7, marginBottom: 20 }}>
            {ENDORSE_TAGS.map((t) => {
              const on = tags.includes(t);
              return <span key={t} className={on ? "chip chip-cyan" : "chip"} style={{ fontSize: 12, padding: "7px 12px", cursor: "pointer", border: on ? "1px solid rgba(91,184,255,0.4)" : "1px solid transparent" }} onClick={() => toggleTag(t)}>{on && "✓ "}{t}</span>;
            })}
          </div>
          <div className="label" style={{ marginBottom: 8 }}>Your endorsement</div>
          <textarea value={body} onChange={(e) => setBody(e.target.value)} maxLength={500} placeholder="Coach helped my daughter grow so much this season…" style={{ width: "100%", background: "var(--bg-2)", border: `1px solid ${positive ? "var(--border)" : "var(--loss)"}`, borderRadius: 8, padding: "12px 14px", fontSize: 13, color: "var(--fg)", minHeight: 88, lineHeight: 1.55, fontFamily: "inherit", resize: "vertical", outline: "none" }} />
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: 8 }}>
            {positive ? (
              <span style={{ fontSize: 11, color: "var(--win)", display: "flex", alignItems: "center", gap: 5 }}><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="var(--win)" strokeWidth="2.4"><path d="M20 6 9 17l-5-5" /></svg>Positive tone detected</span>
            ) : (
              <span style={{ fontSize: 11, color: "var(--loss)" }}>⚠ Please keep it positive</span>
            )}
            <span style={{ fontSize: 11, color: "var(--muted)" }}>{body.length} / 500</span>
          </div>
          <button className="btn btn-primary" style={{ width: "100%", justifyContent: "center", marginTop: 18, padding: "12px", opacity: positive ? 1 : 0.5 }} onClick={submit}>Post endorsement</button>
          <p style={{ fontSize: 11, color: "var(--muted)", textAlign: "center", marginTop: 12, lineHeight: 1.5 }}>Posts publicly under your name. Endorsements are screened to keep NTVS supportive for young athletes.</p>
        </div>
      </div>
    </div>
  );
}
Object.assign(window, { PCoach, Endorsements });
