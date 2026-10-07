"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import { finished, type Chat, type Message, type OpenSource, type Question, type Summary } from "@/lib/chat-types";
import { CitationViewer, type CitationView } from "./citation-viewer";
import { ConversationSidebar } from "./conversation-sidebar";
import { MessageView } from "./message";

const message = (e: unknown, fallback: string) => (e instanceof Error ? e.message : fallback);

/** Older transcripts have no blocks; attach a still-tracked question to the last reply. */
function withBlocks(chat: Chat): Message[] {
  const transcript = chat.state.transcript.map(m => ({ ...m }));
  const id = chat.state.question_id;
  if (id && !transcript.some(m => m.blocks?.some(b => b.type === "question" && b.question_id === id))) {
    const last = transcript.findLast(m => m.role === "assistant");
    if (last) last.blocks = [...(last.blocks ?? []), { type: "question", question_id: id }];
  }
  return transcript;
}

export function ChatApp({ onSignedOut }: { onSignedOut: () => Promise<void> }) {
  const [chat, setChat] = useState<Chat | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [questions, setQuestions] = useState<Record<string, Question>>({});
  const [conversations, setConversations] = useState<Summary[]>([]);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [source, setSource] = useState<CitationView | null>(null);
  const [drawer, setDrawer] = useState(false);
  const events = useRef<EventSource | null>(null);
  const receipt = useRef<{ text: string; revision: number; request_id: string } | null>(null);
  const bottom = useRef<HTMLDivElement>(null);

  const refreshList = useCallback(() => api<Summary[]>("/api/v2/demo/conversations/").then(setConversations).catch(() => undefined), []);
  const accept = useCallback((q: Question) => {
    setQuestions(old => ({ ...old, [q.id]: q }));
    if (finished(q)) events.current?.close();
  }, []);

  const stream = useCallback((id: string) => {
    events.current?.close();
    const es = new EventSource(`/api/v2/demo/questions/${id}/events/`);
    events.current = es;
    es.onmessage = event => { if (events.current === es) accept(JSON.parse(event.data) as Question); };
    es.onerror = () => {
      es.close();
      void api<Question>(`/api/v2/demo/questions/${id}/`)
        .then(q => { if (events.current === es) { accept(q); if (!finished(q)) setError("Live updates paused. Reopen this conversation to check progress."); } })
        .catch(e => setError(message(e, "Could not recover the comparison")));
    };
  }, [accept]);

  const show = useCallback((data: Chat) => {
    events.current?.close();
    receipt.current = null;
    setChat(data);
    setMessages(withBlocks(data));
    setSource(null);
    setDrawer(false);
    window.history.replaceState(null, "", `?conversation=${data.id}`);
    const ids = new Set(data.state.transcript.flatMap(m => (m.blocks ?? []).flatMap(b => (b.type === "question" ? [b.question_id] : []))));
    if (data.state.question_id) ids.add(data.state.question_id);
    for (const id of ids) {
      void api<Question>(`/api/v2/demo/questions/${id}/`).then(q => {
        accept(q);
        if (id === data.state.question_id && !finished(q)) stream(id);
      }).catch(() => undefined);
    }
  }, [accept, stream]);

  const begin = useCallback(async () => {
    setBusy(true); setError("");
    try { show(await api<Chat>("/api/v2/demo/conversations/", { method: "POST" })); setText(""); }
    catch (e) { setError(message(e, "Could not start a chat")); }
    finally { setBusy(false); }
  }, [show]);

  async function open(id: string) {
    setError("");
    try { show(await api<Chat>(`/api/v2/demo/conversations/${id}/`)); }
    catch (e) { setError(message(e, "Conversation unavailable")); }
  }

  useEffect(() => {
    const id = new URLSearchParams(window.location.search).get("conversation");
    void refreshList();
    if (id) void api<Chat>(`/api/v2/demo/conversations/${id}/`).then(show).catch(() => void begin());
    else void begin();
    return () => events.current?.close();
  }, [begin, refreshList, show]);

  useEffect(() => { bottom.current?.scrollIntoView({ block: "end" }); }, [messages, questions]);

  const answering = Boolean(chat?.state.question_id && !finished(questions[chat.state.question_id]));
  const stopped = chat?.state.stage === "stopped";

  async function send(picked?: string) {
    const value = (picked ?? text).trim();
    if (!chat || busy || answering || !value || stopped) return;
    setBusy(true); setError("");
    const request = receipt.current?.text === value && receipt.current.revision === chat.state.revision
      ? receipt.current : { text: value, revision: chat.state.revision, request_id: crypto.randomUUID() };
    receipt.current = request;
    setMessages(old => [...old, { role: "customer", text: value }]);
    if (!picked) setText("");
    try {
      const data = await api<Chat>(`/api/v2/demo/conversations/${chat.id}/`, { method: "POST", body: JSON.stringify(request) });
      receipt.current = null;
      setChat(data);
      setMessages(withBlocks(data));
      if (data.state.question_id && data.state.question_id !== chat.state.question_id) stream(data.state.question_id);
      void refreshList();
    } catch (e) {
      setMessages(old => old.slice(0, -1));
      if (!picked) setText(value);
      setError(message(e, "Message unavailable"));
    } finally { setBusy(false); }
  }

  async function cancel() {
    const id = chat?.state.question_id;
    if (!id) return;
    try {
      await api(`/api/v2/demo/questions/${id}/cancel/`, { method: "POST" });
      events.current?.close();
      accept(await api<Question>(`/api/v2/demo/questions/${id}/`));
    } catch (e) { setError(message(e, "Could not stop the answer")); }
  }

  const onSource: OpenSource = (load, label) => {
    setError("");
    load()
      .then(a => setSource({ documentVersionId: a.document_id, page: a.page, quote: a.quote, label: `${label} · page ${a.page}`, bbox: null, boxes: a.boxes, pdfUrl: a.pdf_url }))
      .catch(e => setError(message(e, "Source unavailable")));
  };

  return (
    <div className={`chat-shell${source ? " with-source" : ""}${drawer ? " drawer-open" : ""}`}>
      <button type="button" className="drawer-toggle" aria-label="Show conversations" onClick={() => setDrawer(!drawer)}>☰</button>
      {drawer && <div className="scrim" aria-hidden onClick={() => setDrawer(false)} />}
      <ConversationSidebar
        conversations={conversations} current={chat?.id} collapsed={Boolean(source)} busy={busy}
        onNew={() => void begin()} onOpen={id => void open(id)}
        onSignOut={() => void api("/api/v1/auth/logout/", { method: "POST" }).then(onSignedOut)}
        onErase={() => void api("/api/v1/account/", { method: "DELETE" }).then(onSignedOut)}
      />
      <main className="chat">
        <div className="transcript" aria-live="polite">
          {!chat && !error && <p className="muted center">Starting a conversation…</p>}
          {messages.map((m, i) => (
            <MessageView
              key={i} message={m} cards={chat?.cards ?? []} questions={questions} onSource={onSource}
              onPick={i === messages.length - 1 && !busy && !answering && !stopped ? value => void send(value) : undefined}
            />
          ))}
          {busy && chat && <div className="msg assistant"><p className="muted typing">Thinking…</p></div>}
          {stopped && <div className="ended"><p>This conversation has ended.</p><button type="button" onClick={() => void begin()}>Start a new chat</button></div>}
          <div ref={bottom} />
        </div>
        {error && <p role="alert" className="chat-error">{error}</p>}
        {!stopped && (
          <form className="composer" onSubmit={e => { e.preventDefault(); void send(); }}>
            <div className="composer-box">
              <textarea
                aria-label="Message CoverGuide" rows={1} value={text} placeholder="Tell me what cover you need…"
                onChange={e => setText(e.target.value)}
                onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) { e.preventDefault(); void send(); } }}
              />
              {answering
                ? <button type="button" className="send stop" onClick={() => void cancel()} aria-label="Stop answering">■</button>
                : <button type="submit" className="send" disabled={busy || !text.trim() || !chat} aria-label="Send message">↑</button>}
            </div>
            <p className="disclaimer">Answers quote the policy documents. The insurer’s own decisions on cover and claims prevail.</p>
          </form>
        )}
      </main>
      {source && <CitationViewer citation={source} onClose={() => setSource(null)} />}
    </div>
  );
}
