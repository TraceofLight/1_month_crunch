"""메모리 기반 Mini Git CLI와 커밋 그래프 알고리즘을 제공한다."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import shlex
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Tuple


@dataclass
class Commit:
    """Mini Git 커밋 노드의 최소 메타데이터를 보관한다."""

    hash: str
    message: str
    author: str
    timestamp: str
    parents: List[str]


class SystemClock:
    """실행 시점의 시간을 커밋 timestamp 형식으로 변환한다."""

    def now(self) -> str:
        """현재 지역 시간을 초 단위 문자열로 반환한다."""

        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class MiniGit:
    """브랜치, 커밋 DAG, 역색인, 탐색 명령을 메모리에서 관리한다."""

    def __init__(self, clock: Optional[SystemClock] = None):
        self.clock = clock or SystemClock()
        self.current_user: Optional[str] = None
        self.current_branch: Optional[str] = None
        self.branches: Dict[str, Optional[str]] = {}
        self.commits: Dict[str, Commit] = {}
        self.keyword_index: Dict[str, List[str]] = {}
        self.author_index: Dict[str, List[str]] = {}
        self.commit_counter = 0

    def execute(self, line: str) -> List[str]:
        """한 줄 명령을 파싱하고 대응하는 저장소 동작의 출력 줄을 반환한다."""

        command, args = parse_command(line)
        if command == "":
            return []
        if command == "INVALID":
            return ["Invalid args"]
        if command == "INIT":
            if len(args) != 1:
                return ["Invalid args"]
            return self.initialize(args[0])
        if command == "BRANCH":
            if len(args) != 1:
                return ["Invalid args"]
            return self.create_branch(args[0])
        if command == "SWITCH":
            if len(args) != 1:
                return ["Invalid args"]
            return self.switch_branch(args[0])
        if command == "COMMIT":
            if len(args) != 1:
                return ["Invalid args"]
            result = self.create_commit(args[0])
            if result is None:
                return ["Repository not initialized"]
            return [f"[{self.current_branch} {result}] {args[0]}"]
        if command == "LOG":
            return self.log_command(args)
        if command == "PATH":
            if len(args) != 2:
                return ["Invalid args"]
            return self.path_command(args[0], args[1])
        if command == "ANCESTORS":
            if len(args) != 1:
                return ["Invalid args"]
            return self.ancestors_command(args[0])
        if command == "SEARCH":
            return self.search_command(args)
        if command == "MERGE":
            if len(args) != 1:
                return ["Invalid args"]
            return self.merge_command(args[0])
        if command == "DIFF":
            if len(args) != 2:
                return ["Invalid args"]
            return diff_files(args[0], args[1])
        return [f"Unknown command: {command.lower()}"]

    def initialize(self, user_name: str) -> List[str]:
        """저장소 상태를 초기화하고 main 브랜치와 현재 author를 설정한다."""

        self.current_user = user_name
        self.current_branch = "main"
        self.branches = {"main": None}
        self.commits = {}
        self.keyword_index = {}
        self.author_index = {}
        self.commit_counter = 0
        return [
            "Initialized repository.",
            "Current branch: main",
            f"Current user: {user_name}",
        ]

    def create_branch(self, branch_name: str) -> List[str]:
        """현재 HEAD를 가리키는 새 브랜치를 만든다."""

        if not self._is_initialized():
            return ["Repository not initialized"]
        if branch_name in self.branches:
            return [f"Branch already exists: {branch_name}"]
        self.branches[branch_name] = self.branches[self.current_branch]
        return [f"Created branch: {branch_name}"]

    def switch_branch(self, branch_name: str) -> List[str]:
        """HEAD를 지정한 브랜치로 전환한다."""

        if not self._is_initialized():
            return ["Repository not initialized"]
        if branch_name not in self.branches:
            return [f"Unknown branch: {branch_name}"]
        self.current_branch = branch_name
        return [f"Switched to branch: {branch_name}"]

    def create_commit(self, message: str, parents: Optional[List[str]] = None) -> Optional[str]:
        """현재 HEAD를 부모로 하는 커밋을 생성하고 역색인을 갱신한다."""

        if not self._is_initialized():
            return None
        if parents is None:
            head = self.branches[self.current_branch]
            parents = [] if head is None else [head]
        commit_hash = self._next_hash()
        commit = Commit(
            hash=commit_hash,
            message=message,
            author=self.current_user or "",
            timestamp=self.clock.now(),
            parents=copy_list(parents),
        )
        self.commits[commit_hash] = commit
        self.branches[self.current_branch] = commit_hash
        self._index_commit(commit)
        return commit_hash

    def merge_command(self, branch_name: str) -> List[str]:
        """현재 브랜치와 대상 브랜치 HEAD를 부모로 하는 병합 커밋을 만든다."""

        if not self._is_initialized():
            return ["Repository not initialized"]
        if branch_name not in self.branches:
            return [f"Unknown branch: {branch_name}"]
        if branch_name == self.current_branch:
            return ["Invalid args"]
        current_head = self.branches[self.current_branch]
        target_head = self.branches[branch_name]
        if current_head is None:
            return ["Current branch has no commits"]
        if target_head is None:
            return [f"Branch has no commits: {branch_name}"]
        message = f"Merge branch {branch_name}"
        commit_hash = self.create_commit(message, [current_head, target_head])
        return [f"[{self.current_branch} {commit_hash}] {message}"]

    def log_command(self, args: List[str]) -> List[str]:
        """기본 위상 순서 로그 또는 지정 기준 정렬 로그를 반환한다."""

        if not self._is_initialized():
            return ["Repository not initialized"]
        if len(args) == 0:
            commits = self.topological_commits()
            return self._format_commits(commits)
        if len(args) != 1 or not args[0].startswith("--sort-by="):
            return ["Invalid args"]
        key = args[0][len("--sort-by=") :]
        if key == "date":
            commits = merge_sort(
                list(self.commits.values()),
                lambda left, right: compare_text(left.timestamp, right.timestamp)
                or compare_text(left.hash, right.hash),
            )
            return self._format_commits(commits)
        if key == "author":
            commits = merge_sort(
                list(self.commits.values()),
                lambda left, right: compare_text(left.author, right.author)
                or compare_text(left.timestamp, right.timestamp)
                or compare_text(left.hash, right.hash),
            )
            return self._format_commits(commits)
        return ["Invalid args"]

    def path_command(self, start: str, goal: str) -> List[str]:
        """커밋-부모 간선을 무방향으로 보아 최단 경로를 계산한다."""

        if not self._is_initialized():
            return ["Repository not initialized"]
        missing = self._first_missing_commit([start, goal])
        if missing:
            return [f"Unknown commit: {missing}"]
        path = self.shortest_path(start, goal)
        if not path:
            return ["No path"]
        return ["Path: " + " -> ".join(path)]

    def ancestors_command(self, commit_hash: str) -> List[str]:
        """지정 커밋에서 부모 방향으로 도달 가능한 모든 조상을 반환한다."""

        if not self._is_initialized():
            return ["Repository not initialized"]
        if commit_hash not in self.commits:
            return [f"Unknown commit: {commit_hash}"]
        ancestors = self.ancestors(commit_hash)
        if len(ancestors) == 0:
            return ["No ancestors"]
        return [f"- {commit.hash}: {commit.message}" for commit in ancestors]

    def search_command(self, args: List[str]) -> List[str]:
        """역색인에서 키워드 또는 author 후보 커밋을 가져와 출력한다."""

        if not self._is_initialized():
            return ["Repository not initialized"]
        if len(args) != 1:
            return ["Invalid args"]
        if args[0].startswith("--author="):
            author = args[0][len("--author=") :]
            hashes = self.author_index.get(author, [])
        elif args[0].startswith("--"):
            return ["Invalid args"]
        else:
            tokens = tokenize_message(args[0])
            hashes = indexed_intersection(self.keyword_index, tokens)
        commits = [self.commits[commit_hash] for commit_hash in hashes]
        return self._format_search(commits)

    def topological_commits(self) -> List[Commit]:
        """모든 커밋을 부모가 자식보다 먼저 나오도록 DFS 후위 순서로 반환한다."""

        visited = set()
        result: List[Commit] = []
        for commit_hash in self.commits:
            self._visit_parent_first(commit_hash, visited, result)
        return result

    def shortest_path(self, start: str, goal: str) -> List[str]:
        """BFS로 모든 최단 후보를 찾고 문자열 기준 사전순 최소 경로를 고른다."""

        if start == goal:
            return [start]
        adjacency = self._undirected_adjacency()
        queue = deque([[start]])
        best_depth = None
        best_path: List[str] = []
        seen_depth = {start: 0}
        while queue:
            path = queue.popleft()
            current = path[-1]
            depth = len(path) - 1
            if best_depth is not None and depth > best_depth:
                continue
            if current == goal:
                if best_depth is None or path_string(path) < path_string(best_path):
                    best_depth = depth
                    best_path = path
                continue
            for neighbor in adjacency.get(current, []):
                next_depth = depth + 1
                if best_depth is not None and next_depth > best_depth:
                    continue
                if neighbor in path:
                    continue
                previous_depth = seen_depth.get(neighbor)
                if previous_depth is not None and previous_depth < next_depth:
                    continue
                seen_depth[neighbor] = next_depth
                queue.append(path + [neighbor])
        return best_path

    def ancestors(self, commit_hash: str) -> List[Commit]:
        """스택 기반 DFS로 모든 조상을 중복 없이 수집한다."""

        visited = set()
        result: List[Commit] = []
        stack = copy_list(self.commits[commit_hash].parents)
        while stack:
            parent_hash = stack.pop(0)
            if parent_hash in visited:
                continue
            visited.add(parent_hash)
            parent = self.commits[parent_hash]
            result.append(parent)
            for grand_parent in parent.parents:
                if grand_parent not in visited:
                    stack.append(grand_parent)
        return result

    def _visit_parent_first(self, commit_hash: str, visited: set, result: List[Commit]) -> None:
        if commit_hash in visited:
            return
        visited.add(commit_hash)
        commit = self.commits[commit_hash]
        for parent_hash in commit.parents:
            self._visit_parent_first(parent_hash, visited, result)
        result.append(commit)

    def _undirected_adjacency(self) -> Dict[str, List[str]]:
        adjacency: Dict[str, List[str]] = {commit_hash: [] for commit_hash in self.commits}
        for commit in self.commits.values():
            for parent_hash in commit.parents:
                adjacency[commit.hash].append(parent_hash)
                adjacency[parent_hash].append(commit.hash)
        for commit_hash in adjacency:
            adjacency[commit_hash] = merge_sort(
                adjacency[commit_hash],
                lambda left, right: compare_text(left, right),
            )
        return adjacency

    def _format_commits(self, commits: Iterable[Commit]) -> List[str]:
        lines: List[str] = []
        for commit in commits:
            labels = self._branch_labels(commit.hash)
            suffix = f" [{', '.join(labels)}]" if labels else ""
            lines.append(f"commit {commit.hash} ({commit.author}, {commit.timestamp}){suffix}")
            lines.append(commit.message)
        return lines

    def _format_search(self, commits: Sequence[Commit]) -> List[str]:
        count = len(commits)
        noun = "commit" if count == 1 else "commits"
        lines = [f"Found {count} {noun}:"]
        for commit in commits:
            lines.append(f"- {commit.hash}: {commit.message}")
        return lines

    def _branch_labels(self, commit_hash: str) -> List[str]:
        labels: List[str] = []
        for branch_name, head_hash in self.branches.items():
            if head_hash == commit_hash:
                labels.append(branch_name)
        return labels

    def _index_commit(self, commit: Commit) -> None:
        append_to_index(self.author_index, commit.author, commit.hash)
        for token in tokenize_message(commit.message):
            append_to_index(self.keyword_index, token, commit.hash)

    def _next_hash(self) -> str:
        self.commit_counter += 1
        commit_hash = f"c{self.commit_counter:06d}"
        while commit_hash in self.commits:
            self.commit_counter += 1
            commit_hash = f"c{self.commit_counter:06d}"
        return commit_hash

    def _first_missing_commit(self, commit_hashes: Sequence[str]) -> Optional[str]:
        for commit_hash in commit_hashes:
            if commit_hash not in self.commits:
                return commit_hash
        return None

    def _is_initialized(self) -> bool:
        return self.current_branch is not None and self.current_branch in self.branches


def parse_command(line: str) -> Tuple[str, List[str]]:
    """shlex 기반으로 따옴표 포함 CLI 입력을 명령과 인자로 분리한다."""

    try:
        parts = shlex.split(line)
    except ValueError:
        return "INVALID", []
    if len(parts) == 0:
        return "", []
    return parts[0].upper(), parts[1:]


def tokenize_message(message: str) -> List[str]:
    """커밋 메시지를 공백으로 나눈 뒤 소문자로 정규화한다."""

    tokens: List[str] = []
    for token in message.split():
        normalized = normalize_token(token)
        if normalized != "":
            tokens.append(normalized)
    return tokens


def normalize_token(token: str) -> str:
    """검색 키워드와 메시지 토큰에 같은 정규화를 적용한다."""

    return token.lower()


def append_to_index(index: Dict[str, List[str]], key: str, commit_hash: str) -> None:
    """역색인 목록에 같은 커밋 해시가 중복 저장되지 않게 추가한다."""

    if key not in index:
        index[key] = []
    for existing in index[key]:
        if existing == commit_hash:
            return
    index[key].append(commit_hash)


def indexed_intersection(index: Dict[str, List[str]], keys: Sequence[str]) -> List[str]:
    """여러 역색인 키를 모두 포함하는 커밋 해시를 첫 키의 순서대로 반환한다."""

    if len(keys) == 0:
        return []
    first_posting = index.get(keys[0], [])
    result: List[str] = []
    for commit_hash in first_posting:
        if is_in_all_postings(index, keys[1:], commit_hash):
            result.append(commit_hash)
    return result


def is_in_all_postings(
    index: Dict[str, List[str]],
    keys: Sequence[str],
    commit_hash: str,
) -> bool:
    """커밋 해시가 나머지 모든 posting list에 포함되는지 확인한다."""

    for key in keys:
        found = False
        for candidate_hash in index.get(key, []):
            if candidate_hash == commit_hash:
                found = True
                break
        if not found:
            return False
    return True


def merge_sort(items: List, compare: Callable) -> List:
    """비교 함수를 받는 안정 병합 정렬을 직접 구현한다."""

    if len(items) <= 1:
        return copy_list(items)
    midpoint = len(items) // 2
    left = merge_sort(items[:midpoint], compare)
    right = merge_sort(items[midpoint:], compare)
    return merge(left, right, compare)


def insertion_sort(items: List, compare: Callable) -> List:
    """작은 입력의 비교용으로 안정 삽입 정렬을 직접 구현한다."""

    result = copy_list(items)
    index = 1
    while index < len(result):
        value = result[index]
        cursor = index - 1
        while cursor >= 0 and compare(result[cursor], value) > 0:
            result[cursor + 1] = result[cursor]
            cursor -= 1
        result[cursor + 1] = value
        index += 1
    return result


def merge(left: List, right: List, compare: Callable) -> List:
    """두 정렬 구간을 안정성을 유지하며 병합한다."""

    merged: List = []
    left_index = 0
    right_index = 0
    while left_index < len(left) and right_index < len(right):
        if compare(left[left_index], right[right_index]) <= 0:
            merged.append(left[left_index])
            left_index += 1
        else:
            merged.append(right[right_index])
            right_index += 1
    while left_index < len(left):
        merged.append(left[left_index])
        left_index += 1
    while right_index < len(right):
        merged.append(right[right_index])
        right_index += 1
    return merged


def compare_text(left: str, right: str) -> int:
    """문자열 비교 결과를 -1, 0, 1 중 하나로 반환한다."""

    if left < right:
        return -1
    if left > right:
        return 1
    return 0


def copy_list(items: Sequence) -> List:
    """입력 순서를 유지한 새 리스트를 만든다."""

    copied: List = []
    for item in items:
        copied.append(item)
    return copied


def path_string(path: Sequence[str]) -> str:
    """경로 후보의 사전순 비교용 문자열을 만든다."""

    return "->".join(path)


def diff_files(left_path: str, right_path: str) -> List[str]:
    """두 텍스트 파일을 줄 단위로 비교해 공통, 삭제, 추가 줄을 출력한다."""

    try:
        left_lines = Path(left_path).read_text(encoding="utf-8").splitlines()
        right_lines = Path(right_path).read_text(encoding="utf-8").splitlines()
    except OSError as error:
        return [f"File error: {error.filename}"]
    return diff_lines(left_lines, right_lines)


def diff_lines(left_lines: Sequence[str], right_lines: Sequence[str]) -> List[str]:
    """LCS 테이블을 사용해 두 줄 목록의 간단한 diff를 만든다."""

    table = lcs_lengths(left_lines, right_lines)
    return build_diff(left_lines, right_lines, table)


def lcs_lengths(left_lines: Sequence[str], right_lines: Sequence[str]) -> List[List[int]]:
    """최장 공통 부분 수열 길이 테이블을 계산한다."""

    table: List[List[int]] = []
    left_index = 0
    while left_index <= len(left_lines):
        row: List[int] = []
        right_index = 0
        while right_index <= len(right_lines):
            row.append(0)
            right_index += 1
        table.append(row)
        left_index += 1

    left_index = len(left_lines) - 1
    while left_index >= 0:
        right_index = len(right_lines) - 1
        while right_index >= 0:
            if left_lines[left_index] == right_lines[right_index]:
                table[left_index][right_index] = table[left_index + 1][right_index + 1] + 1
            elif table[left_index + 1][right_index] >= table[left_index][right_index + 1]:
                table[left_index][right_index] = table[left_index + 1][right_index]
            else:
                table[left_index][right_index] = table[left_index][right_index + 1]
            right_index -= 1
        left_index -= 1
    return table


def build_diff(
    left_lines: Sequence[str],
    right_lines: Sequence[str],
    table: Sequence[Sequence[int]],
) -> List[str]:
    """LCS 테이블을 따라가며 공통 줄과 변경 줄을 순서대로 출력한다."""

    output: List[str] = []
    left_index = 0
    right_index = 0
    while left_index < len(left_lines) and right_index < len(right_lines):
        if left_lines[left_index] == right_lines[right_index]:
            output.append(f"  {left_lines[left_index]}")
            left_index += 1
            right_index += 1
        elif table[left_index + 1][right_index] >= table[left_index][right_index + 1]:
            output.append(f"- {left_lines[left_index]}")
            left_index += 1
        else:
            output.append(f"+ {right_lines[right_index]}")
            right_index += 1
    while left_index < len(left_lines):
        output.append(f"- {left_lines[left_index]}")
        left_index += 1
    while right_index < len(right_lines):
        output.append(f"+ {right_lines[right_index]}")
        right_index += 1
    return output


def repl() -> None:
    """표준 입력에서 Mini Git 명령을 반복 처리한다."""

    repo = MiniGit()
    while True:
        try:
            line = input("mini-git> ")
        except EOFError:
            print()
            break
        if line.strip().lower() in ("exit", "quit"):
            break
        for output_line in repo.execute(line):
            print(output_line)


if __name__ == "__main__":
    repl()
