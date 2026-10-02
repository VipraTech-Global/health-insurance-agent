"use client";

import { useEffect, useState } from "react";
import { AuthPanel } from "@/components/auth-panel";
import { DemoApp } from "@/components/demo-app";
import { api } from "@/lib/api";

export default function DemoPage() {
  const [session, setSession] = useState<{ authenticated: boolean; user?: { email: string } } | null>(null);
  const [error, setError] = useState("");
  async function refresh() {
    try { setSession(await api("/api/v1/auth/session/")); }
    catch (e) { setError(e instanceof Error ? e.message : "Session unavailable"); }
  }
  useEffect(() => { void refresh(); }, []);
  if (error) return <main className="demo-shell"><p role="alert">{error}</p></main>;
  if (!session) return <main className="demo-shell">Loading CoverGuide…</main>;
  if (!session.authenticated) return <AuthPanel onSuccess={refresh} />;
  return <DemoApp onSignedOut={refresh} />;
}
