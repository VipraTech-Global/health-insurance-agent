"use client";

import { createParser, type EventSourceMessage } from "eventsource-parser";
import { FormEvent, useCallback, useEffect, useMemo, useRef, useState } from "react";

import { CitationViewer, type CitationView } from "@/components/citation-viewer";
import { api } from "@/lib/api";
import type { components } from "@/lib/api-schema";

type Conversation = components["schemas"]["V2Conversation"];
type Message = components["schemas"]["V2Message"];
type Profile = components["schemas"]["CurrentProfile"];
type ProfileFact = components["schemas"]["ProfileFact"];
type ProfileRequirement = components["schemas"]["ProfileRequirement"];
type Comparison = components["schemas"]["ComparisonDetail"];
type ComparisonCitation = components["schemas"]["ComparisonCitation"];
type Catalogue = components["schemas"]["CatalogueReadiness"];
type TurnAccepted = components["schemas"]["TurnAccepted"];
type Page<T> = { next: string | null; previous: string | null; results: T[] };
type ActiveTurn = { id: string; eventUrl: string; state: string };
type ProfileEdit =
  | { kind: "fact"; item: ProfileFact }
  | { kind: "requirement"; item: ProfileRequirement };

const progressLabels: Record<string, string> = {
  queued: "Waiting for the adviser worker…",
  understanding_request: "Understanding your request…",
  checking_policies: "Checking the published reviewed policies…",
  validating_evidence: "Validating rules and exact evidence…",
};

function objectValue(value: unknown): Record<string, unknown> | null {
  return value !== null && typeof value === "object" && !Array.isArray(value)
    ? value as Record<string, unknown>
    : null;
}

const MONEY_UNIT_SUFFIX: Record<string, string> = { money_per_year: "/year", money_per_day: "/day" };

function displayValue(value: unknown): string {
  const item = objectValue(value);
  if (!item) return value === null ? "Not specified" : String(value);
  if (item.state === "unknown") return "Unknown";
  if (item.state === "not_applicable") return "Not applicable";
  if (item.state === "finite") {
    const unitKey = typeof item.unit === "string" ? item.unit : null;
    const suffix = unitKey ? MONEY_UNIT_SUFFIX[unitKey] : undefined;
    const base = [item.currency, item.value].filter(Boolean).join(" ");
    if (suffix) return `${base}${suffix}`;
    const unit = unitKey === "money" ? null : unitKey;
    return [base, unit].filter(Boolean).join(" ");
  }
  if (item.kind === "quantity") {
    return [item.currency, item.value, item.unit].filter(Boolean).join(" ");
  }
  if (item.kind === "duration") {
    const duration = objectValue(item.value);
    return duration ? [duration.value, duration.unit].filter(Boolean).join(" ") : "Unknown";
  }
  if ("value" in item) return String(item.value);
  return JSON.stringify(value);
}

function monthlyEmiLabel(criterion: string, comparisonValue: unknown): string | null {
  if (criterion !== "budget") return null;
  const item = objectValue(comparisonValue);
  if (!item || item.state !== "finite" || item.unit !== "money_per_year") return null;
  const annual = Number(item.value);
  if (!Number.isFinite(annual)) return null;
  const monthly = Math.round((annual / 12) * 100) / 100;
  return [item.currency, monthly].filter(Boolean).join(" ") + "/month";
}

function citationView(citation: ComparisonCitation): CitationView {
  const locator = objectValue(citation.locator);
  const rawBox = locator?.kind === "pdf_region" ? locator.bbox : null;
  const bbox = Array.isArray(rawBox) && rawBox.length === 4 && rawBox.every(Number.isFinite)
    ? rawBox as [number, number, number, number]
    : null;
  return {
    documentVersionId: citation.document_version_id,
    page: citation.page,
    quote: citation.quote,
    label: citation.section_label || `Policy evidence · page ${citation.page ?? "unknown"}`,
    bbox,
  };
}

async function allPages<T>(initialPath: string): Promise<T[]> {
  const rows: T[] = [];
  let path: string | null = initialPath;
  while (path) {
    const page: Page<T> = await api<Page<T>>(path);
    rows.push(...page.results);
    path = page.next;
  }
  return rows;
}

