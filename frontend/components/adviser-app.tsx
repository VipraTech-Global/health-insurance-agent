"use client";

import { createParser, type EventSourceMessage } from "eventsource-parser";
import { FormEvent, useEffect, useRef, useState } from "react";
import { api, ensureCsrf } from "@/lib/api";
import { AISettings } from "@/components/ai-settings";
import { CitationViewer } from "@/components/citation-viewer";

type Conversation = { id: string; title: string; profile_revision: number };
type Claim = { id: string; text: string; citations: Citation[] };
type Answer = { id: string; blocks: { type: string; text?: string; patch?: Record<string, string>; expected_revision?: number }[]; claims: Claim[]; verification_status: string };
type Message = { id: string; role: "user" | "assistant"; content: string; origin: string; answer?: Answer | null };
type Profile = { revision: number; data: Record<string, string>; confirmed_at: string | null };
type Citation = { documentId: string; page: number; quote: string; label: string; rectangles: [number, number, number, number][] };
type Coverage = { total_discovered: number; active_for_recommendation: number; active_for_test: number; counts: Record<string, number>; last_successful_source_check: string | null; sample_pending_evidence: (Citation & { reviewState?: string }) | null };

const profileFields = [
  ["members", "Who needs cover?", "e.g. Me (32), spouse (30), child (4)"],
  ["location", "Location", "City, state and PIN if known"],
  ["existing_cover", "Existing cover", "Employer or personal policy; or none"],
  ["budget", "Annual budget", "Amount or not sure"],
  ["medical_information", "Medical conditions", "Include anything relevant; or unknown"],
  ["priorities", "Must-haves", "Hospitals, maternity, room type, other needs"],
];

