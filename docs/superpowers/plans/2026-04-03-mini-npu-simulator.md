# Mini NPU Simulator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python console app that classifies Cross/X patterns with MAC operations, supports manual and JSON-driven analysis, measures performance, and includes both bonus tasks.

**Architecture:** Keep the runtime in `main.py` with small, testable units: matrix validation, pattern generation, MAC scoring, JSON analysis, performance measurement, and console flows. Use `tests/test_main.py` for standard-library `unittest` coverage so implementation can stay dependency-free while still following TDD.

**Tech Stack:** Python 3.10+, standard library only (`json`, `time`, `pathlib`, `dataclasses`, `re`, `unittest`, `tempfile`)

---

## File Structure

- Create: `d:/Projects/Github/1_month_crunch/main.py` — application entry point plus all runtime helpers for matrix handling, MAC, JSON analysis, performance, and console flows
- Create: `d:/Projects/Github/1_month_crunch/data.json` — deterministic dataset for batch analysis, including pass cases and analyzable fail cases
- Create: `d:/Projects/Github/1_month_crunch/tests/__init__.py` — enables package-style unittest imports
- Create: `d:/Projects/Github/1_month_crunch/tests/test_main.py` — unit tests for pure helpers and flow-level functions using injected input/output callables
- Modify: `d:/Projects/Github/1_month_crunch/README.md` — execution guide, schema explanation, results report, complexity analysis, and bonus notes

### Task 1: Add matrix, label, and pattern foundations

**Files:**
- Create: `d:/Projects/Github/1_month_crunch/tests/__init__.py`
- Create: `d:/Projects/Github/1_month_crunch/tests/test_main.py`
- Create: `d:/Projects/Github/1_month_crunch/main.py`
- Test: `d:/Projects/Github/1_month_crunch/tests/test_main.py`

- [ ] **Step 1: Write the failing foundation tests**

Write `d:/Projects/Github/1_month_crunch/tests/__init__.py` as an empty file, then create `d:/Projects/Github/1_month_crunch/tests/test_main.py` with this content:

```python
import unittest

from main import Matrix, generate_cross_pattern, generate_x_pattern, normalize_label


class FoundationTests(unittest.TestCase):
    def test_matrix_rejects_non_square_input(self) -> None:
        with self.assertRaises(ValueError):
            Matrix([[1, 0, 1], [0, 1, 0]])

    def test_normalize_label_variants(self) -> None:
        self.assertEqual(normalize_label("+"), "Cross")
        self.assertEqual(normalize_label("cross"), "Cross")
        self.assertEqual(normalize_label("x"), "X")

    def test_generate_cross_and_x_patterns(self) -> None:
        cross = generate_cross_pattern(5)
        x_pattern = generate_x_pattern(5)

        self.assertEqual(cross.values[2], [1.0, 1.0, 1.0, 1.0, 1.0])
        self.assertEqual([row[2] for row in cross.values], [1.0, 1.0, 1.0, 1.0, 1.0])
        self.assertEqual(x_pattern.values[0][0], 1.0)
        self.assertEqual(x_pattern.values[0][4], 1.0)
        self.assertEqual(x_pattern.values[2][2], 1.0)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the foundation tests to verify they fail**

Run:

```bash
python -m unittest tests.test_main -v
```

Expected: FAIL with `ImportError` or `AttributeError` because `main.py` does not yet define the imported names.

- [ ] **Step 3: Write the minimal matrix and pattern implementation**

Create `d:/Projects/Github/1_month_crunch/main.py` with this content:

```python
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
```

- [ ] **Step 4: Run the foundation tests again to verify they pass**

Run:

```bash
python -m unittest tests.test_main -v
```

Expected: PASS with `OK`.

- [ ] **Step 5: Commit the foundation layer**

Run:

```bash
git add main.py tests/__init__.py tests/test_main.py
git commit -m "feat: add matrix and pattern foundations"
```

### Task 2: Add MAC scoring, epsilon judgement, and timing helpers

**Files:**
- Modify: `d:/Projects/Github/1_month_crunch/tests/test_main.py`
- Modify: `d:/Projects/Github/1_month_crunch/main.py`
- Test: `d:/Projects/Github/1_month_crunch/tests/test_main.py`

- [ ] **Step 1: Add failing tests for scoring and timing**

Append these tests to `d:/Projects/Github/1_month_crunch/tests/test_main.py`:

```python
from main import EPSILON, benchmark_mac, judge_scores, mac_1d, mac_2d


