from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Lasso, LogisticRegression, Ridge
from sklearn.metrics import (
    accuracy_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    recall_score,
    roc_auc_score,
    r2_score,
    f1_score,
)
from sklearn.model_selection import GridSearchCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src.finance_risk.data import FEATURE_COLUMNS, RANDOM_STATE

ALPHAS = [0.01, 0.1, 1, 10, 100]
NUMERIC_COLUMNS = FEATURE_COLUMNS
CATEGORICAL_COLUMNS = ["income_band", "debt_level", "age_band"]

RULE_DESCRIPTIONS = [
    "최근 6개월 연체 횟수가 3회 이상이면 고위험으로 판단",
    "부채 비율이 75% 이상이고 연 소득이 5,000만원 미만이면 고위험으로 판단",
    "연 소득이 2,500만원 미만이고 최근 연체가 1회 이상이면 고위험으로 판단",
    "신용카드가 8개 이상이고 소비 점수가 80점 이상이면 고위험으로 판단",
    "부채 비율이 60% 이상이고 신용카드가 7개 이상이면 고위험으로 판단",
    "30세 미만 고객이면서 부채 비율이 70% 이상이고 소비 점수가 70점 이상이면 고위험으로 판단",
]


class CustomerRiskFeatureAdder(BaseEstimator, TransformerMixin):
    """Add categorical risk bands without fitting on test data."""

    def fit(self, X: pd.DataFrame, y: object = None) -> "CustomerRiskFeatureAdder":
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        transformed = X.copy()
        transformed["income_band"] = pd.cut(
            transformed["annual_income"],
            bins=[-np.inf, 3000, 7000, np.inf],
            labels=["low", "middle", "high"],
        ).astype("object")
        transformed["debt_level"] = pd.cut(
            transformed["debt_ratio"],
            bins=[-np.inf, 0.3, 0.7, np.inf],
            labels=["low", "middle", "high"],
        ).astype("object")
        transformed["age_band"] = pd.cut(
            transformed["age"],
            bins=[19, 29, 44, 59, np.inf],
            labels=["20s", "30_40s", "45_50s", "60s"],
        ).astype("object")
        return transformed


def make_one_hot_encoder() -> OneHotEncoder:
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", sparse=False)


def build_preprocessor() -> Pipeline:
    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", make_one_hot_encoder()),
        ]
    )
    column_transformer = ColumnTransformer(
        transformers=[
            ("numeric", numeric_pipeline, NUMERIC_COLUMNS),
            ("categorical", categorical_pipeline, CATEGORICAL_COLUMNS),
        ],
        remainder="drop",
        verbose_feature_names_out=False,
    )
    return Pipeline(
        steps=[
            ("feature_engineering", CustomerRiskFeatureAdder()),
            ("preprocess", column_transformer),
        ]
    )


def rule_based_predict(row: pd.Series) -> int:
    if row["overdue_count_6m"] >= 3:
        return 1
    if row["debt_ratio"] >= 0.75 and row["annual_income"] < 5000:
        return 1
    if row["annual_income"] < 2500 and row["overdue_count_6m"] >= 1:
        return 1
    if row["credit_card_count"] >= 8 and row["spending_score"] >= 80:
        return 1
    if row["debt_ratio"] >= 0.60 and row["credit_card_count"] >= 7:
        return 1
    if row["age"] < 30 and row["debt_ratio"] >= 0.70 and row["spending_score"] >= 70:
        return 1
    return 0


def predict_rule_based(X: pd.DataFrame) -> np.ndarray:
    return X.apply(rule_based_predict, axis=1).to_numpy()


def build_regression_pipeline(model_type: str, alpha: float) -> Pipeline:
    if model_type == "Ridge":
        model = Ridge(alpha=alpha, random_state=RANDOM_STATE)
    elif model_type == "Lasso":
        model = Lasso(alpha=alpha, random_state=RANDOM_STATE, max_iter=20_000)
    else:
        raise ValueError(f"unknown regression model type: {model_type}")
    return Pipeline(steps=[("preprocess", build_preprocessor()), ("model", model)])


def build_logistic_pipeline() -> Pipeline:
    return Pipeline(
        steps=[
            ("preprocess", build_preprocessor()),
            (
                "model",
                LogisticRegression(
                    class_weight="balanced",
                    max_iter=2_000,
                    random_state=RANDOM_STATE,
                    solver="lbfgs",
                ),
            ),
        ]
    )


def build_classifier_search(fast: bool = False, cv: int = 5) -> GridSearchCV:
    classifier = RandomForestClassifier(
        random_state=RANDOM_STATE,
        class_weight="balanced",
        n_jobs=-1,
    )
    pipeline = Pipeline(steps=[("preprocess", build_preprocessor()), ("model", classifier)])
    if fast:
        param_grid = {
            "model__n_estimators": [80],
            "model__max_depth": [4, None],
            "model__min_samples_leaf": [1, 4],
            "model__max_features": ["sqrt"],
        }
    else:
        param_grid = {
            "model__n_estimators": [80, 120, 160],
            "model__max_depth": [4, 8, None],
            "model__min_samples_leaf": [1, 3, 5],
            "model__max_features": ["sqrt", None],
        }
    return GridSearchCV(
        estimator=pipeline,
        param_grid=param_grid,
        scoring="roc_auc",
        cv=cv,
        n_jobs=-1,
        refit=True,
    )


def evaluate_classification(
    name: str,
    y_true: Iterable[int],
    y_pred: Iterable[int],
    y_score: Iterable[float] | None = None,
) -> dict[str, float | str]:
    y_true_array = np.asarray(y_true)
    y_pred_array = np.asarray(y_pred)
    score = y_pred_array if y_score is None else np.asarray(y_score)
    return {
        "model": name,
        "accuracy": accuracy_score(y_true_array, y_pred_array),
        "precision": precision_score(y_true_array, y_pred_array, zero_division=0),
        "recall": recall_score(y_true_array, y_pred_array, zero_division=0),
        "f1_score": f1_score(y_true_array, y_pred_array, zero_division=0),
        "auc": roc_auc_score(y_true_array, score),
    }


def evaluate_regression(
    name: str,
    alpha: float,
    y_true: Iterable[float],
    y_pred: Iterable[float],
) -> dict[str, float | str]:
    y_true_array = np.asarray(y_true)
    y_pred_array = np.asarray(y_pred)
    return {
        "model": name,
        "alpha": alpha,
        "rmse": float(np.sqrt(mean_squared_error(y_true_array, y_pred_array))),
        "mae": mean_absolute_error(y_true_array, y_pred_array),
        "r2": r2_score(y_true_array, y_pred_array),
    }


def get_transformed_feature_names(fitted_pipeline: Pipeline) -> list[str]:
    preprocess_pipeline = fitted_pipeline.named_steps["preprocess"]
    column_transformer = preprocess_pipeline.named_steps["preprocess"]
    return [str(name) for name in column_transformer.get_feature_names_out()]


@dataclass(frozen=True)
class FittedRegressionModel:
    model_name: str
    alpha: float
    pipeline: Pipeline
    metrics: dict[str, float | str]


def coefficient_frame(fitted_models: list[FittedRegressionModel]) -> pd.DataFrame:
    rows = []
    for fitted in fitted_models:
        features = get_transformed_feature_names(fitted.pipeline)
        coefficients = fitted.pipeline.named_steps["model"].coef_
        for feature, coefficient in zip(features, coefficients):
            rows.append(
                {
                    "model": fitted.model_name,
                    "alpha": fitted.alpha,
                    "feature": feature,
                    "coefficient": float(coefficient),
                }
            )
    return pd.DataFrame(rows)
