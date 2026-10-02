"use client";

import { useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import { CitationViewer, type CitationView } from "./citation-viewer";

type Card = { plan_id: string; index_version: string; insurer: string; name: string; variant: string; plan_type: string; status: string };
type Reason = { field: string; status: string; explanation: string; citations: { quote: string }[] };
type Fit = { plan_id: string; status: string; hard_limits: Reason[]; other_needs: Reason[] };
type Anchor = { quote: string; page: number; method: string; role: string; document_id: string; boxes: [number, number, number, number][]; pdf_url: string };
type PlanResult = { id: string; plan_id: string; index_version: string; name: string; plan_type: string; state: string; model: string; result?: { status: string; message?: string; reason?: string; answer?: { statements: { text: string; conditions: { text: string }[]; restrictions: { text: string }[] }[] }; validation?: { anchors: Anchor[] }; omissions?: string[] } | null };
type Question = { id: string; state: string; plans: PlanResult[] };
type Price = { status: string; amount_printed: string | null; label: string; caveat: string; missing_axes: string[]; axis_options: Record<string, string[]>; citations: { quote: string }[] };
type Coverage = { selection_basis: string; method: string | null; insurers: { id: string; name: string; discovery_status: string; candidate_document_count: number; browser_recovered_pdfs: number; register_entries: number | null; catalogue_complete: boolean }[]; plans: { id: string; name: string; insurer: string; documents: number; pages: number; sections: number; map_fallbacks: number; models: string[]; status: string }[] };
const types = [{ value: "medical_indemnity", label: "Hospital expense cover" }, { value: "top_up", label: "Top-up" }, { value: "super_top_up", label: "Super top-up" }, { value: "critical_illness", label: "Critical illness" }, { value: "fixed_benefit", label: "Fixed benefit" }];
const statusLabel: Record<string, string> = { fits: "Fits documented limits", doesnt_fit: "Doesn’t fit documented limits", unresolved: "Unresolved", ready: "Ready", partial: "Partial documents / facts", documents_unavailable: "Documents unavailable" };

export function DemoApp({ onSignedOut }: { onSignedOut: () => Promise<void> }) {
  const [screen, setScreen] = useState("start");
  const [cards, setCards] = useState<Card[]>([]);
  const [release, setRelease] = useState<string | null>(null);
  const [fits, setFits] = useState<Fit[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const [sessionId, setSessionId] = useState("");
  const [people, setPeople] = useState([{ id: "person-1", relationship: "self", age: "35", ageUnit: "years", dependent: false }]);
  const [city, setCity] = useState("Pune");
  const [sumInsured, setSumInsured] = useState("1000000");
  const [planType, setPlanType] = useState("medical_indemnity");
  const [needs, setNeeds] = useState<string[]>([]);
  const [typedNeeds, setTypedNeeds] = useState("");
  const [budget, setBudget] = useState("");
  const [questionText, setQuestionText] = useState("What room limits and conditions apply?");
  const [question, setQuestion] = useState<Question | null>(null);
  const [coverage, setCoverage] = useState<Coverage | null>(null);
  const [prices, setPrices] = useState<Record<string, Price>>({});
  const [priceAxes, setPriceAxes] = useState<Record<string, Record<string, string>>>({});
  const [citation, setCitation] = useState<CitationView | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [insurer, setInsurer] = useState("");
  const [confirmErasure, setConfirmErasure] = useState(false);
  const events = useRef<EventSource | null>(null);

  useEffect(() => { window.scrollTo(0, 0); }, [screen]);

  useEffect(() => {
    void api<{ plans: Card[]; release_id: string | null }>("/api/v2/demo/catalogue/")
      .then(data => { setCards([...data.plans].sort((a,b) => a.insurer.localeCompare(b.insurer) || a.name.localeCompare(b.name) || a.variant.localeCompare(b.variant))); setRelease(data.release_id); })
      .catch(e => setError(e.message));
    return () => events.current?.close();
  }, []);

  async function perform(fn: () => Promise<void>) {
    setBusy(true); setError("");
    try { await fn(); } catch (e) { setError(e instanceof Error ? e.message : "Request unavailable"); }
    finally { setBusy(false); }
  }

  async function findPlans() {
    await perform(async () => {
      const data = await api<{ session_id: string; results: Fit[] }>("/api/v2/demo/fit/", { method: "POST", body: JSON.stringify({
        ...(sessionId ? { session_id: sessionId } : {}),
        profile: { schema_version: 1, revision: 1, people: people.map(p => ({ id: p.id, relationship: p.relationship,
          age_days: p.age === "" ? null : Math.round(Number(p.age) * (p.ageUnit === "days" ? 1 : 365)), dependent: p.relationship === "child" ? p.dependent : null })),
          city: city || null, zone: null, sum_insured: sumInsured ? Number(sumInsured) : null, plan_type: planType,
          needs, typed_needs: typedNeeds, annual_budget: budget ? Number(budget) : null } }) });
      setSessionId(data.session_id); setFits(data.results); setQuestion(null); events.current?.close(); setScreen("fits");
    });
  }

  function toggle(card: Card) {
    setError("");
    if (selected.includes(card.plan_id)) { setSelected(selected.filter(id => id !== card.plan_id)); return; }
    if (selected.length === 5) { setError("Select up to five plans."); return; }
    const first = cards.find(c => c.plan_id === selected[0]);
    if (first && first.plan_type !== card.plan_type) { setError("Compare plans of the same type. Clear the selection to change type."); return; }
    setSelected([...selected, card.plan_id]);
  }

  async function ask() {
    await perform(async () => {
      const data = await api<Question>("/api/v2/demo/questions/", { method: "POST", body: JSON.stringify({ session_id: sessionId, question: questionText, plan_ids: selected }) });
      setQuestion(data); setScreen("chat"); events.current?.close();
      const stream = new EventSource(`/api/v2/demo/questions/${data.id}/events/`);
      events.current = stream;
      stream.onmessage = event => { const next = JSON.parse(event.data) as Question; setQuestion(next); if (["completed", "cancelled"].includes(next.state)) stream.close(); };
      stream.onerror = () => { stream.close(); setError("Live updates paused. Refresh the answer to check its progress."); };
    });
  }

  async function openCitation(plan: PlanResult, position: number) {
    await perform(async () => {
      const anchor = await api<Anchor>(`/api/v2/demo/citations/${plan.id}/${position}/`);
      setCitation({ documentVersionId: anchor.document_id, page: anchor.page, quote: anchor.quote,
        label: `${plan.name} · page ${anchor.page}`, bbox: null, boxes: anchor.boxes, pdfUrl: anchor.pdf_url });
    });
  }

  async function showCoverage() {
    setScreen("coverage");
    await perform(async () => setCoverage(await api<Coverage>("/api/v2/demo/coverage/")));
  }

  async function showPrices() {
    setScreen("prices");
    await perform(async () => {
      const entries = await Promise.all(cards.filter(c => selected.includes(c.plan_id)).map(async c =>
        [c.plan_id, await api<Price>(`/api/v2/demo/prices/${c.index_version}/`)] as const));
      setPrices(Object.fromEntries(entries));
    });
  }

  async function lookupPrice(card: Card) {
    await perform(async () => {
      const query = new URLSearchParams(priceAxes[card.plan_id] ?? {});
      const value = await api<Price>(`/api/v2/demo/prices/${card.index_version}/?${query}`);
      setPrices(old => ({ ...old, [card.plan_id]: value }));
    });
  }

  const selectedCards = cards.filter(c => selected.includes(c.plan_id));
  const displayCards = cards.filter(c => (!insurer || c.insurer === insurer));
  function planCard(card: Card, fit?: Fit) {
    return <article className="demo-plan" key={card.plan_id}>
      <label className="demo-plan-title"><input type="checkbox" checked={selected.includes(card.plan_id)} onChange={() => toggle(card)} />
        <span><small>{card.insurer}</small><strong>{card.name}</strong><span>{card.variant} · {types.find(t => t.value === card.plan_type)?.label ?? card.plan_type}</span></span></label>
      <p className={`demo-status ${fit?.status ?? "unresolved"}`}>{statusLabel[fit?.status ?? card.status] ?? card.status}</p>
      {fit && <details><summary>Documented reasons and missing information</summary>
        {[...fit.hard_limits, ...fit.other_needs].map((r, i) => <div className="demo-reason" key={i}><p>{r.explanation}</p>{r.citations.map((c, j) => <blockquote key={j}>{c.quote}</blockquote>)}</div>)}
      </details>}
    </article>;
  }

  return <div className="demo-shell">
    <header className="demo-header"><a href="/demo" className="demo-brand">CoverGuide<span>Document-led comparison</span></a><span className="demo-local">LOCAL DEMO</span></header>
    <nav className="demo-nav" aria-label="Demo screens">{[["start", "Your family"], ["fits", "Fit lists"], ["picker", "All plans"], ["chat", "Compare"]].map(([key, label]) =>
      <button key={key} aria-current={screen === key ? "page" : undefined} onClick={() => setScreen(key)}>{label}</button>)}
      <button aria-current={screen === "prices" ? "page" : undefined} onClick={() => void showPrices()}>Prices</button>
      <button aria-current={screen === "coverage" ? "page" : undefined} onClick={() => void showCoverage()}>Source coverage</button></nav>
    <div className="demo-account"><button onClick={() => setScreen("account")}>Account</button><button disabled={busy} onClick={() => void perform(async () => { await api("/api/v1/auth/logout/", { method: "POST" }); events.current?.close(); await onSignedOut(); })}>Sign out</button></div>
    {error && <p className="demo-error" role="alert">{error}</p>}
    {!release && <p className="demo-notice">Source preparation is in progress. No new comparison release has been published yet.</p>}
    <main>
      {screen === "account" && <section><h1>Your local account.</h1><p>Delete this account to erase its saved profiles and answers. Running answers will be cancelled.</p><label><input type="checkbox" checked={confirmErasure} onChange={e => setConfirmErasure(e.target.checked)} /> I understand this permanently deletes my local account and saved demo data.</label><p><button disabled={!confirmErasure || busy} onClick={() => void perform(async () => { await api("/api/v1/account/", { method: "DELETE" }); events.current?.close(); await onSignedOut(); })}>Delete account and saved data</button></p></section>}
      {screen === "start" && <section className="demo-start"><div><p className="eyebrow">START WITH YOUR NEEDS</p><h1>A clearer view of your health cover.</h1><p>Enter your family details. See every plan against documented limits, then compare the clauses that matter to you.</p><p className="demo-muted">This local demo uses synthetic profiles. A fit result does not promise underwriting acceptance or claim payment.</p></div>
        <form onSubmit={e => { e.preventDefault(); void findPlans(); }} className="demo-form">
          <h2>Who needs cover?</h2>{people.map((p, i) => <div className="demo-person" key={p.id}>
            <label>Relationship<select value={p.relationship} onChange={e => setPeople(people.map((v, n) => n === i ? { ...v, relationship: e.target.value } : v))}>{["self", "spouse", "child", "parent", "parent_in_law", "other"].map(r => <option key={r} value={r}>{r.replaceAll("_", " ")}</option>)}</select></label>
            <label>Age<input type="number" min="0" max={p.ageUnit === "days" ? "43800" : "120"} step="1" value={p.age} onChange={e => setPeople(people.map((v, n) => n === i ? { ...v, age: e.target.value } : v))} /></label>
            <label>Age unit<select value={p.ageUnit} onChange={e => setPeople(people.map((v, n) => n === i ? { ...v, ageUnit: e.target.value } : v))}><option value="years">Completed years</option><option value="days">Days (for young children)</option></select></label>
            {p.relationship === "child" && <label><input type="checkbox" checked={p.dependent} onChange={e => setPeople(people.map((v, n) => n === i ? { ...v, dependent: e.target.checked } : v))} /> Financially dependent</label>}
            {i > 0 && <button type="button" onClick={() => setPeople(people.filter((_, n) => n !== i))}>Remove</button>}
          </div>)}
          <button type="button" disabled={people.length >= 12} onClick={() => setPeople([...people, { id: crypto.randomUUID(), relationship: "child", age: "8", ageUnit: "years", dependent: true }])}>+ Add family member</button>
          <div className="demo-two"><label>City<input value={city} onChange={e => setCity(e.target.value)} /></label><label>Sum insured (₹)<input type="number" min="1" value={sumInsured} onChange={e => setSumInsured(e.target.value)} /></label></div>
          <label>Plan type<select value={planType} onChange={e => setPlanType(e.target.value)}>{types.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}</select></label>
          <fieldset><legend>Other needs</legend><div className="demo-needs">{["maternity", "opd", "copay", "room_limit", "ped_waiting"].map(n => <label key={n}><input type="checkbox" checked={needs.includes(n)} onChange={() => setNeeds(needs.includes(n) ? needs.filter(v => v !== n) : [...needs, n])} />{n.replaceAll("_", " ")}</label>)}</div></fieldset>
          <label>Anything else? Include who the need applies to.<textarea value={typedNeeds} onChange={e => setTypedNeeds(e.target.value)} placeholder="For example: my father has diabetes" /></label>
          <label>Indicative annual budget (₹, optional)<input type="number" min="1" value={budget} onChange={e => setBudget(e.target.value)} /></label>
          <button className="demo-primary" disabled={busy} type="submit">See all plans against my details →</button>
        </form></section>}
      {(screen === "fits" || screen === "picker") && <section><p className="eyebrow">YOUR COMPARISON, YOUR CHOICE</p><h1>{screen === "fits" ? "Every plan, with its evidence." : "Explore the full plan list."}</h1>
        <p>Plans appear in insurer A–Z order. You may select plans from any group. No ranking or recommendation is made.</p>
        <label className="demo-filter">Insurer<select value={insurer} onChange={e => setInsurer(e.target.value)}><option value="">All insurers</option>{[...new Set(cards.map(c => c.insurer))].sort().map(name => <option key={name}>{name}</option>)}</select></label>
        {screen === "fits" ? ["fits", "unresolved", "doesnt_fit"].map(status => { const group = displayCards.filter(c => fits.find(f => f.plan_id === c.plan_id)?.status === status); return <section key={status} className="demo-group"><h2>{statusLabel[status]} <span>{group.length}</span></h2><div className="demo-card-grid">{group.map(c => planCard(c, fits.find(f => f.plan_id === c.plan_id)))}</div>{group.length === 0 && <p className="demo-muted">No plans in this group.</p>}</section>; }) : <div className="demo-card-grid">{displayCards.map(c => planCard(c))}</div>}
        {cards.length === 0 && <p>The catalogue is being prepared. Source coverage shows acquisition status for all ten insurers.</p>}
      </section>}
      {screen === "chat" && <section><p className="eyebrow">SIDE BY SIDE, CLAUSE BY CLAUSE</p><h1>Ask the documents.</h1><p>Select 2–5 plans of the same type. Each plan’s answer appears as it finishes.</p>
        <form className="demo-question" onSubmit={e => { e.preventDefault(); void ask(); }}><input aria-label="Question for selected plans" value={questionText} onChange={e => setQuestionText(e.target.value)} maxLength={3000} /><button className="demo-primary" disabled={busy || selected.length < 2 || !sessionId || !release}>Ask {selected.length} plans</button></form>
        {!sessionId && <p>Add your family details first.</p>}
        {question && !["completed", "cancelled"].includes(question.state) && <button onClick={() => void perform(async () => { await api(`/api/v2/demo/questions/${question.id}/cancel/`, { method: "POST" }); events.current?.close(); setQuestion({ ...question, state: "cancelled", plans: [] }); })}>Cancel question</button>}
        {question && <button onClick={() => void perform(async () => setQuestion(await api(`/api/v2/demo/questions/${question.id}/`)))}>Refresh answer</button>}
        <div className="demo-comparison" style={{ gridTemplateColumns: `repeat(${Math.max(1, selected.length)}, minmax(280px, 1fr))` }}>{(question?.plans ?? selectedCards.map(c => ({ id: c.plan_id, plan_id: c.plan_id, index_version: c.index_version, name: c.name, plan_type: c.plan_type, state: "Ready for a question", model: "", result: null }))).map(plan => <article className="demo-answer" key={plan.plan_id}>
          <header><small>{types.find(t => t.value === plan.plan_type)?.label}</small><h2>{plan.name}</h2><span>{plan.state.replaceAll("_", " ")}</span></header>
          {plan.result?.answer?.statements.map((s, i) => <div key={i}><p className="demo-answer-text">{s.text}</p>{s.conditions.length > 0 && <details open><summary>Conditions</summary>{s.conditions.map((c, j) => <p key={j}>{c.text}</p>)}</details>}{s.restrictions.map((r, j) => <p className="demo-notice" key={j}>{r.text}</p>)}</div>)}
          {plan.result?.message && <p>{plan.result.message}</p>}{plan.result?.reason && <details><summary>Why this answer is limited</summary><p>{plan.result.reason}</p></details>}
          {plan.result?.validation?.anchors.map((a, i) => <button className="demo-citation" key={i} onClick={() => void openCitation(plan, i)}><q>{a.quote}</q><span>Page {a.page} ↗ {a.role === "brochure" ? " · from the brochure" : ""}{a.method !== "native_text" ? " · OCR" : ""}</span></button>)}
          {Boolean(plan.result?.omissions?.length) && <details><summary>{plan.result?.omissions?.length} sections did not fit the evidence packet</summary><p>Omitted evidence is not evidence of an exclusion.</p></details>}
          {plan.model && <small className="demo-muted">Answer model: {plan.model}</small>}
        </article>)}</div>
      </section>}
      {screen === "prices" && <section><p className="eyebrow">PRINTED CHARTS ONLY</p><h1>Indicative prices.</h1><p>A price is shown only when every published chart axis matches. We do not calculate tax, discounts or loadings.</p><div className="demo-card-grid">{selectedCards.map(c => { const price = prices[c.plan_id]; return <article className="demo-plan" key={c.plan_id}><h2>{c.name}</h2><p>{price?.label}</p><strong>{price?.amount_printed ?? ({ unpublished: "Price not published", source_unavailable: "Official price source is unavailable or not yet confirmed", invalid_chart: "Chart could not be validated", missing_details: "More details needed", no_exact_combination: "No exact chart combination" }[price?.status ?? ""] ?? "Checking…")}</strong><p>{price?.caveat}</p>{price && Object.keys(price.axis_options ?? {}).length > 0 && <fieldset><legend>Match the printed chart details</legend>{Object.entries(price.axis_options).map(([axis, options]) => <label key={axis}>{axis.replaceAll("_", " ")}<select value={priceAxes[c.plan_id]?.[axis] ?? ""} onChange={e => setPriceAxes(old => ({ ...old, [c.plan_id]: { ...old[c.plan_id], [axis]: e.target.value } }))}><option value="">Select printed value</option>{options.map(value => <option key={value} value={value}>{value}</option>)}</select></label>)}<button disabled={busy} onClick={() => void lookupPrice(c)}>Check exact combination</button></fieldset>}{price?.citations?.length ? <details><summary>Printed chart evidence</summary>{price.citations.map((item, n) => <blockquote key={n}>{item.quote}</blockquote>)}</details> : null}</article>; })}</div>{!selected.length && <p>Select plans in the full picker to inspect their price availability.</p>}</section>}
      {screen === "coverage" && <section><p className="eyebrow">WHAT THIS DEMO CAN SHOW</p><h1>Source coverage.</h1><p>Ten-insurer demo sample; no top-ten ranking is claimed. Candidate links are not current-plan counts. Retrieved documents may still have unresolved edition applicability.</p>
        <div className="demo-table-wrap"><table><thead><tr><th>Insurer</th><th>Source acquisition</th><th>Candidate PDF links</th><th>Browser-recovered PDFs</th><th>Register entries (unverified)</th><th>Current catalogue</th></tr></thead><tbody>{coverage?.insurers.map(i => <tr key={i.id}><th>{i.name}</th><td>{i.discovery_status.replaceAll("_", " ")}</td><td>{i.candidate_document_count}</td><td>{i.browser_recovered_pdfs}</td><td>{i.register_entries ?? "Unknown"}</td><td>{i.catalogue_complete ? "Complete" : "Incomplete"}</td></tr>)}</tbody></table></div>
        <h2>Processed plan editions</h2><div className="demo-table-wrap"><table><thead><tr><th>Plan</th><th>PDFs</th><th>Pages</th><th>Sections</th><th>Map fallbacks</th><th>Models</th><th>Status</th></tr></thead><tbody>{coverage?.plans.map(p => <tr key={p.id}><th>{p.name}</th><td>{p.documents}</td><td>{p.pages}</td><td>{p.sections}</td><td>{p.map_fallbacks}</td><td>{p.models.join(", ")}</td><td>{p.status}</td></tr>)}</tbody></table></div>
      </section>}
    </main>
    {screen !== "start" && screen !== "coverage" && <aside className="demo-selection"><span>{selected.length} of 5 selected · same plan type</span><button onClick={() => setSelected([])}>Clear</button><button className="demo-primary" disabled={selected.length < 2} onClick={() => setScreen("chat")}>Compare selected plans →</button></aside>}
    <footer className="demo-footer">Local demonstration · Neutral document comparison · AI answers pass code checks, not expert review · Indicative premiums exclude tax · Policy terms, underwriting and insurer decisions apply.</footer>
    {citation && <CitationViewer citation={citation} onClose={() => setCitation(null)} />}
  </div>;
}
