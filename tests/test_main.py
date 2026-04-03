import json

import main


DEFAULT_HINT = "힌트가 없습니다."


def test_load_state_uses_defaults_when_file_missing(tmp_path, monkeypatch):
    missing_state_path = tmp_path / "missing_state.json"
    monkeypatch.setattr(main, "STATE_PATH", missing_state_path)

    game = main.QuizGame()

    assert [quiz.to_dict() for quiz in game.quizzes] == [
        quiz.to_dict() for quiz in game.build_default_quizzes()
    ]
    assert game.best_score is None
    assert game.history == []



def test_update_best_score_accepts_higher_score(tmp_path, monkeypatch):
    state_path = tmp_path / "state.json"
    monkeypatch.setattr(main, "STATE_PATH", state_path)

    game = main.QuizGame()
    game.best_score = {"correct": 1, "total": 2, "score": 50}

    updated = game.update_best_score(2, 2, 100)

    assert updated is True
    assert game.best_score == {"correct": 2, "total": 2, "score": 100}



def test_load_state_accepts_old_format_without_hint_or_history(tmp_path, monkeypatch):
    state_path = tmp_path / "state.json"
    state_path.write_text(
        json.dumps(
            {
                "quizzes": [
                    {
                        "question": "문제",
                        "choices": ["하나", "둘", "셋", "넷"],
                        "answer": 2,
                    }
                ],
                "best_score": {"correct": 1, "total": 1, "score": 100},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(main, "STATE_PATH", state_path)

    game = main.QuizGame()

    assert len(game.quizzes) == 1
    assert game.quizzes[0].hint == DEFAULT_HINT
    assert game.best_score == {"correct": 1, "total": 1, "score": 100}
    assert game.history == []



def test_load_state_preserves_history_schema(tmp_path, monkeypatch):
    state_path = tmp_path / "state.json"
    history_entry = {
        "played_at": "2026-04-03T12:34:56",
        "total": 2,
        "correct": 1,
        "score": 50,
        "hint_used": 1,
    }
    state_path.write_text(
        json.dumps(
            {
                "quizzes": [
                    {
                        "question": "문제",
                        "choices": ["하나", "둘", "셋", "넷"],
                        "answer": 2,
                    }
                ],
                "best_score": {"correct": 1, "total": 2, "score": 50},
                "history": [history_entry],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(main, "STATE_PATH", state_path)

    game = main.QuizGame()

    assert game.history == [history_entry]



def test_load_state_preserves_quizzes_and_best_score_when_history_schema_is_invalid(
    tmp_path, monkeypatch
):
    state_path = tmp_path / "state.json"
    state_path.write_text(
        json.dumps(
            {
                "quizzes": [
                    {
                        "question": "문제",
                        "choices": ["하나", "둘", "셋", "넷"],
                        "answer": 2,
                    }
                ],
                "best_score": {"correct": 1, "total": 1, "score": 100},
                "history": [
                    {
                        "played_at": "2026-04-03T12:34:56",
                        "total": 1,
                        "correct": 1,
                        "score": 100,
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(main, "STATE_PATH", state_path)

    game = main.QuizGame()

    assert [quiz.to_dict() for quiz in game.quizzes] == [
        {
            "question": "문제",
            "choices": ["하나", "둘", "셋", "넷"],
            "answer": 2,
            "hint": DEFAULT_HINT,
        }
    ]
    assert game.best_score == {"correct": 1, "total": 1, "score": 100}
    assert game.history == []



def test_load_state_rejects_history_when_correct_exceeds_total(tmp_path, monkeypatch):
    state_path = tmp_path / "state.json"
    state_path.write_text(
        json.dumps(
            {
                "quizzes": [
                    {
                        "question": "문제",
                        "choices": ["하나", "둘", "셋", "넷"],
                        "answer": 2,
                    }
                ],
                "best_score": {"correct": 1, "total": 1, "score": 100},
                "history": [
                    {
                        "played_at": "2026-04-03T12:34:56",
                        "total": 1,
                        "correct": 2,
                        "score": 100,
                        "hint_used": 0,
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(main, "STATE_PATH", state_path)

    game = main.QuizGame()

    assert len(game.quizzes) == 1
    assert game.best_score == {"correct": 1, "total": 1, "score": 100}
    assert game.history == []



def test_load_state_rejects_history_when_hint_used_exceeds_total(tmp_path, monkeypatch):
    state_path = tmp_path / "state.json"
    state_path.write_text(
        json.dumps(
            {
                "quizzes": [
                    {
                        "question": "문제",
                        "choices": ["하나", "둘", "셋", "넷"],
                        "answer": 2,
                    }
                ],
                "best_score": {"correct": 1, "total": 1, "score": 100},
                "history": [
                    {
                        "played_at": "2026-04-03T12:34:56",
                        "total": 1,
                        "correct": 1,
                        "score": 100,
                        "hint_used": 2,
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(main, "STATE_PATH", state_path)

    game = main.QuizGame()

    assert len(game.quizzes) == 1
    assert game.best_score == {"correct": 1, "total": 1, "score": 100}
    assert game.history == []



def test_save_state_writes_hint_and_history(tmp_path, monkeypatch):
    state_path = tmp_path / "state.json"
    monkeypatch.setattr(main, "STATE_PATH", state_path)

    game = main.QuizGame()
    game.quizzes = [
        main.Quiz("문제", ["하나", "둘", "셋", "넷"], 2, "숫자를 떠올려 보세요.")
    ]
    game.best_score = {"correct": 1, "total": 1, "score": 100}
    game.history = [
        {
            "played_at": "2026-04-03T12:34:56",
            "total": 1,
            "correct": 1,
            "score": 100,
            "hint_used": 0,
        }
    ]

    game.save_state()

    data = json.loads(state_path.read_text(encoding="utf-8"))
    assert data["quizzes"][0]["hint"] == "숫자를 떠올려 보세요."
    assert data["history"] == [
        {
            "played_at": "2026-04-03T12:34:56",
            "total": 1,
            "correct": 1,
            "score": 100,
            "hint_used": 0,
        }
    ]



def test_prepare_quiz_round_returns_shuffled_subset_without_mutating_quizzes(tmp_path, monkeypatch):
    state_path = tmp_path / "state.json"
    monkeypatch.setattr(main, "STATE_PATH", state_path)

    game = main.QuizGame()
    original_quizzes = game.quizzes[:]
    selected_total = 3
    asked = {}

    def fake_ask_number(prompt, min_value, max_value):
        asked["prompt"] = prompt
        asked["min"] = min_value
        asked["max"] = max_value
        return selected_total

    monkeypatch.setattr(game, "ask_number", fake_ask_number)

    def reverse_quizzes(quizzes):
        quizzes.reverse()

    monkeypatch.setattr(main.random, "shuffle", reverse_quizzes)

    round_quizzes = game.prepare_quiz_round()

    assert asked == {
        "prompt": "몇 문제를 푸시겠습니까? ",
        "min": 1,
        "max": len(original_quizzes),
    }
    assert round_quizzes == list(reversed(original_quizzes))[:selected_total]
    assert game.quizzes == original_quizzes



def test_prepare_quiz_round_asks_for_single_question_when_only_one_quiz_exists(
    tmp_path, monkeypatch
):
    state_path = tmp_path / "state.json"
    monkeypatch.setattr(main, "STATE_PATH", state_path)

    game = main.QuizGame()
    game.quizzes = [main.Quiz("문제", ["1", "2", "3", "4"], 1)]
    asked = {}

    def fake_ask_number(prompt, min_value, max_value):
        asked["min"] = min_value
        asked["max"] = max_value
        return 1

    monkeypatch.setattr(game, "ask_number", fake_ask_number)
    monkeypatch.setattr(main.random, "shuffle", lambda quizzes: None)

    round_quizzes = game.prepare_quiz_round()

    assert asked == {"min": 1, "max": 1}
    assert round_quizzes == game.quizzes



def test_play_quiz_uses_prepared_round_count_for_score_and_best_score(tmp_path, monkeypatch, capsys):
    state_path = tmp_path / "state.json"
    monkeypatch.setattr(main, "STATE_PATH", state_path)

    game = main.QuizGame()
    round_quizzes = [
        main.Quiz("문제 1", ["1", "2", "3", "4"], 2),
        main.Quiz("문제 2", ["1", "2", "3", "4"], 4),
        main.Quiz("문제 3", ["1", "2", "3", "4"], 1),
    ]
    answers = iter([2, 1, 1])

    monkeypatch.setattr(game, "prepare_quiz_round", lambda: round_quizzes)
    monkeypatch.setattr(game, "ask_number", lambda prompt, min_value, max_value: next(answers))

    game.play_quiz()

    output = capsys.readouterr().out
    assert "퀴즈를 시작합니다! (총 3문제)" in output
    assert "결과: 3문제 중 2문제 정답! (66점)" in output
    assert game.best_score == {"correct": 2, "total": 3, "score": 66}



def test_play_quiz_keeps_stored_quiz_order_after_round(tmp_path, monkeypatch):
    state_path = tmp_path / "state.json"
    monkeypatch.setattr(main, "STATE_PATH", state_path)

    game = main.QuizGame()
    original_quizzes = game.quizzes[:]
    round_quizzes = list(reversed(game.quizzes[:2]))
    answers = iter([quiz.answer for quiz in round_quizzes])

    monkeypatch.setattr(game, "prepare_quiz_round", lambda: round_quizzes)
    monkeypatch.setattr(game, "ask_number", lambda prompt, min_value, max_value: next(answers))

    game.play_quiz()

    assert game.quizzes == original_quizzes
    assert [quiz.question for quiz in game.quizzes] != [quiz.question for quiz in round_quizzes]



def test_repository_state_sample_matches_default_quizzes():
    data = json.loads(main.STATE_PATH.read_text(encoding="utf-8"))
    default_quizzes = [
        quiz.to_dict()
        for quiz in main.QuizGame.build_default_quizzes(object.__new__(main.QuizGame))
    ]

    assert data["quizzes"] == default_quizzes
    assert data["best_score"] == {
        "correct": len(default_quizzes),
        "total": len(default_quizzes),
        "score": 100,
    }
    assert data["history"] == []