export function AdviserApp({ email, isAdmin, onLogout }: { email: string; isAdmin: boolean; onLogout: () => void }) {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [active, setActive] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [profile, setProfile] = useState<Profile | null>(null);
  const [coverage, setCoverage] = useState<Coverage | null>(null);
  const [tab, setTab] = useState<"chat" | "coverage" | "ai">("chat");
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const [activeTurnId, setActiveTurnId] = useState("");
  const [citation, setCitation] = useState<Citation | null>(null);
  const [profileBusy, setProfileBusy] = useState(false);
  const controller = useRef<AbortController | null>(null);

  async function loadConversations() {
    const data = await api<{ results: Conversation[] }>("/api/v1/conversations/");
    setConversations(data.results);
    if (!active && data.results[0]) setActive(data.results[0]);
  }
  useEffect(() => { void loadConversations(); void api<Coverage>("/api/v1/catalogue/coverage/").then(setCoverage); }, []);
  useEffect(() => {
    if (!active) { setMessages([]); setProfile(null); return; }
    setProfile(null);
    let disposed = false;
    void Promise.all([
      api<{ results: Message[] }>(`/api/v1/conversations/${active.id}/messages/`),
      api<Profile>(`/api/v1/conversations/${active.id}/profile/`),
    ]).then(([m, p]) => { if (!disposed) { setMessages(m.results); setProfile(p); } }).catch((caught: Error) => { if (!disposed) setError(caught.message); });
    return () => { disposed = true; };
  }, [active?.id]);

  async function newConversation() {
    const item = await api<Conversation>("/api/v1/conversations/", { method: "POST", body: JSON.stringify({ title: "Insurance planning" }) });
    setConversations([item, ...conversations]); setActive(item); setTab("chat");
  }

  async function saveProfile(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); if (!active || !profile) return;
    setProfileBusy(true);
    const values = Object.fromEntries(new FormData(event.currentTarget).entries());
    try {
      const updated = await api<Profile>(`/api/v1/conversations/${active.id}/profile/`, { method: "PATCH", body: JSON.stringify({ expected_revision: profile.revision, patch: values }) });
      setProfile(updated);
    } catch (caught) { setError(caught instanceof Error ? caught.message : "Could not save profile"); }
    finally { setProfileBusy(false); }
  }

  async function confirmProfile() {
    if (!active || !profile) return;
    setProfileBusy(true);
    try {
      setProfile(await api<Profile>(`/api/v1/conversations/${active.id}/profile/confirm/`, { method: "POST", body: JSON.stringify({ expected_revision: profile.revision }) }));
    } catch (caught) { setError(caught instanceof Error ? caught.message : "Could not confirm profile"); }
    finally { setProfileBusy(false); }
  }

  async function sendTurn(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); if (!active || !profile) return;
    const submitter = (event.nativeEvent as SubmitEvent)
      .submitter as HTMLButtonElement | null;
    const operation = submitter?.value || "chat";
    const form = event.currentTarget; const input = new FormData(form).get("message")?.toString().trim(); if (!input) return;
    form.reset(); setError(""); setStatus("Connecting…");
    const optimistic: Message = { id: crypto.randomUUID(), role: "user", content: input, origin: "text" };
    setMessages((current) => [...current, optimistic]);
    controller.current = new AbortController();
    try {
      const csrf = await ensureCsrf();
      const response = await fetch(`/api/v1/conversations/${active.id}/turns/`, { method: "POST", credentials: "include", signal: controller.current.signal, headers: { "Content-Type": "application/json", "X-CSRFToken": csrf }, body: JSON.stringify({ request_id: crypto.randomUUID(), text: input, operation, expected_profile_revision: profile.revision }) });
      if (!response.ok || !response.body) { const body = await response.json(); throw new Error(body.error?.message ?? "Turn failed"); }
      const decoder = new TextDecoder();
      const parser = createParser({ onEvent(eventMessage: EventSourceMessage) {
        const payload = JSON.parse(eventMessage.data);
        if (eventMessage.event === "accepted") setActiveTurnId(payload.turn_id);
        if (eventMessage.event === "progress") setStatus(payload.stage);
        if (eventMessage.event === "result") {
          const answer = payload.answer as Answer | undefined;
          const text = answer?.blocks?.find((block) => block.type === "text")?.text;
          if (text && answer) setMessages((current) => [...current, { id: answer.id, role: "assistant", content: text, origin: answer.verification_status, answer }]);
          setStatus("");
          setActiveTurnId("");
        }
        if (eventMessage.event === "error") { setError(payload.message); setStatus(""); setActiveTurnId(""); }
      }});
      const reader = response.body.getReader();
      while (true) { const { value, done } = await reader.read(); if (done) break; parser.feed(decoder.decode(value, { stream: true })); }
    } catch (caught) {
      if ((caught as Error).name !== "AbortError") setError(caught instanceof Error ? caught.message : "Turn failed");
      setStatus("");
      setActiveTurnId("");
    }
  }

  async function stopTurn() {
    if (activeTurnId) {
      await api(`/api/v1/turns/${activeTurnId}/cancel/`, {
        method: "POST",
        body: "{}",
      }).catch(() => undefined);
    }
    controller.current?.abort();
    setStatus("");
    setActiveTurnId("");
  }

  return <div className="app-shell">
    <aside className="rail">
      <div className="brand"><span className="mark small">CG</span><div><strong>CoverGuide</strong><small>Local adviser pilot</small></div></div>
      <button className="new-chat" onClick={newConversation}>＋ New conversation</button>
      <nav>
        <p className="nav-label">CONVERSATIONS</p>
        {conversations.map((item) => <button key={item.id} className={active?.id === item.id && tab === "chat" ? "nav-item active" : "nav-item"} onClick={() => { setActive(item); setTab("chat"); }}>{item.title}</button>)}
        <p className="nav-label">SETTINGS</p><button className={tab === "ai" ? "nav-item active" : "nav-item"} onClick={() => setTab("ai")}>AI settings</button>
        <p className="nav-label">CORPUS</p>
        <button className={tab === "coverage" ? "nav-item active" : "nav-item"} onClick={() => setTab("coverage")}>Coverage & review</button>
      </nav>
      <div className="user-row"><span>{email.slice(0, 1).toUpperCase()}</span><div><strong>{email}</strong><button onClick={onLogout}>Sign out</button></div></div>
    </aside>
    <main className="workspace">
      {tab === "ai" ? <AISettings isAdmin={isAdmin} /> : tab === "coverage" ? <CoveragePanel coverage={coverage} onOpen={setCitation} /> : !active ? <EmptyState onCreate={newConversation} /> : <>
        <header className="topbar"><div><p className="eyebrow">ADVISORY CONVERSATION</p><h2>{active.title}</h2></div><span className="pilot-badge">Local pilot</span></header>
        <div className="conversation-layout">
          <section className="chat-panel">
            <div className="messages">
              {messages.length === 0 && <div className="welcome"><span>✦</span><h1>Let’s map the cover you need.</h1><p>I’ll ask only what affects the decision. You can say “not sure” at any point.</p></div>}
              {messages.map((message) => <article key={message.id} className={`message ${message.role}`}><div className="message-label">{message.role === "user" ? "You" : "CoverGuide"}{message.origin === "controlled_template" && <em>verified template</em>}</div><p>{message.answer ? message.answer.blocks.find((block) => block.type === "text")?.text : message.content}</p>{message.answer?.blocks.filter((block) => block.type === "profile_suggestion" && block.patch).map((block, index) => <div key={index} className="profile-suggestion"><dl>{Object.entries(block.patch!).map(([key, value]) => <div key={key}><dt>{profileFields.find(([field]) => field === key)?.[1] ?? key}</dt><dd>{value}</dd></div>)}</dl><button className="secondary" disabled={profileBusy || profile?.revision !== block.expected_revision} onClick={async () => { if (!active) return; setProfileBusy(true); try { setProfile(await api<Profile>(`/api/v1/conversations/${active.id}/profile/`, { method: "PATCH", body: JSON.stringify({ expected_revision: block.expected_revision, patch: block.patch }) })); } catch (caught) { setError(caught instanceof Error ? caught.message : "Could not apply details"); } finally { setProfileBusy(false); } }}>Add these details to my profile</button></div>)}{message.answer?.claims.map((claim) => <div className="answer-claim" key={claim.id}><p>{claim.text}</p><div className="claim-sources">{claim.citations.map((source, index) => <button type="button" className="citation-button" key={`${source.documentId}-${source.page}-${index}`} onClick={() => setCitation(source)}>Open source {index + 1}</button>)}</div></div>)}</article>)}
            </div>
            {error && <div className="error-banner" role="alert">{error}<button onClick={() => setError("")}>Dismiss</button></div>}
            {status && <div className="processing"><i />{status}<button onClick={stopTurn}>Stop</button></div>}
            <form className="composer" onSubmit={sendTurn}><textarea name="message" rows={2} placeholder="Ask a policy question or tell me about your needs…"/><div><span>Enter details in your own words</span><div className="composer-actions"><button className="recommend" name="operation" value="recommend" disabled={!!status || !profile}>Check recommendations</button><button className="send" name="operation" value="chat" disabled={!!status || !profile}>Send →</button></div></div></form>
          </section>
          <aside className="profile-panel"><div className="profile-heading"><div><p className="eyebrow">INSURANCE PROFILE</p><h3>Your details</h3></div><span className={profile?.confirmed_at ? "confirmed" : "pending"}>{profile?.confirmed_at ? "Confirmed" : "Draft"}</span></div>
            {profile && <form key={profile.revision} onSubmit={saveProfile}>{profileFields.map(([key, label, placeholder]) => <label key={key}>{label}<input name={key} defaultValue={profile.data[key] ?? ""} placeholder={placeholder} disabled={profileBusy} /></label>)}<button className="secondary" disabled={profileBusy}>Save changes</button>{!profile.confirmed_at && <button type="button" className="primary" onClick={confirmProfile} disabled={profileBusy}>Confirm profile</button>}<small>Revision {profile.revision}. Changes create a new immutable revision.</small></form>}
          </aside>
        </div>
      </>}
      {citation && <CitationViewer citation={citation} onClose={() => setCitation(null)} />}
    </main>
  </div>;
}

