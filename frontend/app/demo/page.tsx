"use client";

import { useEffect, useState } from "react";
import { AuthPanel } from "@/components/auth-panel";
import { ChatApp } from "@/components/chat-app";
import { api } from "@/lib/api";

export default function DemoPage() {
  const [session, setSession] = useState<{ authenticated: boolean; user?: { email: string } } | null>(null);
  const [error, setError] = useState("");
  async function refresh() {
    try { setSession(await api("/api/v1/auth/session/")); }
    catch (e) { setError(e instanceof Error ? e.message : "Session unavailable"); }
  }
  useEffect(() => { void refresh(); }, []);
  if (error) return <main className="splash"><p role="alert">{error}</p></main>;
  if (!session) return <main className="splash">Loading CoverGuide…</main>;
  if (!session.authenticated) return <AuthPanel onSuccess={refresh} />;
  return <ChatApp onSignedOut={refresh} />;
}
