# README Evaluation Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rewrite `README.md` so it still reads cleanly but also directly answers the assignment rubric items that AI Codyssey and other evaluators are flagging as missing.

**Architecture:** Keep the current README as the base and strengthen it section-by-section rather than replacing it wholesale. The work stays documentation-only: enrich the current structure with explicit design explanations, Git/process rationale, interview-style Q&A, and screenshot placeholders while preserving the current implemented feature set and repository state.

**Tech Stack:** Markdown (`README.md`), git history already in the repository, current Python quiz game implementation as the factual source of truth.

---

## File Structure

- Modify: `README.md` — strengthen assignment-facing explanations, add Git/process/interview sections, and insert explicit screenshot placeholders.
- Read-only reference: `main.py` — source of truth for menu flow, class responsibilities, save/load behavior, and exception handling.
- Read-only reference: `state.json` — source of truth for current persisted schema.
- Read-only reference: `C:/Users/heejun_kim/Desktop/q2.txt` — assignment rubric and explanation targets.
- Read-only reference: `docs/superpowers/specs/2026-04-03-readme-evaluation-hardening-design.md` — approved README hardening design.

### Task 1: Add assignment-facing overview sections

**Files:**
- Modify: `README.md:3-40`

- [ ] **Step 1: Write the failing documentation checklist**

```text
README.md must explicitly contain:
- a "퀴즈 주제" statement
- a "선정 이유" explanation
- a sentence tying the chosen topic to the assignment goals
- the current six-item menu
```

- [ ] **Step 2: Verify the current README is missing pieces**

Run: `python - <<'PY'
from pathlib import Path
text = Path('README.md').read_text(encoding='utf-8')
checks = ['퀴즈 주제', '선정 이유', '기본 Python 문법', '6. 종료']
for item in checks:
    print(item, 'OK' if item in text else 'MISSING')
PY`
Expected: at least `퀴즈 주제` and `선정 이유` print `MISSING`

- [ ] **Step 3: Write the minimal implementation**

```markdown
## 2. 퀴즈 주제와 선정 이유

### 퀴즈 주제
- Python 기초 문법

### 선정 이유
- 이번 과제의 핵심이 변수, 자료형, 조건문, 함수, 클래스, 파일 저장 흐름을 직접 구현하는 것이어서, 문제를 푸는 과정 자체가 복습이 되도록 Python 기초 문법을 주제로 선택했습니다.
- 사용자가 퀴즈를 풀고 추가하는 동안 `if/elif`, 반복문, 메서드 호출, JSON 저장이 실제 프로그램 동작과 연결되도록 구성할 수 있어 과제 목표와 가장 자연스럽게 맞닿아 있습니다.
```

```markdown
## 4. 실행 방법

```bash
python main.py
```

실행 시 아래 메뉴가 출력됩니다.

1. 퀴즈 풀기
2. 퀴즈 추가
3. 퀴즈 목록
4. 퀴즈 삭제
5. 점수 확인
6. 종료
```
```

- [ ] **Step 4: Verify the checklist passes**

Run: `python - <<'PY'
from pathlib import Path
text = Path('README.md').read_text(encoding='utf-8')
checks = ['퀴즈 주제', '선정 이유', '기본 Python 문법', '6. 종료']
for item in checks:
    assert item in text, item
print('overview checks passed')
PY`
Expected: prints `overview checks passed`

- [ ] **Step 5: Commit**

```bash
git add README.md
git commit -m "docs: add quiz topic and overview context"
```

### Task 2: Add design explanation sections for evaluation questions

**Files:**
- Modify: `README.md:84-150`

- [ ] **Step 1: Write the failing documentation checklist**

```text
README.md must explicitly explain:
- why Quiz and QuizGame are separated
- how input validation, game flow, and save/load are divided
- where load_state and save_state happen in the program lifecycle
- why JSON is used
- why file I/O uses try/except
- why the current state.json field structure was chosen
```

- [ ] **Step 2: Verify the current README is missing direct evaluation answers**

Run: `python - <<'PY'
from pathlib import Path
text = Path('README.md').read_text(encoding='utf-8')
checks = [
    '입력 처리 / 게임 진행 / 저장-불러오기 흐름',
    '클래스를 분리한 이유',
    'JSON을 사용한 이유',
    'try/except',
    '현재 구조를 이렇게 설계한 이유',
]
for item in checks:
    print(item, 'OK' if item in text else 'MISSING')
