"""Run the full e-commerce multimodal EDA and RFM pipeline."""

from __future__ import annotations

import argparse
import io
import json
import sys
import zipfile
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline import DataAnalyzer


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run e-commerce multimodal EDA and RFM analysis.")
    parser.add_argument("--dataset", default="carrie1/ecommerce-data", help="Kaggle dataset slug.")
    parser.add_argument("--data-dir", default="data/ecommerce", type=Path, help="Directory for raw data.")
    parser.add_argument("--input-csv", default=None, type=Path, help="Use an existing CSV instead of Kaggle lookup.")
    parser.add_argument("--evidence-dir", default="evidence", type=Path, help="Directory for generated evidence files.")
    parser.add_argument("--notebook", default="notebooks/analysis_report.ipynb", type=Path, help="Notebook output path.")
    parser.add_argument("--max-rows", default=0, type=int, help="0 means full dataset; otherwise read this many rows.")
    parser.add_argument("--iqr-threshold", default=1.5, type=float, help="IQR outlier threshold.")
    parser.add_argument("--skip-download", action="store_true", help="Do not call Kaggle; fail if CSV is absent.")
    return parser.parse_args()


def resolve_data_file(data_dir: Path, dataset_slug: str, input_csv: Path | None, skip_download: bool) -> Path:
    data_dir = resolve_path(data_dir)
    if input_csv is not None:
        path = resolve_path(input_csv)
        if path.exists():
            return path
        raise FileNotFoundError(f"Input CSV not found: {path}")

    data_dir.mkdir(parents=True, exist_ok=True)
    existing = sorted(data_dir.glob("*.csv"), key=lambda p: p.stat().st_size, reverse=True)
    if existing:
        return existing[0]

    if skip_download:
        raise FileNotFoundError(f"No CSV found in {data_dir}; rerun without --skip-download or pass --input-csv.")

    try:
        import kaggle
    except ImportError as exc:
        raise RuntimeError("kaggle package is required for automatic download. Run `pip install kaggle`.") from exc

    kaggle.api.authenticate()
    kaggle.api.dataset_download_files(dataset_slug, path=str(data_dir), unzip=False)
    for archive in data_dir.glob("*.zip"):
        with zipfile.ZipFile(archive) as zip_file:
            zip_file.extractall(data_dir)
    downloaded = sorted(data_dir.glob("*.csv"), key=lambda p: p.stat().st_size, reverse=True)
    if not downloaded:
        raise FileNotFoundError(f"Kaggle dataset {dataset_slug} did not contain a CSV file.")
    return downloaded[0]


def resolve_path(path: Path | str) -> Path:
    path = Path(path)
    return path if path.is_absolute() else PROJECT_ROOT / path


def capture_basic_eda(df: pd.DataFrame, evidence_dir: Path) -> dict[str, object]:
    info_buffer = io.StringIO()
    df.info(buf=info_buffer)
    describe = df.describe(include="all").transpose()

    (evidence_dir / "head.csv").write_text(df.head(10).to_csv(index=False), encoding="utf-8")
    (evidence_dir / "info.txt").write_text(info_buffer.getvalue(), encoding="utf-8")
    describe.to_csv(evidence_dir / "describe.csv", encoding="utf-8-sig")

    return {
        "row_count": int(len(df)),
        "column_count": int(len(df.columns)),
        "columns": list(df.columns),
        "info": info_buffer.getvalue(),
        "describe_path": "evidence/describe.csv",
    }


