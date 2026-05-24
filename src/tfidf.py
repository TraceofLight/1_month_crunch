"""NumPy implementation of TF-IDF vectorization."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Iterable, Literal

import numpy as np


TfVariant = Literal["raw", "log", "double"]


@dataclass
class NumpyTfidfVectorizer:
    """A sklearn-compatible TF-IDF vectorizer for pre-tokenized documents."""

    smooth_idf: bool = True
    sublinear_tf: bool = False
    norm: Literal["l2"] | None = "l2"
    tf_variant: TfVariant = "raw"
    double_norm_k: float = 0.5
    vocabulary_: dict[str, int] = field(default_factory=dict, init=False)
    terms_: list[str] = field(default_factory=list, init=False)
    idf_: np.ndarray | None = field(default=None, init=False)
    document_frequency_: np.ndarray | None = field(default=None, init=False)

    def fit(self, tokenized_documents: Iterable[Iterable[str]]) -> "NumpyTfidfVectorizer":
        docs = [list(doc) for doc in tokenized_documents]
        terms = sorted({token for doc in docs for token in doc})
        self.vocabulary_ = {term: index for index, term in enumerate(terms)}
        self.terms_ = terms

        df = np.zeros(len(self.vocabulary_), dtype=np.float64)
        for doc in docs:
            seen_indices = {self.vocabulary_[token] for token in set(doc) if token in self.vocabulary_}
            for index in seen_indices:
                df[index] += 1.0

        n_documents = len(docs)
        if self.smooth_idf:
            self.idf_ = np.log((1.0 + n_documents) / (1.0 + df)) + 1.0
        else:
            safe_df = np.maximum(df, 1.0)
            self.idf_ = np.log(n_documents / safe_df) + 1.0
        self.document_frequency_ = df
        return self

    def fit_transform(self, tokenized_documents: Iterable[Iterable[str]]) -> np.ndarray:
        docs = [list(doc) for doc in tokenized_documents]
        self.fit(docs)
        return self.transform(docs)

    def transform(self, tokenized_documents: Iterable[Iterable[str]]) -> np.ndarray:
        if self.idf_ is None:
            raise ValueError("Vectorizer must be fitted before transform().")

        docs = [list(doc) for doc in tokenized_documents]
        counts = self.count_matrix(docs)
        tf = self._apply_tf_variant(counts)
        tfidf = tf * self.idf_
        return self._normalize(tfidf)

    def count_matrix(self, tokenized_documents: Iterable[Iterable[str]]) -> np.ndarray:
        docs = [list(doc) for doc in tokenized_documents]
        matrix = np.zeros((len(docs), len(self.vocabulary_)), dtype=np.float64)
        for row_index, doc in enumerate(docs):
            counts = Counter(token for token in doc if token in self.vocabulary_)
            for token, count in counts.items():
                matrix[row_index, self.vocabulary_[token]] = float(count)
        return matrix

    def _apply_tf_variant(self, counts: np.ndarray) -> np.ndarray:
        if self.sublinear_tf or self.tf_variant == "log":
            tf = np.zeros_like(counts, dtype=np.float64)
            positive = counts > 0
            tf[positive] = 1.0 + np.log(counts[positive])
            return tf

        if self.tf_variant == "double":
            max_counts = counts.max(axis=1, keepdims=True)
            tf = np.zeros_like(counts, dtype=np.float64)
            positive_rows = max_counts[:, 0] > 0
            tf[positive_rows] = self.double_norm_k + (
                1.0 - self.double_norm_k
            ) * counts[positive_rows] / max_counts[positive_rows]
            tf[counts == 0] = 0.0
            return tf

        return counts.astype(np.float64)

    def _normalize(self, matrix: np.ndarray) -> np.ndarray:
        if self.norm is None:
            return matrix
        if self.norm != "l2":
            raise ValueError(f"Unsupported norm: {self.norm}")

        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        normalized = np.zeros_like(matrix, dtype=np.float64)
        np.divide(matrix, norms, out=normalized, where=norms != 0)
        return normalized
