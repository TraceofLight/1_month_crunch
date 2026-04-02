from __future__ import annotations

from dataclasses import dataclass
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
