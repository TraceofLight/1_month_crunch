from pathlib import Path

import numpy as np
import pandas as pd

from src.pipeline import DataAnalyzer


def write_sample_csv(tmp_path: Path) -> Path:
    df = pd.DataFrame(
        {
            "InvoiceNo": ["A1", "A2", "A3", "A4", "A5", "A6"],
            "StockCode": ["S1", "S2", "S3", "S4", "S5", "S6"],
            "Description": [
                "RED HEART MUG",
                "BLUE BAG",
                "GREEN HOME LAMP",
                "PAPER GIFT SET",
                None,
                "LARGE GARDEN LIGHT",
            ],
            "Quantity": [1, 2, 3, 4, 5, 1],
            "InvoiceDate": [
                "2024-01-01",
                "2024-01-03",
                "2024-01-05",
                "2024-01-08",
                "2024-01-10",
                "2024-01-12",
            ],
            "UnitPrice": [10.0, np.nan, 30.0, 40.0, 1000.0, 20.0],
            "CustomerID": [101, 101, 102, 103, 104, 105],
            "Country": ["UK", "UK", "FR", "FR", "DE", "DE"],
        }
    )
    path = tmp_path / "sample.csv"
    df.to_csv(path, index=False)
    return path


def test_load_data_normalizes_online_retail_columns(tmp_path):
    analyzer = DataAnalyzer(write_sample_csv(tmp_path))

    loaded = analyzer.load_data()

    assert len(loaded) == 6
    assert {
        "invoice_no",
        "stock_code",
        "product_name",
        "quantity",
        "order_date",
        "unit_price",
        "customer_id",
        "country",
        "amount",
        "category",
    }.issubset(loaded.columns)
    assert pd.api.types.is_datetime64_any_dtype(loaded["order_date"])
    assert loaded.loc[0, "amount"] == 10.0


def test_group_median_missing_value_imputation(tmp_path):
    analyzer = DataAnalyzer(write_sample_csv(tmp_path))
    analyzer.load_data()

    cleaned = analyzer.handle_missing_values(
        numeric_strategy="group_median",
        group_col="country",
        numeric_cols=["unit_price"],
        text_fill="UNKNOWN PRODUCT",
    )

    assert cleaned["unit_price"].isna().sum() == 0
    assert cleaned.loc[1, "unit_price"] == 10.0
    assert cleaned.loc[4, "product_name"] == "UNKNOWN PRODUCT"


def test_iqr_outlier_detection_reports_bounds_and_rows(tmp_path):
    analyzer = DataAnalyzer(write_sample_csv(tmp_path))
    analyzer.load_data()

    outliers, bounds = analyzer.detect_outliers("unit_price", threshold=1.5)

    assert bounds["lower"] < bounds["upper"]
    assert outliers["unit_price"].tolist() == [1000.0]


def test_multimodal_feature_engineering_uses_numpy_tensor(tmp_path):
    analyzer = DataAnalyzer(write_sample_csv(tmp_path))
    analyzer.load_data()

    featured = analyzer.engineer_multimodal_features(image_size=8)

    assert {"name_word_count", "name_length", "image_mean", "image_std", "edge_strength"}.issubset(
        featured.columns
    )
    assert analyzer.image_tensor.shape == (6, 8, 8)
    np.testing.assert_allclose(
        featured["image_mean"].to_numpy(),
        analyzer.image_tensor.mean(axis=(1, 2)),
    )
    np.testing.assert_allclose(
        featured["image_std"].to_numpy(),
        analyzer.image_tensor.std(axis=(1, 2)),
    )


def test_multimodal_feature_engineering_parses_space_separated_image_arrays(tmp_path):
    df = pd.DataFrame(
        {
            "InvoiceNo": ["A1", "A2"],
            "StockCode": ["S1", "S2"],
            "Description": ["RED HEART MUG", "BLUE BAG"],
            "Quantity": [1, 2],
            "InvoiceDate": ["2024-01-01", "2024-01-02"],
            "UnitPrice": [10.0, 20.0],
            "CustomerID": [101, 102],
            "Country": ["UK", "UK"],
            "ImageArray": ["0 1 2 3", "4 5 6 7"],
        }
    )
    path = tmp_path / "image_arrays.csv"
    df.to_csv(path, index=False)
    analyzer = DataAnalyzer(path)
    analyzer.load_data()

    featured = analyzer.engineer_multimodal_features(image_size=2, image_col="image_array", store_arrays=False)

    expected = np.array([[[0, 1], [2, 3]], [[4, 5], [6, 7]]], dtype=np.float32)
    assert analyzer.image_tensor.shape == (2, 2, 2)
    np.testing.assert_allclose(analyzer.image_tensor, expected)
    np.testing.assert_allclose(featured["image_mean"].to_numpy(), expected.mean(axis=(1, 2)))


def test_calculate_rfm_assigns_actionable_segments(tmp_path):
    analyzer = DataAnalyzer(write_sample_csv(tmp_path))
    analyzer.load_data()

    rfm = analyzer.calculate_rfm(
        customer_col="customer_id",
        date_col="order_date",
        amount_col="amount",
        reference_date=pd.Timestamp("2024-01-12"),
    )

    assert {"recency", "frequency", "monetary", "r_score", "f_score", "m_score", "segment"}.issubset(
        rfm.columns
    )
    assert rfm.loc[105, "recency"] == 0
    assert rfm["segment"].nunique() >= 4
    assert set(rfm["segment"]).issubset(
        {"VIP", "Loyal", "New", "Churned", "At Risk", "Big Spenders", "Regular"}
    )
