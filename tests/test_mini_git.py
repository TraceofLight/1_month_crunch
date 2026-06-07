"""Mini Git의 핵심 저장소 동작과 CLI 파서를 검증한다."""

import inspect

import scripts.run as run_script
from main import MiniGit, parse_command
from scripts.run import run_demo


def test_commit_graph_branch_search_and_topological_log():
    repo = MiniGit(clock=DeterministicClock())

    assert repo.execute('init "Alice Kim"') == [
        "Initialized repository.",
        "Current branch: main",
        "Current user: Alice Kim",
    ]
    first = repo.create_commit("Initial commit")
    assert repo.execute("branch feature") == ["Created branch: feature"]
    assert repo.execute("switch feature") == ["Switched to branch: feature"]
    login = repo.create_commit("Add login feature")
    assert repo.execute("switch main") == ["Switched to branch: main"]
    payment = repo.create_commit("Add payment feature")

    assert first != login != payment
    assert repo.commits[login].parents == [first]
    assert repo.commits[payment].parents == [first]
    assert repo.execute("search login") == [
        "Found 1 commit:",
        f"- {login}: Add login feature",
    ]
    assert repo.execute('search --author="Alice Kim"') == [
        "Found 3 commits:",
        f"- {first}: Initial commit",
        f"- {login}: Add login feature",
        f"- {payment}: Add payment feature",
    ]

    log_output = repo.execute("log")
    positions = {
        first: _line_index(log_output, f"commit {first}"),
        login: _line_index(log_output, f"commit {login}"),
        payment: _line_index(log_output, f"commit {payment}"),
    }
    assert positions[first] < positions[login]
    assert positions[first] < positions[payment]


def test_path_uses_undirected_shortest_path_with_lexicographic_tie_break():
    repo = MiniGit(clock=DeterministicClock())
    repo.initialize("Alice")
    root = repo.create_commit("root")
    repo.create_branch("a")
    repo.create_branch("b")
    repo.switch_branch("a")
    left = repo.create_commit("left")
    repo.switch_branch("b")
    right = repo.create_commit("right")

    assert repo.execute(f"path {left} {right}") == [f"Path: {left} -> {root} -> {right}"]


def test_ancestors_log_sort_and_errors_are_deterministic():
    repo = MiniGit(clock=DeterministicClock())
    repo.execute("init Bob")
    first = repo.create_commit("First")
    second = repo.create_commit("Second")
    repo.current_user = "Alice"
    third = repo.create_commit("Third")

    assert repo.execute(f"ancestors {third}") == [
        f"- {second}: Second",
        f"- {first}: First",
    ]
    author_log = repo.execute("log --sort-by=author")
    assert _line_index(author_log, "Alice") < _line_index(author_log, "Bob")
    date_log = repo.execute("log --sort-by=date")
    assert _line_index(date_log, f"commit {first}") < _line_index(date_log, f"commit {second}") < _line_index(date_log, f"commit {third}")
    assert repo.execute("switch missing") == ["Unknown branch: missing"]
    assert repo.execute("path missing also-missing") == ["Unknown commit: missing"]
    assert repo.execute("log --sort-by=size") == ["Invalid args"]


def test_parser_accepts_case_insensitive_commands_quotes_and_options():
    assert parse_command('CoMmIt "Add login feature"') == ("COMMIT", ["Add login feature"])
    assert parse_command('SEARCH --author="Alice Kim"') == ("SEARCH", ["--author=Alice Kim"])
    assert parse_command("LOG --sort-by=date") == ("LOG", ["--sort-by=date"])
    assert parse_command("") == ("", [])
    assert MiniGit().execute('commit "unterminated') == ["Invalid args"]


def test_search_accepts_quoted_multi_word_keyword_query():
    repo = MiniGit(clock=DeterministicClock())
    repo.execute("init Alice")
    matching = repo.create_commit("Add login feature")
    repo.create_commit("Add login docs")
    repo.create_commit("Remove payment feature")

    assert repo.execute('search "login feature"') == [
        "Found 1 commit:",
        f"- {matching}: Add login feature",
    ]


def test_merge_creates_commit_with_two_parents():
    repo = MiniGit(clock=DeterministicClock())
    repo.execute("init Alice")
    root = repo.create_commit("root")
    repo.execute("branch feature")
    repo.execute("switch feature")
    feature = repo.create_commit("feature work")
    repo.execute("switch main")
    main = repo.create_commit("main work")

    output = repo.execute("merge feature")
    merge_hash = output[0].split()[1].rstrip("]")

    assert output == [f"[main {merge_hash}] Merge branch feature"]
    assert repo.commits[merge_hash].parents == [main, feature]
    assert repo.execute(f"ancestors {merge_hash}") == [
        f"- {main}: main work",
        f"- {feature}: feature work",
        f"- {root}: root",
    ]


def test_diff_marks_common_deleted_and_added_lines(tmp_path):
    left = tmp_path / "left.txt"
    right = tmp_path / "right.txt"
    left.write_text("same\nold\nkeep\n", encoding="utf-8")
    right.write_text("same\nnew\nkeep\n", encoding="utf-8")

    repo = MiniGit()
    assert repo.execute(f'diff "{left}" "{right}"') == [
        "  same",
        "- old",
        "+ new",
        "  keep",
    ]


def test_read_commands_require_initialized_repository():
    repo = MiniGit()

    assert repo.execute("log") == ["Repository not initialized"]
    assert repo.execute("search login") == ["Repository not initialized"]
    assert repo.execute("path c000001 c000002") == ["Repository not initialized"]
    assert repo.execute("ancestors c000001") == ["Repository not initialized"]


def test_source_does_not_use_python_standard_sort_api():
    source = inspect.getsource(__import__("main"))
    assert "sorted(" not in source
    assert ".sort(" not in source


def test_demo_script_writes_reproducible_evidence(tmp_path):
    output_path = run_demo(tmp_path)

    content = output_path.read_text(encoding="utf-8")
    assert "mini-git> init \"Alice Kim\"" in content
    assert "Path: c000002 -> c000001 -> c000003" in content
    assert "Found 1 commit:" in content


def test_sort_benchmark_writes_reproducible_evidence(tmp_path):
    assert hasattr(run_script, "run_sort_benchmark")
    output_path = run_script.run_sort_benchmark(tmp_path)

    content = output_path.read_text(encoding="utf-8")
    assert "algorithm,size,seconds,first,last" in content
    assert "merge_sort,40," in content
    assert "insertion_sort,40," in content


class DeterministicClock:
    """테스트에서 커밋 시간의 순서를 고정한다."""

    def __init__(self):
        self.counter = 0

    def now(self):
        self.counter += 1
        return f"2026-06-07 09:00:{self.counter:02d}"


def _line_index(lines, fragment):
    for index, line in enumerate(lines):
        if fragment in line:
            return index
    raise AssertionError(f"{fragment!r} not found in {lines!r}")
