# Quiz Bonus Features Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add all five bonus features to the `e1-2` quiz game: random question order, selectable question count, per-question hints with score penalty, quiz deletion, and persisted play history.

**Architecture:** Extend the existing single-file console app in `main.py` without introducing new runtime dependencies. Keep the current `Quiz` / `QuizGame` split, expand the JSON state model for `hint` and `history`, add focused tests in `tests/test_main.py`, and implement each user-visible feature on its own branch with small commits merged back into `e1-2`.

**Tech Stack:** Python 3.10+, standard library (`json`, `random`, `datetime`, `pathlib`), pytest, git branches/merges.

---

## File Structure

- Modify: `main.py` — extend quiz model, menu flow, state loading/saving, quiz play flow, deletion flow, score/history display.
- Modify: `README.md` — document the five bonus features, updated menu, hint/history state schema, and usage flow.
- Modify: `state.json` — refresh sample persisted data to match new schema with `hint` and `history`.
- Create: `tests/test_main.py` — add regression tests for state loading, play scoring, hint penalty, deletion, history persistence, and backward-compatible state parsing.
- Create: `docs/superpowers/plans/2026-04-03-quiz-bonus-features.md` — this plan document.

### Task 1: Add regression test harness for current game behavior

**Files:**
- Modify: `main.py:18-309`
- Create: `tests/test_main.py`
- Test: `tests/test_main.py`

- [ ] **Step 1: Write the failing tests**

```python
from pathlib import Path

import main


def build_game(tmp_path):
    game = main.QuizGame.__new__(main.QuizGame)
    game.state_path = tmp_path / "state.json"
    game.quizzes = []
    game.best_score = None
    game.history = []
    game.is_running = True
    return game


def test_load_state_uses_defaults_when_file_missing(tmp_path, capsys):
    game = build_game(tmp_path)

    main.QuizGame.load_state(game)

    assert len(game.quizzes) >= 5
    assert game.best_score is None
    assert game.history == []
    assert "기본 퀴즈로 시작합니다." in capsys.readouterr().out


def test_update_best_score_accepts_higher_score(tmp_path):
    game = build_game(tmp_path)

    updated = main.QuizGame.update_best_score(game, 4, 5, 80)

    assert updated is True
    assert game.best_score == {"correct": 4, "total": 5, "score": 80}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_main.py::test_load_state_uses_defaults_when_file_missing tests/test_main.py::test_update_best_score_accepts_higher_score -v`
Expected: FAIL because `QuizGame` currently does not initialize `history` in this test harness path.

- [ ] **Step 3: Write minimal implementation**

```python
class QuizGame:
    def __init__(self):
        self.state_path = STATE_PATH
        self.quizzes = []
        self.best_score = None
        self.history = []
        self.is_running = True
        self.load_state()
```

```python
    def load_state(self):
        if not self.state_path.exists():
            self.quizzes = self.build_default_quizzes()
            self.best_score = None
            self.history = []
            print(f"{self.state_path.name} 파일이 없어 기본 퀴즈로 시작합니다.")
            return
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_main.py::test_load_state_uses_defaults_when_file_missing tests/test_main.py::test_update_best_score_accepts_higher_score -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_main.py main.py
git commit -m "test: add baseline coverage for quiz state"
```

### Task 2: Add backward-compatible hint and history state parsing

**Files:**
- Modify: `main.py:18-309`
- Modify: `state.json`
- Test: `tests/test_main.py`

- [ ] **Step 1: Write the failing tests**

