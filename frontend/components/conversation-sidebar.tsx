"use client";

import { useState } from "react";
import type { Summary } from "@/lib/chat-types";

const relative = new Intl.RelativeTimeFormat("en", { numeric: "auto" });
function when(iso: string) {
  const minutes = Math.round((new Date(iso).getTime() - Date.now()) / 60000);
  if (minutes > -60) return relative.format(minutes, "minute");
  if (minutes > -1440) return relative.format(Math.round(minutes / 60), "hour");
  return relative.format(Math.round(minutes / 1440), "day");
}

export function ConversationSidebar({ conversations, current, collapsed, busy, onNew, onOpen, onSignOut, onErase }: {
  conversations: Summary[]; current?: string; collapsed: boolean; busy: boolean;
  onNew: () => void; onOpen: (id: string) => void; onSignOut: () => void; onErase: () => void;
}) {
  const [menu, setMenu] = useState(false);
  const [erase, setErase] = useState(false);
  return (
    <nav className={`sidebar${collapsed ? " collapsed" : ""}`} aria-label="Conversations">
      <button type="button" className="new-chat" disabled={busy} onClick={onNew} title="New chat">
        <span aria-hidden>＋</span><span className="label">New chat</span>
      </button>
      {!collapsed && (
        <ol className="history">
          {conversations.map(c => (
            <li key={c.id}>
              <button type="button" aria-current={c.id === current ? "page" : undefined} onClick={() => onOpen(c.id)}>
                <span className="title">{c.title}</span>
                <small>{when(c.updated_at)}</small>
              </button>
            </li>
          ))}
          {conversations.length === 0 && <li className="muted empty">Your conversations will appear here.</li>}
        </ol>
      )}
      {!collapsed && (
        <div className="account">
          {menu && (
            <div className="account-menu">
              {erase ? (
                <>
                  <p>Erase this account and its private conversation data?</p>
                  <button type="button" className="danger" onClick={onErase}>Confirm erasure</button>
                  <button type="button" onClick={() => setErase(false)}>Keep my account</button>
                </>
              ) : (
                <>
                  <button type="button" onClick={onSignOut}>Sign out</button>
                  <button type="button" onClick={() => setErase(true)}>Erase my account data</button>
                </>
              )}
            </div>
          )}
          <button type="button" className="account-toggle" aria-expanded={menu} onClick={() => { setMenu(!menu); setErase(false); }}>Account</button>
        </div>
      )}
    </nav>
  );
}
