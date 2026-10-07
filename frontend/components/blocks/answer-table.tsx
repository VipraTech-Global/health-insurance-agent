import { useState } from "react";
import { api } from "@/lib/api";
import type { Anchor, OpenSource, PlanAnswer, Question, Statement } from "@/lib/chat-types";
import { SourceLink, planLabel } from "../source-link";

const progress: Record<string, string> = {
  queued: "Waiting to start…",
  searching: "Searching this plan’s documents…",
  answering: "Reading the quoted wording…",
  checking: "Checking quotes against the document…",
  cancelled: "Cancelled",
  source_revoked: "This plan’s documents were withdrawn.",
};

function Links({ plan, positions, onSource }: { plan: PlanAnswer; positions: number[]; onSource: OpenSource }) {
  const anchors = plan.result?.validation?.anchors ?? [];
  return (
    <span className="source-links">
      {positions.filter(n => anchors[n]).map(n => (
        <SourceLink key={n} n={n + 1} title={anchors[n].quote}
          onOpen={() => onSource(() => api<Anchor>(`/api/v2/demo/citations/${plan.id}/${n}/`), planLabel(plan))} />
      ))}
    </span>
  );
}

/** PDF extraction leaves control characters and private-use bullet glyphs in quotes; the wording is unchanged. */
const tidy = (t: string) => t.replace(/[\u0000-\u0009\u000B-\u001F\u007F\uE000-\uF8FF]/g, " ").replace(/ {2,}/g, " ").trim();

function StatementView({ s }: { s: Statement }) {
  const [open, setOpen] = useState(false);
  const quotes = [...(s.excerpts?.length ? s.excerpts : [s.text]), ...[...s.conditions, ...s.restrictions].map(c => c.text)];
  const long = quotes.join(" ").length > 360;
  return (
    <>
      {s.heading && <strong className="heading">{s.heading}</strong>}
      {s.coverage_scope && s.coverage_scope !== "base" && (
        <em className="scope">{s.coverage_scope === "optional premium adjustment" ? "Optional premium adjustment" : "Optional, extra premium"}</em>
      )}
      <div className={long && !open ? "quotes clamped" : "quotes"}>
        {(s.excerpts?.length ? s.excerpts : [s.text]).map((t, i) => <span key={i} className="quote">{tidy(t)}</span>)}
        {[...s.conditions, ...s.restrictions].map((c, i) => <span key={`c${i}`} className="quote condition">{tidy(c.text)}</span>)}
      </div>
      {long && <button type="button" className="more" onClick={() => setOpen(!open)}>{open ? "Show less" : "Show more"}</button>}
    </>
  );
}

function AnswerCell({ plan, onSource }: { plan: PlanAnswer; onSource: OpenSource }) {
  const result = plan.result;
  if (!result) return <span className="muted">{progress[plan.state] ?? "Working…"}</span>;
  const statements = result.answer?.statements ?? [];
  const mapping = result.validation?.statement_anchors;
  const anchors = result.validation?.anchors ?? [];
  if (!statements.length) return <span className="muted">{result.message ?? "The documents don’t state this."}</span>;
  return (
    <ul className="answer-lines">
      {result.message && <li className="muted">{result.message}</li>}
      {statements.map((s, i) => (
        <li key={i}>
          <StatementView s={s} />
          {mapping && <Links plan={plan} positions={mapping[i] ?? []} onSource={onSource} />}
        </li>
      ))}
      {/* Answers stored before per-statement mapping link every anchor once. */}
      {!mapping && anchors.length > 0 && <li><Links plan={plan} positions={anchors.map((_, n) => n)} onSource={onSource} /></li>}
    </ul>
  );
}

export function AnswerTable({ question, onSource }: { question?: Question; onSource: OpenSource }) {
  if (!question) return <p className="muted">Reading the policy documents…</p>;
  if (!question.plans.length) return <p className="muted">This comparison was cancelled.</p>;
  return (
    <div className="table-wrap answer-table">
      <table>
        <thead><tr><th>Plan</th><th>What the policy says</th></tr></thead>
        <tbody>
          {question.plans.map(p => (
            <tr key={p.id}>
              <th scope="row">{p.name}<small className="muted">{p.insurer}{p.variant !== "Default" ? ` · ${p.variant}` : ""}</small></th>
              <td><AnswerCell plan={p} onSource={onSource} /></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
