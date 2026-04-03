import json

import main


DEFAULT_HINT = "힌트가 없습니다."


def test_default_quizzes_include_meaningful_hints(tmp_path, monkeypatch):
    state_path = tmp_path / "state.json"
    monkeypatch.setattr(main, "STATE_PATH", state_path)

    game = main.QuizGame()

    assert all(quiz.hint != DEFAULT_HINT for quiz in game.quizzes)
    assert all(quiz.hint.strip() for quiz in game.quizzes)



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



def test_add_quiz_collects_and_saves_hint_text(tmp_path, monkeypatch):
    state_path = tmp_path / "state.json"
    monkeypatch.setattr(main, "STATE_PATH", state_path)

    game = main.QuizGame()
    game.quizzes = []
    text_answers = iter(
        [
            "새 문제",
            "선택지 1",
            "선택지 2",
            "선택지 3",
            "선택지 4",
            "이 힌트는 정답 범주를 좁혀 줍니다.",
        ]
    )
    number_prompts = []

    monkeypatch.setattr(game, "ask_text", lambda prompt: next(text_answers))

    def fake_ask_number(prompt, min_value, max_value):
        number_prompts.append((prompt, min_value, max_value))
        return 3

    monkeypatch.setattr(game, "ask_number", fake_ask_number)

    game.add_quiz()

    assert len(game.quizzes) == 1
    assert game.quizzes[0].to_dict() == {
        "question": "새 문제",
        "choices": ["선택지 1", "선택지 2", "선택지 3", "선택지 4"],
        "answer": 3,
        "hint": "이 힌트는 정답 범주를 좁혀 줍니다.",
    }
    assert number_prompts == [("정답 번호 (1-4): ", 1, 4)]

    data = json.loads(state_path.read_text(encoding="utf-8"))
    assert data["quizzes"] == [game.quizzes[0].to_dict()]



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



def test_calculate_score_applies_hint_penalty_and_never_goes_below_zero(tmp_path, monkeypatch):
    state_path = tmp_path / "state.json"
    monkeypatch.setattr(main, "STATE_PATH", state_path)

    game = main.QuizGame()

    assert game.calculate_score(2, 3, 1) == 56
    assert game.calculate_score(0, 3, 1) == 0



def test_prompt_hint_returns_true_and_shows_hint_when_selected(tmp_path, monkeypatch, capsys):
    state_path = tmp_path / "state.json"
    monkeypatch.setattr(main, "STATE_PATH", state_path)

    game = main.QuizGame()
    quiz = main.Quiz("문제", ["1", "2", "3", "4"], 2, "도움말")
    asked = {}

    def fake_ask_number(prompt, min_value, max_value):
        asked["prompt"] = prompt
        asked["min"] = min_value
        asked["max"] = max_value
        return 1

    monkeypatch.setattr(game, "ask_number", fake_ask_number)

    hint_used = game.prompt_hint(quiz)

    output = capsys.readouterr().out
    assert hint_used is True
    assert asked == {
        "prompt": "힌트를 보시겠습니까? (1. 예 / 2. 아니오): ",
        "min": 1,
        "max": 2,
    }
    assert "힌트: 도움말" in output



def test_prompt_hint_returns_false_without_showing_hint_when_skipped(tmp_path, monkeypatch, capsys):
    state_path = tmp_path / "state.json"
    monkeypatch.setattr(main, "STATE_PATH", state_path)

    game = main.QuizGame()
    quiz = main.Quiz("문제", ["1", "2", "3", "4"], 2, "도움말")

    monkeypatch.setattr(game, "ask_number", lambda prompt, min_value, max_value: 2)

    hint_used = game.prompt_hint(quiz)

    output = capsys.readouterr().out
    assert hint_used is False
    assert "힌트: 도움말" not in output



