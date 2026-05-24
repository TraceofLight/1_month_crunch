"""NumPy BM25 implementation for comparison with TF-IDF search."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Iterable

import numpy as np

from src.search import InvertedIndex, SearchResult
from src.text_processing import TextPreprocessor, make_snippet


@dataclass
class BM25SearchEngine:
    documents: list[str]
    tokenized_documents: list[list[str]]
    preprocessor: TextPreprocessor
    vocabulary_: dict[str, int]
    idf_: np.ndarray
    term_frequencies_: np.ndarray
    document_lengths_: np.ndarray
    avg_document_length_: float
    inverted_index: InvertedIndex
    k1: float = 1.5
    b: float = 0.75

    @classmethod
    def from_documents(
        cls,
        documents: Iterable[str],
        preprocessor: TextPreprocessor | None = None,
        k1: float = 1.5,
        b: float = 0.75,
    ) -> "BM25SearchEngine":
        doc_list = list(documents)
        text_preprocessor = preprocessor or TextPreprocessor()
        tokenized_documents = text_preprocessor.transform(doc_list)
        vocabulary = {
            term: index
            for index, term in enumerate(sorted({token for doc in tokenized_documents for token in doc}))
        }

        term_frequencies = np.zeros((len(tokenized_documents), len(vocabulary)), dtype=np.float64)
        document_frequency = np.zeros(len(vocabulary), dtype=np.float64)
        document_lengths = np.array([len(doc) for doc in tokenized_documents], dtype=np.float64)

        for row_index, doc in enumerate(tokenized_documents):
            counts = Counter(token for token in doc if token in vocabulary)
            for token, count in counts.items():
                term_frequencies[row_index, vocabulary[token]] = float(count)
            for token in set(doc):
                if token in vocabulary:
                    document_frequency[vocabulary[token]] += 1.0

        n_documents = len(tokenized_documents)
        idf = np.log(1.0 + (n_documents - document_frequency + 0.5) / (document_frequency + 0.5))
        avg_document_length = float(np.mean(document_lengths)) if len(document_lengths) else 0.0
        inverted_index = InvertedIndex.from_documents(tokenized_documents)

        return cls(
            documents=doc_list,
            tokenized_documents=tokenized_documents,
            preprocessor=text_preprocessor,
            vocabulary_=vocabulary,
            idf_=idf,
            term_frequencies_=term_frequencies,
            document_lengths_=document_lengths,
            avg_document_length_=avg_document_length,
            inverted_index=inverted_index,
            k1=k1,
            b=b,
        )

    def search(self, query: str, topk: int = 5) -> list[SearchResult]:
        query_terms = [token for token in self.preprocessor.tokenize(query) if token in self.vocabulary_]
        if not query_terms:
            return []

        candidate_ids = sorted(self.inverted_index.lookup(query_terms))
        if len(candidate_ids) < topk:
            candidate_ids = list(range(len(self.documents)))

        scores = np.zeros(len(candidate_ids), dtype=np.float64)
        candidate_lengths = self.document_lengths_[candidate_ids]
        length_norm = 1.0 - self.b + self.b * candidate_lengths / max(self.avg_document_length_, 1.0)

        for term in query_terms:
            term_index = self.vocabulary_[term]
            tf = self.term_frequencies_[candidate_ids, term_index]
            numerator = tf * (self.k1 + 1.0)
            denominator = tf + self.k1 * length_norm
            scores += self.idf_[term_index] * np.divide(
                numerator,
                denominator,
                out=np.zeros_like(numerator),
                where=denominator != 0,
            )

        ranked = sorted(
            zip(candidate_ids, scores, strict=True),
            key=lambda item: (-item[1], item[0]),
        )[:topk]
        return [
            SearchResult(float(score), int(doc_id), make_snippet(self.documents[doc_id]))
            for doc_id, score in ranked
        ]
