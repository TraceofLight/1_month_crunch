from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.finance_risk.data import N_SAMPLES, RANDOM_STATE, generate_finance_data
from src.finance_risk.experiment import run_experiment


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Finance risk ML pipeline")
    parser.add_argument("--data-path", default="finance_data.csv", help="CSV dataset path")
    parser.add_argument("--evidence-dir", default="evidence", help="Output evidence directory")
    parser.add_argument(
        "--generate-data",
        action="store_true",
        help="Regenerate the assignment dataset before training",
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Use a smaller Random Forest search grid for quick smoke tests",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data_path = Path(args.data_path)
    if args.generate_data or not data_path.exists():
        df = generate_finance_data(
            output_path=data_path,
            n_samples=N_SAMPLES,
            random_state=RANDOM_STATE,
        )
        print(f"데이터 생성 완료: {data_path}")
        print(f"전체 샘플 수: {len(df)}")
        print(f"연체(1) 비율: {df['is_overdue'].mean() * 100:.2f}%")

    results = run_experiment(data_path=data_path, evidence_dir=args.evidence_dir, fast=args.fast)
    best_auc = results["classification"].iloc[0]["auc"]
    best_regression = results["regression"].iloc[0]
    print(f"분류 최고 AUC: {best_auc:.4f}")
    print(
        "회귀 최고 RMSE: "
        f"{best_regression['rmse']:.4f} "
        f"({best_regression['model']}, alpha={best_regression['alpha']})"
    )
    print(f"evidence 저장 위치: {Path(args.evidence_dir).resolve()}")


if __name__ == "__main__":
    main()