def test_play_quiz_uses_prepared_round_count_and_hint_penalty_for_score_and_best_score(
    tmp_path, monkeypatch, capsys
):
    state_path = tmp_path / "state.json"
    monkeypatch.setattr(main, "STATE_PATH", state_path)

    game = main.QuizGame()
    round_quizzes = [
        main.Quiz("문제 1", ["1", "2", "3", "4"], 2, "첫 번째 힌트"),
        main.Quiz("문제 2", ["1", "2", "3", "4"], 4, "두 번째 힌트"),
        main.Quiz("문제 3", ["1", "2", "3", "4"], 1, "세 번째 힌트"),
    ]
    answers = iter([2, 1, 1])
    hint_usage = iter([True, False, False])

    monkeypatch.setattr(game, "prepare_quiz_round", lambda: round_quizzes)
    monkeypatch.setattr(game, "prompt_hint", lambda quiz: next(hint_usage))
    monkeypatch.setattr(game, "ask_number", lambda prompt, min_value, max_value: next(answers))

    game.play_quiz()

    output = capsys.readouterr().out
    assert "퀴즈를 시작합니다! (총 3문제)" in output
    assert "결과: 3문제 중 2문제 정답! (56점)" in output
    assert game.best_score == {"correct": 2, "total": 3, "score": 56}



def test_play_quiz_keeps_stored_quiz_order_after_round(tmp_path, monkeypatch):
    state_path = tmp_path / "state.json"
    monkeypatch.setattr(main, "STATE_PATH", state_path)

    game = main.QuizGame()
    original_quizzes = game.quizzes[:]
    round_quizzes = list(reversed(game.quizzes[:2]))
    answers = iter([quiz.answer for quiz in round_quizzes])

    monkeypatch.setattr(game, "prepare_quiz_round", lambda: round_quizzes)
    monkeypatch.setattr(game, "prompt_hint", lambda quiz: False)
    monkeypatch.setattr(game, "ask_number", lambda prompt, min_value, max_value: next(answers))

    game.play_quiz()

    assert game.quizzes == original_quizzes
    assert [quiz.question for quiz in game.quizzes] != [quiz.question for quiz in round_quizzes]



def test_record_history_appends_recent_result_with_timestamp(tmp_path, monkeypatch):
    state_path = tmp_path / "state.json"
    monkeypatch.setattr(main, "STATE_PATH", state_path)

    game = main.QuizGame()
    monkeypatch.setattr(game, "get_current_timestamp", lambda: "2026-04-03T21:22:23")

    game.record_history(3, 5, 60, 1)

    assert game.history == [
        {
            "played_at": "2026-04-03T21:22:23",
            "total": 5,
            "correct": 3,
            "score": 60,
            "hint_used": 1,
        }
    ]



def test_play_quiz_records_history_after_score_calculation(tmp_path, monkeypatch):
    state_path = tmp_path / "state.json"
    monkeypatch.setattr(main, "STATE_PATH", state_path)

    game = main.QuizGame()
    round_quizzes = [main.Quiz("문제", ["1", "2", "3", "4"], 2, "힌트")]
    call_order = []

    monkeypatch.setattr(game, "prepare_quiz_round", lambda: round_quizzes)
    monkeypatch.setattr(game, "prompt_hint", lambda quiz: True)
    monkeypatch.setattr(game, "ask_number", lambda prompt, min_value, max_value: 2)

    def fake_calculate_score(correct_answers, total_questions, hint_used_count):
        call_order.append(("calculate_score", correct_answers, total_questions, hint_used_count))
        return 90

    def fake_record_history(correct_answers, total_questions, score, hint_used_count):
        call_order.append(("record_history", correct_answers, total_questions, score, hint_used_count))

    monkeypatch.setattr(game, "calculate_score", fake_calculate_score)
    monkeypatch.setattr(game, "record_history", fake_record_history)

    game.play_quiz()

    assert call_order == [
        ("calculate_score", 1, 1, 1),
        ("record_history", 1, 1, 90, 1),
    ]



