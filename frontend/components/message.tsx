import { finished, type Card, type Message, type OpenSource, type Question } from "@/lib/chat-types";
import { AnswerTable } from "./blocks/answer-table";
import { PriceComparisonTable, PriceTable } from "./blocks/price-table";
import { ShortlistTable } from "./blocks/shortlist-table";

export function MessageView({ message, cards, questions, onSource }: {
  message: Message; cards: Card[]; questions: Record<string, Question>; onSource: OpenSource;
}) {
  if (message.role === "customer") return <div className="msg customer"><p>{message.text}</p></div>;
  const blocks = message.blocks ?? [];
  // The guided reply waits until a running policy answer has finished.
  const waiting = blocks.some(b => b.type === "question" && !finished(questions[b.question_id]));
  return (
    <div className="msg assistant">
      {blocks.map((b, i) =>
        b.type === "question" ? <AnswerTable key={i} question={questions[b.question_id]} onSource={onSource} />
        : b.type === "shortlist" ? <ShortlistTable key={i} block={b} cards={cards} onSource={onSource} />
        : b.type === "price" ? <PriceTable key={i} block={b} cards={cards} onSource={onSource} />
        : <PriceComparisonTable key={i} block={b} cards={cards} onSource={onSource} />,
      )}
      {!waiting && <p>{message.text}</p>}
      {!waiting && message.understanding && message.understanding.length > 0 && (
        <details className="understood"><summary>What I’ve understood so far</summary>{message.understanding.map((line, n) => <p key={n}>{line}</p>)}</details>
      )}
    </div>
  );
}