```python
import json


def test_load_state_accepts_missing_hint_and_history(tmp_path):
    state_path = tmp_path / "state.json"
    state_path.write_text(
        json.dumps(
            {
                "quizzes": [
                    {
                        "question": "question",
                        "choices": ["a", "b", "c", "d"],
                        "answer": 2,
                    }
                ],
                "best_score": {"correct": 1, "total": 1, "score": 100},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    game = build_game(tmp_path)

    main.QuizGame.load_state(game)

    assert game.quizzes[0].hint == "힌트가 없습니다."
    assert game.history == []


def test_save_state_writes_hint_and_history(tmp_path):
    game = build_game(tmp_path)
    game.quizzes = [main.Quiz("q", ["1", "2", "3", "4"], 1, "h")]
    game.best_score = {"correct": 1, "total": 1, "score": 100}
    game.history = [{"played_at": "2026-04-03T10:30:00", "total": 1, "correct": 1, "score": 100, "hint_used": 0}]

    main.QuizGame.save_state(game)

    saved = json.loads(game.state_path.read_text(encoding="utf-8"))
    assert saved["quizzes"][0]["hint"] == "h"
    assert saved["history"][0]["hint_used"] == 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_main.py::test_load_state_accepts_missing_hint_and_history tests/test_main.py::test_save_state_writes_hint_and_history -v`
Expected: FAIL because `Quiz` does not support `hint` yet and `save_state()` does not write `history`.

- [ ] **Step 3: Write minimal implementation**

```python
class Quiz:
    def __init__(self, question, choices, answer, hint="힌트가 없습니다."):
        self.question = question
        self.choices = choices
        self.answer = answer
        self.hint = hint

    def to_dict(self):
        return {
            "question": self.question,
            "choices": self.choices,
            "answer": self.answer,
            "hint": self.hint,
        }

    @classmethod
    def from_dict(cls, data):
        question = data["question"]
        choices = data["choices"]
        answer = data["answer"]
        hint = data.get("hint", "힌트가 없습니다.")
        if not isinstance(hint, str) or not hint.strip():
            raise ValueError("hint")
        return cls(question.strip(), [choice.strip() for choice in choices], answer, hint.strip())
```

```python
    def normalize_history(self, history):
        if history is None:
            return []
        if not isinstance(history, list):
            raise ValueError("history")

        normalized_history = []
        for item in history:
            if not isinstance(item, dict):
                raise ValueError("history")
            played_at = item["played_at"]
            total = item["total"]
            correct = item["correct"]
            score = item["score"]
            hint_used = item["hint_used"]
            if not isinstance(played_at, str) or not played_at.strip():
                raise ValueError("history")
            if not all(isinstance(value, int) for value in [total, correct, score, hint_used]):
                raise ValueError("history")
            normalized_history.append(
                {
                    "played_at": played_at,
                    "total": total,
                    "correct": correct,
                    "score": score,
                    "hint_used": hint_used,
                }
            )
        return normalized_history
```

```python
    def load_state(self):
        ...
            self.quizzes = [Quiz.from_dict(item) for item in data.get("quizzes", [])]
            self.best_score = self.normalize_best_score(data.get("best_score"))
            self.history = self.normalize_history(data.get("history"))
            print(self.build_load_message())
        except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError):
            ...
            self.history = []
            self.save_state()
```

```python
    def save_state(self):
        data = {
            "quizzes": [quiz.to_dict() for quiz in self.quizzes],
            "best_score": self.best_score,
            "history": self.history,
        }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_main.py::test_load_state_accepts_missing_hint_and_history tests/test_main.py::test_save_state_writes_hint_and_history -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_main.py main.py state.json
git commit -m "feat: add hint and history state schema"
```

### Task 3: Add random selection and selectable quiz count

**Files:**
- Modify: `main.py:1-309`
- Test: `tests/test_main.py`

- [ ] **Step 1: Write the failing tests**

```python
from unittest.mock import patch


def test_prepare_quiz_round_limits_question_count(tmp_path):
    game = build_game(tmp_path)
    game.quizzes = [
        main.Quiz("q1", ["1", "2", "3", "4"], 1, "h1"),
        main.Quiz("q2", ["1", "2", "3", "4"], 1, "h2"),
        main.Quiz("q3", ["1", "2", "3", "4"], 1, "h3"),
    ]

    with patch.object(main.QuizGame, "ask_number", return_value=2), patch("main.random.shuffle") as mock_shuffle:
        selected = main.QuizGame.prepare_quiz_round(game)

    assert len(selected) == 2
    mock_shuffle.assert_called_once()
    assert [quiz.question for quiz in game.quizzes] == ["q1", "q2", "q3"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_main.py::test_prepare_quiz_round_limits_question_count -v`
Expected: FAIL because `prepare_quiz_round()` does not exist.

