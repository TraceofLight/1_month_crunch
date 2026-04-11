from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter


EPSILON = 1e-9


@dataclass(frozen=True)
class Matrix:
    values: list[list[float]]

    def __post_init__(self) -> None:
        if not self.values:
            raise ValueError("matrix must not be empty")

        size = len(self.values)
        normalized_rows: list[list[float]] = []

        for row in self.values:
            if len(row) != size:
                raise ValueError("matrix must be square")
            normalized_rows.append([float(value) for value in row])

        object.__setattr__(self, "values", normalized_rows)

    @property
    def size(self) -> int:
        return len(self.values)

    def flatten(self) -> list[float]:
        return [value for row in self.values for value in row]


def normalize_label(raw_label: str) -> str:
    normalized = raw_label.strip().lower()
    if normalized in {"+", "cross"}:
        return "Cross"
    if normalized == "x":
        return "X"
    raise ValueError(f"unsupported label: {raw_label}")


def generate_cross_pattern(size: int) -> Matrix:
    if size < 3 or size % 2 == 0:
        raise ValueError("size must be an odd integer >= 3")

    center = size // 2
    values = []
    for row_index in range(size):
        row = []
        for column_index in range(size):
            row.append(1.0 if row_index == center or column_index == center else 0.0)
        values.append(row)
    return Matrix(values)


def generate_x_pattern(size: int) -> Matrix:
    if size < 3 or size % 2 == 0:
        raise ValueError("size must be an odd integer >= 3")

    values = []
    for row_index in range(size):
        row = []
        for column_index in range(size):
            row.append(1.0 if column_index == row_index or column_index == size - 1 - row_index else 0.0)
        values.append(row)
    return Matrix(values)


def mac_2d(pattern: Matrix, filter_matrix: Matrix) -> float:
    if pattern.size != filter_matrix.size:
        raise ValueError("pattern and filter must have the same size")

    total = 0.0
    for row_index in range(pattern.size):
        for column_index in range(pattern.size):
            total += pattern.values[row_index][column_index] * filter_matrix.values[row_index][column_index]
    return total


def mac_1d(pattern_flat: list[float], filter_flat: list[float]) -> float:
    if len(pattern_flat) != len(filter_flat):
        raise ValueError("flattened pattern and filter must have the same length")

    total = 0.0
    for index in range(len(pattern_flat)):
        total += pattern_flat[index] * filter_flat[index]
    return total


def judge_scores(cross_score: float, x_score: float, epsilon: float = EPSILON) -> str:
    if abs(cross_score - x_score) < epsilon:
        return "UNDECIDED"
    return "Cross" if cross_score > x_score else "X"


def benchmark_mac(pattern: Matrix, filter_matrix: Matrix, runs: int = 10, use_flatten: bool = False) -> float:
    if runs <= 0:
        raise ValueError("runs must be positive")

    if use_flatten:
        pattern_flat = pattern.flatten()
        filter_flat = filter_matrix.flatten()
        start = perf_counter()
        for _ in range(runs):
            mac_1d(pattern_flat, filter_flat)
        end = perf_counter()
    else:
        start = perf_counter()
        for _ in range(runs):
            mac_2d(pattern, filter_matrix)
        end = perf_counter()

    return ((end - start) / runs) * 1000.0


def blend_patterns(first: Matrix, second: Matrix) -> Matrix:
    if first.size != second.size:
        raise ValueError("patterns must have the same size")

    values = []
    for row_index in range(first.size):
        row = []
        for column_index in range(first.size):
            row.append((first.values[row_index][column_index] + second.values[row_index][column_index]) / 2.0)
        values.append(row)
    return Matrix(values)


def make_invalid_size_pattern(size: int) -> list[list[float]]:
    pattern = generate_cross_pattern(size).values
    invalid_pattern = [row[:] for row in pattern]
    invalid_pattern[-1] = invalid_pattern[-1][:-1]
    return invalid_pattern


def build_default_data_payload() -> dict:
    filters = {}
    for size in (5, 13, 25):
        filters[f"size_{size}"] = {
            "cross": generate_cross_pattern(size).values,
            "x": generate_x_pattern(size).values,
        }

    blended_13 = blend_patterns(generate_cross_pattern(13), generate_x_pattern(13))

    patterns = {
        "size_5_1": {"input": generate_cross_pattern(5).values, "expected": "+"},
        "size_5_2": {"input": generate_x_pattern(5).values, "expected": "x"},
        "size_13_1": {"input": generate_cross_pattern(13).values, "expected": "+"},
        "size_13_2": {"input": generate_x_pattern(13).values, "expected": "x"},
        "size_13_3": {"input": blended_13.values, "expected": "x"},
        "size_25_1": {"input": generate_cross_pattern(25).values, "expected": "+"},
        "size_25_2": {"input": generate_x_pattern(25).values, "expected": "x"},
        "size_25_3": {"input": make_invalid_size_pattern(25), "expected": "+"},
    }

    return {"filters": filters, "patterns": patterns}


