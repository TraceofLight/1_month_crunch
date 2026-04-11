# Output Format Alignment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the console output look closer to the assignment sample while keeping the current dataset, scoring behavior, PASS/FAIL counts, and bonus features unchanged.

**Architecture:** Restrict the change to presentation helpers and console strings inside `main.py`, plus test expectations in `tests/test_main.py`. Keep all computation, dataset generation, and summary logic intact so only the rendered CLI shape changes.

**Tech Stack:** Python 3.12, standard library only (`json`, `re`, `dataclasses`, `pathlib`, `time`, `unittest`, `tempfile`, `unittest.mock`)

---

## File Structure

- Modify: `/Users/heejun_kim/Documents/Github/1_month_crunch/main.py` — adjust menu text, add section-style console rendering, and reformat manual/batch/generator output without changing logic
- Modify: `/Users/heejun_kim/Documents/Github/1_month_crunch/tests/test_main.py` — add/adjust tests to lock in the new output structure while preserving existing behavior
- Optional later sync: `/Users/heejun_kim/Documents/Github/1_month_crunch/README.md` — only if needed after code output is finalized

### Task 1: Lock in the desired manual-mode and menu output format with failing tests

**Files:**
- Modify: `/Users/heejun_kim/Documents/Github/1_month_crunch/tests/test_main.py`
- Test: `/Users/heejun_kim/Documents/Github/1_month_crunch/tests/test_main.py`

- [ ] **Step 1: Add failing tests for menu and manual-mode formatting**

In `/Users/heejun_kim/Documents/Github/1_month_crunch/tests/test_main.py`, append these tests below `EntryPointTests`:

```python
class OutputFormatTests(unittest.TestCase):
    def test_main_menu_includes_mode_header_and_generator_option(self) -> None:
        output: list[str] = []

        main(input_func=lambda _: "9", output_func=output.append)

        self.assertEqual(output[0], "=== Mini NPU Simulator ===")
        self.assertIn("[모드 선택]", output)
        self.assertIn("1. 사용자 입력 (3x3)", output)
        self.assertIn("2. data.json 분석", output)
        self.assertIn("3. 패턴 생성기 (보너스)", output)

    def test_run_manual_mode_prints_section_headers(self) -> None:
        answers = iter(
            [
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

        run_manual_mode(input_func=lambda _: next(answers), output_func=output.append)

        self.assertIn("# [1] 필터 입력", output)
        self.assertIn("# [2] 패턴 입력", output)
        self.assertIn("# [3] MAC 결과", output)
        self.assertTrue(any(line.startswith("A 점수:") for line in output))
        self.assertTrue(any(line.startswith("B 점수:") for line in output))
        self.assertTrue(any(line.startswith("판정:") for line in output))
```

- [ ] **Step 2: Run the new output-format tests to verify they fail**

Run:

```bash
python -m unittest tests.test_main.OutputFormatTests -v
```

Expected:
- `test_main_menu_includes_mode_header_and_generator_option` fails because `[모드 선택]` is not printed
- `test_run_manual_mode_prints_section_headers` fails because the section-header lines are not printed yet

- [ ] **Step 3: Do not commit this checkpoint**

Per user instruction, leave changes uncommitted.

### Task 2: Implement menu/manual-mode formatting and lock in batch-mode layout with a second failing test

**Files:**
- Modify: `/Users/heejun_kim/Documents/Github/1_month_crunch/main.py`
- Modify: `/Users/heejun_kim/Documents/Github/1_month_crunch/tests/test_main.py`
- Test: `/Users/heejun_kim/Documents/Github/1_month_crunch/tests/test_main.py`

- [ ] **Step 1: Implement the minimal menu/manual output formatting changes**

In `/Users/heejun_kim/Documents/Github/1_month_crunch/main.py`, add a helper above `run_pattern_generator_mode`:

```python
def render_section_header(title: str) -> list[str]:
    return [
        "#----------------------------------------",
        title,
        "#----------------------------------------",
    ]
```

Then update `run_manual_mode(...)` from:

