"use client";

import { useEffect, useState } from "react";
import { AdviserApp } from "@/components/adviser-app";
import { AuthPanel } from "@/components/auth-panel";
import { api } from "@/lib/api";

type Session = { authenticated: boolean; user?: { email: string; is_staff?: boolean } };

export default function Home() {
  const [session, setSession] = useState<Session | null>(null);
  async function refresh() { setSession(await api<Session>("/api/v1/auth/session/")); }
  useEffect(() => { void refresh(); }, []);
  if (!session) return <div className="splash"><span className="mark">CG</span></div>;
  if (!session.authenticated || !session.user) return <AuthPanel onSuccess={refresh} />;
  return <AdviserApp email={session.user.email} onLogout={async () => { await api("/api/v1/auth/logout/", { method: "POST" }); setSession({ authenticated: false }); }} />;
}
