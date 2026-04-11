# Mini NPU Simulator Design

- Date: 2026-04-03
- Project: `1_month_crunch`
- Target branch: `e1-3`
- Deliverables: `main.py`, `data.json`, `README.md`

## 1. Goal

Build a Python console application that simulates MAC (Multiply-Accumulate) operations used for simple pattern recognition. The program must support both manual 3x3 input and batch analysis from `data.json`, measure performance by matrix size, and include both bonus tasks: a 1D-array optimization path and an automatic pattern generator.

## 2. Scope

### Required scope
- Console menu with two execution modes
  1. Manual input for 3x3 filters/patterns
  2. `data.json` batch analysis
- Direct MAC implementation using loops only
- Input validation for manual mode
- JSON loading and schema/size validation for batch mode
- Label normalization to internal standard labels `Cross` and `X`
- Epsilon-based tie handling with `UNDECIDED`
- Performance measurement in milliseconds with at least 10 iterations
- Summary report for total/pass/fail and failed cases
- README with execution guide and result report

### Bonus scope
- 1D flattened-array MAC implementation and performance comparison against the 2D version
- Pattern generator for odd-size `Cross` and `X` matrices, reused for sample data and performance analysis

## 3. Design Principles

- Keep the program simple enough to remain understandable in one file if possible, but separate responsibilities clearly through small classes and functions.
- Use only Python standard library modules.
- Prefer deterministic sample data so the README analysis remains reproducible.
- Treat malformed JSON cases as case-level failures instead of terminating the program.
- Keep the data model and printed labels consistent with the assignment wording.

## 4. Program Structure

Implementation will use `main.py` as the single entry point, with a small set of focused classes/functions inside it.

### Planned components

#### `Matrix`
- Stores an `n x n` numeric matrix as a 2D list.
- Validates square shape when created from loaded or input data.
- Supports flattening to a 1D list for the optimized path.

#### Label normalization helpers
- Normalize filter keys and expected labels into internal labels:
  - `cross`, `+` -> `Cross`
  - `x` -> `X`
- Keep output and comparisons based on `Cross` / `X` only.

#### Pattern generator
- `generate_cross_pattern(size)`
- `generate_x_pattern(size)`
- Produces odd-sized matrices for 3x3, 5x5, 13x13, 25x25.
- Reused when generating `data.json` and when preparing performance-analysis samples.

#### MAC engines
- `mac_2d(pattern, filter_matrix)`
- `mac_1d(pattern_flat, filter_flat)`
- Both return numeric scores and must match logically.
- No external vectorized libraries are allowed.

#### Judgement helpers
- Compare `Cross` and `X` scores.
- If `abs(score_cross - score_x) < 1e-9`, return `UNDECIDED`.
- Otherwise return the higher-scoring label.
- Batch mode marks only exact `Cross`/`X` matches as `PASS`; `UNDECIDED` becomes `FAIL`.

#### Manual input flow helpers
- Read a fixed number of rows for 3x3 matrices.
- Validate row length and numeric parsing.
- Re-prompt on invalid input without terminating.

#### JSON loading / validation helpers
- Load `filters` and `patterns` from `data.json`.
- Expect filters under `size_5`, `size_13`, `size_25`.
- Expect pattern keys of form `size_{N}_{idx}`.
- Extract `N` from each pattern key and map it to the correct filter group.
- Fail a case if shape, schema, or size matching is invalid.

#### Performance helpers
- Time only the MAC call section.
- Run at least 10 iterations and compute average ms.
- Report `N x N`, average time, and operation count `N^2`.
- Compare both 2D and 1D implementations for bonus analysis.

#### Console app flow
- Show menu
- Dispatch to manual mode or batch mode
- Print per-case output, performance tables, and final summary

## 5. Data Design

### `data.json` structure

The project will include a generated `data.json` with this shape:

```json
{
  "filters": {
    "size_5": {
      "cross": "5x5 numeric matrix",
      "x": "5x5 numeric matrix"
    },
    "size_13": {
      "cross": "13x13 numeric matrix",
      "x": "13x13 numeric matrix"
    },
    "size_25": {
      "cross": "25x25 numeric matrix",
      "x": "25x25 numeric matrix"
    }
  },
  "patterns": {
    "size_5_1": {
      "input": "5x5 numeric matrix",
      "expected": "+"
    }
  }
}
```

In the real file, each quoted matrix description above will be replaced by a full square numeric matrix.

### Dataset strategy
- Most cases should pass under the implemented normalization and epsilon policy.
- At least one case may intentionally exercise edge behavior such as near-tie, tie, or schema mismatch so the README can explain failure causes and why the program remains stable.
- The data should remain deterministic and small enough to inspect directly.

## 6. Execution Flow

## Mode 1: Manual 3x3 input
1. Prompt for filter A as three space-separated rows.
2. Prompt for filter B as three space-separated rows.
3. Prompt for a 3x3 input pattern.
4. Compute both MAC scores with the 2D implementation.
5. Judge as `A`, `B`, or undecided for the manual-mode UI.
6. Measure average runtime over 10 runs.
7. Also flatten the same matrices and measure the 1D version for bonus comparison.
8. Print scores, average time, and decision.

## Mode 2: `data.json` analysis
1. Load and validate filter groups.
2. Load pattern cases.
3. For each case:
   - Parse `N` from the key.
   - Select the matching filter group.
   - Validate matrix sizes.
   - Normalize expected label.
   - Compute `Cross` and `X` scores.
   - Judge `Cross`, `X`, or `UNDECIDED`.
   - Print `PASS` or `FAIL`.
4. Aggregate total/pass/fail counts and failed-case reasons.
5. Run performance analysis for 3x3, 5x5, 13x13, 25x25.
6. Print both normal and optimized performance views.

## 7. Error Handling

### Manual input errors
- Wrong number of values in a row
- Wrong number of rows
- Non-numeric input

Behavior:
- Print a clear guidance message.
- Re-prompt until valid input is entered.

### Batch analysis errors
- Missing `filters` or `patterns`
- Missing `size_N` filter group
- Invalid pattern key format
- Missing `input` or `expected`
- Non-square or mismatched matrix sizes

Behavior:
- Do not crash the whole program.
- Mark the case as `FAIL` when the problem is case-local.
- If the whole file cannot be parsed as JSON, print an error and return to the menu or end cleanly.

## 8. Testing Strategy

Implementation will be validated through deterministic scenario checks rather than a separate test framework.

### Core checks
- Cross filter against Cross pattern produces a stronger Cross score.
- X filter against X pattern produces a stronger X score.
- Mixed Cross/X combinations produce lower opposite scores.
- 2D and 1D MAC implementations return the same value for identical inputs.
- Normalization converts raw input labels to `Cross` / `X` consistently.
- Epsilon comparison returns `UNDECIDED` for near-equal scores.
- Invalid shape cases are reported without program termination.

## 9. README Plan

The README will follow the style of prior branches while staying focused on this assignment.

### Planned sections
1. Project overview
2. Runtime environment
3. How to run
4. File structure
5. Implementation summary
6. Core feature details
7. `data.json` schema explanation
8. Result report
9. Performance analysis
10. Bonus implementation notes

### Required report content
- Why label normalization is necessary
- Why epsilon comparison is necessary for floating-point safety
- Why failures can occur from schema/data/policy differences, not only code bugs
- Why MAC complexity grows as `O(N^2)`
- How measured results relate to operation count
- Why zero failures, if achieved, are explained by the chosen normalization and comparison policy

## 10. Out of Scope

- External dependencies such as NumPy or pandas
- GUI or web interface
- Arbitrary-size non-square matrices
- Advanced hardware-level optimization beyond the simple 1D flattening bonus

## 11. Implementation Plan Handoff

After this design is approved in written form, the next step is to create an implementation plan covering:
- file updates
- data generation steps
- feature build order
- validation and runtime checks
- README/report completion