export function AdviserApp({ email, onLogout }: { email: string; onLogout: () => void }) {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [active, setActive] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [profile, setProfile] = useState<Profile | null>(null);
  const [comparisons, setComparisons] = useState<Record<string, Comparison>>({});
  const [catalogue, setCatalogue] = useState<Catalogue | null>(null);
  const [tab, setTab] = useState<"chat" | "catalogue">("chat");
  const [progress, setProgress] = useState("");
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [activeTurn, setActiveTurn] = useState<ActiveTurn | null>(null);
  const [retryableTurnId, setRetryableTurnId] = useState<string | null>(null);
  const [citation, setCitation] = useState<CitationView | null>(null);
  const [profileEdit, setProfileEdit] = useState<ProfileEdit | null>(null);
  const [busy, setBusy] = useState(false);
  const controller = useRef<AbortController | null>(null);

  const loadConversation = useCallback(async (conversationId: string) => {
    const [loadedMessages, loadedProfile] = await Promise.all([
      allPages<Message>(`/api/v2/conversations/${conversationId}/messages/`),
      api<Profile>(`/api/v2/conversations/${conversationId}/profile/`),
    ]);
    const comparisonIds = [...new Set(
      loadedMessages.map((item) => item.comparison_id).filter((id): id is string => !!id),
    )];
    const loadedComparisons = await Promise.all(
      comparisonIds.map(async (id) => [id, await api<Comparison>(`/api/v2/comparisons/${id}/`)] as const),
    );
    setMessages(loadedMessages);
    setProfile(loadedProfile);
    setComparisons(Object.fromEntries(loadedComparisons));
  }, []);

  const refreshCatalogue = useCallback(async () => {
    setCatalogue(await api<Catalogue>("/api/v2/knowledge/readiness/"));
  }, []);

  const followTurn = useCallback(async (conversationId: string, accepted: TurnAccepted) => {
    controller.current?.abort();
    const aborter = new AbortController();
    controller.current = aborter;
    const storageKey = `coverguide-v2-turn:${conversationId}`;
    const running = { id: accepted.turn_id, eventUrl: accepted.event_url, state: "queued" };
    setActiveTurn(running);
    setRetryableTurnId(null);
    setProgress("queued");
    localStorage.setItem(storageKey, JSON.stringify(running));
    let afterSequence = 0;
    let terminal = false;
    try {
      while (!terminal && !aborter.signal.aborted) {
        const join = accepted.event_url.includes("?") ? "&" : "?";
        const response = await fetch(
          `${accepted.event_url}${join}after_sequence=${afterSequence}&timeout=15`,
          { credentials: "include", cache: "no-store", signal: aborter.signal },
        );
        if (!response.ok || !response.body) throw new Error(`Event reconnect failed (${response.status}).`);
        const decoder = new TextDecoder();
        const parser = createParser({
          onEvent(event: EventSourceMessage) {
            const sequence = Number(event.id);
            if (Number.isFinite(sequence)) afterSequence = Math.max(afterSequence, sequence);
            const payload = JSON.parse(event.data) as Record<string, unknown>;
            if (event.event === "turn.started") setProgress("understanding_request");
            if (event.event === "turn.progress" && typeof payload.progress_code === "string") {
              setProgress(payload.progress_code);
            }
            if (event.event === "comparison.completed" || event.event === "clarification.required") {
              terminal = true;
              setRetryableTurnId(null);
              setNotice(event.event === "clarification.required" ? "One focused clarification is needed." : "Policy comparison validated and saved.");
            }
            if (event.event === "turn.failed") {
              terminal = true;
              setRetryableTurnId(accepted.turn_id);
              setError(`The adviser stopped safely (${String(payload.error_code || "technical_failure")}). No insurance answer was produced.`);
            }
            if (event.event === "turn.cancelled") {
              terminal = true;
              setRetryableTurnId(accepted.turn_id);
              setNotice("Turn cancelled. You can retry it without duplicating your message.");
            }
            if (event.event === "turn.stale") {
              terminal = true;
              setRetryableTurnId(accepted.turn_id);
              setError("The profile or knowledge release changed during this turn. Retry against the current state.");
            }
          },
        });
        const reader = response.body.getReader();
        while (true) {
          const { value, done } = await reader.read();
          if (done) break;
          parser.feed(decoder.decode(value, { stream: true }));
        }
      }
      if (terminal) {
        localStorage.removeItem(storageKey);
        await loadConversation(conversationId);
        await refreshCatalogue();
        setProgress("");
        setActiveTurn(null);
      }
    } catch (caught) {
      if ((caught as Error).name !== "AbortError") {
        setError(caught instanceof Error ? caught.message : "Could not reconnect to the turn.");
      }
    }
  }, [loadConversation, refreshCatalogue]);

  useEffect(() => {
    let disposed = false;
    void Promise.all([
      allPages<Conversation>("/api/v2/conversations/"),
      api<Catalogue>("/api/v2/knowledge/readiness/"),
    ]).then(([items, readiness]) => {
      if (disposed) return;
      setConversations(items);
      setCatalogue(readiness);
      setActive((current) => current || items[0] || null);
    }).catch((caught: Error) => { if (!disposed) setError(caught.message); });
    return () => { disposed = true; };
  }, []);

  useEffect(() => {
    // A pending stream belongs to its conversation. Clear its UI state when
    // moving to another conversation; the saved turn remains reconnectable.
    controller.current?.abort();
    setActiveTurn(null);
    setProgress("");
    setElapsedSeconds(0);
    setRetryableTurnId(null);
    setError("");
    setNotice("");
    if (!active) {
      setMessages([]);
      setProfile(null);
      setComparisons({});
      return;
    }
    let disposed = false;
    void loadConversation(active.id).then(() => {
      if (disposed) return;
      const saved = localStorage.getItem(`coverguide-v2-turn:${active.id}`);
      if (!saved) return;
      try {
        const value = JSON.parse(saved) as ActiveTurn;
        if (value.id && value.eventUrl) {
          void followTurn(active.id, { message_id: "", turn_id: value.id, event_url: value.eventUrl });
        }
      } catch {
        localStorage.removeItem(`coverguide-v2-turn:${active.id}`);
      }
    }).catch((caught: Error) => { if (!disposed) setError(caught.message); });
    return () => { disposed = true; controller.current?.abort(); };
  }, [active, followTurn, loadConversation]);

  async function newConversation() {
    setBusy(true);
    try {
      const item = await api<Conversation>("/api/v2/conversations/", {
        method: "POST",
        body: JSON.stringify({ title: "Insurance planning" }),
      });
      setConversations((current) => [item, ...current]);
      setActive(item);
      setTab("chat");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not start a conversation.");
    } finally {
      setBusy(false);
    }
  }

  async function sendMessage(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!active || activeTurn) return;
    const form = event.currentTarget;
    const text = new FormData(form).get("message")?.toString().trim();
    if (!text) return;
    form.reset();
    setError("");
    setNotice("");
    setMessages((current) => [...current, {
      id: crypto.randomUUID(),
      sequence: (current.at(-1)?.sequence ?? 0) + 1,
      role: "customer",
      content: text,
      origin: "text",
      submitted_at: new Date().toISOString(),
      created_at: new Date().toISOString(),
      comparison_id: null,
    }]);
    try {
      const accepted = await api<TurnAccepted>(`/api/v2/conversations/${active.id}/messages/`, {
        method: "POST",
        body: JSON.stringify({
          request_id: crypto.randomUUID(),
          text,
          ...(profile ? { expected_profile_revision: profile.revision } : {}),
        }),
      });
      await followTurn(active.id, accepted);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "The message could not be submitted.");
      await loadConversation(active.id).catch(() => undefined);
    }
  }

  async function stopTurn() {
    if (!activeTurn) return;
    try {
      await api(`/api/v2/turns/${activeTurn.id}/cancel/`, { method: "POST" });
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not request cancellation.");
    }
  }

  // Browser-observed elapsed time for the current progress stage, not a server-reported
  // duration. Resets on stage change and on turn change (covers a new turn landing on the
  // same stage a previous turn ended on); stops once there is no active turn.
  useEffect(() => {
    if (!activeTurn || !progress) {
      setElapsedSeconds(0);
      return;
    }
    const start = performance.now();
    setElapsedSeconds(0);
    const id = window.setInterval(() => {
      setElapsedSeconds(Math.floor((performance.now() - start) / 1000));
    }, 1000);
    return () => window.clearInterval(id);
  }, [progress, activeTurn?.id]);

  async function retryTurn() {
    if (!active || !retryableTurnId) return;
    setError("");
    try {
      const accepted = await api<TurnAccepted>(`/api/v2/turns/${retryableTurnId}/retry/`, {
        method: "POST",
      });
      await followTurn(active.id, accepted);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not retry the turn.");
    }
  }

  async function reconnectTurn() {
    if (!active || !activeTurn) return;
    setError("");
    await followTurn(active.id, {
      message_id: "",
      turn_id: activeTurn.id,
      event_url: activeTurn.eventUrl,
    });
  }

  async function saveProfileEdit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!active || !profile || !profileEdit) return;
    const raw = new FormData(event.currentTarget).get("value")?.toString() || "null";
    setBusy(true);
    try {
      const value: unknown = JSON.parse(raw);
      const facts = profileEdit.kind === "fact" ? [{
        logical_key: profileEdit.item.logical_key,
        fact_type: profileEdit.item.fact_type,
        subject_person_id: profileEdit.item.subject_person_id,
        value,
        status: "confirmed",
      }] : [];
      const requirements = profileEdit.kind === "requirement" ? [{
        logical_key: profileEdit.item.logical_key,
        criterion: profileEdit.item.criterion,
        operator: profileEdit.item.operator,
        target_value: value,
        priority: profileEdit.item.priority,
        scope: profileEdit.item.scope,
        subject_person_id: profileEdit.item.subject_person_id,
        status: "confirmed",
      }] : [];
      const updated = await api<Profile>(`/api/v2/conversations/${active.id}/profile/`, {
        method: "PATCH",
        body: JSON.stringify({
          expected_revision: profile.revision,
          correction_text: `Customer corrected ${profileEdit.kind} ${profileEdit.item.logical_key}.`,
          facts,
          requirements,
        }),
      });
      setProfile(updated);
      setProfileEdit(null);
      setNotice("Correction saved as a new profile revision.");
    } catch (caught) {
      setError(caught instanceof SyntaxError ? "Enter a valid JSON value." : caught instanceof Error ? caught.message : "Could not save the correction.");
    } finally {
      setBusy(false);
    }
  }

  async function uploadQuote(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!active) return;
    const form = event.currentTarget;
    const data = new FormData(form);
    if (!(data.get("file") instanceof File) || !(data.get("file") as File).size) return;
    data.set("kind", "quote");
    setBusy(true);
    try {
      const accepted = await api<components["schemas"]["UploadAccepted"]>(
        `/api/v2/conversations/${active.id}/uploads/`,
        { method: "POST", body: data },
      );
      form.reset();
      setNotice(`Quote received. Document job ${accepted.job_id.slice(0, 8)} is processing.`);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not upload the quote.");
    } finally {
      setBusy(false);
    }
  }

  const latestComparison = useMemo(() => {
    const id = [...messages].reverse().find((item) => item.comparison_id)?.comparison_id;
    return id ? comparisons[id] : undefined;
  }, [messages, comparisons]);

  return (
    <div className="app-shell">
      <aside className="rail">
        <div className="brand"><span className="mark small">CG</span><div><strong>CoverGuide</strong><small>Evidence-grounded policy comparison</small></div></div>
        <button className="new-chat" onClick={newConversation} disabled={busy}>＋ New conversation</button>
        <nav>
          <p className="nav-label">CONVERSATIONS</p>
          {conversations.map((item) => (
            <button key={item.id} className={active?.id === item.id && tab === "chat" ? "nav-item active" : "nav-item"} onClick={() => { setActive(item); setTab("chat"); }}>
              {item.title || "Insurance planning"}
            </button>
          ))}
          <p className="nav-label">KNOWLEDGE</p>
          <button className={tab === "catalogue" ? "nav-item active" : "nav-item"} onClick={() => setTab("catalogue")}>Knowledge readiness</button>
        </nav>
        <div className="user-row"><span>{email.slice(0, 1).toUpperCase()}</span><div><strong>{email}</strong><button onClick={onLogout}>Sign out</button></div></div>
      </aside>
      <main className="workspace">
        <div className="alpha-warning" role="status">
          <strong>Development alpha · incomplete comparison</strong>
          <span>{catalogue?.warning || "Missing policy categories are shown as unknown and are never treated as coverage."}</span>
        </div>
        {tab === "catalogue" ? <CataloguePanel catalogue={catalogue} /> : !active ? (
          <div className="empty"><span>✦</span><h1>Start with your own words.</h1><p>No profile form is required. Tell CoverGuide who needs cover, what matters, or what is uncertain.</p><button className="primary" onClick={newConversation}>Start a conversation</button></div>
        ) : (
          <>
            <header className="topbar"><div><p className="eyebrow">POLICY COMPARISON</p><h2>{active.title || "Insurance planning"}</h2></div><span className={catalogue?.ready ? "ready-badge" : "blocked-badge"}>{catalogue?.ready ? `${catalogue.catalogue_limit} products ready` : "Knowledge gated"}</span></header>
            <div className="conversation-layout">
              <section className="chat-panel">
                <div className="catalogue-limit">{catalogue?.comparison_label || "Only published reviewed products are compared."} Premiums and underwriting remain conditional until supported by your quote or schedule.</div>
                <div className="messages">
                  {messages.length === 0 && <div className="welcome"><span>✦</span><h1>What would a good policy need to do for you?</h1><p>Write naturally. I’ll keep uncertain details unresolved and ask one focused question when needed.</p></div>}
                  {messages.map((message) => {
                    const comparison = message.comparison_id ? comparisons[message.comparison_id] : undefined;
                    const isClarification = comparison?.outcome === "clarification_required";
                    return (
                      <article key={message.id} className={`message ${message.role === "customer" ? "user" : "assistant"}`}>
                        <div className="message-label">{message.role === "customer" ? "You" : "CoverGuide"}</div>
                        {!isClarification && <p>{message.content}</p>}
                        {comparison && <ComparisonPanel comparison={comparison} onCitation={setCitation} />}
                      </article>
                    );
                  })}
                </div>
                {error && <div className="error-banner" role="alert">{error}<div><button onClick={() => setError("")}>Dismiss</button>{activeTurn ? <button onClick={reconnectTurn}>Reconnect</button> : retryableTurnId ? <button onClick={retryTurn}>Retry safely</button> : null}</div></div>}
                {notice && <div className="notice-banner">{notice}<button onClick={() => setNotice("")}>Dismiss</button></div>}
                {progress && <div className="processing"><i />{progressLabels[progress] || progress}{elapsedSeconds >= 3 && ` (${elapsedSeconds}s)`}{activeTurn && <button onClick={stopTurn}>Cancel</button>}</div>}
                <form className="composer" onSubmit={sendMessage}>
                  <textarea name="message" rows={2} placeholder="Ask a policy question or describe who needs cover…" aria-label="Message CoverGuide" />
                  <div><span>Facts, requirements and uncertainty are saved with their source message.</span><button className="send" disabled={!!activeTurn}>Send →</button></div>
                </form>
              </section>
              <aside className="profile-panel">
                <div className="profile-heading"><div><p className="eyebrow">CURRENT PROFILE</p><h3>People & priorities</h3></div><span className="revision-badge">r{profile?.revision ?? "–"}</span></div>
                <ProfilePanel profile={profile} onEdit={setProfileEdit} />
                <form className="quote-upload" onSubmit={uploadQuote}><p className="eyebrow">OPTIONAL QUOTE</p><label>Confirm premium and selected options<input name="file" type="file" accept="application/pdf" disabled={busy} /></label><button className="secondary" disabled={busy}>Upload PDF</button></form>
                {latestComparison?.information_needs.length ? <div className="open-needs"><p className="eyebrow">STILL NEEDED</p>{latestComparison.information_needs.map((need) => <p key={need.id}>{need.reason}</p>)}</div> : null}
              </aside>
            </div>
          </>
        )}
        {citation && <CitationViewer citation={citation} onClose={() => setCitation(null)} />}
        {profileEdit && <ProfileEditDialog edit={profileEdit} busy={busy} onSubmit={saveProfileEdit} onClose={() => setProfileEdit(null)} />}
      </main>
    </div>
  );
}

