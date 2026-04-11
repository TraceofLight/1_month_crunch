# Output Format Alignment Design

- Date: 2026-04-11
- Project: `1_month_crunch`
- Target files: `main.py`, `tests/test_main.py`, `README.md`

## Goal

Make the console output look closer to the assignment's sample layout while preserving the current dataset, scoring policy, summary counts, and bonus features.

## Scope

### In scope
- Add `[모드 선택]` and section separators similar to the sample output.
- Reformat manual-mode output into labeled sections.
- Reformat batch-mode output into filter-load / pattern-analysis / performance / summary sections.
- Keep the existing 2D/1D bonus timing output.
- Keep current PASS/FAIL data and case results unchanged.
- Keep pattern-generator mode available and present it in a compatible style.

### Out of scope
- Changing `data.json` contents.
- Changing the `UNDECIDED` rule or any PASS/FAIL outcomes.
- Rewriting README beyond later documentation sync if needed.

## Approach

Adjust only presentation strings and rendering helpers. Do not change scoring logic, dataset generation, or summary calculations.