def save_default_data(path: str | Path) -> Path:
    target_path = Path(path)
    target_path.write_text(
        json.dumps(build_default_data_payload(), indent=2),
        encoding="utf-8",
    )
    return target_path


def parse_pattern_size(case_id: str) -> int:
    match = re.fullmatch(r"size_(\d+)_\d+", case_id)
    if match is None:
        raise ValueError(f"invalid pattern key: {case_id}")
    return int(match.group(1))


def matrix_from_raw(raw_matrix: list[list[float]]) -> Matrix:
    return Matrix(raw_matrix)


def analyze_case(case_id: str, case_payload: dict, filters: dict[str, dict[str, Matrix]]) -> dict:
    try:
        size = parse_pattern_size(case_id)
        filter_key = f"size_{size}"
        pattern = matrix_from_raw(case_payload["input"])
        expected = normalize_label(case_payload["expected"])

        if filter_key not in filters:
            raise ValueError(f"관련 필터가 없어 판정할 수 없음: {filter_key}")

        filter_group = filters[filter_key]

        if pattern.size != size:
            raise ValueError(f"pattern size mismatch: expected {size}x{size}, got {pattern.size}x{pattern.size}")

        cross_score = mac_2d(pattern, filter_group["Cross"])
        x_score = mac_2d(pattern, filter_group["X"])
        predicted = judge_scores(cross_score, x_score)
        passed = predicted == expected
        reason = "" if passed else f"expected {expected}, got {predicted}"

        return {
            "case_id": case_id,
            "cross_score": cross_score,
            "x_score": x_score,
            "predicted": predicted,
            "expected": expected,
            "status": "PASS" if passed else "FAIL",
            "reason": reason,
        }
    except (KeyError, TypeError, ValueError) as error:
        return {
            "case_id": case_id,
            "cross_score": None,
            "x_score": None,
            "predicted": "UNDECIDED",
            "expected": case_payload.get("expected", "UNKNOWN") if isinstance(case_payload, dict) else "UNKNOWN",
            "status": "FAIL",
            "reason": str(error),
        }


def build_performance_report() -> list[dict]:
    report = []
    for size in (3, 5, 13, 25):
        pattern = generate_cross_pattern(size)
        filter_matrix = generate_cross_pattern(size)
        report.append(
            {
                "size": size,
                "operations": size * size,
                "two_d_ms": benchmark_mac(pattern, filter_matrix, runs=10, use_flatten=False),
                "one_d_ms": benchmark_mac(pattern, filter_matrix, runs=10, use_flatten=True),
            }
        )
    return report


def analyze_data_file(path: str | Path) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))

    raw_filters = payload["filters"]
    filters: dict[str, dict[str, Matrix]] = {}
    for size_key, filter_payload in raw_filters.items():
        filters[size_key] = {
            normalize_label("cross"): matrix_from_raw(filter_payload["cross"]),
            normalize_label("x"): matrix_from_raw(filter_payload["x"]),
        }

    results = []
    failures = []
    for case_id, case_payload in payload["patterns"].items():
        result = analyze_case(case_id, case_payload, filters)
        results.append(result)
        if result["status"] == "FAIL":
            failures.append({"case_id": case_id, "reason": result["reason"]})

    summary = {
        "total": len(results),
        "passed": sum(1 for item in results if item["status"] == "PASS"),
        "failed": sum(1 for item in results if item["status"] == "FAIL"),
    }

    return {
        "results": results,
        "failures": failures,
        "summary": summary,
        "performance": build_performance_report(),
    }


def parse_matrix_row(raw_text: str, expected_size: int) -> list[float]:
    parts = raw_text.strip().split()
    if len(parts) != expected_size:
        raise ValueError(f"각 줄에 {expected_size}개의 숫자를 공백으로 구분해 입력하세요.")

    try:
        values = [float(part) for part in parts]
    except ValueError as error:
        raise ValueError(f"각 줄에 {expected_size}개의 숫자를 공백으로 구분해 입력하세요.") from error

    if any(value not in {0.0, 1.0} for value in values):
        raise ValueError(f"각 줄에 {expected_size}개의 숫자를 공백으로 구분해 입력하세요.")

    return values


