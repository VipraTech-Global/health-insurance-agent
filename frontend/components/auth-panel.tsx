"use client";

import { FormEvent, useState } from "react";
import { api } from "@/lib/api";

export function AuthPanel({ onSuccess }: { onSuccess: () => void }) {
  const [registering, setRegistering] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true); setError("");
    const form = new FormData(event.currentTarget);
    try {
      await api(`/api/v1/auth/${registering ? "register" : "login"}/`, { method: "POST", body: JSON.stringify({ email: form.get("email"), password: form.get("password") }) });
      onSuccess();
    } catch (caught) { setError(caught instanceof Error ? caught.message : "Could not sign in"); }
    finally { setBusy(false); }
  }

  return <main className="auth-shell">
    <section className="auth-story">
      <p className="eyebrow">LOCAL PILOT · EVIDENCE FIRST</p>
      <h1>Insurance advice you can trace back to the page.</h1>
      <p>Build a profile, compare documented fit, and open the exact source behind every material claim.</p>
      <div className="trust-row"><span>Reviewed sources</span><span>Exact citations</span><span>Honest unknowns</span></div>
    </section>
    <section className="auth-card">
      <div className="mark">CG</div>
      <h2>{registering ? "Create your pilot account" : "Welcome back"}</h2>
      <p>Your conversations stay inside this local demonstration.</p>
      <form onSubmit={submit}>
        <label>Email<input required type="email" name="email" autoComplete="email" placeholder="you@example.com" /></label>
        <label>Password<input required minLength={8} type="password" name="password" autoComplete={registering ? "new-password" : "current-password"} /></label>
        {error && <p className="error" role="alert">{error}</p>}
        <button className="primary" disabled={busy}>{busy ? "Working…" : registering ? "Create account" : "Sign in"}</button>
      </form>
      <button className="link-button" onClick={() => setRegistering(!registering)}>{registering ? "Already have an account? Sign in" : "New here? Create an account"}</button>
    </section>
  </main>;
}

