import { useState } from "react";
import { api } from "@/lib/api";
import type { Anchor, AnswerGroup, Card, OpenSource, PlanAnswer, Question, Statement } from "@/lib/chat-types";
import { QuoteLinks, SourceLink, planLabel } from "../source-link";

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

function AnswerCell({ plan, card, onSource }: { plan: PlanAnswer; card?: Card; onSource: OpenSource }) {
  const result = plan.result;
  if (!result) return <span className="muted">{progress[plan.state] ?? "Working…"}</span>;
  const statements = result.answer?.statements ?? [];
  const own = plan.card_statements ?? [];
  const mapping = result.validation?.statement_anchors;
  const anchors = result.validation?.anchors ?? [];
  if (!statements.length && !own.length) return <span className="muted">{result.message ?? "The documents don’t state this."}</span>;
  // The card's quotes lead when they decide the answer; an add-on that extends what the
  // base cover has follows the engine's wording instead.
  const extending = plan.group === "base" && own.every(s => s.coverage_scope === "optional, extra premium");
  const ownLines = own.map((s, i) => (
    <li key={`card${i}`}>
      <StatementView s={s} />
      <QuoteLinks card={card} kind="cards" onSource={onSource}
        quotes={[...(s.citations ?? []), ...[...s.conditions, ...s.restrictions].flatMap(c => c.citations ?? [])]} />
    </li>
  ));
  return (
    <ul className="answer-lines">
      {!extending && ownLines}
      {statements.length > 0 && result.message && <li className="muted">{result.message}</li>}
      {statements.map((s, i) => (
        <li key={i}>
          <StatementView s={s} />
          {mapping && <Links plan={plan} positions={mapping[i] ?? []} onSource={onSource} />}
        </li>
      ))}
      {/* Answers stored before per-statement mapping link every anchor once. */}
      {!mapping && anchors.length > 0 && <li><Links plan={plan} positions={anchors.map((_, n) => n)} onSource={onSource} /></li>}
      {extending && ownLines}
    </ul>
  );
}

/** Group headings: a benefit is in the base cover or sold as an add-on; a term is stated. */
const GROUPS: { key: AnswerGroup; benefit: string; term: string }[] = [
  { key: "base", benefit: "In the base cover", term: "States its terms" },
  { key: "addon", benefit: "Optional add-on (extra premium)", term: "An optional add-on changes them (extra premium)" },
  { key: "excluded", benefit: "States it isn’t covered", term: "States it isn’t covered" },
];

const variantLabel = (p: PlanAnswer) => (p.variant && p.variant !== "Default" ? ` (${p.variant})` : "");

function PlanRow({ plan, cards, onSource }: { plan: PlanAnswer; cards: Card[]; onSource: OpenSource }) {
  return (
    <tr>
      <th scope="row">{plan.name}<small className="muted">{plan.insurer}{plan.variant !== "Default" ? ` · ${plan.variant}` : ""}</small></th>
      <td><AnswerCell plan={plan} card={cards.find(c => c.plan_id === plan.plan_id)} onSource={onSource} /></td>
    </tr>
  );
}

function GroupHeading({ label, count }: { label: string; count: number }) {
  return (
    <tr className="group-row">
      <th scope="rowgroup" colSpan={2}>{label}<span className="count">{count}</span></th>
    </tr>
  );
}

export function AnswerTable({ question, cards, onSource }: { question?: Question; cards: Card[]; onSource: OpenSource }) {
  if (!question) return <p className="muted">Reading the policy documents…</p>;
  if (!question.plans.length) return <p className="muted">This comparison was cancelled.</p>;
  // A topic answer is grouped by where each plan's wording puts it; free-form answers are not.
  const grouped = Boolean(question.topic) && question.plans.some(p => p.group);
  if (!grouped) {
    return (
      <div className="table-wrap answer-table">
        <table>
          <thead><tr><th>Plan</th><th>What the policy says</th></tr></thead>
          <tbody>{question.plans.map(p => <PlanRow key={p.id} plan={p} cards={cards} onSource={onSource} />)}</tbody>
        </table>
      </div>
    );
  }
  const missing = question.plans.filter(p => p.group === "not_found");
  const other = question.plans.filter(p => !p.group);
  return (
    <div className="table-wrap answer-table grouped">
      <table>
        <thead><tr><th>Plan</th><th>What the policy says</th></tr></thead>
        {GROUPS.map(g => {
          const rows = question.plans.filter(p => p.group === g.key);
          return rows.length > 0 && (
            <tbody key={g.key}>
              <GroupHeading label={question.terms ? g.term : g.benefit} count={rows.length} />
              {rows.map(p => <PlanRow key={p.id} plan={p} cards={cards} onSource={onSource} />)}
            </tbody>
          );
        })}
        {other.length > 0 && (
          <tbody>
            <GroupHeading label={other.some(p => !p.result) ? "Still reading" : "Couldn’t be read"} count={other.length} />
            {other.map(p => <PlanRow key={p.id} plan={p} cards={cards} onSource={onSource} />)}
          </tbody>
        )}
        {missing.length > 0 && (
          <tbody>
            <GroupHeading label={question.terms ? "Not stated in the documents" : "Not mentioned in the documents"} count={missing.length} />
            <tr className="missing-row">
              <td colSpan={2}>
                {missing.map(p => `${p.name}${variantLabel(p)}`).join(", ")}
                <small className="muted">Not mentioning it doesn’t mean a plan excludes it.</small>
              </td>
            </tr>
          </tbody>
        )}
      </table>
    </div>
  );
}