def read_matrix_from_input(title: str, size: int, input_func=input, output_func=print) -> Matrix:
    output_func(title)
    rows: list[list[float]] = []

    while len(rows) < size:
        try:
            row = parse_matrix_row(input_func("").strip(), size)
            rows.append(row)
        except ValueError:
            output_func(f"입력 형식 오류: 각 줄에 {size}개의 숫자를 공백으로 구분해 입력하세요.")
            rows = []
            output_func(title)

    return Matrix(rows)


def render_performance_lines(performance_rows: list[dict]) -> list[str]:
    lines = ["크기 | 2D 평균(ms) | 1D 평균(ms) | 연산 횟수", "---- | ------------ | ------------ | --------"]
    for row in performance_rows:
        lines.append(
            f"{row['size']}x{row['size']} | {row['two_d_ms']:.6f} | {row['one_d_ms']:.6f} | {row['operations']}"
        )
    return lines


def render_matrix_lines(matrix: Matrix) -> list[str]:
    return [" ".join(str(int(value)) if value.is_integer() else str(value) for value in row) for row in matrix.values]


def render_section_header(title: str) -> list[str]:
    return [
        "#----------------------------------------",
        title,
        "#----------------------------------------",
    ]


def read_odd_size(input_func=input, output_func=print) -> int:
    while True:
        raw_value = input_func("패턴 크기 N(홀수, 3 이상): ").strip()
        try:
            size = int(raw_value)
        except ValueError:
            output_func("입력 형식 오류: 크기 N은 정수로 입력하세요.")
            continue

        if size < 3 or size % 2 == 0:
            output_func("입력 형식 오류: 크기 N은 3 이상의 홀수여야 합니다.")
            continue

        return size



def read_pattern_kind(input_func=input, output_func=print) -> str:
    while True:
        output_func("1. Cross")
        output_func("2. X")
        choice = input_func("패턴 선택: ").strip()
        if choice == "1":
            return "Cross"
        if choice == "2":
            return "X"
        output_func("잘못된 선택입니다. 1 또는 2를 입력하세요.")



def read_yes_no(prompt: str, input_func=input, output_func=print) -> bool:
    while True:
        choice = input_func(prompt).strip().lower()
        if choice in {"y", "yes"}:
            return True
        if choice in {"n", "no"}:
            return False
        output_func("잘못된 입력입니다. y 또는 n을 입력하세요.")



def append_generated_pattern_case(data_path: str | Path, pattern: Matrix, label: str) -> str:
    target_path = Path(data_path)
    if not target_path.exists():
        save_default_data(target_path)

    payload = json.loads(target_path.read_text(encoding="utf-8"))
    patterns = payload.setdefault("patterns", {})
    prefix = f"size_{pattern.size}_"
    indexes = []

    for case_id in patterns:
        match = re.fullmatch(rf"{re.escape(prefix)}(\d+)", case_id)
        if match is not None:
            indexes.append(int(match.group(1)))

    next_index = (max(indexes) + 1) if indexes else 1
    case_id = f"{prefix}{next_index}"
    patterns[case_id] = {
        "input": pattern.values,
        "expected": "+" if label == "Cross" else "x",
    }

    target_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return case_id



def run_pattern_generator_mode(data_path: str | Path = "data.json", input_func=input, output_func=print) -> dict:
    output_func("=== Mini NPU Simulator ===")
    for line in render_section_header("# [보너스] 패턴 생성기"):
        output_func(line)
    size = read_odd_size(input_func=input_func, output_func=output_func)
    label = read_pattern_kind(input_func=input_func, output_func=output_func)
    pattern = generate_cross_pattern(size) if label == "Cross" else generate_x_pattern(size)

    output_func(f"생성된 패턴 ({label}, {size}x{size})")
    for line in render_matrix_lines(pattern):
        output_func(line)

    for line in render_section_header("# [성능 비교]"):
        output_func(line)
    two_d_ms = benchmark_mac(pattern, pattern, runs=10, use_flatten=False)
    one_d_ms = benchmark_mac(pattern, pattern, runs=10, use_flatten=True)
    output_func(f"연산 시간(평균/10회, 2D): {two_d_ms:.6f} ms")
    output_func(f"연산 시간(평균/10회, 1D): {one_d_ms:.6f} ms")

    for line in render_section_header("# [저장 여부]"):
        output_func(line)
    saved_case_id = None
    if read_yes_no("data.json에 추가할까요? (y/n): ", input_func=input_func, output_func=output_func):
        saved_case_id = append_generated_pattern_case(data_path, pattern, label)
        output_func(f"data.json에 저장했습니다: {saved_case_id}")

    return {
        "size": size,
        "label": label,
        "pattern": pattern,
        "two_d_ms": two_d_ms,
        "one_d_ms": one_d_ms,
        "saved_case_id": saved_case_id,
    }