- [ ] **Step 3: Write minimal implementation**

```python
import random
```

```python
    def prepare_quiz_round(self):
        quiz_count = self.ask_number("몇 문제를 풀까요? ", 1, len(self.quizzes))
        selected_quizzes = list(self.quizzes)
        random.shuffle(selected_quizzes)
        return selected_quizzes[:quiz_count]
```

```python
    def play_quiz(self):
        if not self.quizzes:
            print("\n등록된 퀴즈가 없습니다.")
            return

        round_quizzes = self.prepare_quiz_round()
        print(f"\n퀴즈를 시작합니다! (총 {len(round_quizzes)}문제)")
        correct_answers = 0

        for number, quiz in enumerate(round_quizzes, start=1):
            ...

        total_questions = len(round_quizzes)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_main.py::test_prepare_quiz_round_limits_question_count -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_main.py main.py
git commit -m "feat: randomize quiz order and question count"
```

### Task 4: Add hint flow with score penalty

**Files:**
- Modify: `main.py:18-309`
- Test: `tests/test_main.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_calculate_score_applies_hint_penalty(tmp_path):
    game = build_game(tmp_path)

    score = main.QuizGame.calculate_score(game, correct_answers=4, total_questions=5, hint_used=2)

    assert score == 60


def test_maybe_show_hint_returns_usage_count(tmp_path, capsys):
    game = build_game(tmp_path)
    quiz = main.Quiz("q", ["1", "2", "3", "4"], 1, "use list")

    answers = iter(["y"])
    game.ask_choice = lambda prompt, valid_choices: next(answers)

    used = main.QuizGame.maybe_show_hint(game, quiz)

    assert used == 1
    assert "힌트: use list" in capsys.readouterr().out
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_main.py::test_calculate_score_applies_hint_penalty tests/test_main.py::test_maybe_show_hint_returns_usage_count -v`
Expected: FAIL because score calculation and hint flow helpers do not exist.

- [ ] **Step 3: Write minimal implementation**

```python
    def ask_choice(self, prompt, valid_choices):
        while True:
            value = self.read_input(prompt).strip().lower()
            if value in valid_choices:
                return value
            print(f"잘못된 입력입니다. {', '.join(valid_choices)} 중 하나를 입력하세요.")
```

```python
    def maybe_show_hint(self, quiz):
        use_hint = self.ask_choice("힌트를 볼까요? (y/n): ", {"y", "n"})
        if use_hint == "y":
            print(f"힌트: {quiz.hint}")
            return 1
        return 0
```

```python
    def calculate_score(self, correct_answers, total_questions, hint_used):
        base_score = int(correct_answers / total_questions * 100)
        final_score = base_score - (hint_used * 10)
        return max(final_score, 0)
```

```python
    def play_quiz(self):
        ...
        hint_used = 0
        for number, quiz in enumerate(round_quizzes, start=1):
            quiz.display(number)
            hint_used += self.maybe_show_hint(quiz)
            selected_answer = self.ask_number("정답 입력 (1-4): ", 1, 4)
            ...
        score = self.calculate_score(correct_answers, total_questions, hint_used)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_main.py::test_calculate_score_applies_hint_penalty tests/test_main.py::test_maybe_show_hint_returns_usage_count -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_main.py main.py
git commit -m "feat: add quiz hints with score penalty"
```

### Task 5: Persist play history and show it in score view

**Files:**
- Modify: `main.py:18-309`
- Modify: `state.json`
- Test: `tests/test_main.py`

- [ ] **Step 1: Write the failing tests**

