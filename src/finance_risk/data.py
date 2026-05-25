from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

FEATURE_COLUMNS = [
    "age",
    "annual_income",
    "spending_score",
    "debt_ratio",
    "credit_card_count",
    "overdue_count_6m",
]
REGRESSION_TARGET = "credit_score"
CLASSIFICATION_TARGET = "is_overdue"
RANDOM_STATE = 42
N_SAMPLES = 10_000


def generate_finance_data(
    output_path: str | Path = "finance_data.csv",
    n_samples: int = N_SAMPLES,
    random_state: int = RANDOM_STATE,
) -> pd.DataFrame:
    """Generate the assignment's synthetic finance risk dataset."""
    output_path = Path(output_path)
    np.random.seed(random_state)

    data = {
        "age": np.random.randint(20, 70, n_samples),
        "annual_income": np.random.normal(5000, 2000, n_samples).round(0),
        "spending_score": np.random.randint(1, 100, n_samples),
        "debt_ratio": np.random.uniform(0, 1, n_samples).round(2),
        "credit_card_count": np.random.randint(1, 10, n_samples),
        "overdue_count_6m": np.random.poisson(0.5, n_samples),
    }

    df = pd.DataFrame(data)
    df["annual_income"] = df["annual_income"].apply(lambda x: max(x, 1500))

    df["credit_score"] = (
        300
        + (df["annual_income"] / 100) * 3
        - (df["overdue_count_6m"] * 50)
        - (df["debt_ratio"] * 100)
        + np.random.normal(0, 30, n_samples)
    )
    df["credit_score"] = df["credit_score"].clip(0, 1000).round(0)

    threshold = df["credit_score"].quantile(0.15)
    df["is_overdue"] = np.where(
        (df["credit_score"] < threshold) & (np.random.rand(n_samples) > 0.2),
        1,
        0,
    )

    df = df.sample(frac=1, random_state=random_state).reset_index(drop=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    return df


def load_finance_data(path: str | Path = "finance_data.csv") -> pd.DataFrame:
    path = Path(path)
    df = pd.read_csv(path)
    required_columns = set(FEATURE_COLUMNS + [REGRESSION_TARGET, CLASSIFICATION_TARGET])
    missing_columns = required_columns.difference(df.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"finance data is missing required columns: {missing}")
    return df
