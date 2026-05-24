"""Run the full document search and classification pipeline."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from sklearn.datasets import fetch_20newsgroups
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import classification_report

from src.bm25 import BM25SearchEngine
from src.classification import ClassificationResult, train_logistic_regression
from src.search import SearchEngine
from src.text_processing import TextPreprocessor
from src.tfidf import NumpyTfidfVectorizer


CATEGORIES = [
    "comp.graphics",
    "rec.sport.baseball",
    "sci.space",
    "talk.politics.misc",
]


def load_balanced_20newsgroups(
    preprocessor: TextPreprocessor,
    data_home: Path,
    categories: list[str],
    sample_per_class: int,
    random_state: int,
) -> tuple[list[str], list[list[str]], np.ndarray, list[str]]:
    dataset = fetch_20newsgroups(
        subset="all",
        categories=categories,
        remove=("headers", "footers", "quotes"),
        data_home=str(data_home),
    )

    records_by_label: dict[int, list[tuple[str, list[str]]]] = {index: [] for index in range(len(dataset.target_names))}
    for text, label in zip(dataset.data, dataset.target, strict=True):
        tokens = preprocessor.tokenize(text)
        if len(tokens) >= 5:
            records_by_label[int(label)].append((text, tokens))

    rng = np.random.default_rng(random_state)
    selected_texts: list[str] = []
    selected_tokens: list[list[str]] = []
    selected_labels: list[int] = []

    for label, records in records_by_label.items():
        if len(records) < sample_per_class:
            raise ValueError(
                f"Class {dataset.target_names[label]} has {len(records)} usable records, "
                f"less than requested {sample_per_class}."
            )
        chosen_indices = rng.choice(len(records), size=sample_per_class, replace=False)
        for record_index in chosen_indices:
            text, tokens = records[int(record_index)]
            selected_texts.append(text)
            selected_tokens.append(tokens)
            selected_labels.append(label)

    order = rng.permutation(len(selected_texts))
    texts = [selected_texts[int(index)] for index in order]
    tokens = [selected_tokens[int(index)] for index in order]
    labels = np.array([selected_labels[int(index)] for index in order], dtype=int)
    return texts, tokens, labels, list(dataset.target_names)


def validate_tfidf(
    tokenized_documents: list[list[str]],
    evidence_dir: Path,
) -> tuple[float, float, tuple[int, int]]:
    vectorizer = NumpyTfidfVectorizer(
        smooth_idf=True,
        sublinear_tf=False,
        norm="l2",
        tf_variant="raw",
    )
    custom_matrix = vectorizer.fit_transform(tokenized_documents)
    joined_docs = [" ".join(tokens) for tokens in tokenized_documents]

    sklearn_vectorizer = TfidfVectorizer(
        tokenizer=str.split,
        preprocessor=None,
        lowercase=False,
        token_pattern=None,
        vocabulary=vectorizer.vocabulary_,
        smooth_idf=True,
        sublinear_tf=False,
        norm="l2",
    )
    sklearn_matrix = sklearn_vectorizer.fit_transform(joined_docs).toarray()
    diff = np.abs(custom_matrix - sklearn_matrix)
    max_error = float(diff.max()) if diff.size else 0.0
    mean_error = float(diff.mean()) if diff.size else 0.0
    result = "PASS" if max_error <= 1e-6 else "FAIL"

    (evidence_dir / "tfidf_validation.txt").write_text(
        "\n".join(
            [
                "=== TF-IDF 구현 검증 결과 ===",
                f"TF-IDF 행렬 shape: {custom_matrix.shape}",
                "[검증] 직접 구현 vs Scikit-learn",
                "  - sklearn 설정: tokenizer=str.split, lowercase=False, token_pattern=None",
                "  - sklearn 설정: smooth_idf=True, sublinear_tf=False, norm='l2'",
                "  - 직접 구현 설정: raw count TF, smooth_idf=True, sublinear_tf=False, norm='l2'",
                f"  - 최대 오차: {max_error:.12e}",
                f"  - 평균 오차: {mean_error:.12e}",
                f"  - 결과: {result} (허용 오차 1e-6)",
            ]
        ),
        encoding="utf-8",
    )
    return max_error, mean_error, custom_matrix.shape


def write_search_results(path: Path, title: str, query: str, results: Iterable) -> None:
    lines = [title, f"Query: {query}", "", "Top 결과:"]
    for rank, result in enumerate(results, start=1):
        lines.append(f"{rank}. [{result.score:.6f}] doc_id={result.doc_id} {result.snippet}")
    path.write_text("\n".join(lines), encoding="utf-8")


def plot_confusion_matrix(
    matrix: np.ndarray,
    target_names: list[str],
    output_path: Path,
) -> None:
    plt.figure(figsize=(9, 7))
    sns.heatmap(
        matrix,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=target_names,
        yticklabels=target_names,
    )
    plt.xlabel("Predicted")
    plt.ylabel("Actual")
    plt.tight_layout()
    plt.savefig(output_path, dpi=160)
    plt.close()


def write_classification_metrics(
    result: ClassificationResult,
    labels: np.ndarray,
    target_names: list[str],
    evidence_dir: Path,
) -> None:
    report = classification_report(
        result.y_test,
        result.y_pred,
        target_names=target_names,
        digits=4,
        zero_division=0,
    )
    lines = [
        "=== 분류 성능 평가 ===",
        "모델: Logistic Regression(max_iter=1000, class_weight='balanced', random_state=42)",
        f"데이터: Train {len(result.train_indices)} / Test {len(result.test_indices)}",
        f"전체 문서 수: {len(labels)}",
        f"카테고리: {', '.join(target_names)}",
        f"정확도: {result.accuracy:.6f}",
        f"F1-Score(macro): {result.f1_macro:.6f}",
        "",
        "=== Classification Report ===",
        report,
        "=== Confusion Matrix ===",
        np.array2string(result.confusion_matrix),
    ]
    (evidence_dir / "classification_metrics.txt").write_text("\n".join(lines), encoding="utf-8")
    plot_confusion_matrix(result.confusion_matrix, target_names, evidence_dir / "confusion_matrix.png")


def analyze_misclassifications(
    texts: list[str],
    tokenized_documents: list[list[str]],
    target_names: list[str],
    result: ClassificationResult,
    evidence_dir: Path,
    limit: int = 8,
) -> int:
    misclassified_positions = np.where(result.y_test != result.y_pred)[0]
    coefficients = result.model.coef_
    terms = result.vectorizer.terms_
    lines = ["=== 오분류 케이스 분석 ==="]

    for case_number, test_position in enumerate(misclassified_positions[:limit], start=1):
        original_index = int(result.test_indices[int(test_position)])
        actual = int(result.y_test[int(test_position)])
        predicted = int(result.y_pred[int(test_position)])
        tokens = tokenized_documents[original_index]
        token_set = set(tokens)

        if coefficients.shape[0] == len(target_names):
            predicted_weights = coefficients[predicted]
        else:
            predicted_weights = coefficients[0]
        weighted_terms = [
            (term, float(predicted_weights[index]))
            for index, term in enumerate(terms)
            if term in token_set
        ]
        weighted_terms.sort(key=lambda item: item[1], reverse=True)
        influential = ", ".join(term for term, _ in weighted_terms[:5]) or "확인 가능한 고가중치 단어 없음"
        snippet = " ".join(texts[original_index].split())[:360]

        lines.extend(
            [
                "",
                f"[케이스 {case_number}]",
                f"예측: {target_names[predicted]} / 실제: {target_names[actual]}",
                f"문서 ID: {original_index}",
                f"예측 클래스 쪽으로 작용한 단어: {influential}",
                f"문서: {snippet}",
                "원인: 단어 빈도 기반 특성이 주제 단어의 문맥, 부정, 인용 관계를 구분하지 못해 "
                "예측 클래스에서 자주 등장한 표면 단어에 끌린 사례다.",
            ]
        )

    if len(misclassified_positions) == 0:
        lines.append("오분류가 발생하지 않았다.")

    (evidence_dir / "misclassified_cases.txt").write_text("\n".join(lines), encoding="utf-8")
    return int(len(misclassified_positions))


def compare_tf_variants(
    tokenized_documents: list[list[str]],
    labels: np.ndarray,
    texts: list[str],
    preprocessor: TextPreprocessor,
    query: str,
    evidence_dir: Path,
    random_state: int,
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for variant in ["raw", "log", "double"]:
        result = train_logistic_regression(
            tokenized_documents,
            labels,
            random_state=random_state,
            tf_variant=variant,
        )
        engine = SearchEngine.from_documents(
            texts,
            preprocessor=preprocessor,
            vectorizer=NumpyTfidfVectorizer(tf_variant=variant),
        )
        search_results = engine.search(query, topk=1)
        top_result = search_results[0] if search_results else None
        rows.append(
            {
                "tf_variant": variant,
                "accuracy": f"{result.accuracy:.6f}",
                "f1_macro": f"{result.f1_macro:.6f}",
                "top1_doc_id": str(top_result.doc_id if top_result else ""),
                "top1_score": f"{top_result.score:.6f}" if top_result else "",
            }
        )

    with (evidence_dir / "tf_variant_comparison.csv").open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["tf_variant", "accuracy", "f1_macro", "top1_doc_id", "top1_score"],
        )
        writer.writeheader()
        writer.writerows(rows)
    return rows


def run_pipeline(args: argparse.Namespace) -> dict[str, object]:
    evidence_dir = Path(args.evidence_dir)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    data_home = Path(args.data_home)
    data_home.mkdir(parents=True, exist_ok=True)

    preprocessor = TextPreprocessor()
    texts, tokenized_documents, labels, target_names = load_balanced_20newsgroups(
        preprocessor=preprocessor,
        data_home=data_home,
        categories=CATEGORIES,
        sample_per_class=args.sample_per_class,
        random_state=args.random_state,
    )

    max_error, mean_error, tfidf_shape = validate_tfidf(tokenized_documents, evidence_dir)

    search_engine = SearchEngine.from_documents(texts, preprocessor=preprocessor)
    tfidf_results = search_engine.search(args.query, topk=args.topk)
    write_search_results(
        evidence_dir / "search_results_tfidf.txt",
        "=== TF-IDF 코사인 검색 결과 ===",
        args.query,
        tfidf_results,
    )

    bm25_engine = BM25SearchEngine.from_documents(texts, preprocessor=preprocessor)
    bm25_results = bm25_engine.search(args.query, topk=args.topk)
    write_search_results(
        evidence_dir / "search_results_bm25.txt",
        "=== BM25 검색 결과 ===",
        args.query,
        bm25_results,
    )

    classification_result = train_logistic_regression(
        tokenized_documents,
        labels,
        random_state=args.random_state,
    )
    write_classification_metrics(classification_result, labels, target_names, evidence_dir)
    misclassified_count = analyze_misclassifications(
        texts,
        tokenized_documents,
        target_names,
        classification_result,
        evidence_dir,
    )
    tf_variant_rows = compare_tf_variants(
        tokenized_documents,
        labels,
        texts,
        preprocessor,
        args.query,
        evidence_dir,
        args.random_state,
    )

    summary = {
        "documents": len(texts),
        "categories": target_names,
        "sample_per_class": args.sample_per_class,
        "query": args.query,
        "topk": args.topk,
        "tfidf_shape": list(tfidf_shape),
        "tfidf_max_error": max_error,
        "tfidf_mean_error": mean_error,
        "classification_accuracy": classification_result.accuracy,
        "classification_f1_macro": classification_result.f1_macro,
        "misclassified_count": misclassified_count,
        "tf_variants": tf_variant_rows,
    }
    (evidence_dir / "run_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("=== Pipeline complete ===")
    print(f"Documents: {len(texts)}")
    print(f"TF-IDF validation max error: {max_error:.12e}")
    print(f"Accuracy: {classification_result.accuracy:.6f}")
    print(f"F1 macro: {classification_result.f1_macro:.6f}")
    print(f"Evidence directory: {evidence_dir}")
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run NLP document search and classification pipeline.")
    parser.add_argument("--query", default="space shuttle nasa mission", help="Search query.")
    parser.add_argument("--topk", type=int, default=5, help="Number of search results to return.")
    parser.add_argument("--sample-per-class", type=int, default=200, help="Balanced samples per category.")
    parser.add_argument("--random-state", type=int, default=42, help="Random seed.")
    parser.add_argument("--data-home", default="data", help="Dataset cache directory.")
    parser.add_argument("--evidence-dir", default="evidence", help="Output directory for logs and figures.")
    return parser


if __name__ == "__main__":
    run_pipeline(build_parser().parse_args())
