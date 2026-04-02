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
        filter_group = filters[f"size_{size}"]
        pattern = matrix_from_raw(case_payload["input"])
        expected = normalize_label(case_payload["expected"])

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
