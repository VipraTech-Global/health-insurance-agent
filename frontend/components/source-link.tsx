"use client";

import { api } from "@/lib/api";
import type { Anchor, Card, OpenSource, Quote } from "@/lib/chat-types";

export const planLabel = (c: { insurer: string; name: string; variant: string }) =>
  `${c.insurer} — ${c.name}${c.variant && c.variant !== "Default" ? ` (${c.variant})` : ""}`;

/** Card and price citations resolve through the fact-card (or legacy index) endpoints. */
export function cardAnchor(card: Card, quote: Quote, kind: "cards" | "prices") {
  const path = card.card_version
    ? `${kind === "cards" ? "fact-cards" : "fact-prices"}/${card.card_version}`
    : `${kind}/${card.index_version}`;
  return () => api<Anchor>(`/api/v2/demo/${path}/citation/`, { method: "POST", body: JSON.stringify({ citation: quote }) });
}

export function SourceLink({ n, title, onOpen }: { n: number; title: string; onOpen: () => void }) {
  return (
    <button type="button" className="source-link" title={`Open source: ${title}`} aria-label={`Open source ${n}: ${title}`} onClick={onOpen}>
      {n}
    </button>
  );
}

/** Numbered links for a list of card or price quotations. */
export function QuoteLinks({ card, quotes, kind, onSource }: { card?: Card; quotes: Quote[]; kind: "cards" | "prices"; onSource: OpenSource }) {
  if (!card || !quotes.length) return <span className="muted">—</span>;
  const unique = quotes.filter((q, i) => quotes.findIndex(o => o.quote === q.quote && o.page_id === q.page_id) === i);
  return (
    <span className="source-links">
      {unique.map((q, i) => (
        <SourceLink key={i} n={i + 1} title={q.quote} onOpen={() => onSource(cardAnchor(card, q, kind), planLabel(card))} />
      ))}
    </span>
  );
}