class MacTests(unittest.TestCase):
    def test_mac_scores_and_flattened_scores_match(self) -> None:
        cross = generate_cross_pattern(3)
        x_pattern = generate_x_pattern(3)

        self.assertEqual(mac_2d(cross, cross), 5.0)
        self.assertEqual(mac_2d(cross, x_pattern), 1.0)
        self.assertEqual(mac_2d(cross, x_pattern), mac_1d(cross.flatten(), x_pattern.flatten()))

    def test_judge_scores_uses_epsilon_for_ties(self) -> None:
        self.assertEqual(judge_scores(1.0, 1.0 + (EPSILON / 2)), "UNDECIDED")
        self.assertEqual(judge_scores(5.0, 1.0), "Cross")
        self.assertEqual(judge_scores(1.0, 5.0), "X")

    def test_benchmark_mac_returns_non_negative_milliseconds(self) -> None:
        cross = generate_cross_pattern(5)
        average_ms = benchmark_mac(cross, cross, runs=10, use_flatten=False)
        self.assertGreaterEqual(average_ms, 0.0)
```

- [ ] **Step 2: Run the scoring tests to verify they fail**

Run:

```bash
python -m unittest tests.test_main.MacTests -v
```

Expected: FAIL because the MAC, judgement, and benchmark helpers do not exist yet.

- [ ] **Step 3: Implement MAC scoring and benchmark helpers**

Add these functions to `d:/Projects/Github/1_month_crunch/main.py` below the pattern generators:

```python
from time import perf_counter


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
```

Also update the imports at the top of `d:/Projects/Github/1_month_crunch/main.py` to:

```python
from dataclasses import dataclass
from time import perf_counter
```

- [ ] **Step 4: Re-run the scoring tests to verify they pass**

Run:

```bash
python -m unittest tests.test_main.MacTests -v
```

Expected: PASS with `OK`.

- [ ] **Step 5: Commit the MAC logic**

Run:

```bash
git add main.py tests/test_main.py
git commit -m "feat: add mac scoring and benchmark helpers"
```

### Task 3: Add JSON dataset generation, validation, and batch analysis

**Files:**
- Modify: `d:/Projects/Github/1_month_crunch/tests/test_main.py`
- Modify: `d:/Projects/Github/1_month_crunch/main.py`
- Create: `d:/Projects/Github/1_month_crunch/data.json`
- Test: `d:/Projects/Github/1_month_crunch/tests/test_main.py`

- [ ] **Step 1: Add failing tests for dataset generation and analysis**

Append these tests to `d:/Projects/Github/1_month_crunch/tests/test_main.py`:

```python
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from main import analyze_data_file, save_default_data


class JsonAnalysisTests(unittest.TestCase):
    def test_save_default_data_writes_required_sections(self) -> None:
        with TemporaryDirectory() as temp_dir:
            data_path = Path(temp_dir) / "data.json"
            save_default_data(data_path)
            payload = json.loads(data_path.read_text(encoding="utf-8"))

        self.assertEqual(sorted(payload["filters"].keys()), ["size_13", "size_25", "size_5"])
        self.assertIn("size_5_1", payload["patterns"])
        self.assertIn("size_25_3", payload["patterns"])

    def test_analyze_data_file_returns_summary_and_fail_reasons(self) -> None:
        with TemporaryDirectory() as temp_dir:
            data_path = Path(temp_dir) / "data.json"
            save_default_data(data_path)
            report = analyze_data_file(data_path)

        self.assertEqual(report["summary"]["total"], 8)
        self.assertEqual(report["summary"]["passed"], 6)
        self.assertEqual(report["summary"]["failed"], 2)
        self.assertIn("size_13_3", {item["case_id"] for item in report["results"]})
        self.assertIn("size_25_3", {item["case_id"] for item in report["failures"]})
