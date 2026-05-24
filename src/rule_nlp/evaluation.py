"""Evaluation helpers for extraction and sentiment experiments."""

from __future__ import annotations

from collections import Counter
from typing import Iterable, Sequence


def compute_binary_metrics(
    y_true: Sequence[str],
    y_pred: Sequence[str],
    positive_label: str = "positive",
) -> dict[str, float]:
    if len(y_true) != len(y_pred):
        raise ValueError("y_true and y_pred must have the same length")
    if not y_true:
        raise ValueError("at least one label is required")

    tp = sum(1 for true, pred in zip(y_true, y_pred) if true == positive_label and pred == positive_label)
    fp = sum(1 for true, pred in zip(y_true, y_pred) if true != positive_label and pred == positive_label)
    fn = sum(1 for true, pred in zip(y_true, y_pred) if true == positive_label and pred != positive_label)
    correct = sum(1 for true, pred in zip(y_true, y_pred) if true == pred)

    precision = _safe_divide(tp, tp + fp)
    recall = _safe_divide(tp, tp + fn)
    f1 = _safe_divide(2 * precision * recall, precision + recall)
    return {
        "accuracy": round(correct / len(y_true), 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "support": len(y_true),
    }


def compute_extraction_metrics(
    gold_items: Iterable[object],
    predicted_items: Iterable[object],
) -> dict[str, float]:
    gold_counter = Counter(gold_items)
    predicted_counter = Counter(predicted_items)
    true_positive = sum((gold_counter & predicted_counter).values())
    false_positive = sum((predicted_counter - gold_counter).values())
    false_negative = sum((gold_counter - predicted_counter).values())
    precision = _safe_divide(true_positive, true_positive + false_positive)
    recall = _safe_divide(true_positive, true_positive + false_negative)
    f1 = _safe_divide(2 * precision * recall, precision + recall)
    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "tp": true_positive,
        "fp": false_positive,
        "fn": false_negative,
    }


def _safe_divide(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0
