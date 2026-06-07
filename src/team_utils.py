"""팀 Git 협업 규칙을 점검하는 작은 유틸리티 함수 모음."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import re


@dataclass(frozen=True)
class CommitMessageStatus:
    """커밋 메시지 검증 결과를 담는다."""

    valid: bool
    reason: str


@dataclass(frozen=True)
class PrBodyStatus:
    """PR 본문 필수 항목 검증 결과를 담는다."""

    missing: list[str]

    @property
    def valid(self) -> bool:
        """누락 항목이 없으면 참을 반환한다."""
        return not self.missing


@dataclass(frozen=True)
class ConflictFileReport:
    """충돌 마커가 발견된 파일과 라인 번호를 담는다."""

    path: str
    lines: list[int]


@dataclass(frozen=True)
class ConflictMarkerReport:
    """저장소에서 발견한 충돌 마커의 요약을 담는다."""

    total_markers: int
    files: list[ConflictFileReport]

    def to_dict(self) -> dict[str, object]:
        """JSON 저장에 사용할 수 있는 딕셔너리로 변환한다."""
        return {
            "total_markers": self.total_markers,
            "files": [asdict(file_report) for file_report in self.files],
        }


COMMIT_PATTERN = re.compile(r"^(feat|fix|docs|refactor|test|chore|build|ci)(\([a-z0-9-]+\))?: .+")
ISSUE_PATTERN = re.compile(r"\b(Closes|Fixes)\s+#\d+\b", re.IGNORECASE)
CONFLICT_MARKERS = ("<<<<<<<", "=======", ">>>>>>>")
VAGUE_SUBJECTS = {"update", "fix", "temp", "wip", "final", "bug fix", "edit file"}


def branch_name(member: str, topic: str) -> str:
    """팀원 이름과 작업 주제로 GitHub Flow용 feature 브랜치 이름을 만든다."""
    slug = _slugify(f"{member}-{topic}")
    return f"feature/{slug}"


def commit_message_status(message: str) -> CommitMessageStatus:
    """Conventional Commit 형식과 의미 있는 subject 여부를 검증한다."""
    normalized = " ".join(message.strip().split())
    if normalized.lower() in VAGUE_SUBJECTS:
        return CommitMessageStatus(False, "금지된 단독 메시지")
    if not COMMIT_PATTERN.match(normalized):
        return CommitMessageStatus(False, "허용된 type과 subject 형식이 아님")

    subject = normalized.split(": ", 1)[1].strip().lower()
    if subject in VAGUE_SUBJECTS:
        return CommitMessageStatus(False, "subject가 변경 대상이나 효과를 설명하지 않음")
    return CommitMessageStatus(True, "유효한 커밋 메시지")


def pr_body_status(body: str) -> PrBodyStatus:
    """PR 본문에서 이슈 연결, 변경 사항, 변경 이유, 검증 방법을 확인한다."""
    checks = [
        ("연결 이슈", bool(ISSUE_PATTERN.search(body))),
        ("변경 사항", "what" in body.lower() or "변경 사항" in body),
        ("변경 이유", "why" in body.lower() or "변경 이유" in body),
        ("검증 방법", "how" in body.lower() or "테스트/검증" in body or "검증 방법" in body),
    ]
    missing = [name for name, present in checks if not present]
    return PrBodyStatus(missing)


def conflict_marker_report(root: Path) -> ConflictMarkerReport:
    """지정한 경로 아래 텍스트 파일에서 Git 충돌 마커 위치를 찾는다."""
    files: list[ConflictFileReport] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or _should_skip(path):
            continue
        lines = _marker_lines(path)
        if lines:
            files.append(ConflictFileReport(str(path.relative_to(root)).replace("\\", "/"), lines))

    total_markers = sum(len(file_report.lines) for file_report in files)
    return ConflictMarkerReport(total_markers, files)


def _slugify(value: str) -> str:
    """브랜치 이름에 안전한 소문자 하이픈 문자열로 변환한다."""
    lowered = value.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", lowered).strip("-")
    return re.sub(r"-+", "-", slug)


def _should_skip(path: Path) -> bool:
    """바이너리와 Git 내부 디렉터리를 검사 대상에서 제외한다."""
    ignored_parts = {".git", "__pycache__", ".pytest_cache"}
    if ignored_parts.intersection(path.parts):
        return True
    return path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".zip", ".pyc"}


def _marker_lines(path: Path) -> list[int]:
    """파일 하나에서 충돌 마커가 시작되는 라인 번호 목록을 반환한다."""
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return []
    lines: list[int] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if any(line.startswith(marker) for marker in CONFLICT_MARKERS):
            lines.append(line_number)
    return lines