def test_play_quiz_persists_recorded_history_to_written_state(tmp_path, monkeypatch):
    state_path = tmp_path / "state.json"
    monkeypatch.setattr(main, "STATE_PATH", state_path)

    game = main.QuizGame()
    round_quizzes = [main.Quiz("문제", ["1", "2", "3", "4"], 2, "힌트")]

    monkeypatch.setattr(game, "prepare_quiz_round", lambda: round_quizzes)
    monkeypatch.setattr(game, "prompt_hint", lambda quiz: True)
    monkeypatch.setattr(game, "ask_number", lambda prompt, min_value, max_value: 2)
    monkeypatch.setattr(game, "get_current_timestamp", lambda: "2026-04-03T21:22:23")

    game.play_quiz()

    data = json.loads(state_path.read_text(encoding="utf-8"))
    assert data["history"] == [
        {
            "played_at": "2026-04-03T21:22:23",
            "total": 1,
            "correct": 1,
            "score": 90,
            "hint_used": 1,
        }
    ]



def test_show_best_score_displays_bounded_recent_history_most_recent_first(
    tmp_path, monkeypatch, capsys
):
    state_path = tmp_path / "state.json"
    monkeypatch.setattr(main, "STATE_PATH", state_path)

    game = main.QuizGame()
    game.best_score = {"correct": 4, "total": 5, "score": 80}
    game.history = [
        {
            "played_at": "2026-04-03T10:00:00",
            "total": 1,
            "correct": 1,
            "score": 100,
            "hint_used": 0,
        },
        {
            "played_at": "2026-04-03T11:00:00",
            "total": 2,
            "correct": 1,
            "score": 50,
            "hint_used": 1,
        },
        {
            "played_at": "2026-04-03T12:00:00",
            "total": 3,
            "correct": 2,
            "score": 66,
            "hint_used": 1,
        },
        {
            "played_at": "2026-04-03T13:00:00",
            "total": 4,
            "correct": 3,
            "score": 75,
            "hint_used": 0,
        },
        {
            "played_at": "2026-04-03T14:00:00",
            "total": 5,
            "correct": 4,
            "score": 80,
            "hint_used": 1,
        },
        {
            "played_at": "2026-04-03T15:00:00",
            "total": 6,
            "correct": 5,
            "score": 83,
            "hint_used": 0,
        },
    ]

    game.show_best_score()

    output = capsys.readouterr().out
    assert "최고 점수: 80점 (5문제 중 4문제 정답)" in output
    assert "최근 플레이 기록" in output
    assert "2026-04-03T10:00:00 - 1문제 중 1문제 정답 (100점, 힌트 0회 사용)" not in output

    recent_entries = [
        "2026-04-03T15:00:00 - 6문제 중 5문제 정답 (83점, 힌트 0회 사용)",
        "2026-04-03T14:00:00 - 5문제 중 4문제 정답 (80점, 힌트 1회 사용)",
        "2026-04-03T13:00:00 - 4문제 중 3문제 정답 (75점, 힌트 0회 사용)",
        "2026-04-03T12:00:00 - 3문제 중 2문제 정답 (66점, 힌트 1회 사용)",
        "2026-04-03T11:00:00 - 2문제 중 1문제 정답 (50점, 힌트 1회 사용)",
    ]
    positions = [output.index(entry) for entry in recent_entries]
    assert positions == sorted(positions)





