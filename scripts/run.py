"""저장소의 Git 협업 과제 산출물을 점검하고 evidence 리포트를 저장한다."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.team_utils import (  # noqa: E402
    branch_name,
    commit_message_status,
    conflict_marker_report,
    pr_body_status,
)


def main() -> int:
    """로드, 전처리, 실행, 평가, 저장 단계를 한 번에 수행한다."""
    evidence_dir = ROOT / "evidence"
    evidence_dir.mkdir(exist_ok=True)

    inputs = load_inputs()
    prepared = preprocess(inputs)
    results = execute_checks(prepared)
    evaluation = evaluate(results)
    save_results(evidence_dir, evaluation)
    print(render_text_report(evaluation))
    return 0 if evaluation["overall_pass"] else 1


def load_inputs() -> dict[str, object]:
    """저장소 파일과 예시 데이터를 읽어 검증 입력으로 준비한다."""
    return {
        "required_paths": [
            "README.md",
            "SUBMISSION.md",
            "docs/CONTRIBUTING.md",
            "docs/conflict-resolution.md",
            "docs/troubleshooting-log.md",
            "src/team_utils.py",
            "tests/test_team_utils.py",
            "Dockerfile",
        ],
        "branch_examples": [
            ("Kim Min Seo", "Add Math Utils"),
            ("Lee Ji Hyun", "Review Guide"),
            ("Park Seo Yeon", "Conflict Log"),
            ("Choi Jun Ho", "Troubleshooting"),
        ],
        "commit_examples": [
            "feat: add math utility examples",
            "docs: add conflict resolution record",
            "update",
            "fix: bug fix",
        ],
        "pr_body": """
        Closes #12
        ## 변경 사항(What)
        - 문서와 유틸 함수를 추가했다.
        ## 변경 이유(Why)
        - 협업 규칙을 재현 가능하게 검증하기 위해서다.
        ## 테스트/검증(How)
        - python3 -m unittest discover -s tests
        """,
    }


def preprocess(inputs: dict[str, object]) -> dict[str, object]:
    """경로 존재 여부와 예시 데이터를 검증하기 쉬운 형태로 변환한다."""
    required_paths = inputs["required_paths"]
    assert isinstance(required_paths, list)
    path_status = {path: (ROOT / path).exists() for path in required_paths}
    return {**inputs, "path_status": path_status}


def execute_checks(prepared: dict[str, object]) -> dict[str, object]:
    """문서 구조, 규칙 함수, 테스트 실행 결과를 수집한다."""
    branch_examples = prepared["branch_examples"]
    commit_examples = prepared["commit_examples"]
    pr_body = prepared["pr_body"]
    assert isinstance(branch_examples, list)
    assert isinstance(commit_examples, list)
    assert isinstance(pr_body, str)

    test_process = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    return {
        "path_status": prepared["path_status"],
        "branch_names": [branch_name(member, topic) for member, topic in branch_examples],
        "commit_status": {
            message: commit_message_status(message).__dict__ for message in commit_examples
        },
        "pr_body_status": pr_body_status(pr_body).__dict__,
        "conflict_markers": conflict_marker_report(ROOT / "src").to_dict(),
        "test_exit_code": test_process.returncode,
        "test_stdout": test_process.stdout,
        "test_stderr": test_process.stderr,
    }


def evaluate(results: dict[str, object]) -> dict[str, object]:
    """실행 결과를 평가해 전체 통과 여부를 계산한다."""
    path_status = results["path_status"]
    commit_status = results["commit_status"]
    pr_body_status = results["pr_body_status"]
    conflict_markers = results["conflict_markers"]
    assert isinstance(path_status, dict)
    assert isinstance(commit_status, dict)
    assert isinstance(pr_body_status, dict)
    assert isinstance(conflict_markers, dict)

    overall_pass = (
        all(path_status.values())
        and commit_status["feat: add math utility examples"]["valid"]
        and not commit_status["update"]["valid"]
        and pr_body_status["missing"] == []
        and conflict_markers["total_markers"] == 0
        and results["test_exit_code"] == 0
    )
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "overall_pass": overall_pass,
        **results,
    }


def save_results(evidence_dir: Path, evaluation: dict[str, object]) -> None:
    """평가 결과를 JSON과 텍스트 파일로 저장한다."""
    (evidence_dir / "run-report.json").write_text(
        json.dumps(evaluation, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (evidence_dir / "run-report.txt").write_text(render_text_report(evaluation), encoding="utf-8")


def render_text_report(evaluation: dict[str, object]) -> str:
    """사람이 읽기 쉬운 실행 리포트를 만든다."""
    path_status = evaluation["path_status"]
    assert isinstance(path_status, dict)
    lines = [
        "Git 협업 워크플로우 점검 리포트",
        f"생성 시각(UTC): {evaluation['generated_at']}",
        f"전체 결과: {'통과' if evaluation['overall_pass'] else '실패'}",
        "",
        "필수 경로:",
    ]
    lines.extend(f"- {path}: {'있음' if exists else '없음'}" for path, exists in path_status.items())
    lines.extend(
        [
            "",
            f"테스트 종료 코드: {evaluation['test_exit_code']}",
            f"src 충돌 마커 수: {evaluation['conflict_markers']['total_markers']}",
        ]
    )
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
