from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from sklearn.metrics import ConfusionMatrixDisplay, RocCurveDisplay, confusion_matrix
from sklearn.model_selection import train_test_split

from src.finance_risk.data import (
    CLASSIFICATION_TARGET,
    FEATURE_COLUMNS,
    RANDOM_STATE,
    REGRESSION_TARGET,
    load_finance_data,
)
from src.finance_risk.modeling import (
    ALPHAS,
    FittedRegressionModel,
    build_classifier_search,
    build_logistic_pipeline,
    build_regression_pipeline,
    coefficient_frame,
    evaluate_classification,
    evaluate_regression,
    get_transformed_feature_names,
    predict_rule_based,
)


def run_experiment(
    data_path: str | Path = "finance_data.csv",
    evidence_dir: str | Path = "evidence",
    fast: bool = False,
) -> dict[str, Any]:
    data_path = Path(data_path)
    evidence_dir = Path(evidence_dir)
    evidence_dir.mkdir(parents=True, exist_ok=True)

    df = load_finance_data(data_path)
    X = df[FEATURE_COLUMNS]
    y_regression = df[REGRESSION_TARGET]
    y_classification = df[CLASSIFICATION_TARGET]

    (
        X_train,
        X_test,
        y_class_train,
        y_class_test,
        y_reg_train,
        y_reg_test,
    ) = train_test_split(
        X,
        y_classification,
        y_regression,
        test_size=0.2,
        stratify=y_classification,
        random_state=RANDOM_STATE,
    )

    classification_table, rf_search = _run_classification(
        X_train=X_train,
        X_test=X_test,
        y_train=y_class_train,
        y_test=y_class_test,
        evidence_dir=evidence_dir,
        fast=fast,
    )
    regression_table, regression_coefficients = _run_regression(
        X_train=X_train,
        X_test=X_test,
        y_train=y_reg_train,
        y_test=y_reg_test,
        evidence_dir=evidence_dir,
    )
    feature_importance = _save_feature_importance(rf_search.best_estimator_, evidence_dir)

    split_summary = {
        "train_rows": int(len(X_train)),
        "test_rows": int(len(X_test)),
        "test_size": 0.2,
        "stratified_by": CLASSIFICATION_TARGET,
        "random_state": RANDOM_STATE,
        "classification_train_positive_rate": float(y_class_train.mean()),
        "classification_test_positive_rate": float(y_class_test.mean()),
    }
    result = {
        "dataset": {
            "samples": int(len(df)),
            "features": FEATURE_COLUMNS,
            "overdue_rate": float(df[CLASSIFICATION_TARGET].mean()),
            "credit_score_min": float(df[REGRESSION_TARGET].min()),
            "credit_score_max": float(df[REGRESSION_TARGET].max()),
        },
        "split": split_summary,
        "best_random_forest_params": rf_search.best_params_,
        "best_random_forest_cv_auc": float(rf_search.best_score_),
        "classification": classification_table,
        "regression": regression_table,
        "feature_importance": feature_importance,
    }

    _write_json(evidence_dir / "metrics.json", result)
    _write_markdown_table(
        evidence_dir / "classification_comparison.md",
        classification_table,
        title="분류 모델 성능 비교",
    )
    _write_markdown_table(
        evidence_dir / "regression_metrics.md",
        regression_table,
        title="회귀 모델 성능 비교",
    )
    return result


def _run_classification(
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
    y_train: pd.Series,
    y_test: pd.Series,
    evidence_dir: Path,
    fast: bool,
) -> tuple[pd.DataFrame, Any]:
    baseline_pred = predict_rule_based(X_test)
    baseline_metrics = evaluate_classification(
        "규칙 기반 베이스라인",
        y_true=y_test,
        y_pred=baseline_pred,
        y_score=baseline_pred,
    )

    logistic_model = build_logistic_pipeline()
    logistic_model.fit(X_train, y_train)
    logistic_pred = logistic_model.predict(X_test)
    logistic_score = logistic_model.predict_proba(X_test)[:, 1]
    logistic_metrics = evaluate_classification(
        "Logistic Regression (balanced)",
        y_true=y_test,
        y_pred=logistic_pred,
        y_score=logistic_score,
    )

    rf_search = build_classifier_search(fast=fast, cv=3 if fast else 5)
    rf_search.fit(X_train, y_train)
    rf_pred = rf_search.predict(X_test)
    rf_score = rf_search.predict_proba(X_test)[:, 1]
    rf_metrics = evaluate_classification(
        "Random Forest (GridSearchCV)",
        y_true=y_test,
        y_pred=rf_pred,
        y_score=rf_score,
    )

    classification_table = pd.DataFrame(
        [baseline_metrics, logistic_metrics, rf_metrics]
    ).sort_values("auc", ascending=False)
    classification_table.to_csv(evidence_dir / "classification_comparison.csv", index=False)
    _save_confusion_matrix(y_test, rf_pred, evidence_dir)
    _save_roc_curve(y_test, rf_score, evidence_dir, auc_value=rf_metrics["auc"])
    return classification_table, rf_search