```python
from datetime import datetime


def test_record_history_appends_latest_play(tmp_path):
    game = build_game(tmp_path)
    with patch("main.datetime") as mock_datetime:
        mock_datetime.now.return_value = datetime(2026, 4, 3, 10, 30, 0)
        mock_datetime.now.return_value.isoformat.return_value = "2026-04-03T10:30:00"

        main.QuizGame.record_history(game, total_questions=5, correct_answers=4, score=60, hint_used=2)

    assert game.history == [
        {
            "played_at": "2026-04-03T10:30:00",
            "total": 5,
            "correct": 4,
            "score": 60,
            "hint_used": 2,
        }
    ]


def test_show_best_score_prints_history(tmp_path, capsys):
    game = build_game(tmp_path)
    game.best_score = {"correct": 4, "total": 5, "score": 60}
    game.history = [
        {"played_at": "2026-04-03T10:30:00", "total": 5, "correct": 4, "score": 60, "hint_used": 2}
    ]

    main.QuizGame.show_best_score(game)

    output = capsys.readouterr().out
    assert "최고 점수: 60점" in output
    assert "2026-04-03T10:30:00" in output
    assert "힌트 사용 2회" in output
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_main.py::test_record_history_appends_latest_play tests/test_main.py::test_show_best_score_prints_history -v`
Expected: FAIL because play history support does not exist.

- [ ] **Step 3: Write minimal implementation**

```python
from datetime import datetime
```

```python
    def record_history(self, total_questions, correct_answers, score, hint_used):
        self.history.append(
            {
                "played_at": datetime.now().isoformat(timespec="seconds"),
                "total": total_questions,
                "correct": correct_answers,
                "score": score,
                "hint_used": hint_used,
            }
        )
```

```python
    def show_best_score(self):
        if self.best_score is None:
            print("\n아직 퀴즈를 풀지 않아 최고 점수가 없습니다.")
            return

        print(
            f"\n최고 점수: {self.best_score['score']}점 "
            f"({self.best_score['total']}문제 중 {self.best_score['correct']}문제 정답)"
        )
        if not self.history:
            print("기록이 없습니다.")
            return

        print("최근 플레이 기록")
        for item in self.history[-5:]:
            print(
                f"- {item['played_at']}: {item['correct']}/{item['total']} 정답, "
                f"{item['score']}점, 힌트 사용 {item['hint_used']}회"
            )
```

```python
    def play_quiz(self):
        ...
        score = self.calculate_score(correct_answers, total_questions, hint_used)
        self.record_history(total_questions, correct_answers, score, hint_used)
        if self.update_best_score(correct_answers, total_questions, score):
            ...
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_main.py::test_record_history_appends_latest_play tests/test_main.py::test_show_best_score_prints_history -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_main.py main.py state.json
git commit -m "feat: track quiz play history"
```

### Task 6: Add quiz deletion flow and expanded menu

**Files:**
- Modify: `main.py:18-309`
- Test: `tests/test_main.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_delete_quiz_removes_selected_item(tmp_path):
    game = build_game(tmp_path)
    game.quizzes = [
        main.Quiz("keep", ["1", "2", "3", "4"], 1, "h1"),
        main.Quiz("remove", ["1", "2", "3", "4"], 2, "h2"),
    ]
    game.ask_number = lambda prompt, min_value, max_value: 2
    game.ask_choice = lambda prompt, valid_choices: "y"
    saved = []
    game.save_state = lambda: saved.append("saved")

    main.QuizGame.delete_quiz(game)

    assert [quiz.question for quiz in game.quizzes] == ["keep"]
    assert saved == ["saved"]


def test_handle_menu_routes_to_delete_and_exit(tmp_path):
    game = build_game(tmp_path)
    called = []
    game.play_quiz = lambda: called.append("play")
    game.add_quiz = lambda: called.append("add")
    game.show_quiz_list = lambda: called.append("list")
    game.delete_quiz = lambda: called.append("delete")
    game.show_best_score = lambda: called.append("score")
    game.exit_game = lambda: called.append("exit")

    for menu in range(1, 7):
        main.QuizGame.handle_menu(game, menu)

    assert called == ["play", "add", "list", "delete", "score", "exit"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_main.py::test_delete_quiz_removes_selected_item tests/test_main.py::test_handle_menu_routes_to_delete_and_exit -v`
Expected: FAIL because delete flow and six-item menu do not exist.

- [ ] **Step 3: Write minimal implementation**

```python
    def show_menu(self):
        print("\n========================================")
        print("        나만의 퀴즈 게임")
        print("========================================")
        print("1. 퀴즈 풀기")
        print("2. 퀴즈 추가")
        print("3. 퀴즈 목록")
        print("4. 퀴즈 삭제")
        print("5. 점수 확인")
        print("6. 종료")
        print("========================================")
```

