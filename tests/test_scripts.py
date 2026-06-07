"""Script entry point tests."""

import subprocess
import sys


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
