from src.finance_risk.data import N_SAMPLES, RANDOM_STATE, generate_finance_data


def main() -> None:
    df = generate_finance_data(
        output_path="finance_data.csv",
        n_samples=N_SAMPLES,
        random_state=RANDOM_STATE,
    )
    print("데이터 생성 완료: finance_data.csv")
    print(f"전체 샘플 수: {len(df)}")
    print(f"연체(1) 비율: {df['is_overdue'].mean() * 100:.2f}% (불균형 데이터 확인)")


if __name__ == "__main__":
    main()