def test_delete_quiz_removes_selected_quiz_after_confirmation(tmp_path, monkeypatch, capsys):
    state_path = tmp_path / "state.json"
    monkeypatch.setattr(main, "STATE_PATH", state_path)

    game = main.QuizGame()
    game.quizzes = [
        main.Quiz("첫 번째 문제", ["1", "2", "3", "4"], 1),
        main.Quiz("두 번째 문제", ["1", "2", "3", "4"], 2),
    ]

    answers = iter([2, 1])
    prompts = []

    def fake_ask_number(prompt, min_value, max_value):
        prompts.append((prompt, min_value, max_value))
        return next(answers)

    monkeypatch.setattr(game, "ask_number", fake_ask_number)

    game.delete_quiz()

    output = capsys.readouterr().out
    assert prompts == [
        ("삭제할 퀴즈 번호를 선택하세요: ", 1, 2),
        ("정말 삭제하시겠습니까? (1. 예 / 2. 아니오): ", 1, 2),
    ]
    assert [quiz.question for quiz in game.quizzes] == ["첫 번째 문제"]
    assert "[1] 첫 번째 문제" in output
    assert "[2] 두 번째 문제" in output
    assert "퀴즈가 삭제되었습니다!" in output

    data = json.loads(state_path.read_text(encoding="utf-8"))
    assert [quiz["question"] for quiz in data["quizzes"]] == ["첫 번째 문제"]



def test_delete_quiz_cancels_when_confirmation_is_declined(tmp_path, monkeypatch, capsys):
    state_path = tmp_path / "state.json"
    monkeypatch.setattr(main, "STATE_PATH", state_path)

    game = main.QuizGame()
    game.quizzes = [
        main.Quiz("첫 번째 문제", ["1", "2", "3", "4"], 1),
        main.Quiz("두 번째 문제", ["1", "2", "3", "4"], 2),
    ]

    answers = iter([1, 2])
    monkeypatch.setattr(game, "ask_number", lambda prompt, min_value, max_value: next(answers))

    game.delete_quiz()

    output = capsys.readouterr().out
    assert [quiz.question for quiz in game.quizzes] == ["첫 번째 문제", "두 번째 문제"]
    assert "퀴즈 삭제가 취소되었습니다." in output



def test_delete_quiz_shows_message_when_no_quizzes_exist(tmp_path, monkeypatch, capsys):
    state_path = tmp_path / "state.json"
    monkeypatch.setattr(main, "STATE_PATH", state_path)

    game = main.QuizGame()
    game.quizzes = []
    asked = {"called": False}

    def fake_ask_number(prompt, min_value, max_value):
        asked["called"] = True
        return 1

    monkeypatch.setattr(game, "ask_number", fake_ask_number)

    game.delete_quiz()

    output = capsys.readouterr().out
    assert "등록된 퀴즈가 없습니다." in output
    assert asked["called"] is False



def test_handle_menu_routes_delete_and_exit_in_expanded_menu(tmp_path, monkeypatch):
    state_path = tmp_path / "state.json"
    monkeypatch.setattr(main, "STATE_PATH", state_path)

    game = main.QuizGame()
    called = []

    monkeypatch.setattr(game, "delete_quiz", lambda: called.append("delete"))
    monkeypatch.setattr(game, "exit_game", lambda: called.append("exit"))

    game.handle_menu(4)
    game.handle_menu(6)

    assert called == ["delete", "exit"]



def test_run_accepts_expanded_menu_range_and_handles_delete_then_exit(tmp_path, monkeypatch):
    state_path = tmp_path / "state.json"
    monkeypatch.setattr(main, "STATE_PATH", state_path)

    game = main.QuizGame()
    selections = iter([4, 6])
    ask_calls = []
    handled = []

    monkeypatch.setattr(game, "show_menu", lambda: None)

    def fake_ask_number(prompt, min_value, max_value):
        ask_calls.append((prompt, min_value, max_value))
        return next(selections)

    def fake_handle_menu(selected_menu):
        handled.append(selected_menu)
        if selected_menu == 6:
            game.is_running = False

    monkeypatch.setattr(game, "ask_number", fake_ask_number)
    monkeypatch.setattr(game, "handle_menu", fake_handle_menu)

    game.run()

    assert ask_calls == [
        ("선택: ", 1, 6),
        ("선택: ", 1, 6),
    ]
    assert handled == [4, 6]



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
