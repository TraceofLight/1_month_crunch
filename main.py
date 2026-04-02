from __future__ import annotations

from dataclasses import dataclass


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
