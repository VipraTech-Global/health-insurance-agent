import type { Card, OpenSource, ShortlistBlock } from "@/lib/chat-types";
import { QuoteLinks } from "../source-link";

const NEED_STATUS = {
  fits: "Covered", doesnt_fit: "Not covered", unresolved: "Not found in documents", addon: "Add-on (extra premium)",
} as const;

export function ShortlistTable({ block, cards, onSource }: { block: ShortlistBlock; cards: Card[]; onSource: OpenSource }) {
  const needs = block.needs ?? [];
  const priced = block.plans.some(p => p.premium);
  // Blocks stored before per-need columns keep one column of supporting quotes.
  const legacy = !block.needs;
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Plan</th><th>Insurer</th>
            {needs.map(n => <th key={n.field}>{n.label}</th>)}
            {priced && <th>Printed premium</th>}
            {legacy && <th>Sources</th>}
          </tr>
        </thead>
        <tbody>
          {block.plans.map(p => {
            const card = cards.find(c => c.plan_id === p.plan_id);
            return (
              <tr key={p.plan_id}>
                <th scope="row">
                  {p.name}
                  {p.variant && p.variant !== "Default" && <small className="muted">{p.variant}</small>}
                  {legacy && !p.confirmed && <small className="muted">Couldn’t be fully confirmed from the documents</small>}
                </th>
                <td>{p.insurer}</td>
                {needs.map(n => {
                  const need = p.needs?.find(x => x.field === n.field);
                  const status = need?.status ?? "unresolved";
                  return (
                    <td key={n.field} className={`need ${status}`}>
                      {need?.detail ?? NEED_STATUS[status]}
                      {need && need.citations.length > 0 && <QuoteLinks card={card} quotes={need.citations} kind="cards" onSource={onSource} />}
                    </td>
                  );
                })}
                {priced && <td>{p.premium ? `₹${p.premium}` : <span className="muted">Not printed</span>}</td>}
                {legacy && <td><QuoteLinks card={card} quotes={p.citations} kind="cards" onSource={onSource} /></td>}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
