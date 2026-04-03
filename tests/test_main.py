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