```python
def run_manual_mode(input_func=input, output_func=print) -> dict:
    output_func("=== Mini NPU Simulator ===")
    filter_a = read_matrix_from_input("필터 A (3줄 입력, 공백 구분)", 3, input_func=input_func, output_func=output_func)
    filter_b = read_matrix_from_input("필터 B (3줄 입력, 공백 구분)", 3, input_func=input_func, output_func=output_func)
    pattern = read_matrix_from_input("패턴 (3줄 입력, 공백 구분)", 3, input_func=input_func, output_func=output_func)
```

To:

```python
def run_manual_mode(input_func=input, output_func=print) -> dict:
    output_func("=== Mini NPU Simulator ===")
    for line in render_section_header("# [1] 필터 입력"):
        output_func(line)
    filter_a = read_matrix_from_input("필터 A (3줄 입력, 공백 구분)", 3, input_func=input_func, output_func=output_func)
    filter_b = read_matrix_from_input("필터 B (3줄 입력, 공백 구분)", 3, input_func=input_func, output_func=output_func)

    for line in render_section_header("# [2] 패턴 입력"):
        output_func(line)
    pattern = read_matrix_from_input("패턴 (3줄 입력, 공백 구분)", 3, input_func=input_func, output_func=output_func)
```

Then, just before the score output in the same function, add:

```python
    for line in render_section_header("# [3] MAC 결과"):
        output_func(line)
```

Finally, update `main(...)` from:

```python
def main(input_func=input, output_func=print) -> None:
    output_func("=== Mini NPU Simulator ===")
    output_func("1. 사용자 입력 (3x3)")
    output_func("2. data.json 분석")
    output_func("3. 패턴 생성기 (보너스)")
    choice = input_func("선택: ").strip()
```

To:

```python
def main(input_func=input, output_func=print) -> None:
    output_func("=== Mini NPU Simulator ===")
    output_func("[모드 선택]")
    output_func("1. 사용자 입력 (3x3)")
    output_func("2. data.json 분석")
    output_func("3. 패턴 생성기 (보너스)")
    choice = input_func("선택: ").strip()
```

- [ ] **Step 2: Re-run the output-format tests to verify they pass**

Run:

```bash
python -m unittest tests.test_main.OutputFormatTests -v
```

Expected: PASS with `OK`.

- [ ] **Step 3: Add a failing test for batch-mode sectioned output**

Append this test to `OutputFormatTests` in `/Users/heejun_kim/Documents/Github/1_month_crunch/tests/test_main.py`:

```python
    def test_run_json_mode_prints_sectioned_sample_like_output(self) -> None:
        with TemporaryDirectory() as temp_dir:
            data_path = Path(temp_dir) / "data.json"
            save_default_data(data_path)
            output: list[str] = []

            run_json_mode(data_path=data_path, output_func=output.append)

        self.assertIn("# [1] 필터 로드", output)
        self.assertIn("# [2] 패턴 분석 (라벨 정규화 적용)", output)
        self.assertIn("# [3] 성능 분석 (평균/10회)", output)
        self.assertIn("# [4] 결과 요약", output)
        self.assertIn("--- size_5_1 ---", output)
        self.assertTrue(any(line.startswith("Cross 점수:") for line in output))
        self.assertTrue(any(line.startswith("X 점수:") for line in output))
        self.assertTrue(any(line.startswith("판정:") for line in output))
```

- [ ] **Step 4: Run the batch-format test to verify it fails**

Run:

```bash
python -m unittest tests.test_main.OutputFormatTests.test_run_json_mode_prints_sectioned_sample_like_output -v
```

Expected: FAIL because current batch mode does not print the section headers or per-case multi-line blocks yet.

- [ ] **Step 5: Do not commit this checkpoint**

Per user instruction, leave changes uncommitted.

### Task 3: Implement batch-mode and generator-mode presentation alignment, then run full verification

**Files:**
- Modify: `/Users/heejun_kim/Documents/Github/1_month_crunch/main.py`
- Test: `/Users/heejun_kim/Documents/Github/1_month_crunch/tests/test_main.py`

- [ ] **Step 1: Implement sample-like batch-mode formatting**

In `/Users/heejun_kim/Documents/Github/1_month_crunch/main.py`, replace the body of `run_json_mode(...)` from:

```python
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
```

With:

```python
    report = analyze_data_file(target_path)

    for line in render_section_header("# [1] 필터 로드"):
        output_func(line)
    for size_key in sorted(report_filter_key for report_filter_key in json.loads(target_path.read_text(encoding="utf-8"))["filters"].keys()):
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
```

Then, to avoid reading the JSON file twice, replace the `for size_key in sorted(...)` line block you just inserted with this improved version immediately after `report = analyze_data_file(target_path)`:

```python
    payload = json.loads(target_path.read_text(encoding="utf-8"))
```

And use:

```python
    for size_key in sorted(payload["filters"].keys()):
        output_func(f"✓ {size_key} 필터 로드 완료 (Cross, X)")
```

- [ ] **Step 2: Make the pattern-generator mode visually consistent with the new section style**

In `/Users/heejun_kim/Documents/Github/1_month_crunch/main.py`, update `run_pattern_generator_mode(...)` from:

```python
def run_pattern_generator_mode(data_path: str | Path = "data.json", input_func=input, output_func=print) -> dict:
    output_func("=== 패턴 생성기 (보너스) ===")
    size = read_odd_size(input_func=input_func, output_func=output_func)
    label = read_pattern_kind(input_func=input_func, output_func=output_func)
    pattern = generate_cross_pattern(size) if label == "Cross" else generate_x_pattern(size)

    output_func(f"생성된 패턴 ({label}, {size}x{size})")
```

To:

```python
def run_pattern_generator_mode(data_path: str | Path = "data.json", input_func=input, output_func=print) -> dict:
    output_func("=== Mini NPU Simulator ===")
    for line in render_section_header("# [보너스] 패턴 생성기"):
        output_func(line)
    size = read_odd_size(input_func=input_func, output_func=output_func)
    label = read_pattern_kind(input_func=input_func, output_func=output_func)
    pattern = generate_cross_pattern(size) if label == "Cross" else generate_x_pattern(size)

    output_func(f"생성된 패턴 ({label}, {size}x{size})")
```

Then add section headers before timing and optional save prompt:

```python
    for line in render_section_header("# [성능 비교]"):
        output_func(line)
```

Insert that immediately before:

```python
    two_d_ms = benchmark_mac(pattern, pattern, runs=10, use_flatten=False)
```

And insert:

```python
    for line in render_section_header("# [저장 여부]"):
        output_func(line)
```

Immediately before:

```python
    saved_case_id = None
```

- [ ] **Step 3: Run the focused output-format tests to verify they pass**

Run:

```bash
python -m unittest tests.test_main.OutputFormatTests -v
```

Expected: PASS with `OK`.

- [ ] **Step 4: Run the full suite and sample smoke commands**

Run:

```bash
python -m unittest -v && printf "1\n0 1 0\n1 1 1\n0 1 0\n1 0 1\n0 1 0\n1 0 1\n1 0 1\n0 1 0\n1 0 1\n" | python main.py && printf "2\n" | python main.py && printf "3\n5\n1\nn\n" | python main.py
```

Expected:
- all tests pass
- manual mode prints section headers and still ends with `판정: B`
- batch mode prints four major sections and still reports the same case outcomes and totals
- generator mode prints the new bonus sections and still shows 2D/1D timings

- [ ] **Step 5: Do not commit this checkpoint**

Per user instruction, leave changes uncommitted.

## Self-Review

### 1. Spec coverage
- Mode header and menu alignment: covered in Tasks 1-2
- Manual-mode section layout: covered in Tasks 1-2
- Batch-mode section layout and per-case formatting: covered in Task 3
- Generator-mode visual alignment: covered in Task 3
- No changes to data, scoring, or PASS/FAIL behavior: preserved by scope and verification steps

No gaps found.

### 2. Placeholder scan
- No `TODO`, `TBD`, or “implement later” markers remain.
- Each change step includes exact code to add or replace.
- Each verification step includes exact commands and expected outcomes.
- Commit steps are intentionally replaced with explicit no-commit checkpoints to match the user instruction.

### 3. Type consistency
- All planned references use existing function names consistently: `main`, `run_manual_mode`, `run_json_mode`, `run_pattern_generator_mode`, `render_section_header`.
- No new data fields are introduced; only rendering changes are planned.
