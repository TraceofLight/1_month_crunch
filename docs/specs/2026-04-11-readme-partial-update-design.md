# README Partial Update Design

- Date: 2026-04-11
- Project: `1_month_crunch`
- Target file: `README.md`

## Goal

Update only the README sections needed to expose the newly added pattern-generator menu, generated-pattern reuse in `data.json`, and graceful `Ctrl+C` / `Ctrl+D` exit handling.

## Scope

### In scope
- Add menu option 3 to the run instructions.
- Update the bonus-feature description so the pattern generator is visibly user-facing.
- Document that generated patterns can be appended to `data.json` using the existing `size_{N}_{idx}` key rule.
- Document that missing related filters cause a case-level FAIL because judgment is impossible.
- Add verification notes for the new generator mode and graceful exit behavior.
- Insert screenshot placeholders only for newly added functionality.

### Out of scope
- Rewriting unrelated existing README sections.
- Re-documenting manual-mode input validation details.
- Replacing existing screenshots.

## Editing approach

Keep the update minimal and local:
- `3. 실행 방법`
- `6. 핵심 기능 설명 > 보너스 기능`
- `7. data.json 구조 설명`
- `10. 테스트 및 검증`

Use placeholders in plain text form:
- `(패턴 생성기 실행 사진 필요)`
- `(종료 처리 사진 필요)`
