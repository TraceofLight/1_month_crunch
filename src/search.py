"""Cosine-similarity document search."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable

import numpy as np

from src.text_processing import TextPreprocessor, make_snippet
from src.tfidf import NumpyTfidfVectorizer


@dataclass(frozen=True)
class SearchResult:
    score: float
    doc_id: int
    snippet: str


class InvertedIndex:
    """Term to document-id lookup used for search candidate pruning."""

    def __init__(self) -> None:
        self._index: dict[str, set[int]] = defaultdict(set)

    def add_document(self, doc_id: int, tokens: Iterable[str]) -> None:
        for token in set(tokens):
            self._index[token].add(doc_id)

    @classmethod
    def from_documents(cls, tokenized_documents: Iterable[Iterable[str]]) -> "InvertedIndex":
        index = cls()
        for doc_id, tokens in enumerate(tokenized_documents):
            index.add_document(doc_id, tokens)
        return index

    def lookup(self, tokens: Iterable[str]) -> set[int]:
        doc_ids: set[int] = set()
        for token in tokens:
            doc_ids.update(self._index.get(token, set()))
        return doc_ids


def cosine_similarity(query_vectors: Iterable[Iterable[float]], doc_vectors: Iterable[Iterable[float]]) -> np.ndarray:
    query_matrix = np.asarray(query_vectors, dtype=np.float64)
    document_matrix = np.asarray(doc_vectors, dtype=np.float64)
    if query_matrix.ndim == 1:
        query_matrix = query_matrix.reshape(1, -1)
    if document_matrix.ndim == 1:
        document_matrix = document_matrix.reshape(1, -1)

    numerator = query_matrix @ document_matrix.T
    query_norms = np.linalg.norm(query_matrix, axis=1, keepdims=True)
    doc_norms = np.linalg.norm(document_matrix, axis=1, keepdims=True).T
    denominator = query_norms @ doc_norms
    scores = np.zeros_like(numerator, dtype=np.float64)
    np.divide(numerator, denominator, out=scores, where=denominator != 0)
    return scores


@dataclass
class SearchEngine:
    documents: list[str]
    tokenized_documents: list[list[str]]
    preprocessor: TextPreprocessor
    vectorizer: NumpyTfidfVectorizer
    document_vectors: np.ndarray
    inverted_index: InvertedIndex

    @classmethod
    def from_documents(
        cls,
        documents: Iterable[str],
        preprocessor: TextPreprocessor | None = None,
        vectorizer: NumpyTfidfVectorizer | None = None,
    ) -> "SearchEngine":
        doc_list = list(documents)
        text_preprocessor = preprocessor or TextPreprocessor()
        tokenized_documents = text_preprocessor.transform(doc_list)
        tfidf_vectorizer = vectorizer or NumpyTfidfVectorizer()
        document_vectors = tfidf_vectorizer.fit_transform(tokenized_documents)
        inverted_index = InvertedIndex.from_documents(tokenized_documents)
        return cls(
            documents=doc_list,
            tokenized_documents=tokenized_documents,
            preprocessor=text_preprocessor,
            vectorizer=tfidf_vectorizer,
            document_vectors=document_vectors,
            inverted_index=inverted_index,
        )

    def search(self, query: str, topk: int = 5) -> list[SearchResult]:
        query_tokens = self.preprocessor.tokenize(query)
        if not query_tokens:
            return []

        query_vector = self.vectorizer.transform([query_tokens])
        candidate_ids = sorted(self.inverted_index.lookup(query_tokens))
        if len(candidate_ids) < topk:
            candidate_ids = list(range(len(self.documents)))

        candidate_vectors = self.document_vectors[candidate_ids]
        scores = cosine_similarity(query_vector, candidate_vectors)[0]
        ranked = sorted(
            zip(candidate_ids, scores, strict=True),
            key=lambda item: (-item[1], item[0]),
        )[:topk]

        return [
            SearchResult(
                score=float(score),
                doc_id=int(doc_id),
                snippet=make_snippet(self.documents[doc_id]),
            )
            for doc_id, score in ranked
        ]