def run_manual_mode(input_func=input, output_func=print) -> dict:
    output_func("=== Mini NPU Simulator ===")
    for line in render_section_header("# [1] 필터 입력"):
        output_func(line)
    filter_a = read_matrix_from_input("필터 A (3줄 입력, 공백 구분)", 3, input_func=input_func, output_func=output_func)
    filter_b = read_matrix_from_input("필터 B (3줄 입력, 공백 구분)", 3, input_func=input_func, output_func=output_func)

    for line in render_section_header("# [2] 패턴 입력"):
        output_func(line)
    pattern = read_matrix_from_input("패턴 (3줄 입력, 공백 구분)", 3, input_func=input_func, output_func=output_func)

    score_a = mac_2d(pattern, filter_a)
    score_b = mac_2d(pattern, filter_b)
    decision = "판정 불가" if abs(score_a - score_b) < EPSILON else ("A" if score_a > score_b else "B")
    average_ms = benchmark_mac(pattern, filter_a, runs=10, use_flatten=False)
    optimized_ms = benchmark_mac(pattern, filter_a, runs=10, use_flatten=True)

    for line in render_section_header("# [3] MAC 결과"):
        output_func(line)
    output_func(f"A 점수: {score_a}")
    output_func(f"B 점수: {score_b}")
    output_func(f"연산 시간(평균/10회, 2D): {average_ms:.6f} ms")
    output_func(f"연산 시간(평균/10회, 1D): {optimized_ms:.6f} ms")
    output_func(f"판정: {decision}")
    return {
        "score_a": score_a,
        "score_b": score_b,
        "decision": decision,
        "two_d_ms": average_ms,
        "one_d_ms": optimized_ms,
    }


def run_json_mode(data_path: str | Path = "data.json", output_func=print) -> dict:
    target_path = Path(data_path)
    if not target_path.exists():
        save_default_data(target_path)
        output_func(f"기본 data.json을 생성했습니다: {target_path}")

    report = analyze_data_file(target_path)
    payload = json.loads(target_path.read_text(encoding="utf-8"))

    for line in render_section_header("# [1] 필터 로드"):
        output_func(line)
    for size_key in sorted(payload["filters"].keys()):
        output_func(f"✓ {size_key} 필터 로드 완료 (Cross, X)")

    for line in render_section_header("# [2] 패턴 분석 (라벨 정규화 적용)"):
        output_func(line)
    for result in report["results"]:
        output_func(f"--- {result['case_id']} ---")
        if result["cross_score"] is None:
            output_func(f"판정 불가 | expected: {result['expected']} | FAIL")
            output_func(f"reason: {result['reason']}")
        else:
            output_func(f"Cross 점수: {result['cross_score']}")
            output_func(f"X 점수: {result['x_score']}")
            output_func(f"판정: {result['predicted']} | expected: {result['expected']} | {result['status']}")

    for line in render_section_header("# [3] 성능 분석 (평균/10회)"):
        output_func(line)
    for line in render_performance_lines(report["performance"]):
        output_func(line)

    for line in render_section_header("# [4] 결과 요약"):
        output_func(line)
    output_func(f"총 테스트: {report['summary']['total']}개")
    output_func(f"통과: {report['summary']['passed']}개")
    output_func(f"실패: {report['summary']['failed']}개")
    if report["failures"]:
        output_func("실패 케이스:")
        for failure in report["failures"]:
            output_func(f"- {failure['case_id']}: {failure['reason']}")

    return report


def main(input_func=input, output_func=print) -> None:
    output_func("=== Mini NPU Simulator ===")
    output_func("[모드 선택]")
    output_func("1. 사용자 입력 (3x3)")
    output_func("2. data.json 분석")
    output_func("3. 패턴 생성기 (보너스)")
    choice = input_func("선택: ").strip()

    if choice == "1":
        run_manual_mode(input_func=input_func, output_func=output_func)
    elif choice == "2":
        run_json_mode(output_func=output_func)
    elif choice == "3":
        run_pattern_generator_mode(input_func=input_func, output_func=output_func)
    else:
        output_func("잘못된 선택입니다. 1, 2 또는 3을 입력하세요.")



def safe_main(input_func=input, output_func=print) -> None:
    try:
        main(input_func=input_func, output_func=output_func)
    except EOFError:
        output_func("입력이 종료되어 프로그램을 종료합니다.")
    except KeyboardInterrupt:
        output_func("프로그램을 종료합니다.")


if __name__ == "__main__":
    safe_main()
