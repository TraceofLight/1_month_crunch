# Pattern Generator Exposure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expose the bonus pattern generator in the console menu, let generated patterns be benchmarked and optionally appended to `data.json`, report missing related filters as readable case-level FAILs, and exit cleanly on `Ctrl+C` / `Ctrl+D`.

**Architecture:** Keep all runtime behavior in `main.py` and extend the current single-file structure with a few focused helpers: generator input/read helpers, matrix rendering, `data.json` append logic, and a safe top-level wrapper. Drive the change with `unittest` updates in `tests/test_main.py`, reusing existing generator/MAC helpers instead of restructuring the program.

**Tech Stack:** Python 3.12, standard library only (`json`, `re`, `dataclasses`, `pathlib`, `time`, `unittest`, `tempfile`, `unittest.mock`)

---

## File Structure

- Modify: `/Users/heejun_kim/Documents/Github/1_month_crunch/main.py` — add generator-mode helpers, `data.json` append support, missing-filter failure wording, menu option 3, and graceful `Ctrl+C` / `Ctrl+D` handling
- Modify: `/Users/heejun_kim/Documents/Github/1_month_crunch/tests/test_main.py` — add TDD coverage for generator mode, missing-filter FAIL messaging, menu dispatch, and graceful exit behavior
- Defer: `/Users/heejun_kim/Documents/Github/1_month_crunch/README.md` — document the exposed bonus feature later, per current user instruction to focus on implementation first

### Task 1: Add failing tests for generator mode and missing-filter behavior

**Files:**
- Modify: `/Users/heejun_kim/Documents/Github/1_month_crunch/tests/test_main.py`
- Test: `/Users/heejun_kim/Documents/Github/1_month_crunch/tests/test_main.py`

- [ ] **Step 1: Add the failing tests**

Append these imports near the top of `/Users/heejun_kim/Documents/Github/1_month_crunch/tests/test_main.py`:

```python
from unittest.mock import patch
```

Then append these tests below the existing `ConsoleFlowTests` class in `/Users/heejun_kim/Documents/Github/1_month_crunch/tests/test_main.py`:

```python
from main import append_generated_pattern_case, run_pattern_generator_mode, safe_main


class BonusFeatureTests(unittest.TestCase):
    def test_append_generated_pattern_case_adds_new_case(self) -> None:
        with TemporaryDirectory() as temp_dir:
            data_path = Path(temp_dir) / "data.json"
            save_default_data(data_path)

            case_id = append_generated_pattern_case(data_path, generate_cross_pattern(7), "Cross")
            payload = json.loads(data_path.read_text(encoding="utf-8"))

        self.assertEqual(case_id, "size_7_1")
        self.assertIn("size_7_1", payload["patterns"])
        self.assertEqual(payload["patterns"]["size_7_1"]["expected"], "+")

    def test_run_pattern_generator_mode_retries_invalid_size_and_prints_benchmark(self) -> None:
        answers = iter(["4", "5", "1", "n"])
        output: list[str] = []

        result = run_pattern_generator_mode(input_func=lambda _: next(answers), output_func=output.append)

        self.assertEqual(result["label"], "Cross")
        self.assertEqual(result["size"], 5)
        self.assertIsNone(result["saved_case_id"])
        self.assertTrue(any("홀수" in line for line in output))
        self.assertTrue(any("2D" in line for line in output))
        self.assertTrue(any("1D" in line for line in output))

    def test_analyze_data_file_reports_missing_related_filters_as_readable_fail(self) -> None:
        with TemporaryDirectory() as temp_dir:
            data_path = Path(temp_dir) / "data.json"
            save_default_data(data_path)
            append_generated_pattern_case(data_path, generate_cross_pattern(7), "Cross")

            report = analyze_data_file(data_path)

        reasons = {item["case_id"]: item["reason"] for item in report["failures"]}
        self.assertIn("size_7_1", reasons)
        self.assertIn("관련 필터", reasons["size_7_1"])
        self.assertIn("판정", reasons["size_7_1"])


class EntryPointTests(unittest.TestCase):
    def test_main_dispatches_pattern_generator_mode(self) -> None:
        output: list[str] = []

        with patch("main.run_pattern_generator_mode") as generator_mode:
            main(input_func=lambda _: "3", output_func=output.append)

        generator_mode.assert_called_once()

    def test_safe_main_handles_keyboard_interrupt(self) -> None:
        output: list[str] = []

        safe_main(input_func=lambda _: (_ for _ in ()).throw(KeyboardInterrupt()), output_func=output.append)

        self.assertTrue(any("종료" in line for line in output))

    def test_safe_main_handles_eof_error(self) -> None:
        output: list[str] = []

        safe_main(input_func=lambda _: (_ for _ in ()).throw(EOFError()), output_func=output.append)

        self.assertTrue(any("입력이 종료" in line or "종료" in line for line in output))
```

- [ ] **Step 2: Run the new tests to verify they fail**

Run:

```bash
python -m unittest tests.test_main.BonusFeatureTests tests.test_main.EntryPointTests -v
```

Expected:
- `ImportError` or `AttributeError` for `append_generated_pattern_case`, `run_pattern_generator_mode`, or `safe_main`
- `test_main_dispatches_pattern_generator_mode` fails because menu option `3` is not implemented
- missing-filter reason assertion fails because current error text is only a raw missing key

- [ ] **Step 3: Do not commit this checkpoint**