def build_plots(df: pd.DataFrame, rfm: pd.DataFrame, corr: pd.DataFrame, evidence_dir: Path) -> list[str]:
    sns.set_theme(style="whitegrid")
    paths: list[str] = []

    hist_df = df[pd.to_numeric(df["unit_price_capped"], errors="coerce").notna()]
    fig, ax = plt.subplots(figsize=(9, 5))
    sns.histplot(hist_df["unit_price_capped"], bins=50, kde=True, ax=ax, color="#2a6f97")
    ax.set_title("Unit Price Distribution After IQR Capping")
    ax.set_xlabel("Unit price capped")
    ax.set_ylabel("Transaction count")
    paths.append(save_figure(fig, evidence_dir / "histogram_unit_price.png"))

    box_df = df[["unit_price", "unit_price_capped"]].rename(
        columns={"unit_price": "Before", "unit_price_capped": "After"}
    )
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.boxplot(data=box_df.melt(var_name="Stage", value_name="Unit price"), x="Stage", y="Unit price", ax=ax)
    ax.set_title("Unit Price Outlier Treatment Before vs After")
    ax.set_xlabel("Treatment stage")
    ax.set_ylabel("Unit price")
    paths.append(save_figure(fig, evidence_dir / "boxplot_outlier_before_after.png"))

    segment_counts = rfm["segment"].value_counts().rename_axis("segment").reset_index(name="customers")
    fig, ax = plt.subplots(figsize=(9, 5))
    sns.barplot(data=segment_counts, x="segment", y="customers", ax=ax, palette="deep", hue="segment", legend=False)
    ax.set_title("RFM Segment Customer Counts")
    ax.set_xlabel("RFM segment")
    ax.set_ylabel("Customer count")
    ax.tick_params(axis="x", rotation=20)
    paths.append(save_figure(fig, evidence_dir / "bar_rfm_segments.png"))

    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="vlag", center=0, ax=ax)
    ax.set_title("Numeric Feature Correlation Matrix")
    ax.set_xlabel("Feature")
    ax.set_ylabel("Feature")
    paths.append(save_figure(fig, evidence_dir / "heatmap_correlation.png"))

    scatter_df = df.sample(min(5000, len(df)), random_state=42) if len(df) > 5000 else df
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.scatterplot(
        data=scatter_df,
        x="image_mean",
        y="unit_price_capped",
        hue="category",
        alpha=0.55,
        linewidth=0,
        ax=ax,
    )
    ax.set_title("Image Mean vs Unit Price")
    ax.set_xlabel("Image mean")
    ax.set_ylabel("Unit price capped")
    ax.legend(title="Category", bbox_to_anchor=(1.02, 1), loc="upper left")
    paths.append(save_figure(fig, evidence_dir / "scatter_image_mean_price.png"))

    positive = df[(df["amount"] > 0) & df["order_date"].notna()].copy()
    monthly = positive.groupby(positive["order_date"].dt.to_period("M"))["amount"].sum()
    monthly.index = monthly.index.astype(str)
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.lineplot(x=monthly.index, y=monthly.values, marker="o", ax=ax, color="#c44e52")
    ax.set_title("Monthly Revenue Trend")
    ax.set_xlabel("Order month")
    ax.set_ylabel("Revenue")
    ax.tick_params(axis="x", rotation=35)
    paths.append(save_figure(fig, evidence_dir / "line_monthly_revenue.png"))

    retention = calculate_cohort_retention(df)
    if not retention.empty:
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.heatmap(retention, annot=True, fmt=".0%", cmap="YlGnBu", vmin=0, vmax=1, ax=ax)
        ax.set_title("Cohort Retention Rate")
        ax.set_xlabel("Months since first purchase")
        ax.set_ylabel("First purchase cohort")
        paths.append(save_figure(fig, evidence_dir / "bonus_cohort_retention_heatmap.png"))
        retention.to_csv(evidence_dir / "bonus_cohort_retention.csv", encoding="utf-8-sig")

    return paths


def save_figure(fig: plt.Figure, path: Path) -> str:
    fig.tight_layout()
    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)
    return str(path.relative_to(PROJECT_ROOT)).replace("\\", "/")


def calculate_cohort_retention(df: pd.DataFrame) -> pd.DataFrame:
    required = {"customer_id", "order_date", "amount"}
    if not required.issubset(df.columns):
        return pd.DataFrame()
    work = df[(df["amount"] > 0) & df["customer_id"].notna() & df["order_date"].notna()].copy()
    if work.empty:
        return pd.DataFrame()
    work["order_month"] = work["order_date"].dt.to_period("M")
    work["cohort_month"] = work.groupby("customer_id")["order_month"].transform("min")
    work["cohort_index"] = (
        (work["order_month"].dt.year - work["cohort_month"].dt.year) * 12
        + (work["order_month"].dt.month - work["cohort_month"].dt.month)
        + 1
    )
    cohorts = work.groupby(["cohort_month", "cohort_index"])["customer_id"].nunique().unstack(fill_value=0)
    if cohorts.empty:
        return pd.DataFrame()
    retention = cohorts.divide(cohorts.iloc[:, 0], axis=0)
    retention.index = retention.index.astype(str)
    return retention


