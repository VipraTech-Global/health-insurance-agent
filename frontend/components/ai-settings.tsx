"use client";

import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { components } from "@/lib/api-schema";

type Models = components["schemas"]["ModelList"];
type Relay = components["schemas"]["RelayStatus"];
type ActionResult = components["schemas"]["AccountActionResult"];

export function AISettings({ isAdmin }: { isAdmin: boolean }) {
  const [models, setModels] = useState<Models | null>(null);
  const [relay, setRelay] = useState<Relay | null>(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);
  const [candidate, setCandidate] = useState("");
  const reload = useCallback(async () => {
    setModels(await api<Models>("/api/v1/ai/models/"));
    if (isAdmin) setRelay(await api<Relay>("/api/v1/admin/ai-relay/"));
  }, [isAdmin]);
  useEffect(() => { void reload().catch((e: Error) => setError(e.message)); }, [reload]);
  useEffect(() => {
    if (!relay?.account.login_in_progress) return;
    let disposed = false;
    let timer: ReturnType<typeof setTimeout>;
    async function poll() {
      try {
        const result = await api<ActionResult>("/api/v1/admin/ai-relay/accounts/", { method: "POST", body: JSON.stringify({ action: "status" }) });
        if (disposed) return;
        if (result.account) setRelay((previous) => previous ? { ...previous, account: result.account! } : previous);
        if (result.account?.login_in_progress) timer = setTimeout(poll, 2000);
        else { setNotice(result.account?.state === "Connected" ? "Codex is connected." : "Login ended. Check the account status."); await reload(); }
      } catch (e) { if (!disposed) setError(e instanceof Error ? e.message : "Could not check login status. Use Refresh to try again."); }
    }
    timer = setTimeout(poll, 2000);
    return () => { disposed = true; clearTimeout(timer); };
  }, [relay?.account.login_in_progress, reload]);

  async function selectModel(routeId: string) {
    if (!routeId) return;
    setBusy(true); setError(""); setNotice("");
    try {
      setModels(await api<Models>("/api/v1/ai/preferences/", { method: "PATCH", body: JSON.stringify({ route_id: routeId }) }));
      setNotice("Your model choice is saved for future turns.");
    } catch (e) { setError(e instanceof Error ? e.message : "Could not save your choice."); }
    finally { setBusy(false); }
  }
  async function accountAction(action: string) {
    if (["connect", "disconnect", "restore", "forget"].includes(action) && !window.confirm(action === "forget" ? "Forget this laptop-wide Codex account? Its saved login will be removed. This also affects Job-In." : "This changes the laptop-wide Codex connection used by CoverGuide and Job-In. Continue?")) return;
    const tab = action === "connect" ? window.open("about:blank", "_blank") : null;
    if (action === "connect" && !tab) { setError("Allow a new tab for Codex login, then try again."); return; }
    if (tab) tab.opener = null;
    setBusy(true); setError(""); setNotice("");
    try {
      const result = await api<ActionResult>("/api/v1/admin/ai-relay/accounts/", { method: "POST", body: JSON.stringify({ action }) });
      if (tab && result.authorization_url) tab.location.href = result.authorization_url;
      else tab?.close();
      await reload();
    } catch (e) { tab?.close(); setError(e instanceof Error ? e.message : "The account action failed."); }
    finally { setBusy(false); }
  }
  async function qualify() {
    if (!candidate) return;
    setBusy(true); setError(""); setNotice("Testing the model's answer and interview responses…");
    try {
      const result = await api<components["schemas"]["Qualification"]>("/api/v1/admin/ai-relay/qualifications/", { method: "POST", body: JSON.stringify({ model: candidate }) });
      setNotice(result.state === "qualified" ? `${candidate} passed and is available to users.` : `${candidate} did not pass and remains unavailable.`);
      await reload();
    } catch (e) { setError(e instanceof Error ? e.message : "Qualification failed."); setNotice(""); }
    finally { setBusy(false); }
  }
  return <section className="coverage ai-settings"><p className="eyebrow">YOUR PREFERENCES</p><h1>AI settings</h1>
    <p className="lede">Choose the model for your conversations. Every policy answer still needs verified evidence.</p>
    {error && <div className="error-banner" role="alert">{error}</div>}
    {notice && <p role="status">{notice}</p>}
    <label>Your AI model<select aria-label="Your AI model" value={models?.selected_route_id ?? ""} disabled={busy || !models?.models.length} onChange={(e) => void selectModel(e.target.value)}>
      {!models?.selected_available && <option value={models?.selected_route_id ?? ""}>{models?.selected_model ? `${models.selected_model} — unavailable` : "No qualified model available"}</option>}
      {models?.models.map((model) => <option key={model.route_id} value={model.route_id}>{model.model}</option>)}
    </select></label>
    <p>Only tested models appear here. Your selected model is used as chosen; an unavailable model produces a clear error.</p>
    <button className="secondary" disabled={busy} onClick={() => void reload().catch((e: Error) => setError(e.message))}>Refresh models and status</button>
    {isAdmin && <div className="relay-admin"><h2>Codex subscription</h2><div className="notice"><b>Laptop-wide connection</b><p>CoverGuide and Job-In share this subscription. Connecting, disconnecting, restoring, or forgetting an account affects both applications.</p></div>
      <p><strong>{relay?.account.state ?? "Checking connection…"}</strong> {relay?.account.masked_identifier}</p>
      {relay?.catalogue_error && <p role="alert">{relay.catalogue_error}</p>}
      <div className="relay-actions">
        <button className="primary" disabled={busy || relay?.account.login_in_progress} onClick={() => void accountAction("connect")}>{relay?.account.has_active_account ? "Switch Codex account" : "Connect Codex"}</button>
        {relay?.account.login_in_progress && <><button className="secondary" disabled={busy} onClick={() => void accountAction("status")}>Check login status</button><button className="secondary" disabled={busy} onClick={() => void accountAction("cancel")}>Cancel login</button></>}
        {relay?.account.has_active_account && <button className="secondary" disabled={busy || relay.account.login_in_progress} onClick={() => void accountAction("disconnect")}>Disconnect</button>}
        {relay?.account.can_restore && !relay.account.has_active_account && <button className="secondary" disabled={busy || relay.account.login_in_progress} onClick={() => void accountAction("restore")}>Restore account</button>}
        {(relay?.account.has_active_account || relay?.account.can_restore) && <button className="secondary" disabled={busy || relay.account.login_in_progress} onClick={() => void accountAction("forget")}>Forget account</button>}
      </div>
      <h2>Qualify another model</h2><p>Newly discovered models must pass both tests before users can choose them.</p>
      <label>Discovered model<select aria-label="Discovered model" value={candidate} onChange={(e) => setCandidate(e.target.value)} disabled={busy}><option value="">Choose a model</option>{relay?.discovered_models.map((model) => <option key={model} value={model}>{model}</option>)}</select></label>
      <button className="secondary" disabled={busy || !candidate} onClick={() => void qualify()}>Test and qualify</button>
    </div>}
  </section>;
}