PY`
Expected: most or all print `MISSING`

- [ ] **Step 3: Write the minimal implementation**

```markdown
## 8. 클래스 구조와 책임 분리 설명

### `Quiz` 클래스
- 개별 퀴즈 1개를 표현하는 데이터 단위입니다.
- 문제(`question`), 선택지(`choices`), 정답(`answer`), 힌트(`hint`)를 속성으로 가집니다.
- 퀴즈 출력(`display`), 정답 판정(`is_correct`), JSON 저장용 변환(`to_dict`, `from_dict`)을 담당합니다.

### `QuizGame` 클래스
- 게임 전체 흐름을 관리하는 상위 클래스입니다.
- 퀴즈 목록, 최고 점수, 플레이 히스토리, 실행 상태, 파일 경로를 관리합니다.
- 메뉴 표시, 입력 처리, 퀴즈 진행, 퀴즈 추가/삭제, 점수 확인, 파일 저장/불러오기, 안전 종료를 담당합니다.

### 클래스를 분리한 이유
- 퀴즈 1개 자체의 책임과 게임 전체 흐름의 책임을 분리하기 위해서입니다.
- 함수만으로 모두 구현하면 퀴즈 데이터와 게임 상태가 섞여 수정 범위가 커지기 쉽습니다.
- 클래스로 나누면 `Quiz`는 “문제 한 개”, `QuizGame`은 “게임 진행 전체”라는 역할이 분명해집니다.
```

```markdown
## 9. 입력 처리 / 게임 진행 / 저장-불러오기 흐름 설명

### 입력 처리 기준
- `ask_text()`는 빈 문자열을 허용하지 않고 재입력을 요구합니다.
- `ask_number()`는 공백 제거 후 정수 변환을 시도하고, 실패하거나 허용 범위를 벗어나면 안내 메시지를 출력한 뒤 재입력을 요구합니다.
- `read_input()`는 `KeyboardInterrupt`, `EOFError`를 받아 `SafeExit` 예외로 변환합니다.

### 게임 진행 흐름
1. `QuizGame().run()`으로 시작합니다.
2. `show_menu()`로 메뉴를 출력합니다.
3. `ask_number()`로 메뉴 번호를 입력받습니다.
4. `handle_menu()`가 선택한 기능에 따라 퀴즈 풀기/추가/목록/삭제/점수 확인/종료를 분기합니다.
5. 퀴즈 풀기에서는 `prepare_quiz_round()`로 문제 수 선택과 랜덤 출제를 준비하고, 각 문제에서 힌트 사용 여부와 정답 입력을 처리합니다.
6. 점수 계산 후 최고 점수와 히스토리를 갱신하고 저장합니다.

### 저장/불러오기 흐름
- 프로그램 시작 시 `__init__()`에서 `load_state()`를 호출합니다.
- `state.json`이 있으면 퀴즈 목록, 최고 점수, 히스토리를 복원합니다.
- 파일이 없으면 기본 퀴즈 데이터로 시작합니다.
- 퀴즈 추가/삭제, 퀴즈 플레이 후 점수 갱신, 정상 종료, 안전 종료 시 `save_state()`를 호출합니다.
```

```markdown
## 10. 예외 처리 설명

### `Ctrl+C` / `EOFError` 안전 종료
- 사용자가 실행 중 `Ctrl+C`를 누르거나 입력 스트림이 종료되면 `read_input()`에서 `SafeExit` 예외를 발생시킵니다.
- `run()` 메서드는 이 예외를 받아 `handle_safe_exit()`를 호출합니다.
- `handle_safe_exit()`는 안내 메시지를 출력하고 `save_state()`를 호출한 뒤 종료합니다.

