import { finished, type Card, type Message, type OpenSource, type Question } from "@/lib/chat-types";
import { AnswerTable } from "./blocks/answer-table";
import { PriceComparisonTable, PriceTable } from "./blocks/price-table";
import { ShortlistTable } from "./blocks/shortlist-table";

export function MessageView({ message, cards, questions, onSource, onPick }: {
  message: Message; cards: Card[]; questions: Record<string, Question>; onSource: OpenSource;
  /** Set on the latest reply only: its suggested answers can be tapped. */
  onPick?: (text: string) => void;
}) {
  if (message.role === "customer") return <div className="msg customer"><p>{message.text}</p></div>;
  const blocks = message.blocks ?? [];
  // The guided reply waits until a running policy answer has finished.
  const waiting = blocks.some(b => b.type === "question" && !finished(questions[b.question_id]));
  return (
    <div className="msg assistant">
      {blocks.map((b, i) =>
        b.type === "question" ? <AnswerTable key={i} question={questions[b.question_id]} cards={cards} onSource={onSource} />
        : b.type === "shortlist" ? <ShortlistTable key={i} block={b} cards={cards} onSource={onSource} />
        : b.type === "price" ? <PriceTable key={i} block={b} cards={cards} onSource={onSource} />
        : <PriceComparisonTable key={i} block={b} cards={cards} onSource={onSource} />,
      )}
      {!waiting && <p>{message.text}</p>}
      {!waiting && onPick && message.suggestions && message.suggestions.length > 0 && (
        <div className="suggestions" role="group" aria-label="Suggested replies">
          {message.suggestions.map(s => <button type="button" key={s} className="chip" onClick={() => onPick(s)}>{s}</button>)}
        </div>
      )}
      {!waiting && message.understanding && message.understanding.length > 0 && (
        <details className="understood"><summary>What I’ve understood so far</summary>{message.understanding.map((line, n) => <p key={n}>{line}</p>)}</details>
      )}
    </div>
  );
}