```python
    def run(self):
        while self.is_running:
            try:
                self.show_menu()
                selected_menu = self.ask_number("선택: ", 1, 6)
                self.handle_menu(selected_menu)
            except SafeExit:
                self.handle_safe_exit()
```

```python
    def handle_menu(self, selected_menu):
        if selected_menu == 1:
            self.play_quiz()
        elif selected_menu == 2:
            self.add_quiz()
        elif selected_menu == 3:
            self.show_quiz_list()
        elif selected_menu == 4:
            self.delete_quiz()
        elif selected_menu == 5:
            self.show_best_score()
        else:
            self.exit_game()
```

```python
    def delete_quiz(self):
        if not self.quizzes:
            print("\n등록된 퀴즈가 없습니다.")
            return

        self.show_quiz_list()
        selected_index = self.ask_number("삭제할 퀴즈 번호를 선택하세요: ", 1, len(self.quizzes))
        confirm = self.ask_choice("정말 삭제할까요? (y/n): ", {"y", "n"})
        if confirm == "n":
            print("삭제를 취소했습니다.")
            return

        deleted_quiz = self.quizzes.pop(selected_index - 1)
        self.save_state()
        print(f"'{deleted_quiz.question}' 퀴즈를 삭제했습니다.")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_main.py::test_delete_quiz_removes_selected_item tests/test_main.py::test_handle_menu_routes_to_delete_and_exit -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_main.py main.py
git commit -m "feat: add quiz deletion menu flow"
```

### Task 7: Update quiz creation, defaults, and persisted sample data

**Files:**
- Modify: `main.py:69-101,163-171,295-305`
- Modify: `state.json`
- Test: `tests/test_main.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_add_quiz_collects_hint_and_saves(tmp_path):
    game = build_game(tmp_path)
    answers = iter(["question", "a", "b", "c", "d", "extra help"])
    game.ask_text = lambda prompt: next(answers)
    game.ask_number = lambda prompt, min_value, max_value: 3
    saved = []
    game.save_state = lambda: saved.append("saved")

    main.QuizGame.add_quiz(game)

    assert game.quizzes[0].hint == "extra help"
    assert saved == ["saved"]


def test_build_default_quizzes_include_hints(tmp_path):
    game = build_game(tmp_path)

    quizzes = main.QuizGame.build_default_quizzes(game)

    assert all(quiz.hint for quiz in quizzes)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_main.py::test_add_quiz_collects_hint_and_saves tests/test_main.py::test_build_default_quizzes_include_hints -v`
Expected: FAIL because default quizzes and quiz creation do not include hints.

- [ ] **Step 3: Write minimal implementation**

```python
    def build_default_quizzes(self):
        return [
            Quiz(
                "Python의 창시자는 누구인가요?",
                ["Guido van Rossum", "Linus Torvalds", "James Gosling", "Bjarne Stroustrup"],
                1,
                "파이썬 이름과 자주 함께 언급되는 인물입니다.",
            ),
            Quiz(
                "키와 값을 함께 저장하는 Python 자료형은 무엇인가요?",
                ["list", "tuple", "set", "dict"],
                4,
                "중괄호와 key-value 구조를 떠올려 보세요.",
            ),
            Quiz(
                "함수를 정의할 때 사용하는 키워드는 무엇인가요?",
                ["func", "def", "lambda", "return"],
                2,
                "function definition의 앞 세 글자입니다.",
            ),
            Quiz(
                "len([1, 2, 3, 4])의 결과는 무엇인가요?",
                ["2", "3", "4", "5"],
                3,
                "리스트 안 원소 개수를 세면 됩니다.",
            ),
            Quiz(
                "예외 처리를 시작할 때 가장 먼저 쓰는 키워드는 무엇인가요?",
                ["catch", "except", "try", "finally"],
                3,
                "except보다 먼저 나오는 블록입니다.",
            ),
            Quiz(
                "조건이 거짓일 때 다른 분기를 실행하는 키워드는 무엇인가요?",
                ["elif", "else", "for", "while"],
                2,
                "if와 짝을 이루는 기본 분기 키워드입니다.",
            ),
        ]
```