### 파일 입출력에서 `try/except`가 필요한 이유
- `state.json`은 파일이 없을 수도 있고, JSON 형식이 깨졌을 수도 있으며, 읽기/쓰기 중 OS 오류가 날 수도 있습니다.
- 예외 처리가 없으면 프로그램이 바로 중단되어 사용자가 데이터를 다루기 어려워집니다.
- 따라서 `load_state()`와 `save_state()`에 `try/except`를 두어, 오류 시 기본 데이터 복구 또는 안내 메시지 출력이 가능하도록 했습니다.
```

```markdown
## 14. JSON 사용 이유와 한계

### JSON을 사용한 이유
- Python 표준 라이브러리만으로 쉽게 읽고 쓸 수 있습니다.
- 사람이 파일 내용을 직접 확인하기 쉽습니다.
- 퀴즈 목록, 최고 점수, 플레이 기록처럼 구조화된 데이터를 저장하기 적합합니다.

### JSON 형식의 특징
- 키-값 기반 구조라서 객체와 배열 표현이 쉽습니다.
- 문자열, 숫자, 배열, 객체 등 기본 데이터 구조를 그대로 담기 좋습니다.
- 텍스트 기반이라 디버깅과 확인이 편합니다.

### 현재 구조를 이렇게 설계한 이유
- `quizzes`는 문제 목록 전체를 한 번에 저장하기 위해 배열 구조로 두었습니다.
- 각 퀴즈는 `question`, `choices`, `answer`, `hint` 필드만 가지도록 최소 구조로 설계했습니다.
- `best_score`는 최고 기록만 빠르게 보여주기 위해 단일 객체로 유지했습니다.
- `history`는 여러 번의 플레이 결과를 남기기 위해 배열 구조로 두었습니다.
```
```

- [ ] **Step 4: Verify the checklist passes**

Run: `python - <<'PY'
from pathlib import Path
text = Path('README.md').read_text(encoding='utf-8')
checks = [
    '입력 처리 / 게임 진행 / 저장-불러오기 흐름 설명',
    '클래스를 분리한 이유',
    'JSON을 사용한 이유',
    'try/except',
    '현재 구조를 이렇게 설계한 이유',
]
for item in checks:
    assert item in text, item
print('design explanation checks passed')
PY`
Expected: prints `design explanation checks passed`

- [ ] **Step 5: Commit**

```bash
git add README.md
git commit -m "docs: explain design and persistence flow"
```

### Task 3: Add Git workflow and evidence placeholder sections

**Files:**
- Modify: `README.md:150-220`

- [ ] **Step 1: Write the failing documentation checklist**

```text
README.md must explicitly cover:
- commit unit strategy
- commit message rule
- why branches were separated
- what merge means
- clone/pull practice explanation
- placeholders for git log, branch/merge, clone, pull, and screenshots
```

- [ ] **Step 2: Verify the current README is missing Git/process coverage**

Run: `python - <<'PY'
from pathlib import Path
text = Path('README.md').read_text(encoding='utf-8')
checks = [
    '커밋 단위 기준',
    '커밋 메시지 규칙',
    '브랜치 분리와 병합의 의미',
    'clone / pull 실습',
    '스크린샷 필요',
]
for item in checks:
    print(item, 'OK' if item in text else 'MISSING')
PY`
Expected: most or all print `MISSING`

- [ ] **Step 3: Write the minimal implementation**

```markdown
## 11. Git 작업 전략 설명

### 커밋 단위 기준
이번 작업은 기능 단위로 커밋을 나누는 것을 목표로 했습니다.

예시 기준:
- 문서 초안 추가
- 퀴즈 모델과 기본 데이터 추가
- 메뉴 흐름 및 입력 처리 추가
- 목록/점수 표시 추가
- 저장/불러오기 기능 추가
- 퀴즈 플레이/추가/안전 종료 기능 추가
- 보너스 기능(랜덤, 힌트, 삭제, 히스토리) 추가

### 커밋 메시지 규칙
- `feat:` 기능 추가
- `docs:` 문서 보강
- `test:` 테스트 추가/보강
- `merge:` 브랜치 병합
- 메시지만 보아도 어떤 변경이 있었는지 알 수 있도록 작성했습니다.

### 브랜치 분리와 병합의 의미
- 브랜치를 분리하면 메인 흐름을 건드리지 않고 특정 기능을 독립적으로 개발할 수 있습니다.
- 병합은 분리된 기능 작업을 다시 메인 흐름에 반영하는 과정입니다.
- 이번 프로젝트에서는 기능별로 브랜치를 나누고, 완료 후 `e1-2`에 병합하는 방식으로 기록을 남겼습니다.

### Git 증빙 자료
- `(여기 git log --oneline --graph 스크린샷 필요)`
- `(여기 브랜치 생성 및 병합 확인 스크린샷 필요)`
```

