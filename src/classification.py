"""TF-IDF based document classification utilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score
from sklearn.model_selection import train_test_split

from src.tfidf import NumpyTfidfVectorizer


@dataclass
class ClassificationResult:
    model: LogisticRegression
    vectorizer: NumpyTfidfVectorizer
    train_indices: np.ndarray
    test_indices: np.ndarray
    y_test: np.ndarray
    y_pred: np.ndarray
    accuracy: float
    f1_macro: float
    confusion_matrix: np.ndarray


def train_logistic_regression(
    tokenized_documents: list[list[str]],
    labels: Iterable[int],
    random_state: int = 42,
    test_size: float = 0.2,
    tf_variant: str = "raw",
) -> ClassificationResult:
    y = np.asarray(list(labels), dtype=int)
    indices = np.arange(len(tokenized_documents))
    train_indices, test_indices = train_test_split(
        indices,
        test_size=test_size,
        random_state=random_state,
        stratify=y,
    )

    train_docs = [tokenized_documents[index] for index in train_indices]
    test_docs = [tokenized_documents[index] for index in test_indices]

    vectorizer = NumpyTfidfVectorizer(tf_variant=tf_variant)
    x_train = vectorizer.fit_transform(train_docs)
    x_test = vectorizer.transform(test_docs)

    model = LogisticRegression(
        max_iter=1000,
        random_state=random_state,
        class_weight="balanced",
    )
    model.fit(x_train, y[train_indices])
    y_pred = model.predict(x_test)
    labels_sorted = np.unique(y)

    return ClassificationResult(
        model=model,
        vectorizer=vectorizer,
        train_indices=train_indices,
        test_indices=test_indices,
        y_test=y[test_indices],
        y_pred=y_pred,
        accuracy=float(accuracy_score(y[test_indices], y_pred)),
        f1_macro=float(f1_score(y[test_indices], y_pred, average="macro")),
        confusion_matrix=confusion_matrix(y[test_indices], y_pred, labels=labels_sorted),
    )