function ProfilePanel({ profile, onEdit }: { profile: Profile | null; onEdit: (edit: ProfileEdit) => void }) {
  if (!profile) return <p className="muted">Loading the current structured profile…</p>;
  const people = [{ id: null, display_name: "Household / purchase" }, ...profile.people];
  return <div className="profile-groups">{people.map((person) => {
    const facts = profile.facts.filter((item) => item.subject_person_id === person.id);
    const requirements = profile.requirements.filter((item) => item.subject_person_id === person.id);
    if (!facts.length && !requirements.length && person.id !== null) return null;
    return <section key={person.id || "purchase"} className="profile-group"><h4>{person.display_name}</h4>{!facts.length && !requirements.length ? <p className="muted">Details will appear as the conversation develops.</p> : null}{facts.map((fact) => <div className="profile-row" key={fact.id}><div><small>{fact.fact_type.replaceAll("_", " ")}</small><strong>{displayValue(fact.value)}</strong><em>{fact.status}</em></div><button onClick={() => onEdit({ kind: "fact", item: fact })}>Edit</button></div>)}{requirements.map((requirement) => <div className="profile-row requirement-row" key={requirement.id}><div><small>{requirement.criterion.replaceAll("_", " ")}</small><strong>{displayValue(requirement.target_value)}</strong><em>{requirement.priority} · {requirement.status}</em></div><button onClick={() => onEdit({ kind: "requirement", item: requirement })}>Edit</button></div>)}</section>;
  })}</div>;
}

