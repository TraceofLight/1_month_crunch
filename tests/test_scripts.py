"""Script entry point tests."""

import subprocess
import sys

import pytest

from mini_redis.cli import main


def test_demo_script_runs_from_repository_root():
    """scripts/demo.py works when executed as the documented file path."""
    result = subprocess.run(
        [sys.executable, "scripts/demo.py"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "mini-redis> CONFIG SET maxmemory 30" in result.stdout
    assert "(error) ERR unknown command 'HELLO'" in result.stdout


def test_repl_script_accepts_quit_from_standard_input():
    """scripts/run.py starts the REPL and exits on quit."""
    result = subprocess.run(
        [sys.executable, "scripts/run.py"],
        input="quit\n",
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "mini-redis>" in result.stdout


def test_repl_exits_cleanly_on_keyboard_interrupt(monkeypatch, capsys):
    """Ctrl+C exits the REPL without propagating a traceback."""
    def raise_keyboard_interrupt(_prompt):
        raise KeyboardInterrupt

    monkeypatch.setattr("builtins.input", raise_keyboard_interrupt)

    try:
        main()
    except KeyboardInterrupt:
        pytest.fail("KeyboardInterrupt must not escape the REPL")

    assert capsys.readouterr().out == "\n"


def test_repl_reports_input_errors_and_continues(monkeypatch, capsys):
    """Unexpected input errors do not terminate the REPL with a traceback."""
    responses = [OSError("input failed"), "quit"]

    def read_input(_prompt):
        response = responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response

    monkeypatch.setattr("builtins.input", read_input)

    main()

    assert capsys.readouterr().out == "(error) ERR internal error: input failed\n"


def test_repl_reports_command_errors_and_continues(monkeypatch, capsys):
    """Unexpected command errors do not terminate the REPL with a traceback."""
    class BrokenRedis:
        def execute(self, _line):
            raise RuntimeError("command failed")

    responses = ["GET key", "quit"]
    monkeypatch.setattr("builtins.input", lambda _prompt: responses.pop(0))
    monkeypatch.setattr("mini_redis.cli.MiniRedis", BrokenRedis)

    main()

    assert capsys.readouterr().out == "(error) ERR internal error: command failed\n"
