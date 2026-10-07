export type Quote = { section_id: string; page_id: string; quote: string; occurrence: number };
export type Card = { plan_id: string; index_version: string; card_version?: string; insurer: string; name: string; variant: string; plan_type: string };
export type Anchor = { quote: string; page: number; document_id: string; boxes: [number, number, number, number][]; pdf_url: string };

export type ShortlistBlock = {
  type: "shortlist";
  plans: { plan_id: string; insurer: string; name: string; variant: string; plan_type: string; confirmed: boolean; citations: Quote[] }[];
};
export type QuestionBlock = { type: "question"; question_id: string };
export type PriceBlock = {
  type: "price"; plan_id: string; status: string; amount_printed: string | null; label?: string; caveat?: string;
  budget_comparison?: { status: string; note: string }; citations: Quote[];
};
export type PriceRow = { plan_id: string; name: string; amount_printed: string; axes: Record<string, string>; citations: Quote[]; zone_citations: Quote[]; chart_zone_citations?: Quote[] };
export type PriceComparisonBlock = {
  type: "price_comparison"; basis: string; note: string; rows: PriceRow[]; not_found: { plan_id: string; name: string; reason: string }[];
};
export type Block = ShortlistBlock | QuestionBlock | PriceBlock | PriceComparisonBlock;

export type Message = { role: "customer" | "assistant"; text: string; understanding?: string[]; blocks?: Block[] };

export type Statement = {
  text: string; heading?: string; excerpts?: string[];
  coverage_scope?: "base" | "optional, extra premium" | "optional premium adjustment";
  conditions: { text: string }[]; restrictions: { text: string }[];
};
export type PlanAnswer = {
  id: string; plan_id: string; name: string; variant: string; insurer: string; state: string; model: string;
  result?: { status?: string; message?: string; answer?: { statements: Statement[] }; validation?: { anchors: Anchor[]; statement_anchors?: number[][] } } | null;
};
export type Question = { id: string; state: string; plans: PlanAnswer[] };

export type State = { revision: number; stage: string; message: string; question_id: string | null; transcript: Message[] };
export type Chat = { id: string; release_id: string; cards: Card[]; state: State };
export type Summary = { id: string; title: string; updated_at: string };

/** Fetches a source anchor and opens it in the side panel under the given label. */
export type OpenSource = (load: () => Promise<Anchor>, label: string) => void;

export const finished = (q?: Question) => Boolean(q && ["completed", "cancelled"].includes(q.state));