function EmptyState({ onCreate }: { onCreate: () => void }) { return <div className="empty"><span>✦</span><h1>Start an evidence-first conversation</h1><p>Your profile and every advisory answer are versioned for traceability.</p><button className="primary" onClick={onCreate}>Start a conversation</button></div>; }

function CoveragePanel({ coverage, onOpen }: { coverage: Coverage | null; onOpen: (citation: Citation) => void }) {
  const counts = coverage?.counts ?? {};
  const active = (coverage?.active_for_test ?? 0) > 0;
  return <section className="coverage"><p className="eyebrow">CORPUS READINESS</p><h1>Catalogue coverage</h1><p className="lede">Inventory and recommendation readiness are reported separately. A discovered listing is never treated as verified by default.</p><div className="metric-grid"><div><strong>{coverage?.total_discovered ?? 0}</strong><span>Discovered</span></div><div><strong>{coverage?.active_for_test ?? 0}</strong><span>Active for test</span></div><div><strong>{counts.awaiting_review ?? 0}</strong><span>Awaiting review</span></div><div className="accent"><strong>{coverage?.active_for_recommendation ?? 0}</strong><span>Recommendable</span></div></div><div className="notice"><b>{active ? "One-plan test corpus active" : "Recommendation corpus unavailable"}</b><p>{active ? "Care Supreme is enabled for evidence-backed local testing. It remains awaiting review for a personalised recommendation, along with the other catalogue listings." : "No plan will be recommended until its version, decision-critical facts, and exact source evidence have passed review."}</p></div>{coverage?.sample_pending_evidence && <div className="evidence-proof"><div><span>{coverage.sample_pending_evidence.reviewState === "verified" ? "Active evidence proof" : "Pending extraction proof"}</span><strong>{coverage.sample_pending_evidence.label}</strong><p>{coverage.sample_pending_evidence.quote}</p></div><button className="secondary" onClick={() => onOpen(coverage.sample_pending_evidence!)}>Open exact source</button></div>}<p className="updated">Last successful source check: {coverage?.last_successful_source_check ? new Date(coverage.last_successful_source_check).toLocaleString() : "None recorded"}</p></section>;
}