```

- [ ] **Step 2: Run the JSON tests to verify they fail**

Run:

```bash
python -m unittest tests.test_main.JsonAnalysisTests -v
```

Expected: FAIL because `save_default_data` and `analyze_data_file` do not exist yet.

- [ ] **Step 3: Implement dataset generation and batch analysis helpers**

Add these imports near the top of `d:/Projects/Github/1_month_crunch/main.py`:

```python
import json
import re
from pathlib import Path
```

Then add these functions below `benchmark_mac` in `d:/Projects/Github/1_month_crunch/main.py`:

```python
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
```

- [ ] **Step 4: Generate the actual batch dataset file**

Run:

```bash
python - <<'PY'
from main import save_default_data
save_default_data("data.json")
PY
```

Expected: a new `d:/Projects/Github/1_month_crunch/data.json` file containing filter groups for 5, 13, and 25 and eight pattern cases.

- [ ] **Step 5: Re-run the JSON tests to verify they pass**

Run:

```bash
python -m unittest tests.test_main.JsonAnalysisTests -v
```

Expected: PASS with `OK`.

- [ ] **Step 6: Commit the batch-analysis layer**

Run:

```bash
git add main.py data.json tests/test_main.py
git commit -m "feat: add batch analysis and seed dataset"
```

### Task 4: Add interactive console flows for manual mode and batch mode

**Files:**
- Modify: `d:/Projects/Github/1_month_crunch/tests/test_main.py`
- Modify: `d:/Projects/Github/1_month_crunch/main.py`
- Test: `d:/Projects/Github/1_month_crunch/tests/test_main.py`

- [ ] **Step 1: Add failing tests for row parsing and manual mode retry behavior**

Append these tests to `d:/Projects/Github/1_month_crunch/tests/test_main.py`:

```python
from main import parse_matrix_row, run_manual_mode


class ConsoleFlowTests(unittest.TestCase):
    def test_parse_matrix_row_validates_column_count_and_numbers(self) -> None:
        self.assertEqual(parse_matrix_row("1 0 1", 3), [1.0, 0.0, 1.0])

        with self.assertRaises(ValueError):
            parse_matrix_row("1 0", 3)

        with self.assertRaises(ValueError):
            parse_matrix_row("1 a 0", 3)

    def test_run_manual_mode_retries_invalid_input_and_returns_decision(self) -> None:
        answers = iter(
            [
                "1 0",
                "0 1 0",
                "1 1 1",
                "0 1 0",
                "1 0 1",
                "0 1 0",
                "1 0 1",
                "1 0 1",
                "0 1 0",
                "1 0 1",
            ]
        )
        output: list[str] = []

        result = run_manual_mode(input_func=lambda _: next(answers), output_func=output.append)

        self.assertEqual(result["decision"], "B")
        self.assertTrue(any("입력 형식 오류" in line for line in output))
```

- [ ] **Step 2: Run the console-flow tests to verify they fail**

Run:

```bash
python -m unittest tests.test_main.ConsoleFlowTests -v
```

Expected: FAIL because parsing and manual-mode helpers do not exist yet.

- [ ] **Step 3: Implement parsing, console modes, and the entry point**

Append these functions to `d:/Projects/Github/1_month_crunch/main.py`:

```python
def parse_matrix_row(raw_text: str, expected_size: int) -> list[float]:
    parts = raw_text.strip().split()
    if len(parts) != expected_size:
        raise ValueError(f"각 줄에 {expected_size}개의 숫자를 공백으로 구분해 입력하세요.")

    try:
        return [float(part) for part in parts]
    except ValueError as error:
        raise ValueError(f"각 줄에 {expected_size}개의 숫자를 공백으로 구분해 입력하세요.") from error


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