def _run_regression(
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
    y_train: pd.Series,
    y_test: pd.Series,
    evidence_dir: Path,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    fitted_models: list[FittedRegressionModel] = []
    metric_rows = []
    for model_name in ["Ridge", "Lasso"]:
        for alpha in ALPHAS:
            pipeline = build_regression_pipeline(model_name, alpha)
            pipeline.fit(X_train, y_train)
            prediction = pipeline.predict(X_test)
            prediction = prediction.clip(0, 1000)
            metrics = evaluate_regression(model_name, alpha, y_test, prediction)
            metric_rows.append(metrics)
            fitted_models.append(
                FittedRegressionModel(
                    model_name=model_name,
                    alpha=alpha,
                    pipeline=pipeline,
                    metrics=metrics,
                )
            )

    regression_table = pd.DataFrame(metric_rows).sort_values(["rmse", "mae"])
    regression_coefficients = coefficient_frame(fitted_models)
    regression_table.to_csv(evidence_dir / "regression_metrics.csv", index=False)
    regression_coefficients.to_csv(evidence_dir / "regression_coefficients.csv", index=False)
    _save_regression_coefficient_plot(regression_coefficients, evidence_dir)
    return regression_table, regression_coefficients


def _save_confusion_matrix(y_true: pd.Series, y_pred: pd.Series, evidence_dir: Path) -> None:
    matrix = confusion_matrix(y_true, y_pred)
    display = ConfusionMatrixDisplay(matrix, display_labels=["Normal", "Overdue"])
    fig, ax = plt.subplots(figsize=(5.5, 4.5))
    display.plot(ax=ax, cmap="Blues", colorbar=False, values_format="d")
    ax.set_title("Random Forest Confusion Matrix")
    fig.tight_layout()
    fig.savefig(evidence_dir / "classification_confusion_matrix.png", dpi=160)
    plt.close(fig)


def _save_roc_curve(
    y_true: pd.Series,
    y_score: pd.Series,
    evidence_dir: Path,
    auc_value: float,
) -> None:
    fig, ax = plt.subplots(figsize=(6, 4.5))
    RocCurveDisplay.from_predictions(y_true, y_score, ax=ax, name="Random Forest")
    ax.plot([0, 1], [0, 1], linestyle="--", color="gray", linewidth=1)
    ax.set_title(f"ROC-AUC Curve (AUC={auc_value:.3f})")
    fig.tight_layout()
    fig.savefig(evidence_dir / "classification_roc_curve.png", dpi=160)
    plt.close(fig)


def _save_regression_coefficient_plot(coefficients: pd.DataFrame, evidence_dir: Path) -> None:
    plot_data = coefficients[coefficients["feature"].isin(FEATURE_COLUMNS)].copy()
    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.8), sharey=True)
    for ax, model_name in zip(axes, ["Ridge", "Lasso"]):
        model_data = plot_data[plot_data["model"] == model_name]
        sns.lineplot(
            data=model_data,
            x="alpha",
            y="coefficient",
            hue="feature",
            marker="o",
            ax=ax,
        )
        ax.set_xscale("log")
        ax.set_title(f"{model_name} coefficients by alpha")
        ax.set_xlabel("alpha")
        ax.set_ylabel("standardized coefficient")
    handles, labels = axes[0].get_legend_handles_labels()
    axes[0].legend_.remove()
    axes[1].legend_.remove()
    fig.legend(handles, labels, loc="lower center", ncol=3)
    fig.tight_layout(rect=[0, 0.12, 1, 1])
    fig.savefig(evidence_dir / "regression_coefficients.png", dpi=160)
    plt.close(fig)


def _save_feature_importance(fitted_pipeline: Any, evidence_dir: Path) -> pd.DataFrame:
    features = get_transformed_feature_names(fitted_pipeline)
    importances = fitted_pipeline.named_steps["model"].feature_importances_
    importance_table = (
        pd.DataFrame({"feature": features, "importance": importances})
        .sort_values("importance", ascending=False)
        .reset_index(drop=True)
    )
    importance_table.to_csv(evidence_dir / "feature_importance.csv", index=False)

    top_features = importance_table.head(12).sort_values("importance")
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(7.5, 5.2))
    ax.barh(top_features["feature"], top_features["importance"], color="#2f6f73")
    ax.set_title("Random Forest Feature Importance Top 12")
    ax.set_xlabel("importance")
    ax.set_ylabel("")
    fig.tight_layout()
    fig.savefig(evidence_dir / "feature_importance.png", dpi=160)
    plt.close(fig)
    return importance_table


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    def default(value: Any) -> Any:
        if isinstance(value, pd.DataFrame):
            return value.to_dict(orient="records")
        if hasattr(value, "item"):
            return value.item()
        raise TypeError(f"object of type {type(value).__name__} is not JSON serializable")

    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=default), encoding="utf-8")


def _write_markdown_table(path: Path, table: pd.DataFrame, title: str) -> None:
    rounded = table.copy()
    for column in rounded.select_dtypes(include="number").columns:
        rounded[column] = rounded[column].map(lambda value: f"{value:.4f}")
    lines = [f"# {title}", ""]
    lines.append("| " + " | ".join(rounded.columns) + " |")
    lines.append("| " + " | ".join(["---"] * len(rounded.columns)) + " |")
    for _, row in rounded.iterrows():
        lines.append("| " + " | ".join(str(value) for value in row) + " |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