Per user instruction, leave changes uncommitted.

### Task 2: Implement generator helpers, `data.json` append flow, and readable missing-filter FAILs

**Files:**
- Modify: `/Users/heejun_kim/Documents/Github/1_month_crunch/main.py`
- Test: `/Users/heejun_kim/Documents/Github/1_month_crunch/tests/test_main.py`

- [ ] **Step 1: Add the generator-mode helper functions**

Insert these functions in `/Users/heejun_kim/Documents/Github/1_month_crunch/main.py` below `render_performance_lines`:

```python
def render_matrix_lines(matrix: Matrix) -> list[str]:
    return [" ".join(str(int(value)) if value.is_integer() else str(value) for value in row) for row in matrix.values]



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
    output_func("=== 패턴 생성기 (보너스) ===")
    size = read_odd_size(input_func=input_func, output_func=output_func)
    label = read_pattern_kind(input_func=input_func, output_func=output_func)
    pattern = generate_cross_pattern(size) if label == "Cross" else generate_x_pattern(size)

    output_func(f"생성된 패턴 ({label}, {size}x{size})")
    for line in render_matrix_lines(pattern):
        output_func(line)

    two_d_ms = benchmark_mac(pattern, pattern, runs=10, use_flatten=False)
    one_d_ms = benchmark_mac(pattern, pattern, runs=10, use_flatten=True)
    output_func(f"연산 시간(평균/10회, 2D): {two_d_ms:.6f} ms")
    output_func(f"연산 시간(평균/10회, 1D): {one_d_ms:.6f} ms")

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
```

- [ ] **Step 2: Replace the raw missing-filter lookup with a readable case-level FAIL reason**

In `/Users/heejun_kim/Documents/Github/1_month_crunch/main.py`, replace the start of `analyze_case(...)` from:

```python
        size = parse_pattern_size(case_id)
        filter_group = filters[f"size_{size}"]
        pattern = matrix_from_raw(case_payload["input"])
        expected = normalize_label(case_payload["expected"])
```

To:

```python
        size = parse_pattern_size(case_id)
        filter_key = f"size_{size}"
        pattern = matrix_from_raw(case_payload["input"])
        expected = normalize_label(case_payload["expected"])

        if filter_key not in filters:
            raise ValueError(f"관련 필터가 없어 판정할 수 없음: {filter_key}")

        filter_group = filters[filter_key]
```

This keeps the failure local to the case while producing the readable reason required by the spec.

- [ ] **Step 3: Run the focused tests to verify they now pass**

Run:

```bash
python -m unittest tests.test_main.BonusFeatureTests -v
```

Expected: PASS with `OK`.

- [ ] **Step 4: Do not commit this checkpoint**

Per user instruction, leave changes uncommitted.

### Task 3: Integrate menu option 3 and add graceful `Ctrl+C` / `Ctrl+D` handling

**Files:**
- Modify: `/Users/heejun_kim/Documents/Github/1_month_crunch/main.py`
- Test: `/Users/heejun_kim/Documents/Github/1_month_crunch/tests/test_main.py`

- [ ] **Step 1: Update the menu and add the safe wrapper**

In `/Users/heejun_kim/Documents/Github/1_month_crunch/main.py`, replace the current `main(...)` and `if __name__ == "__main__":` block:

```python
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

With:

```python
def main(input_func=input, output_func=print) -> None:
    output_func("=== Mini NPU Simulator ===")
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
```

- [ ] **Step 2: Run the entry-point tests to verify they pass**

Run:

```bash
python -m unittest tests.test_main.EntryPointTests -v
```

Expected: PASS with `OK`.

- [ ] **Step 3: Run the full suite plus console smoke checks**

Run:

```bash
python -m unittest -v && printf "3\n5\n1\nn\n" | python main.py && printf "2\n" | python main.py
```

Expected:
- `python -m unittest -v` ends with `OK`
- generator mode prints the generated `5x5` Cross pattern and both `2D` / `1D` timing lines
- batch mode still ends with summary lines and keeps any missing-filter case as a readable `FAIL`

- [ ] **Step 4: Do not commit this checkpoint**

Per user instruction, leave changes uncommitted.

## Self-Review

### 1. Spec coverage
- Menu exposure of the bonus generator: covered in Task 3
- Odd-size generator input and Cross/X selection: covered in Task 2
- Immediate performance reuse of generated patterns: covered in Task 2
- Optional `data.json` persistence: covered in Task 2
- Missing related filters reported as readable case-level FAILs: covered in Task 2
- Graceful `Ctrl+C` / `Ctrl+D` exit: covered in Task 3
- README update: intentionally deferred because the user asked to do implementation first, then document later

No code-scope gaps found for the current phase.

### 2. Placeholder scan
- No `TODO`, `TBD`, or “implement later” steps remain.
- Each code-edit step includes exact code to add or replace.
- Each verification step includes exact commands and expected results.
- Commit steps were intentionally replaced with explicit no-commit checkpoints to match the user’s instruction.

### 3. Type consistency
- Planned function names are consistent across tests and implementation: `append_generated_pattern_case`, `run_pattern_generator_mode`, and `safe_main`.
- Result keys returned by generator mode remain consistent: `size`, `label`, `pattern`, `two_d_ms`, `one_d_ms`, `saved_case_id`.
- Missing-filter handling uses the existing `analyze_case` result schema without introducing new fields.
