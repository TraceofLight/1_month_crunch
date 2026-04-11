# Pattern Generator Exposure and Graceful Exit Design

- Date: 2026-04-11
- Project: `1_month_crunch`
- Target branch: `e1-3`
- Target files: `main.py`, `tests/test_main.py`, `README.md`

## 1. Goal

Expose the already-implemented bonus pattern generator as a visible console feature, let generated patterns be reused in performance analysis and optionally appended to `data.json`, and make program termination via `Ctrl+C` / `Ctrl+D` end cleanly without raw interrupt output.

## 2. Why this change is needed

The current code already contains the core bonus primitives:
- odd-size `Cross` pattern generation
- odd-size `X` pattern generation
- flattened 1D MAC optimization
- 2D vs 1D benchmark comparison

However, the bonus feature is mostly internal. A user cannot discover or run the generator directly from the menu, so the implementation is easy to miss during review. The assignment wording expects the generator to be an actual usable feature, not only helper functions hidden in code.

Separately, the current console flow does not handle `KeyboardInterrupt` and `EOFError` gracefully, so `Ctrl+C` / `Ctrl+D` produces an unfriendly termination path.

## 3. Scope

### In scope
- Add a third menu option for the bonus pattern generator.
- Let the user enter an odd size `N >= 3`.
- Let the user choose `Cross` or `X`.
- Print the generated `N x N` pattern in the console.
- Reuse that generated pattern immediately for 2D/1D performance analysis.
- Offer optional persistence of the generated pattern into `data.json`.
- If a generated pattern is stored for a size with no matching filter group, keep batch analysis stable and mark the case as `FAIL` with an explicit “cannot judge because related filter is missing” style reason.
- Handle `Ctrl+C` and `Ctrl+D` cleanly across the program.
- Update README so the exposed bonus feature is visible in the documentation.

### Out of scope
- Adding a fourth classification label beyond `Cross` and `X`
- Auto-generating missing filter groups for every new size
- Changing mode 1 from fixed 3x3 manual input to arbitrary-size input
- GUI/web output

## 4. User-facing design

## 4-1. Main menu

The main menu will become:

1. 사용자 입력 (3x3)
2. data.json 분석
3. 패턴 생성기 (보너스)

This makes the bonus work directly discoverable during grading and manual review.

## 4-2. Pattern generator flow

The new mode will run in this order:
1. Ask for pattern size `N`.
2. Validate that `N` is an odd integer and `N >= 3`.
3. Ask whether to generate `Cross` or `X`.
4. Build the matrix using the existing generator functions.
5. Print the generated matrix in a simple space-separated format.
6. Run benchmark output on that generated pattern using the matching filter shape.
7. Ask whether to append the generated pattern to `data.json`.
8. If yes, save a new pattern case with the expected label.

## 4-3. `data.json` reuse behavior

When a generated pattern is appended to `data.json`, only the new pattern case is guaranteed to be added.

If the corresponding `filters["size_N"]` group already exists, the case can be judged normally in mode 2.

If the corresponding filter group does not exist, mode 2 must not crash. Instead, it will:
- keep the case in the results
- mark it as `FAIL`
- include a reason that clearly states that related filters are missing, so the case could not be judged

Recommended failure wording:
- `related filters for size_7 are missing, so this case cannot be judged`

The exact wording may vary slightly in Korean, but the reason must communicate “FAIL because judgment was impossible due to missing related filters”, not “FAIL because the pattern itself was wrong”.

## 4-4. Graceful exit behavior

At the top-level program flow, `KeyboardInterrupt` and `EOFError` will be caught and converted into a short user-facing exit message.

Expected behavior:
- no traceback
- no raw `KeyboardInterrupt` line
- clean termination message only

Example messages:
- `프로그램을 종료합니다.`
- `입력이 종료되어 프로그램을 종료합니다.`

A single shared exit path is preferred so the behavior is consistent regardless of which menu or prompt was active when termination happened.

## 5. Internal design

### 5-1. Reuse of existing logic

The implementation should reuse the current helpers wherever possible:
- `generate_cross_pattern(size)`
- `generate_x_pattern(size)`
- `benchmark_mac(...)`
- `render_performance_lines(...)` where applicable
- existing JSON load/save helpers

This change is about exposing and connecting existing capability, not redesigning the simulator.

### 5-2. New helpers

The following focused helpers are expected:
- a size input helper for odd integer validation
- a pattern type selection helper
- a matrix rendering helper for console output
- a function that appends a generated pattern case to `data.json`
- a `run_pattern_generator_mode(...)` console flow
- a top-level safe wrapper for graceful termination

### 5-3. `data.json` append strategy

A generated case key should remain machine-parseable by batch mode.

Current batch mode expects `size_{N}_{idx}`. To stay compatible without broad parser changes, generated cases should follow the same shape, for example:
- `size_7_1`
- `size_7_2`

If the file already contains those keys, the append helper should allocate the next available index for that size.

Each appended case should contain:
- `input`: generated matrix values
- `expected`: raw label source (`+` for Cross or `x` for X) or standardized label, as long as it still works with existing normalization rules

The simplest approach is:
- save `+` for generated Cross cases
- save `x` for generated X cases

## 6. Error handling

### Generator mode input errors
- Non-integer size input
- Even size input
- Size smaller than 3
- Invalid pattern-type selection
- Invalid yes/no selection when asking to append to `data.json`

Behavior:
- print a short guidance message
- re-prompt without crashing

### Batch analysis with missing related filters

If a pattern case references `size_N` but `filters["size_N"]` is absent, the analysis result should be:
- `cross_score = None`
- `x_score = None`
- `predicted = UNDECIDED`
- `status = FAIL`
- `reason = explicit missing-filter explanation`

This keeps the summary counts stable and communicates that the failure came from incomplete comparison resources.

### Graceful termination

`KeyboardInterrupt` and `EOFError` should end the program cleanly from:
- main menu selection
- manual matrix input
- generator size input
- generator choice prompts

## 7. Testing design

The updated tests should cover:

1. Generator mode produces a valid Cross pattern for an odd size.
2. Generator mode produces a valid X pattern for an odd size.
3. Invalid size input re-prompts until a valid odd size is entered.
4. Generated mode prints both 2D and 1D timing output.
5. Appending a generated pattern writes a new `patterns` entry into `data.json`.
6. Batch analysis treats missing related filters as case-level `FAIL` with a readable reason.
7. Top-level execution catches `KeyboardInterrupt` cleanly.
8. Top-level execution catches `EOFError` cleanly.

## 8. README changes

README should be updated to make the bonus feature visibly real, not just mentioned as internal helpers.

It should explicitly state:
- menu option 3 exists
- the user can generate `N x N` Cross/X patterns
- generated patterns can be reused for performance analysis immediately
- generated patterns can be appended to `data.json`
- if matching filters for that size are missing, mode 2 reports a case-level `FAIL` because judgment is not possible
- `Ctrl+C` / `Ctrl+D` exits cleanly

## 9. Implementation notes

This should remain a small, focused enhancement.

The project already has the core logic needed for generation and benchmarking. The main work is:
- surfacing the flow in the menu
- preserving compatibility with current `data.json` analysis behavior
- improving console robustness

No architectural rewrite is needed.

## 10. Handoff

After this design is approved, the next step is to create a concrete implementation plan for:
- `main.py` menu and generator flow updates
- `data.json` append helper changes
- missing-filter failure-message refinement
- graceful `Ctrl+C` / `Ctrl+D` handling
- `tests/test_main.py` coverage
- README bonus-feature documentation updates
