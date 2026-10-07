import type { Card, OpenSource, PriceBlock, PriceComparisonBlock } from "@/lib/chat-types";
import { QuoteLinks, planLabel } from "../source-link";

export function PriceComparisonTable({ block, cards, onSource }: { block: PriceComparisonBlock; cards: Card[]; onSource: OpenSource }) {
  return (
    <div className="table-wrap">
      <table>
        <caption>Printed annual premiums, lowest first · {block.basis}</caption>
        <thead><tr><th>Plan</th><th>Printed premium</th><th>Chart basis</th><th>Sources</th></tr></thead>
        <tbody>
          {block.rows.map(r => {
            const card = cards.find(c => c.plan_id === r.plan_id);
            return (
              <tr key={r.plan_id}>
                <th scope="row">{r.name}</th>
                <td className="amount">₹{r.amount_printed}</td>
                <td>{Object.values(r.axes).join(" · ")}</td>
                <td>
                  <QuoteLinks card={card} quotes={[...r.citations, ...(r.chart_zone_citations ?? [])]} kind="prices" onSource={onSource} />
                  {r.zone_citations.length > 0 && <QuoteLinks card={card} quotes={r.zone_citations} kind="cards" onSource={onSource} />}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
      {block.note && <p className="table-note">{block.note}</p>}
      {block.not_found.length > 0 && <p className="table-note">No printed price: {block.not_found.map(m => `${m.name} (${m.reason})`).join("; ")}</p>}
    </div>
  );
}

export function PriceTable({ block, cards, onSource }: { block: PriceBlock; cards: Card[]; onSource: OpenSource }) {
  const card = cards.find(c => c.plan_id === block.plan_id);
  if (block.status !== "available" || !block.amount_printed) return null;
  return (
    <div className="table-wrap">
      <table>
        <thead><tr><th>Plan</th><th>Printed premium</th><th>Budget</th><th>Sources</th></tr></thead>
        <tbody>
          <tr>
            <th scope="row">{card ? planLabel(card) : block.plan_id}</th>
            <td className="amount">₹{block.amount_printed}</td>
            <td>{block.budget_comparison?.note ?? "—"}</td>
            <td><QuoteLinks card={card} quotes={block.citations} kind="prices" onSource={onSource} /></td>
          </tr>
        </tbody>
      </table>
      <p className="table-note">{[block.label, block.caveat].filter(Boolean).join(". ")}</p>
    </div>
  );
}
