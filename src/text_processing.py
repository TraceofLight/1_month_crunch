"""Text cleaning and tokenization utilities."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable


DEFAULT_ENGLISH_STOPWORDS = {
    "a",
    "about",
    "above",
    "after",
    "again",
    "against",
    "all",
    "am",
    "an",
    "and",
    "any",
    "are",
    "as",
    "at",
    "be",
    "because",
    "been",
    "before",
    "being",
    "below",
    "between",
    "both",
    "but",
    "by",
    "can",
    "could",
    "did",
    "do",
    "does",
    "doing",
    "down",
    "during",
    "each",
    "few",
    "for",
    "from",
    "further",
    "had",
    "has",
    "have",
    "having",
    "he",
    "her",
    "here",
    "hers",
    "herself",
    "him",
    "himself",
    "his",
    "how",
    "i",
    "if",
    "in",
    "into",
    "is",
    "it",
    "its",
    "itself",
    "just",
    "me",
    "more",
    "most",
    "my",
    "myself",
    "no",
    "nor",
    "not",
    "now",
    "of",
    "off",
    "on",
    "once",
    "only",
    "or",
    "other",
    "our",
    "ours",
    "ourselves",
    "out",
    "over",
    "own",
    "same",
    "she",
    "should",
    "so",
    "some",
    "such",
    "than",
    "that",
    "the",
    "their",
    "theirs",
    "them",
    "themselves",
    "then",
    "there",
    "these",
    "they",
    "this",
    "those",
    "through",
    "to",
    "too",
    "under",
    "until",
    "up",
    "very",
    "was",
    "we",
    "were",
    "what",
    "when",
    "where",
    "which",
    "while",
    "who",
    "whom",
    "why",
    "will",
    "with",
    "you",
    "your",
    "yours",
    "yourself",
    "yourselves",
}


@dataclass
class TextPreprocessor:
    """Lowercase, clean, tokenize, and remove stopwords."""

    stopwords: Iterable[str] | None = None
    min_token_length: int = 2
    keep_default_stopwords: bool = False

    def __post_init__(self) -> None:
        custom_stopwords = set(self.stopwords or [])
        if self.keep_default_stopwords or self.stopwords is None:
            custom_stopwords |= DEFAULT_ENGLISH_STOPWORDS
        self.stopwords_ = {word.lower() for word in custom_stopwords}

    def clean(self, text: str) -> str:
        lowered = text.lower()
        alnum_and_space = re.sub(r"[^a-z0-9\s]+", " ", lowered)
        return re.sub(r"\s+", " ", alnum_and_space).strip()

    def tokenize(self, text: str) -> list[str]:
        cleaned = self.clean(text)
        tokens = cleaned.split()
        return [
            token
            for token in tokens
            if len(token) >= self.min_token_length
            and not token.isdigit()
            and token not in self.stopwords_
        ]

    def transform(self, texts: Iterable[str]) -> list[list[str]]:
        return [self.tokenize(text) for text in texts]


def make_snippet(text: str, max_chars: int = 220) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    if len(compact) <= max_chars:
        return compact
    return compact[: max_chars - 3].rstrip() + "..."