```markdown
## 12. clone / pull 실습 증빙

### 수행 목적
- 원격 저장소를 복제(clone)하고, 다른 로컬 복제본의 변경을 기존 작업 디렉터리에서 pull로 가져오는 흐름을 직접 경험하기 위함입니다.

### 정리 방식
1. 저장소를 별도 위치에 `clone`합니다.
2. 복제본에서 README 같은 파일에 간단한 변경을 합니다.
3. 변경 내용을 `commit`하고 `push`합니다.
4. 원래 작업 디렉터리에서 `pull`해 변경이 반영되는지 확인합니다.

### 증빙 자리
- `(여기 clone 실습 화면 스크린샷 필요)`
- `(여기 복제본에서 변경 후 commit/push 화면 스크린샷 필요)`
- `(여기 원래 디렉터리에서 pull 반영 확인 스크린샷 필요)`
```

```markdown
## 13. 실행 결과 및 검증 체크리스트

### 실행 화면 증빙 자리
- `(여기 메뉴 화면 스크린샷 필요)`
- `(여기 퀴즈 플레이 화면 스크린샷 필요)`
- `(여기 퀴즈 추가 화면 스크린샷 필요)`
- `(여기 점수 확인 화면 스크린샷 필요)`
- `(여기 잘못된 입력 처리 화면 스크린샷 필요)`
- `(여기 데이터 유지 확인 화면 스크린샷 필요)`

### 직접 확인한 검증 포인트
- `state.json`이 있으면 저장된 퀴즈/점수를 불러옵니다.
- `state.json`이 없으면 기본 퀴즈 데이터로 시작합니다.
- `state.json`이 손상되면 안내 메시지를 출력하고 기본 데이터로 복구합니다.
- 퀴즈를 풀고 종료한 뒤 재실행하면 최고 점수와 퀴즈 데이터가 유지됩니다.
```

- [ ] **Step 4: Verify the checklist passes**

Run: `python - <<'PY'
from pathlib import Path
text = Path('README.md').read_text(encoding='utf-8')
checks = [
    '커밋 단위 기준',
    '커밋 메시지 규칙',
    '브랜치 분리와 병합의 의미',
    'clone / pull 실습 증빙',
    '스크린샷 필요',
]
for item in checks:
    assert item in text, item
print('git evidence checks passed')
PY`
Expected: prints `git evidence checks passed`

- [ ] **Step 5: Commit**

```bash
git add README.md
git commit -m "docs: add git workflow evidence guide"
```

### Task 4: Add interview-style Q&A and final consistency pass

**Files:**
- Modify: `README.md:220-320`

- [ ] **Step 1: Write the failing documentation checklist**

```text
README.md must explicitly answer:
- JSON storage limits at 1000+ quizzes
- how to respond if state.json is corrupted
- what to edit first if scoring rules or quiz structure changes
```

- [ ] **Step 2: Verify the current README is missing interview answers**

Run: `python - <<'PY'
from pathlib import Path
text = Path('README.md').read_text(encoding='utf-8')
checks = [
    '1000개 이상',
    '손상되어 JSON 파싱에 실패',
    '요구사항이 바뀐다면',
]
for item in checks:
    print(item, 'OK' if item in text else 'MISSING')
PY`
Expected: one or more print `MISSING`

- [ ] **Step 3: Write the minimal implementation**

