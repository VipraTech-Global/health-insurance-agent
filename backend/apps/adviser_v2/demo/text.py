"""Original-text token accounting and the winning BM25 implementation."""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

import tiktoken


@lru_cache(maxsize=1)
def tokenizer() -> Any:
    return tiktoken.get_encoding("o200k_base")


def token_count(text: str) -> int:
    return len(tokenizer().encode(text, disallowed_special=()))


@dataclass(frozen=True)
class LexicalDocument:
    id: str
    text: str


def lexical_terms(text: str) -> list[str]:
    return re.findall(r"\w+", text.casefold())


class BM25:
    """Okapi BM25, k1=1.5, b=.75, positive Robertson IDF."""

    def __init__(self, chunks: list[LexicalDocument]):
        self.chunks = chunks
        self.frequencies = [Counter(lexical_terms(c.text)) for c in chunks]
        self.lengths = [sum(f.values()) for f in self.frequencies]
        self.average = sum(self.lengths) / len(chunks) if chunks else 1
        self.df = Counter(term for counts in self.frequencies for term in counts)

    def rank(self, query: str) -> list[LexicalDocument]:
        if not query.strip():
            raise ValueError("Retrieval needs the customer's question text.")
        scores = []
        for i, counts in enumerate(self.frequencies):
            score = 0.0
            for term in set(lexical_terms(query)):
                frequency = counts[term]
                if frequency:
                    idf = math.log(
                        1 + (len(self.chunks) - self.df[term] + 0.5) / (self.df[term] + 0.5)
                    )
                    score += (
                        idf
                        * frequency
                        * 2.5
                        / (frequency + 1.5 * (0.25 + 0.75 * self.lengths[i] / self.average))
                    )
            scores.append((score, self.chunks[i]))
        return [c for _score, c in sorted(scores, key=lambda pair: (-pair[0], pair[1].id))]
