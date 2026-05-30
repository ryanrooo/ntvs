// NTVS Prototype — Coach profile editor (stepper + live preview)
function PEditor() {
  const { go, store } = useNav();
  const steps = ["Basics", "Link clubs", "Career history", "Credentials", "Review"];
  const [step, setStep] = useState(2);
  const [positions, setPositions] = useState([
    { club: "Drive Nation", color: "#5bb8ff", role: "Head Coach · 18 Black", yr: "2022–Present", verified: true },
    { club: "Texas Advantage", color: "#f5c518", role: "Head Coach · 16/17 Elite", yr: "2019–2022", verified: true },
  ]);
  const [draft, setDraft] = useState({ club: "Texas Tornados", role: "Assistant Coach", age: "15–17", yr: "2016–2019", note: "" });
  const [showForm, setShowForm] = useState(true);

  const colorFor = (name) => (clubById(CLUBS.find((c) => c.name === name)?.id)?.color) || "#fb923c";

  const addPosition = () => {
    if (!draft.club || !draft.role) { store.toast("Add a club and role first", "warn"); return; }
    setPositions((p) => [...p, { club: draft.club, color: colorFor(draft.club), role: `${draft.role} · ${draft.age}`, yr: draft.yr, verified: false }]);
    setDraft({ club: "", role: "", age: "", yr: "", note: "" });
    setShowForm(false);
    store.toast("Position added to your resume");
  };
  const removePos = (i) => setPositions((p) => p.filter((_, idx) => idx !== i));

  const strength = Math.min(100, 40 + positions.length * 14 + (step >= 3 ? 10 : 0));

  return (
    <div className="page" style={{ padding: 0, display: "flex", flexDirection: "column" }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "18px 40px", borderBottom: "1px solid var(--border)", background: "var(--bg-2)" }}>
        <div><div className="kicker" style={{ marginBottom: 5 }}>Editing your profile · Draft</div><h2 style={{ fontSize: 20 }}>Build your coaching resume</h2></div>
        <div style={{ display: "flex", alignItems: "center", gap: 18 }}>
          <span style={{ fontSize: 12, color: "var(--muted)" }}>Saved just now</span>
          <button className="btn" onClick={() => go("coach", { id: "mdelgado" })}>Preview</button>
          <button className="btn btn-primary" onClick={() => { store.toast("Profile published!"); go("coach", { id: "mdelgado" }); }}>Publish profile</button>
        </div>
      </div>

      {/* stepper */}
      <div style={{ display: "flex", gap: 8, padding: "16px 40px", borderBottom: "1px solid var(--border)" }}>
        {steps.map((s, i) => (
          <div key={s} style={{ display: "flex", alignItems: "center", gap: 8, flex: 1, cursor: "pointer" }} onClick={() => setStep(i)}>
            <div style={{ width: 24, height: 24, borderRadius: 999, display: "grid", placeItems: "center", fontSize: 12, fontWeight: 700, fontFamily: "var(--font-mono)", transition: "all .2s", background: i < step ? "var(--cyan)" : i === step ? "var(--accent)" : "var(--surface-2)", color: i <= step ? "#0a0a0a" : "var(--muted)" }}>{i < step ? "✓" : i + 1}</div>
            <span style={{ fontSize: 13, fontWeight: i === step ? 600 : 400, color: i === step ? "var(--fg)" : "var(--muted)" }}>{s}</span>
            {i < steps.length - 1 && <div style={{ flex: 1, height: 1, background: i < step ? "var(--cyan)" : "var(--border)" }} />}
          </div>
        ))}
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1.25fr 1fr", flex: 1, minHeight: 0 }}>
        {/* FORM */}
        <div style={{ padding: "28px 40px", overflow: "auto", borderRight: "1px solid var(--border)" }}>
          {step === 2 ? (
            <React.Fragment>
              <h3 style={{ fontSize: 18, marginBottom: 4 }}>Career history</h3>
              <p style={{ fontSize: 13, color: "var(--muted)", marginBottom: 22 }}>Add the teams you've coached. Verified entries are matched against NTVS match records automatically.</p>
              {positions.map((e, i) => (
                <div key={i} className="card" style={{ padding: 16, marginBottom: 12, borderLeft: `3px solid ${e.color}` }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                    <div>
                      <div style={{ display: "flex", alignItems: "center", gap: 8 }}><span style={{ fontWeight: 600, fontSize: 15 }}>{e.club}</span>{e.verified ? <span className="chip chip-cyan" style={{ fontSize: 9 }}>✓ VERIFIED</span> : <span className="chip chip-amber" style={{ fontSize: 9 }}>PENDING</span>}</div>
                      <div style={{ fontSize: 13, color: "var(--fg-2)", marginTop: 4 }}>{e.role}</div>
                      <div className="mono" style={{ fontSize: 12, color: "var(--muted)", marginTop: 4 }}>{e.yr}</div>
                    </div>
                    <span className="hoverable" style={{ fontSize: 13, color: "var(--muted)", cursor: "pointer", padding: 4 }} onClick={() => removePos(i)}>✕</span>
                  </div>
                </div>
              ))}

              {showForm ? (
                <div className="card pop-in" style={{ padding: 18, marginTop: 6, border: "1px solid var(--accent)" }}>
                  <div className="label" style={{ marginBottom: 16, color: "var(--accent)" }}>+ New position</div>
                  <div style={{ display: "flex", gap: 14 }}>
                    <EField label="Club" value={draft.club} onChange={(v) => setDraft({ ...draft, club: v })} list={CLUBS.map((c) => c.name)} />
                    <EField label="Role" value={draft.role} onChange={(v) => setDraft({ ...draft, role: v })} placeholder="Head Coach" />
                  </div>
                  <div style={{ display: "flex", gap: 14 }}>
                    <EField label="Age group / team" value={draft.age} onChange={(v) => setDraft({ ...draft, age: v })} placeholder="15–17" />
                    <EField label="Years" value={draft.yr} onChange={(v) => setDraft({ ...draft, yr: v })} placeholder="2016 – 2019" mono />
                  </div>
                  <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
                    <button className="btn btn-primary" style={{ fontSize: 13 }} onClick={addPosition}>Add position</button>
                    <button className="btn btn-ghost" style={{ fontSize: 13, color: "var(--muted)" }} onClick={() => setShowForm(false)}>Cancel</button>
                  </div>
                </div>
              ) : (
                <button className="btn" style={{ width: "100%", justifyContent: "center", marginTop: 6 }} onClick={() => setShowForm(true)}>＋ Add another position</button>
              )}

              <div className="card" style={{ padding: 16, marginTop: 20, display: "flex", gap: 14, alignItems: "center", background: "var(--bg-2)" }}>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--cyan)" strokeWidth="2"><path d="M10 13a5 5 0 0 0 7 0l3-3a5 5 0 0 0-7-7l-1 1" /><path d="M14 11a5 5 0 0 0-7 0l-3 3a5 5 0 0 0 7 7l1-1" /></svg>
                <div style={{ flex: 1 }}><div style={{ fontSize: 13, fontWeight: 600 }}>Request club verification</div><div style={{ fontSize: 12, color: "var(--muted)", marginTop: 2 }}>Your club's director can confirm your role to earn the ✓ badge.</div></div>
                <button className="btn" style={{ fontSize: 12 }} onClick={() => store.toast("Verification request sent")}>Send request</button>
              </div>
            </React.Fragment>
          ) : (
            <div style={{ textAlign: "center", padding: "60px 20px", color: "var(--muted)" }}>
              <div style={{ fontSize: 16, fontWeight: 600, color: "var(--fg)", marginBottom: 8 }}>{steps[step]}</div>
              <p style={{ fontSize: 13, maxWidth: 320, margin: "0 auto 20px", lineHeight: 1.5 }}>This step is part of the full flow. Jump to <strong style={{ color: "var(--accent)" }}>Career history</strong> to try the live resume builder.</p>
              <button className="btn btn-primary" onClick={() => setStep(2)}>Go to Career history</button>
            </div>
          )}

          {/* nav */}
          <div style={{ display: "flex", justifyContent: "space-between", marginTop: 28, paddingTop: 20, borderTop: "1px solid var(--border-soft)" }}>
            <button className="btn" disabled={step === 0} style={{ opacity: step === 0 ? 0.4 : 1 }} onClick={() => setStep((s) => Math.max(0, s - 1))}>← Back</button>
            <button className="btn btn-primary" onClick={() => step < steps.length - 1 ? setStep((s) => s + 1) : (store.toast("Profile published!"), go("coach", { id: "mdelgado" }))}>{step < steps.length - 1 ? "Continue →" : "Publish"}</button>
          </div>
        </div>

        {/* LIVE PREVIEW */}
        <div style={{ padding: "28px 32px", overflow: "auto", background: "var(--bg-2)" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 18 }}>
            <div className="label">Live preview</div><span className="chip" style={{ fontSize: 10 }}>How recruiters see it</span>
          </div>
          <div className="card" style={{ padding: 22, background: "var(--surface)" }}>
            <div style={{ display: "flex", gap: 16, alignItems: "center" }}>
              <div style={{ width: 60, height: 60, borderRadius: 14, background: "linear-gradient(135deg, #5bb8ff, #2563eb)", color: "#fff", display: "grid", placeItems: "center", fontFamily: "var(--font-display)", fontWeight: 700, fontSize: 22 }}>MD</div>
              <div>
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}><span style={{ fontWeight: 700, fontSize: 20, fontFamily: "var(--font-display)" }}>Maria Delgado</span><VerifiedBadge /></div>
                <div style={{ fontSize: 12, color: "var(--muted)", marginTop: 4 }}>Head Coach · Drive Nation · Frisco, TX</div>
              </div>
            </div>
            <div style={{ display: "flex", gap: 24, marginTop: 18, paddingTop: 18, borderTop: "1px solid var(--border-soft)" }}>
              {[["189", "Wins"], ["73%", "Win rate"], ["23", "Commits"], [String(positions.filter((p) => p.verified).length), "Verified"]].map(([v, k]) => (
                <div key={k}><div className="stat-num" style={{ fontSize: 22 }}>{v}</div><div className="label" style={{ marginTop: 3 }}>{k}</div></div>
              ))}
            </div>
            <div className="label" style={{ margin: "20px 0 12px" }}>Career · {positions.length} positions</div>
            <div style={{ position: "relative", paddingLeft: 20 }}>
              <div style={{ position: "absolute", left: 4, top: 4, bottom: 4, width: 2, background: "var(--border)" }} />
              {positions.map((p, i) => (
                <div key={i} className="pop-in" style={{ position: "relative", marginBottom: 14, opacity: p.verified ? 1 : 0.75 }}>
                  <div style={{ position: "absolute", left: -20, top: 3, width: 10, height: 10, borderRadius: 999, background: p.color, border: "2px solid var(--surface)" }} />
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <span style={{ fontSize: 13, fontWeight: 600 }}>{p.club}</span>
                    {!p.verified && <span style={{ fontSize: 10, color: "var(--accent)" }}>● pending</span>}
                  </div>
                  <div style={{ fontSize: 12, color: "var(--muted)", marginTop: 2 }}>{p.role} · <span className="mono">{p.yr}</span></div>
                </div>
              ))}
            </div>
          </div>
          <div style={{ marginTop: 16 }}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}><span style={{ fontSize: 12, color: "var(--muted)" }}>Profile strength</span><span style={{ fontSize: 12, color: "var(--accent)", fontWeight: 600 }}>{strength}%</span></div>
            <Bar value={strength} color="var(--accent)" height={8} />
            <div style={{ fontSize: 11, color: "var(--muted)", textAlign: "center", marginTop: 10 }}>{strength < 100 ? "Add a photo & more positions to reach 100%" : "Looking great — ready to publish!"}</div>
          </div>
        </div>
      </div>
    </div>
  );
}

function EField({ label, value, onChange, placeholder, mono, list }) {
  const id = useRef("dl" + Math.random().toString(36).slice(2)).current;
  return (
    <div style={{ marginBottom: 16, flex: 1 }}>
      <div className="label" style={{ marginBottom: 7 }}>{label}</div>
      <input value={value} onChange={(e) => onChange(e.target.value)} placeholder={placeholder} list={list ? id : undefined}
        style={{ width: "100%", background: "var(--bg-2)", border: "1px solid var(--border)", borderRadius: 8, padding: "10px 12px", fontSize: 14, color: "var(--fg)", fontFamily: mono ? "var(--font-mono)" : "var(--font-sans)", outline: "none" }} />
      {list && <datalist id={id}>{list.map((o) => <option key={o} value={o} />)}</datalist>}
    </div>
  );
}
Object.assign(window, { PEditor, EField });
