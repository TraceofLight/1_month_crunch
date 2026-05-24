"""Reusable e-commerce multimodal analysis pipeline."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


class DataAnalyzer:
    """Load, clean, enrich, and segment e-commerce transaction data."""

    COLUMN_ALIASES = {
        "InvoiceNo": "invoice_no",
        "invoice_no": "invoice_no",
        "invoice": "invoice_no",
        "StockCode": "stock_code",
        "stock_code": "stock_code",
        "Description": "product_name",
        "description": "product_name",
        "product_name": "product_name",
        "ProductName": "product_name",
        "Quantity": "quantity",
        "quantity": "quantity",
        "InvoiceDate": "order_date",
        "invoice_date": "order_date",
        "order_date": "order_date",
        "UnitPrice": "unit_price",
        "unit_price": "unit_price",
        "price": "unit_price",
        "CustomerID": "customer_id",
        "customer_id": "customer_id",
        "Country": "country",
        "country": "country",
        "amount": "amount",
        "Amount": "amount",
        "category": "category",
        "Category": "category",
        "image_array": "image_array",
        "ImageArray": "image_array",
    }

    CATEGORY_RULES = (
        ("Seasonal", r"CHRISTMAS|EASTER|HALLOWEEN|VALENTINE|ADVENT"),
        ("Kitchen", r"MUG|CUP|PLATE|BOWL|TEA|COFFEE|CAKE|KITCHEN|SPOON"),
        ("Home Decor", r"HOME|HEART|SIGN|FRAME|CANDLE|LIGHT|LAMP|CLOCK|WALL"),
        ("Accessories", r"BAG|PURSE|WALLET|SCARF|JEWEL|NECKLACE|BRACELET"),
        ("Stationery", r"CARD|PAPER|NOTEBOOK|PENCIL|PEN|WRAP|TAG"),
        ("Gifts", r"GIFT|SET|BOX|BUNDLE|PACK"),
        ("Garden", r"GARDEN|PLANT|FLOWER|POT"),
        ("Toys", r"TOY|DOLL|GAME|PUZZLE"),
    )

    def __init__(self, data_path: str | Path):
        self.data_path = Path(data_path)
        self.raw_df: pd.DataFrame | None = None
        self.df: pd.DataFrame | None = None
        self.image_tensor: np.ndarray | None = None
        self.rfm: pd.DataFrame | None = None

    def load_data(self, nrows: int | None = None, encoding: str | None = None) -> pd.DataFrame:
        """Read a CSV file and normalize common Online Retail column names."""
        if not self.data_path.exists():
            raise FileNotFoundError(f"Data file not found: {self.data_path}")

        read_encoding = encoding or "ISO-8859-1"
        try:
            raw_df = pd.read_csv(self.data_path, nrows=nrows, encoding=read_encoding)
        except UnicodeDecodeError:
            raw_df = pd.read_csv(self.data_path, nrows=nrows, encoding="utf-8")

        df = raw_df.rename(columns={col: self.COLUMN_ALIASES.get(col, col) for col in raw_df.columns})
        self.raw_df = raw_df
        self.df = self._normalize_frame(df)
        return self.df.copy()

    def handle_missing_values(
        self,
        numeric_strategy: str = "group_median",
        group_col: str = "category",
        numeric_cols: Iterable[str] | None = None,
        text_cols: Iterable[str] | None = None,
        text_fill: str = "UNKNOWN",
        date_strategy: str = "drop",
    ) -> pd.DataFrame:
        """Fill missing values, including group-wise numeric imputation."""
        df = self._require_df().copy()
        numeric_cols = list(numeric_cols or [col for col in ["quantity", "unit_price"] if col in df.columns])
        text_cols = list(text_cols or [col for col in ["product_name", "stock_code", "country"] if col in df.columns])

        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            if numeric_strategy == "group_mean" and group_col in df.columns:
                fill_values = df.groupby(group_col, observed=False)[col].transform("mean")
                df[col] = df[col].fillna(fill_values)
            elif numeric_strategy == "group_median" and group_col in df.columns:
                fill_values = df.groupby(group_col, observed=False)[col].transform("median")
                df[col] = df[col].fillna(fill_values)
            elif numeric_strategy == "mean":
                df[col] = df[col].fillna(df[col].mean())
            elif numeric_strategy == "median":
                df[col] = df[col].fillna(df[col].median())
            else:
                raise ValueError(f"Unsupported numeric_strategy: {numeric_strategy}")
            df[col] = df[col].fillna(df[col].median())

        for col in text_cols:
            df[col] = df[col].fillna(text_fill)

        if "order_date" in df.columns:
            df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
            if date_strategy == "drop":
                df = df.dropna(subset=["order_date"])
            elif date_strategy == "median":
                median_date = df["order_date"].dropna().median()
                df["order_date"] = df["order_date"].fillna(median_date)
            else:
                raise ValueError(f"Unsupported date_strategy: {date_strategy}")

        if "product_name" in df.columns:
            df["category"] = self._derive_category(df["product_name"])
        if {"quantity", "unit_price"}.issubset(df.columns):
            df["amount"] = df["quantity"] * df["unit_price"]

        self.df = df
        return df.copy()

    def engineer_multimodal_features(
        self,
        image_size: int = 8,
        image_col: str | None = None,
        store_arrays: bool = True,
    ) -> pd.DataFrame:
        """Create text and NumPy image-array features with vectorized operations."""
        if image_size < 2:
            raise ValueError("image_size must be at least 2")

        df = self._require_df().copy()
        product_names = df.get("product_name", pd.Series("", index=df.index)).fillna("").astype(str)
        df["name_word_count"] = product_names.str.split().str.len()
        df["name_length"] = product_names.str.len()

        if image_col and image_col in df.columns:
            tensor = self._stack_image_column(df[image_col], image_size=image_size)
        else:
            tensor = self._generate_product_image_tensor(df, image_size=image_size)

        self.image_tensor = tensor
        df["image_mean"] = tensor.mean(axis=(1, 2))
        df["image_std"] = tensor.std(axis=(1, 2))
        x_edges = np.abs(np.diff(tensor, axis=2)).mean(axis=(1, 2))
        y_edges = np.abs(np.diff(tensor, axis=1)).mean(axis=(1, 2))
        df["edge_strength"] = (x_edges + y_edges) / 2.0
        if store_arrays:
            df["image_array"] = pd.Series(list(tensor.astype(np.uint8)), index=df.index)

        self.df = df
        return df.copy()

    def detect_outliers(self, column: str, threshold: float = 1.5) -> tuple[pd.DataFrame, dict[str, float]]:
        """Detect outliers with an explicit IQR implementation."""
        df = self._require_df()
        if column not in df.columns:
            raise KeyError(f"Column not found: {column}")
        series = pd.to_numeric(df[column], errors="coerce").dropna()
        q1 = float(series.quantile(0.25))
        q3 = float(series.quantile(0.75))
        iqr = q3 - q1
        lower = q1 - threshold * iqr
        upper = q3 + threshold * iqr
        mask = (pd.to_numeric(df[column], errors="coerce") < lower) | (
            pd.to_numeric(df[column], errors="coerce") > upper
        )
        bounds = {"q1": q1, "q3": q3, "iqr": float(iqr), "lower": float(lower), "upper": float(upper)}
        return df.loc[mask].copy(), bounds

    def cap_outliers(
        self,
        column: str,
        threshold: float = 1.5,
        output_col: str | None = None,
    ) -> pd.DataFrame:
        """Winsorize a column to IQR bounds and keep the result in a new column by default."""
        df = self._require_df().copy()
        _, bounds = self.detect_outliers(column, threshold=threshold)
        target_col = output_col or f"{column}_capped"
        df[target_col] = pd.to_numeric(df[column], errors="coerce").clip(bounds["lower"], bounds["upper"])
        self.df = df
        return df.copy()

    def calculate_rfm(
        self,
        customer_col: str = "customer_id",
        date_col: str = "order_date",
        amount_col: str = "amount",
        reference_date: str | pd.Timestamp | None = None,
        invoice_col: str = "invoice_no",
        min_amount: float = 0.0,
    ) -> pd.DataFrame:
        """Calculate Recency, Frequency, Monetary scores and assign customer segments."""
        df = self._require_df().copy()
        for col in [customer_col, date_col, amount_col]:
            if col not in df.columns:
                raise KeyError(f"Column not found: {col}")

        work = df[[customer_col, date_col, amount_col] + ([invoice_col] if invoice_col in df.columns else [])].copy()
        work[date_col] = pd.to_datetime(work[date_col], errors="coerce")
        work[amount_col] = pd.to_numeric(work[amount_col], errors="coerce")
        work = work.dropna(subset=[customer_col, date_col, amount_col])
        work = work[work[amount_col] > min_amount]
        if "quantity" in df.columns:
            positive_quantity = pd.to_numeric(df.loc[work.index, "quantity"], errors="coerce") > 0
            work = work.loc[positive_quantity.fillna(False)]

        if work.empty:
            raise ValueError("No valid rows available for RFM calculation")

        ref_date = pd.to_datetime(reference_date) if reference_date is not None else work[date_col].max()
        frequency_agg = (invoice_col, "nunique") if invoice_col in work.columns else (date_col, "count")
        rfm = work.groupby(customer_col).agg(
            last_order=(date_col, "max"),
            frequency=frequency_agg,
            monetary=(amount_col, "sum"),
        )
        rfm["recency"] = (ref_date - rfm["last_order"]).dt.days
        rfm["r_score"] = self._score_series(rfm["recency"], higher_is_better=False)
        rfm["f_score"] = self._score_series(rfm["frequency"], higher_is_better=True)
        rfm["m_score"] = self._score_series(rfm["monetary"], higher_is_better=True)
        rfm["rfm_score"] = rfm[["r_score", "f_score", "m_score"]].sum(axis=1)
        rfm["segment"] = self._segment_rfm(rfm)
        ordered = [
            "last_order",
            "recency",
            "frequency",
            "monetary",
            "r_score",
            "f_score",
            "m_score",
            "rfm_score",
            "segment",
        ]
        self.rfm = rfm[ordered].sort_values(["rfm_score", "monetary"], ascending=False)
        return self.rfm.copy()

    def summarize_numeric(self, columns: Iterable[str] | None = None) -> pd.DataFrame:
        """Return core statistics for numeric variables."""
        df = self._require_df()
        if columns is None:
            numeric = df.select_dtypes(include=[np.number])
        else:
            numeric = df[list(columns)].apply(pd.to_numeric, errors="coerce")
        return pd.DataFrame(
            {
                "mean": numeric.mean(),
                "median": numeric.median(),
                "std": numeric.std(),
                "q1": numeric.quantile(0.25),
                "q3": numeric.quantile(0.75),
                "min": numeric.min(),
                "max": numeric.max(),
            }
        )

    def correlation_matrix(self, columns: Iterable[str]) -> pd.DataFrame:
        """Calculate a Pearson correlation matrix for selected numeric columns."""
        df = self._require_df()
        numeric = df[list(columns)].apply(pd.to_numeric, errors="coerce")
        return numeric.corr()

    def _normalize_frame(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        if "order_date" in df.columns:
            df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
        for col in ["quantity", "unit_price", "amount", "customer_id"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        if "invoice_no" in df.columns:
            df["invoice_no"] = df["invoice_no"].astype(str)
        if "stock_code" in df.columns:
            df["stock_code"] = df["stock_code"].astype(str)
        if "category" not in df.columns and "product_name" in df.columns:
            df["category"] = self._derive_category(df["product_name"])
        if "amount" not in df.columns and {"quantity", "unit_price"}.issubset(df.columns):
            df["amount"] = df["quantity"] * df["unit_price"]
        return df

    def _derive_category(self, product_names: pd.Series) -> np.ndarray:
        text = product_names.fillna("").astype(str).str.upper()
        conditions = [text.str.contains(pattern, regex=True, na=False) for _, pattern in self.CATEGORY_RULES]
        choices = [label for label, _ in self.CATEGORY_RULES]
        return np.select(conditions, choices, default="Misc")

    def _generate_product_image_tensor(self, df: pd.DataFrame, image_size: int) -> np.ndarray:
        stock = df.get("stock_code", pd.Series("", index=df.index)).fillna("").astype(str)
        names = df.get("product_name", pd.Series("", index=df.index)).fillna("").astype(str)
        keys = stock.str.cat(names, sep="|")
        hashes = pd.util.hash_pandas_object(keys, index=False).to_numpy(dtype=np.uint64)
        offsets = np.arange(image_size * image_size, dtype=np.uint64)
        bit_shifts = (offsets % np.uint64(8)) * np.uint64(8)
        pixels = (
            (hashes[:, None] >> bit_shifts[None, :])
            + offsets[None, :] * np.uint64(37)
            + (hashes[:, None] % np.uint64(251))
        ) % np.uint64(256)
        return pixels.astype(np.float32).reshape(len(df), image_size, image_size)

    def _stack_image_column(self, series: pd.Series, image_size: int) -> np.ndarray:
        parsed = series.map(self._parse_image_value).to_numpy()
        tensor = np.stack(parsed).astype(np.float32)
        if tensor.ndim == 4:
            tensor = tensor.mean(axis=3)
        if tensor.shape[1] != image_size or tensor.shape[2] != image_size:
            tensor = tensor[:, :: max(tensor.shape[1] // image_size, 1), :: max(tensor.shape[2] // image_size, 1)]
            tensor = tensor[:, :image_size, :image_size]
        return tensor

    @staticmethod
    def _parse_image_value(value: object) -> np.ndarray:
        if isinstance(value, np.ndarray):
            return value
        if isinstance(value, list):
            return np.asarray(value)
        if isinstance(value, str):
            return np.asarray(ast.literal_eval(value))
        raise TypeError(f"Unsupported image value type: {type(value)!r}")

    @staticmethod
    def _score_series(series: pd.Series, higher_is_better: bool, buckets: int = 5) -> pd.Series:
        if series.nunique(dropna=True) <= 1:
            return pd.Series(np.full(len(series), 3, dtype=int), index=series.index)
        ranks = series.rank(method="first", ascending=higher_is_better, pct=True)
        scores = np.ceil(ranks * buckets).clip(1, buckets).astype(int)
        return pd.Series(scores, index=series.index)

    @staticmethod
    def _segment_rfm(rfm: pd.DataFrame) -> np.ndarray:
        r = rfm["r_score"]
        f = rfm["f_score"]
        m = rfm["m_score"]
        frequency = rfm["frequency"]
        conditions = [
            (r >= 4) & (f >= 4) & (m >= 4),
            (r >= 3) & (f >= 4),
            (r == 3) & (f <= 3),
            (m >= 4) & (f <= 3),
            (r >= 4) & (frequency <= 1),
            r <= 2,
        ]
        choices = ["VIP", "Loyal", "At Risk", "Big Spenders", "New", "Churned"]
        return np.select(conditions, choices, default="Regular")

    def _require_df(self) -> pd.DataFrame:
        if self.df is None:
            raise RuntimeError("load_data() must be called before this operation")
        return self.df