```python
    def add_quiz(self):
        print("\n새로운 퀴즈를 추가합니다.")
        question = self.ask_text("문제를 입력하세요: ")
        choices = [self.ask_text(f"선택지 {number}: ") for number in range(1, 5)]
        answer = self.ask_number("정답 번호 (1-4): ", 1, 4)
        hint = self.ask_text("힌트를 입력하세요: ")

        self.quizzes.append(Quiz(question, choices, answer, hint))
        self.save_state()
        print("퀴즈가 추가되었습니다!")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_main.py::test_add_quiz_collects_hint_and_saves tests/test_main.py::test_build_default_quizzes_include_hints -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_main.py main.py state.json
git commit -m "feat: save quiz hints in create flow"
```

### Task 8: Refresh README and run full verification

**Files:**
- Modify: `README.md`
- Modify: `state.json`
- Test: `tests/test_main.py`

- [ ] **Step 1: Write the failing documentation/status checks**

```text
README.md must mention:
- random quiz order
- question count selection
- hint feature and 10-point penalty
- quiz deletion menu
- history persisted in state.json
```

```python
def test_state_sample_contains_history_key():
    import json
    from pathlib import Path

    saved = json.loads(Path("state.json").read_text(encoding="utf-8"))
    assert "history" in saved
```

- [ ] **Step 2: Run checks to verify they fail**

Run: `pytest tests/test_main.py::test_state_sample_contains_history_key -v`
Expected: FAIL until `state.json` sample is updated.

- [ ] **Step 3: Write minimal implementation**

```json
{
  "quizzes": [
    {
      "question": "Python의 창시자는 누구인가요?",
      "choices": [
        "Guido van Rossum",
        "Linus Torvalds",
        "James Gosling",
        "Bjarne Stroustrup"
      ],
      "answer": 1,
      "hint": "파이썬 이름과 자주 함께 언급되는 인물입니다."
    }
  ],
  "best_score": {
    "correct": 1,
    "total": 1,
    "score": 90
  },
  "history": [
    {
      "played_at": "2026-04-03T10:30:00",
      "total": 1,
      "correct": 1,
      "score": 90,
      "hint_used": 1
    }
  ]
}
```

```markdown
## 5. 기능 목록

### 퀴즈 풀기
- 문제 수를 선택한 뒤 랜덤 순서로 퀴즈를 풉니다.
- 각 문제에서 힌트 사용 여부를 고를 수 있습니다.
- 힌트 1회당 10점이 감점됩니다.

### 퀴즈 삭제
- 등록된 퀴즈 번호를 선택해 삭제할 수 있습니다.

### 점수 확인
- 최고 점수와 최근 플레이 기록을 함께 확인할 수 있습니다.
```

- [ ] **Step 4: Run full verification**

Run: `pytest -v`
Expected: PASS with all tests green

Run: `python main.py`
Expected: menu shows 1-6 options, quiz play asks for question count and hint usage, score screen shows history after a round

- [ ] **Step 5: Commit**

```bash
git add README.md state.json tests/test_main.py main.py
git commit -m "docs: document quiz bonus features"
```

## Self-Review

- Spec coverage check:
  - 랜덤 출제 → Task 3
  - 문제 수 선택 → Task 3
  - 힌트 기능 + 감점 → Task 4 and Task 7
  - 퀴즈 삭제 → Task 6
  - 점수 기록 히스토리 → Task 2 and Task 5
  - 상태 저장/재실행 유지 → Task 2, Task 5, Task 8
  - README 반영 → Task 8
  - 기능별 커밋 → each task Step 5
- Placeholder scan: no `TODO`, `TBD`, or undefined “write tests later” steps remain.
- Type consistency check:
  - `Quiz(..., hint)` is introduced in Task 2 and used consistently in Tasks 3-8.
  - `history` item keys remain `played_at`, `total`, `correct`, `score`, `hint_used` across all tasks.
  - `prepare_quiz_round`, `ask_choice`, `maybe_show_hint`, `calculate_score`, `record_history`, and `delete_quiz` names are used consistently.
