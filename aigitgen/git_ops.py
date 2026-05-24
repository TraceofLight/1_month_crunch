from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


class GitError(RuntimeError):
    pass


@dataclass
class GitSnapshot:
    status: str
    diff: str
    branch: str
    changed_files: list[str]

    @property
    def has_changes(self) -> bool:
        return bool(self.status.strip()) or bool(self.diff.strip())


def _run(args: list[str], cwd: Path | None = None) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except FileNotFoundError as exc:
        raise GitError("git 실행 파일을 찾을 수 없습니다. Git 설치 여부를 확인하세요.") from exc

    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip()
        raise GitError(f"git {' '.join(args)} 실패: {message}")
    return result.stdout


def ensure_git_repo(cwd: Path | None = None) -> None:
    try:
        _run(["rev-parse", "--is-inside-work-tree"], cwd=cwd)
    except GitError as exc:
        raise GitError("현재 디렉터리는 Git 저장소가 아닙니다. `git init` 후 다시 시도하세요.") from exc


def current_branch(cwd: Path | None = None) -> str:
    return _run(["rev-parse", "--abbrev-ref", "HEAD"], cwd=cwd).strip() or "HEAD"


def collect_status(cwd: Path | None = None) -> tuple[str, list[str], list[str]]:
    """Return (pretty status, all changed file paths, untracked-only paths)."""
    raw = _run(["status", "--porcelain=v1"], cwd=cwd)
    files: list[str] = []
    untracked: list[str] = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        marker = line[:2]
        # porcelain format: XY <path>  (rename: XY old -> new)
        path = line[3:].strip().strip('"')
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        files.append(path)
        if marker == "??":
            untracked.append(path)

    pretty = _run(["status", "--short"], cwd=cwd)
    return pretty, files, untracked


def _diff_untracked(paths: list[str], cwd: Path | None = None) -> str:
    """Synthesize a diff for untracked files by comparing against an empty input.

    Uses `git diff --no-index` which generates output without mutating the index.
    Returns concatenated diff blocks. Binary files are skipped automatically by git.
    """
    blocks: list[str] = []
    null_dev = "/dev/null"
    for path in paths:
        try:
            result = subprocess.run(
                ["git", "diff", "--no-index", "--", null_dev, path],
                cwd=cwd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
        except FileNotFoundError as exc:
            raise GitError("git 실행 파일을 찾을 수 없습니다.") from exc
        # `git diff --no-index` exits 1 when there is a diff (which is normal here).
        if result.returncode not in (0, 1):
            continue
        if result.stdout.strip():
            blocks.append(result.stdout)
    return "".join(blocks)


def collect_diff(
    cwd: Path | None = None,
    staged_only: bool = False,
    base: str | None = None,
    untracked: list[str] | None = None,
) -> str:
    """Collect a unified diff.

    Priority:
      - If base is provided, return `git diff <base>...HEAD` (PR-style).
      - If staged_only, return staged diff (plus untracked-as-new-file diff if any).
      - Otherwise return combined staged + unstaged diff appended with untracked-file diffs.
    """
    if base:
        return _run(["diff", f"{base}...HEAD"], cwd=cwd)

    if staged_only:
        diff = _run(["diff", "--staged"], cwd=cwd)
    else:
        try:
            diff = _run(["diff", "HEAD"], cwd=cwd)
        except GitError:
            # No HEAD yet (fresh repo). Fall back to staged-only diff.
            diff = _run(["diff", "--staged"], cwd=cwd)

    if untracked:
        diff += _diff_untracked(untracked, cwd=cwd)
    return diff


def snapshot(
    cwd: Path | None = None,
    *,
    staged_only: bool = False,
    base: str | None = None,
) -> GitSnapshot:
    ensure_git_repo(cwd)
    status, files, untracked = collect_status(cwd)
    diff = collect_diff(cwd, staged_only=staged_only, base=base, untracked=untracked)
    branch = current_branch(cwd)
    return GitSnapshot(status=status, diff=diff, branch=branch, changed_files=files)