def run_manual_mode(input_func=input, output_func=print) -> dict:
    output_func("=== Mini NPU Simulator ===")
    filter_a = read_matrix_from_input("필터 A (3줄 입력, 공백 구분)", 3, input_func=input_func, output_func=output_func)
    filter_b = read_matrix_from_input("필터 B (3줄 입력, 공백 구분)", 3, input_func=input_func, output_func=output_func)
    pattern = read_matrix_from_input("패턴 (3줄 입력, 공백 구분)", 3, input_func=input_func, output_func=output_func)

    score_a = mac_2d(pattern, filter_a)
    score_b = mac_2d(pattern, filter_b)
    decision = "판정 불가" if abs(score_a - score_b) < EPSILON else ("A" if score_a > score_b else "B")
    average_ms = benchmark_mac(pattern, filter_a, runs=10, use_flatten=False)
    optimized_ms = benchmark_mac(pattern, filter_a, runs=10, use_flatten=True)

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

    output_func("=== data.json 분석 결과 ===")
    for result in report["results"]:
        if result["cross_score"] is None:
            output_func(f"{result['case_id']}: FAIL | reason: {result['reason']}")
        else:
            output_func(
                f"{result['case_id']}: Cross={result['cross_score']}, X={result['x_score']}, "
                f"판정={result['predicted']}, expected={result['expected']}, {result['status']}"
            )

    output_func("=== 성능 분석 ===")
    for line in render_performance_lines(report["performance"]):
        output_func(line)

    output_func("=== 결과 요약 ===")
    output_func(f"총 테스트: {report['summary']['total']}")
    output_func(f"통과: {report['summary']['passed']}")
    output_func(f"실패: {report['summary']['failed']}")
    for failure in report["failures"]:
        output_func(f"- {failure['case_id']}: {failure['reason']}")

    return report