function ComparisonPanel({ comparison, onCitation }: { comparison: Comparison; onCitation: (citation: CitationView) => void }) {
  const showProducts = comparison.outcome !== "clarification_required";
  return <div className="comparison-detail">
    <div className="comparison-heading"><div><p className="eyebrow">POLICY COMPARISON</p><h3>Policy comparison</h3></div><span>{comparison.comparison_label}</span></div>
    <p className="comparison-framing">CoverGuide compares the reviewed products against the criteria you shared. It does not choose a policy; the decision is yours.</p>
    {showProducts ? <div className="compared-product-grid">{comparison.products.map((product) => <section key={product.id} className="compared-product">
      <div className="product-identity"><div><h4>{product.product}</h4><p>{product.insurer}</p></div><span>{product.variant}</span></div>
      <code>{product.uin || "UIN not verified"}</code>
      <div className="criterion-matrix" role="table" aria-label={`${product.product} criteria`}>
        {product.criteria.map((criterion) => <div key={criterion.id} className={`criterion-row match-${criterion.outcome}`} role="row"><span role="cell">{criterion.criterion.replaceAll("_", " ")}</span><b role="cell">{criterion.outcome.replaceAll("_", " ")}</b>{criterion.comparison_value != null ? <em role="cell">{displayValue(criterion.comparison_value)}</em> : null}{monthlyEmiLabel(criterion.criterion, criterion.comparison_value) ? <em className="derived-emi" role="cell">≈ {monthlyEmiLabel(criterion.criterion, criterion.comparison_value)} (derived, not an insurer-published rate)</em> : null}</div>)}
      </div>
      <div className="product-evidence-section"><b>Evidence gaps and unknowns</b>{product.evidence_gaps.length ? <ul>{product.evidence_gaps.map((gap) => <li key={`${gap.requirement_id}-${gap.criterion}`}>{gap.criterion.replaceAll("_", " ")} · {gap.outcome.replaceAll("_", " ")}</li>)}</ul> : <p>None identified for the shared criteria.</p>}</div>
      <div className="product-evidence-section"><b>Applicable restrictions</b>{product.restrictions.length ? product.restrictions.map((restriction) => <div key={restriction.statement_id} className="restriction"><p>{restriction.text}</p><div className="claim-sources">{restriction.citations.map((source, index) => <button type="button" className="citation-button" key={source.id} onClick={() => onCitation(citationView(source))}>Restriction source {index + 1} · p.{source.page ?? "–"}</button>)}</div></div>) : <p>No applicable restriction was established from the published evidence.</p>}</div>
      <div className="product-evidence-section"><b>Policy evidence</b>{product.evidence.length ? <div className="claim-sources">{product.evidence.map((source, index) => <button type="button" className="citation-button" key={`${source.id}-${index}`} onClick={() => onCitation(citationView(source))}>Evidence {index + 1} · p.{source.page ?? "–"}</button>)}</div> : <p>No cited product statement is available.</p>}</div>
    </section>)}</div> : null}
    <div className="comparison-statements">{comparison.statements.map((statement) => <div key={statement.id} className={statement.critical ? "critical-statement" : ""}><p>{statement.text}</p>{statement.citations.length ? <div className="claim-sources">{statement.citations.map((source, index) => <button type="button" className="citation-button" key={source.id} onClick={() => onCitation(citationView(source))}>Source {index + 1} · p.{source.page ?? "–"}</button>)}</div> : null}</div>)}</div>
  </div>;
}

