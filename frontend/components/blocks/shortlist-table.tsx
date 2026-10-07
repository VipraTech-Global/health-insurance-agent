import type { Card, OpenSource, ShortlistBlock } from "@/lib/chat-types";
import { QuoteLinks } from "../source-link";

const planType = (t: string) => t.replaceAll("_", " ");

export function ShortlistTable({ block, cards, onSource }: { block: ShortlistBlock; cards: Card[]; onSource: OpenSource }) {
  return (
    <div className="table-wrap">
      <table>
        <thead><tr><th>Plan</th><th>Insurer</th><th>Variant</th><th>Type</th><th>Sources</th></tr></thead>
        <tbody>
          {block.plans.map(p => (
            <tr key={p.plan_id}>
              <th scope="row">{p.name}{!p.confirmed && <small className="muted">Couldn’t be fully confirmed from the documents</small>}</th>
              <td>{p.insurer}</td>
              <td>{p.variant}</td>
              <td>{planType(p.plan_type)}</td>
              <td><QuoteLinks card={cards.find(c => c.plan_id === p.plan_id)} quotes={p.citations} kind="cards" onSource={onSource} /></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
