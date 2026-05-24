"""Command-line search entrypoint."""

from __future__ import annotations

import argparse
from functools import lru_cache
from pathlib import Path

import numpy as np
from sklearn.datasets import fetch_20newsgroups

from src.search import SearchEngine
from src.text_processing import TextPreprocessor


CATEGORIES = [
    "comp.graphics",
    "rec.sport.baseball",
    "sci.space",
    "talk.politics.misc",
]


@lru_cache(maxsize=1)
def _default_engine(sample_per_class: int = 200, random_state: int = 42) -> SearchEngine:
    preprocessor = TextPreprocessor()
    dataset = fetch_20newsgroups(
        subset="all",
        categories=CATEGORIES,
        remove=("headers", "footers", "quotes"),
        data_home="data",
    )
    records_by_label: dict[int, list[str]] = {index: [] for index in range(len(dataset.target_names))}
    for text, label in zip(dataset.data, dataset.target, strict=True):
        if len(preprocessor.tokenize(text)) >= 5:
            records_by_label[int(label)].append(text)

    rng = np.random.default_rng(random_state)
    selected: list[str] = []
    for records in records_by_label.values():
        chosen = rng.choice(len(records), size=sample_per_class, replace=False)
        selected.extend(records[int(index)] for index in chosen)
    order = rng.permutation(len(selected))
    ordered = [selected[int(index)] for index in order]
    return SearchEngine.from_documents(ordered, preprocessor=preprocessor)


def search(query: str) -> list[tuple[float, int, str]]:
    """Return [(score, doc_id, text_snippet), ...] for the default corpus."""

    return [
        (result.score, result.doc_id, result.snippet)
        for result in _default_engine().search(query, topk=5)
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description="Search the 20 Newsgroups TF-IDF index.")
    parser.add_argument("--query", required=True, help="Natural-language search query.")
    parser.add_argument("--topk", type=int, default=5, help="Number of results to print.")
    parser.add_argument("--sample-per-class", type=int, default=200, help="Balanced samples per category.")
    args = parser.parse_args()

    engine = _default_engine(sample_per_class=args.sample_per_class)
    results = engine.search(args.query, topk=args.topk)

    print("=== 검색 결과 ===")
    print(f"Query: {args.query}")
    print("")
    for rank, result in enumerate(results, start=1):
        print(f"{rank}. [{result.score:.6f}] doc_id={result.doc_id} {result.snippet}")


if __name__ == "__main__":
    main()