function ProfileEditDialog({ edit, busy, onSubmit, onClose }: { edit: ProfileEdit; busy: boolean; onSubmit: (event: FormEvent<HTMLFormElement>) => void; onClose: () => void }) {
  const value = edit.kind === "fact" ? edit.item.value : edit.item.target_value;
  const label = edit.kind === "fact" ? edit.item.fact_type : edit.item.criterion;
  return <div className="modal-backdrop" role="presentation"><section className="edit-dialog" role="dialog" aria-modal="true" aria-label={`Correct ${label}`}><p className="eyebrow">PROFILE CORRECTION</p><h3>{label.replaceAll("_", " ")}</h3><p>Enter the complete typed JSON value. The old revision remains in history and cannot override this correction.</p><form onSubmit={onSubmit}><textarea name="value" rows={8} defaultValue={JSON.stringify(value, null, 2)} autoFocus /><div><button type="button" className="secondary" onClick={onClose}>Cancel</button><button className="primary" disabled={busy}>Save correction</button></div></form></section></div>;
}

function CataloguePanel({ catalogue }: { catalogue: Catalogue | null }) {
  return <section className="coverage"><p className="eyebrow">PUBLISHED KNOWLEDGE RELEASE</p><h1>What CoverGuide can safely compare</h1><p className="lede">A product becomes available after its exact identity, agreed supported rules, evidence, embeddings and publication gate pass. Uncovered categories remain unknown.</p>{catalogue && <div className="catalogue-limit">{catalogue.comparison_label}</div>}<div className={`release-status ${catalogue?.ready ? "ready" : "blocked"}`}><strong>{catalogue?.ready ? "Development alpha published" : "Not ready for live advice"}</strong><span>{catalogue?.release ? `${catalogue.release.label.replaceAll("_", " ")} · Release ${catalogue.release.number} · ${new Date(catalogue.release.published_at || "").toLocaleString()}` : catalogue?.blocking_reason || "No release is published."}</span></div><div className="product-inventory">{catalogue?.products.map((product) => <article key={product.id}><div><span className={product.included_in_current_release ? "status-dot ready" : "status-dot"} /><div><h3>{product.name}</h3><p>{product.insurer}</p></div></div><code>{product.uin || "UIN not verified"}</code><dl><div><dt>Documents</dt><dd>{product.document_count}</dd></div><div><dt>Verified rules</dt><dd>{product.rule_count}</dd></div><div><dt>Material issues</dt><dd>{product.unresolved_material_jobs}</dd></div></dl><div className="category-summary"><b>Covered</b><span>{product.covered_inventory_categories.join(", ") || "None yet"}</span><b>Unknown</b><span>{product.missing_inventory_categories.join(", ") || "None"}</span></div><small>{product.included_in_current_release ? "included in demo" : product.publication_status.replaceAll("_", " ")}</small></article>)}</div>{!catalogue && <p>Loading readiness…</p>}</section>;
}
