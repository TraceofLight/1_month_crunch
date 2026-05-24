import json
from pathlib import Path

from scripts.run import build_notebook


def test_generated_notebook_contains_required_markdown_sections(tmp_path):
    summary = {
        "data_file": "data/ecommerce/data.csv",
        "plots": [
            "evidence/histogram_unit_price.png",
            "evidence/boxplot_outlier_before_after.png",
            "evidence/bar_rfm_segments.png",
            "evidence/heatmap_correlation.png",
            "evidence/scatter_image_mean_price.png",
            "evidence/line_monthly_revenue.png",
        ],
        "row_count": 541909,
        "column_count": 17,
        "order_start": "2010-12-01",
        "order_end": "2011-12-09",
        "customers": 4338,
        "unit_price_mean": 4.61,
        "unit_price_median": 2.08,
        "unit_price_outliers": 39627,
        "unit_price_outlier_rate": 0.0731,
        "missing_before_total": 136534,
        "missing_after_total": 135080,
        "correlation_pairs": [
            {"pair": "quantity-amount", "correlation": 0.887},
            {"pair": "edge_strength-image_std", "correlation": 0.235},
        ],
        "segments": {
            "VIP": {
                "customers": 945,
                "avg_recency": 11.5,
                "avg_frequency": 11.16,
                "avg_monetary": 6077.30,
                "customer_share": 0.218,
                "revenue_share": 0.644,
            },
            "Churned": {
                "customers": 1564,
                "avg_recency": 193.9,
                "avg_frequency": 1.98,
                "avg_monetary": 567.50,
                "customer_share": 0.361,
                "revenue_share": 0.100,
            },
        },
    }

    notebook_path = tmp_path / "analysis_report.ipynb"
    build_notebook(summary, notebook_path)

    notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
    all_source = "\n".join("".join(cell["source"]) for cell in notebook["cells"])

    assert "sys.path.insert" in all_source
    assert "상관계수 해석" in all_source
    assert "RFM 세그먼트별 특징" in all_source
    assert "비즈니스 인사이트" in all_source
    assert "quantity-amount" in all_source


def test_readme_documents_chart_axes_rfm_actions_and_insight_validation():
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "차트별 제목과 축 레이블" in readme
    assert "| 차트 | 파일 | 제목 | X축 | Y축 |" in readme
    assert "RFM 세그먼트별 특징과 운영 전략" in readme
    assert "대상 세그먼트" in readme
    assert readme.count("(근거)") >= 3
    assert readme.count("(실행)") >= 3
    assert readme.count("(검증)") >= 3