```markdown
## 15. 심층 인터뷰 대비 설명

### 퀴즈 데이터가 1000개 이상으로 늘어난다면 현재 JSON 저장 방식에 어떤 한계가 생기는가?
- JSON 파일은 전체를 한 번에 읽고 다시 쓰는 구조라 데이터가 커질수록 로딩과 저장 비용이 함께 커집니다.
- 특정 문제만 빠르게 검색하거나 일부만 수정하기가 비효율적입니다.
- 동시 수정 충돌 관리도 어렵기 때문에 규모가 커지면 데이터베이스 같은 방식이 더 적합할 수 있습니다.

### `state.json`이 손상되어 JSON 파싱에 실패한다면 어떤 대응이 가능한가?
- 현재 구현은 안내 메시지를 출력하고 기본 데이터로 복구한 뒤 다시 저장합니다.
- 데이터를 최대한 잃지 않으려면 손상된 파일을 `.bak`처럼 별도로 백업한 뒤 새 파일을 만드는 대응도 가능합니다.
- 즉, 기본 복구는 “프로그램 실행 가능 상태 회복”, 백업은 “사용자 데이터 보존 가능성 확보”라는 목적이 다릅니다.

### 정답 채점 방식이나 퀴즈 구조 요구사항이 바뀐다면 어디를 먼저 수정해야 하는가?
- 점수 계산 규칙이 바뀌면 `QuizGame.calculate_score()`와 그 결과를 사용하는 `play_quiz()`를 먼저 수정해야 합니다.
- 선택지 개수 같은 퀴즈 구조가 바뀌면 `Quiz.from_dict()` 검증, `build_default_quizzes()`, `add_quiz()`, `display()`를 함께 수정해야 합니다.
- 저장 필드가 바뀌면 `to_dict()`, `from_dict()`, `state.json` 스키마 설명, 관련 README 설명도 같이 수정해야 합니다.
```

```markdown
## 16. 제출 전 체크 포인트

- 프로젝트 개요 / 퀴즈 주제 선정 이유 / 실행 방법 / 기능 목록 / 파일 구조 / `state.json` 설명이 README에 포함되어 있는지 확인
- `(여기 개발 환경 설정 스크린샷 필요)`
- `(여기 git log --oneline --graph 스크린샷 필요)`
- `(여기 clone / pull 실습 스크린샷 필요)`
- `(여기 프로그램 실행 결과 스크린샷 필요)`
```

- [ ] **Step 4: Run a final consistency verification**

Run: `python - <<'PY'
from pathlib import Path
text = Path('README.md').read_text(encoding='utf-8')
checks = [
    '퀴즈 주제',
    '선정 이유',
    '입력 처리 / 게임 진행 / 저장-불러오기 흐름 설명',
    '파일 입출력에서 `try/except`가 필요한 이유',
    '브랜치 분리와 병합의 의미',
    'clone / pull 실습 증빙',
    '1000개 이상',
    '손상되어 JSON 파싱에 실패',
    '요구사항이 바뀐다면',
    '스크린샷 필요',
]
for item in checks:
    assert item in text, item
print('final README rubric checks passed')
PY`
Expected: prints `final README rubric checks passed`

- [ ] **Step 5: Commit**

```bash
git add README.md
git commit -m "docs: harden readme for assignment review"
```

## Self-Review

- Spec coverage check:
  - 퀴즈 주제 선정 이유 → Task 1
  - 클래스 분리 이유 / 함수와의 차이 → Task 2
  - 입력 처리 / 게임 진행 / 저장-불러오기 흐름 → Task 2
  - `state.json` 읽기/쓰기 순서 → Task 2
  - `try/except` 필요성 / 안전 종료 → Task 2
  - Git 커밋/브랜치/merge 설명 → Task 3
  - clone/pull 및 스크린샷 자리표시자 → Task 3
  - JSON 사용 이유와 구조 설계 이유 → Task 2
  - 1000개 이상 한계 / 손상 대응 / 요구사항 변경 시 수정 지점 → Task 4
- Placeholder scan: no `TODO`, `TBD`, or vague “write docs later” steps remain.
- Type consistency check:
  - All referenced methods match the current quiz game code: `run`, `ask_text`, `ask_number`, `read_input`, `load_state`, `save_state`, `calculate_score`, `play_quiz`, `build_default_quizzes`, `Quiz.from_dict`, `display`, `to_dict`, `from_dict`.
  - README-only work remains scoped to `README.md` and does not require code edits.