def main(input_func=input, output_func=print) -> None:
    output_func("=== Mini NPU Simulator ===")
    output_func("1. 사용자 입력 (3x3)")
    output_func("2. data.json 분석")
    choice = input_func("선택: ").strip()

    if choice == "1":
        run_manual_mode(input_func=input_func, output_func=output_func)
    elif choice == "2":
        run_json_mode(output_func=output_func)
    else:
        output_func("잘못된 선택입니다. 1 또는 2를 입력하세요.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Re-run the console-flow tests to verify they pass**

Run:

```bash
python -m unittest tests.test_main.ConsoleFlowTests -v
```

Expected: PASS with `OK`.

- [ ] **Step 5: Run the full test suite and both console smoke checks**

Run:

```bash
python -m unittest -v
printf "1\n0 1 0\n1 1 1\n0 1 0\n1 0 1\n0 1 0\n1 0 1\n1 0 1\n0 1 0\n1 0 1\n" | python main.py
printf "2\n" | python main.py
```

Expected:
- `python -m unittest -v` ends with `OK`
- Manual mode prints `판정: B`
- Batch mode prints totals `총 테스트: 8`, `통과: 6`, `실패: 2`

- [ ] **Step 6: Commit the console flows**

Run:

```bash
git add main.py tests/test_main.py data.json
git commit -m "feat: add interactive console modes"
```

### Task 5: Rewrite README with execution guide and result report

**Files:**
- Modify: `d:/Projects/Github/1_month_crunch/README.md`
- Test: `d:/Projects/Github/1_month_crunch/main.py`

- [ ] **Step 1: Capture the final outputs you will cite in the README**

Run:

```bash
printf "1\n0 1 0\n1 1 1\n0 1 0\n1 0 1\n0 1 0\n1 0 1\n1 0 1\n0 1 0\n1 0 1\n" | python main.py
printf "2\n" | python main.py
python -m unittest -v
```

Expected: command outputs provide the exact values and summary lines to cite in the README sections.

- [ ] **Step 2: Replace `d:/Projects/Github/1_month_crunch/README.md` with a submission-ready report**

Write `d:/Projects/Github/1_month_crunch/README.md` with these sections in this exact order:

```markdown
# 1_month_crunch

## 1. 프로젝트 개요
- Mini NPU Simulator 과제 목적
- 사용자 입력 모드 / data.json 분석 모드 / 성능 분석 / 보너스 기능 요약

## 2. 실행 환경
- Python 3.10+
- Standard Library only
- 확인한 OS / shell 정보

## 3. 실행 방법
```bash
python main.py
```
- 메뉴 1: 사용자 입력 (3x3)
- 메뉴 2: data.json 분석
- `data.json`이 없으면 자동 생성된다고 명시

## 4. 파일 구조
```text
.
├─ README.md
├─ data.json
├─ main.py
└─ tests/
   ├─ __init__.py
   └─ test_main.py
```

## 5. 구현 요약
- `Matrix`의 책임
- 라벨 정규화 규칙 (`+`/`cross` -> `Cross`, `x` -> `X`)
- 2D MAC / 1D MAC 차이
- epsilon 정책과 `UNDECIDED`

## 6. 핵심 기능 설명
### 사용자 입력 모드
- 3x3 필터 A/B 입력
- 잘못된 입력 시 재입력 유도
- A/B/판정 불가 출력

### data.json 분석 모드
- `filters.size_5`, `size_13`, `size_25`
- `patterns.size_{N}_{idx}` 규칙
- PASS / FAIL / 실패 사유 출력

### 보너스 기능
- 패턴 생성기
- 1차원 배열 최적화 비교

## 7. data.json 구조 설명
- 최상위 `filters`, `patterns`
- 각 size 필터 구조
- 각 pattern의 `input`, `expected`
- 의도적으로 포함한 실패 케이스 2개 설명

## 8. 결과 리포트
- 총 테스트 / 통과 / 실패 수를 실제 실행 결과로 적기
- 실패 원인 분석을 10줄 이상 작성하기
- `size_13_3`은 동점으로 `UNDECIDED`가 되어 FAIL이 되는 이유 설명
- `size_25_3`은 스키마/크기 불일치 FAIL이라는 점 설명
- 정규화와 epsilon 정책 덕분에 나머지 케이스가 안정적으로 PASS가 되는 이유 설명

## 9. 성능 분석
- 3x3 / 5x5 / 13x13 / 25x25 표 작성
- `크기 | 2D 평균(ms) | 1D 평균(ms) | 연산 횟수(N²)` 형식 사용
- 입력/출력 시간 제외, MAC 호출만 측정했다고 설명
- O(N²) 근거를 연산 횟수와 연결해서 설명

## 10. 테스트 및 검증
```bash
python -m unittest -v
```
- 수동 입력 예시 검증
- batch 모드 검증

## 11. 트러블슈팅 / 배운 점
- 부동소수점 동점 처리 필요성
- JSON 스키마 검증 필요성
- 1D 최적화가 구조를 단순화하지만 복잡도 자체는 바꾸지 않는다는 점
```

Use the real measured numbers from Step 1 in sections 8 and 9 instead of invented values.

- [ ] **Step 3: Run the final verification pass**

Run:

```bash
python -m unittest -v && printf "2\n" | python main.py
```

Expected: tests pass and batch mode still prints `총 테스트: 8`, `통과: 6`, `실패: 2` after the README rewrite.

- [ ] **Step 4: Commit the finished submission**

Run:

```bash
git add README.md main.py data.json tests/test_main.py
git commit -m "docs: add mini npu simulator report"
```

## Self-Review

### 1. Spec coverage
- Manual 3x3 input with validation: covered in Task 4
- JSON load, size parsing, schema handling, case-level FAIL behavior: covered in Task 3
- Label normalization and epsilon policy: covered in Tasks 1-3
- Performance analysis for 3x3 / 5x5 / 13x13 / 25x25: covered in Tasks 2-4 and documented in Task 5
- Bonus 1D optimization and pattern generator: covered in Tasks 1-4
- README result report with failure analysis and O(N²): covered in Task 5

No gaps found.

### 2. Placeholder scan
- No `TODO`, `TBD`, or “implement later” markers remain.
- Each code-changing step includes the exact content to add or run.
- Commands and expected outcomes are spelled out for every test/verification step.

### 3. Type consistency
- `Matrix`, `normalize_label`, `generate_cross_pattern`, `generate_x_pattern`, `mac_2d`, `mac_1d`, `judge_scores`, `benchmark_mac`, `save_default_data`, `analyze_data_file`, `parse_matrix_row`, `run_manual_mode`, `run_json_mode`, and `main` are referenced consistently across tasks.
- Batch-analysis result keys (`results`, `failures`, `summary`, `performance`) stay consistent between implementation and tests.
