from pathlib import Path

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.model_selection import GridSearchCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src.finance_risk.data import FEATURE_COLUMNS, generate_finance_data
from src.finance_risk.experiment import run_experiment
from src.finance_risk.modeling import (
    RULE_DESCRIPTIONS,
    build_classifier_search,
    build_preprocessor,
    rule_based_predict,
)


def test_generate_finance_data_matches_required_schema_and_imbalance(tmp_path):
    output_path = tmp_path / "finance_data.csv"

    df = generate_finance_data(output_path=output_path, n_samples=10_000, random_state=42)

    assert output_path.exists()
    assert len(df) == 10_000
    assert list(df.columns) == [
        "age",
        "annual_income",
        "spending_score",
        "debt_ratio",
        "credit_card_count",
        "overdue_count_6m",
        "credit_score",
        "is_overdue",
    ]
    assert df["credit_score"].between(0, 1000).all()
    assert 0.10 <= df["is_overdue"].mean() <= 0.15


def test_rule_based_baseline_has_at_least_five_rules_and_binary_predictions():
    high_risk = pd.Series(
        {
            "age": 24,
            "annual_income": 1800,
            "spending_score": 95,
            "debt_ratio": 0.88,
            "credit_card_count": 9,
            "overdue_count_6m": 3,
        }
    )
    low_risk = pd.Series(
        {
            "age": 45,
            "annual_income": 9000,
            "spending_score": 40,
            "debt_ratio": 0.15,
            "credit_card_count": 2,
            "overdue_count_6m": 0,
        }
    )

    assert len(RULE_DESCRIPTIONS) >= 5
    assert rule_based_predict(high_risk) == 1
    assert rule_based_predict(low_risk) == 0


def test_preprocessor_uses_train_fit_components_for_numeric_and_categorical_data():
    preprocessor = build_preprocessor()

    assert isinstance(preprocessor, Pipeline)
    column_transformer = preprocessor.named_steps["preprocess"]
    assert isinstance(column_transformer, ColumnTransformer)

    transformer_names = {name for name, _, _ in column_transformer.transformers}
    assert {"numeric", "categorical"} <= transformer_names

    transformers = {name: transformer for name, transformer, _ in column_transformer.transformers}
    numeric_pipeline = transformers["numeric"]
    categorical_pipeline = transformers["categorical"]
    assert any(isinstance(step, SimpleImputer) for _, step in numeric_pipeline.steps)
    assert any(isinstance(step, StandardScaler) for _, step in numeric_pipeline.steps)
    assert any(isinstance(step, SimpleImputer) for _, step in categorical_pipeline.steps)
    assert any(isinstance(step, OneHotEncoder) for _, step in categorical_pipeline.steps)


def test_classifier_search_uses_balanced_random_forest_and_limited_grid():
    search = build_classifier_search()

    assert isinstance(search, GridSearchCV)
    assert search.cv == 5
    total_combinations = 1
    for values in search.param_grid.values():
        assert len(values) <= 5
        total_combinations *= len(values)
    assert total_combinations <= 100

    classifier = search.estimator.named_steps["model"]
    assert classifier.class_weight == "balanced"


def test_run_experiment_writes_expected_evidence_files(tmp_path):
    data_path = tmp_path / "finance_data.csv"
    evidence_dir = tmp_path / "evidence"
    generate_finance_data(output_path=data_path, n_samples=1_000, random_state=42)

    results = run_experiment(data_path=data_path, evidence_dir=evidence_dir, fast=True)

    assert results["dataset"]["samples"] == 1_000
    expected_files = {
        "metrics.json",
        "classification_comparison.csv",
        "regression_metrics.csv",
        "regression_coefficients.csv",
        "classification_confusion_matrix.png",
        "classification_roc_curve.png",
        "regression_coefficients.png",
        "feature_importance.png",
    }
    assert expected_files <= {path.name for path in evidence_dir.iterdir()}
    assert set(FEATURE_COLUMNS) <= set(results["feature_importance"]["feature"].tolist())


def test_readme_covers_required_decision_rationale_and_operational_tradeoffs():
    readme = Path("README.md").read_text(encoding="utf-8")
    required_phrases = [
        "python data_gen.py",
        "finance_data.csv",
        "10,000",
        "규칙 기반 베이스라인",
        "Pipeline",
        "ColumnTransformer",
        "데이터 누수",
        'class_weight="balanced"',
        "혼동 행렬",
        "ROC-AUC",
        "Ridge와 Lasso",
        "alpha 후보 `0.01, 0.1, 1, 10, 100`",
        "GridSearchCV",
        "앙상블은",
        "편향",
        "분산",
        "성능과 예측 속도",
        "성능 우선",
        "오탐",
        "미탐",
    ]

    missing_phrases = [phrase for phrase in required_phrases if phrase not in readme]

    assert not missing_phrases