def summarize_results(
    df: pd.DataFrame,
    missing_before: pd.Series,
    missing_after: pd.Series,
    outlier_count: int,
    outlier_bounds: dict[str, float],
    numeric_summary: pd.DataFrame,
    corr: pd.DataFrame,
    rfm: pd.DataFrame,
    plot_paths: list[str],
    data_file: Path,
    evidence_dir: Path,
) -> dict[str, object]:
    segment_summary = (
        rfm.groupby("segment")
        .agg(
            customers=("segment", "size"),
            avg_recency=("recency", "mean"),
            avg_frequency=("frequency", "mean"),
            avg_monetary=("monetary", "mean"),
            total_monetary=("monetary", "sum"),
        )
        .sort_values("customers", ascending=False)
    )
    segment_summary["customer_share"] = segment_summary["customers"] / segment_summary["customers"].sum()
    segment_summary["revenue_share"] = segment_summary["total_monetary"] / segment_summary["total_monetary"].sum()
    segment_summary.to_csv(evidence_dir / "rfm_segment_summary.csv", encoding="utf-8-sig")
    rfm.to_csv(evidence_dir / "rfm_customers.csv", encoding="utf-8-sig")
    numeric_summary.to_csv(evidence_dir / "numeric_summary.csv", encoding="utf-8-sig")
    corr.to_csv(evidence_dir / "correlation_matrix.csv", encoding="utf-8-sig")

    high_corr = corr.where(~np.eye(len(corr), dtype=bool)).stack().sort_values(key=lambda s: s.abs(), ascending=False)
    corr_pairs = [
        {"pair": f"{left}-{right}", "correlation": float(value)}
        for (left, right), value in high_corr.drop_duplicates().head(5).items()
    ]
    top_segment = segment_summary.iloc[0]
    vip = segment_summary.loc["VIP"] if "VIP" in segment_summary.index else None
    churned = segment_summary.loc["Churned"] if "Churned" in segment_summary.index else None
    loyal = segment_summary.loc["Loyal"] if "Loyal" in segment_summary.index else None
    new = segment_summary.loc["New"] if "New" in segment_summary.index else None

    summary = {
        "data_file": str(data_file.relative_to(PROJECT_ROOT)).replace("\\", "/")
        if data_file.is_relative_to(PROJECT_ROOT)
        else str(data_file),
        "row_count": int(len(df)),
        "column_count": int(len(df.columns)),
        "order_start": str(df["order_date"].min().date()),
        "order_end": str(df["order_date"].max().date()),
        "customers": int(rfm.shape[0]),
        "missing_before_total": int(missing_before.sum()),
        "missing_after_total": int(missing_after.sum()),
        "unit_price_outliers": int(outlier_count),
        "unit_price_outlier_rate": float(outlier_count / len(df)),
        "outlier_bounds": outlier_bounds,
        "unit_price_mean": float(numeric_summary.loc["unit_price", "mean"]),
        "unit_price_median": float(numeric_summary.loc["unit_price", "median"]),
        "amount_mean": float(numeric_summary.loc["amount", "mean"]),
        "amount_q3": float(numeric_summary.loc["amount", "q3"]),
        "image_mean_avg": float(numeric_summary.loc["image_mean", "mean"]),
        "top_segment": {"name": str(top_segment.name), "customers": int(top_segment["customers"])},
        "vip": row_to_dict(vip),
        "churned": row_to_dict(churned),
        "loyal": row_to_dict(loyal),
        "new": row_to_dict(new),
        "segments": {
            str(index): {
                "customers": int(row["customers"]),
                "avg_recency": float(row["avg_recency"]),
                "avg_frequency": float(row["avg_frequency"]),
                "avg_monetary": float(row["avg_monetary"]),
                "customer_share": float(row["customer_share"]),
                "revenue_share": float(row["revenue_share"]),
            }
            for index, row in segment_summary.iterrows()
        },
        "correlation_pairs": corr_pairs,
        "plots": plot_paths,
    }
    (evidence_dir / "analysis_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    write_summary_text(summary, numeric_summary, segment_summary, corr, evidence_dir)
    return summary


def row_to_dict(row: pd.Series | None) -> dict[str, float | int] | None:
    if row is None:
        return None
    return {
        "customers": int(row["customers"]),
        "avg_recency": float(row["avg_recency"]),
        "avg_frequency": float(row["avg_frequency"]),
        "avg_monetary": float(row["avg_monetary"]),
        "customer_share": float(row["customer_share"]),
        "revenue_share": float(row["revenue_share"]),
    }


def write_summary_text(
    summary: dict[str, object],
    numeric_summary: pd.DataFrame,
    segment_summary: pd.DataFrame,
    corr: pd.DataFrame,
    evidence_dir: Path,
) -> None:
    lines = [
        "E-commerce multimodal EDA and RFM evidence",
        f"Rows: {summary['row_count']:,}",
        f"Columns: {summary['column_count']}",
        f"Order range: {summary['order_start']} to {summary['order_end']}",
        f"Customers in RFM: {summary['customers']:,}",
        f"Missing values before/after: {summary['missing_before_total']} -> {summary['missing_after_total']}",
        f"Unit price outliers: {summary['unit_price_outliers']:,} ({summary['unit_price_outlier_rate']:.2%})",
        "",
        "Numeric summary",
        numeric_summary.to_string(),
        "",
        "RFM segment summary",
        segment_summary.to_string(),
        "",
        "Correlation matrix",
        corr.to_string(),
    ]
    (evidence_dir / "run_summary.txt").write_text("\n".join(lines), encoding="utf-8")


def build_notebook(summary: dict[str, object], notebook_path: Path) -> None:
    notebook_path.parent.mkdir(parents=True, exist_ok=True)
    plots = summary["plots"]
    plot_markdown = "\n\n".join([f"![{Path(path).stem}](../{path})" for path in plots])
    notebook = {
        "cells": [
            markdown_cell(
                "# 이커머스 멀티 모달 데이터 분석 및 RFM 리포트\n"
                "\n"
                "UCI Online Retail 거래 데이터를 기반으로 수치형 거래 정보, 상품명 텍스트, "
                "상품 코드/상품명에서 생성한 NumPy 이미지 배열 피처를 하나의 분석 흐름으로 처리한다."
            ),
            code_cell(
                "from pathlib import Path\n"
                "from src.pipeline import DataAnalyzer\n"
                "\n"
                "PROJECT_ROOT = Path.cwd().parent if Path.cwd().name == 'notebooks' else Path.cwd()\n"
                f"analyzer = DataAnalyzer(PROJECT_ROOT / '{summary['data_file']}')\n"
                "df = analyzer.load_data()\n"
                "df.info()\n"
                "df.head()\n"
            ),
            markdown_cell(
                f"데이터는 {summary['row_count']:,}건, {summary['column_count']}개 컬럼으로 구성된다. "
                f"거래 기간은 {summary['order_start']}부터 {summary['order_end']}까지이며, "
                f"RFM 계산에 사용된 고객 수는 {summary['customers']:,}명이다. "
                f"단가 평균은 {summary['unit_price_mean']:.2f}, 중앙값은 {summary['unit_price_median']:.2f}로 "
                "고가 상품과 비정상 입력값이 평균을 끌어올리는 오른쪽 꼬리 분포가 확인된다."
            ),
            code_cell(
                "df.describe(include='all').T\n"
                "missing_before = df.isna().sum()\n"
                "df = analyzer.handle_missing_values(numeric_strategy='group_median', group_col='category')\n"
                "df = analyzer.engineer_multimodal_features(store_arrays=False)\n"
                "outliers, bounds = analyzer.detect_outliers('unit_price')\n"
                "df = analyzer.cap_outliers('unit_price', output_col='unit_price_capped')\n"
                "rfm = analyzer.calculate_rfm()\n"
                "missing_after = df.isna().sum()\n"
                "missing_before, missing_after, bounds, rfm.head()\n"
            ),
            markdown_cell(
                f"IQR 기준 단가 이상치는 {summary['unit_price_outliers']:,}건"
                f"({summary['unit_price_outlier_rate']:.2%})이다. "
                f"결측치는 {summary['missing_before_total']}개에서 {summary['missing_after_total']}개로 감소했다. "
                "상품명 단어 수, 문자열 길이, 이미지 평균, 이미지 표준편차, 엣지 강도는 반복문이 아니라 NumPy/Pandas 벡터 연산으로 산출한다."
            ),
            code_cell(
                "numeric_cols = ['quantity', 'unit_price', 'amount', 'name_word_count', 'image_mean', 'image_std', 'edge_strength']\n"
                "numeric_summary = analyzer.summarize_numeric(numeric_cols)\n"
                "corr = analyzer.correlation_matrix(['quantity', 'unit_price_capped', 'amount', 'name_word_count', 'image_mean', 'image_std', 'edge_strength'])\n"
                "numeric_summary, corr\n"
            ),
            markdown_cell(plot_markdown),
            markdown_cell(
                "RFM 세그먼트별 고객 수, 평균 최근성, 평균 구매 빈도, 평균 구매 금액은 "
                "`evidence/rfm_segment_summary.csv`에 저장했다. "
                "막대그래프는 세그먼트 규모를, 라인차트는 월별 매출 추세를, 히트맵은 수치 피처 간 상관관계와 코호트 유지율을 확인하는 근거로 사용한다."
            ),
        ],
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3.12"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    notebook_path.write_text(json.dumps(notebook, ensure_ascii=False, indent=2), encoding="utf-8")


def markdown_cell(source: str) -> dict[str, object]:
    return {"cell_type": "markdown", "metadata": {}, "source": source.splitlines(keepends=True)}


def code_cell(source: str) -> dict[str, object]:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": source.splitlines(keepends=True),
    }


def main() -> None:
    args = parse_args()
    evidence_dir = resolve_path(args.evidence_dir)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    notebook_path = resolve_path(args.notebook)
    data_file = resolve_data_file(args.data_dir, args.dataset, args.input_csv, args.skip_download)

    nrows = None if args.max_rows == 0 else args.max_rows
    analyzer = DataAnalyzer(data_file)
    df = analyzer.load_data(nrows=nrows)
    basic_eda = capture_basic_eda(df, evidence_dir)
    missing_before = df.isna().sum()

    df = analyzer.handle_missing_values(numeric_strategy="group_median", group_col="category")
    df = analyzer.engineer_multimodal_features(image_size=8, store_arrays=False)
    outliers, outlier_bounds = analyzer.detect_outliers("unit_price", threshold=args.iqr_threshold)
    df = analyzer.cap_outliers("unit_price", threshold=args.iqr_threshold, output_col="unit_price_capped")
    if {"quantity", "unit_price_capped"}.issubset(df.columns):
        df["amount_capped"] = df["quantity"] * df["unit_price_capped"]
        analyzer.df = df
    missing_after = df.isna().sum()

    numeric_cols = ["quantity", "unit_price", "amount", "name_word_count", "image_mean", "image_std", "edge_strength"]
    numeric_summary = analyzer.summarize_numeric(numeric_cols)
    corr_cols = ["quantity", "unit_price_capped", "amount", "name_word_count", "image_mean", "image_std", "edge_strength"]
    corr = analyzer.correlation_matrix(corr_cols)
    rfm = analyzer.calculate_rfm(amount_col="amount")

    plot_paths = build_plots(df, rfm, corr, evidence_dir)
    summary = summarize_results(
        df=df,
        missing_before=missing_before,
        missing_after=missing_after,
        outlier_count=len(outliers),
        outlier_bounds=outlier_bounds,
        numeric_summary=numeric_summary,
        corr=corr,
        rfm=rfm,
        plot_paths=plot_paths,
        data_file=data_file,
        evidence_dir=evidence_dir,
    )
    summary["basic_eda"] = basic_eda
    (evidence_dir / "analysis_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    build_notebook(summary, notebook_path)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
